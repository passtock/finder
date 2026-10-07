import os, glob, sys
from PIL import Image

sys.stdout.reconfigure(encoding='utf-8')

base = r"c:\Users\passp\Desktop\univercity\4-2\taobao_jackets\downloaded_jackets"
folders = sorted([d for d in os.listdir(base) if os.path.isdir(os.path.join(base, d)) and d.startswith("item_")])

print(f"Checking {len(folders)} folders...")

for f in folders[:10]:
    fpath = os.path.join(base, f)
    info_path = os.path.join(fpath, "item_info.txt")
    title = ""
    if os.path.exists(info_path):
        for line in open(info_path, encoding='utf-8', errors='ignore'):
            if line.startswith("상품명:"): title = line.replace("상품명:", "").strip()
    
    jpgs = sorted(glob.glob(os.path.join(fpath, "*.jpg")))
    print(f"\n[{f}] Title: {title}")
    for p in jpgs[:5]:
        sz = os.path.getsize(p)
        try:
            with Image.open(p) as im:
                w, h = im.size
                print(f"  - {os.path.basename(p)}: {sz} bytes ({w}x{h})")
        except Exception as e:
            print(f"  - {os.path.basename(p)}: {sz} bytes (error: {e})")
