import os
import subprocess
import time
import urllib.request
import json

profile_dir = r"c:\Users\passp\Desktop\univercity\4-2\taobao_jackets\chrome_debug_profile"
os.makedirs(profile_dir, exist_ok=True)

cmd = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "--remote-debugging-port=9222",
    f"--user-data-dir={profile_dir}",
    "--no-first-run",
    "https://shop193475709.world.taobao.com/?spm=a21xtw.29978518.0.0"
]

print("[*] 디버깅 포트(9222) 전용 크롬을 실행합니다...")
subprocess.Popen(cmd)

for i in range(10):
    time.sleep(1)
    try:
        with urllib.request.urlopen("http://127.0.0.1:9222/json/version", timeout=1) as resp:
            data = json.loads(resp.read().decode())
            print("[✓] 9222 포트 연결 성공!", data.get("Browser"))
            break
    except Exception:
        pass
else:
    print("[-] 연결 대기 중...")
