"""Reflex設定ファイル"""

import reflex as rx
import os

config = rx.Config(
    app_name="mapcomplete_dashboard",
    # 本番環境用設定（Render.com動的ポート対応）
    backend_port=int(os.getenv("PORT", 8000)),  # Render.comの動的ポート対応
    frontend_port=int(os.getenv("PORT", 8000)),  # 本番環境ではバックエンドと同じポート
    # 本番デプロイモード設定
    deploy_url="https://job-medley-dashboard.onrender.com",  # Render.comのURL
    # セッション管理設定
    timeout=1800,  # 30分（秒単位）
    # データベース設定（不要だがReflexのデフォルト設定）
    db_url="sqlite:///reflex.db",
)
