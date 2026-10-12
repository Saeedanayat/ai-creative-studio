@echo off
setlocal EnableDelayedExpansion
title AI Creative Studio - Setup and Launch
cd /d "%~dp0"

echo ==================================================
echo   AI Creative Studio - Windows launcher
echo ==================================================
echo.

REM ---------- 1. Find Python (3.9 or newer) ----------
set "PY="
py -3 -c "import sys; sys.exit(0 if sys.version_info[:2] >= (3,9) else 1)" >nul 2>&1
if not errorlevel 1 set "PY=py -3"
if not defined PY (
    python -c "import sys; sys.exit(0 if sys.version_info[:2] >= (3,9) else 1)" >nul 2>&1
    if not errorlevel 1 set "PY=python"
)
if not defined PY (
    echo [ERROR] A working Python 3.9 or newer was not found.
    echo.
    echo  1. Download Python from https://www.python.org/downloads/
    echo     ^(Python 3.10, 3.11 or 3.12 is recommended^)
    echo  2. In the installer, TICK the box "Add python.exe to PATH".
    echo  3. Finish the installation, then double-click run_windows.bat again.
    echo.
    echo  Note: if typing "python" only opens the Microsoft Store, install Python from python.org.
    goto :fail
)
echo [OK] Python found: %PY%
%PY% --version
echo.

REM ---------- 2. Create virtual environment if needed ----------
if not exist "venv\Scripts\activate.bat" (
    echo [STEP] Creating virtual environment ^(first run only^)...
    %PY% -m venv venv
    if errorlevel 1 (
        echo [ERROR] Could not create the virtual environment.
        echo         Try deleting the "venv" folder if it exists, then run this file again.
        goto :fail
    )
) else (
    echo [OK] Virtual environment already exists.
)

REM ---------- 3. Activate ----------
call "venv\Scripts\activate.bat"
if errorlevel 1 (
    echo [ERROR] Could not activate the virtual environment.
    goto :fail
)
echo [OK] Virtual environment activated.
echo.

REM ---------- 4. Install dependencies ----------
echo [STEP] Installing required packages ^(this can take a few minutes the first time^)...
python -m pip install --upgrade pip
if errorlevel 1 (
    echo [WARNING] Could not upgrade pip. Continuing anyway...
)
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo [ERROR] Package installation failed.
    echo  - Check that you are connected to the internet.
    echo  - If the message above mentions a specific package, copy it and search for it online.
    echo  - If your Python is very new, installing Python 3.12 from python.org often fixes this.
    goto :fail
)
echo [OK] Packages installed.
echo.

REM ---------- 5. Check .env ----------
if not exist ".env" (
    echo [INFO] No ".env" file found. The app will start in Demo Mode.
    echo        For real image generation: copy .env.example to .env and add your HF_TOKEN.
    echo.
)

REM ---------- 6. Start the app ----------
echo [STEP] Starting AI Creative Studio...
echo        Your browser should open automatically.
echo        If not, open:  http://localhost:8501
echo        To stop the app, press CTRL+C in this window, or close it.
echo.
python -m streamlit run app.py
if errorlevel 1 (
    echo.
    echo [ERROR] The application stopped with an error. Read the messages above.
    goto :fail
)
goto :end

:fail
echo.
echo ==================================================
echo   Something went wrong. Read the message above.
echo ==================================================
pause
exit /b 1

:end
echo.
pause
exit /b 0
