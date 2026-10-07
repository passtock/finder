import sys
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

sys.stdout.reconfigure(encoding='utf-8')

opt = Options()
opt.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
d = webdriver.Chrome(options=opt)
d.save_screenshot("current_screen.png")
print("Screenshot saved to current_screen.png")

with open("current_page_source.html", "w", encoding="utf-8") as f:
    f.write(d.page_source)
print("Page source saved (length:", len(d.page_source), ")")
