$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot

if (-not (Get-Command py -ErrorAction SilentlyContinue)) {
    throw 'Python Launcher (py) was not found. Install Python 3.11 and retry.'
}

py -3.11 -c "import sys; print(sys.version)" | Out-Null
if ($LASTEXITCODE -ne 0) { throw 'Python 3.11 is required for this release.' }

if (-not (Test-Path '.venv\Scripts\python.exe')) {
    py -3.11 -m venv .venv
}

& .venv\Scripts\python.exe -m pip install --disable-pip-version-check -r requirements.txt
if (-not (Test-Path '.env')) { Copy-Item .env.example .env }
& .venv\Scripts\python.exe scripts\seed_demo.py
Start-Process powershell -ArgumentList '-NoExit','-ExecutionPolicy','Bypass','-Command',"Set-Location '$PSScriptRoot'; .venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000"
Start-Sleep -Seconds 3
Start-Process 'http://127.0.0.1:8000'
