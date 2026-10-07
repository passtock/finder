import os, glob, sys
from PIL import Image
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')

folder = r"c:\Users\passp\Desktop\univercity\4-2\taobao_jackets\downloaded_jackets\item_1081695145771"
jpgs = sorted(glob.glob(os.path.join(folder, "photo_*.jpg")))

print(f"Total photos in item_1081695145771: {len(jpgs)}")

# Let's inspect the size card photos we identified visually from the user's screenshot:
# photo_002, photo_009, photo_016, photo_023, photo_031, photo_039, photo_048, photo_056, photo_064, photo_072, photo_080, photo_088, photo_096, photo_105, photo_112
sample_cards = ["photo_002.jpg", "photo_009.jpg", "photo_016.jpg", "photo_023.jpg", "photo_031.jpg"]

for name in sample_cards:
    p = os.path.join(folder, name)
    if os.path.exists(p):
        im = Image.open(p)
        arr = np.array(im)
        print(f"{name}: size={os.path.getsize(p)} bytes, dim={im.size}, mean_rgb={arr.mean(axis=(0,1))}")
