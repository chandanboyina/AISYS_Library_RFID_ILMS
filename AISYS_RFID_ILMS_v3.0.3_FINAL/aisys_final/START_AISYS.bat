@echo off
setlocal
cd /d "%~dp0"

echo ==========================================================
echo   AISYS RFID LIBRARY CONTROL CENTER
 echo ==========================================================

where py >nul 2>&1
if errorlevel 1 (
  echo Python launcher was not found.
  echo Install Python 3.11 or newer, then run this file again.
  pause
  exit /b 1
)

py -3.11 -c "import sys; print(sys.version)" >nul 2>&1
if errorlevel 1 (
  echo Python 3.11 is required for the pinned offline-compatible stack.
  echo Install Python 3.11 and run START_AISYS.bat again.
  pause
  exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
  echo [1/4] Creating isolated Python environment...
  py -3.11 -m venv .venv
  if errorlevel 1 goto :fail
)

 echo [2/4] Installing pinned dependencies...
call ".venv\Scripts\python.exe" -m pip install --disable-pip-version-check -r requirements.txt
if errorlevel 1 goto :fail

if not exist ".env" (
  echo [3/4] Creating local configuration...
  copy /Y ".env.example" ".env" >nul
) else (
  echo [3/4] Local configuration already exists.
)

 echo [4/4] Preparing demo data...
call ".venv\Scripts\python.exe" scripts\seed_demo.py
if errorlevel 1 goto :fail

start "AISYS API" cmd /k "cd /d "%~dp0" && .venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000"
timeout /t 3 /nobreak >nul
start "" "http://127.0.0.1:8000"

echo.
echo AISYS is starting at http://127.0.0.1:8000
 echo Demo login: admin / Admin@12345
 echo.
echo Keep the AISYS API window open while using the application.
exit /b 0

:fail
echo.
echo AISYS startup failed. Read the error above.
pause
exit /b 1
