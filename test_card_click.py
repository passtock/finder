import sys, time, re

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains

sys.stdout.reconfigure(encoding='utf-8')

opt = Options()
opt.add_experimental_option('debuggerAddress', '127.0.0.1:9222')
driver = webdriver.Chrome(options=opt)

cards = driver.find_elements(By.CSS_SELECTOR, "[class*='cardContainer']")
catalog_handle = driver.current_window_handle

# Let's test Card #136 (X271) - index 135
card = cards[135]
title = card.find_element(By.CSS_SELECTOR, "[class*='title']").text.strip().replace("\n", " ")
print(f"Testing click on Card #136: {title}")

handles_before = list(driver.window_handles)
title_el = card.find_element(By.CSS_SELECTOR, "[class*='title']")
driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", title_el)
time.sleep(0.5)

# Click
ActionChains(driver).move_to_element(title_el).click().perform()
time.sleep(3)

handles_after = list(driver.window_handles)
new_handles = [h for h in handles_after if h not in handles_before]
print(f"New handles opened: {len(new_handles)}")

if new_handles:
    driver.switch_to.window(new_handles[0])
    print(f"Opened URL: {driver.current_url}")
    print(f"Page title: {driver.title}")
    match = re.search(r'id=(\d+)', driver.current_url)
    item_id = match.group(1) if match else "unknown"
    print(f"Extracted item_id: {item_id}")
    driver.close()
    driver.switch_to.window(catalog_handle)
    print("Closed test tab and returned to catalog.")
else:
    print("Direct title click didn't open tab, trying JS click or container click...")
    # fallback test
    driver.execute_script("arguments[0].click();", title_el)
    time.sleep(3)
    handles_after = list(driver.window_handles)
    new_handles = [h for h in handles_after if h not in handles_before]
    print(f"Retry new handles: {len(new_handles)}")
    if new_handles:
        driver.switch_to.window(new_handles[0])
        print(f"Opened URL: {driver.current_url}")
        driver.close()
        driver.switch_to.window(catalog_handle)
