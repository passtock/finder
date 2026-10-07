import subprocess

ps_script = """
Get-CimInstance Win32_Process -Filter "name = 'chrome.exe'" | ForEach-Object {
    [PSCustomObject]@{
        Id = $_.ProcessId
        CommandLine = $_.CommandLine
    }
} | Format-List
"""

try:
    out = subprocess.check_output(['powershell', '-Command', ps_script], text=True)
    print(out)
except Exception as e:
    print("Error:", e)
