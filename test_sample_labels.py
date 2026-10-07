import os, glob, json, requests, uuid, base64, io, re
from PIL import Image

feynman_auth = os.path.expanduser('~/.feynman/agent/auth.json')
with open(feynman_auth, 'r', encoding='utf-8') as f:
    api_key = json.load(f)['opencode-go']['key']

def encode_thumb(img_path):
    with Image.open(img_path) as im:
        im = im.convert('RGB')
        im.thumbnail((250, 250))
        buf = io.BytesIO()
        im.save(buf, format='JPEG', quality=75)
        return base64.b64encode(buf.getvalue()).decode('utf-8')

with open('analyzed_jackets_checkpoint.json', 'r', encoding='utf-8') as f:
    checkpoint = json.load(f)

# Pick 5 jackets across different folders
test_keys = [
    'item_1054456462690_photo_002.jpg', # X31
    'item_1061875162656_photo_002.jpg', # M1
    'item_1077196468019_photo_002.jpg', # E1
    'item_1081695145771_photo_002.jpg', # P211
    'item_1075139885104_photo_002.jpg', # Q61
]

for k in test_keys:
    data = checkpoint[k]
    fld = os.path.join(r'downloaded_jackets', data['folder'])
    # extract range
    rng_str = data['photo_range']
    m = re.findall(r'photo_\d+\.jpg', rng_str)
    all_jpgs = sorted(glob.glob(os.path.join(fld, 'photo_*.jpg')))
    fnames = [os.path.basename(p) for p in all_jpgs]
    idx1 = fnames.index(m[0])
    idx2 = fnames.index(m[1])
    jkt_photos = fnames[idx1:idx2+1]
    
    # Candidates are photos from index 3 onwards
    candidates = jkt_photos[3:] if len(jkt_photos) > 4 else jkt_photos[2:]
    
    prompt = """다음 사진들 중에서 자켓의 '브랜드 목 라벨'(브랜드 로고가 적힌 라벨 또는 안감 상표) 사진 1개의 파일명만 JSON으로 출력하세요.
예시: {"brand_label_photo": "photo_007.jpg"}"""
    
    content_list = [{'type': 'text', 'text': prompt}]
    for c in candidates:
        content_list.append({'type': 'text', 'text': c})
        b64 = encode_thumb(os.path.join(fld, c))
        if b64:
            content_list.append({'type': 'image_url', 'image_url': {'url': f'data:image/jpeg;base64,{b64}'}})
            
    url = 'https://opencode.ai/zen/go/v1/chat/completions'
    headers = {'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json', 'x-opencode-session': f'ses_{uuid.uuid4().hex[:8]}'}
    payload = {'model': 'deepseek-v4.1-flash', 'messages': [{'role': 'user', 'content': content_list}], 'max_tokens': 500}
    
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=30)
        c = resp.json()['choices'][0]['message']
        txt = c.get('content') or c.get('reasoning_content') or ''
        m_res = re.search(r'photo_\d+\.jpg', txt)
        print(f"Jacket {data['folder']} {data.get('jacket_code')}: candidates {candidates} -> LABEL: {m_res.group(0) if m_res else 'None'}")
    except Exception as e:
        print("Err:", e)
