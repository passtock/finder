import os, glob, sys
from PIL import Image
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')

folder = r"c:\Users\passp\Desktop\univercity\4-2\taobao_jackets\downloaded_jackets\item_1081695145771"
jpgs = sorted(glob.glob(os.path.join(folder, "photo_*.jpg")))

print(f"Total photos: {len(jpgs)}")
candidates = []

for idx, p in enumerate(jpgs):
    if os.path.getsize(p) == 33084: # guide banner
        continue
    
    with Image.open(p) as im:
        w, h = im.size
        # Center crop (30% to 70% of w and h)
        crop = im.crop((int(w * 0.25), int(h * 0.25), int(w * 0.75), int(h * 0.75)))
        arr = np.array(crop)
        # White paper has high RGB: check percentage of pixels with R>170, G>170, B>170
        white_pixels = (arr[:,:,0] > 160) & (arr[:,:,1] > 160) & (arr[:,:,2] > 160)
        white_ratio = white_pixels.sum() / (crop.size[0] * crop.size[1])
        mean_rgb = arr.mean()
        
        # A size card occupies at least 20% white in the center
        if white_ratio >= 0.15 and mean_rgb >= 100:
            candidates.append((os.path.basename(p), white_ratio, mean_rgb))

print(f"Candidates found: {len(candidates)} / {len(jpgs)}")
for c in candidates:
    print(f"  {c[0]}: white_ratio={c[1]:.2f}, mean_rgb={c[2]:.1f}")
