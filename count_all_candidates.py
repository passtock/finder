import cv2, os, glob, sys
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')

base = r"c:\Users\passp\Desktop\univercity\4-2\taobao_jackets\downloaded_jackets"
folders = sorted([d for d in os.listdir(base) if os.path.isdir(os.path.join(base, d)) and d.startswith("item_")])

def find_candidate_cards(folder_path):
    jpgs = sorted(glob.glob(os.path.join(folder_path, "photo_*.jpg")))
    candidates = []
    for idx, p in enumerate(jpgs):
        if os.path.getsize(p) == 33084: # banner
            continue
        img = cv2.imread(p)
        if img is None: continue
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 175, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        h_img, w_img = gray.shape
        total_area = h_img * w_img
        
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if 0.15 * total_area < area < 0.85 * total_area:
                x, y, w, h = cv2.boundingRect(cnt)
                aspect = float(h) / w
                cx = x + w / 2.0
                if 1.25 <= aspect <= 3.0 and 0.25 * w_img < cx < 0.75 * w_img:
                    candidates.append((idx, os.path.basename(p)))
                    break
    return len(jpgs), candidates

print(f"{'Folder':<20} | {'Total Photos':<12} | {'Card Candidates':<15}")
print("-" * 55)

total_photos_all = 0
total_candidates_all = 0

for f in folders:
    fpath = os.path.join(base, f)
    n_photos, cands = find_candidate_cards(fpath)
    total_photos_all += n_photos
    total_candidates_all += len(cands)
    sample_cands = [c[1] for c in cands[:6]]
    print(f"{f:<20} | {n_photos:<12} | {len(cands):<3} {sample_cands}")

print("-" * 55)
print(f"Total: {len(folders)} folders | {total_photos_all} photos | ~{total_candidates_all} jacket candidates")
