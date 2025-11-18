#!/bin/bash
# Render.com用起動スクリプト
# Reflexアプリケーションの起動

set -e

echo "==================================="
echo "Reflex App Start Script for Render"
echo "==================================="

# 環境変数の確認
echo ""
echo "Environment Check:"
echo "- DATABASE_URL: ${DATABASE_URL:0:30}... (${#DATABASE_URL} chars)"
echo "- PORT: ${PORT:-8000}"

# 静的フロントエンドの存在確認
echo ""
echo "Checking exported frontend:"
STATIC_DIR=""
if [ -d ".web/build" ]; then
    echo "✓ Export directory found: .web/build"
    STATIC_DIR=".web/build"
    ls -lh .web/build/ 2>/dev/null | head -5
elif [ -d ".web/_static" ]; then
    echo "✓ Export directory found: .web/_static"
    STATIC_DIR=".web/_static"
    ls -lh .web/_static/ 2>/dev/null | head -5
elif [ -d "frontend" ]; then
    echo "✓ Frontend directory found"
    STATIC_DIR="frontend"
    ls -lh frontend/ 2>/dev/null | head -5
else
    echo "✗ No static frontend found"
    echo "Available directories:"
    ls -d .web*/ */ 2>/dev/null | grep -v "^mapcomplete_dashboard" || echo "No directories found"
fi

# Reflexアプリケーションの起動
echo ""
echo "Starting Reflex production server..."
echo "- Mode: Production with exported build"
echo "- Backend port: $PORT"
echo "- Static files: $STATIC_DIR"

# Reflexをプロダクションモードで起動
# 注意: --backend-onlyは使用せず、通常のprodモードで起動
# .web/buildの静的ファイルは自動的に配信される
exec reflex run --env prod --loglevel info
