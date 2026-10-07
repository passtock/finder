@echo off
chcp 65001 > nul
echo [*] 타오바오 디버깅 전용 크롬을 실행합니다...
start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="%~dp0chrome_debug_profile" "https://shop193475709.world.taobao.com/?spm=a21xtw.29978518.0.0"
echo [✓] 9222 포트로 크롬이 시작되었습니다.
