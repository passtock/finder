# -*- coding: utf-8 -*-
"""
OpenCode Go x DeepSeek 4.1 Flash 기반 빈티지 가죽자켓 브랜드 & 실측 자동 판독기
파인만 에이전트(Feynman) API 키를 자동으로 연동하여 12개 품목에 대해
손글씨 실측표(编号, 肩宽, 胸围, 衣长, 袖长)와 브랜드 라벨을 초고속 클라우드 판독합니다.
"""

import os
import sys
import glob
import json
import uuid
import re
import io
import base64
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
DEFAULT_MODEL = "deepseek-v4.1-flash"

TARGET_FOLDERS = [
    "item_1077196468019", # E1
    "item_811036195091",  # AC91
    "item_1080043211319", # Q118
    "item_1083932831050", # P306
    "item_1071816497728", # P1
    "item_1075139885104", # Q61
    "item_1078567805117", # Q91
    "item_1061875162656", # M1
    "item_1069955447343", # M41
    "item_1075374113206", # U61
    "item_1081695145771", # P211
    "item_1054456462690", # X31
]

def get_feynman_api_key():
    """파인만 에이전트(~/.feynman/agent/auth.json)에 저장된 OpenCode Go API 키 자동 로드"""
    feynman_auth = os.path.expanduser("~/.feynman/agent/auth.json")
    if os.path.exists(feynman_auth):
        try:
            with open(feynman_auth, "r", encoding="utf-8") as f:
                data = json.load(f)
                item = data.get("opencode-go") or data.get("opencodego")
                if isinstance(item, dict) and item.get("key"):
                    return item["key"]
                elif isinstance(item, str):
                    return item
        except Exception as e:
            print(f"[-] Feynman auth.json 읽기 오류: {e}")
            
    # 환경변수 또는 로컬 config fallback
    if os.environ.get("OPENCODE_API_KEY"):
        return os.environ.get("OPENCODE_API_KEY")
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f).get("api_key", "")
        except Exception:
            pass
    return ""

def encode_image(img_path, max_dim=600):
    try:
        with Image.open(img_path) as im:
            im = im.convert("RGB")
            w, h = im.size
            if max(w, h) > max_dim:
                scale = max_dim / float(max(w, h))
                im = im.resize((int(w * scale), int(h * scale)), Image.Resampling.LANCZOS)
            buf = io.BytesIO()
            im.save(buf, format="JPEG", quality=80)
            return base64.b64encode(buf.getvalue()).decode("utf-8")
    except Exception as e:
        print(f"[-] 이미지 변환 실패 ({img_path}): {e}")
        return None

