# ドメイン制限認証システム - 実装ガイド

**バージョン**: 1.0
**実装日**: 2025年11月22日
**ステータス**: 本番運用可能 ✅

## 概要

求職者分析ダッシュボード（Reflex）に、ドメイン制限付きメール認証システムを実装しました。

### 実装内容

- **ドメイン制限**: @f-a-c.co.jp、@cyxen.co.jp のみアクセス可能
- **共通パスワード**: 全ユーザー共通のパスワードで認証
- **Tursoデータベース連携**: クラウドデータベースからのデータ取得
- **サーバーサイド認証**: セキュアな認証フロー

---

## アーキテクチャ

```
ユーザー
    ↓
ログインページ（login.py）
    ↓
認証処理（auth.py）
    ├─ ドメイン検証
    ├─ パスワード検証
    └─ セッション管理
    ↓
ダッシュボード（mapcomplete_dashboard.py）
    ↓
Tursoデータベース（18,877行）
```

---

## ファイル構成

### 1. 環境変数設定ファイル

**ファイル**: `.env`

```env
# ドメイン制限認証設定
# 許可ドメイン（カンマ区切り）
ALLOWED_DOMAINS=f-a-c.co.jp,cyxen.co.jp

# 認証パスワード（全ユーザー共通）
AUTH_PASSWORD=cyxen_2025_12_01

# セッション秘密鍵
SESSION_SECRET=f8e9a7b6c5d4e3f2a1b0c9d8e7f6a5b4c3d2e1f0a9b8c7d6e5f4a3b2c1d0e9f8

# Tursoクラウドデータベース設定
TURSO_DATABASE_URL=libsql://job-jobseekeranalyzer-makimaki1006.aws-ap-northeast-1.turso.io
TURSO_AUTH_TOKEN=eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9.eyJhIjoicnciLCJpYXQiOjE3NjM3ODk2NzgsImlkIjoiNTU1YzQwMzgtZjI0MS00ODAwLTgzYTctYmE4MmYzOGQyZGFhIiwicmlkIjoiNjJmNTFkMjgtNTdhNC00M2Y2LWIzZTAtYmRlZGZiM2YxNmY1In0.Q-WMFowjDxhbdUqkeKYG7y4qkhfbsFaVgqKtAyU0y2bdCTNCHOp8IQsHFYgJ6wdT4m96WIXtP4UO-jRbB8woBg
```

**重要**: `.env`ファイルは`.gitignore`に追加し、Gitにコミットしないでください。

---

### 2. 認証ロジック

**ファイル**: `mapcomplete_dashboard/auth.py`

**主要機能**:

#### AuthState クラス
```python
class AuthState(rx.State):
    """認証状態管理"""

    # 認証状態（サーバーサイドで管理）
    is_authenticated: bool = False
    user_email: str = ""

    # フォーム入力
    email: str = ""
    password: str = ""

    # エラー
    error_message: str = ""
```

#### login() メソッド
```python
def login(self):
    """ログイン処理（ドメイン検証 + パスワード）"""

    # 1. 入力チェック
    if not self.email or not self.password:
        self.error_message = "メールアドレスとパスワードを入力してください"
        return

    # 2. メールアドレス形式チェック
    if "@" not in self.email:
        self.error_message = "有効なメールアドレスを入力してください"
        return

    # 3. ドメイン抽出
    email_domain = self.email.split("@")[1]

    # 4. ドメイン検証
    if email_domain not in ALLOWED_DOMAINS:
        self.error_message = f"このドメイン（@{email_domain}）は許可されていません"
        return

    # 5. パスワード検証
    auth_password = os.getenv("AUTH_PASSWORD")
    if self.password != auth_password:
        self.error_message = "パスワードが間違っています"
        return

    # 6. 認証成功
    self.is_authenticated = True
    self.user_email = self.email

    # 7. ダッシュボードへリダイレクト
    return rx.redirect("/")
```

#### logout() メソッド
```python
def logout(self):
    """ログアウト"""
    self.is_authenticated = False
    self.user_email = ""
    self.email = ""
    self.password = ""
    self.error_message = ""

    return rx.redirect("/login")
```

#### require_auth デコレータ
```python
def require_auth(component_fn):
    """認証が必要なコンポーネントをデコレート"""
    def wrapper(*args, **kwargs):
        return rx.cond(
            AuthState.is_authenticated,
            component_fn(*args, **kwargs),
            rx.redirect("/login")
        )
    return wrapper
```

---

### 3. ログインページUI

**ファイル**: `mapcomplete_dashboard/login.py`

**画面構成**:

