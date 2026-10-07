import os, sys, glob, json, uuid, re, io, base64, requests
from PIL import Image

sys.stdout.reconfigure(encoding='utf-8')

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
        print(f"Error encoding {img_path}: {e}")
        return None

folder = r"c:\Users\passp\Desktop\univercity\4-2\taobao_jackets\downloaded_jackets\item_1076140587381"
jpgs = sorted(glob.glob(os.path.join(folder, "photo_*.jpg")))
print("Jpgs found:", len(jpgs))

# size card is photo_002
card_b64 = encode_image(jpgs[1]) # photo_002
jacket_b64 = encode_image(jpgs[2]) # photo_003
label_b64 = encode_image(jpgs[4]) # photo_005

prompt = (
    "제공된 사진들은 동일한 빈티지 가죽자켓의 손글씨 실측표 카드, 전체 사진, 라벨/세부 사진입니다.\n"
    "다른 설명 없이 아래 JSON 포맷으로만 응답해주세요:\n"
    "```json\n"
    "{\n"
    '  "jacket_code": "실측지 상단 编号 (예: E1, Q118, V80 등)",\n'
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

content_list = [
    {"type": "text", "text": prompt},
    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{card_b64}"}},
    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{jacket_b64}"}},
    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{label_b64}"}}
]

url = "https://opencode.ai/zen/go/v1/chat/completions"
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json",
    "x-opencode-session": f"ses_taobao_test_{uuid.uuid4().hex[:8]}"
}
payload = {
    "model": "deepseek-v4.1-flash",
    "messages": [{"role": "user", "content": content_list}],
    "max_tokens": 4000
}

resp = requests.post(url, headers=headers, json=payload, timeout=60)
print("Status code:", resp.status_code)
res = resp.json()
choice = res["choices"][0]["message"]
content = choice.get("content", "")
reasoning = choice.get("reasoning_content", "")
print("Reasoning snippet:", reasoning[:200])
print("Content:\n", content)
