"""ドメイン制限認証モジュール

許可されたドメインのメールアドレスのみアクセスを許可します。
AuthStateはDashboardStateのサブステートとして定義されています。
LocalStorageで認証状態を永続化し、ページリロード後も維持します。

E2Eテストモード:
    環境変数 E2E_TEST_MODE=true を設定すると、認証をスキップします。
    これはPlaywright等のE2Eテストで使用します。
"""
import os
import reflex as rx
from dotenv import load_dotenv

# 環境変数を読み込み
load_dotenv()

# E2Eテストモード（認証スキップ）
E2E_TEST_MODE = os.getenv("E2E_TEST_MODE", "").lower() == "true"
if E2E_TEST_MODE:
    print("[INFO] E2E_TEST_MODE enabled - 認証がスキップされます")

# 許可ドメイン（カンマ区切り）
ALLOWED_DOMAINS_STR = os.getenv("ALLOWED_DOMAINS", "f-a-c.co.jp,cyxen.co.jp")
ALLOWED_DOMAINS = [d.strip() for d in ALLOWED_DOMAINS_STR.split(",") if d.strip()]


# 注意: AuthStateは独立したStateとして定義。
# Reflexでは複数のStateを使用可能だが、
# イベントハンドラが呼び出されない場合は、
# コンポーネント内でこのStateが正しく参照されているか確認が必要。
class AuthState(rx.State):
    """認証状態管理（LocalStorage永続化対応）"""

    # 認証状態（LocalStorageで永続化）
    _is_authenticated: bool = False
    _user_email: str = ""

    # LocalStorage用のキー（永続化）
    auth_token: str = rx.LocalStorage(name="auth_token")
    stored_email: str = rx.LocalStorage(name="stored_email")

    # フォーム入力
    email: str = ""
    password: str = ""

    # エラー
    error_message: str = ""

    @rx.var
    def is_authenticated(self) -> bool:
        """認証状態を返す（LocalStorageから復元）"""
        # E2Eテストモードでは常に認証済み
        if E2E_TEST_MODE:
            return True
        # LocalStorageにトークンがあれば認証済み
        if self.auth_token == "authenticated":
            self._is_authenticated = True
            return True
        return self._is_authenticated

    @rx.var
    def user_email(self) -> str:
        """ユーザーメールを返す（LocalStorageから復元）"""
        if self.stored_email:
            self._user_email = self.stored_email
            return self.stored_email
        return self._user_email

    def set_email(self, value: str):
        """メールアドレスを設定"""
        self.email = value

    def set_password(self, value: str):
        """パスワードを設定"""
        self.password = value

    def handle_login_submit(self, form_data: dict):
        """フォーム送信からのログイン処理"""
        print(f"[DEBUG] Form submitted: {form_data}")
        self.email = form_data.get("email", "")
        self.password = form_data.get("password", "")
        return self.login()

    def force_login(self):
        """デバッグ用: 強制ログイン（LocalStorage永続化）"""
        import sys
        print("[DEBUG] Force login triggered!", file=sys.stderr, flush=True)
        print("[DEBUG] Force login triggered!", flush=True)
        self._is_authenticated = True
        self._user_email = "debug@cyxen.co.jp"
        self.auth_token = "authenticated"  # LocalStorageに保存
        self.stored_email = "debug@cyxen.co.jp"  # LocalStorageに保存
        self.error_message = ""
        print("[DEBUG] LocalStorage auth_token set to 'authenticated'", flush=True)
        return rx.redirect("/")

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

        # 認証成功（LocalStorage永続化）
        self._is_authenticated = True
        self._user_email = self.email
        self.auth_token = "authenticated"  # LocalStorageに保存
        self.stored_email = self.email  # LocalStorageに保存
        self.error_message = ""

        print(f"[INFO] ログイン成功: {self.email}")

        # ダッシュボードへリダイレクト
        return rx.redirect("/")

    def logout(self):
        """ログアウト（LocalStorageクリア）"""
        print(f"[INFO] ログアウト: {self.user_email}")

        self._is_authenticated = False
        self._user_email = ""
        self.auth_token = ""  # LocalStorageクリア
        self.stored_email = ""  # LocalStorageクリア
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
