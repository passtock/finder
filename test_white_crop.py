import os, glob, sys
from PIL import Image
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')

folder = r"c:\Users\passp\Desktop\univercity\4-2\taobao_jackets\downloaded_jackets\item_1081695145771"
jpgs = sorted(glob.glob(os.path.join(folder, "photo_*.jpg")))[:25]

print("Index | Filename      | Center White % | Avg Center RGB | Is Known Card")
print("-" * 65)

known_cards = {"photo_002.jpg", "photo_009.jpg", "photo_016.jpg", "photo_023.jpg"}

for p in jpgs:
    fname = os.path.basename(p)
    if os.path.getsize(p) == 33084: # guide banner
        print(f"{fname:<15} | [GUIDE BANNER]")
        continue
    with Image.open(p) as im:
        w, h = im.size
        # center 50% box
        crop = im.crop((w*0.25, h*0.25, w*0.75, h*0.75))
        arr = np.array(crop)
        # white pixels where R>200, G>200, B>200
        white_mask = (arr[:,:,0] > 190) & (arr[:,:,1] > 190) & (arr[:,:,2] > 190)
        white_pct = (white_mask.sum() / (crop.size[0] * crop.size[1])) * 100
        mean_rgb = arr.mean(axis=(0,1))
        
        is_known = "★ CARD" if fname in known_cards else ""
        print(f"{fname:<15} | {white_pct:14.1f}% | {mean_rgb[0]:5.1f}, {mean_rgb[1]:5.1f}, {mean_rgb[2]:5.1f} | {is_known}")
