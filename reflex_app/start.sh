#!/bin/bash
# Render.com用起動スクリプト
# Reflexエクスポート済みSPAを静的サーバーで配信

set -e

echo "==================================="
echo "Reflex Static Server for Render"
echo "==================================="

# 環境変数の確認
echo ""
echo "Environment Check:"
echo "- PORT: ${PORT:-8000}"

# 静的ファイルの確認
if [ ! -d ".web/build" ]; then
    echo "ERROR: .web/build directory not found!"
    echo "Run 'reflex export' during build phase."
    exit 1
fi

echo "✓ Static files found: .web/build"
ls -lh .web/build/ 2>/dev/null | head -5

# PythonのHTTPサーバーで静的ファイルを配信
echo ""
echo "Starting static file server..."
echo "- Port: $PORT"
echo "- Directory: .web/build"

cd .web/build
exec python -m http.server $PORT --bind 0.0.0.0
