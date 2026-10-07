import os
import re
import sys
import time
import requests
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains

# UTF-8 출력 보장
sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = r"c:\Users\passp\Desktop\univercity\4-2\taobao_jackets"
OUTPUT_DIR = os.path.join(BASE_DIR, "downloaded_jackets")
RESULT_CSV = os.path.join(BASE_DIR, "taobao_leather_jackets_summary.csv")
RESULT_EXCEL = os.path.join(BASE_DIR, "taobao_leather_jackets_summary.xlsx")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 상점 메인 URL
SHOP_URL = "https://shop193475709.world.taobao.com/?spm=a21xtw.29978518.0.0"

def connect_to_browser():
    chrome_options = Options()
    chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
    return webdriver.Chrome(options=chrome_options)

def is_strictly_mens_longsleeve_jacket(title):
    """
    엄격한 필터 조건:
    1. 가죽 자켓만 (조끼/바지/치마/코트 제외)
    2. 긴팔만 (민소매/반팔/조끼 제외)
    3. 남성 전용 (여성 전용 제외)
    """
    # 여성 전용 제외
    if any(k in title for k in ["女款", "女士", "女装", "短裙", "半身裙", "女西装"]):
        return False, "여성 전용 상품 제외"
    if "女" in title and "男" not in title:
        return False, "여성 표기 상품 제외"

    # 조끼 / 민소매 / 반팔 제외 (긴팔만 허용)
    if any(k in title for k in ["马甲", "马夹", "背心", "无袖", "短袖"]):
        return False, "조끼/민소매/반팔 제외"

    # 롱코트 / 트렌치코트 / 바지 / 치마 제외
    if any(k in title for k in ["大衣", "风衣", "长款", "皮裤", "裤子", "短裤"]):
        return False, "코트/바지 형태 제외"

    # 필수 가죽자켓 키워드
    jacket_keywords = ["皮衣", "皮夹克", "夹克", "机车", "飞行员", "A2", "G1", "西服", "西装", "外套"]
    if not any(k in title for k in jacket_keywords):
        return False, "가죽자켓 키워드 미포함"

    return True, "통과"

def setup_shop_catalog(driver):
    """
    상점 홈 접속 -> 왼쪽 메뉴 '男装真皮外套' 클릭 -> 상단 '价格' 순 정렬 클릭 -> 전체 상품(60개) 스크롤 로딩
    """
    print(f"[*] 상점 메인 페이지 접속: {SHOP_URL}", flush=True)
    driver.get(SHOP_URL)
    time.sleep(3)

    # 1. 왼쪽 카테고리 메뉴에서 '男装真皮外套' 클릭
    print("    - 왼쪽 카테고리 메뉴에서 '男装真皮外套' 선택 중...", flush=True)
    driver.execute_script("""
        let spans = Array.from(document.querySelectorAll('span'));
        let target = spans.find(s => s.innerText.trim() === '男装真皮外套');
        if (target) target.click();
    """)
    time.sleep(2)

    # 2. 상단 정렬 탭에서 '价格' (가격순) 클릭
    print("    - 상단 정렬에서 '价格' (가격순 정렬) 버튼 클릭 중...", flush=True)
    driver.execute_script("""
        let spans = Array.from(document.querySelectorAll('span'));
        let priceBtn = spans.find(s => s.innerText.trim() === '价格');
        if (priceBtn) (priceBtn.parentElement || priceBtn).click();
    """)
    time.sleep(2)

    # 3. 카탈로그 전체 카드(총 60개) 점진적 스크롤 로딩
    print("    - 카탈로그 페이지 점진적 스크롤하여 전체 상품 카드 로딩 중...", flush=True)
    for y in range(0, 8000, 800):
        driver.execute_script(f"window.scrollTo(0, {y});")
        time.sleep(0.8)
        cards = driver.find_elements(By.CSS_SELECTOR, "[class*='cardContainer']")
        print(f"      [카탈로그 스크롤] Y={y}px: 로드된 상품 카드 {len(cards)}개...", flush=True)
        if len(cards) >= 60:
            print(f"    - [카탈로그 로딩 완료] 전체 {len(cards)}개의 모든 상품 카드 로딩 성공!", flush=True)
            break

    # 맨 위로 스크롤 복귀
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(1)

