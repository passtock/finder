import os, json, requests, uuid, re, sys
from upgrade_master_jacket_catalog import encode_thumb, DOWNLOAD_DIR, api_key

folder_path = os.path.join(DOWNLOAD_DIR, 'item_1007701910240')
card_p = os.path.join(folder_path, 'photo_002.jpg')
label_p = os.path.join(folder_path, 'photo_006.jpg')
front_p = os.path.join(folder_path, 'photo_003.jpg')

prompt = 'Analyze jacket: respond with JSON {"brand": "...", "jacket_code": "..."}'
content_list = [{'type': 'text', 'text': prompt}]
for name, p in [('card', card_p), ('label', label_p), ('front', front_p)]:
    b64 = encode_thumb(p, 300)
    print(f"{name}: path={p}, exists={os.path.exists(p)}, b64_len={len(b64) if b64 else 0}")
    if b64:
        content_list.append({'type': 'text', 'text': name})
        content_list.append({'type': 'image_url', 'image_url': {'url': f'data:image/jpeg;base64,{b64}'}})

url = 'https://opencode.ai/zen/go/v1/chat/completions'
headers = {
    'Authorization': f'Bearer {api_key}',
    'Content-Type': 'application/json',
    'x-opencode-session': f'ses_test_{uuid.uuid4().hex[:8]}'
}
payload = {
    'model': 'deepseek-v4.1-flash',
    'messages': [{'role': 'user', 'content': content_list}],
    'max_tokens': 2000
}
try:
    resp = requests.post(url, headers=headers, json=payload, timeout=35)
    print('Status code:', resp.status_code)
    print('Resp text:', resp.text[:1000])
except Exception as e:
    print('Exception:', e)
