import os, glob, sys, json, requests, uuid, re, cv2
from PIL import Image
import base64, io

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = r"c:\Users\passp\Desktop\univercity\4-2\taobao_jackets"
DOWNLOAD_DIR = os.path.join(BASE_DIR, "downloaded_jackets")
CACHE_FILE = os.path.join(BASE_DIR, "detected_cards_cache_v2.json")

feynman_auth = os.path.expanduser('~/.feynman/agent/auth.json')
with open(feynman_auth, 'r', encoding='utf-8') as f:
    api_key = json.load(f)['opencode-go']['key']

def is_size_card_candidate(img_path):
    if os.path.getsize(img_path) == 33084: # guide banner
        return False
    try:
        img = cv2.imread(img_path)
        if img is None: return False
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 170, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        total = img.shape[0] * img.shape[1]
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if 0.28 * total < area < 0.90 * total:
                x, y, w, h = cv2.boundingRect(cnt)
                aspect = float(h) / w
                cx = x + w / 2.0
                if 0.65 <= aspect <= 3.2 and 0.15 * img.shape[1] < cx < 0.85 * img.shape[1]:
                    return True
        return False
    except Exception:
        return False

def encode_thumb(img_path, max_dim=250):
    try:
        with Image.open(img_path) as im:
            im = im.convert('RGB')
            w, h = im.size
            if max(w, h) > max_dim:
                scale = max_dim / float(max(w, h))
                im = im.resize((int(w * scale), int(h * scale)), Image.Resampling.LANCZOS)
            buf = io.BytesIO()
            im.save(buf, format='JPEG', quality=75)
            return base64.b64encode(buf.getvalue()).decode('utf-8')
    except Exception:
        return None

def verify_candidates(folder_path, candidate_fnames):
    if not candidate_fnames:
        return []
    
    verified = []
    # Send in batches of 12
    for i in range(0, len(candidate_fnames), 12):
        batch = candidate_fnames[i:i + 12]
        prompt = (
            "다음 사진들 중에서 '손글씨 실측표 카드'(编号, 肩宽, 胸围 등이 인쇄된 흰 종이 양식에 손글씨로 숫자가 적힌 실측표)의 파일명만 JSON 리스트로 출력하세요. "
            "세탁 라벨, 옷 디테일, 브랜드 택 등은 절대 제외하세요.\n"
            "형식: [\"photo_002.jpg\", \"photo_009.jpg\"]"
        )
        content_list = [{'type': 'text', 'text': prompt}]
        for fname in batch:
            p = os.path.join(folder_path, fname)
            b64 = encode_thumb(p)
            if b64:
                content_list.append({'type': 'text', 'text': fname})
                content_list.append({'type': 'image_url', 'image_url': {'url': f'data:image/jpeg;base64,{b64}'}})
        
        url = 'https://opencode.ai/zen/go/v1/chat/completions'
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
            'x-opencode-session': f'ses_card_{uuid.uuid4().hex[:8]}'
        }
        payload = {
            'model': 'deepseek-v4.1-flash',
            'messages': [{'role': 'user', 'content': content_list}],
            'max_tokens': 1200
        }
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=35)
            if resp.status_code == 200:
                c = resp.json()['choices'][0]['message']
                txt = c.get('content') or c.get('reasoning_content') or ''
                matches = re.findall(r'photo_\d+\.jpg', txt)
                valid = [m for m in matches if m in batch]
                verified.extend(valid)
        except Exception as e:
            print(f"Request error: {e}")
            
    if "photo_002.jpg" in candidate_fnames and "photo_002.jpg" not in verified:
        verified.insert(0, "photo_002.jpg")
        
    return sorted(list(set(verified)))

def run():
    folders = sorted(glob.glob(os.path.join(DOWNLOAD_DIR, "*")))
    cache = {}
    total_jackets = 0

    for fld in folders:
        fld_name = os.path.basename(fld)
        jpgs = sorted(glob.glob(os.path.join(fld, "photo_*.jpg")))
        if not jpgs: continue

        if len(jpgs) <= 18:
            confirmed = ["photo_002.jpg"] if any(os.path.basename(j) == "photo_002.jpg" for j in jpgs) else [os.path.basename(jpgs[0])]
        else:
            candidates = [os.path.basename(p) for p in jpgs if is_size_card_candidate(p)]
            if "photo_002.jpg" not in candidates and any(os.path.basename(j) == "photo_002.jpg" for j in jpgs):
                candidates.insert(0, "photo_002.jpg")
            confirmed = verify_candidates(fld, candidates)

        cache[fld_name] = confirmed
        total_jackets += len(confirmed)
        print(f"[{fld_name}] {len(jpgs)} photos -> {len(confirmed)} jackets: {confirmed[:4]}...", flush=True)

    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

    print(f"\n==========================================")
    print(f"Total jackets across all folders: {total_jackets}")

if __name__ == "__main__":
    run()
