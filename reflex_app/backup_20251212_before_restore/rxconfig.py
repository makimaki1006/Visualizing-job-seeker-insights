"""Reflex設定ファイル"""

import reflex as rx
import os

# Reflex Cloud環境検出
is_reflex_cloud = os.getenv("REFLEX_DEPLOYMENT") is not None

config = rx.Config(
    app_name="mapcomplete_dashboard",
    # セッション管理設定
    timeout=1800,  # 30分（秒単位）
    # データベース設定（不要だがReflexのデフォルト設定）
    db_url="sqlite:///reflex.db",
)
