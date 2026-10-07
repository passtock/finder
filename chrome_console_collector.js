// =========================================================================
// 🧥 [Finder] 타오바오 상세페이지 원클릭 고화질 이미지 수집 콘솔 스크립트
// 사용법: 타오바오 상품 상세페이지에서 F12 키 누르고 -> [Console] 탭에 붙여넣고 Enter!
// =========================================================================

(async function collectTaobaoImages() {
    console.log("%c[Finder] 🚀 1단계: 상세페이지 바닥까지 자동 스크롤을 시작합니다...", "color: #3b82f6; font-size: 14px; font-weight: bold;");

    // 1. '图文详情' 탭이 있으면 자동 클릭
    const detailTabs = Array.from(document.querySelectorAll('*')).filter(el => 
        (el.textContent || '').trim() === '图文详情' || (el.textContent || '').trim() === '商品详情'
    );
    if (detailTabs.length > 0) {
        detailTabs[0].click();
        console.log("  [✓] '图文详情' 탭 클릭 완료");
        await new Promise(r => setTimeout(r, 1000));
    }

    // 2. 바닥까지 점진적 스크롤 (레이지 로딩 이미지 활성화)
    let prevHeight = 0;
    let unchangedCount = 0;
    let step = 2500;
    let currentY = 0;

    for (let i = 0; i < 40; i++) {
        currentY += step;
        window.scrollTo(0, currentY);
        await new Promise(r => setTimeout(r, 300));
        
        let scrollH = document.body.scrollHeight;
        if (currentY >= scrollH) {
            // 바운스 스크롤 (IntersectionObserver 강제 발동)
            window.scrollTo(0, Math.max(0, scrollH - 2000));
            await new Promise(r => setTimeout(r, 400));
            window.scrollTo(0, scrollH);
            await new Promise(r => setTimeout(r, 800));

            let newH = document.body.scrollHeight;
            if (newH === prevHeight) {
                unchangedCount++;
                if (unchangedCount >= 3) break;
            } else {
                unchangedCount = 0;
                prevHeight = newH;
            }
        }
    }

    console.log("%c[Finder] ✅ 2단계: 스크롤 완료! 순수 고화질 원본 사진 추출 중...", "color: #10b981; font-size: 14px; font-weight: bold;");

    // 3. 상품 정보 및 이미지 URL 추출
    const urlParams = new URLSearchParams(window.location.search);
    const itemId = urlParams.get('id') || Date.now().toString();
    const title = (document.title || 'taobao_item').replace(/-淘宝网|-tmall.com天猫/g, '').trim();

    const container = document.querySelector('#imageTextInfo-content') || 
                      document.querySelector('.desc-root') || 
                      document.querySelector('.descV8-richtext') ||
                      document.querySelector('#description') || document.body;

    const imgs = container.querySelectorAll('img');
    const urls = [];

    imgs.forEach(img => {
        let src = img.getAttribute('data-src') || img.getAttribute('data-ks-lazyload') || img.src || '';
        if (!src || !src.includes('alicdn.com')) return;

        // 아이콘, 아바타, 빈 이미지 제외
        if (['avatar', 'icon', 'logo', '1x1', 'TB1', 'grey.gif', 'shop_logo', 'shopmanag'].some(k => src.includes(k))) {
            return;
        }

        // 고화질 원본 복원 (썸네일 리사이즈 파라미터 및 webp 제거)
        let clean = src.replace(/_[0-9]+x[0-9]+.*$/, '').replace(/_[qQ][0-9]+.*$/, '').replace(/_\.webp$/, '');
        if (clean.startsWith('//')) clean = 'https:' + clean;

        if (!urls.includes(clean)) {
            urls.push(clean);
        }
    });

    console.log(`%c[Finder] 🎉 총 ${urls.length}장의 고화질 사진을 발견했습니다!`, "color: #8b5cf6; font-size: 15px; font-weight: bold;");
    console.table(urls.slice(0, 10).map((u, idx) => ({ '순번': idx + 1, '고화질 이미지 URL': u })));

    // 4. TXT 파일로 다운로드 (내 컴퓨터에 바로 저장)
    const content = [
        `상품ID: ${itemId}`,
        `상품명: ${title}`,
        `URL: ${window.location.href}`,
        `수집된 사진 수: ${urls.length}`,
        `수집일시: ${new Date().toLocaleString()}`,
        `\n--- 이미지 URL 목록 ---`,
        ...urls
    ].join('\n');

    const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `taobao_item_${itemId}_images.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);

    console.log(`%c[Finder] 💾 'taobao_item_${itemId}_images.txt' 파일이 다운로드 폴더에 저장되었습니다!`, "color: #059669; font-weight: bold;");
    console.log("%c[TIP] URL 리스트를 클립보드에 복사하시려면 콘솔에 copy(window.__finder_urls) 를 입력하세요.", "color: #6b7280;");
    window.__finder_urls = urls;

    return { itemId, title, count: urls.length, urls };
})();
