# -*- coding: utf-8 -*-
"""
OpenCode Go 기반 빈티지 가죽자켓 브랜드 & 실측 자동 판독기
노트북 로컬 CPU 사용량 0% - 클라우드 Vision AI (OpenCode Go)를 호출하여
손글씨 실측표(编号, 肩宽, 胸围, 衣长, 袖长)와 브랜드 라벨을 고정밀 분석합니다.
"""

import os
import sys
import glob
import json
import base64
import re
import argparse
import requests
import pandas as pd
from PIL import Image

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = r"c:\Users\passp\Desktop\univercity\4-2\taobao_jackets"
DOWNLOAD_DIR = os.path.join(BASE_DIR, "downloaded_jackets")
OUTPUT_EXCEL = os.path.join(BASE_DIR, "taobao_leather_jackets_with_brands.xlsx")
OUTPUT_CSV = os.path.join(BASE_DIR, "taobao_leather_jackets_with_brands.csv")
CONFIG_FILE = os.path.join(BASE_DIR, "opencode_config.json")

# OpenCode Go 기본 설정
DEFAULT_BASE_URL = "https://opencode.ai/zen/go/v1"
DEFAULT_MODEL = "qwen2.5-vl-72b-instruct"

SYSTEM_PROMPT = """당신은 빈티지 및 아메카지 가죽자켓 전문 분석가입니다.
제공된 이미지(손글씨 실측표 및 자켓/라벨 사진)를 정밀하게 분석하여 아래 JSON 포맷으로만 응답하세요.

[필수 추출 항목]
1. jacket_code: 손글씨 실측지의 '编号' (예: Q118, AC91, 91, E1 등)
2. brand: 판독된 브랜드명 영문/한글 (예: Schott NYC, L.L.Bean, RUPERT, BEAMS, GUESS, 빈티지 오리지널 등)
3. leather_type: 가죽 종류 (예: 양가죽(绵羊皮), 소가죽(牛皮), 염소가죽(山羊皮), 스웨이드 등)
4. origin: 제조국 (예: 미국, 이탈리아, 일본, 한국, 파키스탄, 중국 등)
5. shoulder_cm: 어깨 실측 (숫자)
6. chest_cm: 가슴 실측 (단면 숫자로 변환, 胸围x2일 경우 단면 값 표기)
7. length_cm: 총기장 (숫자)
8. sleeve_cm: 소매길이 (숫자)
9. style: 자켓 형태 (예: 싱글 라이더, 더블 라이더, A-2 플라이트, 테일러드 블레이저 등)

응답은 반드시 마크다운 코드블록 없이 순수 JSON 형식만 반환하세요:
{
  "jacket_code": "...",
  "brand": "...",
  "leather_type": "...",
  "origin": "...",
  "shoulder_cm": "...",
  "chest_cm": "...",
  "length_cm": "...",
  "sleeve_cm": "...",
  "style": "..."
}"""

def load_api_key():
    # 1. 환경변수 확인
    key = os.environ.get("OPENCODE_API_KEY", "")
    if key:
        return key
    
    # 2. config 파일 확인
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                return cfg.get("api_key", "")
        except Exception:
            pass
    return ""

def encode_image_to_base64(image_path, max_dim=1024):
    """이미지 리사이즈 후 Base64 인코딩 (전송 속도 최적화 및 토큰 절약)"""
    try:
        with Image.open(image_path) as img:
            img = img.convert("RGB")
            w, h = img.size
            if max(w, h) > max_dim:
                scale = max_dim / float(max(w, h))
                img = img.resize((int(w * scale), int(h * scale)), Image.Resampling.LANCZOS)
            
            import io
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=85)
            return base64.b64encode(buf.getvalue()).decode("utf-8")
    except Exception as e:
        print(f"[-] 이미지 변환 실패 ({image_path}): {e}")
        return None

