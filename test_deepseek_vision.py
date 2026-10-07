# -*- coding: utf-8 -*-
import sys
import os
import json
import requests
import uuid
import base64
import io
from PIL import Image

sys.stdout.reconfigure(encoding='utf-8')

p = os.path.expanduser('~/.feynman/agent/auth.json')
data = json.load(open(p, 'r', encoding='utf-8'))
item = data.get('opencode-go') or data.get('opencodego')
api_key = item.get('key') if isinstance(item, dict) else item

def get_b64(path):
    with Image.open(path) as img:
        img.thumbnail((600, 600))
        buf = io.BytesIO()
        img.save(buf, format='JPEG', quality=80)
        return base64.b64encode(buf.getvalue()).decode('utf-8')

b64_card = get_b64(r'downloaded_jackets\item_1077196468019\photo_002.jpg')
b64_label = get_b64(r'downloaded_jackets\item_1077196468019\photo_007.jpg')

url = 'https://opencode.ai/zen/go/v1/chat/completions'
headers = {
    'Authorization': f'Bearer {api_key}',
    'Content-Type': 'application/json',
    'x-opencode-session': f'ses_{uuid.uuid4().hex[:12]}'
}
prompt = (
    "두 사진은 빈티지 가죽자켓의 실측표 카드와 라벨입니다. "
    "JSON 형식으로만 추출해주세요:\n"
    "{\"code\": \"...\", \"brand\": \"...\", \"leather\": \"...\", \"origin\": \"...\", "
    "\"shoulder\": \"...\", \"chest\": \"...\", \"length\": \"...\", \"sleeve\": \"...\"}"
)
payload = {
    'model': 'deepseek-v4.1-flash',
    'messages': [{
        'role': 'user',
        'content': [
            {'type': 'text', 'text': prompt},
            {'type': 'image_url', 'image_url': {'url': f'data:image/jpeg;base64,{b64_card}'}},
            {'type': 'image_url', 'image_url': {'url': f'data:image/jpeg;base64,{b64_label}'}}
        ]
    }],
    'max_tokens': 4000
}

resp = requests.post(url, headers=headers, json=payload, timeout=60)
msg = resp.json()['choices'][0]['message']
print(msg.get('content'))
