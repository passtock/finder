import os, glob, sys, json, requests, base64, io, uuid
from PIL import Image

sys.stdout.reconfigure(encoding='utf-8')

feynman_auth = os.path.expanduser("~/.feynman/agent/auth.json")
with open(feynman_auth, "r", encoding="utf-8") as f:
    api_key = json.load(f)["opencode-go"]["key"]

def encode_image(img_path, max_dim=500):
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
    except Exception:
        return None

folder = r"c:\Users\passp\Desktop\univercity\4-2\taobao_jackets\downloaded_jackets\item_1081695145771"

test_jackets = [
    ("Jacket 1", "photo_002.jpg", "photo_003.jpg", "photo_006.jpg"),
    ("Jacket 2", "photo_009.jpg", "photo_010.jpg", "photo_013.jpg"),
    ("Jacket 3", "photo_016.jpg", "photo_017.jpg", "photo_020.jpg"),
]

for label, card_name, front_name, tag_name in test_jackets:
    card_p = os.path.join(folder, card_name)
    front_p = os.path.join(folder, front_name)
    tag_p = os.path.join(folder, tag_name)
    
    card_b64 = encode_image(card_p)
    front_b64 = encode_image(front_p)
    tag_b64 = encode_image(tag_p)
    
    prompt = (
        "다음 3장의 사진은 동일한 1벌의 빈티지 가죽자켓 사진입니다:\n"
        "- 사진 1: 손글씨 실측표 카드\n"
        "- 사진 2: 자켓 전체 정면 사진\n"
        "- 사진 3: 목 라벨 / 케어 라벨\n\n"
        "아래 JSON 포맷으로만 응답해주세요 (다른 텍스트 없이):\n"
        "```json\n"
        "{\n"
        '  "jacket_code": "실측지 상단 编号 (예: P211, P212, P213 등)",\n'
        '  "brand": "라벨에 적힌 정확한 브랜드명 영문/한글 (미상일 경우 빈티지 오리지널)",\n'
        '  "leather_type": "가죽 종류 (양가죽, 소가죽, 사슴가죽 등)",\n'
        '  "origin": "원산지 (미국, 이탈리아, 일본, 한국 등, 불명 시 불명)",\n'
        '  "shoulder_cm": "어깨 실측 숫자",\n'
        '  "chest_cm": "가슴 실측 숫자",\n'
        '  "length_cm": "총기장 실측 숫자",\n'
        '  "sleeve_cm": "소매길이 실측 숫자"\n'
        "}\n"
        "```"
    )
    
    url = "https://opencode.ai/zen/go/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "x-opencode-session": f"ses_seg_{uuid.uuid4().hex[:8]}"
    }
    payload = {
        "model": "deepseek-v4.1-flash",
        "messages": [{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{card_b64}"}},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{front_b64}"}},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{tag_b64}"}}
            ]
        }],
        "max_tokens": 2000
    }
    
    resp = requests.post(url, headers=headers, json=payload, timeout=40)
    choice = resp.json()["choices"][0]["message"]
    content = choice.get("content") or choice.get("reasoning_content") or ""
    print(f"=== {label} ({card_name}) ===")
    print(content)