def call_opencode_vision(api_key, base_url, model, image_paths, prompt_text=""):
    """OpenCode Go API를 호출하여 이미지 분석 수행"""
    url = f"{base_url.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    content_list = [{"type": "text", "text": prompt_text or SYSTEM_PROMPT}]
    for p in image_paths:
        b64 = encode_image_to_base64(p)
        if b64:
            content_list.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{b64}",
                    "detail": "high"
                }
            })

    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": content_list}
        ],
        "temperature": 0.1
    }

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=60)
        if resp.status_code == 200:
            res_json = resp.json()
            raw_text = res_json["choices"][0]["message"]["content"].strip()
            
            # JSON 블록 정리
            if raw_text.startswith("```json"):
                raw_text = raw_text[7:-3].strip()
            elif raw_text.startswith("```"):
                raw_text = raw_text[3:-3].strip()
            
            return json.loads(raw_text)
        else:
            print(f"[-] OpenCode API 응답 오류 [{resp.status_code}]: {resp.text[:200]}")
            return None
    except Exception as e:
        print(f"[-] API 요청 중 예외 발생: {e}")
        return None

def analyze_all_jackets(api_key, base_url=DEFAULT_BASE_URL, model=DEFAULT_MODEL):
    if not api_key:
        print("\n" + "="*60)
        print("[!] OpenCode Go API Key가 설정되지 않았습니다.")
        print(f"    방법 1: set OPENCODE_API_KEY=your_key_here")
        print(f"    방법 2: python opencode_jacket_analyzer.py --api-key YOUR_KEY")
        print(f"    방법 3: {CONFIG_FILE} 에 {{\"api_key\": \"YOUR_KEY\"}} 저장")
        print("="*60 + "\n")
        return

    item_folders = sorted([f for f in glob.glob(os.path.join(DOWNLOAD_DIR, "item_*")) if os.path.isdir(f)])
    print(f"[*] 총 {len(item_folders)}개 상품 폴더를 검색합니다 (OpenCode Go 모델: {model})...")

    all_results = []
    
    for idx, folder in enumerate(item_folders, 1):
        folder_name = os.path.basename(folder)
        jpgs = sorted(glob.glob(os.path.join(folder, "photo_*.jpg")))
        if not jpgs:
            continue
            
        print(f"\n[{idx}/{len(item_folders)}] {folder_name} 분석 중 ({len(jpgs)}장 보유)...")
        
        # 1. 실측표 사진 후보 탐색 (보통 앞 번호 1~15번 사이에 손글씨 실측표 존재)
        # 각 자켓마다 손글씨 표 + 자켓 전면/라벨 2~3장을 묶어서 전송
        candidates = jpgs[:12] # 앞쪽 대표 사진들
        
        result = call_opencode_vision(api_key, base_url, model, candidates)
        if result:
            print(f"  [✓] 판독 성공: [{result.get('jacket_code', '-')}] 브랜드: {result.get('brand', '미상')} | 가죽: {result.get('leather_type', '-')} | 어깨: {result.get('shoulder_cm', '-')} | 가슴: {result.get('chest_cm', '-')}")
            all_results.append({
                "상품폴더": folder_name,
                "자켓번호": result.get("jacket_code", "-"),
                "브랜드": result.get("brand", "빈티지 오리지널"),
                "가죽소재": result.get("leather_type", "천연가죽"),
                "원산지": result.get("origin", "불명"),
                "스타일": result.get("style", "레더 자켓"),
                "어깨(cm)": result.get("shoulder_cm", "-"),
                "가슴(cm)": result.get("chest_cm", "-"),
                "기장(cm)": result.get("length_cm", "-"),
                "소매(cm)": result.get("sleeve_cm", "-"),
                "총사진수": len(jpgs)
            })
        else:
            print(f"  [-] 판독 실패/건너뜀: {folder_name}")

    if all_results:
        df = pd.DataFrame(all_results)
        df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")
        df.to_excel(OUTPUT_EXCEL, index=False)
        print(f"\n[🎉] 전체 분석 완료! 결과 파일이 저장되었습니다:")
        print(f"  - Excel: {OUTPUT_EXCEL}")
        print(f"  - CSV:   {OUTPUT_CSV}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="OpenCode Go 가죽자켓 브랜드 판독기")
    parser.add_argument("--api-key", default="", help="OpenCode Go API Key")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="OpenCode Go Base URL")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Model name (e.g. qwen2.5-vl-72b-instruct)")
    args = parser.parse_args()

    key = args.api_key or load_api_key()
    analyze_all_jackets(key, args.base_url, args.model)
