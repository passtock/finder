import subprocess
import time
import urllib.request
import json
import os

# Kill existing chrome
subprocess.run(['taskkill', '/F', '/IM', 'chrome.exe'], capture_output=True)
time.sleep(2)

# Start chrome with remote debugging port and a clean temp debug dir
temp_dir = os.path.join(os.environ['TEMP'], 'chrome_tb_debug')
os.makedirs(temp_dir, exist_ok=True)

cmd = [
    r'C:\Program Files\Google\Chrome\Application\chrome.exe',
    '--remote-debugging-port=9222',
    f'--user-data-dir={temp_dir}',
    '--no-first-run',
    '--no-default-browser-check',
    'https://shop193475709.world.taobao.com/?spm=a21xtw.29978518.0.0'
]

print("Launching:", cmd)
proc = subprocess.Popen(cmd)
time.sleep(3)

try:
    with urllib.request.urlopen('http://127.0.0.1:9222/json/version', timeout=3) as resp:
        data = json.loads(resp.read().decode())
        print("[SUCCESS] CDP Connected:", data)
except Exception as e:
    print("[FAILED] CDP Connection:", e)