```
┌─────────────────────────────┐
│         🗺️                  │
│  求職者分析ダッシュボード      │
│                             │
│  ┌─────────────────────┐   │
│  │ メールアドレス         │   │
│  └─────────────────────┘   │
│                             │
│  ┌─────────────────────┐   │
│  │ パスワード            │   │
│  └─────────────────────┘   │
│                             │
│  ┌─────────────────────┐   │
│  │     ログイン          │   │
│  └─────────────────────┘   │
│                             │
│  [エラーメッセージ表示領域]   │
│                             │
│  許可ドメイン:               │
│  @f-a-c.co.jp               │
│  @cyxen.co.jp               │
└─────────────────────────────┘
```

**主要コード**:

```python
def login_page() -> rx.Component:
    """ログイン画面"""
    return rx.box(
        rx.vstack(
            # ロゴエリア
            rx.heading("🗺️", size="9"),
            rx.heading("求職者分析ダッシュボード", size="7"),

            # ログインフォーム
            rx.input(
                placeholder="メールアドレス",
                value=AuthState.email,
                on_change=AuthState.set_email,
                type="email"
            ),
            rx.input(
                placeholder="パスワード",
                value=AuthState.password,
                on_change=AuthState.set_password,
                type="password"
            ),
            rx.button(
                "ログイン",
                on_click=AuthState.login
            ),

            # エラーメッセージ
            rx.cond(
                AuthState.error_message != "",
                rx.box(
                    rx.text(AuthState.error_message, color="#D55E00")
                )
            ),

            # 注意書き
            rx.text("※ 以下のドメインのメールアドレスでログイン可能です"),
            rx.text("@f-a-c.co.jp / @cyxen.co.jp")
        )
    )
```

---

## データベース設定

### Turso クラウドデータベース

**データベース情報**:

| 項目 | 値 |
|------|-----|
| Organization | makimaki1006 |
| Database | job-jobseekeranalyzer |
| Region | ap-northeast-1 (Tokyo) |
| URL | libsql://job-jobseekeranalyzer-makimaki1006.aws-ap-northeast-1.turso.io |
| データ行数 | 18,877行 |
| 都道府県数 | 48 |
| 市区町村数 | 22 |

**接続設定** (`db_helper.py`):

```python
TURSO_DATABASE_URL = os.getenv("TURSO_DATABASE_URL", "")
TURSO_AUTH_TOKEN = os.getenv("TURSO_AUTH_TOKEN", "")

if TURSO_DATABASE_URL and TURSO_AUTH_TOKEN:
    # libsql:// を https:// に変換
    if TURSO_DATABASE_URL.startswith('libsql://'):
        TURSO_DATABASE_URL = TURSO_DATABASE_URL.replace('libsql://', 'https://')

    # Turso接続
    import libsql_client
    _HAS_TURSO = True
```

---

## 起動方法

### 1. 環境変数の設定

`.env`ファイルが存在し、以下の項目が設定されていることを確認：

- `ALLOWED_DOMAINS`
- `AUTH_PASSWORD`
- `SESSION_SECRET`
- `TURSO_DATABASE_URL`
- `TURSO_AUTH_TOKEN`

### 2. 依存パッケージのインストール

```bash
pip install reflex libsql-client python-dotenv
```

### 3. サーバー起動

```bash
cd "C:\Users\fuji1\OneDrive\Pythonスクリプト保管\job_medley_project\reflex_app"
reflex run --backend-port 8003 --frontend-port 3003
```

### 4. サーバー起動確認

以下のメッセージが表示されれば成功：

```
[DB] サーバーサイドフィルタリングを有効化 (turso)
[INFO] DB全体: 18,877行, フィルタ済み: 9行
[INFO] 都道府県数: 48, 市区町村数: 22
[INFO] 選択: 北海道 札幌市中央区

--------------------------------- App Running ---------------------------------
App running at: http://localhost:3003/
Backend running at: http://0.0.0.0:8003
```

---

## 使用方法

### 1. ログイン

1. ブラウザで http://localhost:3003/ にアクセス
2. ログインページが表示されます
3. **メールアドレス**: 許可されたドメインのアドレス（例: user@f-a-c.co.jp）
4. **パスワード**: `cyxen_2025_12_01`
5. 「ログイン」ボタンをクリック

### 2. 認証エラーの対処

#### エラー: 「このドメイン（@xxx）は許可されていません」

**原因**: 許可されていないドメインのメールアドレスを使用

**対処法**: @f-a-c.co.jp または @cyxen.co.jp のメールアドレスを使用

#### エラー: 「パスワードが間違っています」

