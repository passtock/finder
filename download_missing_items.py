import os, sys, glob, re
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = r"c:\Users\passp\Desktop\univercity\4-2\taobao_jackets\downloaded_jackets"

def download_item(txt_path):
    fname = os.path.basename(txt_path)
    item_id = fname.replace('taobao_item_', '').replace('_images.txt', '')
    folder = os.path.join(BASE_DIR, f'item_{item_id}')
    
    if os.path.exists(folder) and len(glob.glob(os.path.join(folder, "*.jpg"))) > 50:
        print(f"[-] 이미 다운로드 완료됨: {item_id}")
        return
        
    os.makedirs(folder, exist_ok=True)
    
    title = f"item_{item_id}"
    url = ""
    urls = []
    
    with open(txt_path, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            line = line.strip()
            if line.startswith("상품명:"):
                title = line.replace("상품명:", "").strip()
            elif line.startswith("URL:"):
                url = line.replace("URL:", "").strip()
            elif line.startswith("http"):
                urls.append(line)
                
    # item_info.txt 기록
    info_path = os.path.join(folder, "item_info.txt")
    with open(info_path, "w", encoding="utf-8") as inf:
        inf.write(f"상품ID: {item_id}\n")
        inf.write(f"상품명: {title}\n")
        inf.write(f"URL: {url}\n")
        inf.write(f"총 이미지 수: {len(urls)}\n")
        
    print(f"[*] 다운로드 시작: item_{item_id} (총 {len(urls)}장) -> {folder}")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    def fetch_img(idx_url):
        idx, img_url = idx_url
        target_path = os.path.join(folder, f"photo_{idx:03d}.jpg")
        if os.path.exists(target_path) and os.path.getsize(target_path) > 3000:
            return True
        for _ in range(2):
            try:
                resp = requests.get(img_url, headers=headers, timeout=12)
                if resp.status_code == 200 and len(resp.content) > 3000:
                    with open(target_path, "wb") as img_f:
                        img_f.write(resp.content)
                    return True
            except Exception:
                pass
        return False

    tasks = [(i + 1, u) for i, u in enumerate(urls)]
    success_count = 0
    with ThreadPoolExecutor(max_workers=20) as executor:
        for res in executor.map(fetch_img, tasks):
            if res: success_count += 1
            
    print(f"[✓] 완료: item_{item_id} -> {success_count}/{len(urls)}장 저장 완료")

def main():
    txt_files = glob.glob(os.path.join(BASE_DIR, 'taobao_item_*_images.txt'))
    print(f"[*] 총 {len(txt_files)}개 txt 파일 확인 중...")
    
    to_download = []
    for f in txt_files:
        fname = os.path.basename(f)
        item_id = fname.replace('taobao_item_', '').replace('_images.txt', '')
        folder = os.path.join(BASE_DIR, f'item_{item_id}')
        if not os.path.exists(folder) or len(glob.glob(os.path.join(folder, "*.jpg"))) < 50:
            to_download.append(f)
            
    print(f"[*] 다운로드 대상: {len(to_download)}개 상품")
    for f in to_download:
        download_item(f)
        
    print("\n[🎉] 모든 신규 상품 이미지 다운로드 완료!")

if __name__ == "__main__":
    main()
