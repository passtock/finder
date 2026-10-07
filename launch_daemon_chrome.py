import subprocess
import time
import os
import urllib.request
import json

# Kill any lingering instances
subprocess.run(['taskkill', '/F', '/IM', 'chrome.exe'], capture_output=True)
time.sleep(2)

profile_dir = r"c:\Users\passp\Desktop\univercity\4-2\taobao_jackets\chrome_debug_profile"
os.makedirs(profile_dir, exist_ok=True)

cmd = [
    r'C:\Program Files\Google\Chrome\Application\chrome.exe',
    '--remote-debugging-port=9222',
    f'--user-data-dir={profile_dir}',
    '--no-first-run',
    '--no-default-browser-check',
    'https://shop193475709.world.taobao.com/?spm=a21xtw.29978518.0.0'
]

DETACHED_PROCESS = 0x00000008
CREATE_NEW_PROCESS_GROUP = 0x00000200

proc = subprocess.Popen(
    cmd,
    creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP,
    close_fds=True
)

time.sleep(3)

try:
    with urllib.request.urlopen('http://127.0.0.1:9222/json/version', timeout=3) as resp:
        print("[SUCCESS] Chrome running independently on 9222:", json.loads(resp.read().decode())['Browser'])
except Exception as e:
    print("[FAILED]:", e)
