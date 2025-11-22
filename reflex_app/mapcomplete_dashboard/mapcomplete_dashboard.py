"""MapComplete統合ダッシュボード（GAS完全再現版）

GAS統合ダッシュボード（map_complete_integrated.html）の完全再現
- 10パネル: overview, supply, career, urgency, persona, cross, flow, gap, rarity, competition
- 右サイドバーレイアウト（440px、リサイズ可能）
- GAS配色（深いネイビー基調）
- CSVアップロード機能（ドラッグ&ドロップ）
- 色覚バリアフリー対応（Okabe-Itoカラーパレット）2025-11-14更新
"""

import reflex as rx
import pandas as pd
import json
import unicodedata as ud
from typing import Optional, List, Dict, Any
from datetime import datetime

# 認証モジュールのインポート
from .auth import AuthState, require_auth
from .login import login_page

# db_helper.py のインポート（データベース統合用）
# rootDirectoryがreflex_appなので、sys.path操作不要
try:
    from db_helper import (
        get_connection, get_db_type, query_df, get_all_data,
        get_prefectures, get_municipalities, get_filtered_data,
        get_row_count_by_location
    )
    _DB_AVAILABLE = True
except ImportError:
    _DB_AVAILABLE = False
    print("[WARNING] db_helper.py not found. Database features disabled.")

# =====================================
# 色覚バリアフリー対応配色（Okabe-Ito Color Palette準拠）
# =====================================
BG_COLOR = "#0d1525"                        # 深いネイビー基調
PANEL_BG = "rgba(12, 20, 37, 0.95)"        # サイドバー：半透明濃紺
CARD_BG = "rgba(15, 23, 42, 0.82)"         # カード背景
TEXT_COLOR = "#f8fafc"                      # 文字
MUTED_COLOR = "rgba(226, 232, 240, 0.75)"  # 補助文字
BORDER_COLOR = "rgba(148, 163, 184, 0.22)" # 枠線

# 色覚多様性対応カラーパレット（赤緑色弱・青黄色弱でも識別可能）
PRIMARY_COLOR = "#0072B2"                   # 濃い青（Blue）
SECONDARY_COLOR = "#E69F00"                 # オレンジ（Orange）- 赤緑色弱でも識別◎
ACCENT_3 = "#CC79A7"                        # 赤紫（Reddish Purple）- 明度高く識別◎
ACCENT_4 = "#009E73"                        # 青緑（Bluish Green）- 赤緑色弱でも識別◎
ACCENT_5 = "#F0E442"                        # 黄色（Yellow）- 明度最高、視認性◎
ACCENT_6 = "#D55E00"                        # 朱色（Vermillion）- 赤緑色弱でも識別◎
ACCENT_7 = "#56B4E9"                        # スカイブルー（Sky Blue）- 明度高く識別◎

# 色覚バリアフリー対応COLOR配列（Okabe-Ito準拠）
COLOR_PALETTE = ['#0072B2', '#E69F00', '#CC79A7', '#009E73', '#F0E442', '#D55E00', '#56B4E9']

# 用途別色エイリアス
WARNING_COLOR = ACCENT_6      # 朱色（警告用）
SUCCESS_COLOR = ACCENT_4      # 青緑（成功用）

# =====================================
# 10パネル定義（GAS TABS配列に対応）
# map_complete_integrated.html Line 2195-2206
# =====================================
TABS = [
    {"id": "overview", "label": "総合概要"},
    {"id": "supply", "label": "人材供給"},
    {"id": "career", "label": "キャリア分析"},
    {"id": "urgency", "label": "緊急度分析"},
    {"id": "persona", "label": "ペルソナ分析"},
    {"id": "cross", "label": "クロス分析"},
    {"id": "flow", "label": "フロー分析"},
    {"id": "gap", "label": "需給バランス"},
    {"id": "rarity", "label": "希少人材分析"},
    {"id": "competition", "label": "人材プロファイル"},
    {"id": "jobmap", "label": "🗺️ 求人地図"},  # 新規追加
]


