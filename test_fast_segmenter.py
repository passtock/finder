import os, glob, sys, time
from PIL import Image
import numpy as np
from rapidocr_onnxruntime import RapidOCR

sys.stdout.reconfigure(encoding='utf-8')

ocr = RapidOCR()
folder = r"c:\Users\passp\Desktop\univercity\4-2\taobao_jackets\downloaded_jackets\item_1081695145771"
jpgs = sorted(glob.glob(os.path.join(folder, "photo_*.jpg")))

print(f"Scanning all {len(jpgs)} photos in item_1081695145771...")
t0 = time.time()

size_cards = []

for idx, p in enumerate(jpgs):
    sz = os.path.getsize(p)
    if sz == 33084: # guide banner
        continue
    
    # Fast brightness check on center box
    with Image.open(p) as im:
        w, h = im.size
        crop = im.crop((w*0.25, h*0.25, w*0.75, h*0.75))
        arr = np.array(crop)
        mean_rgb = arr.mean()
        if mean_rgb < 90: # dark jacket, skip OCR completely!
            continue
    
    # Run OCR on candidate bright images
    res, _ = ocr(p)
    if not res: continue
    full_text = "".join([r[1] for r in res])
    if any(k in full_text for k in ["编号", "肩宽", "胸围", "衣长", "袖长"]):
        # Extract code if present
        code = "-"
        for r in res:
            t = r[1].strip()
            if any(k in t for k in ["P", "Q", "E", "M", "U", "V", "W", "X", "AC", "1L", "Z", "J"]):
                code = t
                break
        size_cards.append((idx, os.path.basename(p), code, full_text[:30]))

dt = time.time() - t0
print(f"\nScan completed in {dt:.2f}s! Found {len(size_cards)} size cards:")
print(f"{'No':<3} | {'Index':<5} | {'Filename':<15} | {'Detected Code':<15}")
print("-" * 45)
for no, (idx, fname, code, txt) in enumerate(size_cards, 1):
    print(f"{no:<3} | {idx:<5} | {fname:<15} | {code:<15}")
