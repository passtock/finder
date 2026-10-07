# 🧥 타오바오 레더자켓 스크래퍼 & AI 브랜드 판독 파이프라인

본 도구는 타오바오 빈티지 상점(**老咔叽LAOKAJI**)의 레더자켓 전체 상품을 자동으로 수집하고, 상세 사진(목 라벨, 케어라벨, 실측표)을 분석하여 브랜드를 매칭하는 파이프라인입니다.

---

## 📁 구성 파일

1. **`taobao_jacket_pipeline.py`**:
   - 현재 로그인된 Chrome 브라우저(`port: 9222`)와 연동
   - 상점 내 모든 레더자켓 상품 링크, 가격, 상세 이미지 일괄 수집 및 로컬 다운로드
   - 1차 요약 엑셀(`taobao_leather_jackets_summary.xlsx`) 생성
2. **`ai_brand_matcher.py`**:
   - 다운로드된 이미지(목 탭, 케어 라벨, 실측지)를 Gemini Vision AI로 판독
   - 브랜드명, 가죽 종류, 제조국, 어깨/가슴/기장 실측 데이터를 추출하여 최종 엑셀(`taobao_leather_jackets_with_brands.xlsx`) 생성

---

## 🚀 실행 방법

### 1단계: 상품 및 상세 이미지 일괄 스크랩
터미널에서 아래 명령을 실행합니다:
```bash
python taobao_jacket_pipeline.py
```
* 수집된 이미지는 `downloaded_jackets/item_{ID}/` 폴더에 자동 분류 저장됩니다.

### 2단계: AI 브랜드 매칭 및 실측 엑셀 생성
```bash
# Gemini API Key 설정 후 실행 (키가 있을 경우)
set GEMINI_API_KEY=your_api_key_here
python ai_brand_matcher.py
```
* 완료 시 `taobao_leather_jackets_with_brands.xlsx` 파일이 생성됩니다.
