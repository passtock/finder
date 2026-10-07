import os, glob, sys, json, requests, base64, io, uuid, re
from PIL import Image

sys.stdout.reconfigure(encoding='utf-8')

feynman_auth = os.path.expanduser("~/.feynman/agent/auth.json")
with open(feynman_auth, "r", encoding="utf-8") as f:
    api_key = json.load(f)["opencode-go"]["key"]

def encode_thumb(img_path, max_dim=200):
    try:
        with Image.open(img_path) as im:
            im = im.convert("RGB")
            w, h = im.size
            if max(w, h) > max_dim:
                scale = max_dim / float(max(w, h))
                im = im.resize((int(w * scale), int(h * scale)), Image.Resampling.LANCZOS)
            buf = io.BytesIO()
            im.save(buf, format="JPEG", quality=70)
            return base64.b64encode(buf.getvalue()).decode("utf-8")
    except Exception:
        return None

def find_cards_in_folder(folder_path, batch_size=20):
    jpgs = sorted(glob.glob(os.path.join(folder_path, "photo_*.jpg")))
    # Filter out template banner (33084 bytes)
    valid_jpgs = [p for p in jpgs if os.path.getsize(p) != 33084]
    
    print(f"Scanning {os.path.basename(folder_path)}: {len(valid_jpgs)} photos...")
    all_cards = []
    
    for i in range(0, len(valid_jpgs), batch_size):
        batch = valid_jpgs[i:i + batch_size]
        content_list = [
            {"type": "text", "text": "아래 사진들 중에서 흰색 종이에 손글씨로 '编号', '肩宽', '胸围' 등이 적힌 실측표 카드 사진 파일명 목록만 JSON 배열로 출력하세요. 예: [\"photo_002.jpg\", \"photo_009.jpg\"]. 실측표가 하나도 없으면 [] 출력."}
        ]
        
        for p in batch:
            fname = os.path.basename(p)
            b64 = encode_thumb(p)
            if b64:
                content_list.append({"type": "text", "text": f"[{fname}]"})
                content_list.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}})
                
        url = "https://opencode.ai/zen/go/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "x-opencode-session": f"ses_batch_{uuid.uuid4().hex[:8]}"
        }
        payload = {
            "model": "deepseek-v4.1-flash",
            "messages": [{"role": "user", "content": content_list}],
            "max_tokens": 1000
        }
        
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=40)
            if resp.status_code == 200:
                c = resp.json()["choices"][0]["message"]
                txt = c.get("content") or c.get("reasoning_content") or ""
                m = re.search(r'\[(.*?)\]', txt, re.DOTALL)
                if m:
                    cards = json.loads(f"[{m.group(1)}]")
                    cards = [str(x).strip() for x in cards if str(x).strip().endswith('.jpg')]
                    all_cards.extend(cards)
                    print(f"  Batch {i//batch_size + 1}: found {cards}")
        except Exception as e:
            print(f"  Batch {i//batch_size + 1} error: {e}")
            
    return all_cards

folder = r"c:\Users\passp\Desktop\univercity\4-2\taobao_jackets\downloaded_jackets\item_1081695145771"
cards = find_cards_in_folder(folder)
print(f"\n[DONE] Total size cards detected in item_1081695145771: {len(cards)}")
print(cards)
