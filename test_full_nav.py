import sys, time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

sys.stdout.reconfigure(encoding='utf-8')

opt = Options()
opt.add_experimental_option('debuggerAddress', '127.0.0.1:9222')
driver = webdriver.Chrome(options=opt)

# 1. Click 男装真皮外套
res1 = driver.execute_script("""
    let spans = Array.from(document.querySelectorAll('span, a'));
    let target = spans.find(s => s.innerText && s.innerText.trim() === '男装真皮外套');
    if (target) {
        // Find clickable container or itself
        let clickTarget = target.closest('li') || target.closest('div') || target;
        clickTarget.click();
        return { clicked: true, tag: clickTarget.tagName, text: clickTarget.innerText };
    }
    return { clicked: false };
""")
print("Step 1 (Click 男装真皮外套):", res1)
time.sleep(2)

# 2. Click 价格
res2 = driver.execute_script("""
    let spans = Array.from(document.querySelectorAll('span, a, div'));
    let priceBtn = spans.find(s => s.innerText && s.innerText.trim() === '价格' && s.children.length <= 1);
    if (priceBtn) {
        let clickTarget = priceBtn.closest('li') || priceBtn.closest('div') || priceBtn;
        clickTarget.click();
        return { clicked: true, tag: clickTarget.tagName, text: clickTarget.innerText };
    }
    return { clicked: false };
""")
print("Step 2 (Click 价格):", res2)
time.sleep(3)

# 3. Scroll down to load all items
for y in range(0, 10000, 1000):
    driver.execute_script(f"window.scrollTo(0, {y});")
    time.sleep(0.5)

cards = driver.find_elements(By.CSS_SELECTOR, "[class*='cardContainer']")
print(f"Total cards loaded: {len(cards)}")
for i, c in enumerate(cards):
    title = c.find_element(By.CSS_SELECTOR, "[class*='title']").text.strip().replace("\n", " ")
    price = ""
    try:
        price = c.find_element(By.CSS_SELECTOR, "[class*='price']").text.strip().replace("\n", " ")
    except Exception:
        pass
    print(f"[{i+1}] {title} | {price}")

driver.save_screenshot("test_nav_result.png")
