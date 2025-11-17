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

# フロントエンドの存在確認
echo ""
echo "Checking frontend build:"
if [ -d "frontend" ]; then
    echo "✓ Frontend directory exists"
    ls -lh frontend/ | head -5
else
    echo "✗ Frontend directory NOT found"
    echo "Available directories:"
    ls -ld */ 2>/dev/null || echo "No directories found"
fi

# Reflexアプリケーションの起動
echo ""
echo "Starting Reflex production server..."
echo "- Using production mode with backend host 0.0.0.0"
echo ""

# 本番モードで起動
# --backend-host 0.0.0.0: Render.comからのリクエストを受け付ける
exec reflex run --env prod --backend-host 0.0.0.0 --loglevel info
