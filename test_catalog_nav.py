import sys
sys.stdout.reconfigure(encoding='utf-8')
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time

opt = Options()
opt.add_experimental_option('debuggerAddress', '127.0.0.1:9222')
driver = webdriver.Chrome(options=opt)

driver.get('https://shop193475709.world.taobao.com/category.htm')
time.sleep(3)

# 1. Click 男装真皮外套
driver.execute_script("""
    let els = Array.from(document.querySelectorAll('span, a, div'));
    let target = els.find(s => s.innerText && s.innerText.trim() === '男装真皮外套');
    if (target) {
        console.log('Found category:', target);
        target.click();
    }
""")
time.sleep(3)

# 2. Click 价格
driver.execute_script("""
    let els = Array.from(document.querySelectorAll('span, a, div'));
    let priceBtn = els.find(s => s.innerText && s.innerText.trim() === '价格');
    if (priceBtn) {
        console.log('Found priceBtn:', priceBtn);
        (priceBtn.parentElement || priceBtn).click();
    }
""")
time.sleep(3)

driver.save_screenshot('after_filter.png')
print('URL after filter:', driver.current_url)

cards = driver.find_elements('css selector', "[class*='cardContainer']")
print(f'Card containers count: {len(cards)}')

# Scroll a bit
for y in range(800, 4800, 800):
    driver.execute_script(f"window.scrollTo(0, {y});")
    time.sleep(0.5)

cards = driver.find_elements('css selector', "[class*='cardContainer']")
print(f'Card containers count after scroll: {len(cards)}')
for i, c in enumerate(cards[:5]):
    print(f'Card {i}: {c.text[:50].replace(chr(10), " ")}')
