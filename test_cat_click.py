import sys, time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

sys.stdout.reconfigure(encoding='utf-8')

opt = Options()
opt.add_experimental_option('debuggerAddress', '127.0.0.1:9222')
driver = webdriver.Chrome(options=opt)

driver.get('https://shop193475709.taobao.com/category.htm')
time.sleep(3)
print('Current URL:', driver.current_url)

# Check if 男装真皮外套 exists
cat_found = driver.execute_script("""
    let els = Array.from(document.querySelectorAll('span, a, div'));
    let target = els.find(s => s.innerText && s.innerText.trim() === '男装真皮外套');
    if (target) {
        target.click();
        return true;
    }
    return false;
""")
print('男装真皮外套 found and clicked:', cat_found)
time.sleep(3)
print('URL after category click:', driver.current_url)

driver.save_screenshot('cat_click_screen.png')
