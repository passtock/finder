import os
import glob
import json
import pandas as pd
from PIL import Image
import google.generativeai as genai

# ==========================================
# Gemini AI 설정 (API 키 설정 필요 시 환경변수 또는 직접 입력)
# ==========================================
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

SUMMARY_EXCEL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "taobao_leather_jackets_summary.xlsx")
ANALYZED_EXCEL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "taobao_leather_jackets_with_brands.xlsx")

SYSTEM_PROMPT = """
당신은 빈티지 및 아메카지 레더자켓 전문 감정가입니다.
제공된 레더자켓 사진들(손글씨 실측표, 목 탭/라벨, 케어라벨, 정면 사진 등)을 분석하여 다음 정보를 JSON 형식으로만 응답하세요:

{
  "detected_brand": "판독된 브랜드명 (예: L.L.Bean, Schott NYC, Avirex, 미상 등)",
  "leather_type": "가죽 종류 (예: 소가죽, 양가죽, 버팔로, 돈모 등)",
  "origin_country": "원산지/제조국 (예: 미국, 파키스탄, 일본, 한국, 불명 등)",
  "jacket_style": "스타일 (예: A-2 플라이트 자켓, 싱글 라이더, 더블 라이더, 가죽 코트 등)",
  "measurements": {
    "shoulder_cm": "어깨 실측",
    "chest_cm": "가슴 실측",
    "length_cm": "기장 실측",
    "sleeve_cm": "소매 실측"
  },
  "vintage_notes": "특이사항 및 빈티지 특징 요약"
}
JSON만 반환하고 마크다운 코드블록이나 다른 텍스트는 포함하지 마세요.
"""

def analyze_item_images(item_folder):
    """아이템 폴더 내 이미지들을 Gemini Vision으로 분석"""
    if not GEMINI_API_KEY:
        print("[!] GEMINI_API_KEY가 설정되지 않았습니다. 환경변수 등록 후 실행해주세요.")
        return None

    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash")

    # 폴더 내 다운로드된 이미지 로드
    img_files = sorted(glob.glob(os.path.join(item_folder, "*.jpg")))[:5]
    if not img_files:
        return None

    pil_images = [Image.open(f) for f in img_files]

    try:
        response = model.generate_content([SYSTEM_PROMPT] + pil_images)
        text = response.text.strip()
        # JSON 파싱
        if text.startswith("```json"):
            text = text[7:-3].strip()
        elif text.startswith("```"):
            text = text[3:-3].strip()
        data = json.loads(text)
        return data
    except Exception as e:
        print(f"[-] 분석 중 오류 발생: {e}")
        return None

def run_brand_matching():
    if not os.path.exists(SUMMARY_EXCEL):
        print(f"[-] {SUMMARY_EXCEL} 파일이 없습니다. 먼저 taobao_jacket_pipeline.py를 실행하세요.")
        return

    df = pd.read_excel(SUMMARY_EXCEL)
    print(f"[*] 총 {len(df)}개 상품의 브랜드 분석을 시작합니다...")

    brands = []
    leathers = []
    origins = []
    styles = []
    shoulders = []
    chests = []
    lengths = []
    sleeves = []
    notes = []

    for idx, row in df.iterrows():
        folder = row["저장폴더"]
        print(f"[{idx+1}/{len(df)}] {row['상품ID']} 분석 중...")
        res = analyze_item_images(folder)
        if res:
            brands.append(res.get("detected_brand", "미상"))
            leathers.append(res.get("leather_type", "불명"))
            origins.append(res.get("origin_country", "불명"))
            styles.append(res.get("jacket_style", "미분류"))
            m = res.get("measurements", {})
            shoulders.append(m.get("shoulder_cm", "-"))
            chests.append(m.get("chest_cm", "-"))
            lengths.append(m.get("length_cm", "-"))
            sleeves.append(m.get("sleeve_cm", "-"))
            notes.append(res.get("vintage_notes", ""))
        else:
            brands.append("분석 대기/실패")
            leathers.append("-")
            origins.append("-")
            styles.append("-")
            shoulders.append("-")
            chests.append("-")
            lengths.append("-")
            sleeves.append("-")
            notes.append("-")

    df["판독브랜드"] = brands
    df["가죽종류"] = leathers
    df["원산지"] = origins
    df["스타일"] = styles
    df["어깨(cm)"] = shoulders
    df["가슴(cm)"] = chests
    df["기장(cm)"] = lengths
    df["소매(cm)"] = sleeves
    df["비고"] = notes

    df.to_excel(ANALYZED_EXCEL, index=False)
    print(f"\n[🎉] 브랜드 매칭 완료! 엑셀 파일 저장됨: {ANALYZED_EXCEL}")

if __name__ == "__main__":
    run_brand_matching()
