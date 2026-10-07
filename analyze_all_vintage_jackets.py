import sys
sys.stdout.reconfigure(encoding='utf-8')
import os
import glob
import re
import json
import pandas as pd
from rapidocr_onnxruntime import RapidOCR

engine = RapidOCR()

BASE_DIR = r"c:\Users\passp\Desktop\univercity\4-2\taobao_jackets"
DOWNLOAD_DIR = os.path.join(BASE_DIR, "downloaded_jackets")
OUTPUT_EXCEL = os.path.join(BASE_DIR, "taobao_leather_jackets_with_brands.xlsx")
OUTPUT_CSV = os.path.join(BASE_DIR, "taobao_leather_jackets_with_brands.csv")

TARGET_FOLDERS = [
    "item_1077196468019", # E1
    "item_811036195091",  # AC91
    "item_1080043211319", # Q118
    "item_1083932831050", # P306
    "item_1071816497728", # P1
    "item_1075139885104", # Q61
    "item_1078567805117", # Q91
    "item_1061875162656", # M1
    "item_1069955447343", # M41
    "item_1075374113206", # U61
    "item_1081695145771", # P211
    "item_1054456462690", # X31
]

KNOWN_BRANDS = [
    "L.L.Bean", "Schott", "Avirex", "GUESS", "BEAMS", "Comme Ca", "Franco Ferraro",
    "Polo Ralph Lauren", "Harley-Davidson", "Diesel", "Zara", "Massimo Dutti", "Wilson",
    "G-Star", "Alpha Industries", "AllSaints", "Levis", "Edwin", "Calvin Klein", "Armani",
    "Oakwood", "Redskins", "Chevignon", "Marlboro", "Vanson", "Aero Leather", "Belstaff",
    "Procyon", "Burberry", "Daks", "Aquascutum", "Timberland", "Nautica", "Tommy Hilfiger",
    "Gap", "Banana Republic", "Coach", "Hugo Boss", "Barbour", "Golden Bear", "Lewis Leathers"
]

def parse_size_card(lines):
    full_text = " ".join(lines)
    # 编号, 面料, 肩宽, 胸围, 衣长, 袖长
    card_info = {
        "code": "",
        "leather": "",
        "shoulder": "",
        "chest": "",
        "length": "",
        "sleeve": ""
    }
    
    # 编号
    m_code = re.search(r'编号\s*[:：]?\s*([A-Za-z0-9\-]+)', full_text)
    if m_code: card_info["code"] = m_code.group(1)
    
    # 面料
    m_mat = re.search(r'面料\s*[:：]?\s*([^\d\s,，]{2,8})', full_text)
    if m_mat: card_info["leather"] = m_mat.group(1)
    
    # 숫자 추출 (어깨, 가슴, 기장, 소매 순서로 기재되는 양식)
    # 양식: 肩宽 [N] 胸围 [N] 衣长 [N] 袖长 [N]
    m_sh = re.search(r'肩宽[^\d]*(\d{2,3})', full_text)
    if m_sh: card_info["shoulder"] = m_sh.group(1)
    
    m_ch = re.search(r'胸围[^\d]*(\d{2,3})', full_text)
    if m_ch: card_info["chest"] = m_ch.group(1)
    
    m_len = re.search(r'衣长[^\d]*(\d{2,3})', full_text)
    if m_len: card_info["length"] = m_len.group(1)
    
    m_sl = re.search(r'袖长[^\d]*(\d{2,3})', full_text)
    if m_sl: card_info["sleeve"] = m_sl.group(1)
    
    return card_info

def analyze_brand_from_texts(texts):
    combined = " ".join(texts)
    detected_brand = ""
    origin = ""
    leather_type = ""
    
    # Check known brands
    for b in KNOWN_BRANDS:
        if re.search(rf'\b{re.escape(b)}\b', combined, re.IGNORECASE):
            detected_brand = b
            break
            
    # Check origin
    if re.search(r'made\s*in\s*u\.?s\.?a|usa\b', combined, re.IGNORECASE):
        origin = "미국 (USA)"
    elif re.search(r'made\s*in\s*italy|italia\b', combined, re.IGNORECASE):
        origin = "이탈리아"
    elif re.search(r'made\s*in\s*korea|한국\b', combined, re.IGNORECASE):
        origin = "한국"
    elif re.search(r'made\s*in\s*japan\b', combined, re.IGNORECASE):
        origin = "일본"
    elif re.search(r'made\s*in\s*pakistan\b', combined, re.IGNORECASE):
        origin = "파키스탄"
    elif re.search(r'made\s*in\s*china\b', combined, re.IGNORECASE):
        origin = "중국"

    # Check leather
    if re.search(r'lambskin|羊皮|绵羊皮', combined, re.IGNORECASE):
        leather_type = "양가죽 (Lambskin)"
    elif re.search(r'cowhide|牛皮|소가죽|buffalo', combined, re.IGNORECASE):
        leather_type = "소가죽 (Cowhide)"
    elif re.search(r'pigskin|猪皮|돈모', combined, re.IGNORECASE):
        leather_type = "돼지가죽 (Pigskin)"
    elif re.search(r'goatskin|山羊皮', combined, re.IGNORECASE):
        leather_type = "산양가죽 (Goatskin)"
    elif re.search(r'suede|麂皮|翻毛皮', combined, re.IGNORECASE):
        leather_type = "스웨이드/스웨이드 가죽"

    return detected_brand, origin, leather_type