def scroll_to_true_bottom(driver):
    """
    타오바오 상세 페이지의 동적 청크/무한 지연 로딩을 완벽하게 끝까지 해제.
    페이지 높이가 더 이상 늘어나지 않을 때까지(30만~40만 px 이상) 100% 바닥까지 도달.
    """
    print("    - [동적 완전 스크롤] 상세 페이지 실제 최하단(30만px+)까지 정밀 탐색 시작...", flush=True)

    # 1단계: 상단에서부터 2500px 단위로 점진적으로 내려가면서 화면 영역 렌더링 활성화
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

    # 2단계: 최하단에서 동적 모듈 확장(IntersectionObserver) 추적 및 바운스 스크롤
    prev_h = 0
    unchanged_count = 0
    round_num = 0

    while True:
        round_num += 1
        # 맨 바닥으로 스크롤
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1.2)
        
        # 2500px 살짝 위로 올렸다가 다시 바닥으로 (동적 로딩 이벤트 트리거)
        driver.execute_script("window.scrollTo(0, Math.max(0, document.body.scrollHeight - 2500));")
        time.sleep(0.5)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1.2)

        curr_h = driver.execute_script("return document.body.scrollHeight;")
        curr_y = driver.execute_script("return window.scrollY || window.pageYOffset;")

        if curr_h == prev_h:
            unchanged_count += 1
            if unchanged_count >= 3:
                print(f"    - [★ 바닥 100% 완전 도달!] 최종 전체 페이지 높이: {curr_h}px (확인 {round_num}회차)", flush=True)
                break
        else:
            diff = curr_h - prev_h if prev_h > 0 else curr_h
            print(f"    - [스크롤 확장 중 #{round_num}] 현재 높이: {curr_h}px (+{diff}px 추가 로드)", flush=True)
            unchanged_count = 0
            prev_h = curr_h

        if round_num > 60:
            print(f"    - [!] 최대 스크롤 상한선 도달 (최종 높이: {curr_h}px)", flush=True)
            break

    time.sleep(1.0)
    return curr_h

def scrape_detail_images(driver, item_id, item_title):
    """
    상세페이지 진입 후:
    1. '图文详情' 탭 클릭
    2. 실제 페이지 맨 바닥(최대 35만px 이상)까지 100% 동적 완전 스크롤
    3. 설명 영역(#imageTextInfo-content / .desc-root / .descV8-richtext)의 순수 상품 고화질 원본만 추출
    4. 멀티스레드로 초고속 다운로드 (손글씨 실측표, 목 라벨, 케어 라벨, 전신 사진 전부 포함)
    """
    # '图文详情' 탭 클릭
    try:
        detail_tabs = driver.find_elements(By.XPATH, "//*[contains(text(), '图文详情')]")
        if detail_tabs:
            driver.execute_script("arguments[0].click();", detail_tabs[0])
            time.sleep(1)
    except Exception:
        pass

    # 실제 페이지 바닥까지 동적 정밀 스크롤
    total_h = scroll_to_true_bottom(driver)

    # 순수 상품 설명 영역의 고화질 원본 이미지 URL 추출
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
            
            // 로고, 아바타, 썸네일 아이콘 배제
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
    print(f"    - 순수 상품 상세 사진 {len(image_urls)}장 발견 (끝까지 100% 탐색 완료)", flush=True)

    # 상품 전용 폴더 생성
    item_folder = os.path.join(OUTPUT_DIR, f"item_{item_id}")
    os.makedirs(item_folder, exist_ok=True)

    # 고속 멀티스레드 다운로드 (누락 없이 전부 다운로드)
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

    print(f"    - 실측표 및 라벨 포함 고화질 사진 저장 완료: {len(downloaded_files)}장 ({item_folder})", flush=True)

    # 폴더 내 정보 파일 기록
    info_path = os.path.join(item_folder, "item_info.txt")
    with open(info_path, "w", encoding="utf-8") as f:
        f.write(f"상품ID: {item_id}\n")
        f.write(f"상품명: {item_title}\n")
        f.write(f"URL: {driver.current_url}\n")
        f.write(f"총 페이지 높이: {total_h}px\n")
        f.write(f"다운로드된 사진 수: {len(downloaded_files)}\n")

    return downloaded_files, item_folder

