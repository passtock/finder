import sys, time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

sys.stdout.reconfigure(encoding='utf-8')

opt = Options()
opt.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
d = webdriver.Chrome(options=opt)

print("Navigating to https://shop193475709.taobao.com/search.htm ...")
d.get("https://shop193475709.taobao.com/search.htm")
time.sleep(4)

print("Current URL:", d.current_url)
print("Title:", d.title)
cards = d.find_elements(By.CSS_SELECTOR, "[class*='cardContainer'], .item, .shop-hesper-bd, .pagination, [class*='item']")
print(f"Elements found: {len(cards)}")

# Check text on page
body_text = d.find_element(By.TAG_NAME, "body").text
print(f"Body text preview (first 500 chars):\n{body_text[:500]}")
d.save_screenshot("search_screen.png")
