import sys
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

sys.stdout.reconfigure(encoding='utf-8')

opt = Options()
opt.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
d = webdriver.Chrome(options=opt)
print("Current URL:", d.current_url)
print("Title:", d.title)

# Check cards
cards = d.find_elements(By.CSS_SELECTOR, "[class*='cardContainer']")
print(f"Cards found on page: {len(cards)}")

# Check category menu spans
spans = d.find_elements(By.TAG_NAME, "span")
menu_texts = [s.text.strip() for s in spans if s.text.strip()]
print(f"Sample span texts: {menu_texts[:15]}")
