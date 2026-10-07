import os, sys, re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

sys.stdout.reconfigure(encoding='utf-8')

opt = Options()
opt.add_experimental_option('debuggerAddress', '127.0.0.1:9222')
driver = webdriver.Chrome(options=opt)

BASE_DIR = r"c:\Users\passp\Desktop\univercity\4-2\taobao_jackets"
OUTPUT_DIR = os.path.join(BASE_DIR, "downloaded_jackets")

def is_strictly_mens_longsleeve_jacket(title):
    # 여성 전용 제외
    if any(k in title for k in ["女款", "女士", "女装", "短裙", "半身裙", "女西装", "女式"]):
        return False, "여성 전용 상품 제외"
    if "女" in title and "男" not in title:
        return False, "여성 표기 상품 제외"

    # 조끼 / 민소매 / 반팔 제외 (긴팔만 허용)
    if any(k in title for k in ["马甲", "马夹", "背心", "无袖", "短袖"]):
        return False, "조끼/민소매/반팔 제외"

    # 롱코트 / 트렌치코트 / 바지 / 치마 제외
    if any(k in title for k in ["大衣", "风衣", "长款", "皮裤", "裤子", "短裤"]):
        return False, "코트/바지 형태 제외"

    # 필수 가죽자켓 키워드
    jacket_keywords = ["皮衣", "皮夹克", "夹克", "机车", "飞行员", "A2", "G1", "西服", "西装", "外套"]
    if not any(k in title for k in jacket_keywords):
        return False, "가죽자켓 키워드 미포함"

    return True, "통과"

cards = driver.find_elements(By.CSS_SELECTOR, "[class*='cardContainer']")
print(f"Total cards on page: {len(cards)}")

# Check existing items in downloaded_jackets
existing_folders = set()
for d in os.listdir(OUTPUT_DIR):
    folder = os.path.join(OUTPUT_DIR, d)
    if os.path.isdir(folder):
        photos = [f for f in os.listdir(folder) if f.startswith("photo_")]
        if len(photos) >= 50:
            existing_folders.add(d)

print(f"Existing completed jacket folders (>= 50 photos): {len(existing_folders)} ({existing_folders})")

target_items = []
for idx, c in enumerate(cards):
    title = c.find_element(By.CSS_SELECTOR, "[class*='title']").text.strip().replace("\n", " ")
    
    # get item link / id if possible
    href = ""
    try:
        a_tag = c.find_element(By.TAG_NAME, "a")
        href = a_tag.get_attribute("href") or ""
    except Exception:
        pass
    
    ok, reason = is_strictly_mens_longsleeve_jacket(title)
    if ok:
        target_items.append((idx, title, href))

print(f"\nFiltered target men's jackets: {len(target_items)}")
for seq, (idx, title, href) in enumerate(target_items, 1):
    print(f"[{seq:02d}] Card #{idx+1:03d} | {title} | {href[:40] if href else 'no link'}")