def run_pipeline():
    driver = connect_to_browser()
    print("[+] 브라우저 세션(Port 9222) 연결 성공!", flush=True)

    # 기존 다른 탭 닫고 메인 탭 1개로 정리
    catalog_handle = driver.current_window_handle
    for h in list(driver.window_handles):
        if h != catalog_handle:
            try:
                driver.switch_to.window(h)
                driver.close()
            except Exception:
                pass
    driver.switch_to.window(catalog_handle)

    # 1. 상점 접속 -> 남성가죽자켓 선택 -> 가격순 정렬 -> 60개 카드 전체 로딩
    setup_shop_catalog(driver)

    cards = driver.find_elements(By.CSS_SELECTOR, "[class*='cardContainer']")
    print(f"\n[+] 카탈로그 내 총 {len(cards)}개 상품 카드 대상 엄격한 필터링 시작...", flush=True)

    # 엄격한 필터링 적용 (남성 긴팔 가죽자켓만)
    target_indices = []
    for idx, c in enumerate(cards):
        title = c.find_element(By.CSS_SELECTOR, "[class*='title']").text.strip().replace("\n", " ")
        ok, reason = is_strictly_mens_longsleeve_jacket(title)
        if ok:
            target_indices.append((idx, title))
            print(f"  [O 선정 #{len(target_indices)}] 카드 {idx+1}: {title} | {reason}", flush=True)
        else:
            print(f"  [X 제외] 카드 {idx+1}: {title[:35]} | {reason}", flush=True)

    print(f"\n[+] 총 {len(target_indices)}개의 '남성 긴팔 가죽자켓' 타겟 상품이 엄격하게 선정되었습니다!", flush=True)

    # 기존 저장된 내역 불러오기 (중복 수집 방지)
    results = []
    if os.path.exists(RESULT_CSV):
        try:
            prev_df = pd.read_csv(RESULT_CSV, encoding="utf-8-sig")
            results = prev_df.to_dict('records')
        except Exception:
            results = []

    saved_ids = {str(r.get("상품ID")) for r in results}

    for seq, (card_idx, title) in enumerate(target_indices, 1):
        driver.switch_to.window(catalog_handle)
        cards = driver.find_elements(By.CSS_SELECTOR, "[class*='cardContainer']")
        if card_idx >= len(cards):
            continue
        card = cards[card_idx]

        print(f"\n" + "="*60, flush=True)
        print(f">>> [수집 진행률: {seq} / {len(target_indices)}]", flush=True)
        print(f"    - 대상 상품: {title}", flush=True)

        handles_before = list(driver.window_handles)

        try:
            title_el = card.find_element(By.CSS_SELECTOR, "[class*='title']")
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", title_el)
            time.sleep(0.5)
            ActionChains(driver).move_to_element(title_el).click().perform()
            time.sleep(3)
        except Exception as e:
            print(f"[-] 카드 클릭 실패 ({e}), 건너뜁니다.", flush=True)
            continue

        handles_after = list(driver.window_handles)
        new_handles = [h for h in handles_after if h not in handles_before]
        if not new_handles:
            print("[-] 새 탭이 열리지 않았습니다. 건너뜁니다.", flush=True)
            continue

        item_handle = new_handles[0]
        driver.switch_to.window(item_handle)

        try:
            current_url = driver.current_url
            match = re.search(r'id=(\d+)', current_url)
            item_id = match.group(1) if match else str(int(time.time()))

            # 이미 100% 수집된 상품인지 확인 (사진 50장 이상 존재 시 건너뛰기)
            item_folder = os.path.join(OUTPUT_DIR, f"item_{item_id}")
            if os.path.exists(item_folder):
                existing_photos = [f for f in os.listdir(item_folder) if f.startswith("photo_")]
                if len(existing_photos) >= 50:
                    print(f"    - [기존 수집 완료 확인: {len(existing_photos)}장 보유] 중복 수집 생략하고 통과합니다.", flush=True)
                    if item_id not in saved_ids:
                        results.append({
                            "순번": seq,
                            "상품ID": item_id,
                            "상품명": title,
                            "상세URL": current_url,
                            "다운로드사진수": len(existing_photos),
                            "저장폴더": item_folder
                        })
                        saved_ids.add(item_id)
                    continue

            # 바닥까지 100% 완전 스크롤 및 고화질 사진 전체 수집
            downloaded_files, item_folder = scrape_detail_images(driver, item_id, title)

            results.append({
                "순번": seq,
                "상품ID": item_id,
                "상품명": title,
                "상세URL": current_url,
                "다운로드사진수": len(downloaded_files),
                "저장폴더": item_folder
            })
            saved_ids.add(item_id)

            # 실시간 CSV 및 엑셀 갱신
            df = pd.DataFrame(results)
            df.to_csv(RESULT_CSV, index=False, encoding="utf-8-sig")
            df.to_excel(RESULT_EXCEL, index=False)
            print(f"[✓] 실시간 엑셀/CSV 갱신 완료 (현재 누적: {len(results)}개 상품)", flush=True)

        except Exception as e:
            print(f"[-] 상품 분석 도중 오류: {e}", flush=True)
        finally:
            driver.close()
            driver.switch_to.window(catalog_handle)
            time.sleep(1)

    print(f"\n" + "="*60, flush=True)
    print(f"[🎉] 상점 내 남성 가죽자켓(가격순 정렬) 전체 스크랩 완료!", flush=True)
    print(f"  - 총 수집 완료 상품 수: {len(results)}개", flush=True)
    print(f"  - CSV: {RESULT_CSV}", flush=True)
    print(f"  - Excel: {RESULT_EXCEL}", flush=True)
    print(f"  - 이미지 폴더: {OUTPUT_DIR}", flush=True)
    print("="*60, flush=True)

if __name__ == "__main__":
    run_pipeline()
