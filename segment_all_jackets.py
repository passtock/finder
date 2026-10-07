import os, glob, sys, json, requests, uuid, re
from PIL import Image
from test_cv_card import is_size_card
import base64, io

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = r"c:\Users\passp\Desktop\univercity\4-2\taobao_jackets"
DOWNLOAD_DIR = os.path.join(BASE_DIR, "downloaded_jackets")
CACHE_FILE = os.path.join(BASE_DIR, "detected_cards_cache.json")

feynman_auth = os.path.expanduser('~/.feynman/agent/auth.json')
with open(feynman_auth, 'r', encoding='utf-8') as f:
    api_key = json.load(f)['opencode-go']['key']

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

def verify_cards_with_llm(folder_path, candidate_fnames):
    if not candidate_fnames:
        return []
    
    # If candidate is only photo_002.jpg, it is almost certainly the size card
    if len(candidate_fnames) == 1 and candidate_fnames[0] == "photo_002.jpg":
        return candidate_fnames

    verified = []
    # Send candidates in batches of up to 15
    for i in range(0, len(candidate_fnames), 15):
        batch = candidate_fnames[i:i + 15]
        prompt = (
            "다음 사진들 중에서 '손글씨 실측표 카드'(编号, 肩宽, 胸围 등이 인쇄된 흰 종이 양식에 손글씨로 숫자가 적힌 실측표)의 파일명만 JSON 리스트로 출력하세요. "
            "세탁 라벨, 옷 디테일, 브랜드 택 등은 제외하세요.\n"
            "예시: [\"photo_002.jpg\", \"photo_009.jpg\"]"
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
            'max_tokens': 600
        }
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=35)
            if resp.status_code == 200:
                c = resp.json()['choices'][0]['message']
                txt = c.get('content') or c.get('reasoning_content') or ''
                m = re.search(r'\[(.*?)\]', txt, re.DOTALL)
                if m:
                    res_list = json.loads(f'[{m.group(1)}]')
                    valid_fnames = [str(x).strip() for x in res_list if str(x).strip().endswith('.jpg') and str(x).strip() in batch]
                    verified.extend(valid_fnames)
                else:
                    print(f"Warning: no json list in response: {txt[:100]}")
            else:
                print(f"API error: {resp.status_code}")
        except Exception as e:
            print(f"Request exception: {e}")
            
    # Always ensure photo_002.jpg is included if it was in candidates and looks like card
    if "photo_002.jpg" in candidate_fnames and "photo_002.jpg" not in verified:
        verified.insert(0, "photo_002.jpg")
        
    return sorted(list(set(verified)))

def find_all_jacket_segments():
    # Check cache
    cache = {}
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                cache = json.load(f)
        except Exception:
            cache = {}

    folders = sorted(glob.glob(os.path.join(DOWNLOAD_DIR, "*")))
    all_segments = []

    for fld in folders:
        fld_name = os.path.basename(fld)
        jpgs = sorted(glob.glob(os.path.join(fld, "photo_*.jpg")))
        if not jpgs:
            continue
            
        print(f"\n==========================================")
        print(f"[*] Processing {fld_name} ({len(jpgs)} photos)...")

        # 1. Get confirmed size cards
        if fld_name in cache:
            confirmed_cards = cache[fld_name]
            print(f"  [Cache] Loaded {len(confirmed_cards)} confirmed cards: {confirmed_cards[:5]}...")
        else:
            if len(jpgs) <= 18:
                # Single jacket folder
                confirmed_cards = ["photo_002.jpg"] if any(os.path.basename(j) == "photo_002.jpg" for j in jpgs) else [os.path.basename(jpgs[0])]
                print(f"  [Single Item] Size card: {confirmed_cards}")
            else:
                # Multi jacket folder: Filter candidates by CV
                candidates = [os.path.basename(p) for p in jpgs if is_size_card(p)[0]]
                if "photo_002.jpg" not in candidates and any(os.path.basename(j) == "photo_002.jpg" for j in jpgs):
                    candidates.insert(0, "photo_002.jpg")
                print(f"  [CV Filter] Found {len(candidates)} candidates: {candidates[:6]}...")
                confirmed_cards = verify_cards_with_llm(fld, candidates)
                print(f"  [LLM Verified] {len(confirmed_cards)} confirmed size cards!")
                
            cache[fld_name] = confirmed_cards
            with open(CACHE_FILE, "w", encoding="utf-8") as cf:
                json.dump(cache, cf, ensure_ascii=False, indent=2)

        # 2. Build jacket segments from confirmed size cards
        # Map filenames to index
        fname_list = [os.path.basename(p) for p in jpgs]
        
        for idx, card_fname in enumerate(confirmed_cards):
            card_idx = fname_list.index(card_fname) if card_fname in fname_list else -1
            if card_idx == -1:
                continue
                
            # Next card index
            if idx + 1 < len(confirmed_cards):
                next_card_fname = confirmed_cards[idx + 1]
                next_card_idx = fname_list.index(next_card_fname) if next_card_fname in fname_list else len(fname_list)
            else:
                next_card_idx = len(fname_list)
                
            jacket_photos = fname_list[card_idx:next_card_idx]
            
            # Identify front photo (first photo after card)
            front_photo = jacket_photos[1] if len(jacket_photos) > 1 else card_fname
            
            # Identify label/detail photo (typically 4th, 5th, or last photos)
            label_photo = jacket_photos[-1] if len(jacket_photos) > 2 else front_photo
            for candidate_label in jacket_photos[2:]:
                # Pick a candidate label if available
                label_photo = candidate_label
                break
                
            seg_info = {
                "folder": fld_name,
                "jacket_index": idx + 1,
                "total_in_folder": len(confirmed_cards),
                "card_photo": card_fname,
                "front_photo": front_photo,
                "label_photo": label_photo,
                "photo_range": f"{jacket_photos[0]} ~ {jacket_photos[-1]} ({len(jacket_photos)}장)",
                "all_photos": jacket_photos
            }
            all_segments.append(seg_info)
            print(f"  Jacket #{idx+1}: {card_fname} | Front: {front_photo} | Range: {seg_info['photo_range']}")

    print(f"\n==========================================")
    print(f"[🎉] Total segments across all 26 folders: {len(all_segments)}")
    return all_segments

if __name__ == "__main__":
    segments = find_all_jacket_segments()
