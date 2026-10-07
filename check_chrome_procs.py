import subprocess
import json

try:
    out = subprocess.check_output(
        ['powershell', '-Command', 'Get-Process chrome -ErrorAction SilentlyContinue | Measure-Object | Select-Object -ExpandProperty Count'],
        text=True
    ).strip()
    print(f"Running Chrome instances: {out}")
except Exception as e:
    print(e)
