import sys
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

sys.stdout.reconfigure(encoding='utf-8')

opt = Options()
opt.add_experimental_option('debuggerAddress', '127.0.0.1:9222')
driver = webdriver.Chrome(options=opt)

res = driver.execute_script("""
    let els = Array.from(document.querySelectorAll('*'));
    let matches = els.filter(e => e.innerText && e.innerText.includes('男装真皮外套') && e.children.length === 0);
    return matches.map(m => ({
        tag: m.tagName,
        text: m.innerText,
        className: m.className,
        parentTag: m.parentElement ? m.parentElement.tagName : '',
        parentClass: m.parentElement ? m.parentElement.className : '',
        parentHref: m.parentElement ? m.parentElement.getAttribute('href') : '',
        href: m.getAttribute('href')
    }));
""")
import json
print(json.dumps(res, indent=2, ensure_ascii=False))
