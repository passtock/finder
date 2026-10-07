import os, glob, sys, time
from rapidocr_onnxruntime import RapidOCR

sys.stdout.reconfigure(encoding='utf-8')

ocr = RapidOCR()
folder = r"c:\Users\passp\Desktop\univercity\4-2\taobao_jackets\downloaded_jackets\item_1081695145771"
jpgs = sorted(glob.glob(os.path.join(folder, "photo_*.jpg")))[:20]

print(f"Testing rapidocr on first 20 photos...")

for p in jpgs:
    t0 = time.time()
    res, elapse = ocr(p)
    dt = time.time() - t0
    texts = [r[1] for r in res] if res else []
    
    is_card = any(k in "".join(texts) for k in ["编号", "肩宽", "胸围", "衣长", "袖长"])
    # 33084 bytes is the guide template banner
    is_guide = (os.path.getsize(p) == 33084)
    
    card_str = "★ [사이즈표 카드!]" if (is_card and not is_guide) else ("(가이드 배너)" if is_guide else "")
    print(f"{os.path.basename(p)} ({dt*1000:.1f}ms): {card_str} | texts: {texts[:4]}")
