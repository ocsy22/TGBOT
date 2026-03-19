@echo off
echo ===============================================
echo  TG Auto Publisher - Windows Build Script
echo ===============================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found! Please install Python 3.10+
    pause
    exit /b 1
)

echo [1/3] Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo [2/3] Building EXE...
python build.py
if errorlevel 1 (
    echo ERROR: Build failed
    pause
    exit /b 1
)

echo.
echo [3/3] Build complete!
echo Output: dist\TGAutoPublisher.exe
echo.
echo NOTE: Copy ffmpeg.exe to the same directory as TGAutoPublisher.exe
pause
