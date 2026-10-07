import sys
sys.stdout.reconfigure(encoding='utf-8')
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

opt = Options()
opt.add_experimental_option('debuggerAddress', '127.0.0.1:9222')
driver = webdriver.Chrome(options=opt)

driver.get('https://shop193475709.world.taobao.com/category.htm')
import time
time.sleep(3)

soup = BeautifulSoup(driver.page_source, 'html.parser')
for el in soup.find_all(['a', 'span', 'li', 'div']):
    text = el.get_text(strip=True)
    if '男装真皮' in text or '价格' in text:
        href = el.get('href', '')
        tag = el.name
        cls = el.get('class', [])
        print(f"Tag: {tag} | Class: {cls} | Text: {text} | Href: {href}")
