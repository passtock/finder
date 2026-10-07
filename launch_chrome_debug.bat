@echo off
taskkill /F /IM chrome.exe >nul 2>&1
timeout /t 1 /nobreak >nul
start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 "https://shop193475709.world.taobao.com/?spm=a21xtw.29978518.0.0"
