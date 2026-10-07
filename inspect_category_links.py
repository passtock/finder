import sys
sys.stdout.reconfigure(encoding='utf-8')
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import json

opt = Options()
opt.add_experimental_option('debuggerAddress', '127.0.0.1:9222')
driver = webdriver.Chrome(options=opt)

html = driver.page_source
soup = BeautifulSoup(html, 'html.parser')

# Find all links that point to item.taobao.com
items = []
for a in soup.find_all('a', href=True):
    href = a['href']
    if 'item.taobao.com' in href or 'detail.tmall.com' in href or 'id=' in href:
        text = a.get_text(strip=True)
        if text and len(text) > 5:
            items.append((text, href))

print(f"Total product links found: {len(items)}")
for t, h in items[:10]:
    print(f"  {t[:40]} -> {h[:60]}")
