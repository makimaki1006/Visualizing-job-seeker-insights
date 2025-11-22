"""ドメイン制限認証モジュール

許可されたドメインのメールアドレスのみアクセスを許可します。
"""
import os
import reflex as rx
from dotenv import load_dotenv

# 環境変数を読み込み
load_dotenv()

# 許可ドメイン（カンマ区切り）
ALLOWED_DOMAINS_STR = os.getenv("ALLOWED_DOMAINS", "f-a-c.co.jp,cyxen.co.jp")
ALLOWED_DOMAINS = [d.strip() for d in ALLOWED_DOMAINS_STR.split(",") if d.strip()]


class AuthState(rx.State):
    """認証状態管理"""

    # 認証状態（LocalStorageで永続化）
    is_authenticated: bool = False
    user_email: str = ""

    # フォーム入力
    email: str = ""
    password: str = ""

    # エラー
    error_message: str = ""

    def login(self):
        """ログイン処理（ドメイン検証 + パスワード）"""
        print(f"[DEBUG] Login attempt: email={self.email}")

        # 入力チェック
        if not self.email or not self.password:
            self.error_message = "メールアドレスとパスワードを入力してください"
            return

        # メールアドレス形式チェック
        if "@" not in self.email:
            self.error_message = "有効なメールアドレスを入力してください"
            return

        # ドメイン抽出
        email_domain = self.email.split("@")[1] if "@" in self.email else ""

        # ドメイン検証
        if email_domain not in ALLOWED_DOMAINS:
            self.error_message = f"このドメイン（@{email_domain}）は許可されていません"
            allowed_list = " / ".join([f"@{d}" for d in ALLOWED_DOMAINS])
            self.error_message += f"\n許可ドメイン: {allowed_list}"
            print(f"[WARN] Domain not allowed: {email_domain}")
            return

        # パスワード検証（環境変数から取得）
        auth_password = os.getenv("AUTH_PASSWORD")
        if not auth_password:
            self.error_message = "認証設定が不足しています（.envファイルを確認してください）"
            print("[ERROR] AUTH_PASSWORDが設定されていません")
            return

        if self.password != auth_password:
            self.error_message = "パスワードが間違っています"
            print(f"[WARN] パスワード認証失敗: {self.email}")
            return

        # 認証成功
        self.is_authenticated = True
        self.user_email = self.email
        self.error_message = ""

        print(f"[INFO] ログイン成功: {self.email}")

        # ダッシュボードへリダイレクト
        return rx.redirect("/")

    def logout(self):
        """ログアウト"""
        print(f"[INFO] ログアウト: {self.user_email}")

        self.is_authenticated = False
        self.user_email = ""
        self.email = ""
        self.password = ""
        self.error_message = ""

        # ログインページへリダイレクト
        return rx.redirect("/login")


def require_auth(component_fn):
    """認証が必要なコンポーネントをデコレート

    使用例:
        @require_auth
        def protected_page():
            return rx.text("This is protected")
    """
    def wrapper(*args, **kwargs):
        return rx.cond(
            AuthState.is_authenticated,
            component_fn(*args, **kwargs),
            rx.redirect("/login")
        )
    return wrapper
