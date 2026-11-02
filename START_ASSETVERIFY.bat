@echo off
setlocal
cd /d "%~dp0"
title AssetVerify Launcher

echo Starting AssetVerify...

if not exist ".env" (
    echo ERROR: .env was not found beside app.py.
    echo Create .env and set DATABASE_URL, SECRET_KEY, and ADMIN_PASSWORD.
    pause
    exit /b 1
)

set "PYTHON=%~dp0.venv\Scripts\python.exe"
if not exist "%PYTHON%" (
    echo Creating the Python environment...
    py -3 -m venv .venv
    if errorlevel 1 (
        echo ERROR: Python 3 was not found or the environment could not be created.
        pause
        exit /b 1
    )
)

"%PYTHON%" -c "import flask, flask_sqlalchemy, flask_login, pymysql, dotenv, qrcode, PIL, pyotp, cryptography" >nul 2>&1
if errorlevel 1 (
    echo Installing the required packages. This may take a few minutes the first time...
    "%PYTHON%" -m pip install -r requirements.txt
    if errorlevel 1 (
        echo ERROR: Package installation failed. Check your internet connection.
        pause
        exit /b 1
    )
)

echo Checking the MySQL connection and preparing app tables...
"%PYTHON%" -m flask --app app init-db
if errorlevel 1 (
    echo ERROR: Database setup failed. Make sure MySQL is running and DATABASE_URL in .env is correct.
    pause
    exit /b 1
)

"%PYTHON%" -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5013/login', timeout=2)" >nul 2>&1
if not errorlevel 1 (
    "%PYTHON%" -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5013/static/css/shared/theme.css', timeout=2)" >nul 2>&1
    if errorlevel 1 (
        echo An older AssetVerify server is still running and cannot find the moved frontend files.
        echo Close the existing AssetVerify Server window, then run this launcher again.
        pause
        endlocal
        exit /b 1
    )
    "%PYTHON%" -c "import json,urllib.request; data=json.load(urllib.request.urlopen('http://127.0.0.1:5013/health/version', timeout=2)); assert data.get('version') == 'retired-guard-20261102'" >nul 2>&1
    if errorlevel 1 (
        echo An older AssetVerify server is still running and has not loaded the latest navigation changes.
        echo Close the existing AssetVerify Server window, then run this launcher again.
        pause
        endlocal
        exit /b 1
    )
    "%PYTHON%" -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5013/team', timeout=2)" >nul 2>&1
    if errorlevel 1 (
        echo An older AssetVerify version is still running and does not include technician management.
        echo Close the existing AssetVerify Server window, then run this launcher again.
        pause
        endlocal
        exit /b 1
    )
    echo AssetVerify is already running. Opening it in your browser...
    start "" http://127.0.0.1:5013
    endlocal
    exit /b 0
)

echo Starting the web server...
start "AssetVerify Server" /D "%~dp0" cmd /k ""%PYTHON%" -m flask --app app run --host 127.0.0.1 --port 5013"

set /a attempts=0
:wait_for_server
"%PYTHON%" -c "import json,urllib.request; urllib.request.urlopen('http://127.0.0.1:5013/login', timeout=2); urllib.request.urlopen('http://127.0.0.1:5013/static/css/shared/theme.css?v=retired-guard-20261102', timeout=2); data=json.load(urllib.request.urlopen('http://127.0.0.1:5013/health/version', timeout=2)); assert data.get('version') == 'retired-guard-20261102'" >nul 2>&1
if not errorlevel 1 (
    start "" http://127.0.0.1:5013
    echo AssetVerify is ready. Keep the server window open while using it.
    endlocal
    exit /b 0
)
set /a attempts+=1
if %attempts% GEQ 25 (
    echo ERROR: The app did not respond after 25 seconds.
    echo Check the AssetVerify Server window for the error message.
    pause
    endlocal
    exit /b 1
)
timeout /t 1 /nobreak >nul
goto wait_for_server
