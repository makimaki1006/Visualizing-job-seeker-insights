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
echo "- Exported frontend: $(ls -d frontend 2>/dev/null && echo 'YES' || echo 'NO')"

# Reflexアプリケーションの起動
echo ""
echo "Starting Reflex production server..."
echo "- Backend will serve both API and static frontend files"
echo ""

# 本番モードで起動（バックエンドのみ、フロントエンドは静的ファイル配信）
# --backend-only: バックエンドサーバーのみ起動
# フロントエンドは reflex export で生成された静的ファイルを配信
exec reflex run --env prod --backend-only --loglevel info
