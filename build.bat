@echo off
REM Build script for ProteinScout
REM Builds the frontend and prepares backend for bundling

echo === Building ProteinScout ===
echo.

REM Build frontend
echo Building React frontend...
call npm run build
if %errorlevel% neq 0 exit /b 1

REM Prepare backend for bundling
echo Preparing backend for bundling...
if not exist "src-tauri\resources\backend" mkdir "src-tauri\resources\backend"

REM Remove old backend files
if exist "src-tauri\resources\backend\main.py" del "src-tauri\resources\backend\main.py"
if exist "src-tauri\resources\backend\routers" rmdir /s /q "src-tauri\resources\backend\routers"
if exist "src-tauri\resources\backend\core" rmdir /s /q "src-tauri\resources\backend\core"

REM Copy fresh backend files
copy "backend\main.py" "src-tauri\resources\backend\"
xcopy "backend\routers" "src-tauri\resources\backend\routers" /E /I /Y
xcopy "backend\core" "src-tauri\resources\backend\core" /E /I /Y

echo Done: Backend prepared for bundling
echo.
echo === Build Ready ===
echo Run 'npm run tauri build' to create the final app
pause
