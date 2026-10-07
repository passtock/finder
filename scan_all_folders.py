import os, glob, sys
sys.stdout.reconfigure(encoding='utf-8')

base = r"c:\Users\passp\Desktop\univercity\4-2\taobao_jackets\downloaded_jackets"
folders = sorted([d for d in os.listdir(base) if os.path.isdir(os.path.join(base, d)) and d.startswith("item_")])

print(f"Total folders: {len(folders)}")
total_photos = 0
for f in folders:
    jpgs = glob.glob(os.path.join(base, f, "photo_*.jpg"))
    total_photos += len(jpgs)
    print(f"{f}: {len(jpgs)} photos")

print(f"\nTotal photos across all folders: {total_photos}")
