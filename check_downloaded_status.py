import os, glob, sys
sys.stdout.reconfigure(encoding='utf-8')

base = r"c:\Users\passp\Desktop\univercity\4-2\taobao_jackets\downloaded_jackets"
folders = sorted([d for d in os.listdir(base) if os.path.isdir(os.path.join(base, d)) and d.startswith("item_")])

print(f"Total folders found: {len(folders)}")
valid_folders = []
captcha_folders = []

for f in folders:
    fpath = os.path.join(base, f)
    photos = glob.glob(os.path.join(fpath, "photo_*"))
    info_path = os.path.join(fpath, "item_info.txt")
    title = ""
    if os.path.exists(info_path):
        with open(info_path, "r", encoding="utf-8", errors="ignore") as inf:
            for l in inf:
                if l.startswith("상품명:"): title = l.replace("상품명:", "").strip()
    
    cnt = len(photos)
    if cnt >= 5:
        valid_folders.append((f, cnt, title))
    else:
        captcha_folders.append((f, cnt, title))

print(f"\n--- VALID FOLDERS (>= 5 photos): {len(valid_folders)} ---")
for f, cnt, title in valid_folders:
    print(f"{f}: {cnt:3d} photos | {title}")

print(f"\n--- CAPTCHA / INCOMPLETE FOLDERS (< 5 photos): {len(captcha_folders)} ---")
for f, cnt, title in captcha_folders:
    print(f"{f}: {cnt:3d} photos | {title}")
