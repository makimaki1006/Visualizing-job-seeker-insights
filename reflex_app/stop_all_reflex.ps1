# Reflexプロセスを安全に停止するスクリプト
Write-Host "Stopping all Reflex processes..." -ForegroundColor Yellow

# Node.jsプロセスを停止（Reflexフロントエンド）
Get-Process node -ErrorAction SilentlyContinue | Where-Object {
    $_.Path -like "*reflex*"
} | Stop-Process -Force

# Pythonプロセスのうち、Reflexに関連するものだけを停止
Get-Process python -ErrorAction SilentlyContinue | Where-Object {
    $_.CommandLine -like "*reflex*" -or $_.CommandLine -like "*uvicorn*"
} | Stop-Process -Force

# ポート3000と8000を使用しているプロセスを確認
$port3000 = netstat -ano | findstr :3000 | findstr LISTENING
$port8000 = netstat -ano | findstr :8000 | findstr LISTENING

if ($port3000) {
    Write-Host "Port 3000 is still in use, cleaning up..." -ForegroundColor Yellow
    $pid = ($port3000 -split '\s+')[-1]
    taskkill /PID $pid /F
}

if ($port8000) {
    Write-Host "Port 8000 is still in use, cleaning up..." -ForegroundColor Yellow
    $pid = ($port8000 -split '\s+')[-1]
    taskkill /PID $pid /F
}

Write-Host "All Reflex processes stopped." -ForegroundColor Green