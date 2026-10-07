import os, json, requests, uuid, base64, io, re
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

folder = r'downloaded_jackets\item_1077196468019'
photos = [f'photo_{i:03d}.jpg' for i in range(3, 11)]

prompt = """아래 사진들 중에서 자켓의 '목 브랜드 라벨'(Brand Logo Tag, Neck Label, 목 안쪽 브랜드 상표 또는 케어라벨) 사진 파일명을 찾아주세요.
가장 선명한 브랜드 라벨 사진 1개의 파일명만 JSON으로 출력하세요.
예시: {"label_photo": "photo_007.jpg"}"""

content_list = [{'type': 'text', 'text': prompt}]

for p in photos:
    content_list.append({'type': 'text', 'text': p})
    b64 = encode_thumb(os.path.join(folder, p))
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
    'max_tokens': 200
}

resp = requests.post(url, headers=headers, json=payload, timeout=30)
txt = resp.json()['choices'][0]['message'].get('content')
print("Response:", txt)
