import os, glob, sys
import pandas as pd

sys.stdout.reconfigure(encoding='utf-8')

base = r"c:\Users\passp\Desktop\univercity\4-2\taobao_jackets\downloaded_jackets"
csv_path = r"c:\Users\passp\Desktop\univercity\4-2\taobao_jackets\taobao_leather_jackets_with_brands.csv"

df = pd.read_csv(csv_path, encoding='utf-8-sig')

print(f"{'순번':<4} | {'폴더':<18} | {'판독품번':<8} | {'제목 품번':<10} | {'실측사진':<12} | {'일치여부'}")
print("-" * 75)

for idx, row in df.iterrows():
    folder = row['상품폴더']
    brand_code = str(row['자켓품번'])
    title = str(row['상품명'])
    card_photo = str(row['실측사진'])
    
    # 제목 끝이나 중간에 있는 품번 추출 (예: E1, AC91, Q118, V100, V93 등)
    tokens = title.split()
    title_code = tokens[-1] if tokens else ""
    
    match = (brand_code.upper() in title_code.upper()) or (title_code.upper() in brand_code.upper())
    print(f"{row['순번']:<4} | {folder:<18} | {brand_code:<8} | {title_code:<10} | {card_photo:<12} | {'OK' if match else 'MISMATCH'}")