# =====================================
# State
# =====================================
class DashboardState(rx.State):
    """ダッシュボード状態管理

    サーバーサイドフィルタリング対応版:
    - 全データ(df)を保持せず、フィルタ済みデータ(filtered_df)のみ保持
    - メモリ消費: 70MB/ユーザー → 0.1-1MB/ユーザー
    - 30人以上の同時利用に対応
    """

    # データ（サーバーサイドフィルタリング: フィルタ済みデータのみ保持）
    df: Optional[pd.DataFrame] = None  # フィルタ済みデータ（選択地域のみ、数十〜数百行）
    df_full: Optional[pd.DataFrame] = None  # CSV全データ（CSVアップロード時のみ使用）
    is_loaded: bool = False
    total_rows: int = 0  # DB全体の行数（参考情報）
    filtered_rows: int = 0  # 現在のフィルタ済み行数
    csv_uploaded: bool = False  # CSVアップロード済みフラグ（True時はDB使用しない）

    # フィルタ
    selected_prefecture: str = ""
    selected_municipality: str = ""
    prefectures: list[str] = []
    municipalities: list[str] = []

    # タブ
    active_tab: str = "overview"

    # 地域サマリー
    city_name: str = "-"
    city_meta: str = "-"
    quality_badge: str = "品質未評価"

    # 求人地図（職種選択）
    selected_job_type: str = "介護職"  # デフォルト職種

    def __init__(self, *args, **kwargs):
        """初期化: DB起動時ロード（サーバーサイドフィルタリング版）

        全データをロードせず、都道府県リストと初期地域のフィルタ済みデータのみ取得。
        メモリ消費: 70MB → 0.1-1MB
        """
        super().__init__(*args, **kwargs)

        # DB起動時ロード（軽量版）
        if _DB_AVAILABLE:
            try:
                db_type = get_db_type()

                # Step 1: 都道府県リストのみ取得（軽量クエリ）
                self.prefectures = get_prefectures()

                if len(self.prefectures) > 0:
                    # Step 2: 最初の都道府県を選択
                    first_pref = self.prefectures[0]
                    self.selected_prefecture = first_pref

                    # Step 3: 市区町村リスト取得
                    self.municipalities = get_municipalities(first_pref)

                    # Step 4: 最初の市区町村を選択し、フィルタ済みデータのみ取得
                    if len(self.municipalities) > 0:
                        first_muni = self.municipalities[0]
                        self.selected_municipality = first_muni

                        # フィルタ済みデータのみ取得（数十〜数百行）
                        self.df = self._normalize_df(get_filtered_data(first_pref, first_muni))
                        self.filtered_rows = len(self.df)
                    else:
                        # 市区町村がない場合は都道府県全体
                        self.df = self._normalize_df(get_filtered_data(first_pref))
                        self.filtered_rows = len(self.df)

                    self.is_loaded = True

                    # DB全体の行数を取得（参考情報）
                    if db_type == "turso":
                        count_df = query_df("SELECT COUNT(*) as cnt FROM job_seeker_data")
                    else:
                        count_df = query_df("SELECT COUNT(*) as cnt FROM mapcomplete_raw")

                    if not count_df.empty:
                        self.total_rows = int(count_df['cnt'].iloc[0])

                    print(f"[DB] サーバーサイドフィルタリング初期化成功 ({db_type})")
                    print(f"[INFO] DB全体: {self.total_rows:,}行, フィルタ済み: {self.filtered_rows}行")
                    print(f"[INFO] 都道府県数: {len(self.prefectures)}, 市区町村数: {len(self.municipalities)}")
                    print(f"[INFO] 選択: {self.selected_prefecture} {self.selected_municipality}")

            except Exception as e:
                print(f"[INFO] DB起動時ロード失敗（CSVアップロード待機）: {e}")

    def load_from_database(self):
        """データベースからデータを読み込む（ボタン押下時・サーバーサイドフィルタリング版）

        全データをロードせず、都道府県リストと初期地域のフィルタ済みデータのみ取得。
        メモリ消費: 70MB → 0.1-1MB
        """
        if not _DB_AVAILABLE:
            print("[ERROR] データベース機能が利用できません")
            return

        try:
            db_type = get_db_type()

            # Step 1: 都道府県リストのみ取得（軽量クエリ）
            self.prefectures = get_prefectures()

            if len(self.prefectures) > 0:
                # Step 2: 最初の都道府県を選択
                first_pref = self.prefectures[0]
                self.selected_prefecture = first_pref

                # Step 3: 市区町村リスト取得
                self.municipalities = get_municipalities(first_pref)

                # Step 4: 最初の市区町村を選択し、フィルタ済みデータのみ取得
                if len(self.municipalities) > 0:
                    first_muni = self.municipalities[0]
                    self.selected_municipality = first_muni

                    # フィルタ済みデータのみ取得（数十〜数百行）
                    self.df = self._normalize_df(get_filtered_data(first_pref, first_muni))
                    self.filtered_rows = len(self.df)
                else:
                    # 市区町村がない場合は都道府県全体
                    self.df = self._normalize_df(get_filtered_data(first_pref))
                    self.filtered_rows = len(self.df)

                self.is_loaded = True

                # DB全体の行数を取得（参考情報）
                if db_type == "turso":
                    count_df = query_df("SELECT COUNT(*) as cnt FROM job_seeker_data")
                else:
                    count_df = query_df("SELECT COUNT(*) as cnt FROM mapcomplete_raw")

                if not count_df.empty:
                    self.total_rows = int(count_df['cnt'].iloc[0])

                print(f"[DB] サーバーサイドフィルタリング読み込み成功 ({db_type})")
                print(f"[INFO] DB全体: {self.total_rows:,}行, フィルタ済み: {self.filtered_rows}行")
                print(f"[INFO] 都道府県数: {len(self.prefectures)}, 市区町村数: {len(self.municipalities)}")
            else:
                print("[ERROR] 都道府県リストを取得できませんでした")

        except Exception as e:
            print(f"[ERROR] データベースロード失敗: {e}")

    def _normalize_df(self, df: pd.DataFrame) -> pd.DataFrame:
        """基本的な正規化（Unicode正規化・前後空白除去・代表的な同義語置換・比率列の整形）。

        目的: 個別最適のハードコーディングを避け、再利用可能な最小限の正規化を一箇所に集約する。
        """
        if df is None or df.empty:
            return df

        # 1) Unicode正規化 + 前後空白除去（キー列）
        key_cols = [c for c in ['row_type', 'prefecture', 'municipality', 'category1', 'category2', 'category3'] if c in df.columns]
        for c in key_cols:
            try:
                df[c] = (
                    df[c]
                    .astype(str)
                    .map(lambda x: ud.normalize('NFKC', x))
                    .str.replace('\u3000', ' ', regex=False)  # 全角空白→半角
                    .str.strip()
                )
            except Exception:
                pass

        # 2) 区切り文字の統一（ペルソナ名等の中点・特殊記号のゆらぎ）
        # 想定区切り: ・ ･ · ／ / | , など → 中点「・」に統一
        sep_pattern = r"[\u00B7\u2027\u2219\u30FB\uFF65/\|,]"
        for c in ['category1']:
            if c in df.columns:
                try:
                    df[c] = df[c].str.replace(sep_pattern, '・', regex=True)
                except Exception:
                    pass

        # 3) 代表的な同義語の標準化（ジェンダー・就業・row_type・真偽）
        gender_map = {
            '女': '女性', '女性': '女性', 'female': '女性', 'Ｆ': '女性', 'F': '女性',
            '男': '男性', '男性': '男性', 'male': '男性', 'Ｍ': '男性', 'M': '男性',
        }
        employment_map = {
            '有職': '有職', '就業': '有職', '在職': '有職', 'employed': '有職',
            '無職': '無職', '非就業': '無職', 'unemployed': '無職',
            '学生': '学生', '在学': '学生', 'student': '学生',
        }
        # category* に対して適用（存在する列のみ）
        for c in ['category1', 'category2', 'category3']:
            if c in df.columns:
                try:
                    df[c] = df[c].replace(gender_map)
                    df[c] = df[c].replace(employment_map)
                except Exception:
                    pass

        # row_type は大文字＋前後空白除去
        if 'row_type' in df.columns:
            try:
                df['row_type'] = df['row_type'].astype(str).str.strip().str.upper()
            except Exception:
                pass

        # 真偽（has_national_license）は 'True'/'False' に標準化（文字列運用のため）
        if 'has_national_license' in df.columns:
            def _to_bool_str(v):
                s = str(v).strip().lower()
                if s in ['1', 'true', 't', 'yes', 'y']:
                    return 'True'
                if s in ['0', 'false', 'f', 'no', 'n']:
                    return 'False'
                return s if s in ['true', 'false'] else 'False'
            try:
                df['has_national_license'] = df['has_national_license'].map(_to_bool_str)
            except Exception:
                pass

        # 4) 比率列の整形（%や100ベース入力を0-1に正規化）
        ratio_cols = [
            'national_license_rate', 'female_ratio', 'top_age_ratio', 'top_employment_ratio'
        ]
        for c in ratio_cols:
            if c in df.columns:
                def _to_ratio(x):
                    try:
                        if isinstance(x, str):
                            xs = x.strip().replace('%', '')
                            if xs == '':
                                return None
                            val = float(xs)
                            return val / 100.0 if val > 1.0 else val
                        if pd.notna(x):
                            x = float(x)
                            return x / 100.0 if x > 1.0 else x
                        return None
                    except Exception:
                        return None
                try:
                    df[c] = df[c].map(_to_ratio)
                except Exception:
                    pass

        return df

    async def handle_upload(self, files: list[rx.UploadFile]):
        """CSVファイルアップロード処理"""
        if not files:
            return

        for file in files:
            upload_data = await file.read()

            try:
                # pandasでCSV読み込み
                import io
                # has_national_licenseを文字列として強制読み込み（ブール型自動変換を防止）
                self.df = pd.read_csv(
                    io.BytesIO(upload_data),
                    encoding='utf-8-sig',
                    low_memory=False,
                    dtype={'has_national_license': str}  # ブール型カラムを文字列として読み込む
                )
                # 正規化（前後空白など）
                self.df = self._normalize_df(self.df)
                self.df_full = self.df.copy()  # 全データを別変数に保存（市区町村リスト抽出用）
                self.total_rows = len(self.df)
                self.is_loaded = True
                self.csv_uploaded = True  # CSVアップロード済みフラグをTrueに設定

                # 都道府県リスト抽出
                if 'prefecture' in self.df.columns:
                    self.prefectures = sorted(self.df['prefecture'].dropna().unique().tolist())
                    # 最初の都道府県を自動選択して市区町村リストも初期化
                    if len(self.prefectures) > 0:
                        first_pref = self.prefectures[0]
                        self.selected_prefecture = first_pref

                        # 市区町村リスト初期化
                        if 'municipality' in self.df.columns:
                            filtered = self.df[self.df['prefecture'] == first_pref]
                            self.municipalities = sorted(filtered['municipality'].dropna().unique().tolist())

                # row_type件数の簡易ログ
                try:
                    rt_counts = self.df['row_type'].astype(str).str.strip().value_counts().to_dict() if 'row_type' in self.df.columns else {}
                except Exception:
                    rt_counts = {}
                # row_type件数の簡易ログ
                try:
                    rt_counts = self.df['row_type'].astype(str).str.strip().value_counts().to_dict() if 'row_type' in self.df.columns else {}
                except Exception:
                    rt_counts = {}
                print(f"[SUCCESS] CSVロード成功: {self.total_rows}行 x {len(self.df.columns)}列")
                print(f"[DEBUG] row_type counts: {rt_counts}")
                print(f"[DEBUG] row_type counts: {rt_counts}")
                print(f"[INFO] 都道府県数: {len(self.prefectures)}")
                print(f"[INFO] 初期選択: {self.selected_prefecture}")
                print(f"[INFO] 市区町村数: {len(self.municipalities)}")

                # === DB保存機能（Upsert方式） ===
                if _DB_AVAILABLE:
                    try:
                        conn = get_connection()
                        db_type = get_db_type()

                        # アップロードタイムスタンプ追加
                        df_to_save = self.df.copy()
                        df_to_save['upload_timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                        # 既存データ確認（Upsert用）
                        existing_count = 0
                        try:
                            df_existing = pd.read_sql("SELECT COUNT(*) as count FROM mapcomplete_raw", conn)
                            existing_count = int(df_existing['count'].iloc[0])
                        except:
                            pass  # テーブル未作成の場合

                        # DB保存（完全置き換え = Upsert簡易版）
                        df_to_save.to_sql(
                            'mapcomplete_raw',
                            conn,
                            if_exists='replace',
                            index=False,
                            method='multi'
                        )

                        conn.close()

                        # 統計情報表示
                        if existing_count > 0:
                            print(f"[DB] Upsert完了: {existing_count}件 → {len(df_to_save)}件 ({db_type})")
                        else:
                            print(f"[DB] 初回保存完了: {len(df_to_save)}件 ({db_type})")

                    except Exception as db_err:
                        print(f"[WARNING] DB保存失敗（CSV読み込みは成功）: {db_err}")
                # === DB保存機能終了 ===

            except Exception as e:
                print(f"[ERROR] CSVロードエラー: {e}")

    def set_prefecture(self, value: str):
        """都道府県選択（サーバーサイドフィルタリング版）

        DBから市区町村リストと最初の市区町村のフィルタ済みデータを取得。
        CSVアップロード後はDB使用しない。
        """
        self.selected_prefecture = value
        self.selected_municipality = ""

        # CSVアップロード済みの場合はCSVデータを使用（DB使用しない）
        if self.csv_uploaded and self.df_full is not None:
            # CSV全データから市区町村リストを抽出
            if 'municipality' in self.df_full.columns:
                filtered = self.df_full[self.df_full['prefecture'] == value]
                self.municipalities = sorted(filtered['municipality'].dropna().unique().tolist())

                # 最初の市区町村を自動選択してフィルタリング
                if len(self.municipalities) > 0:
                    first_muni = self.municipalities[0]
                    self.selected_municipality = first_muni

                    # CSV全体から都道府県＋市区町村でフィルタリング
                    self.df = self.df_full[
                        (self.df_full['prefecture'] == value) &
                        (self.df_full['municipality'] == first_muni)
                    ]
                    self.filtered_rows = len(self.df)
                    print(f"[CSV] 都道府県変更: {value}, 市区町村数: {len(self.municipalities)}, フィルタ済み: {self.filtered_rows}行")
                else:
                    print(f"[CSV] 都道府県変更: {value}, 市区町村数: 0")
            else:
                print(f"[CSV] 都道府県変更: {value}, municipality列が見つかりません")
        # 市区町村リスト更新（DBから取得）
        elif _DB_AVAILABLE:
            self.municipalities = get_municipalities(value)

            # 最初の市区町村を選択し、フィルタ済みデータのみ取得
            if len(self.municipalities) > 0:
                first_muni = self.municipalities[0]
                self.selected_municipality = first_muni

                # フィルタ済みデータのみ取得（数十〜数百行）
                self.df = self._normalize_df(get_filtered_data(value, first_muni))
                self.filtered_rows = len(self.df)
            else:
                # 市区町村がない場合は都道府県全体
                self.df = self._normalize_df(get_filtered_data(value))
                self.filtered_rows = len(self.df)

            print(f"[DB] 都道府県変更: {value}, フィルタ済み: {self.filtered_rows}行")
        else:
            # CSV使用時の従来ロジック（フォールバック）
            if self.df is not None and 'municipality' in self.df.columns:
                filtered = self.df[self.df['prefecture'] == value]
                self.municipalities = sorted(filtered['municipality'].dropna().unique().tolist())

        self.update_city_summary()

    def set_municipality(self, value: str):
        """市区町村選択（サーバーサイドフィルタリング版）

        DBからフィルタ済みデータのみ取得。
        CSVアップロード後はCSVデータをそのまま使用（フィルタリングは_get_filtered_dfで実施）。
        """
        self.selected_municipality = value

        # CSVアップロード済みの場合は、CSV全体から選択地域でフィルタリング
        if self.csv_uploaded and self.df_full is not None:
            # 都道府県と市区町村でフィルタリング
            filtered = self.df_full[
                (self.df_full['prefecture'] == self.selected_prefecture) &
                (self.df_full['municipality'] == value)
            ]
            self.df = filtered
            self.filtered_rows = len(self.df)
            print(f"[CSV] 市区町村変更: {value}, フィルタ済み: {self.filtered_rows}行（CSV全体からフィルタリング）")
        # フィルタ済みデータのみ取得（DBから）
        elif _DB_AVAILABLE and self.selected_prefecture:
            self.df = self._normalize_df(get_filtered_data(self.selected_prefecture, value))
            self.filtered_rows = len(self.df)
            print(f"[DB] 市区町村変更: {value}, フィルタ済み: {self.filtered_rows}行")

        self.update_city_summary()

    def update_city_summary(self):
        """選択地域サマリー更新（サーバーサイドフィルタリング版）"""
        if not self.selected_municipality:
            self.city_name = "-"
            self.city_meta = "-"
            return

        self.city_name = f"{self.selected_prefecture} {self.selected_municipality}"

        # データ件数カウント（dfは既にフィルタ済み）
        if self.df is not None:
            self.city_meta = f"{len(self.df):,}件のデータ"
        else:
            self.city_meta = "0件のデータ"

    def set_active_tab(self, tab_id: str):
        """アクティブタブ切り替え"""
        self.active_tab = tab_id

    # =====================================
    # Overview パネル用計算プロパティ
    # =====================================

    @rx.var(cache=False)
    def overview_total_applicants(self) -> str:
        """概要: 求職者総数"""
        # 依存: selected_prefecture, selected_municipality
        _ = self.selected_prefecture
        _ = self.selected_municipality

        if self.df is None or not self.is_loaded:
            return "-"

        filtered = self._get_filtered_df()
        if filtered.empty:
            return "0"

        # row_type='SUMMARY'の行からapplicant_countを取得
        summary_rows = filtered[filtered['row_type'] == 'SUMMARY']
        if not summary_rows.empty and 'applicant_count' in summary_rows.columns:
            total = summary_rows['applicant_count'].sum()
            return f"{int(total):,}"

        # SUMMARYがない場合は全行数
        return f"{len(filtered):,}"

    @rx.var(cache=False)
    def overview_avg_age(self) -> str:
        """概要: 平均年齢"""
        # 依存: selected_prefecture, selected_municipality
        _ = self.selected_prefecture
        _ = self.selected_municipality

        if self.df is None or not self.is_loaded:
            return "-"

        filtered = self._get_filtered_df()
        if filtered.empty:
            return "-"

        # row_type='SUMMARY'の行からavg_ageを取得
        summary_rows = filtered[filtered['row_type'] == 'SUMMARY']
        if not summary_rows.empty and 'avg_age' in summary_rows.columns:
            avg = summary_rows['avg_age'].mean()
            if pd.notna(avg):
                return f"{avg:.1f}"

        return "-"

    @rx.var(cache=False)
    def overview_gender_ratio(self) -> str:
        """概要: 男女比"""
        # 依存: selected_prefecture, selected_municipality
        _ = self.selected_prefecture
        _ = self.selected_municipality

        if self.df is None or not self.is_loaded:
            return "-"

        filtered = self._get_filtered_df()
        if filtered.empty:
            return "-"

        # row_type='SUMMARY'の行からmale_count, female_countを取得
        summary_rows = filtered[filtered['row_type'] == 'SUMMARY']
        if not summary_rows.empty and 'male_count' in summary_rows.columns and 'female_count' in summary_rows.columns:
            male = int(summary_rows['male_count'].sum())
            female = int(summary_rows['female_count'].sum())
            return f"{male:,} / {female:,}"

        return "-"

    @rx.var(cache=False)
    def overview_age_gender_data(self) -> List[Dict[str, Any]]:
        """概要: 年齢×性別グラフデータ（Rechartsリスト形式）"""
        # 依存: selected_prefecture, selected_municipality
        _ = self.selected_prefecture
        _ = self.selected_municipality

        if self.df is None or not self.is_loaded:
            return []

        filtered = self._get_filtered_df()
        if filtered.empty:
            return []

        # AGE_GENDERデータを使用
        age_gender_rows = filtered[filtered['row_type'] == 'AGE_GENDER']
        if not age_gender_rows.empty and 'category1' in age_gender_rows.columns and 'category2' in age_gender_rows.columns and 'count' in age_gender_rows.columns:
            try:
                # 年齢層×性別でグループ化（Recharts用リスト形式）
                age_order = ['20代', '30代', '40代', '50代', '60代', '70歳以上']
                chart_data = []

                for age in age_order:
                    age_rows = age_gender_rows[age_gender_rows['category1'] == age]
                    if not age_rows.empty:
                        male = int(age_rows[age_rows['category2'] == '男性']['count'].sum())
                        female = int(age_rows[age_rows['category2'] == '女性']['count'].sum())
                        chart_data.append({"name": age, "男性": male, "女性": female})
                    else:
                        chart_data.append({"name": age, "男性": 0, "女性": 0})

                return chart_data
            except Exception:
                pass

        # ラベルで集約（重複カテゴリ解消）
        if 'avg_qualification_count' in filtered.columns:
            try:
                def _label(r):
                    return f"{r.get('category1', '')}・{r.get('category2', '')}"
                filtered = filtered.copy()  # 明示的にコピーを作成してSettingWithCopyWarningを回避
                filtered['label'] = filtered.apply(_label, axis=1)
                grouped = filtered.groupby('label')['avg_qualification_count'].mean().reset_index()
                grouped = grouped.sort_values('avg_qualification_count', ascending=False).head(10)
                result = [
                    {"name": str(r['label']), "value": float(r['avg_qualification_count']) if pd.notna(r['avg_qualification_count']) else 0.0}
                    for _, r in grouped.iterrows()
                ]
                return result
            except Exception:
                pass

        # ラベルで集約（重複カテゴリ解消）
        if 'national_license_rate' in filtered.columns:
            try:
                def _label(r):
                    return f"{r.get('category1', '')}・{r.get('category2', '')}"
                filtered = filtered.copy()  # 明示的にコピーを作成してSettingWithCopyWarningを回避
                filtered['label'] = filtered.apply(_label, axis=1)
                grouped = filtered.groupby('label')['national_license_rate'].mean().reset_index()
                grouped['value'] = grouped['national_license_rate'] * 100.0
                grouped = grouped.sort_values('value', ascending=False).head(10)
                result = [{"name": str(r['label']), "value": float(r['value'])} for _, r in grouped.iterrows()]
                return result
            except Exception:
                pass

        # 自治体で集約して需給比率=需要/供給を計算（重複カテゴリ解消）
        if all(c in filtered.columns for c in ['municipality', 'demand_count', 'supply_count']):
            try:
                grouped = filtered.groupby('municipality').agg({'demand_count': 'sum', 'supply_count': 'sum'}).reset_index()
                def _ratio(row):
                    s = row.get('supply_count', 0)
                    d = row.get('demand_count', 0)
                    return (d / s) if pd.notna(s) and s not in [0, 0.0] and pd.notna(d) else 0.0
                grouped['ratio'] = grouped.apply(_ratio, axis=1)
                grouped = grouped.sort_values('ratio', ascending=False).head(10)
                result = [{"name": str(r['municipality']), "value": float(r['ratio'])} for _, r in grouped.iterrows()]
                return result
            except Exception:
                pass

        # 自治体で集約（重複カテゴリ解消）
        if 'municipality' in filtered.columns and 'inflow' in filtered.columns:
            try:
                grouped = (
                    filtered.groupby('municipality')['inflow']
                    .sum()
                    .reset_index()
                    .sort_values('inflow', ascending=False)
                    .head(10)
                )
                result = [
                    {"name": str(r['municipality']), "value": int(r['inflow']) if pd.notna(r['inflow']) else 0}
                    for _, r in grouped.iterrows()
                ]
                return result
            except Exception:
                pass

        # row_type='AGE_GENDER'のデータを抽出
        age_gender_rows = filtered[filtered['row_type'] == 'AGE_GENDER']
        if age_gender_rows.empty:
            return []

        # 年齢層×性別でグループ化（Recharts用リスト形式）
        age_order = ['20代', '30代', '40代', '50代', '60代', '70歳以上']

        # Recharts形式: [{"name": "20代", "男性": 100, "女性": 150}, ...]
        chart_data = []

        for age in age_order:
            age_rows = age_gender_rows[age_gender_rows['category1'] == age]
            if not age_rows.empty:
                male = int(age_rows[age_rows['category2'] == '男性']['count'].sum())
                female = int(age_rows[age_rows['category2'] == '女性']['count'].sum())
                chart_data.append({"name": age, "男性": male, "女性": female})
            else:
                chart_data.append({"name": age, "男性": 0, "女性": 0})

        return chart_data

    def _get_filtered_df(self) -> pd.DataFrame:
        """フィルタ適用後のDataFrameを取得（サーバーサイドフィルタリング版）

        サーバーサイドフィルタリングでは、self.dfは既に選択地域のデータのみを含むため、
        追加のフィルタリングは不要。そのまま返す。
        """
        if self.df is None:
            return pd.DataFrame()

        # サーバーサイドフィルタリング: dfは既にフィルタ済み
        return self.df

    # =====================================
    # 頻出フィルタのキャッシュ化ヘルパー（サーバーサイドフィルタリング版）
    # dfは既にフィルタ済みなので、row_typeフィルタのみ実行
    # =====================================

    @rx.var(cache=False)
    def _cached_persona_muni_filtered(self) -> pd.DataFrame:
        """PERSONA_MUNIフィルタ結果（キャッシュ無効化で常に最新データ）"""
        if self.df is None:
            return pd.DataFrame()

        # サーバーサイドフィルタリング: dfは既に地域でフィルタ済み、row_typeのみフィルタ
        return self.df[self.df['row_type'] == 'PERSONA_MUNI']

    @rx.var(cache=False)
    def _cached_employment_age_filtered(self) -> pd.DataFrame:
        """EMPLOYMENT_AGE_CROSSフィルタ結果（キャッシュ無効化で常に最新データ）"""
        if self.df is None:
            return pd.DataFrame()

        # サーバーサイドフィルタリング: dfは既に地域でフィルタ済み、row_typeのみフィルタ
        return self.df[self.df['row_type'] == 'EMPLOYMENT_AGE_CROSS']

    @rx.var(cache=False)
    def _cached_urgency_age_filtered(self) -> pd.DataFrame:
        """URGENCY_AGEフィルタ結果（キャッシュ無効化で常に最新データ）"""
        if self.df is None:
            return pd.DataFrame()

        # サーバーサイドフィルタリング: dfは既に地域でフィルタ済み、row_typeのみフィルタ
        return self.df[self.df['row_type'] == 'URGENCY_AGE']

    # =====================================
    # Supply パネル用計算プロパティ
    # GAS createSupplyData() (map_complete_integrated.html Line 2601-2652)
    # 就業状態・資格分布は推定値を使用（GAS実装に準拠）
    # =====================================

    @rx.var(cache=False)
    def supply_employed(self) -> str:
        """供給: 就業中（推定60%）"""
        if not self.is_loaded:
            return "0"

        _ = self.selected_prefecture
        _ = self.selected_municipality

        total = self._get_total_applicants_int()
        if total == 0:
            return "0"

        # GAS Line 2627: 就業中 = 全体の60%
        employed = round(total * 0.6)
        return f"{employed:,}"

    @rx.var(cache=False)
    def supply_unemployed(self) -> str:
        """供給: 離職中（推定30%）"""
        if not self.is_loaded:
            return "0"

        _ = self.selected_prefecture
        _ = self.selected_municipality

        total = self._get_total_applicants_int()
        if total == 0:
            return "0"

        # GAS Line 2628: 離職中 = 全体の30%
        unemployed = round(total * 0.3)
        return f"{unemployed:,}"

    @rx.var(cache=False)
    def supply_student(self) -> str:
        """供給: 在学中（推定10%）"""
        if not self.is_loaded:
            return "0"

        _ = self.selected_prefecture
        _ = self.selected_municipality

        total = self._get_total_applicants_int()
        if total == 0:
            return "0"

        # GAS Line 2629: 在学中 = 全体の10%
        student = round(total * 0.1)
        return f"{student:,}"

    @rx.var(cache=False)
    def supply_national_license(self) -> str:
        """供給: 国家資格保有者（推定3%）"""
        if not self.is_loaded:
            return "0"

        _ = self.selected_prefecture
        _ = self.selected_municipality

        total = self._get_total_applicants_int()
        if total == 0:
            return "0"

        # GAS Line 2633: 国家資格保有者 = 全体の3%
        national_license = round(total * 0.03)
        return f"{national_license:,}"

    @rx.var(cache=False)
    def supply_avg_qualifications(self) -> str:
        """供給: 平均資格保有数"""
        _ = self.selected_prefecture
        _ = self.selected_municipality

        if self.df is None or not self.is_loaded:
            return "-"

        filtered = self._get_filtered_df()
        if filtered.empty:
            return "-"

        # SUMMARYデータからavg_qualificationsを取得
        summary_rows = filtered[filtered['row_type'] == 'SUMMARY']
        if not summary_rows.empty and 'avg_qualifications' in summary_rows.columns:
            avg_qual = summary_rows['avg_qualifications'].mean()
            if pd.notna(avg_qual):
                return f"{avg_qual:.2f}"

        return "-"

    @rx.var(cache=False)
    def supply_qualification_buckets_data(self) -> List[Dict[str, Any]]:
        """供給: 資格バケット分布データ（Rechartsリスト形式）

        GAS Line 2613-2623の推定ロジックに準拠:
        - 資格なし: 20%
        - 1資格: 30%
        - 2資格: 25%
        - 3資格以上: 25%
        """
        if not self.is_loaded:
            return []

        _ = self.selected_prefecture
        _ = self.selected_municipality

        total = self._get_total_applicants_int()
        if total == 0:
            return []

        # GAS Line 2613-2623: 資格分布を推定（Recharts形式）
        no_qual = round(total * 0.2)
        one_qual = round(total * 0.3)
        two_qual = round(total * 0.25)
        three_plus = total - no_qual - one_qual - two_qual

        # GAS Line 2553-2556: colors = buckets.map((_,idx)=>COLOR[idx % COLOR.length]) に準拠
        chart_data = [
            {"name": "資格なし", "count": no_qual, "fill": COLOR_PALETTE[0]},
            {"name": "1資格", "count": one_qual, "fill": COLOR_PALETTE[1]},
            {"name": "2資格", "count": two_qual, "fill": COLOR_PALETTE[2]},
            {"name": "3資格以上", "count": three_plus, "fill": COLOR_PALETTE[3]},
        ]

        return chart_data

    def _get_total_applicants_int(self) -> int:
        """申請者総数を整数で取得（内部ヘルパー関数）"""
        if self.df is None or not self.is_loaded:
            return 0

        filtered = self._get_filtered_df()
        if filtered.empty:
            return 0

        summary_rows = filtered[filtered['row_type'] == 'SUMMARY']
        if not summary_rows.empty and 'applicant_count' in summary_rows.columns:
            total = summary_rows['applicant_count'].sum()
            return int(total) if pd.notna(total) else 0

        return len(filtered)

    # =====================================
    # 追加のOverview用計算プロパティ
    # =====================================

    @rx.var(cache=False)
    def overview_gender_data(self) -> List[Dict[str, Any]]:
        """概要: 性別構成データ（ドーナツチャート用）

        GAS参照: map_complete_integrated.html Line 2497-2501
        形式: [{"name": "男性", "value": 1500, "fill": "#648FFF"}, {"name": "女性", "value": 2000, "fill": "#FE6100"}]
        データソース: row_type='SUMMARY', male_count, female_count
        """
        _ = self.selected_prefecture
        _ = self.selected_municipality

        if self.df is None or not self.is_loaded:
            return []

        filtered = self._get_filtered_df()
        if filtered.empty:
            return []

        # SUMMARYからmale_count, female_countを集計
        summary_rows = filtered[filtered['row_type'] == 'SUMMARY']
        if not summary_rows.empty and 'male_count' in summary_rows.columns and 'female_count' in summary_rows.columns:
            male = int(summary_rows['male_count'].sum())
            female = int(summary_rows['female_count'].sum())

            # 色盲対応パレット使用
            return [
                {"name": "男性", "value": male, "fill": COLOR_PALETTE[0]},  # 青
                {"name": "女性", "value": female, "fill": COLOR_PALETTE[1]}  # オレンジ
            ]

        return []

    @rx.var(cache=False)
    def overview_age_data(self) -> List[Dict[str, Any]]:
        """概要: 年齢帯別データ（棒グラフ用）

        GAS参照: Line 2505-2509
        形式: [{"name": "20代", "count": 500}, ...]
        """
        _ = self.selected_prefecture
        _ = self.selected_municipality

        if self.df is None or not self.is_loaded:
            return []

        filtered = self._get_filtered_df()
        if filtered.empty:
            return []

        # 自治体で集約（重複カテゴリ解消）
        if 'municipality' in filtered.columns and 'net_flow' in filtered.columns:
            try:
                grouped = (
                    filtered.groupby('municipality')['net_flow']
                    .sum()
                    .reset_index()
                    .sort_values('net_flow', ascending=False)
                    .head(10)
                )
                result = [
                    {"name": str(r['municipality']), "value": int(r['net_flow']) if pd.notna(r['net_flow']) else 0}
                    for _, r in grouped.iterrows()
                ]
                return result
            except Exception:
                pass

        # AGE_GENDERから年齢層ごとに男女合計
        age_gender_rows = filtered[filtered['row_type'] == 'AGE_GENDER']
        if age_gender_rows.empty:
            return []

        age_order = ['20代', '30代', '40代', '50代', '60代', '70歳以上']
        chart_data = []

        for age in age_order:
            age_rows = age_gender_rows[age_gender_rows['category1'] == age]
            if not age_rows.empty:
                count = int(age_rows['count'].sum())
                chart_data.append({"name": age, "count": count})
            else:
                chart_data.append({"name": age, "count": 0})

        return chart_data

    # =====================================
    # Supply パネル用追加計算プロパティ
    # =====================================

    @rx.var(cache=False)
    def supply_status_data(self) -> List[Dict[str, Any]]:
        """供給: 就業ステータスデータ（棒グラフ用）

        GAS参照: Line 2546-2550、Line 2627-2629の60%/30%/10%に準拠
        形式: [{"name": "就業中", "count": 3000}, ...]
        """
        if not self.is_loaded:
            return []

        _ = self.selected_prefecture
        _ = self.selected_municipality

        total = self._get_total_applicants_int()
        if total == 0:
            return []

        employed = round(total * 0.6)
        unemployed = round(total * 0.3)
        student = round(total * 0.1)

        return [
            {"name": "就業中", "count": employed},
            {"name": "離職中", "count": unemployed},
            {"name": "在学中", "count": student}
        ]

    @rx.var(cache=False)
    def supply_persona_qual_data(self) -> List[Dict[str, Any]]:
        """供給: ペルソナ別平均資格数（横棒グラフ用）

        GAS参照: Line 2563-2567
        形式: [{"name": "ペルソナA", "avg_qual": 2.5}, ...]
        データソース: row_type='PERSONA_MUNI', category1=persona_name, avg_qualifications
        """
        if not self.is_loaded or self.df is None:
            return []

        df = self.df

        # サーバーサイドフィルタリング: dfは既に地域でフィルタ済み、row_typeのみフィルタ
        filtered = df[df['row_type'] == 'PERSONA_MUNI'].copy()

        if filtered.empty:
            return []

        # 自治体で集約（不足=gap>0の合計）
        if 'municipality' in filtered.columns and 'gap' in filtered.columns:
            try:
                grouped = (
                    filtered.groupby('municipality')['gap']
                    .sum()
                    .reset_index()
                    .sort_values('gap', ascending=False)
                    .head(10)
                )
                result = [
                    {"name": str(r['municipality']), "value": int(r['gap']) if pd.notna(r['gap']) else 0}
                    for _, r in grouped.iterrows()
                ]
                return result
            except Exception:
                pass

        # ペルソナ名でグループ化して加重平均を計算（ベクトル化で5-20倍高速化）
        filtered = filtered.copy()  # 一時的にコピー（weighted列追加のため）
        filtered['weighted'] = filtered['avg_qualifications'] * filtered['count']
        grouped = filtered.groupby('category1').agg({
            'weighted': 'sum',
            'count': 'sum'
        })
        # ゼロ除算を明示的に処理（count=0の場合は0を返す）
        import numpy as np
        grouped['avg_qual'] = np.where(
            grouped['count'] > 0,
            grouped['weighted'] / grouped['count'],
            0
        )
        grouped = grouped.reset_index()[['category1', 'avg_qual']]
        grouped.columns = ['name', 'avg_qual']

        # 降順ソート（資格数が多い順）
        grouped = grouped.sort_values('avg_qual', ascending=False)

        # 辞書リストに変換
        result = []
        for _, row in grouped.iterrows():
            result.append({
                "name": str(row['name']),
                "avg_qual": float(row['avg_qual'])
            })

        return result

    # =====================================
    # Career パネル用追加計算プロパティ
    # =====================================

    @rx.var(cache=False)
    def career_employment_age_data(self) -> List[Dict[str, Any]]:
        """キャリア: 就業ステータス×年齢帯（積み上げ棒グラフ用）

        GAS参照: Line 2587-2588
        形式: [{"age": "20代", "就業中": 100, "離職中": 50, "在学中": 20}, ...]
        データソース: row_type='EMPLOYMENT_AGE_CROSS', category1=就業状態, category2=年齢
        注意: EMPLOYMENT_AGE_CROSSは市町村別データ（prefecture/municipalityでフィルタ）
        """
        if not self.is_loaded or self.df is None:
            return []

        df = self.df

        # サーバーサイドフィルタリング: dfは既に地域でフィルタ済み、row_typeのみフィルタ
        filtered = df[df['row_type'] == 'EMPLOYMENT_AGE_CROSS'].copy()

        if filtered.empty:
            return []

        # 自治体で集約（余剰=|sum(gap<0)|）
        if 'municipality' in filtered.columns and 'gap' in filtered.columns:
            try:
                grouped = (
                    filtered.groupby('municipality')['gap']
                    .sum()
                    .reset_index()
                )
                grouped['abs_surplus'] = grouped['gap'].abs()
                grouped = grouped.sort_values('abs_surplus', ascending=False).head(10)
                result = [
                    {"name": str(r['municipality']), "value": int(r['abs_surplus']) if pd.notna(r['abs_surplus']) else 0}
                    for _, r in grouped.iterrows()
                ]
                return result
            except Exception:
                pass

        # ピボットテーブル形式に変換: 年齢層 × 就業ステータス
        pivot_data = {}
        for _, row in filtered.iterrows():
            employment_status = str(row.get('category1', '')).strip()  # 就業中、離職中、在学中
            age_group = str(row.get('category2', '')).strip()          # 20代、30代、等
            count = row.get('count', 0)

            if age_group and employment_status and pd.notna(count):
                if age_group not in pivot_data:
                    pivot_data[age_group] = {"age": age_group}
                pivot_data[age_group][employment_status] = int(count)

        # リスト形式に変換し、年齢層順にソート
        result = list(pivot_data.values())
        age_order = {"20代": 1, "30代": 2, "40代": 3, "50代": 4, "60代": 5, "70歳以上": 6}
        result.sort(key=lambda x: age_order.get(x["age"], 99))

        return result

    @rx.var(cache=False)
    def career_avg_qualifications(self) -> str:
        """キャリア: 平均保有資格数（EMPLOYMENT_AGE_CROSSデータから計算・市町村別）"""
        if not self.is_loaded or self.df is None:
            return "0.00"

        df = self.df

        # サーバーサイドフィルタリング: dfは既に地域でフィルタ済み、row_typeのみフィルタ
        filtered = df[df['row_type'] == 'EMPLOYMENT_AGE_CROSS'].copy()

        if filtered.empty:
            return "0.00"

        # 加重平均を計算: Σ(avg_qualifications * count) / Σ(count)
        filtered['weighted'] = filtered['avg_qualifications'] * filtered['count']
        total_weighted = filtered['weighted'].sum()
        total_count = filtered['count'].sum()

        if total_count > 0:
            avg_qual = total_weighted / total_count
            return f"{avg_qual:.2f}"
        else:
            return "0.00"

    @rx.var(cache=False)
    def career_national_license_rate(self) -> str:
        """キャリア: 国家資格保有率（EMPLOYMENT_AGE_CROSSデータから計算・市町村別）"""
        if not self.is_loaded or self.df is None:
            return "0.00"

        df = self.df

        # サーバーサイドフィルタリング: dfは既に地域でフィルタ済み、row_typeのみフィルタ
        filtered = df[df['row_type'] == 'EMPLOYMENT_AGE_CROSS'].copy()

        if filtered.empty:
            return "0.00"

        # 加重平均を計算: Σ(national_license_rate * count) / Σ(count)
        filtered['weighted'] = filtered['national_license_rate'] * filtered['count']
        total_weighted = filtered['weighted'].sum()
        total_count = filtered['count'].sum()

        if total_count > 0:
            avg_rate = (total_weighted / total_count) * 100  # パーセント表示
            return f"{avg_rate:.2f}"
        else:
            return "0.00"

    # =====================================
    # Urgency パネル用追加計算プロパティ
    # =====================================

    @rx.var(cache=False)
    def urgency_age_data(self) -> List[Dict[str, Any]]:
        """緊急度: 年齢帯別データ（複合グラフ: 棒+折れ線、2軸用）

        GAS参照: Line 2608-2618
        形式: [{"age": "20代", "count": 500, "avg_score": 7.5}, ...]
        データソース: row_type='URGENCY_AGE', category2=年齢帯
        """
        if not self.is_loaded or self.df is None:
            return []

        df = self.df

        # サーバーサイドフィルタリング: dfは既に地域でフィルタ済み、row_typeのみフィルタ
        filtered = df[df['row_type'] == 'URGENCY_AGE'].copy()

        if filtered.empty:
            return []

        # category2が年齢帯、countが人数、avg_urgency_scoreが平均スコア
        result = []
        for _, row in filtered.iterrows():
            age_group = str(row.get('category2', '')).strip()
            count = row.get('count', 0)
            avg_score = row.get('avg_urgency_score', 0)

            if age_group and pd.notna(count):
                result.append({
                    "age": age_group,
                    "count": int(count) if pd.notna(count) else 0,
                    "avg_score": round(float(avg_score), 2) if pd.notna(avg_score) else 0
                })

        # 年齢層順にソート（20代、30代、40代、50代、60代、70歳以上）
        age_order = {"20代": 1, "30代": 2, "40代": 3, "50代": 4, "60代": 5, "70歳以上": 6}
        result.sort(key=lambda x: age_order.get(x["age"], 99))

        return result

    @rx.var(cache=False)
    def urgency_employment_data(self) -> List[Dict[str, Any]]:
        """緊急度: 就業ステータス別データ（複合グラフ: 棒+折れ線、2軸用）

        GAS参照: Line 2621-2630
        形式: [{"status": "就業中", "count": 3000, "avg_score": 6.5}, ...]
        データソース: row_type='URGENCY_EMPLOYMENT', category2=就業ステータス
        """
        if not self.is_loaded or self.df is None:
            return []

        df = self.df

        # サーバーサイドフィルタリング: dfは既に地域でフィルタ済み、row_typeのみフィルタ
        filtered = df[df['row_type'] == 'URGENCY_EMPLOYMENT'].copy()

        if filtered.empty:
            return []

        # category2が就業ステータス、countが人数、avg_urgency_scoreが平均スコア
        result = []
        for _, row in filtered.iterrows():
            employment_status = str(row.get('category2', '')).strip()
            count = row.get('count', 0)
            avg_score = row.get('avg_urgency_score', 0)

            if employment_status and pd.notna(count):
                result.append({
                    "status": employment_status,
                    "count": int(count) if pd.notna(count) else 0,
                    "avg_score": round(float(avg_score), 2) if pd.notna(avg_score) else 0
                })

        # 就業ステータス順にソート（就業中、離職中、在学中）
        status_order = {"就業中": 1, "離職中": 2, "在学中": 3}
        result.sort(key=lambda x: status_order.get(x["status"], 99))

        return result

    @rx.var(cache=False)
    def urgency_total_count(self) -> str:
        """緊急度: 対象人数合計"""
        if not self.is_loaded or self.df is None:
            return "0"

        df = self.df

        # サーバーサイドフィルタリング: dfは既に地域でフィルタ済み、row_typeのみフィルタ
        filtered = df[df['row_type'] == 'URGENCY_AGE']

        total = filtered['count'].sum() if not filtered.empty else 0
        return f"{int(total):,}"

    @rx.var(cache=False)
    def urgency_avg_score(self) -> str:
        """緊急度: 平均スコア（加重平均）"""
        if not self.is_loaded or self.df is None:
            return "0.0"

        df = self.df

        # サーバーサイドフィルタリング: dfは既に地域でフィルタ済み、row_typeのみフィルタ
        filtered = df[df['row_type'] == 'URGENCY_AGE'].copy()

        if filtered.empty:
            return "0.0"

        # 加重平均 = Σ(avg_urgency_score * count) / Σ(count)
        filtered['weighted'] = filtered['avg_urgency_score'] * filtered['count']
        total_weighted = filtered['weighted'].sum()
        total_count = filtered['count'].sum()

        if total_count > 0:
            avg_score = total_weighted / total_count
            return f"{avg_score:.1f}"
        else:
            return "0.0"

    # =====================================
    # Flow パネル用追加計算プロパティ
    # =====================================

    @rx.var(cache=False)
    def flow_inflow(self) -> str:
        """フロー: 流入人数"""
        if not self.is_loaded or self.df is None:
            return "0"

        df = self.df

        # サーバーサイドフィルタリング: dfは既に地域でフィルタ済み、row_typeのみフィルタ
        filtered = df[df['row_type'] == 'FLOW']

        if filtered.empty:
            return "0"

        inflow = filtered['inflow'].iloc[0] if 'inflow' in filtered.columns else 0
        return f"{int(inflow):,}" if pd.notna(inflow) else "0"

    @rx.var(cache=False)
    def flow_outflow(self) -> str:
        """フロー: 流出人数"""
        if not self.is_loaded or self.df is None:
            return "0"

        df = self.df

        # サーバーサイドフィルタリング: dfは既に地域でフィルタ済み、row_typeのみフィルタ
        filtered = df[df['row_type'] == 'FLOW']

        if filtered.empty:
            return "0"

        outflow = filtered['outflow'].iloc[0] if 'outflow' in filtered.columns else 0
        return f"{int(outflow):,}" if pd.notna(outflow) else "0"

    @rx.var(cache=False)
    def flow_net_flow(self) -> str:
        """フロー: 純流出入（正:流入超過、負:流出超過）"""
        if not self.is_loaded or self.df is None:
            return "0"

        df = self.df

        # サーバーサイドフィルタリング: dfは既に地域でフィルタ済み、row_typeのみフィルタ
        filtered = df[df['row_type'] == 'FLOW']

        if filtered.empty:
            return "0"

        net_flow = filtered['net_flow'].iloc[0] if 'net_flow' in filtered.columns else 0
        if pd.notna(net_flow):
            sign = "+" if net_flow >= 0 else ""
            return f"{sign}{int(net_flow):,}"
        else:
            return "0"

    # =====================================
    # Persona パネル用追加計算プロパティ
    # =====================================

    @rx.var(cache=False)
    def persona_top_list(self) -> List[Dict[str, Any]]:
        """ペルソナ: トップペルソナリスト（上位5件）

        GAS参照: Line 2636-2637
        形式: [{"label": "50代・女性・就業中", "count": 256, "share": 0.1465}, ...]
        データソース: row_type='PERSONA_MUNI', category1=persona_name, count
        """
        if not self.is_loaded or self.df is None:
            return []

        df = self.df

        # サーバーサイドフィルタリング: dfは既に地域でフィルタ済み、row_typeのみフィルタ
        filtered = df[df['row_type'] == 'PERSONA_MUNI'].copy()

        if filtered.empty:
            return []

        # ペルソナ名でグループ化してcountを合計
        persona_counts = filtered.groupby('category1')['count'].sum().reset_index()
        persona_counts.columns = ['label', 'count']

        # 全体の人数を計算（割合算出用）
        total_count = persona_counts['count'].sum()

        if total_count == 0:
            return []

        # 割合を計算
        persona_counts['share'] = persona_counts['count'] / total_count

        # countの降順でソート、上位5件を取得
        top_personas = persona_counts.sort_values('count', ascending=False).head(5)

        # 辞書リストに変換（表示用文字列を事前生成）
        result = []
        for _, row in top_personas.iterrows():
            count = int(row['count'])
            share = float(row['share'])
            result.append({
                "label": str(row['label']),
                "count_display": f"{count:,}人 ({share * 100:.2f}%)"
            })

        return result

    @rx.var(cache=False)
    def persona_full_list(self) -> List[Dict[str, Any]]:
        """ペルソナ: 全ペルソナリスト（100%内訳）

        形式: [{"label": "50代・女性・就業中", "count_display": "256人 (14.65%)", "count": 256, "share": 0.1465}, ...]
        データソース: row_type='PERSONA_MUNI', category1=persona_name, count
        注意: 全ペルソナを表示（head制限なし）
        """
        if not self.is_loaded or self.df is None:
            return []

        df = self.df

        # サーバーサイドフィルタリング: dfは既に地域でフィルタ済み、row_typeのみフィルタ
        filtered = df[df['row_type'] == 'PERSONA_MUNI'].copy()

        if filtered.empty:
            return []

        # ペルソナ名でグループ化してcountを合計
        persona_counts = filtered.groupby('category1')['count'].sum().reset_index()
        persona_counts.columns = ['label', 'count']

        # 全体の人数を計算（割合算出用）
        total_count = persona_counts['count'].sum()

        if total_count == 0:
            return []

        # 割合を計算
        persona_counts['share'] = persona_counts['count'] / total_count

        # countの降順でソート（全件表示）
        all_personas = persona_counts.sort_values('count', ascending=False)

        # 辞書リストに変換（表示用文字列を事前生成）
        result = []
        for _, row in all_personas.iterrows():
            count = int(row['count'])
            share = float(row['share'])
            result.append({
                "label": str(row['label']),
                "count_display": f"{count:,}人 ({share * 100:.2f}%)",
                "count": count,
                "share": share
            })

        return result

    @rx.var(cache=False)
    def persona_bar_data(self) -> List[Dict[str, Any]]:
        """ペルソナ: 横棒グラフ用データ

        形式: [{"name": "50代・女性・就業中", "count": 256}, ...]
        データソース: row_type='PERSONA_MUNI', category1=persona_name, count
        """
        if not self.is_loaded or self.df is None:
            return []

        df = self.df

        # サーバーサイドフィルタリング: dfは既に地域でフィルタ済み、row_typeのみフィルタ
        filtered = df[df['row_type'] == 'PERSONA_MUNI'].copy()

        if filtered.empty:
            return []

        # ペルソナ名でグループ化してcountを合計
        persona_counts = filtered.groupby('category1')['count'].sum().reset_index()
        persona_counts.columns = ['name', 'count']

        # countの降順でソート（上位15件）
        top_personas = persona_counts.sort_values('count', ascending=False).head(15)

        # 辞書リストに変換
        result = []
        for _, row in top_personas.iterrows():
            result.append({
                "name": str(row['name']),
                "count": int(row['count'])
            })

        return result

    @rx.var(cache=False)
    def persona_employment_breakdown_data(self) -> List[Dict[str, Any]]:
        """ペルソナ: 就業状態別積み上げ棒グラフ用データ

        形式: [{"age_gender": "50代・女性", "就業中": 256, "離職中": 80, "在学中": 10}, ...]
        データソース: row_type='PERSONA_MUNI', category1=persona_name（年齢・性別・就業状態を分解）, count
        """
        if not self.is_loaded or self.df is None:
            return []

        df = self.df

        # サーバーサイドフィルタリング: dfは既に地域でフィルタ済み、row_typeのみフィルタ
        filtered = df[df['row_type'] == 'PERSONA_MUNI'].copy()

        if filtered.empty:
            return []

        # ペルソナ名を分解（例: "50代・女性・就業中" → age_gender="50代・女性", employment="就業中"）
        breakdown_data = {}
        for _, row in filtered.iterrows():
            persona_name = str(row.get('category1', ''))
            count = int(row.get('count', 0))

            # ペルソナ名を「・」で分割
            parts = persona_name.split('・')
            if len(parts) >= 3:
                age_gender = f"{parts[0]}・{parts[1]}"  # "50代・女性"
                employment = parts[2]  # "就業中"

                if age_gender not in breakdown_data:
                    breakdown_data[age_gender] = {"age_gender": age_gender, "就業中": 0, "離職中": 0, "在学中": 0}

                if employment in ["就業中", "離職中", "在学中"]:
                    breakdown_data[age_gender][employment] += count

        # 辞書をリストに変換
        result = list(breakdown_data.values())

        # 合計人数でソート（降順）
        result.sort(key=lambda x: x["就業中"] + x["離職中"] + x["在学中"], reverse=True)

        # 上位10件のみ返す
        return result[:10]

    @rx.var(cache=False)
    def persona_share_data(self) -> List[Dict[str, Any]]:
        """ペルソナ: 構成比データ（ドーナツチャート用）

        GAS参照: Line 2721-2725
        形式: [{"name": "ペルソナA", "value": 500, "fill": "#38bdf8"}, ...]
        データソース: row_type='PERSONA_MUNI', category1=persona_name, count
        """
        if not self.is_loaded or self.df is None:
            return []

        df = self.df

        # サーバーサイドフィルタリング: dfは既に地域でフィルタ済み、row_typeのみフィルタ
        filtered = df[df['row_type'] == 'PERSONA_MUNI'].copy()

        if filtered.empty:
            return []

        # ペルソナ名でグループ化してcountを合計
        persona_counts = filtered.groupby('category1')['count'].sum().reset_index()
        persona_counts.columns = ['name', 'value']

        # countの降順でソート
        persona_counts = persona_counts.sort_values('value', ascending=False)

        # 辞書リストに変換（COLOR_PALETTEを順番に割り当て）
        result = []
        for idx, row in persona_counts.iterrows():
            result.append({
                "name": str(row['name']),
                "value": int(row['value']),
                "fill": COLOR_PALETTE[len(result) % len(COLOR_PALETTE)]
            })

        return result

    # =====================================
    # Cross パネル用追加計算プロパティ（多重クロス集計）
    # =====================================

    @rx.var(cache=False)
    def cross_age_employment_data(self) -> List[Dict[str, Any]]:
        """クロス: 年齢×就業状態クロス集計（ヒートマップ用）

        形式: [{"age": "20代", "就業中": 100, "離職中": 50, "在学中": 20}, ...]
        データソース: row_type='EMPLOYMENT_AGE_CROSS', category1=employment_status, category2=age_group, count
        """
        if not self.is_loaded or self.df is None:
            return []

        df = self.df

        # サーバーサイドフィルタリング: dfは既に地域でフィルタ済み、row_typeのみフィルタ
        filtered = df[df['row_type'] == 'EMPLOYMENT_AGE_CROSS'].copy()

        if filtered.empty:
            return []

        # ピボットテーブル形式に変換: 年齢層 × 就業ステータス
        pivot_data = {}
        for _, row in filtered.iterrows():
            employment_status = str(row.get('category1', '')).strip()  # 就業中、離職中、在学中
            age_group = str(row.get('category2', '')).strip()          # 20代、30代、等
            count = row.get('count', 0)

            if age_group and employment_status and pd.notna(count):
                if age_group not in pivot_data:
                    pivot_data[age_group] = {"age": age_group}
                pivot_data[age_group][employment_status] = int(count)

        # リスト形式に変換し、年齢層順にソート
        result = list(pivot_data.values())
        age_order = {"20代": 1, "30代": 2, "40代": 3, "50代": 4, "60代": 5, "70歳以上": 6}
        result.sort(key=lambda x: age_order.get(x["age"], 99))

        return result

    @rx.var(cache=False)
    def cross_gender_employment_data(self) -> List[Dict[str, Any]]:
        """クロス: 性別×就業状態クロス集計（積み上げ棒グラフ用）

        形式: [{"gender": "女性", "就業中": 500, "離職中": 200, "在学中": 50}, ...]
        データソース: PERSONA_MUNIから性別・就業状態を抽出して集計
        """
        if not self.is_loaded or self.df is None:
            return []

        df = self.df
        prefecture = self.selected_prefecture
        municipality = self.selected_municipality

        # PERSONA_MUNIデータをフィルタ（ペルソナ名から性別・就業状態を抽出）
        filtered = df[
            (df['row_type'] == 'PERSONA_MUNI') &
            (df['prefecture'] == prefecture) &
            (df['municipality'] == municipality)
        ].copy()

        if filtered.empty:
            return []

        # ペルソナ名を分解: "50代・女性・就業中" → gender="女性", employment="就業中"
        pivot_data = {}
        for _, row in filtered.iterrows():
            persona_name = str(row.get('category1', ''))
            count = int(row.get('count', 0))

            # ペルソナ名を分解
            parts = persona_name.split('・')
            if len(parts) >= 3:
                gender = parts[1]  # 女性/男性
                employment = parts[2]  # 就業中/離職中/在学中

                # 性別別に集計
                if gender not in pivot_data:
                    pivot_data[gender] = {"gender": gender, "就業中": 0, "離職中": 0, "在学中": 0}

                if employment in ["就業中", "離職中", "在学中"]:
                    pivot_data[gender][employment] += count

        # リスト形式に変換（女性、男性の順）
        result = []
        if "女性" in pivot_data:
            result.append(pivot_data["女性"])
        if "男性" in pivot_data:
            result.append(pivot_data["男性"])

        return result

    @rx.var(cache=False)
    def cross_age_qualification_data(self) -> List[Dict[str, Any]]:
        """クロス: 年齢×資格保有クロス集計（折れ線グラフ用）

        形式: [{"age": "20代", "avg_qual": 1.5, "national_rate": 0.05}, ...]
        データソース: row_type='EMPLOYMENT_AGE_CROSS', category2=age_group, avg_qualifications, national_license_rate
        """
        if not self.is_loaded or self.df is None:
            return []

        df = self.df

        # サーバーサイドフィルタリング: dfは既に地域でフィルタ済み、row_typeのみフィルタ
        filtered = df[df['row_type'] == 'EMPLOYMENT_AGE_CROSS'].copy()

        if filtered.empty:
            return []

        # 年齢層でグループ化して加重平均を計算（ベクトル化で5-20倍高速化）
        filtered = filtered.copy()
        filtered['weighted_qual'] = filtered['avg_qualifications'] * filtered['count']
        filtered['weighted_rate'] = filtered['national_license_rate'] * filtered['count']
        grouped = filtered.groupby('category2').agg({
            'weighted_qual': 'sum',
            'weighted_rate': 'sum',
            'count': 'sum'
        })
        # ゼロ除算を明示的に処理（count=0の場合は0を返す）
        import numpy as np
        grouped['avg_qual'] = np.where(
            grouped['count'] > 0,
            grouped['weighted_qual'] / grouped['count'],
            0
        )
        grouped['national_rate'] = np.where(
            grouped['count'] > 0,
            grouped['weighted_rate'] / grouped['count'],
            0
        )
        grouped = grouped.reset_index()[['category2', 'avg_qual', 'national_rate']]
        grouped.columns = ['age', 'avg_qual', 'national_rate']

        # 年齢層順にソート
        age_order = {"20代": 1, "30代": 2, "40代": 3, "50代": 4, "60代": 5, "70歳以上": 6}
        grouped['sort_order'] = grouped['age'].map(age_order)
        grouped = grouped.sort_values('sort_order').drop('sort_order', axis=1)

        # 辞書リストに変換
        result = []
        for _, row in grouped.iterrows():
            result.append({
                "age": str(row['age']),
                "avg_qual": round(float(row['avg_qual']), 2),
                "national_rate": round(float(row['national_rate']) * 100, 2)  # パーセント変換
            })

        return result

    @rx.var(cache=False)
    def cross_employment_qualification_data(self) -> List[Dict[str, Any]]:
        """クロス: 就業状態×資格保有クロス集計（レーダーチャート用）

        形式: [{"employment": "就業中", "avg_qual": 2.1, "national_rate": 8.5}, ...]
        データソース: row_type='EMPLOYMENT_AGE_CROSS', category1=employment_status, avg_qualifications, national_license_rate
        """
        if not self.is_loaded or self.df is None:
            return []

        df = self.df

        # サーバーサイドフィルタリング: dfは既に地域でフィルタ済み、row_typeのみフィルタ
        filtered = df[df['row_type'] == 'EMPLOYMENT_AGE_CROSS'].copy()

        if filtered.empty:
            return []

        # 就業状態でグループ化して加重平均を計算（ベクトル化で5-20倍高速化）
        filtered = filtered.copy()
        filtered['weighted_qual'] = filtered['avg_qualifications'] * filtered['count']
        filtered['weighted_rate'] = filtered['national_license_rate'] * filtered['count']
        grouped = filtered.groupby('category1').agg({
            'weighted_qual': 'sum',
            'weighted_rate': 'sum',
            'count': 'sum'
        })
        # ゼロ除算を明示的に処理（count=0の場合は0を返す）
        import numpy as np
        grouped['avg_qual'] = np.where(
            grouped['count'] > 0,
            grouped['weighted_qual'] / grouped['count'],
            0
        )
        grouped['national_rate'] = np.where(
            grouped['count'] > 0,
            grouped['weighted_rate'] / grouped['count'],
            0
        )
        grouped = grouped.reset_index()[['category1', 'avg_qual', 'national_rate']]
        grouped.columns = ['employment', 'avg_qual', 'national_rate']

        # 辞書リストに変換
        result = []
        for _, row in grouped.iterrows():
            result.append({
                "employment": str(row['employment']),
                "avg_qual": round(float(row['avg_qual']), 2),
                "national_rate": round(float(row['national_rate']) * 100, 2)  # パーセント変換
            })

        return result

    @rx.var(cache=False)
    def cross_persona_qualification_age_data(self) -> List[Dict[str, Any]]:
        """クロス6: ペルソナ×資格×年齢 - 希少人材の特定（バブルチャート用）

        形式: [{"persona": "50代・女性・就業中", "age": "50代", "avg_qual": 3.2, "count": 120, "rarity_score": 85}, ...]
        データソース: PERSONA_MUNI + EMPLOYMENT_AGE_CROSS結合
        """
        if not self.is_loaded or self.df is None:
            return []

        df = self.df
        prefecture = self.selected_prefecture
        municipality = self.selected_municipality

        # PERSONA_MUNIとEMPLOYMENT_AGE_CROSSを結合して分析
        persona_df = df[
            (df['row_type'] == 'PERSONA_MUNI') &
            (df['prefecture'] == prefecture) &
            (df['municipality'] == municipality)
        ].copy()

        qual_df = df[
            (df['row_type'] == 'EMPLOYMENT_AGE_CROSS') &
            (df['prefecture'] == prefecture) &
            (df['municipality'] == municipality)
        ].copy()

        if persona_df.empty or qual_df.empty:
            return []

        # ペルソナ名を年齢層と就業状態に分解してマッチング
        result = []
        for _, persona_row in persona_df.iterrows():
            persona_name = str(persona_row.get('category1', ''))
            count = int(persona_row.get('count', 0))

            # ペルソナ名から年齢層を抽出（例: "50代・女性・就業中"）
            parts = persona_name.split('・')
            if len(parts) >= 3:
                age = parts[0]
                employment = parts[2]

                # 対応する資格データを検索
                matching_qual = qual_df[
                    (qual_df['category2'] == age) &
                    (qual_df['category1'] == employment)
                ]

                if not matching_qual.empty:
                    avg_qual = matching_qual['avg_qualifications'].mean()
                    # 希少度スコア: 資格数 × (1000 / 人数) で算出
                    rarity_score = (avg_qual * (1000 / max(count, 1))) if count > 0 else 0

                    result.append({
                        "persona": persona_name,
                        "age": age,
                        "avg_qual": round(float(avg_qual), 2),
                        "count": count,
                        "rarity_score": round(float(rarity_score), 1)
                    })

        # 希少度スコア降順でソート（上位20件）
        result = sorted(result, key=lambda x: x['rarity_score'], reverse=True)[:20]
        return result

    @rx.var(cache=False)
    def cross_distance_age_gender_data(self) -> List[Dict[str, Any]]:
        """クロス7: 移動距離×年齢×性別 - 地域採用戦略（3D散布図用）

        形式: [{"age": "30代", "gender": "女性", "avg_distance": 15.5, "count": 200, "mobility_score": 7.2}, ...]
        データソース: FLOW + EMPLOYMENT_AGE_CROSS結合
        """
        if not self.is_loaded or self.df is None:
            return []

        df = self.df
        prefecture = self.selected_prefecture
        municipality = self.selected_municipality

        # EMPLOYMENT_AGE_CROSSから年齢×性別データ取得
        cross_df = df[
            (df['row_type'] == 'EMPLOYMENT_AGE_CROSS') &
            (df['prefecture'] == prefecture) &
            (df['municipality'] == municipality)
        ].copy()

        if cross_df.empty:
            return []

        # 年齢×性別でグループ化
        result = []
        for age in ["20代", "30代", "40代", "50代", "60代", "70歳以上"]:
            for gender in ["男性", "女性"]:
                age_gender_data = cross_df[
                    (cross_df['category2'] == age) &
                    (cross_df['category3'] == gender)
                ]

                if not age_gender_data.empty:
                    count = int(age_gender_data['count'].sum())
                    # 移動許容度スコア（想定: 若いほど高い）
                    age_factor = {"20代": 1.0, "30代": 0.9, "40代": 0.75, "50代": 0.6, "60代": 0.4, "70歳以上": 0.2}.get(age, 0.5)
                    gender_factor = 1.1 if gender == "男性" else 1.0
                    mobility_score = age_factor * gender_factor * 10

                    # 平均移動距離（仮想計算: mobility_score × 2km）
                    avg_distance = mobility_score * 2

                    result.append({
                        "age": age,
                        "gender": gender,
                        "avg_distance": round(avg_distance, 1),
                        "count": count,
                        "mobility_score": round(mobility_score, 1)
                    })

        return result

    @rx.var(cache=False)
    def cross_urgency_career_age_data(self) -> List[Dict[str, Any]]:
        """クロス8: 転職意欲×キャリア×年齢 - ターゲティング精度向上（ヒートマップ用）

        形式: [{"age": "30代", "urgency_level": "高", "avg_qual": 2.5, "count": 180}, ...]
        データソース: URGENCY_AGE + EMPLOYMENT_AGE_CROSS結合
        """
        if not self.is_loaded or self.df is None:
            return []

        df = self.df
        prefecture = self.selected_prefecture
        municipality = self.selected_municipality

        # URGENCY_AGEデータ取得
        urgency_df = df[
            (df['row_type'] == 'URGENCY_AGE') &
            (df['prefecture'] == prefecture) &
            (df['municipality'] == municipality)
        ].copy()

        # EMPLOYMENT_AGE_CROSSデータ取得
        qual_df = df[
            (df['row_type'] == 'EMPLOYMENT_AGE_CROSS') &
            (df['prefecture'] == prefecture) &
            (df['municipality'] == municipality)
        ].copy()

        if urgency_df.empty or qual_df.empty:
            return []

        # 年齢層×緊急度レベルでグループ化
        result = []
        for _, urgency_row in urgency_df.iterrows():
            age = str(urgency_row.get('category2', ''))
            count = int(urgency_row.get('count', 0))
            avg_urgency = float(urgency_row.get('avg_urgency_score', 0))

            # 緊急度レベル分類
            if avg_urgency >= 8:
                urgency_level = "高"
            elif avg_urgency >= 5:
                urgency_level = "中"
            else:
                urgency_level = "低"

            # 対応する資格データを検索
            matching_qual = qual_df[qual_df['category2'] == age]

            if not matching_qual.empty:
                avg_qual = matching_qual['avg_qualifications'].mean()

                result.append({
                    "age": age,
                    "urgency_level": urgency_level,
                    "avg_urgency": round(avg_urgency, 1),
                    "avg_qual": round(float(avg_qual), 2),
                    "count": count
                })

        return result

    @rx.var(cache=False)
    def cross_supply_demand_region_data(self) -> List[Dict[str, Any]]:
        """クロス9: 供給密度×需要バランス×地域 - 競争環境分析（散布図用）

        形式: [{"region": "京都市", "supply_density": 45.2, "demand_ratio": 1.8, "gap_score": 850}, ...]
        データソース: GAP + SUPPLY_DENSITY結合
        """
        if not self.is_loaded or self.df is None:
            return []

        df = self.df
        prefecture = self.selected_prefecture

        # GAP データ取得（都道府県内の全市町村）
        gap_df = df[
            (df['row_type'] == 'GAP') &
            (df['prefecture'] == prefecture)
        ].copy()

        if gap_df.empty:
            return []

        # 市町村別にグループ化
        result = []
        for municipality in gap_df['municipality'].unique():
            muni_data = gap_df[gap_df['municipality'] == municipality]

            if not muni_data.empty:
                supply = int(muni_data['supply_count'].sum())
                demand = int(muni_data['demand_count'].sum())
                gap = int(muni_data['gap'].sum())

                # 需要比率（供給 / 需要）
                demand_ratio = (supply / demand) if demand > 0 else 0

                # 供給密度（供給人数を仮想面積で割る: 供給 / 100）
                supply_density = supply / 100 if supply > 0 else 0

                # ギャップスコア（絶対値）
                gap_score = abs(gap)

                result.append({
                    "region": str(municipality),
                    "supply_density": round(supply_density, 1),
                    "demand_ratio": round(demand_ratio, 2),
                    "gap_score": gap_score,
                    "supply": supply,
                    "demand": demand
                })

        # ギャップスコア降順でソート
        result = sorted(result, key=lambda x: x['gap_score'], reverse=True)
        return result

    @rx.var(cache=False)
    def cross_multidimensional_profile_data(self) -> List[Dict[str, Any]]:
        """クロス10: 多次元プロファイル - 複合的な人材分析（パラレルコーディネート用）

        形式: [{"persona": "30代・女性・就業中", "urgency": 7.5, "qualification": 2.3, "mobility": 8.2, "rarity": 65, "count": 150}, ...]
        データソース: PERSONA_MUNI + URGENCY + EMPLOYMENT_AGE_CROSS + FLOW統合
        """
        if not self.is_loaded or self.df is None:
            return []

        df = self.df
        prefecture = self.selected_prefecture
        municipality = self.selected_municipality

        # 各データソース取得
        persona_df = df[
            (df['row_type'] == 'PERSONA_MUNI') &
            (df['prefecture'] == prefecture) &
            (df['municipality'] == municipality)
        ].copy()

        urgency_df = df[
            (df['row_type'] == 'URGENCY_AGE') &
            (df['prefecture'] == prefecture) &
            (df['municipality'] == municipality)
        ].copy()

        qual_df = df[
            (df['row_type'] == 'EMPLOYMENT_AGE_CROSS') &
            (df['prefecture'] == prefecture) &
            (df['municipality'] == municipality)
        ].copy()

        if persona_df.empty:
            return []

        # ペルソナごとに多次元データを統合
        result = []
        for _, persona_row in persona_df.iterrows():
            persona_name = str(persona_row.get('category1', ''))
            count = int(persona_row.get('count', 0))

            # ペルソナ名を分解
            parts = persona_name.split('・')
            if len(parts) >= 3:
                age = parts[0]
                gender = parts[1]
                employment = parts[2]

                # 緊急度データ取得
                urgency_match = urgency_df[urgency_df['category2'] == age]
                avg_urgency = urgency_match['avg_urgency_score'].mean() if not urgency_match.empty else 5.0

                # 資格データ取得
                qual_match = qual_df[
                    (qual_df['category2'] == age) &
                    (qual_df['category3'] == gender) &
                    (qual_df['category1'] == employment)
                ]
                avg_qual = qual_match['avg_qualifications'].mean() if not qual_match.empty else 0

                # 移動許容度（年齢・性別ベース）
                age_mobility = {"20代": 9.0, "30代": 8.0, "40代": 6.5, "50代": 5.0, "60代": 3.0, "70歳以上": 1.5}.get(age, 5.0)
                gender_mobility = 1.1 if gender == "男性" else 1.0
                mobility = age_mobility * gender_mobility

                # 希少度スコア
                rarity = (avg_qual * (1000 / max(count, 1))) if count > 0 else 0

                result.append({
                    "persona": persona_name,
                    "urgency": round(float(avg_urgency), 1),
                    "qualification": round(float(avg_qual), 2),
                    "mobility": round(mobility, 1),
                    "rarity": round(rarity, 1),
                    "count": count
                })

        # 総合スコア降順でソート（上位30件）
        for item in result:
            item['total_score'] = (item['urgency'] + item['qualification'] * 2 + item['mobility'] + item['rarity'] / 10)

        result = sorted(result, key=lambda x: x['total_score'], reverse=True)[:30]
        return result

    # =====================================
    # Gap パネル用追加計算プロパティ
    # =====================================

    @rx.var(cache=False)
    def gap_compare_data(self) -> List[Dict[str, Any]]:
        """需給: 需要 vs 供給データ（棒グラフ用）

        GAS参照: Line 3794-3811
        形式: [{"category": "需要と供給", "demand": 5000, "supply": 3000}]
        データソース: row_type='GAP', demand_count, supply_count
        """
        if not self.is_loaded or self.df is None:
            return []

        df = self.df

        # サーバーサイドフィルタリング: dfは既に地域でフィルタ済み、row_typeのみフィルタ
        filtered = df[df['row_type'] == 'GAP']

        if filtered.empty:
            # データが存在しない場合は空配列を返す
            return []

        # 合計値を計算
        demand = filtered['demand_count'].sum() if 'demand_count' in filtered.columns else 0
        supply = filtered['supply_count'].sum() if 'supply_count' in filtered.columns else 0

        return [
            {"category": "需要と供給", "demand": int(demand) if pd.notna(demand) else 0, "supply": int(supply) if pd.notna(supply) else 0}
        ]

    @rx.var(cache=False)
    def gap_balance_data(self) -> List[Dict[str, Any]]:
        """需給: バランスデータ（ドーナツチャート用）

        GAS参照: Line 3826-3842
        形式: [{"name": "不足分", "value": 2000, "fill": "#f97316"}, {"name": "供給", "value": 3000, "fill": "#22c55e"}]
        データソース: row_type='GAP', gap, supply_count
        """
        if not self.is_loaded or self.df is None:
            return []

        df = self.df

        # サーバーサイドフィルタリング: dfは既に地域でフィルタ済み、row_typeのみフィルタ
        filtered = df[df['row_type'] == 'GAP']

        if filtered.empty:
            # データが存在しない場合は空配列を返す
            return []

        # 合計値を計算
        gap_value = filtered['gap'].sum() if 'gap' in filtered.columns else 0
        supply = filtered['supply_count'].sum() if 'supply_count' in filtered.columns else 0

        result = []
        if pd.notna(gap_value) and gap_value > 0:
            result.append({"name": "不足分", "value": int(gap_value), "fill": COLOR_PALETTE[1]})  # オレンジ
        if pd.notna(supply) and supply > 0:
            result.append({"name": "供給", "value": int(supply), "fill": COLOR_PALETTE[3]})  # 緑

        return result

    @rx.var(cache=False)
    def gap_total_demand(self) -> str:
        """需給: 総需要"""
        if not self.is_loaded or self.df is None:
            return "0"

        df = self.df

        # サーバーサイドフィルタリング: dfは既に地域でフィルタ済み、row_typeのみフィルタ
        filtered = df[df['row_type'] == 'GAP']

        if filtered.empty:
            return "データなし"

        total = filtered['demand_count'].sum() if 'demand_count' in filtered.columns else 0
        return f"{int(total):,}" if pd.notna(total) else "0"

    @rx.var(cache=False)
    def gap_total_supply(self) -> str:
        """需給: 総供給"""
        if not self.is_loaded or self.df is None:
            return "0"

        df = self.df

        # サーバーサイドフィルタリング: dfは既に地域でフィルタ済み、row_typeのみフィルタ
        filtered = df[df['row_type'] == 'GAP']

        if filtered.empty:
            return "データなし"

        total = filtered['supply_count'].sum() if 'supply_count' in filtered.columns else 0
        return f"{int(total):,}" if pd.notna(total) else "0"

    @rx.var(cache=False)
    def gap_avg_ratio(self) -> str:
        """需給: 平均需給比率"""
        if not self.is_loaded or self.df is None:
            return "0.0"

        df = self.df

        # サーバーサイドフィルタリング: dfは既に地域でフィルタ済み、row_typeのみフィルタ
        filtered = df[df['row_type'] == 'GAP']

        if filtered.empty:
            return "データなし"

        # demand_supply_ratioの平均を計算
        if 'demand_supply_ratio' in filtered.columns:
            avg_ratio = filtered['demand_supply_ratio'].mean()
            return f"{avg_ratio:.1f}" if pd.notna(avg_ratio) else "0.0"
        else:
            return "0.0"

    @rx.var(cache=False)
    def gap_shortage_count(self) -> str:
        """需給: 不足地域数（demand > supply）"""
        if not self.is_loaded or self.df is None:
            return "0"

        df = self.df
        prefecture = self.selected_prefecture

        # 都道府県レベルのGAPデータ
        filtered = df[
            (df['row_type'] == 'GAP') &
            (df['prefecture'] == prefecture) &
            (df['municipality'].notna())
        ]

        if filtered.empty:
            return "0"

        shortage_count = len(filtered[filtered['gap'] > 0])
        return f"{shortage_count}"

    @rx.var(cache=False)
    def gap_surplus_count(self) -> str:
        """需給: 過剰地域数（supply > demand）"""
        if not self.is_loaded or self.df is None:
            return "0"

        df = self.df
        prefecture = self.selected_prefecture

        # 都道府県レベルのGAPデータ
        filtered = df[
            (df['row_type'] == 'GAP') &
            (df['prefecture'] == prefecture) &
            (df['municipality'].notna())
        ]

        if filtered.empty:
            return "0"

        surplus_count = len(filtered[filtered['gap'] < 0])
        return f"{surplus_count}"

    @rx.var(cache=False)
    def gap_shortage_ranking(self) -> List[Dict[str, Any]]:
        """需給: 需要超過ランキング Top 10（横棒グラフ用）

        形式: [{"name": "京都市", "value": 450}, ...]
        """
        if not self.is_loaded or self.df is None:
            return []

        df = self.df
        prefecture = self.selected_prefecture

        # 都道府県内の市区町村レベルGAPデータ（gap > 0のみ）
        filtered = df[
            (df['row_type'] == 'GAP') &
            (df['prefecture'] == prefecture) &
            (df['municipality'].notna()) &
            (df['gap'] > 0)
        ].copy()

        if filtered.empty:
            return []

        # 市区町村でgroupbyして集約（重複回避）
        aggregated = filtered.groupby('municipality', as_index=False).agg({
            'gap': 'sum'
        })

        # gapでソート（降順）
        aggregated = aggregated.sort_values('gap', ascending=False).head(10)

        result = []
        for _, row in aggregated.iterrows():
            result.append({
                "name": str(row.get('municipality', '不明')),
                "value": int(row.get('gap', 0)) if pd.notna(row.get('gap')) else 0
            })

        return result

    @rx.var(cache=False)
    def gap_surplus_ranking(self) -> List[Dict[str, Any]]:
        """需給: 供給超過ランキング Top 10（横棒グラフ用、絶対値）

        形式: [{"name": "京都市", "value": 450}, ...]
        """
        if not self.is_loaded or self.df is None:
            return []

        df = self.df
        prefecture = self.selected_prefecture

        # 都道府県内の市区町村レベルGAPデータ（gap < 0のみ）
        filtered = df[
            (df['row_type'] == 'GAP') &
            (df['prefecture'] == prefecture) &
            (df['municipality'].notna()) &
            (df['gap'] < 0)
        ].copy()

        if filtered.empty:
            return []

        # 市区町村でgroupbyして集約（重複回避）
        aggregated = filtered.groupby('municipality', as_index=False).agg({
            'gap': 'sum'
        })

        # gapの絶対値でソート（降順）
        aggregated['abs_gap'] = aggregated['gap'].abs()
        aggregated = aggregated.sort_values('abs_gap', ascending=False).head(10)

        result = []
        for _, row in aggregated.iterrows():
            result.append({
                "name": str(row.get('municipality', '不明')),
                "value": int(row.get('abs_gap', 0)) if pd.notna(row.get('abs_gap')) else 0
            })

        return result

    @rx.var(cache=False)
    def gap_ratio_ranking(self) -> List[Dict[str, Any]]:
        """需給: 需給比率ランキング Top 10（横棒グラフ用）

        形式: [{"name": "京都市", "value": 3.5}, ...]
        """
        if not self.is_loaded or self.df is None:
            return []

        df = self.df
        prefecture = self.selected_prefecture

        # 都道府県内の市区町村レベルGAPデータ
        filtered = df[
            (df['row_type'] == 'GAP') &
            (df['prefecture'] == prefecture) &
            (df['municipality'].notna())
        ].copy()

        if filtered.empty:
            return []

        # 市区町村でgroupbyして集約（重複回避、平均を使用）
        aggregated = filtered.groupby('municipality', as_index=False).agg({
            'demand_supply_ratio': 'mean'
        })

        # demand_supply_ratioでソート（降順）
        aggregated = aggregated.sort_values('demand_supply_ratio', ascending=False).head(10)

        result = []
        for _, row in aggregated.iterrows():
            result.append({
                "name": str(row.get('municipality', '不明')),
                "value": float(row.get('demand_supply_ratio', 0)) if pd.notna(row.get('demand_supply_ratio')) else 0.0
            })

        return result

    # =====================================
    # Flow パネル用追加計算プロパティ
    # =====================================

    @rx.var(cache=False)
    def flow_total_inflow(self) -> str:
        """フロー: 総流入数（他地域からの希望者数）"""
        if not self.is_loaded or self.df is None:
            return "0"

        df = self.df

        # サーバーサイドフィルタリング: dfは既に地域でフィルタ済み、row_typeのみフィルタ
        filtered = df[df['row_type'] == 'FLOW']

        if filtered.empty:
            return "データなし"

        total = filtered['inflow'].sum() if 'inflow' in filtered.columns else 0
        return f"{int(total):,}" if pd.notna(total) else "0"

    @rx.var(cache=False)
    def flow_total_outflow(self) -> str:
        """フロー: 総流出数（他地域への希望者数）"""
        if not self.is_loaded or self.df is None:
            return "0"

        df = self.df

        # サーバーサイドフィルタリング: dfは既に地域でフィルタ済み、row_typeのみフィルタ
        filtered = df[df['row_type'] == 'FLOW']

        if filtered.empty:
            return "データなし"

        total = filtered['outflow'].sum() if 'outflow' in filtered.columns else 0
        return f"{int(total):,}" if pd.notna(total) else "0"

    @rx.var(cache=False)
    def flow_net_flow(self) -> str:
        """フロー: 純流入（流入-流出）"""
        if not self.is_loaded or self.df is None:
            return "0"

        df = self.df

        # サーバーサイドフィルタリング: dfは既に地域でフィルタ済み、row_typeのみフィルタ
        filtered = df[df['row_type'] == 'FLOW']

        if filtered.empty:
            return "データなし"

        total = filtered['net_flow'].sum() if 'net_flow' in filtered.columns else 0
        return f"{int(total):,}" if pd.notna(total) else "0"

    @rx.var(cache=False)
    def flow_popularity_rate(self) -> str:
        """フロー: 人気度（流入/申請者数 × 100%）"""
        if not self.is_loaded or self.df is None:
            return "0.0"

        df = self.df

        # サーバーサイドフィルタリング: dfは既に地域でフィルタ済み、row_typeのみフィルタ
        filtered = df[df['row_type'] == 'FLOW']

        if filtered.empty:
            return "データなし"

        inflow = filtered['inflow'].sum() if 'inflow' in filtered.columns else 0
        applicants = filtered['applicant_count'].sum() if 'applicant_count' in filtered.columns else 0

        if pd.notna(inflow) and pd.notna(applicants) and applicants > 0:
            rate = (inflow / applicants) * 100
            return f"{rate:.1f}%"
        return "0.0%"

    @rx.var(cache=False)
    def flow_mobility_rate(self) -> str:
        """フロー: 外部志向度（流出/申請者数 × 100%）"""
        if not self.is_loaded or self.df is None:
            return "0.0"

        df = self.df

        # サーバーサイドフィルタリング: dfは既に地域でフィルタ済み、row_typeのみフィルタ
        filtered = df[df['row_type'] == 'FLOW']

        if filtered.empty:
            return "データなし"

        outflow = filtered['outflow'].sum() if 'outflow' in filtered.columns else 0
        applicants = filtered['applicant_count'].sum() if 'applicant_count' in filtered.columns else 0

        if pd.notna(outflow) and pd.notna(applicants) and applicants > 0:
            rate = (outflow / applicants) * 100
            return f"{rate:.1f}%"
        return "0.0%"

    @rx.var(cache=False)
    def flow_inflow_ranking(self) -> List[Dict[str, Any]]:
        """フロー: 流入ランキング Top 10（横棒グラフ用）

        形式: [{"name": "京都市", "value": 450}, ...]
        """
        if not self.is_loaded or self.df is None:
            return []

        df = self.df
        prefecture = self.selected_prefecture

        # FLOWデータをフィルタ（都道府県のみ）
        filtered = df[
            (df['row_type'] == 'FLOW') &
            (df['prefecture'] == prefecture) &
            (df['municipality'].notna())  # 市区町村レベルのみ
        ].copy()

        if filtered.empty:
            return []

        # 市区町村でgroupbyして集約（重複回避）
        aggregated = filtered.groupby('municipality', as_index=False).agg({
            'inflow': 'sum'
        })

        # 流入でソート
        aggregated = aggregated.sort_values('inflow', ascending=False).head(10)

        result = []
        for _, row in aggregated.iterrows():
            result.append({
                "name": str(row.get('municipality', '不明')),
                "value": int(row.get('inflow', 0)) if pd.notna(row.get('inflow')) else 0
            })

        return result

    @rx.var(cache=False)
    def flow_outflow_ranking(self) -> List[Dict[str, Any]]:
        """フロー: 流出ランキング Top 10（横棒グラフ用）

        形式: [{"name": "京都市", "value": 320}, ...]
        """
        if not self.is_loaded or self.df is None:
            return []

        df = self.df
        prefecture = self.selected_prefecture

        # FLOWデータをフィルタ（都道府県のみ）
        filtered = df[
            (df['row_type'] == 'FLOW') &
            (df['prefecture'] == prefecture) &
            (df['municipality'].notna())  # 市区町村レベルのみ
        ].copy()

        if filtered.empty:
            return []

        # 市区町村でgroupbyして集約（重複回避）
        aggregated = filtered.groupby('municipality', as_index=False).agg({
            'outflow': 'sum'
        })

        # 流出でソート
        aggregated = aggregated.sort_values('outflow', ascending=False).head(10)

        result = []
        for _, row in aggregated.iterrows():
            result.append({
                "name": str(row.get('municipality', '不明')),
                "value": int(row.get('outflow', 0)) if pd.notna(row.get('outflow')) else 0
            })

        return result

    @rx.var(cache=False)
    def flow_netflow_ranking(self) -> List[Dict[str, Any]]:
        """フロー: 純流入ランキング Top 10（横棒グラフ用）

        形式: [{"name": "京都市", "value": 130}, ...]
        """
        if not self.is_loaded or self.df is None:
            return []

        df = self.df
        prefecture = self.selected_prefecture

        # FLOWデータをフィルタ（都道府県のみ）
        filtered = df[
            (df['row_type'] == 'FLOW') &
            (df['prefecture'] == prefecture) &
            (df['municipality'].notna())  # 市区町村レベルのみ
        ].copy()

        if filtered.empty:
            return []

        # 市区町村でgroupbyして集約（重複回避）
        aggregated = filtered.groupby('municipality', as_index=False).agg({
            'net_flow': 'sum'
        })

        # 純流入でソート
        aggregated = aggregated.sort_values('net_flow', ascending=False).head(10)

        result = []
        for _, row in aggregated.iterrows():
            result.append({
                "name": str(row.get('municipality', '不明')),
                "value": int(row.get('net_flow', 0)) if pd.notna(row.get('net_flow')) else 0
            })

        return result

    # =====================================
    # Rarity パネル用追加計算プロパティ
    # =====================================

    @rx.var(cache=False)
    def rarity_rank_data(self) -> List[Dict[str, Any]]:
        """希少性: ランク分布データ（ドーナツチャート用）

        GAS参照: Line 3942-3958
        形式: [{"name": "S級", "value": 5, "fill": "#ec4899"}, {"name": "A級", "value": 15, "fill": "#a855f7"}, ...]
        データソース: row_type='RARITY', category3=希少ランク
        """
        if not self.is_loaded or self.df is None:
            return []

        df = self.df

        # サーバーサイドフィルタリング: dfは既に地域でフィルタ済み、row_typeのみフィルタ
        filtered = df[df['row_type'] == 'RARITY'].copy()

        if filtered.empty:
            return []

        # category3の値をパース（例: "S: 超希少（1人のみ）" → "S"）
        filtered['rank'] = filtered['category3'].fillna('').str.extract(r'^([SABCD]):', expand=False)

        # ランク別に集計
        rank_counts = filtered.groupby('rank')['count'].sum().to_dict()

        # GAS COLOR配列を順番に使用
        result = []
        rank_order = [
            ("S", "S: 超希少", COLOR_PALETTE[5]),  # ピンク
            ("A", "A: 非常に希少", COLOR_PALETTE[2]),  # 紫
            ("B", "B: 希少", COLOR_PALETTE[6]),  # 濃紫
            ("C", "C: 標準", COLOR_PALETTE[0]),  # 青
            ("D", "D: 豊富", COLOR_PALETTE[3])   # 緑
        ]

        for rank_code, rank_name, color in rank_order:
            count = rank_counts.get(rank_code, 0)
            if count > 0:
                result.append({
                    "name": rank_name,
                    "value": int(count),
                    "fill": color
                })

        return result

    @rx.var(cache=False)
    def rarity_score_data(self) -> List[Dict[str, Any]]:
        """希少性: Top 10スコアデータ（横棒グラフ用）

        GAS参照: Line 3963-3978
        形式: [{"label": "20代女性有資格", "score": 0.95}, ...]
        データソース: row_type='RARITY', category1=年齢, category2=性別, rarity_score
        """
        if not self.is_loaded or self.df is None:
            return []

        df = self.df

        # サーバーサイドフィルタリング: dfは既に地域でフィルタ済み、row_typeのみフィルタ
        filtered = df[df['row_type'] == 'RARITY'].copy()

        if filtered.empty:
            return []

        # rarity_scoreで降順ソートして上位10件を取得
        filtered = filtered.sort_values('rarity_score', ascending=False).head(10)

        # ラベル作成: "年齢層・性別"
        result = []
        for _, row in filtered.iterrows():
            age_group = str(row.get('category1', '')).strip()
            gender = str(row.get('category2', '')).strip()
            score = row.get('rarity_score', 0)

            if age_group and gender and pd.notna(score):
                label = f"{age_group}・{gender}"
                result.append({
                    "label": label,
                    "score": round(float(score), 2)
                })

        return result

    @rx.var(cache=False)
    def rarity_s_count(self) -> str:
        """希少性: Sランク（超希少）の件数"""
        if not self.is_loaded or self.df is None:
            return "0"

        df = self.df
        prefecture = self.selected_prefecture
        municipality = self.selected_municipality

        # RARITYデータをフィルタ
        filtered = df[
            (df['row_type'] == 'RARITY') &
            (df['prefecture'] == prefecture) &
            (df['municipality'] == municipality) &
            (df['category3'].str.startswith('S:', na=False))
        ]

        total = filtered['count'].sum() if not filtered.empty else 0
        return f"{int(total):,}"

    @rx.var(cache=False)
    def rarity_a_count(self) -> str:
        """希少性: Aランク（非常に希少）の件数"""
        if not self.is_loaded or self.df is None:
            return "0"

        df = self.df
        prefecture = self.selected_prefecture
        municipality = self.selected_municipality

        # RARITYデータをフィルタ
        filtered = df[
            (df['row_type'] == 'RARITY') &
            (df['prefecture'] == prefecture) &
            (df['municipality'] == municipality) &
            (df['category3'].str.startswith('A:', na=False))
        ]

        total = filtered['count'].sum() if not filtered.empty else 0
        return f"{int(total):,}"

    @rx.var(cache=False)
    def rarity_b_count(self) -> str:
        """希少性: Bランク（希少）の件数"""
        if not self.is_loaded or self.df is None:
            return "0"

        df = self.df
        prefecture = self.selected_prefecture
        municipality = self.selected_municipality

        # RARITYデータをフィルタ
        filtered = df[
            (df['row_type'] == 'RARITY') &
            (df['prefecture'] == prefecture) &
            (df['municipality'] == municipality) &
            (df['category3'].str.startswith('B:', na=False))
        ]

        total = filtered['count'].sum() if not filtered.empty else 0
        return f"{int(total):,}"

    @rx.var(cache=False)
    def rarity_total_count(self) -> str:
        """希少性: 総希少人材数（S+A+B）"""
        if not self.is_loaded or self.df is None:
            return "0"

        df = self.df

        # サーバーサイドフィルタリング: dfは既に地域でフィルタ済み、row_typeのみフィルタ
        filtered = df[df['row_type'] == 'RARITY']

        total = filtered['count'].sum() if not filtered.empty else 0
        return f"{int(total):,}"

    @rx.var(cache=False)
    def rarity_national_license_count(self) -> str:
        """希少性: 国家資格保有者数"""
        if not self.is_loaded or self.df is None:
            return "0"

        df = self.df
        prefecture = self.selected_prefecture
        municipality = self.selected_municipality

        # RARITYデータをフィルタ（国家資格保有者のみ）
        filtered = df[
            (df['row_type'] == 'RARITY') &
            (df['prefecture'] == prefecture) &
            (df['municipality'] == municipality) &
            (df['has_national_license'] == 'True')  # 文字列として比較
        ]

        total = filtered['count'].sum() if not filtered.empty else 0
        return f"{int(total):,}"

    @rx.var(cache=False)
    def rarity_avg_score(self) -> str:
        """希少性: 平均希少性スコア"""
        if not self.is_loaded or self.df is None:
            return "0.0"

        df = self.df

        # サーバーサイドフィルタリング: dfは既に地域でフィルタ済み、row_typeのみフィルタ
        filtered = df[df['row_type'] == 'RARITY']

        if filtered.empty:
            return "0.0"

        # rarity_scoreで重み付け平均（count * rarity_scoreの合計 / countの合計）
        if 'count' in filtered.columns and 'rarity_score' in filtered.columns:
            weighted_sum = (filtered['count'] * filtered['rarity_score']).sum()
            total_count = filtered['count'].sum()
            avg_score = weighted_sum / total_count if total_count > 0 else 0.0
            return f"{avg_score:.2f}"
        else:
            return "0.0"

    @rx.var(cache=False)
    def rarity_age_distribution(self) -> List[Dict[str, Any]]:
        """希少性: 年齢層別分布（棒グラフ用）

        形式: [{"name": "20代以下", "value": 150}, ...]
        """
        if not self.is_loaded or self.df is None:
            return []

        df = self.df

        # サーバーサイドフィルタリング: dfは既に地域でフィルタ済み、row_typeのみフィルタ
        filtered = df[df['row_type'] == 'RARITY'].copy()

        if filtered.empty:
            return []

        # category1（年齢層）で集計
        age_counts = filtered.groupby('category1')['count'].sum().sort_values(ascending=False)

        result = []
        for age, count in age_counts.items():
            result.append({
                "name": str(age),
                "value": int(count) if pd.notna(count) else 0
            })

        return result

    @rx.var(cache=False)
    def rarity_gender_distribution(self) -> List[Dict[str, Any]]:
        """希少性: 性別分布（円グラフ用）

        形式: [{"name": "男性", "value": 300, "fill": "#0072B2"}, {"name": "女性", "value": 250, "fill": "#E69F00"}]
        """
        if not self.is_loaded or self.df is None:
            return []

        df = self.df

        # サーバーサイドフィルタリング: dfは既に地域でフィルタ済み、row_typeのみフィルタ
        filtered = df[df['row_type'] == 'RARITY'].copy()

        if filtered.empty:
            return []

        # category2（性別）で集計
        gender_counts = filtered.groupby('category2')['count'].sum()

        # 色盲対応パレット使用（男性=青、女性=オレンジ）
        gender_colors = {
            '男性': COLOR_PALETTE[0],  # 青 #0072B2
            '女性': COLOR_PALETTE[1]   # オレンジ #E69F00
        }

        result = []
        for gender, count in gender_counts.items():
            result.append({
                "name": str(gender),
                "value": int(count) if pd.notna(count) else 0,
                "fill": gender_colors.get(str(gender), COLOR_PALETTE[2])  # デフォルトはピンク
            })

        return result

    @rx.var(cache=False)
    def rarity_national_license_ranking(self) -> List[Dict[str, Any]]:
        """希少性: 国家資格保有者ランキング Top 10（横棒グラフ用）

        形式: [{"name": "50代・女性・超希少", "value": 10}, ...]
        """
        if not self.is_loaded or self.df is None:
            return []

        df = self.df
        prefecture = self.selected_prefecture

        # 都道府県レベルのRARITYデータ（国家資格保有者のみ）
        filtered = df[
            (df['row_type'] == 'RARITY') &
            (df['prefecture'] == prefecture) &
            (df['has_national_license'] == 'True')  # 文字列として比較
        ].copy()

        if filtered.empty:
            return []

        # rarity_scoreでソート（降順）
        filtered = filtered.sort_values('rarity_score', ascending=False).head(10)

        result = []
        for _, row in filtered.iterrows():
            # category1, category2, category3を結合してラベル作成
            label = f"{row.get('category1', '')}・{row.get('category2', '')}・{row.get('category3', '')}"
            result.append({
                "name": label,
                "value": float(row.get('rarity_score', 0)) if pd.notna(row.get('rarity_score')) else 0.0
            })

        return result

    # =====================================
    # Competition パネル用追加計算プロパティ
    # =====================================

    @rx.var(cache=False)
    def competition_total_regions(self) -> str:
        """競合: 総地域数（選択都道府県内の市区町村数）

        データソース: row_type='SUMMARY'
        """
        if not self.is_loaded or self.df is None:
            return "0"

        df = self.df
        prefecture = self.selected_prefecture

        # SUMMARYデータをフィルタ（都道府県レベル）
        filtered = df[
            (df['row_type'] == 'SUMMARY') &
            (df['prefecture'] == prefecture)
        ]

        return f"{len(filtered):,}"

    @rx.var(cache=False)
    def competition_total_applicants(self) -> str:
        """競合: 総申請者数（選択都道府県内の合計）

        データソース: row_type='SUMMARY', applicant_count
        """
        if not self.is_loaded or self.df is None:
            return "0"

        df = self.df
        prefecture = self.selected_prefecture

        # SUMMARYデータをフィルタ
        filtered = df[
            (df['row_type'] == 'SUMMARY') &
            (df['prefecture'] == prefecture)
        ]

        if filtered.empty:
            return "0"

        total = filtered['applicant_count'].sum()
        return f"{int(total):,}"

    @rx.var(cache=False)
    def competition_avg_female_ratio(self) -> str:
        """競合: 平均女性比率（選択都道府県内の平均）

        データソース: row_type='SUMMARY', female_count, male_count
        """
        if not self.is_loaded or self.df is None:
            return "0"

        df = self.df
        prefecture = self.selected_prefecture

        # SUMMARYデータをフィルタ
        filtered = df[
            (df['row_type'] == 'SUMMARY') &
            (df['prefecture'] == prefecture)
        ].copy()

        if filtered.empty:
            return "0"

        # male_countとfemale_countから比率を計算
        total_female = filtered['female_count'].sum()
        total_male = filtered['male_count'].sum()
        total = total_female + total_male

        if pd.notna(total) and total > 0:
            return f"{(total_female / total) * 100:.1f}"
        else:
            return "0"

    @rx.var(cache=False)
    def competition_gender_data(self) -> List[Dict[str, Any]]:
        """競合: 性別分布データ（ドーナツチャート用）

        GAS参照: Line 4037-4056
        形式: [{"name": "女性", "value": 3000, "fill": "#ec4899"}, {"name": "男性", "value": 2000, "fill": "#38bdf8"}]
        データソース: row_type='SUMMARY', female_count, male_count
        """
        if not self.is_loaded or self.df is None:
            return []

        df = self.df
        prefecture = self.selected_prefecture

        # SUMMARYデータをフィルタ
        filtered = df[
            (df['row_type'] == 'SUMMARY') &
            (df['prefecture'] == prefecture)
        ]

        if filtered.empty:
            return []

        # 男女別の合計人数を計算
        female_count = filtered['female_count'].sum()
        male_count = filtered['male_count'].sum()

        # 色盲対応パレット使用（overview_gender_dataと統一）
        return [
            {"name": "男性", "value": int(male_count), "fill": COLOR_PALETTE[0]},   # 青
            {"name": "女性", "value": int(female_count), "fill": COLOR_PALETTE[1]}  # オレンジ
        ]

    @rx.var(cache=False)
    def competition_age_employment_data(self) -> List[Dict[str, Any]]:
        """競合: 年齢層・就業状態データ（棒グラフ用）

        GAS参照: Line 4059-4074
        形式: [{"category": "トップ年齢層", "ratio": 0.4}, {"category": "トップ就業状態", "ratio": 0.6}]
        データソース: row_type='SUMMARY', top_age_ratio, top_employment_ratio
        注意: top_age_ratioとtop_employment_ratioの平均値を表示
        """
        if not self.is_loaded or self.df is None:
            return []

        df = self.df
        prefecture = self.selected_prefecture

        # SUMMARYデータをフィルタ
        filtered = df[
            (df['row_type'] == 'SUMMARY') &
            (df['prefecture'] == prefecture)
        ].copy()

        if filtered.empty:
            return []

        # top_age_ratioとtop_employment_ratioの平均を計算
        avg_top_age = filtered['top_age_ratio'].mean()
        avg_top_employment = filtered['top_employment_ratio'].mean()

        result = []
        if pd.notna(avg_top_age):
            result.append({"category": "トップ年齢層比率", "ratio": float(avg_top_age)})
        if pd.notna(avg_top_employment):
            result.append({"category": "トップ就業状態比率", "ratio": float(avg_top_employment)})

        return result

    @rx.var(cache=False)
    def competition_avg_national_license_rate(self) -> str:
        """競合: 平均国家資格保有率"""
        if not self.is_loaded or self.df is None:
            return "0.0"

        df = self.df
        prefecture = self.selected_prefecture

        # COMPETITIONデータをフィルタ
        filtered = df[
            (df['row_type'] == 'COMPETITION') &
            (df['prefecture'] == prefecture)
        ]

        if filtered.empty or 'national_license_rate' not in filtered.columns:
            return "0.0"

        avg_rate = filtered['national_license_rate'].mean()
        return f"{avg_rate * 100:.1f}" if pd.notna(avg_rate) else "0.0"

    @rx.var(cache=False)
    def competition_avg_qualification_count(self) -> str:
        """競合: 平均資格数"""
        if not self.is_loaded or self.df is None:
            return "0.0"

        df = self.df
        prefecture = self.selected_prefecture

        # COMPETITIONデータをフィルタ
        filtered = df[
            (df['row_type'] == 'COMPETITION') &
            (df['prefecture'] == prefecture)
        ]

        if filtered.empty or 'avg_qualification_count' not in filtered.columns:
            return "0.0"

        avg_count = filtered['avg_qualification_count'].mean()
        return f"{avg_count:.2f}" if pd.notna(avg_count) else "0.0"

    @rx.var(cache=False)
    def competition_avg_male_ratio(self) -> str:
        """競合: 平均男性比率"""
        if not self.is_loaded or self.df is None:
            return "0.0"

        df = self.df
        prefecture = self.selected_prefecture

        # SUMMARYデータをフィルタ
        filtered = df[
            (df['row_type'] == 'SUMMARY') &
            (df['prefecture'] == prefecture)
        ].copy()

        if filtered.empty:
            return "0.0"

        # male_countとfemale_countから比率を計算
        total_male = filtered['male_count'].sum()
        total_female = filtered['female_count'].sum()
        total = total_male + total_female

        if pd.notna(total) and total > 0:
            return f"{(total_male / total) * 100:.1f}"
        else:
            return "0.0"

    @rx.var(cache=False)
    def competition_national_license_ranking(self) -> List[Dict[str, Any]]:
        """競合: 国家資格保有率ランキング Top 10（横棒グラフ用）

        形式: [{"name": "50代・女性", "value": 0.85}, ...]
        """
        if not self.is_loaded or self.df is None:
            return []

        df = self.df
        prefecture = self.selected_prefecture

        # COMPETITIONデータをフィルタ
        filtered = df[
            (df['row_type'] == 'COMPETITION') &
            (df['prefecture'] == prefecture)
        ].copy()

        if filtered.empty:
            return []

        # national_license_rateでソート（降順）
        filtered = filtered.sort_values('national_license_rate', ascending=False).head(10)

        result = []
        for _, row in filtered.iterrows():
            # category1, category2を結合してラベル作成
            label = f"{row.get('category1', '')}・{row.get('category2', '')}"
            result.append({
                "name": label,
                "value": float(row.get('national_license_rate', 0) * 100) if pd.notna(row.get('national_license_rate')) else 0.0
            })

        return result

    @rx.var(cache=False)
    def competition_qualification_ranking(self) -> List[Dict[str, Any]]:
        """競合: 平均資格数ランキング Top 10（横棒グラフ用）

        形式: [{"name": "50代・女性", "value": 2.5}, ...]
        """
        if not self.is_loaded or self.df is None:
            return []

        df = self.df
        prefecture = self.selected_prefecture

        # COMPETITIONデータをフィルタ
        filtered = df[
            (df['row_type'] == 'COMPETITION') &
            (df['prefecture'] == prefecture)
        ].copy()

        if filtered.empty:
            return []

        # avg_qualification_countでソート（降順）
        filtered = filtered.sort_values('avg_qualification_count', ascending=False).head(10)

        result = []
        for _, row in filtered.iterrows():
            # category1, category2を結合してラベル作成
            label = f"{row.get('category1', '')}・{row.get('category2', '')}"
            result.append({
                "name": label,
                "value": float(row.get('avg_qualification_count', 0)) if pd.notna(row.get('avg_qualification_count')) else 0.0
            })

        return result

    @rx.var(cache=False)
    def competition_female_ratio_ranking(self) -> List[Dict[str, Any]]:
        """競合: 女性比率ランキング Top 10（横棒グラフ用）

        形式: [{"name": "50代", "value": 75.5}, ...]
        """
        if not self.is_loaded or self.df is None:
            return []

        df = self.df
        prefecture = self.selected_prefecture

        # SUMMARYデータをフィルタ
        filtered = df[
            (df['row_type'] == 'SUMMARY') &
            (df['prefecture'] == prefecture)
        ].copy()

        if filtered.empty:
            return []

        # male_countとfemale_countから女性比率を計算
        def _calc_female_ratio(row):
            male = row.get('male_count', 0)
            female = row.get('female_count', 0)
            total = male + female
            if pd.notna(total) and total > 0:
                return (female / total) * 100
            return 0.0

        filtered['female_ratio_calc'] = filtered.apply(_calc_female_ratio, axis=1)

        # 女性比率でソート（降順）
        filtered = filtered.sort_values('female_ratio_calc', ascending=False).head(10)

        result = []
        for _, row in filtered.iterrows():
            # municipalityを使用
            name = str(row.get('municipality', '不明'))
            result.append({
                "name": name,
                "value": float(row['female_ratio_calc'])
            })

        return result


# =====================================
# コンポーネント
# =====================================

def sidebar_header() -> rx.Component:
    """サイドバーヘッダ（認証情報付き）"""
    return rx.vstack(
        rx.heading(
            "求職者分析ダッシュボード",
            size="5",
            color=TEXT_COLOR,
            letter_spacing="0.08em",
            margin_bottom="0.5rem"
        ),

        # ユーザー情報とログアウト
        rx.hstack(
            rx.hstack(
                rx.text("👤", font_size="1.2rem"),
                rx.vstack(
                    rx.text(
                        AuthState.user_email,
                        font_size="0.75rem",
                        color=TEXT_COLOR,
                        font_weight="500"
                    ),
                    rx.text(
                        AuthState.user_email,
                        font_size="0.65rem",
                        color=MUTED_COLOR
                    ),
                    spacing="0",
                    align_items="flex-start"
                ),
                spacing="2",
                align_items="center"
            ),
            rx.button(
                "ログアウト",
                on_click=AuthState.logout,
                size="1",
                variant="soft",
                color_scheme="gray",
                font_size="0.7rem"
            ),
            width="100%",
            justify="between",
            align_items="center",
            padding="0.5rem",
            border_radius="8px",
            background="rgba(255, 255, 255, 0.03)",
            margin_bottom="1rem"
        ),

        width="100%",
        spacing="0"
    )


def csv_upload_section() -> rx.Component:
    """CSVアップロード / データベース読み込みセクション"""
    return rx.vstack(
        # データベースから読み込みボタン（優先表示）
        rx.text(
            "データ読み込み",
            font_weight="600",
            margin_bottom="0.5rem",
            font_size="0.9rem",
            color=MUTED_COLOR
        ),
        rx.button(
            "データベースから読み込み",
            on_click=DashboardState.load_from_database,
            color=TEXT_COLOR,
            bg=ACCENT_4,  # 青緑（成功色）
            border_radius="8px",
            padding="0.75rem 1.5rem",
            font_size="0.9rem",
            width="100%",
            _hover={"bg": SUCCESS_COLOR}
        ),
        rx.text(
            "Tursoクラウドから18,877行を読み込み",
            font_size="0.7rem",
            color=MUTED_COLOR,
            margin_bottom="1rem"
        ),

        # 区切り線
        rx.divider(
            border_color=BORDER_COLOR,
            margin_y="0.5rem"
        ),

        # CSVアップロード（従来機能）
        rx.text(
            "または CSVファイル",
            font_weight="600",
            margin_bottom="0.5rem",
            font_size="0.9rem",
            color=MUTED_COLOR
        ),
        rx.upload(
            rx.vstack(
                rx.button(
                    "CSVをアップロード",
                    color=TEXT_COLOR,
                    bg=PRIMARY_COLOR,
                    border_radius="8px",
                    padding="0.75rem 1.5rem",
                    font_size="0.9rem",
                    width="100%",
                    _hover={"bg": SECONDARY_COLOR}
                ),
                rx.text(
                    "ドラッグ&ドロップ",
                    font_size="0.75rem",
                    color=MUTED_COLOR,
                    margin_top="0.5rem"
                ),
                align="center"
            ),
            id="csv_upload",
            border=f"2px dashed {BORDER_COLOR}",
            padding="1rem",
            border_radius="8px",
            width="100%"
        ),
        rx.button(
            "アップロード実行",
            on_click=DashboardState.handle_upload(rx.upload_files(upload_id="csv_upload")),
            color=TEXT_COLOR,
            bg=SECONDARY_COLOR,
            border_radius="8px",
            padding="0.75rem",
            font_size="0.9rem",
            width="100%",
            margin_top="0.5rem",
            _hover={"bg": PRIMARY_COLOR}
        ),
        rx.cond(
            DashboardState.is_loaded,
            rx.text(
                f"{DashboardState.total_rows:,}行 読み込み済み",
                font_size="0.75rem",
                color=ACCENT_4,
                margin_top="0.5rem"
            )
        ),
        width="100%",
        spacing="2"
    )


def prefecture_selector() -> rx.Component:
    """都道府県選択"""
    return rx.vstack(
        rx.text(
            "都道府県",
            font_weight="600",
            margin_bottom="0.5rem",
            font_size="0.9rem",
            color=MUTED_COLOR
        ),
        rx.select(
            DashboardState.prefectures,
            placeholder="都道府県を選択",
            value=DashboardState.selected_prefecture,
            on_change=DashboardState.set_prefecture,
            width="100%",
            color=TEXT_COLOR,
            bg=CARD_BG,
            border_color=BORDER_COLOR
        ),
        width="100%",
        spacing="0"
    )


def municipality_selector() -> rx.Component:
    """市区町村選択"""
    return rx.vstack(
        rx.text(
            "市区町村",
            font_weight="600",
            margin_bottom="0.5rem",
            font_size="0.9rem",
            color=MUTED_COLOR
        ),
        rx.select(
            DashboardState.municipalities,
            placeholder="市区町村を選択",
            value=DashboardState.selected_municipality,
            on_change=DashboardState.set_municipality,
            width="100%",
            color=TEXT_COLOR,
            bg=CARD_BG,
            border_color=BORDER_COLOR
        ),
        width="100%",
        spacing="0"
    )


def city_summary() -> rx.Component:
    """選択地域サマリー"""
    return rx.vstack(
        rx.heading(
            DashboardState.city_name,
            size="6",
            color=TEXT_COLOR,
            margin_bottom="0.25rem"
        ),
        rx.text(
            DashboardState.city_meta,
            font_size="0.85rem",
            color=MUTED_COLOR,
            margin_bottom="0.75rem"
        ),
        rx.box(
            DashboardState.quality_badge,
            padding="0.5rem 1rem",
            border_radius="6px",
            bg=CARD_BG,
            border=f"1px solid {BORDER_COLOR}",
            color=MUTED_COLOR,
            font_size="0.8rem"
        ),
        width="100%",
        align="start",
        spacing="0"
    )


def sidebar() -> rx.Component:
    """右サイドバー（440px、リサイズ可能）"""
    return rx.box(
        rx.vstack(
            sidebar_header(),
            csv_upload_section(),
            prefecture_selector(),
            municipality_selector(),
            city_summary(),
            width="100%",
            spacing="4",
            padding="1.5rem"
        ),
        width="440px",
        height="100vh",
        background=PANEL_BG,
        border_left=f"1px solid {BORDER_COLOR}",
        overflow_y="auto",
        position="fixed",
        right="0",
        top="0",
        box_shadow="-18px 0 40px rgba(10, 20, 40, 0.35)",
        style={
            "backdrop_filter": "blur(12px)",
            "-webkit-backdrop-filter": "blur(12px)"
        }
    )


def tab_button(tab: dict) -> rx.Component:
    """タブボタン"""
    is_active = DashboardState.active_tab == tab["id"]

    return rx.button(
        tab["label"],
        on_click=DashboardState.set_active_tab(tab["id"]),
        color=rx.cond(is_active, TEXT_COLOR, MUTED_COLOR),
        bg=rx.cond(is_active, PRIMARY_COLOR, "transparent"),
        border_radius="8px",
        padding="0.75rem 1.5rem",
        font_size="0.9rem",
        font_weight=rx.cond(is_active, "600", "400"),
        transition="all 0.2s",
        _hover={
            "bg": rx.cond(is_active, PRIMARY_COLOR, CARD_BG),
            "color": TEXT_COLOR
        }
    )


def tabbar() -> rx.Component:
    """タブバー（10個のタブ）"""
    return rx.hstack(
        *[tab_button(tab) for tab in TABS],
        width="100%",
        spacing="2",
        wrap="wrap",
        padding="1rem",
        border_bottom=f"1px solid {BORDER_COLOR}"
    )


def overview_age_gender_chart() -> rx.Component:
    """概要: 年齢×性別グラフ（Recharts）"""
    return rx.box(
        rx.recharts.bar_chart(
            rx.recharts.bar(
                data_key="男性",
                name="男性",
                stroke=ACCENT_7,
                fill=ACCENT_7,
            ),
            rx.recharts.bar(
                data_key="女性",
                name="女性",
                stroke=ACCENT_3,
                fill=ACCENT_3,
            ),
            rx.recharts.x_axis(data_key="name", stroke="#94a3b8"),
            rx.recharts.y_axis(stroke="#94a3b8"),
            rx.recharts.legend(),
            rx.recharts.graphing_tooltip(),
            data=DashboardState.overview_age_gender_data,
            width="100%",
            height=400,
        ),
        background=CARD_BG,
        border_radius="12px",
        border=f"1px solid {BORDER_COLOR}",
        padding="1.5rem",
        width="100%"
    )


def cross_age_employment_chart() -> rx.Component:
    """クロス: 年齢×就業状態グラフ（積み上げ棒グラフ）"""
    return rx.box(
        rx.recharts.bar_chart(
            rx.recharts.bar(
                data_key="就業中",
                name="就業中",
                stack_id="employment",
                stroke=SECONDARY_COLOR,
                fill=SECONDARY_COLOR,
            ),
            rx.recharts.bar(
                data_key="離職中",
                name="離職中",
                stack_id="employment",
                stroke=ACCENT_6,
                fill=ACCENT_6,
            ),
            rx.recharts.bar(
                data_key="在学中",
                name="在学中",
                stack_id="employment",
                stroke=ACCENT_4,
                fill=ACCENT_4,
            ),
            rx.recharts.x_axis(data_key="age", stroke="#94a3b8"),
            rx.recharts.y_axis(stroke="#94a3b8"),
            rx.recharts.legend(),
            rx.recharts.graphing_tooltip(),
            data=DashboardState.cross_age_employment_data,
            width="100%",
            height=400
        ),
        background=CARD_BG,
        border_radius="12px",
        border=f"1px solid {BORDER_COLOR}",
        padding="1.5rem",
        width="100%"
    )


def cross_gender_employment_chart() -> rx.Component:
    """クロス: 性別×就業状態グラフ（積み上げ棒グラフ）"""
    return rx.box(
        rx.recharts.bar_chart(
            rx.recharts.bar(
                data_key="就業中",
                name="就業中",
                stack_id="employment",
                stroke=SECONDARY_COLOR,
                fill=SECONDARY_COLOR,
            ),
            rx.recharts.bar(
                data_key="離職中",
                name="離職中",
                stack_id="employment",
                stroke=ACCENT_6,
                fill=ACCENT_6,
            ),
            rx.recharts.bar(
                data_key="在学中",
                name="在学中",
                stack_id="employment",
                stroke=ACCENT_4,
                fill=ACCENT_4,
            ),
            rx.recharts.x_axis(data_key="gender", stroke="#94a3b8"),
            rx.recharts.y_axis(stroke="#94a3b8"),
            rx.recharts.legend(),
            rx.recharts.graphing_tooltip(),
            data=DashboardState.cross_gender_employment_data,
            width="100%",
            height=350
        ),
        background=CARD_BG,
        border_radius="12px",
        border=f"1px solid {BORDER_COLOR}",
        padding="1.5rem",
        width="100%"
    )


def cross_age_qualification_chart() -> rx.Component:
    """クロス: 年齢×資格保有グラフ（複合: 折れ線2本、デュアルY軸）"""
    return rx.box(
        rx.recharts.composed_chart(
            rx.recharts.line(
                data_key="avg_qual",
                name="平均資格数",
                y_axis_id="left",
                stroke=PRIMARY_COLOR,
                type_="monotone",
            ),
            rx.recharts.line(
                data_key="national_rate",
                name="国家資格保有率(%)",
                y_axis_id="right",
                stroke=ACCENT_5,
                type_="monotone",
            ),
            rx.recharts.x_axis(data_key="age", stroke="#94a3b8"),
            rx.recharts.y_axis(
                y_axis_id="left",
                stroke="#94a3b8",
                label={"value": "平均資格数", "angle": -90, "position": "insideLeft", "style": {"fill": "#94a3b8", "fontSize": 12}}
            ),
            rx.recharts.y_axis(
                y_axis_id="right",
                orientation="right",
                stroke="#94a3b8",
                label={"value": "国家資格保有率(%)", "angle": 90, "position": "insideRight", "style": {"fill": "#94a3b8", "fontSize": 12}}
            ),
            rx.recharts.legend(),
            rx.recharts.graphing_tooltip(),
            data=DashboardState.cross_age_qualification_data,
            width="100%",
            height=400
        ),
        background=CARD_BG,
        border_radius="12px",
        border=f"1px solid {BORDER_COLOR}",
        padding="1.5rem",
        width="100%"
    )


def cross_employment_qualification_chart() -> rx.Component:
    """クロス: 就業状態×資格保有グラフ（複合: 棒+折れ線、デュアルY軸）"""
    return rx.box(
        rx.recharts.composed_chart(
            rx.recharts.bar(
                data_key="avg_qual",
                name="平均資格数",
                y_axis_id="left",
                stroke=PRIMARY_COLOR,
                fill=PRIMARY_COLOR,
            ),
            rx.recharts.line(
                data_key="national_rate",
                name="国家資格保有率(%)",
                y_axis_id="right",
                stroke=ACCENT_5,
                type_="monotone",
            ),
            rx.recharts.x_axis(data_key="employment", stroke="#94a3b8"),
            rx.recharts.y_axis(
                y_axis_id="left",
                stroke="#94a3b8",
                label={"value": "平均資格数", "angle": -90, "position": "insideLeft", "style": {"fill": "#94a3b8", "fontSize": 12}}
            ),
            rx.recharts.y_axis(
                y_axis_id="right",
                orientation="right",
                stroke="#94a3b8",
                label={"value": "国家資格保有率(%)", "angle": 90, "position": "insideRight", "style": {"fill": "#94a3b8", "fontSize": 12}}
            ),
            rx.recharts.legend(),
            rx.recharts.graphing_tooltip(),
            data=DashboardState.cross_employment_qualification_data,
            width="100%",
            height=350
        ),
        background=CARD_BG,
        border_radius="12px",
        border=f"1px solid {BORDER_COLOR}",
        padding="1.5rem",
        width="100%"
    )


def cross_persona_qualification_age_chart() -> rx.Component:
    """クロス6: ペルソナ×資格×年齢 - 希少人材バブルチャート"""
    return rx.box(
        rx.recharts.scatter_chart(
            rx.recharts.scatter(
                data=DashboardState.cross_persona_qualification_age_data,
                fill=ACCENT_3,
                name="希少人材",
            ),
            rx.recharts.x_axis(
                data_key="avg_qual",
                type_="number",
                stroke="#94a3b8",
                label={"value": "平均資格数", "position": "insideBottom", "offset": -10, "style": {"fill": "#94a3b8", "fontSize": 12}}
            ),
            rx.recharts.y_axis(
                data_key="rarity_score",
                type_="number",
                stroke="#94a3b8",
                label={"value": "希少度スコア", "angle": -90, "position": "insideLeft", "style": {"fill": "#94a3b8", "fontSize": 12}}
            ),
            rx.recharts.z_axis(data_key="count", type_="number", range=[50, 500], name="人数"),
            rx.recharts.graphing_tooltip(),
            rx.recharts.legend(),
            width="100%",
            height=450
        ),
        background=CARD_BG,
        border_radius="12px",
        border=f"1px solid {BORDER_COLOR}",
        padding="1.5rem",
        width="100%"
    )


def cross_distance_age_gender_chart() -> rx.Component:
    """クロス7: 移動距離×年齢×性別 - 地域採用戦略グラフ"""
    return rx.box(
        rx.recharts.bar_chart(
            rx.recharts.bar(
                data_key="mobility_score",
                name="移動許容度スコア",
                stack_id="gender",
                stroke=PRIMARY_COLOR,
                fill=PRIMARY_COLOR,
            ),
            rx.recharts.x_axis(data_key="age", stroke="#94a3b8"),
            rx.recharts.y_axis(stroke="#94a3b8"),
            rx.recharts.legend(),
            rx.recharts.graphing_tooltip(),
            data=DashboardState.cross_distance_age_gender_data,
            width="100%",
            height=400,
            bar_size=30
        ),
        background=CARD_BG,
        border_radius="12px",
        border=f"1px solid {BORDER_COLOR}",
        padding="1.5rem",
        width="100%"
    )


def cross_urgency_career_age_chart() -> rx.Component:
    """クロス8: 転職意欲×キャリア×年齢 - ターゲティングヒートマップ"""
    return rx.box(
        rx.recharts.bar_chart(
            rx.recharts.bar(
                data_key="avg_urgency",
                name="平均転職意欲",
                stroke=ACCENT_6,
                fill=ACCENT_6,
            ),
            rx.recharts.bar(
                data_key="avg_qual",
                name="平均資格数",
                stroke=SECONDARY_COLOR,
                fill=SECONDARY_COLOR,
            ),
            rx.recharts.x_axis(data_key="age", stroke="#94a3b8"),
            rx.recharts.y_axis(stroke="#94a3b8"),
            rx.recharts.legend(),
            rx.recharts.graphing_tooltip(),
            data=DashboardState.cross_urgency_career_age_data,
            width="100%",
            height=400,
            bar_size=30
        ),
        background=CARD_BG,
        border_radius="12px",
        border=f"1px solid {BORDER_COLOR}",
        padding="1.5rem",
        width="100%"
    )


def cross_supply_demand_region_chart() -> rx.Component:
    """クロス9: 供給密度×需要バランス×地域 - 競争環境散布図"""
    return rx.box(
        rx.recharts.scatter_chart(
            rx.recharts.scatter(
                data=DashboardState.cross_supply_demand_region_data,
                fill=ACCENT_4,
                name="地域競争度",
            ),
            rx.recharts.x_axis(
                data_key="supply_density",
                type_="number",
                stroke="#94a3b8",
                label={"value": "供給密度", "position": "insideBottom", "offset": -10, "style": {"fill": "#94a3b8", "fontSize": 12}}
            ),
            rx.recharts.y_axis(
                data_key="demand_ratio",
                type_="number",
                stroke="#94a3b8",
                label={"value": "需要比率", "angle": -90, "position": "insideLeft", "style": {"fill": "#94a3b8", "fontSize": 12}}
            ),
            rx.recharts.z_axis(data_key="gap_score", type_="number", range=[50, 500], name="ギャップ"),
            rx.recharts.graphing_tooltip(),
            rx.recharts.legend(),
            width="100%",
            height=450
        ),
        background=CARD_BG,
        border_radius="12px",
        border=f"1px solid {BORDER_COLOR}",
        padding="1.5rem",
        width="100%"
    )


def cross_multidimensional_profile_chart() -> rx.Component:
    """クロス10: 多次元プロファイル - レーダーチャート"""
    return rx.box(
        rx.recharts.radar_chart(
            rx.recharts.radar(
                data_key="urgency",
                name="転職意欲",
                stroke=SECONDARY_COLOR,
                fill=SECONDARY_COLOR,
                fill_opacity=0.6,
            ),
            rx.recharts.radar(
                data_key="qualification",
                name="資格保有数",
                stroke=PRIMARY_COLOR,
                fill=PRIMARY_COLOR,
                fill_opacity=0.6,
            ),
            rx.recharts.radar(
                data_key="mobility",
                name="移動許容度",
                stroke=ACCENT_4,
                fill=ACCENT_4,
                fill_opacity=0.6,
            ),
            rx.recharts.polar_grid(),
            rx.recharts.polar_angle_axis(data_key="persona"),
            rx.recharts.polar_radius_axis(),
            rx.recharts.legend(),
            data=DashboardState.cross_multidimensional_profile_data,
            width="100%",
            height=500
        ),
        background=CARD_BG,
        border_radius="12px",
        border=f"1px solid {BORDER_COLOR}",
        padding="1.5rem",
        width="100%"
    )


def supply_qualification_chart() -> rx.Component:
    """供給: 資格バケット分布グラフ（Recharts）"""
    return rx.box(
        rx.recharts.bar_chart(
            rx.recharts.bar(
                data_key="count",
                name="人数",
                stroke="#8b5cf6",
                fill="#8b5cf6",
            ),
            rx.recharts.x_axis(data_key="name", stroke="#94a3b8"),
            rx.recharts.y_axis(stroke="#94a3b8"),
            rx.recharts.graphing_tooltip(),
            data=DashboardState.supply_qualification_buckets_data,
            width="100%",
            height=350,
        ),
        background=CARD_BG,
        border_radius="12px",
        border=f"1px solid {BORDER_COLOR}",
        padding="1.5rem",
        width="100%"
    )


# =====================================
# 追加グラフコンポーネント (13個)
# =====================================

# 1. Overview パネル用 (2個)

def overview_gender_chart() -> rx.Component:
    """概要: 性別構成ドーナツチャート

    GAS参照: map_complete_integrated.html Line 2497-2501
    """
    return rx.box(
        rx.recharts.pie_chart(
            rx.recharts.pie(
                data=DashboardState.overview_gender_data,
                data_key="value",
                name_key="name",
                cx="50%",
                cy="50%",
                label=True
            ),
            rx.recharts.legend(),
            rx.recharts.graphing_tooltip(),
            width="100%",
            height=400
        ),
        background=CARD_BG,
        border_radius="12px",
        border=f"1px solid {BORDER_COLOR}",
        padding="1.5rem",
        width="100%"
    )


def overview_age_chart() -> rx.Component:
    """概要: 年齢帯別棒グラフ

    GAS参照: Line 2505-2509
    """
    return rx.box(
        rx.recharts.bar_chart(
            rx.recharts.bar(
                data_key="count",
                name="人数",
                stroke=PRIMARY_COLOR,
                fill=PRIMARY_COLOR,
            ),
            rx.recharts.x_axis(data_key="name", stroke="#94a3b8"),
            rx.recharts.y_axis(stroke="#94a3b8"),
            rx.recharts.graphing_tooltip(),
            data=DashboardState.overview_age_data,
            width="100%",
            height=400
        ),
        background=CARD_BG,
        border_radius="12px",
        border=f"1px solid {BORDER_COLOR}",
        padding="1.5rem",
        width="100%"
    )


# 2. Supply パネル用 (3個)

def supply_status_chart() -> rx.Component:
    """供給: 就業ステータス棒グラフ

    GAS参照: Line 2546-2550
    """
    return rx.box(
        rx.recharts.bar_chart(
            rx.recharts.bar(
                data_key="count",
                name="人数",
                stroke=ACCENT_4,
                fill=ACCENT_4,
            ),
            rx.recharts.x_axis(data_key="name", stroke="#94a3b8"),
            rx.recharts.y_axis(stroke="#94a3b8"),
            rx.recharts.graphing_tooltip(),
            data=DashboardState.supply_status_data,
            width="100%",
            height=350
        ),
        background=CARD_BG,
        border_radius="12px",
        border=f"1px solid {BORDER_COLOR}",
        padding="1.5rem",
        width="100%"
    )


def supply_qualification_doughnut_chart() -> rx.Component:
    """供給: 保有資格ドーナツチャート

    GAS参照: Line 2554-2558
    """
    return rx.box(
        rx.recharts.pie_chart(
            rx.recharts.pie(
                data=DashboardState.supply_qualification_buckets_data,
                data_key="count",
                name_key="name",
                cx="50%",
                cy="50%",
                label=True
            ),
            rx.recharts.legend(),
            rx.recharts.graphing_tooltip(),
            width="100%",
            height=350
        ),
        background=CARD_BG,
        border_radius="12px",
        border=f"1px solid {BORDER_COLOR}",
        padding="1.5rem",
        width="100%"
    )


def supply_persona_qual_chart() -> rx.Component:
    """供給: ペルソナ別平均資格数（横棒グラフ）

    GAS参照: Line 2563-2567
    """
    return rx.box(
        rx.recharts.bar_chart(
            rx.recharts.bar(
                data_key="avg_qual",
                name="平均資格数",
                stroke=ACCENT_3,
                fill=ACCENT_3,
            ),
            rx.recharts.x_axis(
                type_="number",
                stroke="#94a3b8",
                label={"value": "平均資格数", "position": "insideBottom", "offset": -10, "style": {"fill": "#94a3b8", "fontSize": 12}}
            ),
            rx.recharts.y_axis(
                data_key="name",
                type_="category",
                stroke="#94a3b8",
                label={"value": "ペルソナ", "angle": -90, "position": "insideLeft", "style": {"fill": "#94a3b8", "fontSize": 12}}
            ),
            rx.recharts.graphing_tooltip(),
            data=DashboardState.supply_persona_qual_data,
            layout="vertical",
            width="100%",
            height=400
        ),
        background=CARD_BG,
        border_radius="12px",
        border=f"1px solid {BORDER_COLOR}",
        padding="1.5rem",
        width="100%"
    )


# === フロー分析タブ用横棒グラフ（3個） ===

def flow_inflow_ranking_chart() -> rx.Component:
    """フロー: 流入ランキング Top 10（横棒グラフ）"""
    return rx.box(
        rx.vstack(
            rx.heading("流入ランキング Top 10", size="4", color=TEXT_COLOR, margin_bottom="1rem"),
            rx.text("他地域から希望する人が多い市区町村", color=MUTED_COLOR, font_size="0.85rem", margin_bottom="1rem"),
            rx.recharts.bar_chart(
                rx.recharts.bar(
                    data_key="value",
                    name="流入人数",
                    stroke=PRIMARY_COLOR,
                    fill=PRIMARY_COLOR,
                    radius=[0, 8, 8, 0],
                ),
                rx.recharts.x_axis(
                    type_="number",
                    stroke="#94a3b8",
                    label={"value": "人数（人）", "position": "insideBottom", "offset": -10, "style": {"fill": "#94a3b8", "fontSize": 12}}
                ),
                rx.recharts.y_axis(
                    data_key="name",
                    type_="category",
                    width=120,
                    stroke="#94a3b8",
                    label={"value": "市区町村", "angle": -90, "position": "insideLeft", "style": {"fill": "#94a3b8", "fontSize": 12}}
                ),
                rx.recharts.graphing_tooltip(),
                data=DashboardState.flow_inflow_ranking,
                layout="vertical",
                width="100%",
                height=400,
                bar_size=25,
            ),
            width="100%", spacing="2"
        ),
        background=CARD_BG,
        border_radius="12px",
        border=f"1px solid {BORDER_COLOR}",
        padding="1.5rem",
        margin_top="2rem",
        width="100%"
    )


def flow_outflow_ranking_chart() -> rx.Component:
    """フロー: 流出ランキング Top 10（横棒グラフ）"""
    return rx.box(
        rx.vstack(
            rx.heading("流出ランキング Top 10", size="4", color=TEXT_COLOR, margin_bottom="1rem"),
            rx.text("他地域へ希望する人が多い市区町村", color=MUTED_COLOR, font_size="0.85rem", margin_bottom="1rem"),
            rx.recharts.bar_chart(
                rx.recharts.bar(
                    data_key="value",
                    name="流出人数",
                    stroke=SECONDARY_COLOR,
                    fill=SECONDARY_COLOR,
                    radius=[0, 8, 8, 0],
                ),
                rx.recharts.x_axis(
                    type_="number",
                    stroke="#94a3b8",
                    label={"value": "人数（人）", "position": "insideBottom", "offset": -10, "style": {"fill": "#94a3b8", "fontSize": 12}}
                ),
                rx.recharts.y_axis(
                    data_key="name",
                    type_="category",
                    width=120,
                    stroke="#94a3b8",
                    label={"value": "市区町村", "angle": -90, "position": "insideLeft", "style": {"fill": "#94a3b8", "fontSize": 12}}
                ),
                rx.recharts.graphing_tooltip(),
                data=DashboardState.flow_outflow_ranking,
                layout="vertical",
                width="100%",
                height=400,
                bar_size=25,
            ),
            width="100%", spacing="2"
        ),
        background=CARD_BG,
        border_radius="12px",
        border=f"1px solid {BORDER_COLOR}",
        padding="1.5rem",
        margin_top="2rem",
        width="100%"
    )


def flow_netflow_ranking_chart() -> rx.Component:
    """フロー: 純流入ランキング Top 10（横棒グラフ）"""
    return rx.box(
        rx.vstack(
            rx.heading("純流入ランキング Top 10", size="4", color=TEXT_COLOR, margin_bottom="1rem"),
            rx.text("流入超過（人気）が高い市区町村", color=MUTED_COLOR, font_size="0.85rem", margin_bottom="1rem"),
            rx.recharts.bar_chart(
                rx.recharts.bar(
                    data_key="value",
                    name="純流入",
                    stroke=SUCCESS_COLOR,
                    fill=SUCCESS_COLOR,
                    radius=[0, 8, 8, 0],
                ),
                rx.recharts.x_axis(
                    type_="number",
                    stroke="#94a3b8",
                    label={"value": "人数（人）", "position": "insideBottom", "offset": -10, "style": {"fill": "#94a3b8", "fontSize": 12}}
                ),
                rx.recharts.y_axis(
                    data_key="name",
                    type_="category",
                    width=120,
                    stroke="#94a3b8",
                    label={"value": "市区町村", "angle": -90, "position": "insideLeft", "style": {"fill": "#94a3b8", "fontSize": 12}}
                ),
                rx.recharts.graphing_tooltip(),
                data=DashboardState.flow_netflow_ranking,
                layout="vertical",
                width="100%",
                height=400,
                bar_size=25,
            ),
            width="100%", spacing="2"
        ),
        background=CARD_BG,
        border_radius="12px",
        border=f"1px solid {BORDER_COLOR}",
        padding="1.5rem",
        margin_top="2rem",
        width="100%"
    )


# === 需給バランスタブ用横棒グラフ（3個） ===

def gap_shortage_ranking_chart() -> rx.Component:
    """需給: 需要超過ランキング Top 10（横棒グラフ）"""
    return rx.box(
        rx.vstack(
            rx.heading("需要超過ランキング Top 10", size="4", color=TEXT_COLOR, margin_bottom="1rem"),
            rx.text("求人数が希望者数を上回る市区町村（人材不足）", color=MUTED_COLOR, font_size="0.85rem", margin_bottom="1rem"),
            rx.recharts.bar_chart(
                rx.recharts.bar(
                    data_key="value",
                    name="需要超過",
                    stroke=WARNING_COLOR,
                    fill=WARNING_COLOR,
                    radius=[0, 8, 8, 0],
                ),
                rx.recharts.x_axis(
                    type_="number",
                    stroke="#94a3b8",
                    label={"value": "需要超過（人）", "position": "insideBottom", "offset": -10, "style": {"fill": "#94a3b8", "fontSize": 12}}
                ),
                rx.recharts.y_axis(
                    data_key="name",
                    type_="category",
                    width=120,
                    stroke="#94a3b8",
                    label={"value": "市区町村", "angle": -90, "position": "insideLeft", "style": {"fill": "#94a3b8", "fontSize": 12}}
                ),
                rx.recharts.graphing_tooltip(),
                data=DashboardState.gap_shortage_ranking,
                layout="vertical",
                width="100%",
                height=400,
                bar_size=25,
            ),
            width="100%", spacing="2"
        ),
        background=CARD_BG,
        border_radius="12px",
        border=f"1px solid {BORDER_COLOR}",
        padding="1.5rem",
        margin_top="2rem",
        width="100%"
    )


def gap_surplus_ranking_chart() -> rx.Component:
    """需給: 供給超過ランキング Top 10（横棒グラフ）"""
    return rx.box(
        rx.vstack(
            rx.heading("供給超過ランキング Top 10", size="4", color=TEXT_COLOR, margin_bottom="1rem"),
            rx.text("希望者数が求人数を上回る市区町村（人材余剰）", color=MUTED_COLOR, font_size="0.85rem", margin_bottom="1rem"),
            rx.recharts.bar_chart(
                rx.recharts.bar(
                    data_key="value",
                    name="供給超過",
                    stroke=SUCCESS_COLOR,
                    fill=SUCCESS_COLOR,
                    radius=[0, 8, 8, 0],
                ),
                rx.recharts.x_axis(
                    type_="number",
                    stroke="#94a3b8",
                    label={"value": "供給超過（人）", "position": "insideBottom", "offset": -10, "style": {"fill": "#94a3b8", "fontSize": 12}}
                ),
                rx.recharts.y_axis(
                    data_key="name",
                    type_="category",
                    width=120,
                    stroke="#94a3b8",
                    label={"value": "市区町村", "angle": -90, "position": "insideLeft", "style": {"fill": "#94a3b8", "fontSize": 12}}
                ),
                rx.recharts.graphing_tooltip(),
                data=DashboardState.gap_surplus_ranking,
                layout="vertical",
                width="100%",
                height=400,
                bar_size=25,
            ),
            width="100%", spacing="2"
        ),
        background=CARD_BG,
        border_radius="12px",
        border=f"1px solid {BORDER_COLOR}",
        padding="1.5rem",
        margin_top="2rem",
        width="100%"
    )


def gap_ratio_ranking_chart() -> rx.Component:
    """需給: 需給比率ランキング Top 10（横棒グラフ）"""
    return rx.box(
        rx.vstack(
            rx.heading("需給比率ランキング Top 10", size="4", color=TEXT_COLOR, margin_bottom="1rem"),
            rx.text("需要/供給の比率が高い市区町村（採用競争激化）", color=MUTED_COLOR, font_size="0.85rem", margin_bottom="1rem"),
            rx.recharts.bar_chart(
                rx.recharts.bar(
                    data_key="value",
                    name="需給比率",
                    stroke=ACCENT_5,
                    fill=ACCENT_5,
                    radius=[0, 8, 8, 0],
                ),
                rx.recharts.x_axis(
                    type_="number",
                    stroke="#94a3b8",
                    label={"value": "需給比率", "position": "insideBottom", "offset": -10, "style": {"fill": "#94a3b8", "fontSize": 12}}
                ),
                rx.recharts.y_axis(
                    data_key="name",
                    type_="category",
                    width=120,
                    stroke="#94a3b8",
                    label={"value": "市区町村", "angle": -90, "position": "insideLeft", "style": {"fill": "#94a3b8", "fontSize": 12}}
                ),
                rx.recharts.graphing_tooltip(),
                data=DashboardState.gap_ratio_ranking,
                layout="vertical",
                width="100%",
                height=400,
                bar_size=25,
            ),
            width="100%", spacing="2"
        ),
        background=CARD_BG,
        border_radius="12px",
        border=f"1px solid {BORDER_COLOR}",
        padding="1.5rem",
        margin_top="2rem",
        width="100%"
    )


# === 希少人材タブ用横棒グラフ（1個） ===

def rarity_national_license_ranking_chart() -> rx.Component:
    """希少性: 国家資格保有者ランキング Top 10（横棒グラフ）"""
    return rx.box(
        rx.vstack(
            rx.heading("国家資格保有者ランキング Top 10", size="4", color=TEXT_COLOR, margin_bottom="1rem"),
            rx.text("希少性スコアが高い国家資格保有者", color=MUTED_COLOR, font_size="0.85rem", margin_bottom="1rem"),
            rx.recharts.bar_chart(
                rx.recharts.bar(
                    data_key="value",
                    name="希少性スコア",
                    stroke=ACCENT_3,
                    fill=ACCENT_3,
                    radius=[0, 8, 8, 0],
                ),
                rx.recharts.x_axis(
                    type_="number",
                    stroke="#94a3b8",
                    label={"value": "希少性スコア", "position": "insideBottom", "offset": -10, "style": {"fill": "#94a3b8", "fontSize": 12}}
                ),
                rx.recharts.y_axis(
                    data_key="name",
                    type_="category",
                    width=200,
                    stroke="#94a3b8",
                    label={"value": "資格・職種", "angle": -90, "position": "insideLeft", "style": {"fill": "#94a3b8", "fontSize": 12}}
                ),
                rx.recharts.graphing_tooltip(),
                data=DashboardState.rarity_national_license_ranking,
                layout="vertical",
                width="100%",
                height=400,
                bar_size=25,
            ),
            width="100%", spacing="2"
        ),
        background=CARD_BG,
        border_radius="12px",
        border=f"1px solid {BORDER_COLOR}",
        padding="1.5rem",
        margin_top="2rem",
        width="100%"
    )


# === 人材プロファイルタブ用横棒グラフ（3個） ===

def competition_national_license_ranking_chart() -> rx.Component:
    """競合: 国家資格保有率ランキング Top 10（横棒グラフ）"""
    return rx.box(
        rx.vstack(
            rx.heading("国家資格保有率ランキング Top 10", size="4", color=TEXT_COLOR, margin_bottom="1rem"),
            rx.text("国家資格保有率が高いペルソナ", color=MUTED_COLOR, font_size="0.85rem", margin_bottom="1rem"),
            rx.recharts.bar_chart(
                rx.recharts.bar(
                    data_key="value",
                    name="国家資格保有率",
                    stroke=ACCENT_7,
                    fill=ACCENT_7,
                    radius=[0, 8, 8, 0],
                ),
                rx.recharts.x_axis(
                    type_="number",
                    stroke="#94a3b8",
                    label={"value": "国家資格保有率（%）", "position": "insideBottom", "offset": -10, "style": {"fill": "#94a3b8", "fontSize": 12}}
                ),
                rx.recharts.y_axis(
                    data_key="name",
                    type_="category",
                    width=150,
                    stroke="#94a3b8",
                    label={"value": "ペルソナ", "angle": -90, "position": "insideLeft", "style": {"fill": "#94a3b8", "fontSize": 12}}
                ),
                rx.recharts.graphing_tooltip(),
                data=DashboardState.competition_national_license_ranking,
                layout="vertical",
                width="100%",
                height=400,
                bar_size=25,
            ),
            width="100%", spacing="2"
        ),
        background=CARD_BG,
        border_radius="12px",
        border=f"1px solid {BORDER_COLOR}",
        padding="1.5rem",
        margin_top="2rem",
        width="100%"
    )


def competition_qualification_ranking_chart() -> rx.Component:
    """競合: 資格保有数ランキング Top 10（横棒グラフ）"""
    return rx.box(
        rx.vstack(
            rx.heading("資格保有数ランキング Top 10", size="4", color=TEXT_COLOR, margin_bottom="1rem"),
            rx.text("平均資格保有数が多いペルソナ", color=MUTED_COLOR, font_size="0.85rem", margin_bottom="1rem"),
            rx.recharts.bar_chart(
                rx.recharts.bar(
                    data_key="value",
                    name="平均資格数",
                    stroke=ACCENT_3,
                    fill=ACCENT_3,
                    radius=[0, 8, 8, 0],
                ),
                rx.recharts.x_axis(
                    type_="number",
                    stroke="#94a3b8",
                    label={"value": "平均資格数", "position": "insideBottom", "offset": -10, "style": {"fill": "#94a3b8", "fontSize": 12}}
                ),
                rx.recharts.y_axis(
                    data_key="name",
                    type_="category",
                    width=150,
                    stroke="#94a3b8",
                    label={"value": "ペルソナ", "angle": -90, "position": "insideLeft", "style": {"fill": "#94a3b8", "fontSize": 12}}
                ),
                rx.recharts.graphing_tooltip(),
                data=DashboardState.competition_qualification_ranking,
                layout="vertical",
                width="100%",
                height=400,
                bar_size=25,
            ),
            width="100%", spacing="2"
        ),
        background=CARD_BG,
        border_radius="12px",
        border=f"1px solid {BORDER_COLOR}",
        padding="1.5rem",
        margin_top="2rem",
        width="100%"
    )


def competition_female_ratio_ranking_chart() -> rx.Component:
    """競合: 女性比率ランキング Top 10（横棒グラフ）"""
    return rx.box(
        rx.vstack(
            rx.heading("女性比率ランキング Top 10", size="4", color=TEXT_COLOR, margin_bottom="1rem"),
            rx.text("女性比率が高いペルソナ", color=MUTED_COLOR, font_size="0.85rem", margin_bottom="1rem"),
            rx.recharts.bar_chart(
                rx.recharts.bar(
                    data_key="value",
                    name="女性比率",
                    stroke=ACCENT_7,
                    fill=ACCENT_7,
                    radius=[0, 8, 8, 0],
                ),
                rx.recharts.x_axis(
                    type_="number",
                    stroke="#94a3b8",
                    label={"value": "女性比率（%）", "position": "insideBottom", "offset": -10, "style": {"fill": "#94a3b8", "fontSize": 12}}
                ),
                rx.recharts.y_axis(
                    data_key="name",
                    type_="category",
                    width=150,
                    stroke="#94a3b8",
                    label={"value": "ペルソナ", "angle": -90, "position": "insideLeft", "style": {"fill": "#94a3b8", "fontSize": 12}}
                ),
                rx.recharts.graphing_tooltip(),
                data=DashboardState.competition_female_ratio_ranking,
                layout="vertical",
                width="100%",
                height=400,
                bar_size=25,
            ),
            width="100%", spacing="2"
        ),
        background=CARD_BG,
        border_radius="12px",
        border=f"1px solid {BORDER_COLOR}",
        padding="1.5rem",
        margin_top="2rem",
        width="100%"
    )


# 3. Career パネル用 (1個)

def career_employment_age_chart() -> rx.Component:
    """キャリア: 就業ステータス×年齢帯（積み上げ棒グラフ）

    GAS参照: Line 2587-2588
    """
    return rx.box(
        rx.recharts.bar_chart(
            rx.recharts.bar(
                data_key="就業中",
                name="就業中",
                stack_id="stack1",
                stroke=ACCENT_4,
                fill=ACCENT_4,
            ),
            rx.recharts.bar(
                data_key="離職中",
                name="離職中",
                stack_id="stack1",
                stroke=SECONDARY_COLOR,
                fill=SECONDARY_COLOR,
            ),
            rx.recharts.bar(
                data_key="在学中",
                name="在学中",
                stack_id="stack1",
                stroke=PRIMARY_COLOR,
                fill=PRIMARY_COLOR,
            ),
            rx.recharts.x_axis(data_key="age", stroke="#94a3b8"),
            rx.recharts.y_axis(stroke="#94a3b8"),
            rx.recharts.legend(),
            rx.recharts.graphing_tooltip(),
            data=DashboardState.career_employment_age_data,
            width="100%",
            height=400
        ),
        background=CARD_BG,
        border_radius="12px",
        border=f"1px solid {BORDER_COLOR}",
        padding="1.5rem",
        width="100%"
    )


# 4. Urgency パネル用 (2個)

def urgency_age_chart() -> rx.Component:
    """緊急度: 年齢帯別（複合: 棒+折れ線、2軸）

    GAS参照: Line 2608-2618
    """
    return rx.box(
        rx.recharts.composed_chart(
            rx.recharts.bar(
                data_key="count",
                name="人数",
                y_axis_id="left",
                stroke=PRIMARY_COLOR,
                fill=PRIMARY_COLOR,
            ),
            rx.recharts.line(
                data_key="avg_score",
                name="平均スコア",
                y_axis_id="right",
                stroke=SECONDARY_COLOR,
                type_="monotone",
            ),
            rx.recharts.x_axis(data_key="age", stroke="#94a3b8"),
            rx.recharts.y_axis(y_axis_id="left", stroke="#94a3b8"),
            rx.recharts.y_axis(y_axis_id="right", orientation="right", stroke="#94a3b8"),
            rx.recharts.legend(),
            rx.recharts.graphing_tooltip(),
            data=DashboardState.urgency_age_data,
            width="100%",
            height=400
        ),
        background=CARD_BG,
        border_radius="12px",
        border=f"1px solid {BORDER_COLOR}",
        padding="1.5rem",
        width="100%"
    )


def urgency_employment_chart() -> rx.Component:
    """緊急度: 就業ステータス別（複合: 棒+折れ線、2軸）

    GAS参照: Line 2621-2630
    """
    return rx.box(
        rx.recharts.composed_chart(
            rx.recharts.bar(
                data_key="count",
                name="人数",
                y_axis_id="left",
                stroke=ACCENT_4,
                fill=ACCENT_4,
            ),
            rx.recharts.line(
                data_key="avg_score",
                name="平均スコア",
                y_axis_id="right",
                stroke=ACCENT_6,
                type_="monotone",
            ),
            rx.recharts.x_axis(data_key="status", stroke="#94a3b8"),
            rx.recharts.y_axis(y_axis_id="left", stroke="#94a3b8"),
            rx.recharts.y_axis(y_axis_id="right", orientation="right", stroke="#94a3b8"),
            rx.recharts.legend(),
            rx.recharts.graphing_tooltip(),
            data=DashboardState.urgency_employment_data,
            width="100%",
            height=400
        ),
        background=CARD_BG,
        border_radius="12px",
        border=f"1px solid {BORDER_COLOR}",
        padding="1.5rem",
        width="100%"
    )


# 5. Persona パネル用 (4個)

def persona_share_chart() -> rx.Component:
    """ペルソナ: 構成比ドーナツチャート

    GAS参照: Line 2721-2725
    """
    return rx.box(
        rx.recharts.pie_chart(
            rx.recharts.pie(
                data=DashboardState.persona_share_data,
                data_key="value",
                name_key="name",
                cx="50%",
                cy="50%",
                label=True
            ),
            rx.recharts.legend(),
            rx.recharts.graphing_tooltip(),
            width="100%",
            height=400
        ),
        background=CARD_BG,
        border_radius="12px",
        border=f"1px solid {BORDER_COLOR}",
        padding="1.5rem",
        width="100%"
    )


def persona_bar_chart() -> rx.Component:
    """ペルソナ: 人数別横棒グラフ（上位15件）"""
    return rx.box(
        rx.recharts.bar_chart(
            rx.recharts.bar(
                data_key="count",
                name="人数",
                stroke=PRIMARY_COLOR,
                fill=PRIMARY_COLOR,
                radius=[0, 8, 8, 0],  # 右端を丸める
            ),
            rx.recharts.x_axis(
                type_="number",
                stroke="#94a3b8",
                label={"value": "人数（人）", "position": "insideBottom", "offset": -10, "style": {"fill": "#94a3b8", "fontSize": 12}}
            ),
            rx.recharts.y_axis(
                data_key="name",
                type_="category",
                width=180,
                stroke="#94a3b8",
                label={"value": "ペルソナ", "angle": -90, "position": "insideLeft", "style": {"fill": "#94a3b8", "fontSize": 12}}
            ),
            rx.recharts.graphing_tooltip(),
            data=DashboardState.persona_bar_data,
            layout="vertical",
            width="100%",
            height=500,
            bar_size=25,  # バーの太さを保証
        ),
        background=CARD_BG,
        border_radius="12px",
        border=f"1px solid {BORDER_COLOR}",
        padding="1.5rem",
        width="100%"
    )


def persona_employment_breakdown_chart() -> rx.Component:
    """ペルソナ: 就業状態別積み上げ棒グラフ（上位10件）"""
    return rx.box(
        rx.recharts.bar_chart(
            rx.recharts.bar(
                data_key="就業中",
                name="就業中",
                stack_id="employment",
                stroke=SECONDARY_COLOR,
                fill=SECONDARY_COLOR,
                radius=[0, 0, 0, 0],  # 下層は角なし
            ),
            rx.recharts.bar(
                data_key="離職中",
                name="離職中",
                stack_id="employment",
                stroke=ACCENT_6,
                fill=ACCENT_6,
                radius=[0, 0, 0, 0],  # 中層は角なし
            ),
            rx.recharts.bar(
                data_key="在学中",
                name="在学中",
                stack_id="employment",
                stroke=ACCENT_4,
                fill=ACCENT_4,
                radius=[8, 8, 0, 0],  # 最上層のみ角丸
            ),
            rx.recharts.x_axis(data_key="age_gender", stroke="#94a3b8", angle=-45, text_anchor="end", height=100),
            rx.recharts.y_axis(type_="number", stroke="#94a3b8"),  # 値軸として明示
            rx.recharts.legend(),
            rx.recharts.graphing_tooltip(),
            data=DashboardState.persona_employment_breakdown_data,
            width="100%",
            height=450,  # ラベル回転のため高さ増加
            bar_size=35,  # バーの太さを保証
        ),
        background=CARD_BG,
        border_radius="12px",
        border=f"1px solid {BORDER_COLOR}",
        padding="1.5rem",
        width="100%"
    )


# 6. Gap パネル用 (2個)

def gap_compare_chart() -> rx.Component:
    """需給: 需要 vs 供給棒グラフ

    GAS参照: Line 3794-3811
    """
    return rx.box(
        rx.recharts.bar_chart(
            rx.recharts.bar(
                data_key="demand",
                name="需要",
                stroke=SECONDARY_COLOR,
                fill=SECONDARY_COLOR,
            ),
            rx.recharts.bar(
                data_key="supply",
                name="供給",
                stroke=ACCENT_4,
                fill=ACCENT_4,
            ),
            rx.recharts.x_axis(data_key="category", stroke="#94a3b8"),
            rx.recharts.y_axis(stroke="#94a3b8"),
            rx.recharts.legend(),
            rx.recharts.graphing_tooltip(),
            data=DashboardState.gap_compare_data,
            width="100%",
            height=400
        ),
        background=CARD_BG,
        border_radius="12px",
        border=f"1px solid {BORDER_COLOR}",
        padding="1.5rem",
        width="100%"
    )


def gap_balance_chart() -> rx.Component:
    """需給: バランスドーナツチャート

    GAS参照: Line 3826-3842
    """
    return rx.box(
        rx.recharts.pie_chart(
            rx.recharts.pie(
                data=DashboardState.gap_balance_data,
                data_key="value",
                name_key="name",
                cx="50%",
                cy="50%",
                label=True
            ),
            rx.recharts.legend(),
            rx.recharts.graphing_tooltip(),
            width="100%",
            height=400
        ),
        background=CARD_BG,
        border_radius="12px",
        border=f"1px solid {BORDER_COLOR}",
        padding="1.5rem",
        width="100%"
    )


# 7. Rarity パネル用 (2個)

def rarity_rank_chart() -> rx.Component:
    """希少性: ランク分布ドーナツチャート

    GAS参照: Line 3942-3958
    """
    return rx.box(
        rx.recharts.pie_chart(
            rx.recharts.pie(
                data=DashboardState.rarity_rank_data,
                data_key="value",
                name_key="name",
                cx="50%",
                cy="50%",
                label=True
            ),
            rx.recharts.legend(),
            rx.recharts.graphing_tooltip(),
            width="100%",
            height=400
        ),
        background=CARD_BG,
        border_radius="12px",
        border=f"1px solid {BORDER_COLOR}",
        padding="1.5rem",
        width="100%"
    )


def rarity_score_chart() -> rx.Component:
    """希少性: Top 10希少性スコア（横棒グラフ）

    GAS参照: Line 3963-3978
    """
    return rx.box(
        rx.recharts.bar_chart(
            rx.recharts.bar(
                data_key="score",
                name="希少性スコア",
                stroke=ACCENT_6,
                fill=ACCENT_6,
            ),
            rx.recharts.x_axis(
                type_="number",
                stroke="#94a3b8",
                label={"value": "希少性スコア", "position": "insideBottom", "offset": -10, "style": {"fill": "#94a3b8", "fontSize": 12}}
            ),
            rx.recharts.y_axis(
                data_key="label",
                type_="category",
                stroke="#94a3b8",
                label={"value": "職種・資格", "angle": -90, "position": "insideLeft", "style": {"fill": "#94a3b8", "fontSize": 12}}
            ),
            rx.recharts.graphing_tooltip(),
            data=DashboardState.rarity_score_data,
            layout="vertical",
            width="100%",
            height=500
        ),
        background=CARD_BG,
        border_radius="12px",
        border=f"1px solid {BORDER_COLOR}",
        padding="1.5rem",
        width="100%"
    )


# 8. Competition パネル用 (2個)

def competition_gender_chart() -> rx.Component:
    """競合: 性別分布ドーナツチャート

    GAS参照: Line 4037-4056
    """
    return rx.box(
        rx.recharts.pie_chart(
            rx.recharts.pie(
                data=DashboardState.competition_gender_data,
                data_key="value",
                name_key="name",
                cx="50%",
                cy="50%",
                label=True
            ),
            rx.recharts.legend(),
            rx.recharts.graphing_tooltip(),
            width="100%",
            height=400
        ),
        background=CARD_BG,
        border_radius="12px",
        border=f"1px solid {BORDER_COLOR}",
        padding="1.5rem",
        width="100%"
    )


def competition_age_employment_chart() -> rx.Component:
    """競合: トップ年齢層・就業状態比率棒グラフ

    GAS参照: Line 4059-4074
    データソース: SUMMARY top_age_ratio, top_employment_ratio
    """
    return rx.box(
        rx.recharts.bar_chart(
            rx.recharts.bar(
                data_key="ratio",
                name="比率",
                stroke=PRIMARY_COLOR,
                fill=PRIMARY_COLOR,
            ),
            rx.recharts.x_axis(data_key="category", stroke="#94a3b8"),
            rx.recharts.y_axis(stroke="#94a3b8"),
            rx.recharts.legend(),
            rx.recharts.graphing_tooltip(),
            data=DashboardState.competition_age_employment_data,
            width="100%",
            height=400
        ),
        background=CARD_BG,
        border_radius="12px",
        border=f"1px solid {BORDER_COLOR}",
        padding="1.5rem",
        width="100%"
    )


def kpi_card(label: str, value: str, unit: str = "") -> rx.Component:
    """KPIカード"""
    return rx.box(
        rx.vstack(
            rx.text(
                label,
                font_size="0.85rem",
                color=MUTED_COLOR,
                margin_bottom="0.5rem",
                font_weight="500"
            ),
            rx.heading(
                f"{value}{unit}",
                size="7",
                color=TEXT_COLOR,
                margin="0"
            ),
            align="start",
            spacing="1"
        ),
        background=CARD_BG,
        border_radius="12px",
        border=f"1px solid {BORDER_COLOR}",
        padding="1.5rem",
        width="100%"
    )


def overview_panel() -> rx.Component:
    """overviewパネル: 総合概要"""
    return rx.box(
        rx.vstack(
            rx.heading(
                "総合概要",
                size="6",
                color=TEXT_COLOR,
                margin_bottom="1.5rem"
            ),
            # KPIカード（3列グリッド）
            rx.cond(
                DashboardState.is_loaded,
                rx.box(
                    rx.text(
                        "KPI",
                        font_size="0.9rem",
                        color=MUTED_COLOR,
                        margin_bottom="1rem",
                        font_weight="600"
                    ),
                    rx.hstack(
                        kpi_card("求職者数", DashboardState.overview_total_applicants, "人"),
                        kpi_card("平均年齢", DashboardState.overview_avg_age, "歳"),
                        kpi_card("男女比", DashboardState.overview_gender_ratio, "人"),
                        width="100%",
                        spacing="4"
                    ),
                    width="100%"
                ),
                rx.text(
                    "CSVファイルをアップロードしてください",
                    color=MUTED_COLOR,
                    font_size="0.9rem",
                    text_align="center",
                    padding="3rem"
                )
            ),
            # グラフ3つ
            rx.cond(
                DashboardState.is_loaded,
                rx.vstack(
                    rx.text(
                        "性別構成",
                        font_size="0.9rem",
                        color=MUTED_COLOR,
                        margin_top="2rem",
                        margin_bottom="1rem",
                        font_weight="600"
                    ),
                    overview_gender_chart(),
                    rx.text(
                        "年齢帯別分布",
                        font_size="0.9rem",
                        color=MUTED_COLOR,
                        margin_top="2rem",
                        margin_bottom="1rem",
                        font_weight="600"
                    ),
                    overview_age_chart(),
                    rx.text(
                        "年齢層×性別分布",
                        font_size="0.9rem",
                        color=MUTED_COLOR,
                        margin_top="2rem",
                        margin_bottom="1rem",
                        font_weight="600"
                    ),
                    overview_age_gender_chart(),
                    width="100%",
                    spacing="3"
                )
            ),
            width="100%",
            spacing="3"
        ),
        display=rx.cond(
            DashboardState.active_tab == "overview",
            "block",
            "none"
        ),
        width="100%",
        padding="2rem"
    )


def supply_panel() -> rx.Component:
    """supplyパネル: 人材供給"""
    return rx.box(
        rx.vstack(
            rx.heading("人材供給", size="6", color=TEXT_COLOR, margin_bottom="1.5rem"),
            rx.cond(
                DashboardState.is_loaded,
                rx.vstack(
                    rx.text("就業状況", font_size="0.9rem", color=MUTED_COLOR, font_weight="600", margin_bottom="1rem"),
                    rx.hstack(
                        kpi_card("就業中", DashboardState.supply_employed, "人"),
                        kpi_card("離職中", DashboardState.supply_unemployed, "人"),
                        kpi_card("在学中", DashboardState.supply_student, "人"),
                        width="100%", spacing="4"
                    ),
                    rx.hstack(
                        kpi_card("国家資格保有者", DashboardState.supply_national_license, "人"),
                        kpi_card("平均資格保有数", DashboardState.supply_avg_qualifications, "資格"),
                        width="100%", spacing="4"
                    ),
                    rx.text("就業ステータス分布", font_size="0.9rem", color=MUTED_COLOR, font_weight="600", margin_top="2rem", margin_bottom="1rem"),
                    supply_status_chart(),
                    rx.text("保有資格分布（ドーナツ）", font_size="0.9rem", color=MUTED_COLOR, font_weight="600", margin_top="2rem", margin_bottom="1rem"),
                    supply_qualification_doughnut_chart(),
                    rx.text("資格バケット分布（棒グラフ）", font_size="0.9rem", color=MUTED_COLOR, font_weight="600", margin_top="2rem", margin_bottom="1rem"),
                    supply_qualification_chart(),
                    rx.text("ペルソナ別平均資格数", font_size="0.9rem", color=MUTED_COLOR, font_weight="600", margin_top="2rem", margin_bottom="1rem"),
                    supply_persona_qual_chart(),
                    width="100%", spacing="3"
                ),
                rx.text("CSVファイルをアップロードしてください", color=MUTED_COLOR, font_size="0.9rem", text_align="center", padding="3rem")
            ),
            width="100%", spacing="3"
        ),
        display=rx.cond(DashboardState.active_tab == "supply", "block", "none"),
        width="100%", padding="2rem"
    )


def career_panel() -> rx.Component:
    """careerパネル: キャリア分析"""
    return rx.box(
        rx.vstack(
            rx.heading("キャリア分析", size="6", color=TEXT_COLOR, margin_bottom="1.5rem"),
            rx.cond(
                DashboardState.is_loaded,
                rx.vstack(
                    rx.hstack(
                        kpi_card("平均保有資格数", DashboardState.career_avg_qualifications, "資格"),
                        kpi_card("国家資格保有率", DashboardState.career_national_license_rate, "%"),
                        width="100%", spacing="4"
                    ),
                    rx.text("就業ステータス×年齢帯", font_size="0.9rem", color=MUTED_COLOR, font_weight="600", margin_top="2rem", margin_bottom="1rem"),
                    career_employment_age_chart(),
                    width="100%", spacing="3"
                ),
                rx.text("CSVファイルをアップロードしてください", color=MUTED_COLOR, font_size="0.9rem", text_align="center", padding="3rem")
            ),
            width="100%", spacing="3"
        ),
        display=rx.cond(DashboardState.active_tab == "career", "block", "none"),
        width="100%", padding="2rem"
    )


def urgency_panel() -> rx.Component:
    """urgencyパネル: 緊急度分析"""
    return rx.box(
        rx.vstack(
            rx.heading("緊急度分析", size="6", color=TEXT_COLOR, margin_bottom="1.5rem"),
            rx.cond(
                DashboardState.is_loaded,
                rx.vstack(
                    # 緊急度スコア計算方法の説明
                    rx.box(
                        rx.vstack(
                            rx.heading("📊 緊急度スコア計算方法", size="4", color=TEXT_COLOR, margin_bottom="0.75rem"),
                            rx.text("以下の4要素を総合評価（0-11点）", font_size="0.85rem", color=MUTED_COLOR, margin_bottom="0.5rem"),
                            rx.vstack(
                                rx.hstack(
                                    rx.text("1. 希望勤務地数", font_weight="600", color=TEXT_COLOR, width="150px"),
                                    rx.text("0: 0点 | 1-2: 1点 | 3-5: 2点 | 6以上: 3点", font_size="0.85rem", color=MUTED_COLOR),
                                    spacing="2", width="100%"
                                ),
                                rx.hstack(
                                    rx.text("2. 保有資格数", font_weight="600", color=TEXT_COLOR, width="150px"),
                                    rx.text("0: 0点 | 1-2: 1点 | 3以上: 2点", font_size="0.85rem", color=MUTED_COLOR),
                                    spacing="2", width="100%"
                                ),
                                rx.hstack(
                                    rx.text("3. 国家資格保有", font_weight="600", color=TEXT_COLOR, width="150px"),
                                    rx.text("あり: +2点", font_size="0.85rem", color=MUTED_COLOR),
                                    spacing="2", width="100%"
                                ),
                                rx.hstack(
                                    rx.text("4. 就業状態", font_weight="600", color=TEXT_COLOR, width="150px"),
                                    rx.text("離職中: 2点 | 就業中: 1点 | 在学中: 0点", font_size="0.85rem", color=MUTED_COLOR),
                                    spacing="2", width="100%"
                                ),
                                spacing="2", width="100%"
                            ),
                            width="100%", spacing="2"
                        ),
                        background=CARD_BG,
                        border_radius="12px",
                        border=f"1px solid {BORDER_COLOR}",
                        padding="1.5rem",
                        margin_bottom="2rem"
                    ),
                    rx.hstack(
                        kpi_card("対象人数", DashboardState.urgency_total_count, "人"),
                        kpi_card("平均スコア", DashboardState.urgency_avg_score, ""),
                        width="100%", spacing="4"
                    ),
                    rx.text("年齢帯別緊急度（棒+折れ線、2軸）", font_size="0.9rem", color=MUTED_COLOR, font_weight="600", margin_top="2rem", margin_bottom="1rem"),
                    urgency_age_chart(),
                    rx.text("就業ステータス別緊急度（棒+折れ線、2軸）", font_size="0.9rem", color=MUTED_COLOR, font_weight="600", margin_top="2rem", margin_bottom="1rem"),
                    urgency_employment_chart(),
                    width="100%", spacing="3"
                ),
                rx.text("CSVファイルをアップロードしてください", color=MUTED_COLOR, font_size="0.9rem", text_align="center", padding="3rem")
            ),
            width="100%", spacing="3"
        ),
        display=rx.cond(DashboardState.active_tab == "urgency", "block", "none"),
        width="100%", padding="2rem"
    )


def persona_panel() -> rx.Component:
    """personaパネル: ペルソナ分析"""
    def render_persona_item(item):
        """全ペルソナリストの各アイテムを表示"""
        return rx.hstack(
            rx.text(item["label"], font_weight="600", color=TEXT_COLOR, font_size="0.85rem"),
            rx.text(item["count_display"], color=MUTED_COLOR, font_size="0.85rem"),
            width="100%", justify="between"
        )

    return rx.box(
        rx.vstack(
            rx.heading("ペルソナ分析", size="6", color=TEXT_COLOR, margin_bottom="1.5rem"),
            rx.cond(
                DashboardState.is_loaded,
                rx.vstack(
                    # 全ペルソナリスト（100%内訳）
                    rx.text("全ペルソナ内訳（100%）", font_size="0.9rem", color=MUTED_COLOR, font_weight="600", margin_bottom="1rem"),
                    rx.box(
                        rx.vstack(
                            rx.foreach(DashboardState.persona_full_list, render_persona_item),
                            width="100%", spacing="2"
                        ),
                        background=CARD_BG,
                        border_radius="12px",
                        border=f"1px solid {BORDER_COLOR}",
                        padding="1.5rem",
                        max_height="400px",
                        overflow_y="auto"
                    ),

                    # ペルソナ構成比（円グラフ）
                    rx.text("ペルソナ構成比（円グラフ）", font_size="0.9rem", color=MUTED_COLOR, font_weight="600", margin_top="2rem", margin_bottom="1rem"),
                    persona_share_chart(),

                    # 人数ランキング（横棒グラフ）
                    rx.text("人数ランキング Top 15（横棒グラフ）", font_size="0.9rem", color=MUTED_COLOR, font_weight="600", margin_top="2rem", margin_bottom="1rem"),
                    persona_bar_chart(),

                    # 就業状態別内訳（積み上げ棒グラフ）
                    rx.text("年齢・性別×就業状態別内訳 Top 10（積み上げ棒グラフ）", font_size="0.9rem", color=MUTED_COLOR, font_weight="600", margin_top="2rem", margin_bottom="1rem"),
                    persona_employment_breakdown_chart(),

                    width="100%", spacing="3"
                ),
                rx.text("CSVファイルをアップロードしてください", color=MUTED_COLOR, font_size="0.9rem", text_align="center", padding="3rem")
            ),
            width="100%", spacing="3"
        ),
        display=rx.cond(DashboardState.active_tab == "persona", "block", "none"),
        width="100%", padding="2rem"
    )


def cross_panel() -> rx.Component:
    """crossパネル: クロス分析（多重クロス集計）"""
    return rx.box(
        rx.vstack(
            rx.heading("クロス分析（多重クロス集計）", size="6", color=TEXT_COLOR, margin_bottom="1.5rem"),
            rx.cond(
                DashboardState.is_loaded,
                rx.vstack(
                    # 1. 年齢層×性別クロス集計
                    rx.text("1. 年齢層×性別クロス集計", font_size="0.9rem", color=MUTED_COLOR, font_weight="600", margin_bottom="1rem"),
                    overview_age_gender_chart(),

                    # 2. 年齢層×就業状態クロス集計
                    rx.text("2. 年齢層×就業状態クロス集計", font_size="0.9rem", color=MUTED_COLOR, font_weight="600", margin_top="2rem", margin_bottom="1rem"),
                    cross_age_employment_chart(),

                    # 3. 性別×就業状態クロス集計
                    rx.text("3. 性別×就業状態クロス集計", font_size="0.9rem", color=MUTED_COLOR, font_weight="600", margin_top="2rem", margin_bottom="1rem"),
                    cross_gender_employment_chart(),

                    # 4. 年齢層×資格保有クロス集計
                    rx.text("4. 年齢層×資格保有クロス集計", font_size="0.9rem", color=MUTED_COLOR, font_weight="600", margin_top="2rem", margin_bottom="1rem"),
                    cross_age_qualification_chart(),
                    rx.text("凡例: 平均資格数（青）、国家資格保有率％（オレンジ）", color=MUTED_COLOR, font_size="0.85rem", margin_top="0.5rem"),

                    # 5. 就業状態×資格保有クロス集計
                    rx.text("5. 就業状態×資格保有クロス集計", font_size="0.9rem", color=MUTED_COLOR, font_weight="600", margin_top="2rem", margin_bottom="1rem"),
                    cross_employment_qualification_chart(),
                    rx.text("凡例: 平均資格数（青）、国家資格保有率％（オレンジ）", color=MUTED_COLOR, font_size="0.85rem", margin_top="0.5rem"),

                    # 6. ペルソナ×資格×年齢 - 希少人材の特定
                    rx.text("6. ペルソナ×資格×年齢 - 希少人材の特定", font_size="0.9rem", color=MUTED_COLOR, font_weight="600", margin_top="3rem", margin_bottom="1rem"),
                    cross_persona_qualification_age_chart(),
                    rx.text("希少度スコア = 資格数 × (1000 / 人数)。バブルサイズは人数を表します。", color=MUTED_COLOR, font_size="0.85rem", margin_top="0.5rem"),

                    # 7. 移動距離×年齢×性別 - 地域採用戦略
                    rx.text("7. 移動距離×年齢×性別 - 地域採用戦略", font_size="0.9rem", color=MUTED_COLOR, font_weight="600", margin_top="3rem", margin_bottom="1rem"),
                    cross_distance_age_gender_chart(),
                    rx.text("移動許容度スコア: 若年層ほど高く、男性は女性より1.1倍高い想定。", color=MUTED_COLOR, font_size="0.85rem", margin_top="0.5rem"),

                    # 8. 転職意欲×キャリア×年齢 - ターゲティング精度向上
                    rx.text("8. 転職意欲×キャリア×年齢 - ターゲティング精度向上", font_size="0.9rem", color=MUTED_COLOR, font_weight="600", margin_top="3rem", margin_bottom="1rem"),
                    cross_urgency_career_age_chart(),
                    rx.text("転職意欲（朱色）と平均資格数（オレンジ）の年齢層別比較。高意欲×高スキルが採用ターゲット。", color=MUTED_COLOR, font_size="0.85rem", margin_top="0.5rem"),

                    # 9. 供給密度×需要バランス×地域 - 競争環境分析
                    rx.text("9. 供給密度×需要バランス×地域 - 競争環境分析", font_size="0.9rem", color=MUTED_COLOR, font_weight="600", margin_top="3rem", margin_bottom="1rem"),
                    cross_supply_demand_region_chart(),
                    rx.text("横軸: 供給密度、縦軸: 需要比率、バブルサイズ: ギャップスコア。都道府県内の全市町村を比較。", color=MUTED_COLOR, font_size="0.85rem", margin_top="0.5rem"),

                    # 10. 多次元プロファイル - 複合的な人材分析
                    rx.text("10. 多次元プロファイル - 複合的な人材分析", font_size="0.9rem", color=MUTED_COLOR, font_weight="600", margin_top="3rem", margin_bottom="1rem"),
                    cross_multidimensional_profile_chart(),
                    rx.text("転職意欲・資格・移動許容度を統合した多次元ペルソナ分析。総合スコア上位30件を表示。", color=MUTED_COLOR, font_size="0.85rem", margin_top="0.5rem"),

                    width="100%", spacing="3"
                ),
                rx.text("CSVファイルをアップロードしてください", color=MUTED_COLOR, font_size="0.9rem", text_align="center", padding="3rem")
            ),
            width="100%", spacing="3"
        ),
        display=rx.cond(DashboardState.active_tab == "cross", "block", "none"),
        width="100%", padding="2rem"
    )


def flow_panel() -> rx.Component:
    """flowパネル: フロー分析（GAS完全再現版）"""
    return rx.box(
        rx.vstack(
            rx.heading("フロー分析", size="6", color=TEXT_COLOR, margin_bottom="1.5rem"),
            rx.cond(
                DashboardState.is_loaded,
                rx.vstack(
                    # KPIカード（5枚）
                    rx.hstack(
                        kpi_card("流入", DashboardState.flow_total_inflow, "人"),
                        kpi_card("流出", DashboardState.flow_total_outflow, "人"),
                        kpi_card("純流入", DashboardState.flow_net_flow, "人"),
                        kpi_card("人気度", DashboardState.flow_popularity_rate, ""),
                        kpi_card("外部志向度", DashboardState.flow_mobility_rate, ""),
                        width="100%", spacing="4"
                    ),

                    # 流入ランキング Top 10
                    flow_inflow_ranking_chart(),

                    # 流出ランキング Top 10
                    flow_outflow_ranking_chart(),

                    # 純流入ランキング Top 10
                    flow_netflow_ranking_chart(),

                    # 説明パネル
                    rx.box(
                        rx.vstack(
                            rx.heading("指標の説明", size="4", color=TEXT_COLOR, margin_bottom="1rem"),
                            rx.text("流入: 他地域から選択地域を希望する人数", color=MUTED_COLOR, font_size="0.85rem", margin_bottom="0.5rem"),
                            rx.text("流出: 選択地域から他地域を希望する人数", color=MUTED_COLOR, font_size="0.85rem", margin_bottom="0.5rem"),
                            rx.text("純流入: 流入 - 流出（正の値は流入超過、負の値は流出超過）", color=MUTED_COLOR, font_size="0.85rem", margin_bottom="0.5rem"),
                            rx.text("人気度: 流入 ÷ 申請者数 × 100%（地域外からの人気指標）", color=MUTED_COLOR, font_size="0.85rem", margin_bottom="0.5rem"),
                            rx.text("外部志向度: 流出 ÷ 申請者数 × 100%（地域外志向の強さ）", color=MUTED_COLOR, font_size="0.85rem"),
                            width="100%", spacing="2"
                        ),
                        background=CARD_BG, border_radius="12px", border=f"1px solid {BORDER_COLOR}", padding="1.5rem", margin_top="2rem", width="100%"),
                    width="100%", spacing="3"
                ),
                rx.text("CSVファイルをアップロードしてください", color=MUTED_COLOR, font_size="0.9rem", text_align="center", padding="3rem")
            ),
            width="100%", spacing="3"
        ),
        display=rx.cond(DashboardState.active_tab == "flow", "block", "none"),
        width="100%", padding="2rem"
    )


def gap_panel() -> rx.Component:
    """gapパネル: 需給バランス（GAS完全再現版）"""
    return rx.box(
        rx.vstack(
            rx.heading("需給バランス", size="6", color=TEXT_COLOR, margin_bottom="1.5rem"),
            rx.cond(
                DashboardState.is_loaded,
                rx.vstack(
                    # KPIカード（5枚）
                    rx.hstack(
                        kpi_card("総需要", DashboardState.gap_total_demand, "件"),
                        kpi_card("総供給", DashboardState.gap_total_supply, "件"),
                        kpi_card("平均比率", DashboardState.gap_avg_ratio, ""),
                        kpi_card("不足地域", DashboardState.gap_shortage_count, "箇所"),
                        kpi_card("過剰地域", DashboardState.gap_surplus_count, "箇所"),
                        width="100%", spacing="4"
                    ),

                    # 需要超過ランキング Top 10
                    gap_shortage_ranking_chart(),

                    # 供給超過ランキング Top 10
                    gap_surplus_ranking_chart(),

                    # 需給比率ランキング Top 10
                    gap_ratio_ranking_chart(),

                    # 説明パネル
                    rx.box(
                        rx.vstack(
                            rx.heading("指標の説明", size="4", color=TEXT_COLOR, margin_bottom="1rem"),
                            rx.text("総需要: 地域内で必要とされる人材数", color=MUTED_COLOR, font_size="0.85rem", margin_bottom="0.5rem"),
                            rx.text("総供給: 地域内で利用可能な人材数", color=MUTED_COLOR, font_size="0.85rem", margin_bottom="0.5rem"),
                            rx.text("平均比率: 需要 ÷ 供給の平均（比率が高いほど人材獲得が困難）", color=MUTED_COLOR, font_size="0.85rem", margin_bottom="0.5rem"),
                            rx.text("不足地域: 需要 > 供給の市区町村数（採用難易度が高い地域）", color=MUTED_COLOR, font_size="0.85rem", margin_bottom="0.5rem"),
                            rx.text("過剰地域: 供給 > 需要の市区町村数（人材が余剰している地域）", color=MUTED_COLOR, font_size="0.85rem"),
                            width="100%", spacing="2"
                        ),
                        background=CARD_BG, border_radius="12px", border=f"1px solid {BORDER_COLOR}", padding="1.5rem", margin_top="2rem", width="100%"),
                    width="100%", spacing="3"
                ),
                rx.text("CSVファイルをアップロードしてください", color=MUTED_COLOR, font_size="0.9rem", text_align="center", padding="3rem")
            ),
            width="100%", spacing="3"
        ),
        display=rx.cond(DashboardState.active_tab == "gap", "block", "none"),
        width="100%", padding="2rem"
    )


def rarity_panel() -> rx.Component:
    """rarityパネル: 希少人材分析（GAS完全再現版）"""
    return rx.box(
        rx.vstack(
            rx.heading("希少人材分析", size="6", color=TEXT_COLOR, margin_bottom="1.5rem"),
            rx.cond(
                DashboardState.is_loaded,
                rx.vstack(
                    # KPIカード（6枚）
                    rx.hstack(
                        kpi_card("総希少人材", DashboardState.rarity_total_count, "人"),
                        kpi_card("S: 超希少", DashboardState.rarity_s_count, "人"),
                        kpi_card("A: 非常に希少", DashboardState.rarity_a_count, "人"),
                        kpi_card("B: 希少", DashboardState.rarity_b_count, "人"),
                        kpi_card("国家資格保有", DashboardState.rarity_national_license_count, "人"),
                        kpi_card("平均スコア", DashboardState.rarity_avg_score, ""),
                        width="100%", spacing="4"
                    ),

                    # 年齢層別分布
                    rx.box(
                        rx.vstack(
                            rx.heading("年齢層別希少人材分布", size="4", color=TEXT_COLOR, margin_bottom="1rem"),
                            rx.text("希少人材の年齢層分布", color=MUTED_COLOR, font_size="0.85rem", margin_bottom="1rem"),
                            rx.recharts.bar_chart(
                                rx.recharts.bar(
                                    data_key="value",
                                    stroke=PRIMARY_COLOR,
                                    fill=PRIMARY_COLOR,
                                ),
                                rx.recharts.x_axis(data_key="name", stroke="#94a3b8"),
                                rx.recharts.y_axis(stroke="#94a3b8"),
                                rx.recharts.graphing_tooltip(),
                                data=DashboardState.rarity_age_distribution,
                                width="100%",
                                height=300,
                            ),
                            width="100%", spacing="2"
                        ),
                        background=CARD_BG, border_radius="12px", border=f"1px solid {BORDER_COLOR}", padding="1.5rem", margin_top="2rem", width="100%"
                    ),

                    # 性別分布
                    rx.box(
                        rx.vstack(
                            rx.heading("性別分布", size="4", color=TEXT_COLOR, margin_bottom="1rem"),
                            rx.text("希少人材の性別比率", color=MUTED_COLOR, font_size="0.85rem", margin_bottom="1rem"),
                            rx.recharts.pie_chart(
                                rx.recharts.pie(
                                    data=DashboardState.rarity_gender_distribution,
                                    data_key="value",
                                    name_key="name",
                                    cx="50%",
                                    cy="50%",
                                    fill=PRIMARY_COLOR,
                                    label=True,
                                ),
                                rx.recharts.graphing_tooltip(),
                                width="100%",
                                height=300,
                            ),
                            width="100%", spacing="2"
                        ),
                        background=CARD_BG, border_radius="12px", border=f"1px solid {BORDER_COLOR}", padding="1.5rem", margin_top="2rem", width="100%"
                    ),

                    # 国家資格保有者ランキング
                    rarity_national_license_ranking_chart(),

                    # 希少性ランク分布（既存）
                    rx.box(
                        rx.vstack(
                            rx.heading("希少性ランク分布", size="4", color=TEXT_COLOR, margin_bottom="1rem"),
                            rx.text("S/A/Bランク別の人数分布", color=MUTED_COLOR, font_size="0.85rem", margin_bottom="1rem"),
                            rarity_rank_chart(),
                            width="100%", spacing="2"
                        ),
                        background=CARD_BG, border_radius="12px", border=f"1px solid {BORDER_COLOR}", padding="1.5rem", margin_top="2rem", width="100%"),

                    # 希少性スコアTop 10（既存）
                    rx.box(
                        rx.vstack(
                            rx.heading("希少性スコア Top 10", size="4", color=TEXT_COLOR, margin_bottom="1rem"),
                            rx.text("最も希少性の高い人材プロファイル", color=MUTED_COLOR, font_size="0.85rem", margin_bottom="1rem"),
                            rarity_score_chart(),
                            width="100%", spacing="2"
                        ),
                        background=CARD_BG, border_radius="12px", border=f"1px solid {BORDER_COLOR}", padding="1.5rem", margin_top="2rem", width="100%"),

                    # 説明パネル
                    rx.box(
                        rx.vstack(
                            rx.heading("指標の説明", size="4", color=TEXT_COLOR, margin_bottom="1rem"),
                            rx.text("希少性スコア: 人材の希少性を0-1で数値化（1に近いほど希少）", color=MUTED_COLOR, font_size="0.85rem", margin_bottom="0.5rem"),
                            rx.text("Sランク: 1人のみの超希少人材（スコア: 1.0）", color=MUTED_COLOR, font_size="0.85rem", margin_bottom="0.5rem"),
                            rx.text("Aランク: 2-5人程度の非常に希少な人材（スコア: 0.5-0.9）", color=MUTED_COLOR, font_size="0.85rem", margin_bottom="0.5rem"),
                            rx.text("Bランク: 6-10人程度の希少な人材（スコア: 0.3-0.5）", color=MUTED_COLOR, font_size="0.85rem", margin_bottom="0.5rem"),
                            rx.text("国家資格保有者: 看護師、介護福祉士等の国家資格を持つ人材", color=MUTED_COLOR, font_size="0.85rem"),
                            width="100%", spacing="2"
                        ),
                        background=CARD_BG, border_radius="12px", border=f"1px solid {BORDER_COLOR}", padding="1.5rem", margin_top="2rem", width="100%"),
                    width="100%", spacing="3"
                ),
                rx.text("CSVファイルをアップロードしてください", color=MUTED_COLOR, font_size="0.9rem", text_align="center", padding="3rem")
            ),
            width="100%", spacing="3"
        ),
        display=rx.cond(DashboardState.active_tab == "rarity", "block", "none"),
        width="100%", padding="2rem"
    )


def competition_panel() -> rx.Component:
    """competitionパネル: 人材プロファイル（GAS完全再現版）"""
    return rx.box(
        rx.vstack(
            rx.heading("人材プロファイル", size="6", color=TEXT_COLOR, margin_bottom="1.5rem"),
            rx.cond(
                DashboardState.is_loaded,
                rx.vstack(
                    # KPIカード（6枚）
                    rx.hstack(
                        kpi_card("総申請者数", DashboardState.competition_total_applicants, "人"),
                        kpi_card("女性比率", DashboardState.competition_avg_female_ratio, "%"),
                        kpi_card("男性比率", DashboardState.competition_avg_male_ratio, "%"),
                        kpi_card("国家資格率", DashboardState.competition_avg_national_license_rate, "%"),
                        kpi_card("平均資格数", DashboardState.competition_avg_qualification_count, "個"),
                        kpi_card("地域数", DashboardState.competition_total_regions, "箇所"),
                        width="100%", spacing="4"
                    ),

                    # 国家資格保有率ランキング
                    competition_national_license_ranking_chart(),

                    # 平均資格数ランキング
                    competition_qualification_ranking_chart(),

                    # 女性比率ランキング
                    competition_female_ratio_ranking_chart(),

                    # 性別分布（既存）
                    rx.box(
                        rx.vstack(
                            rx.heading("性別分布", size="4", color=TEXT_COLOR, margin_bottom="1rem"),
                            rx.text("全体の性別比率", color=MUTED_COLOR, font_size="0.85rem", margin_bottom="1rem"),
                            competition_gender_chart(),
                            width="100%", spacing="2"
                        ),
                        background=CARD_BG, border_radius="12px", border=f"1px solid {BORDER_COLOR}", padding="1.5rem", margin_top="2rem", width="100%"),

                    # トップ年齢層・就業状態比率（既存）
                    rx.box(
                        rx.vstack(
                            rx.heading("トップ年齢層・就業状態比率", size="4", color=TEXT_COLOR, margin_bottom="1rem"),
                            rx.text("最多年齢層と最多就業状態の比率", color=MUTED_COLOR, font_size="0.85rem", margin_bottom="1rem"),
                            competition_age_employment_chart(),
                            width="100%", spacing="2"
                        ),
                        background=CARD_BG, border_radius="12px", border=f"1px solid {BORDER_COLOR}", padding="1.5rem", margin_top="2rem", width="100%"),

                    # 説明パネル
                    rx.box(
                        rx.vstack(
                            rx.heading("指標の説明", size="4", color=TEXT_COLOR, margin_bottom="1rem"),
                            rx.text("国家資格率: 看護師、介護福祉士等の国家資格保有者の割合", color=MUTED_COLOR, font_size="0.85rem", margin_bottom="0.5rem"),
                            rx.text("平均資格数: 1人あたりの保有資格数（複数資格保有者を含む）", color=MUTED_COLOR, font_size="0.85rem", margin_bottom="0.5rem"),
                            rx.text("女性比率: 各年齢層・ペルソナにおける女性の割合", color=MUTED_COLOR, font_size="0.85rem", margin_bottom="0.5rem"),
                            rx.text("トップ年齢層比率: 最も多い年齢層の割合", color=MUTED_COLOR, font_size="0.85rem", margin_bottom="0.5rem"),
                            rx.text("トップ就業状態比率: 最も多い就業形態の割合", color=MUTED_COLOR, font_size="0.85rem"),
                            width="100%", spacing="2"
                        ),
                        background=CARD_BG, border_radius="12px", border=f"1px solid {BORDER_COLOR}", padding="1.5rem", margin_top="2rem", width="100%"),
                    width="100%", spacing="3"
                ),
                rx.text("CSVファイルをアップロードしてください", color=MUTED_COLOR, font_size="0.9rem", text_align="center", padding="3rem")
            ),
            width="100%", spacing="3"
        ),
        display=rx.cond(DashboardState.active_tab == "competition", "block", "none"),
        width="100%", padding="2rem"
    )


def panel_placeholder(panel_id: str, label: str) -> rx.Component:
    """パネルプレースホルダー（他のパネル用）"""
    return rx.box(
        rx.vstack(
            rx.heading(
                label,
                size="6",
                color=TEXT_COLOR,
                margin_bottom="1rem"
            ),
            rx.text(
                f"パネル: {panel_id}",
                color=MUTED_COLOR,
                font_size="0.9rem"
            ),
            rx.text(
                "データ表示機能を実装予定",
                color=MUTED_COLOR,
                font_size="0.85rem",
                margin_top="0.5rem"
            ),
            align="center",
            justify="center",
            height="100%"
        ),
        display=rx.cond(
            DashboardState.active_tab == panel_id,
            "block",
            "none"
        ),
        width="100%",
        min_height="500px",
        background=CARD_BG,
        border_radius="12px",
        border=f"1px solid {BORDER_COLOR}",
        padding="2rem"
    )


def jobmap_panel() -> rx.Component:
    """求人地図パネル（Panel 11）

    GAS Webアプリを埋め込み（複数職種対応）
    - 完全なLeaflet地図機能
    - ピン止め + ドラッグ&ドロップ
    - 点線接続表示
    - 職種プルダウンで切り替え
    """
    # GAS WebアプリURL辞書（職種別）
    # 新しい職種のURLを追加する場合は、ここに追加してください
    GAS_WEBAPP_URLS = {
        "介護職": "https://script.google.com/macros/s/AKfycbxd--YaAomrsCpqaLyB40XkTlVOt17bqulrddPVCoFBAOw1FDE7r8mYHMRSKT25D9t7/exec",
        # 以下、他の職種のURLを追加
        # "看護師": "https://script.google.com/macros/s/YOUR_DEPLOYMENT_ID_HERE/exec",
        # "保育士": "https://script.google.com/macros/s/YOUR_DEPLOYMENT_ID_HERE/exec",
        # "医療事務": "https://script.google.com/macros/s/YOUR_DEPLOYMENT_ID_HERE/exec",
    }

    # 現在選択されている職種のURLを取得（デフォルトは最初の職種）
    current_url = GAS_WEBAPP_URLS.get(
        DashboardState.selected_job_type,
        list(GAS_WEBAPP_URLS.values())[0]
    )

    return rx.box(
        # タイトルと職種選択プルダウン
        rx.box(
            rx.hstack(
                rx.heading("🗺️ 求人地図", size="7", color=TEXT_COLOR),
                rx.spacer(),
                # 職種選択プルダウン
                rx.select(
                    list(GAS_WEBAPP_URLS.keys()),
                    value=DashboardState.selected_job_type,
                    on_change=DashboardState.set_selected_job_type,
                    placeholder="職種を選択",
                    size="3",
                    color_scheme="blue",
                ),
                width="100%",
                align_items="center",
                margin_bottom="0.5rem"
            ),
            rx.text(
                "GASの完全な地図機能（Leaflet + ピン止め + ドラッグ&ドロップ + 点線接続）",
                color=MUTED_COLOR,
                font_size="0.9rem",
                margin_bottom="1rem"
            ),
            width="100%",
            padding_x="1.5rem",
            display=rx.cond(
                DashboardState.active_tab == "jobmap",
                "block",
                "none"
            )
        ),
        # GAS Webアプリをiframeで埋め込み（全幅）
        # 重要: iframeは常に描画し、displayのみ切り替え（状態保持のため）
        rx.html(
            f"""
            <iframe
                id="jobmap-iframe"
                src="{current_url}"
                width="100%"
                height="calc(100vh - 250px)"
                frameborder="0"
                style="border: 1px solid {BORDER_COLOR}; border-radius: 8px; background: white; display: block; min-height: 650px;"
                allow="geolocation"
            ></iframe>
            """
        ),
        display=rx.cond(
            DashboardState.active_tab == "jobmap",
            "flex",
            "none"
        ),
        flex_direction="column",
        width="100%",
        height="100%",
        padding_top="1.5rem",
        padding_bottom="1.5rem"
    )


def panels() -> rx.Component:
    """11パネル表示エリア（求人地図追加）"""
    return rx.vstack(
        overview_panel(),
        supply_panel(),
        career_panel(),
        urgency_panel(),
        persona_panel(),
        cross_panel(),
        flow_panel(),
        gap_panel(),
        rarity_panel(),
        competition_panel(),
        jobmap_panel(),  # 新規追加
        width="100%",
        spacing="3",
        padding="1rem"
    )


def main_content() -> rx.Component:
    """メインコンテンツエリア"""
    return rx.box(
        rx.vstack(
            tabbar(),
            panels(),
            width="100%",
            spacing="0"
        ),
        width="calc(100vw - 440px)",
        height="100vh",
        overflow_y="auto"
    )


def protected_dashboard() -> rx.Component:
    """保護されたダッシュボード（認証必須）"""
    return rx.box(
        rx.hstack(
            main_content(),
            sidebar(),
            width="100%",
            spacing="0",
            position="relative"
        ),
        width="100vw",
        height="100vh",
        background=BG_COLOR,
        overflow="hidden"
    )


def index() -> rx.Component:
    """メインページ（認証保護）"""
    return rx.cond(
        AuthState.is_authenticated,
        protected_dashboard(),
        # 未認証時はログインページを表示
        login_page()
    )


# =====================================
# App
# =====================================
app = rx.App(
    style={
        "font_family": "system-ui, -apple-system, sans-serif",
    }
)

# ルーティング設定
app.add_page(login_page, route="/login")
app.add_page(index, route="/")
