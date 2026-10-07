import os, glob, sys, json, requests, base64, io, uuid
from PIL import Image

sys.stdout.reconfigure(encoding='utf-8')

feynman_auth = os.path.expanduser("~/.feynman/agent/auth.json")
with open(feynman_auth, "r", encoding="utf-8") as f:
    api_key = json.load(f)["opencode-go"]["key"]

def encode_image(img_path, max_dim=400):
    try:
        with Image.open(img_path) as im:
            im = im.convert("RGB")
            w, h = im.size
            if max(w, h) > max_dim:
                scale = max_dim / float(max(w, h))
                im = im.resize((int(w * scale), int(h * scale)), Image.Resampling.LANCZOS)
            buf = io.BytesIO()
            im.save(buf, format="JPEG", quality=75)
            return base64.b64encode(buf.getvalue()).decode("utf-8")
    except Exception:
        return None

# Test: Send a grid/batch of 10 photos to OpenCode Go and ask which indices are size cards!
folder = r"c:\Users\passp\Desktop\univercity\4-2\taobao_jackets\downloaded_jackets\item_1081695145771"
jpgs = sorted(glob.glob(os.path.join(folder, "photo_*.jpg")))[:20]

content_list = [
    {"type": "text", "text": "아래 20장의 사진 중, 손으로 치수가 적힌 '화이트 실측표 카드(编号, 肩宽, 胸围 등)' 사진의 번호(photo_XXX.jpg) 목록만 JSON 리스트로 출력하세요. 예: [\"photo_002.jpg\", \"photo_009.jpg\", \"photo_016.jpg\"]"}
]

for p in jpgs:
    fname = os.path.basename(p)
    b64 = encode_image(p, max_dim=250)
    if b64:
        content_list.append({"type": "text", "text": f"[{fname}]"})
        content_list.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}})

url = "https://opencode.ai/zen/go/v1/chat/completions"
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json",
    "x-opencode-session": f"ses_test_batch_{uuid.uuid4().hex[:8]}"
}
payload = {
    "model": "deepseek-v4.1-flash",
    "messages": [{"role": "user", "content": content_list}],
    "max_tokens": 1000
}

resp = requests.post(url, headers=headers, json=payload, timeout=40)
print("Status:", resp.status_code)
c = resp.json()["choices"][0]["message"]
print("Content:\n", c.get("content"))
print("Reasoning snippet:\n", (c.get("reasoning_content") or "")[:200])
