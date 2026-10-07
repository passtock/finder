import cv2, os, glob, sys
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')

folder = r"c:\Users\passp\Desktop\univercity\4-2\taobao_jackets\downloaded_jackets\item_1081695145771"
jpgs = sorted(glob.glob(os.path.join(folder, "photo_*.jpg")))[:35]

def is_size_card(img_path):
    if os.path.getsize(img_path) == 33084: # guide banner
        return False, "guide"
    
    img = cv2.imread(img_path)
    if img is None: return False, "none"
    
    # Card is a vertical white rectangle in the center of the image
    # Let's check HSV or grayscale threshold for white paper
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # White paper has high brightness (e.g. > 180)
    _, thresh = cv2.threshold(gray, 175, 255, cv2.THRESH_BINARY)
    
    # Find contours
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    h_img, w_img = gray.shape
    total_area = h_img * w_img
    
    for cnt in contours:
        area = cv2.contourArea(cnt)
        # Card should occupy between 15% and 75% of the total image area
        if 0.12 * total_area < area < 0.85 * total_area:
            x, y, w, h = cv2.boundingRect(cnt)
            aspect = float(h) / w
            # Card is tall (aspect ratio typically 1.3 to 2.5)
            # and centered horizontally (center x is within 30%~70% of image width)
            cx = x + w / 2.0
            if 1.2 <= aspect <= 3.0 and 0.25 * w_img < cx < 0.75 * w_img:
                return True, f"area={area/total_area:.2f}, asp={aspect:.2f}"
                
    return False, "no_card"

if __name__ == '__main__':
    print(f"{'Filename':<15} | {'Is Card?':<10} | {'Details'}")
    print("-" * 50)
    for p in jpgs:
        fname = os.path.basename(p)
        ok, det = is_size_card(p)
        star = "★ SIZE CARD" if ok else ""
        print(f"{fname:<15} | {str(ok):<10} | {det:<20} {star}")

