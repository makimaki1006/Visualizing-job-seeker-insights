@echo off
echo Stopping all Reflex processes...

REM Node.jsプロセス（Reflexフロントエンド）を停止
tasklist /FI "IMAGENAME eq node.exe" | findstr /I "node.exe" >nul
if not errorlevel 1 (
    echo Stopping Node.js processes...
    taskkill /F /IM node.exe 2>nul
)

REM ポート3000を使用しているプロセスを停止
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :3000 ^| findstr LISTENING') do (
    echo Stopping process on port 3000: PID %%a
    taskkill /F /PID %%a 2>nul
)

REM ポート8000を使用しているプロセスを停止
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do (
    echo Stopping process on port 8000: PID %%a
    taskkill /F /PID %%a 2>nul
)

REM .webディレクトリを削除
if exist .web (
    echo Cleaning .web directory...
    rmdir /s /q .web 2>nul
)

echo All Reflex processes stopped.
echo You can now run 'reflex run' to start fresh.