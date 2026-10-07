import os
import re
import sys
import time
import requests
from concurrent.futures import ThreadPoolExecutor
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

# UTF-8 출력 보장
sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = r"c:\Users\passp\Desktop\univercity\4-2\taobao_jackets"
OUTPUT_DIR = os.path.join(BASE_DIR, "downloaded_jackets")
os.makedirs(OUTPUT_DIR, exist_ok=True)

import socket

def is_chrome_running():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1.5)
        s.connect(('127.0.0.1', 9222))
        s.close()
        return True
    except Exception:
        return False

def connect_to_browser():
    if not is_chrome_running():
        raise ConnectionRefusedError(
            "크롬 디버그 포트(9222)가 열려있지 않습니다.\n"
            "  먼저 'launch_chrome_debug.bat'을 실행하여 크롬을 켠 상태여야 합니다."
        )
    chrome_options = Options()
    chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def get_current_product_tab(driver):
    handles = driver.window_handles
    # 1순위: 사용자가 지금 크롬 화면에서 실제로 보고 있는 활성 탭 (document.visibilityState == visible)
    for h in handles:
        try:
            driver.switch_to.window(h)
            vis = driver.execute_script("return document.visibilityState;")
            if vis == "visible":
                url = driver.current_url
                if "item.taobao.com" in url or "detail.tmall.com" in url or "taobao.com" in url or "tmall.com" in url or "id=" in url:
                    return h
        except Exception:
            pass

    # 2순위: 상품 상세페이지 패턴을 가진 탭 검색
    for h in reversed(handles):
        try:
            driver.switch_to.window(h)
            url = driver.current_url
            if "item.taobao.com" in url or "detail.tmall.com" in url or "id=" in url:
                return h
        except Exception:
            pass

    # 3순위: 마지막 탭
    if handles:
        driver.switch_to.window(handles[-1])
        return handles[-1]
    return None

def scroll_to_true_bottom(driver):
    print("[*] 1단계: 상세 페이지 바닥까지 100% 동적 스크롤 시작...", flush=True)

    # 1단계 점진적 스크롤 (화면 영역 활성화)
    curr_y = 0
    step = 2500
    while True:
        total_h = driver.execute_script("return document.body.scrollHeight;")
        curr_y += step
        driver.execute_script(f"window.scrollTo(0, {curr_y});")
        time.sleep(0.2)
        actual_y = driver.execute_script("return window.scrollY || window.pageYOffset;")
        if actual_y + 3500 >= total_h:
            break

    # 2단계 최하단 확장 감지 및 바운스 스크롤
    prev_h = 0
    unchanged_count = 0
    round_num = 0

    while True:
        round_num += 1
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1.0)
        
        # 살짝 위로 올렸다 다시 바닥으로 (IntersectionObserver 이벤트 트리거)
        driver.execute_script("window.scrollTo(0, Math.max(0, document.body.scrollHeight - 2500));")
        time.sleep(0.4)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1.0)

        curr_h = driver.execute_script("return document.body.scrollHeight;")
        if curr_h == prev_h:
            unchanged_count += 1
            if unchanged_count >= 3:
                print(f"  [✓] 바닥 100% 도달 완료! 최종 페이지 높이: {curr_h}px", flush=True)
                break
        else:
            diff = curr_h - prev_h if prev_h > 0 else curr_h
            print(f"  [스크롤 확장 중] 높이: {curr_h}px (+{diff}px)", flush=True)
            unchanged_count = 0
            prev_h = curr_h

        if round_num > 50:
            print(f"  [!] 최대 스크롤 상한 도달 (최종: {curr_h}px)", flush=True)
            break

    time.sleep(1.0)
    return curr_h