all_jackets = []

for folder_name in TARGET_FOLDERS:
    folder_path = os.path.join(DOWNLOAD_DIR, folder_name)
    if not os.path.exists(folder_path):
        continue
        
    info_file = os.path.join(folder_path, "item_info.txt")
    title = folder_name
    url = ""
    if os.path.exists(info_file):
        with open(info_file, "r", encoding="utf-8", errors="ignore") as inf:
            for l in inf:
                if l.startswith("상품명:"): title = l.replace("상품명:", "").strip()
                if l.startswith("URL:"): url = l.replace("URL:", "").strip()
                
    jpgs = sorted(glob.glob(os.path.join(folder_path, "photo_*.jpg")))
    print(f"\n[*] Processing {folder_name} ({len(jpgs)} photos) - {title[:35]}...", flush=True)
    
    # Track jacket blocks within this folder
    current_jacket = None
    jacket_index = 0
    
    for idx, f in enumerate(jpgs):
        # Progress indicator
        if (idx + 1) % 40 == 0:
            print(f"    - {idx+1}/{len(jpgs)} photos scanned...", flush=True)
            
        res, _ = engine(f)
        if not res:
            continue
            
        lines = [line[1] for line in res]
        all_text = " ".join(lines)
        
        # Check if size card
        if any(k in all_text for k in ["肩宽", "胸围", "衣长", "袖长"]) and ("编号" in all_text or "cm" in all_text or "平铺" in all_text):
            if current_jacket:
                all_jackets.append(current_jacket)
                
            jacket_index += 1
            card_info = parse_size_card(lines)
            code = card_info["code"] or f"{folder_name.replace('item_', '')}-{jacket_index}"
            
            current_jacket = {
                "folder": folder_name,
                "item_title": title,
                "jacket_code": code,
                "size_card_photo": os.path.basename(f),
                "leather_from_card": card_info["leather"],
                "shoulder_cm": card_info["shoulder"],
                "chest_cm": card_info["chest"],
                "length_cm": card_info["length"],
                "sleeve_cm": card_info["sleeve"],
                "label_texts": [],
                "detected_brand": "",
                "detected_origin": "",
                "detected_leather": ""
            }
        else:
            if current_jacket:
                # Accumulate tag texts for this jacket
                # Check if tag/label text
                is_label = any(k in all_text.lower() for k in ["made in", "leather", "since", "size", "100%", "dry clean", "pelle", "cuir"]) or any(b.lower() in all_text.lower() for b in KNOWN_BRANDS)
                if is_label or len(lines) <= 10:
                    current_jacket["label_texts"].extend(lines)
                    b, orig, leath = analyze_brand_from_texts(current_jacket["label_texts"])
                    if b and not current_jacket["detected_brand"]: current_jacket["detected_brand"] = b
                    if orig and not current_jacket["detected_origin"]: current_jacket["detected_origin"] = orig
                    if leath and not current_jacket["detected_leather"]: current_jacket["detected_leather"] = leath

    if current_jacket:
        all_jackets.append(current_jacket)

print(f"\n==========================================")
print(f"[+] Total individual jackets parsed: {len(all_jackets)}")

# Build final DataFrame
records = []
for seq, j in enumerate(all_jackets, 1):
    brand = j["detected_brand"] if j["detected_brand"] else "빈티지 / 브랜드 태그 확인중"
    leather = j["detected_leather"] if j["detected_leather"] else (j["leather_from_card"] if j["leather_from_card"] else "가죽")
    origin = j["detected_origin"] if j["detected_origin"] else "불명"
    
    records.append({
        "순번": seq,
        "상품폴더": j["folder"],
        "자켓번호": j["jacket_code"],
        "판독브랜드": brand,
        "가죽종류": leather,
        "원산지": origin,
        "어깨(cm)": j["shoulder_cm"] or "-",
        "가슴(cm)": j["chest_cm"] or "-",
        "기장(cm)": j["length_cm"] or "-",
        "소매(cm)": j["sleeve_cm"] or "-",
        "실측표사진": j["size_card_photo"],
        "상품명": j["item_title"]
    })

df = pd.DataFrame(records)
df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")
df.to_excel(OUTPUT_EXCEL, index=False)
print(f"[✓] Successfully saved to {OUTPUT_EXCEL} and {OUTPUT_CSV}")
