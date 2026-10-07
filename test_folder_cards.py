import os, glob, sys
from PIL import Image
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')

base = r"c:\Users\passp\Desktop\univercity\4-2\taobao_jackets\downloaded_jackets"
test_folders = ["item_1081695145771", "item_1077196468019", "item_1076140587381", "item_811036195091"]

def inspect_folder_cards(folder_name):
    folder_path = os.path.join(base, folder_name)
    jpgs = sorted(glob.glob(os.path.join(folder_path, "photo_*.jpg")))
    print(f"\n[{folder_name}] Total: {len(jpgs)} photos")
    
    candidates = []
    for idx, p in enumerate(jpgs):
        if os.path.getsize(p) == 33084: # banner
            continue
        with Image.open(p) as im:
            w, h = im.size
            crop = im.crop((int(w * 0.25), int(h * 0.25), int(w * 0.75), int(h * 0.75)))
            arr = np.array(crop)
            white_pixels = (arr[:,:,0] > 160) & (arr[:,:,1] > 160) & (arr[:,:,2] > 160)
            white_ratio = white_pixels.sum() / (crop.size[0] * crop.size[1])
            mean_rgb = arr.mean()
            
            if white_ratio >= 0.20 and mean_rgb >= 110:
                candidates.append((idx, os.path.basename(p), white_ratio, mean_rgb))
    
    print(f"  Found {len(candidates)} candidate white card/tag photos:")
    for c in candidates[:15]:
        print(f"    - idx {c[0]:03d} ({c[1]}): white={c[2]:.2f}, rgb={c[3]:.1f}")

for f in test_folders:
    inspect_folder_cards(f)
