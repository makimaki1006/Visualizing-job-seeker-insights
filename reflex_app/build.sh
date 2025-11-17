#!/bin/bash
# Render.com用ビルドスクリプト
# Reflexアプリケーションのビルドプロセス

set -e

echo "==================================="
echo "Reflex App Build Script for Render"
echo "==================================="

# 1. Pythonパッケージのインストール
echo ""
echo "Step 1: Installing Python dependencies..."
pip install -r requirements.txt

# 2. Reflexアプリケーションの初期化（既存プロジェクトのため、rxconfig.pyが存在すればスキップ）
echo ""
echo "Step 2: Checking Reflex configuration..."
if [ ! -f "rxconfig.py" ]; then
    echo "[WARNING] rxconfig.py not found. This should not happen in production."
    echo "[INFO] Skipping reflex init (using existing project structure)"
fi

# 2.5. データディレクトリ作成（SQLiteフォールバック対策）
echo ""
echo "Step 2.5: Creating data directory..."
mkdir -p data
echo "[INFO] Data directory created: $(pwd)/data"

# 3. フロントエンドのビルド（reflex exportでまとめて実行）
echo ""
echo "Step 3: Building frontend and backend..."
reflex export --no-zip

# 5. データベーススキーマの初期化（オプション）
if [ ! -z "$DATABASE_URL" ]; then
    echo ""
    echo "Step 5: Initializing database schema (PostgreSQL)..."
    python -c "
import sys
from pathlib import Path

# 現在のディレクトリをパスに追加（reflex_app/）
sys.path.insert(0, str(Path.cwd()))

from database_schema import get_all_create_table_sqls
import psycopg2
import os

conn = psycopg2.connect(os.environ['DATABASE_URL'])
cursor = conn.cursor()

success_count = 0
fail_count = 0

# PostgreSQL用のSQL文を生成
for sql in get_all_create_table_sqls(db_type='postgresql'):
    try:
        cursor.execute(sql)
        success_count += 1
        print(f'[OK] Executed: {sql[:50]}...')
    except Exception as e:
        fail_count += 1
        print(f'[SKIP] {e}')

conn.commit()
conn.close()
print(f'[INFO] Database schema initialization complete: {success_count} success, {fail_count} skipped')
"
else
    echo ""
    echo "Step 5: Skipping database initialization (DATABASE_URL not set)"
    echo "[INFO] SQLite will be used for local development"
fi

echo ""
echo "==================================="
echo "Build Complete!"
echo "==================================="
