import subprocess

ps = """
Get-CimInstance Win32_Process -Filter "name = 'chrome.exe'" | Where-Object { $_.CommandLine -notmatch '--type=' } | Select-Object ProcessId, CreationDate, CommandLine | Format-List
"""
print(subprocess.check_output(['powershell', '-Command', ps], text=True))
