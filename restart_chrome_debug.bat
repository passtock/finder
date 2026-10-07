@echo off
echo ====================================================
echo  Chrome Debug Launcher (Port 9222)
echo ====================================================
echo Closing existing background Chrome processes...
taskkill /F /IM chrome.exe >nul 2>&1
timeout /t 1 /nobreak >nul
echo Starting Chrome with Remote Debugging on Port 9222...
start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 "https://shop193475709.world.taobao.com/?spm=a21xtw.29978518.0.0"
echo Done! Chrome is now running on Port 9222.
timeout /t 3
