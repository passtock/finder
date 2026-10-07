import subprocess

ps = '(Get-CimInstance Win32_Process -Filter "ProcessId = 6688").CommandLine'
print(subprocess.check_output(['powershell', '-Command', ps], text=True))
