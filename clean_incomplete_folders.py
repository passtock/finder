import os, shutil, glob

base = r"c:\Users\passp\Desktop\univercity\4-2\taobao_jackets\downloaded_jackets"
folders = sorted([d for d in os.listdir(base) if os.path.isdir(os.path.join(base, d)) and d.startswith("item_")])

deleted = []
for f in folders:
    fpath = os.path.join(base, f)
    photos = glob.glob(os.path.join(fpath, "photo_*"))
    if len(photos) < 5:
        shutil.rmtree(fpath)
        deleted.append((f, len(photos)))

print(f"Removed {len(deleted)} incomplete folders (captcha interrupted):")
for f, cnt in deleted:
    print(f" - {f} ({cnt} photos)")