**原因**: パスワードが正しくない

**対処法**: `.env`ファイルの`AUTH_PASSWORD`の値を確認

#### エラー: 「メールアドレスとパスワードを入力してください」

**原因**: 入力フィールドが空

**対処法**: 両方のフィールドに入力

### 3. ログアウト

ダッシュボード右上の「ログアウト」ボタンをクリック

---

## セキュリティ仕様

### 認証フロー

1. **入力検証**: メールアドレス形式とパスワードの存在確認
2. **ドメイン検証**: メールアドレスのドメイン部分を抽出し、許可リストと照合
3. **パスワード検証**: 環境変数のパスワードと照合
4. **セッション管理**: Reflexのサーバーサイド状態管理でセッション保持
5. **リダイレクト**: 認証成功時はダッシュボードへ、未認証時はログインページへ

### データ保護

- **環境変数**: 認証情報は`.env`ファイルで管理、Gitにコミットしない
- **サーバーサイド認証**: 認証状態はサーバー側で管理、クライアント側に保存しない
- **HTTPS推奨**: 本番環境ではHTTPS通信を使用

---

## トラブルシューティング

### 問題: サーバーが起動しない

**確認事項**:
1. `.env`ファイルが存在するか
2. `TURSO_DATABASE_URL`と`TURSO_AUTH_TOKEN`が設定されているか
3. `libsql-client`がインストールされているか

```bash
pip show libsql-client
```

### 問題: データベース接続エラー

**確認事項**:
1. Tursoの認証トークンが正しいか
2. データベースURLが正しいか
3. ネットワーク接続が正常か

**デバッグ方法**:
```bash
# サーバーログを確認
# [DB] サーバーサイドフィルタリングを有効化 (turso)
# が表示されていれば接続成功
```

### 問題: ログインできない

**確認事項**:
1. メールアドレスのドメインが許可リストに含まれているか
2. パスワードが正しいか（`.env`の`AUTH_PASSWORD`と一致）
3. ブラウザのコンソールにエラーが表示されていないか

---

## メンテナンス

### 許可ドメインの追加

`.env`ファイルの`ALLOWED_DOMAINS`を編集：

```env
# 追加例
ALLOWED_DOMAINS=f-a-c.co.jp,cyxen.co.jp,newdomain.co.jp
```

サーバーを再起動して反映。

### パスワードの変更

`.env`ファイルの`AUTH_PASSWORD`を編集：

```env
AUTH_PASSWORD=新しいパスワード
```

サーバーを再起動して反映。

### Turso認証トークンの更新

Tursoダッシュボードで新しいトークンを発行後、`.env`ファイルを更新：

```env
TURSO_AUTH_TOKEN=新しいトークン
```

サーバーを再起動して反映。

---

## 技術仕様

### 使用技術

- **Reflex**: v0.8.19（Pythonウェブフレームワーク）
- **Turso**: クラウドSQLiteデータベース
- **libsql-client**: Turso接続用Pythonクライアント
- **python-dotenv**: 環境変数管理

### サーバー設定

- **バックエンドポート**: 8003
- **フロントエンドポート**: 3003
- **認証方式**: サーバーサイドセッション管理
- **データベース**: Turso（サーバーサイドフィルタリング有効）

---

## 参考情報

### 関連ドキュメント

- [Tursoデータベース統合ガイド](TURSO_DATABASE_INTEGRATION.md)
- [Reflexドキュメント](https://reflex.dev/docs)
- [libsql-client ドキュメント](https://github.com/libsql/libsql-client-py)

### プロジェクト構成

```
reflex_app/
├── .env                          # 環境変数（Git管理外）
├── mapcomplete_dashboard/
│   ├── auth.py                   # 認証ロジック
│   ├── login.py                  # ログインページUI
│   ├── mapcomplete_dashboard.py  # メインダッシュボード
│   └── db_helper.py              # データベース接続
├── docs/
│   ├── DOMAIN_AUTHENTICATION_GUIDE.md  # このドキュメント
│   └── TURSO_DATABASE_INTEGRATION.md   # Turso統合ガイド
└── requirements.txt              # 依存パッケージ
```

---

## 更新履歴

| 日付 | バージョン | 変更内容 |
|------|-----------|---------|
| 2025-11-22 | 1.0 | 初版作成 - ドメイン制限認証システム実装完了 |

---

## サポート

問題が発生した場合は、以下を確認してください：

1. サーバーログ（コンソール出力）
2. ブラウザのデベロッパーツール（F12）のコンソール
3. `.env`ファイルの設定内容

それでも解決しない場合は、プロジェクト管理者に連絡してください。
