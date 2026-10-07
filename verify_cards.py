import os, glob, sys, json, re, io, base64, requests
import pandas as pd
from PIL import Image

sys.stdout.reconfigure(encoding='utf-8')

base = r"c:\Users\passp\Desktop\univercity\4-2\taobao_jackets\downloaded_jackets"
csv_path = r"c:\Users\passp\Desktop\univercity\4-2\taobao_jackets\taobao_leather_jackets_with_brands.csv"
df = pd.read_csv(csv_path, encoding='utf-8-sig')

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
    except Exception:
        return None

print(f"{'순번':<4} | {'폴더':<18} | {'CSV품번':<8} | {'실측사진':<12} | {'카드 실제 적힌 编号'}")
print("-" * 75)

for idx, row in df.iterrows():
    folder = row['상품폴더']
    fpath = os.path.join(base, folder)
    card_name = row['실측사진']
    card_path = os.path.join(fpath, card_name)
    if not os.path.exists(card_path):
        print(f"{row['순번']:<4} | {folder:<18} | {row['자켓품번']:<8} | {card_name:<12} | [파일 없음!]")
        continue
    
    # Let's inspect the card with a fast vision check
    b64 = encode_image(card_path)
    prompt = "이 사진은 빈티지 의류 실측표 카드입니다. 상단 '编号' 뒤에 적힌 손글씨 품번/코드(예: E1, V80, 91 등) 딱 그것만 단답으로 적어주세요. 없거나 템플릿이면 'TEMPLATE'이라고 적으세요."
    
    url = "https://opencode.ai/zen/go/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "x-opencode-session": f"ses_check_{idx}"
    }
    payload = {
        "model": "deepseek-v4.1-flash",
        "messages": [{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}
            ]
        }],
        "max_tokens": 1000
    }
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=20)
        c = resp.json()["choices"][0]["message"]
        txt = (c.get("content") or c.get("reasoning_content") or "").strip().split("\n")[-1].replace("`", "").strip()
        print(f"{row['순번']:<4} | {folder:<18} | {row['자켓품번']:<8} | {card_name:<12} | {txt}")
    except Exception as e:
        print(f"{row['순번']:<4} | {folder:<18} | {row['자켓품번']:<8} | {card_name:<12} | [오류: {e}]")
