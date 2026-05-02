@echo off
REM Setup script for ProteinScout backend dependencies

echo === ProteinScout Backend Setup ===
echo.

REM Check Python
where python >nul 2>nul
if %errorlevel% equ 0 (
    echo Found Python:
    python --version
) else (
    where python3 >nul 2>nul
    if %errorlevel% equ 0 (
        echo Found Python 3:
        python3 --version
    ) else (
        echo ERROR: Python 3 is required but not installed.
        echo Please install Python 3.11 or later from https://www.python.org/
        exit /b 1
    )
)

echo.
echo Installing backend dependencies...
python -m pip install --upgrade pip
python -m pip install -r src-tauri/resources/backend/requirements.txt

echo.
echo === Setup Complete ===
echo You can now run: npm run tauri dev
pause