def analyze_jacket_with_deepseek(api_key, folder_name):
    folder_path = os.path.join(DOWNLOAD_DIR, folder_name)
    if not os.path.exists(folder_path):
        return None

    # 상품명 읽기
    info_file = os.path.join(folder_path, "item_info.txt")
    item_title = folder_name
    if os.path.exists(info_file):
        with open(info_file, "r", encoding="utf-8", errors="ignore") as inf:
            for l in inf:
                if l.startswith("상품명:"): item_title = l.replace("상품명:", "").strip()

    jpgs = sorted(glob.glob(os.path.join(folder_path, "photo_*.jpg")))
    if not jpgs:
        return None

    # 실측 카드 찾기: photo_001, photo_002, photo_003 중 크기가 33084(가이드 템플릿)가 아닌 첫 사진
    size_card_path = None
    for j in jpgs[:4]:
        if os.path.getsize(j) != 33084:
            size_card_path = j
            break

    if not size_card_path:
        size_card_path = jpgs[0]

    # 라벨 사진 후보: photo_005 ~ photo_012 사이에서 한 장 선택
    label_path = None
    for j in jpgs[3:12]:
        label_path = j
        break
    if not label_path:
        label_path = jpgs[-1]

    card_b64 = encode_image(size_card_path)
    label_b64 = encode_image(label_path)

    prompt = (
        "두 장의 사진은 동일한 빈티지 가죽자켓의 손글씨 실측표 카드(사진1)와 라벨/자켓(사진2)입니다.\n"
        "다른 설명 없이 아래 JSON 포맷으로만 응답해주세요:\n"
        "```json\n"
        "{\n"
        '  "jacket_code": "실측지 상단 编号 (예: E1, Q118, 91 등)",\n'
        '  "brand": "판독된 브랜드명 영문/한글 (미상일 경우 빈티지 오리지널)",\n'
        '  "leather_type": "가죽 종류 (양가죽, 소가죽, 염소가죽, 스웨이드 등)",\n'
        '  "origin": "원산지/제조국 (미국, 이탈리아, 일본, 한국 등, 불명 시 불명)",\n'
        '  "shoulder_cm": "어깨 실측 숫자",\n'
        '  "chest_cm": "가슴 실측 숫자",\n'
        '  "length_cm": "총기장 실측 숫자",\n'
        '  "sleeve_cm": "소매길이 실측 숫자"\n'
        "}\n"
        "```"
    )

    url = f"{DEFAULT_BASE_URL.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "x-opencode-session": f"ses_taobao_{uuid.uuid4().hex[:12]}"
    }

    content_list = [
        {"type": "text", "text": prompt},
        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{card_b64}"}}
    ]
    if label_b64:
        content_list.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{label_b64}"}})

    payload = {
        "model": DEFAULT_MODEL,
        "messages": [{"role": "user", "content": content_list}],
        "max_tokens": 4000
    }

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=70)
        if resp.status_code != 200:
            print(f"  [-] API 오류 [{resp.status_code}]: {resp.text[:200]}")
            return None

        choice = resp.json()["choices"][0]
        content = choice["message"].get("content", "")
        reasoning = choice["message"].get("reasoning_content", "")
        search_target = content if content.strip() else reasoning

        m = re.search(r'```json\s*(\{.*?\})\s*```', search_target, re.DOTALL)
        if not m:
            m = re.search(r'(\{\s*"jacket_code".*?\})', search_target, re.DOTALL)

        if m:
            res_dict = json.loads(m.group(1))
            res_dict["folder"] = folder_name
            res_dict["title"] = item_title
            res_dict["card_photo"] = os.path.basename(size_card_path)
            res_dict["total_photos"] = len(jpgs)
            return res_dict
        else:
            print(f"  [-] JSON 추출 실패: {search_target[-300:]}")
            return None
    except Exception as e:
        print(f"  [-] 예외 발생: {e}")
        return None

def main():
    api_key = get_feynman_api_key()
    if not api_key:
        print("[!] 파인만 에이전트 auth.json 또는 OPENCODE_API_KEY를 찾을 수 없습니다.")
        return

    print("=" * 65)
    print("🧥 [OpenCode Go x DeepSeek 4.1 Flash] 가죽자켓 브랜드 판독 시작")
    print(f"• 모델: {DEFAULT_MODEL}")
    print(f"• 연동 API: 파인만 에이전트 OpenCode Go 키 (성공)")
    print(f"• 대상: 완료된 12개 품목 (총 2,602장 사진)")
    print("=" * 65 + "\n")

    results = []
    for idx, folder in enumerate(TARGET_FOLDERS, 1):
        print(f"[{idx:02d}/{len(TARGET_FOLDERS)}] {folder} 분석 중...")
        res = analyze_jacket_with_deepseek(api_key, folder)
        if res:
            code = res.get("jacket_code", "-")
            brand = res.get("brand", "빈티지 오리지널")
            leather = res.get("leather_type", "천연가죽")
            origin = res.get("origin", "불명")
            sh = res.get("shoulder_cm", "-")
            ch = res.get("chest_cm", "-")
            ln = res.get("length_cm", "-")
            sl = res.get("sleeve_cm", "-")
            print(f"  [✓] 품번: {code} | 브랜드: {brand} | 소재: {leather} | 어깨: {sh} | 가슴: {ch} | 기장: {ln}")
            results.append({
                "순번": idx,
                "상품폴더": folder,
                "자켓품번": code,
                "판독브랜드": brand,
                "가죽소재": leather,
                "원산지": origin,
                "어깨(cm)": sh,
                "가슴(cm)": ch,
                "기장(cm)": ln,
                "소매(cm)": sl,
                "실측사진": res.get("card_photo", "-"),
                "총사진수": res.get("total_photos", 0),
                "상품명": res.get("title", folder)
            })
        else:
            print(f"  [-] {folder} 분석 건너뜀")

    if results:
        df = pd.DataFrame(results)
        df.to_excel(OUTPUT_EXCEL, index=False)
        df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")
        print("\n" + "=" * 65)
        print(f"[🎉] 판독 완료! 총 {len(results)}개 품목 저장됨:")
        print(f"  - 엑셀: {OUTPUT_EXCEL}")
        print(f"  - CSV:  {OUTPUT_CSV}")
        print("=" * 65)

if __name__ == "__main__":
    main()
