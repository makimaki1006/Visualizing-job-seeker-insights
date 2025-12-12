"""ログイン画面（ドメイン制限）"""
import reflex as rx
from .auth import AuthState


# カラー定義（既存のダッシュボードと統一）
BG_COLOR = "#0a0f1e"
TEXT_COLOR = "#f8fafc"
MUTED_COLOR = "#94a3b8"
PRIMARY_COLOR = "#0072B2"
BORDER_COLOR = "#1e293b"


def login_page() -> rx.Component:
    """ログイン画面

    メールアドレスのドメインで認証します。
    許可されたドメイン（@f-a-c.co.jp, @cyxen.co.jp）のみアクセス可能。
    """
    return rx.box(
        rx.vstack(
            # ロゴエリア
            rx.box(
                rx.heading(
                    "🗺️",
                    size="9",
                    margin_bottom="0.5rem"
                ),
                rx.heading(
                    "求職者分析ダッシュボード",
                    size="7",
                    color=TEXT_COLOR,
                    margin_bottom="1rem"
                ),
                text_align="center"
            ),

            # ログインフォーム - rx.formでフォーム送信を使用
            rx.form(
                rx.vstack(
                    # メールアドレス入力
                    rx.input(
                        placeholder="メールアドレス",
                        name="email",
                        type="email",
                        size="3",
                        width="100%",
                        required=True,
                    ),

                    # パスワード入力
                    rx.input(
                        placeholder="パスワード",
                        name="password",
                        type="password",
                        size="3",
                        width="100%",
                        required=True,
                    ),

                    # ログインボタン（type="submit"でフォーム送信）
                    rx.button(
                        "ログイン",
                        type="submit",
                        size="3",
                        width="100%",
                        color_scheme="blue"
                    ),

                    spacing="3",
                    width="100%"
                ),
                on_submit=AuthState.handle_login_submit,
                reset_on_submit=False,
                width="100%",
            ),

            # エラーメッセージ
            rx.cond(
                AuthState.error_message != "",
                rx.box(
                    rx.text(
                        AuthState.error_message,
                        color="#D55E00",
                        font_size="0.9rem",
                        white_space="pre-wrap"
                    ),
                    padding="1rem",
                    background="rgba(213, 94, 0, 0.1)",
                    border_radius="8px",
                    border=f"1px solid rgba(213, 94, 0, 0.3)",
                    margin_top="1rem",
                    width="100%"
                )
            ),

            # 注意書き
            rx.box(
                rx.vstack(
                    rx.text(
                        "※ 以下のドメインのメールアドレスでログイン可能です",
                        color=MUTED_COLOR,
                        font_size="0.85rem",
                        text_align="center"
                    ),
                    rx.text(
                        "@f-a-c.co.jp / @cyxen.co.jp",
                        color=PRIMARY_COLOR,
                        font_size="0.85rem",
                        font_weight="500",
                        text_align="center"
                    ),
                    spacing="1"
                ),
                margin_top="2rem"
            ),

            spacing="4",
            width="100%",
            max_width="400px"
        ),
        display="flex",
        justify_content="center",
        align_items="center",
        min_height="100vh",
        background=BG_COLOR,
        padding="2rem"
    )
