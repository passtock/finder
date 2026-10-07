import os, glob, sys, json, requests, base64, io, uuid, re
from PIL import Image
import openpyxl
from openpyxl.drawing.image import Image as XLImage
from openpyxl.styles import Alignment, Font, PatternFill, Border, Side

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = r"c:\Users\passp\Desktop\univercity\4-2\taobao_jackets"
THUMB_DIR = os.path.join(BASE_DIR, "thumbnails")
os.makedirs(THUMB_DIR, exist_ok=True)

feynman_auth = os.path.expanduser("~/.feynman/agent/auth.json")
with open(feynman_auth, "r", encoding="utf-8") as f:
    api_key = json.load(f)["opencode-go"]["key"]

def encode_image(img_path, max_dim=450):
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

def is_bright_candidate(img_path):
    if os.path.getsize(img_path) == 33084: # banner template
        return False
    try:
        with Image.open(img_path) as im:
            w, h = im.size
            crop = im.crop((int(w * 0.25), int(h * 0.25), int(w * 0.75), int(h * 0.75)))
            import numpy as np
            arr = np.array(crop)
            white_pixels = (arr[:,:,0] > 160) & (arr[:,:,1] > 160) & (arr[:,:,2] > 160)
            white_ratio = white_pixels.sum() / (crop.size[0] * crop.size[1])
            mean_rgb = arr.mean()
            return (white_ratio >= 0.20 and mean_rgb >= 115)
    except Exception:
        return False

def analyze_jacket_segment(card_path, front_path, label_path):
    card_b64 = encode_image(card_path)
    front_b64 = encode_image(front_path) if front_path and os.path.exists(front_path) else None
    label_b64 = encode_image(label_path) if label_path and os.path.exists(label_path) else None
    
    if not card_b64:
        return None

    prompt = (
        "제공된 사진들은 1벌의 빈티지 가죽자켓(실측표 카드, 자켓 정면, 라벨)입니다.\n"
        "장황한 설명 없이 아래 JSON 포맷으로만 응답해주세요:\n"
        "```json\n"
        "{\n"
        '  "is_size_card": true,\n'
        '  "jacket_code": "실측지 상단 编号 (예: P211, P212 등)",\n'
        '  "brand": "라벨에 적힌 정확한 브랜드명 영문/한글 (미상일 경우 빈티지 오리지널)",\n'
        '  "leather_type": "가죽 종류 (양가죽, 소가죽, 사슴가죽 등)",\n'
        '  "origin": "원산지 (미국, 이탈리아, 일본, 한국 등, 불명 시 불명)",\n'
        '  "shoulder_cm": "어깨 실측 숫자",\n'
        '  "chest_cm": "가슴 실측 숫자",\n'
        '  "length_cm": "총기장 실측 숫자",\n'
        '  "sleeve_cm": "소매길이 실측 숫자"\n'
        "}\n"
        "```\n"
        "만약 첫 번째 사진이 실측표 카드가 아니라 세탁탭/케어라벨이나 옷 사진이면 {\"is_size_card\": false} 로만 응답하세요."
    )
    
    content_list = [{"type": "text", "text": prompt}]
    content_list.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{card_b64}"}})
    if front_b64:
        content_list.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{front_b64}"}})
    if label_b64:
        content_list.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{label_b64}"}})

    url = "https://opencode.ai/zen/go/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "x-opencode-session": f"ses_seg_{uuid.uuid4().hex[:8]}"
    }
    payload = {
        "model": "deepseek-v4.1-flash",
        "messages": [{"role": "user", "content": content_list}],
        "max_tokens": 1500
    }
    
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=35)
        if resp.status_code == 200:
            c = resp.json()["choices"][0]["message"]
            txt = c.get("content") or c.get("reasoning_content") or ""
            m = re.search(r'```json\s*(\{.*?\})\s*```', txt, re.DOTALL)
            if not m:
                m = re.search(r'(\{.*?"is_size_card".*?\})', txt, re.DOTALL)
            if m:
                return json.loads(m.group(1))
    except Exception as e:
        print(f"Error calling API: {e}")
    return None

print("Segmenter module ready.")
