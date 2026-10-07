import os, sys, glob, json, uuid, re, io, base64, requests
import pandas as pd
from PIL import Image

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = r"c:\Users\passp\Desktop\univercity\4-2\taobao_jackets"
DOWNLOAD_DIR = os.path.join(BASE_DIR, "downloaded_jackets")
OUTPUT_EXCEL = os.path.join(BASE_DIR, "taobao_leather_jackets_with_brands.xlsx")
OUTPUT_CSV = os.path.join(BASE_DIR, "taobao_leather_jackets_with_brands.csv")

feynman_auth = os.path.expanduser("~/.feynman/agent/auth.json")
with open(feynman_auth, "r", encoding="utf-8") as f:
    api_key = json.load(f)["opencode-go"]["key"]

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
        return None

target_folders = ["item_970351720471", "item_1080314063229", "item_738083059484"]

results = []
if os.path.exists(OUTPUT_CSV):
    prev_df = pd.read_csv(OUTPUT_CSV, encoding="utf-8-sig")
    results = prev_df.to_dict('records')

for folder in target_folders:
    folder_path = os.path.join(DOWNLOAD_DIR, folder)
    if not os.path.exists(folder_path): continue

    info_file = os.path.join(folder_path, "item_info.txt")
    item_title = folder
    if os.path.exists(info_file):
        with open(info_file, "r", encoding="utf-8", errors="ignore") as inf:
            for l in inf:
                if l.startswith("상품명:"): item_title = l.replace("상품명:", "").strip()

    jpgs = sorted(glob.glob(os.path.join(folder_path, "photo_*.jpg")))
    if not jpgs: continue

    size_card_path = jpgs[1] if len(jpgs) > 1 and os.path.getsize(jpgs[0]) == 33084 else jpgs[0]
    jacket_path = jpgs[2] if len(jpgs) > 2 else jpgs[-1]
    label_path = jpgs[4] if len(jpgs) > 4 else jpgs[-1]

    card_b64 = encode_image(size_card_path)
    jacket_b64 = encode_image(jacket_path)
    label_b64 = encode_image(label_path)

    prompt = (
        "다음 세 장의 사진(손글씨 실측표, 전체 자켓, 라벨)을 보고 복잡한 생각이나 장황한 추론 과정 없이, 즉시 정확한 값만 아래 JSON 형식으로 답하세요:\n"
        "```json\n"
        "{\n"
        '  "jacket_code": "실측지 상단 编号 (예: W28, V160, U22 등)",\n'
        '  "brand": "판독된 브랜드명 영문/한글 (미상일 경우 빈티지 오리지널)",\n'
        '  "leather_type": "가죽 종류 (양가죽, 소가죽, 염소가죽, 스웨이드, 사슴가죽 등)",\n'
        '  "origin": "원산지/제조국 (미국, 이탈리아, 일본, 한국 등, 불명 시 불명)",\n'
        '  "shoulder_cm": "어깨 실측 숫자",\n'
        '  "chest_cm": "가슴 실측 숫자 (카드에 적힌 그대로 숫자만)",\n'
        '  "length_cm": "총기장 실측 숫자",\n'
        '  "sleeve_cm": "소매길이 실측 숫자"\n'
        "}\n"
        "```"
    )

    content_list = [{"type": "text", "text": prompt}]
    if card_b64: content_list.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{card_b64}"}})
    if jacket_b64: content_list.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{jacket_b64}"}})
    if label_b64: content_list.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{label_b64}"}})

    url = "https://opencode.ai/zen/go/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "x-opencode-session": f"ses_taobao_retry_{uuid.uuid4().hex[:8]}"
    }
    payload = {
        "model": "deepseek-v4.1-flash",
        "messages": [{"role": "user", "content": content_list}],
        "max_tokens": 8000
    }

    resp = requests.post(url, headers=headers, json=payload, timeout=70)
    if resp.status_code == 200:
        choice = resp.json()["choices"][0]["message"]
        content = choice.get("content", "")
        reasoning = choice.get("reasoning_content", "")
        search_target = content if content.strip() else reasoning
        m = re.search(r'```json\s*(\{.*?\})\s*```', search_target, re.DOTALL)
        if not m:
            m = re.search(r'(\{\s*"jacket_code".*?\})', search_target, re.DOTALL)
        if m:
            res_dict = json.loads(m.group(1))
            code = res_dict.get("jacket_code", "-")
            brand = res_dict.get("brand", "빈티지 오리지널")
            leather = res_dict.get("leather_type", "천연가죽")
            origin = res_dict.get("origin", "불명")
            sh = res_dict.get("shoulder_cm", "-")
            ch = res_dict.get("chest_cm", "-")
            ln = res_dict.get("length_cm", "-")
            sl = res_dict.get("sleeve_cm", "-")
            print(f"[✓ 재시도 성공] {folder} -> 품번: {code} | 브랜드: {brand} | 소재: {leather} | {sh}/{ch}/{ln}/{sl}")
            results.append({
                "순번": len(results) + 1,
                "상품폴더": folder,
                "자켓품번": code,
                "판독브랜드": brand,
                "가죽소재": leather,
                "원산지": origin,
                "어깨(cm)": sh,
                "가슴(cm)": ch,
                "기장(cm)": ln,
                "소매(cm)": sl,
                "실측사진": os.path.basename(size_card_path),
                "총사진수": len(jpgs),
                "상품명": item_title
            })

df = pd.DataFrame(results)
# 순번 재정렬
df["순번"] = range(1, len(df) + 1)
df.to_excel(OUTPUT_EXCEL, index=False)
df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")
print(f"\n최종 업데이트 완료! 총 {len(df)}개 품목 모두 저장 완료.")
