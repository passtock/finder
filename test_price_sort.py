import sys, time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

sys.stdout.reconfigure(encoding='utf-8')

opt = Options()
opt.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
d = webdriver.Chrome(options=opt)

print("Current URL:", d.current_url)

# Click 价格
price_btn = None
for el in d.find_elements(By.XPATH, "//*[contains(text(), '价格')]"):
    if el.is_displayed():
        price_btn = el
        break

if price_btn:
    print("Found price sort button:", price_btn.text)
    d.execute_script("arguments[0].click();", price_btn)
    time.sleep(3)
else:
    print("Price button not found directly, looking in spans/divs...")
    d.execute_script("""
        let els = Array.from(document.querySelectorAll('*'));
        let target = els.find(e => e.innerText && e.innerText.trim() === '价格' && e.children.length <= 1);
        if (target) target.click();
    """)
    time.sleep(3)

print("After clicking price sort, URL:", d.current_url)

# Scroll to load items
for y in range(0, 8000, 1000):
    d.execute_script(f"window.scrollTo(0, {y});")
    time.sleep(0.5)

cards = d.find_elements(By.CSS_SELECTOR, "[class*='cardContainer']")
print(f"Total cards loaded: {len(cards)}")

# Check first 5 cards
for i, c in enumerate(cards[:5]):
    title = c.find_element(By.CSS_SELECTOR, "[class*='title']").text.strip().replace("\n", " ")
    print(f"Card {i+1}: {title}")

d.save_screenshot("price_sorted_screen.png")
