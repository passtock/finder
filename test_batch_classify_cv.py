import os, glob, json, requests, uuid, re
from PIL import Image
from test_cv_card import is_size_card
import base64, io

feynman_auth = os.path.expanduser('~/.feynman/agent/auth.json')
with open(feynman_auth, 'r', encoding='utf-8') as f:
    api_key = json.load(f)['opencode-go']['key']

folder = r'c:\Users\passp\Desktop\univercity\4-2\taobao_jackets\downloaded_jackets\item_1081695145771'
jpgs = sorted(glob.glob(os.path.join(folder, 'photo_*.jpg')))
candidates = [os.path.basename(p) for p in jpgs if is_size_card(p)[0]]

print(f'Candidates: {len(candidates)}')

def encode_thumb(img_path):
    with Image.open(img_path) as im:
        im = im.convert('RGB')
        im.thumbnail((300, 300))
        buf = io.BytesIO()
        im.save(buf, format='JPEG', quality=75)
        return base64.b64encode(buf.getvalue()).decode('utf-8')

batch = candidates[:15]
prompt = """다음 사진들 중에서 '손글씨 실측표 카드'(编号, 肩宽, 胸围 등이 인쇄된 흰 종이에 손글씨로 적힌 실측표)의 파일명만 JSON 리스트로 출력하세요. 세탁 라벨, 케어 라벨 등은 제외하세요.
예시: ["photo_002.jpg", "photo_009.jpg"]"""

content_list = [{'type': 'text', 'text': prompt}]

for fname in batch:
    content_list.append({'type': 'text', 'text': fname})
    b64 = encode_thumb(os.path.join(folder, fname))
    content_list.append({'type': 'image_url', 'image_url': {'url': f'data:image/jpeg;base64,{b64}'}})

url = 'https://opencode.ai/zen/go/v1/chat/completions'
headers = {
    'Authorization': f'Bearer {api_key}',
    'Content-Type': 'application/json',
    'x-opencode-session': f'ses_{uuid.uuid4().hex[:8]}'
}
payload = {
    'model': 'deepseek-v4.1-flash',
    'messages': [{'role': 'user', 'content': content_list}],
    'max_tokens': 500
}

resp = requests.post(url, headers=headers, json=payload, timeout=30)
print(resp.json()['choices'][0]['message'].get('content'))
