import sys, json, re, os
from collections import Counter

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = r"c:\Users\passp\Desktop\univercity\4-2\taobao_jackets"
d1 = json.load(open(os.path.join(BASE_DIR, 'jacket_evaluations_checkpoint.json'), encoding='utf-8'))
d2 = json.load(open(os.path.join(BASE_DIR, 'analyzed_jackets_checkpoint.json'), encoding='utf-8'))

def clean_brand(b):
    if not b: return '빈티지 오리지널 (무명)'
    b = b.strip()
    unnamed_keywords = ['무명', '판독 불가', '판독불가', '미상', '미식별', '미표기', 
                        '식별 불가', '식별불가', '라벨 미확인', '미확인', '불명', 
                        '무지라벨', '블랭크', '빈티지 오리지널', 'Non-brand', 'non-brand', '식별불능']
    if any(w in b for w in unnamed_keywords):
        return '빈티지 오리지널 (무명)'
    
    # Strip trailing explanations in parens like (추정), (아키스...), (한국산 라벨...)
    # But preserve brand names like "COACH (코치)", "L.L.Bean"
    b = re.sub(r'\s*\((?:추정|라벨.*|목라벨.*|백화점.*|도메스틱.*|OEM.*|For Gentlemen|art&culture|GOLF.*)\)', '', b, flags=re.IGNORECASE)
    b = b.strip()
    if len(b) <= 1:
        return '빈티지 오리지널 (무명)'
    return b

brand_map = {}
for k in d1:
    b1 = d1[k].get('brand_name', '')
    b2 = d2.get(k, {}).get('brand', '') if k in d2 else ''
    cb1 = clean_brand(b1)
    cb2 = clean_brand(b2)
    
    if cb1 != '빈티지 오리지널 (무명)':
        final_b = cb1
    elif cb2 != '빈티지 오리지널 (무명)':
        final_b = cb2
    else:
        final_b = '빈티지 오리지널 (무명)'
    brand_map[k] = final_b

counts = Counter(brand_map.values())
named_counts = {k: v for k, v in counts.items() if k != '빈티지 오리지널 (무명)'}

print(f"Total jackets: {len(brand_map)}")
print(f"Named jackets: {sum(named_counts.values())}")
print(f"Unnamed jackets: {counts['빈티지 오리지널 (무명)']}")
print(f"Distinct named brands count: {len(named_counts)}")

sorted_brands = sorted(named_counts.items(), key=lambda x: -x[1])
print(f"\nAll {len(sorted_brands)} distinct named brands (Brand: count):")
for idx, (b, c) in enumerate(sorted_brands, start=1):
    print(f"{idx:3d}. {b} ({c}벌)")

# Save brand list to json
with open(os.path.join(BASE_DIR, 'extracted_named_brands.json'), 'w', encoding='utf-8') as f:
    json.dump(sorted_brands, f, ensure_ascii=False, indent=2)