def scrape_active_product():
    print("=" * 60)
    print("🧥 [Finder] 현재 열려있는 타오바오 상품 상세페이지 고속 수집기")
    print("=" * 60)

    try:
        driver = connect_to_browser()
    except Exception as e:
        print(f"[❌ 오류] 크롬(Port 9222)에 연결할 수 없습니다.")
        print(f"  먼저 'launch_chrome_debug.bat'을 실행하여 크롬을 켠 상태여야 합니다.")
        print(f"  세부 에러: {e}")
        return

    tab = get_current_product_tab(driver)
    if not tab:
        print("[❌ 오류] 열려있는 탭을 찾을 수 없습니다.")
        return

    url = driver.current_url
    print(f"[+] 연결된 탭 URL: {url}")

    # Extract item_id
    m_id = re.search(r'[?&]id=(\d+)', url)
    item_id = m_id.group(1) if m_id else str(int(time.time()))

    # Extract title
    title = driver.title.replace("-淘宝网", "").replace("-tmall.com天猫", "").strip()
    try:
        title_el = driver.find_elements(By.CSS_SELECTOR, "h1, [class*='ItemHeader--mainTitle'], [class*='tb-main-title']")
        if title_el:
            t = title_el[0].text.strip()
            if t: title = t
    except Exception:
        pass

    print(f"[+] 상품 ID: {item_id}")
    print(f"[+] 상품명: {title}")

    # '图文详情' 탭 클릭
    try:
        detail_tabs = driver.find_elements(By.XPATH, "//*[contains(text(), '图文详情')]")
        if detail_tabs:
            driver.execute_script("arguments[0].click();", detail_tabs[0])
            time.sleep(1)
    except Exception:
        pass

    # 바닥까지 완전 스크롤
    total_h = scroll_to_true_bottom(driver)

    # 순수 상품 설명 이미지 URL 추출
    js_extract = """
    return (() => {
        let container = document.querySelector('#imageTextInfo-content') || 
                        document.querySelector('.desc-root') || 
                        document.querySelector('.descV8-richtext') ||
                        document.querySelector('#description');
        
        let imgs = container ? container.querySelectorAll('img') : document.querySelectorAll('img');
        const urls = [];
        
        for (const img of imgs) {
            let src = img.getAttribute('data-src') || img.getAttribute('data-ks-lazyload') || img.src || '';
            if (!src || !src.includes('alicdn.com')) continue;
            
            // 로고/아바타 배제
            if (['avatar', 'icon', 'logo', '1x1', 'TB1', 'grey.gif', 'shop_logo', 'shopmanag'].some(k => src.includes(k))) {
                continue;
            }
            
            // 고화질 원본 복원
            let clean = src.replace(/_[0-9]+x[0-9]+.*$/, '').replace(/_[qQ][0-9]+.*$/, '').replace(/_\\.webp$/, '');
            if (clean.startsWith('//')) clean = 'https:' + clean;
            
            if (!urls.includes(clean)) {
                urls.push(clean);
            }
        }
        return urls;
    })();
    """
    image_urls = driver.execute_script(js_extract) or []
    print(f"\n[+] 순수 고화질 상세 사진 {len(image_urls)}장 발견 완료!")

    if not image_urls:
        print("[!] 이미지를 발견하지 못했습니다. 페이지가 로딩 중인지 확인해주세요.")
        return

    # 상품 전용 폴더 생성
    item_folder = os.path.join(OUTPUT_DIR, f"item_{item_id}")
    os.makedirs(item_folder, exist_ok=True)

    # 멀티스레드 고속 다운로드
    print(f"[*] 멀티스레드(8 Workers)로 고화질 사진 다운로드 중 -> {item_folder}...")
    def download_one(task):
        idx, img_url = task
        for attempt in range(2):
            try:
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
                resp = requests.get(img_url, timeout=15, headers=headers)
                if resp.status_code == 200 and len(resp.content) >= 3000:
                    file_path = os.path.join(item_folder, f"photo_{idx:03d}.jpg")
                    with open(file_path, "wb") as f:
                        f.write(resp.content)
                    return file_path
            except Exception:
                pass
        return None

    tasks = [(i + 1, u) for i, u in enumerate(image_urls)]
    downloaded_files = []
    with ThreadPoolExecutor(max_workers=8) as executor:
        for res in executor.map(download_one, tasks):
            if res:
                downloaded_files.append(res)

    print(f"[🎉] 다운로드 완료! 총 {len(downloaded_files)}장의 사진이 저장되었습니다.")
    print(f"     폴더: {item_folder}")

    # item_info.txt 기록
    info_path = os.path.join(item_folder, "item_info.txt")
    with open(info_path, "w", encoding="utf-8") as f:
        f.write(f"상품ID: {item_id}\n")
        f.write(f"상품명: {title}\n")
        f.write(f"URL: {url}\n")
        f.write(f"총 페이지 높이: {total_h}px\n")
        f.write(f"다운로드된 사진 수: {len(downloaded_files)}\n")

    print("\n[TIP] 수집된 상품을 기존 3종 사진 엑셀 도감에 즉시 반영하려면 아래 명령어를 실행하세요:")
    print("      python add_brand_photos_to_catalog.py\n")

if __name__ == "__main__":
    scrape_active_product()
