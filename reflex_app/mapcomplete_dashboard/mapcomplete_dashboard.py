"""MapComplete統合ダッシュボード（GAS完全再現版）

GAS統合ダッシュボード（map_complete_integrated.html）の完全再現
- 10パネル: overview, supply, career, urgency, persona, cross, flow, gap, rarity, competition
- 右サイドバーレイアウト（440px、リサイズ可能）
- GAS配色（深いネイビー基調）
- CSVアップロード機能（ドラッグ&ドロップ）
- 色覚バリアフリー対応（Okabe-Itoカラーパレット）2025-11-14更新
- ログイン機能修正: rx.formパターン適用 2025-11-27更新
- AGE_GENDER_RESIDENCE追加: 居住地ベース年齢×性別切替 2025-12-07更新
"""

import reflex as rx
import pandas as pd
import json
import unicodedata as ud
from typing import Optional, List, Dict, Any
from datetime import datetime
import plotly.graph_objects as go

# 認証モジュールのインポート
from .auth import AuthState, require_auth
from .login import login_page

# db_helper.py のインポート（データベース統合用）
# rootDirectoryがreflex_appなので、sys.path操作不要
try:
    from db_helper import (
        get_connection, get_db_type, query_df, get_all_data,
        get_prefectures, get_municipalities, get_filtered_data,
        get_row_count_by_location, USE_CSV_MODE, _load_csv_data,
        PREFECTURE_ORDER,  # 都道府県の標準順序（北→南）
        clear_cache  # キャッシュクリア関数（データ更新後に使用）
    )
    _DB_AVAILABLE = True
except ImportError:
    _DB_AVAILABLE = False
    USE_CSV_MODE = False
    _load_csv_data = None
    PREFECTURE_ORDER = []  # フォールバック用
    clear_cache = lambda: None  # フォールバック用ダミー関数
    print("[WARNING] db_helper.py not found. Database features disabled.")


def _sort_prefectures_by_jis(prefectures: list) -> list:
    """都道府県リストをJISコード順（北海道→沖縄）でソート"""
    if not PREFECTURE_ORDER:
        return sorted(prefectures)  # フォールバック: 五十音順
    order_map = {pref: i for i, pref in enumerate(PREFECTURE_ORDER)}
    return sorted(prefectures, key=lambda x: order_map.get(x, 999))

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
# 5タブ定義（V3対応: TAB_CONSOLIDATION_PLAN_V2.md準拠）
# 旧11タブから5タブに統合（jobmapは別プロジェクト要件で維持）
# =====================================
TABS = [
    {"id": "overview", "label": "📊 市場概況"},
    {"id": "persona", "label": "👥 人材属性"},
    {"id": "region", "label": "🗺️ 地域・移動パターン"},
    {"id": "gap", "label": "⚖️ 需給バランス"},
    {"id": "jobmap", "label": "🗺️ 求人地図"},  # 別プロジェクト要件で維持
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

    # 資格選択（人材属性タブ用）
    selected_qualification: str = ""  # 選択した資格（空の場合はTop1を使用）

    # 年齢×性別分析の表示モード（"destination": 希望勤務地ベース, "residence": 居住地ベース）
    age_gender_view_mode: str = "destination"

    # CSVモードでの初期化完了フラグ（on_mountで一度だけ実行）
    _csv_initialized: bool = False

    # 3層比較用キャッシュ（全国・都道府県統計）
    national_stats: dict = {}  # {"desired_areas": 65.6, "distance_km": 63.2, "qualifications": 1.09}
    prefecture_stats_cache: dict = {}  # {"東京都": {"desired_areas": 52.3, ...}, ...}

    # =====================================
    # 新機能: RARITY分析用（複数選択対応）
    # =====================================
    rarity_selected_ages: list[str] = []  # 選択された年齢層（複数可）
    rarity_selected_genders: list[str] = []  # 選択された性別（複数可）
    rarity_selected_qualifications: list[str] = []  # 選択された資格（複数可）

    # =====================================
    # 新機能: mobility_type分析用
    # =====================================
    mobility_view_mode: str = "residence"  # "residence": 居住地ベース, "destination": 希望勤務地ベース

    def on_mount_init(self):
        """ページマウント時の初期化（on_mount用）

        ビルド時ではなくランタイムでデータをロードすることで、
        context.jsのサイズを削減（96MB→数KB）
        """
        # 既に初期化済みの場合はスキップ
        if self._csv_initialized or self.is_loaded:
            return

        # CSVモード: 同梱CSVから全データをロード（Reflex Cloud用）
        if USE_CSV_MODE and _load_csv_data is not None:
            try:
                print("[CSV MODE] on_mount: 同梱CSVから自動ロード開始...")
                self.df_full = self._normalize_df(_load_csv_data())
                self.csv_uploaded = True
                self.total_rows = len(self.df_full)
                self.is_loaded = True
                self._csv_initialized = True

                # 都道府県リスト抽出
                self.prefectures = _sort_prefectures_by_jis(self.df_full['prefecture'].dropna().unique().tolist())

                if len(self.prefectures) > 0:
                    # 最初の都道府県を選択
                    first_pref = self.prefectures[0]
                    self.selected_prefecture = first_pref

                    # 市区町村リスト抽出（空文字列や"nan"を除外）
                    filtered = self.df_full[self.df_full['prefecture'] == first_pref]
                    muni_list = filtered['municipality'].dropna().unique().tolist()
                    self.municipalities = sorted([m for m in muni_list if m and str(m).lower() != 'nan'])

                    # 最初の市区町村を選択
                    if len(self.municipalities) > 0:
                        first_muni = self.municipalities[0]
                        self.selected_municipality = first_muni

                        # フィルタ済みデータをdfに設定
                        self.df = self.df_full[
                            (self.df_full['prefecture'] == first_pref) &
                            (self.df_full['municipality'] == first_muni)
                        ].copy()
                    else:
                        self.df = filtered.copy()

                    self.filtered_rows = len(self.df)

                # 3層比較用統計の初期化
                self._init_comparison_stats()

                print(f"[CSV MODE] on_mount初期化成功")
                print(f"[INFO] 全データ: {self.total_rows:,}行, フィルタ済み: {self.filtered_rows}行")
                print(f"[INFO] 都道府県数: {len(self.prefectures)}, 市区町村数: {len(self.municipalities)}")
                print(f"[INFO] 選択: {self.selected_prefecture} {self.selected_municipality}")
                return  # CSVモード完了

            except Exception as e:
                print(f"[ERROR] CSVモード初期化失敗: {e}")

        # DB起動時ロード（軽量版）
        if _DB_AVAILABLE and not USE_CSV_MODE:
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

    def _init_comparison_stats(self):
        """3層比較用の全国・都道府県統計を初期化（on_mount時に1回のみ実行）"""
        if self.df_full is None or self.df_full.empty:
            return

        try:
            df = self.df_full

            # 全国統計の計算
            # 1. 希望勤務地数: SUMMARYのavg_desired_areasから計算（1人あたり平均希望勤務地数）
            summary = df[df['row_type'] == 'SUMMARY']
            if len(summary) > 0 and 'avg_desired_areas' in summary.columns:
                # 各市区町村の平均希望勤務地数を集計（NaNを除外）
                valid_desired = summary['avg_desired_areas'].dropna()
                national_desired = float(valid_desired.mean()) if len(valid_desired) > 0 else 0.0
            else:
                national_desired = 0.0

            # 2. 移動距離: RESIDENCE_FLOWから計算
            rf = df[df['row_type'] == 'RESIDENCE_FLOW']
            if len(rf) > 0 and 'avg_reference_distance_km' in rf.columns:
                national_distance = float(rf['avg_reference_distance_km'].mean())
            else:
                national_distance = 0.0

            # 3. 資格保有数: SUMMARYから計算
            summary = df[df['row_type'] == 'SUMMARY']
            if len(summary) > 0 and 'avg_qualifications' in summary.columns:
                national_qual = float(summary['avg_qualifications'].mean())
            else:
                national_qual = 0.0

            # 4. 性別比率: SUMMARYから計算
            national_male = 0
            national_female = 0
            if len(summary) > 0 and 'male_count' in summary.columns and 'female_count' in summary.columns:
                national_male = int(summary['male_count'].sum())
                national_female = int(summary['female_count'].sum())
            national_total = national_male + national_female
            national_female_ratio = round(national_female / national_total * 100, 1) if national_total > 0 else 0

            # 5. 年齢層分布: AGE_GENDERから計算
            age_gender = df[df['row_type'] == 'AGE_GENDER']
            age_order = ['20代', '30代', '40代', '50代', '60代', '70歳以上']
            national_age_dist = {}
            if len(age_gender) > 0 and 'category1' in age_gender.columns and 'count' in age_gender.columns:
                for age in age_order:
                    age_count = int(age_gender[age_gender['category1'] == age]['count'].sum())
                    national_age_dist[age] = age_count
            # 合計から比率を計算
            age_total = sum(national_age_dist.values())
            national_age_ratio = {}
            for age in age_order:
                if age_total > 0:
                    national_age_ratio[age] = round(national_age_dist.get(age, 0) / age_total * 100, 1)
                else:
                    national_age_ratio[age] = 0

            self.national_stats = {
                "desired_areas": round(national_desired, 1),
                "distance_km": round(national_distance, 1),
                "qualifications": round(national_qual, 2),
                "male_count": national_male,
                "female_count": national_female,
                "female_ratio": national_female_ratio,
                "age_distribution": national_age_ratio,
            }

            # 都道府県別統計の計算
            pref_stats = {}
            for pref in df['prefecture'].dropna().unique():
                pref_dap = dap[dap['prefecture'] == pref]
                pref_rf = rf[rf['prefecture'] == pref]
                pref_summary = summary[summary['prefecture'] == pref]

                # 希望勤務地数（SUMMARYのavg_desired_areasを使用 - Phase1_Applicantsから算出された正確な値）
                if len(pref_summary) > 0 and 'avg_desired_areas' in pref_summary.columns:
                    valid_desired = pref_summary['avg_desired_areas'].dropna()
                    pref_desired = float(valid_desired.mean()) if len(valid_desired) > 0 else 0.0
                else:
                    pref_desired = 0.0

                # 移動距離
                if len(pref_rf) > 0 and 'avg_reference_distance_km' in pref_rf.columns:
                    pref_distance = float(pref_rf['avg_reference_distance_km'].mean())
                else:
                    pref_distance = 0.0

                # 資格保有数
                if len(pref_summary) > 0 and 'avg_qualifications' in pref_summary.columns:
                    pref_qual = float(pref_summary['avg_qualifications'].mean())
                else:
                    pref_qual = 0.0

                # 性別比率
                pref_male = 0
                pref_female = 0
                if len(pref_summary) > 0 and 'male_count' in pref_summary.columns and 'female_count' in pref_summary.columns:
                    pref_male = int(pref_summary['male_count'].sum())
                    pref_female = int(pref_summary['female_count'].sum())
                pref_total = pref_male + pref_female
                pref_female_ratio = round(pref_female / pref_total * 100, 1) if pref_total > 0 else 0

                # 年齢層分布
                pref_age_gender = age_gender[age_gender['prefecture'] == pref]
                pref_age_dist = {}
                if len(pref_age_gender) > 0:
                    for age in age_order:
                        age_count = int(pref_age_gender[pref_age_gender['category1'] == age]['count'].sum())
                        pref_age_dist[age] = age_count
                pref_age_total = sum(pref_age_dist.values())
                pref_age_ratio = {}
                for age in age_order:
                    if pref_age_total > 0:
                        pref_age_ratio[age] = round(pref_age_dist.get(age, 0) / pref_age_total * 100, 1)
                    else:
                        pref_age_ratio[age] = 0

                pref_stats[pref] = {
                    "desired_areas": round(pref_desired, 1),
                    "distance_km": round(pref_distance, 1),
                    "qualifications": round(pref_qual, 2),
                    "male_count": pref_male,
                    "female_count": pref_female,
                    "female_ratio": pref_female_ratio,
                    "age_distribution": pref_age_ratio,
                }

            self.prefecture_stats_cache = pref_stats
            print(f"[3層比較] 全国統計初期化完了: {self.national_stats}")
            print(f"[3層比較] 都道府県統計: {len(pref_stats)}件")

        except Exception as e:
            print(f"[ERROR] 3層比較統計の初期化失敗: {e}")

    def load_from_database(self):
        """データベースからデータを読み込む（ボタン押下時・サーバーサイドフィルタリング版）

        全データをロードせず、都道府県リストと初期地域のフィルタ済みデータのみ取得。
        メモリ消費: 70MB → 0.1-1MB
        """
        print("[DEBUG] load_from_database() called!")
        print(f"[DEBUG] _DB_AVAILABLE={_DB_AVAILABLE}, USE_CSV_MODE={USE_CSV_MODE}")
        if not _DB_AVAILABLE:
            print("[ERROR] データベース機能が利用できません")
            return

        # キャッシュクリア: データベース更新後の最新データを取得するため
        clear_cache()
        print("[DEBUG] Cache cleared for fresh data load")

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
                if db_type == "csv":
                    # CSVモード: グローバルキャッシュから行数取得
                    csv_df = _load_csv_data()
                    self.total_rows = len(csv_df) if csv_df is not None else 0
                elif db_type == "turso":
                    count_df = query_df("SELECT COUNT(*) as cnt FROM job_seeker_data")
                    if not count_df.empty:
                        self.total_rows = int(count_df['cnt'].iloc[0])
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
        # 注意: .astype(str)はNaN→"nan"変換を引き起こすため、NaN以外のみ処理
        key_cols = [c for c in ['row_type', 'prefecture', 'municipality', 'category1', 'category2', 'category3'] if c in df.columns]
        for c in key_cols:
            try:
                # NaNを保持しながら文字列正規化
                mask = df[c].notna()
                df.loc[mask, c] = (
                    df.loc[mask, c]
                    .astype(str)
                    .map(lambda x: ud.normalize('NFKC', x))
                    .str.replace('\u3000', ' ', regex=False)  # 全角空白→半角
                    .str.strip()
                )
                # "nan"文字列が誤って作成された場合、NaNに戻す
                df.loc[df[c] == 'nan', c] = pd.NA
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

    def _get_prefecture_gap_data(self, prefecture: str) -> pd.DataFrame:
        """都道府県レベルのGAPデータを取得（ランキング用ヘルパー）

        サーバーサイドフィルタリングでは self.df に現在選択中の市区町村のデータしか含まれていないため、
        都道府県レベルのランキングを作成するには、都道府県全体のデータを直接DBからクエリする必要がある。

        Args:
            prefecture: 都道府県名

        Returns:
            都道府県内の全市区町村のGAPデータ（DataFrame）
        """
        # CSVアップロードモードの場合は、df_fullまたはdfから取得
        if self.csv_uploaded and self.df_full is not None:
            df_pref = self.df_full[
                (self.df_full['prefecture'] == prefecture) &
                (self.df_full['row_type'] == 'GAP')
            ].copy()
            return df_pref
        elif self.csv_uploaded and self.df is not None:
            df_pref = self.df[
                (self.df['prefecture'] == prefecture) &
                (self.df['row_type'] == 'GAP')
            ].copy()
            return df_pref

        # Turso/DBモードの場合は、都道府県全体のデータを直接クエリ
        # CSVモード対応（USE_CSV_MODE=true）
        db_type = get_db_type()

        if db_type == "csv":
            # CSVモード: グローバルキャッシュからフィルタリング
            csv_df = _load_csv_data()
            if csv_df is None or csv_df.empty:
                return pd.DataFrame()
            df_pref = csv_df[
                (csv_df['prefecture'] == prefecture) &
                (csv_df['row_type'] == 'GAP')
            ].copy()
            return self._normalize_df(df_pref)

        if not _DB_AVAILABLE:
            return pd.DataFrame()

        try:
            if db_type == "turso":
                sql = """
                    SELECT * FROM job_seeker_data
                    WHERE prefecture = ? AND row_type = 'GAP'
                """
                df_pref = query_df(sql, (prefecture,))
            else:
                sql = """
                    SELECT * FROM mapcomplete_raw
                    WHERE prefecture = ? AND row_type = 'GAP'
                """
                df_pref = query_df(sql, (prefecture,))

            return self._normalize_df(df_pref)

        except Exception as e:
            print(f"[ERROR] _get_prefecture_gap_data failed: {e}")
            return pd.DataFrame()

    def _get_prefecture_pattern_data(self, prefecture: str, row_type: str) -> pd.DataFrame:
        """都道府県レベルのパターンデータを取得（DESIRED_AREA_PATTERN, RESIDENCE_FLOW用）

        サーバーサイドフィルタリングでは self.df に現在選択中の市区町村のデータしか含まれていないため、
        都道府県レベルのパターン分析には、都道府県全体のデータを直接DBからクエリする必要がある。

        Args:
            prefecture: 都道府県名
            row_type: 'DESIRED_AREA_PATTERN' or 'RESIDENCE_FLOW'

        Returns:
            都道府県内の全パターンデータ（DataFrame）
        """
        # CSVアップロードモードの場合は、df_fullまたはdfから取得
        if self.csv_uploaded and self.df_full is not None:
            df_pref = self.df_full[
                (self.df_full['prefecture'] == prefecture) &
                (self.df_full['row_type'] == row_type)
            ].copy()
            return df_pref
        elif self.csv_uploaded and self.df is not None:
            # フィルタなしで全データを検索
            if 'row_type' not in self.df.columns:
                return pd.DataFrame()
            df_pref = self.df[self.df['row_type'] == row_type].copy()
            return df_pref

        # Turso/DBモードの場合は、都道府県全体のデータを直接クエリ
        # CSVモード対応（USE_CSV_MODE=true）
        db_type = get_db_type()

        if db_type == "csv":
            # CSVモード: グローバルキャッシュからフィルタリング
            csv_df = _load_csv_data()
            if csv_df is None or csv_df.empty:
                return pd.DataFrame()
            df_pref = csv_df[
                (csv_df['prefecture'] == prefecture) &
                (csv_df['row_type'] == row_type)
            ].copy()
            return self._normalize_df(df_pref)

        if not _DB_AVAILABLE:
            return pd.DataFrame()

        try:
            if db_type == "turso":
                sql = """
                    SELECT * FROM job_seeker_data
                    WHERE prefecture = ? AND row_type = ?
                """
                df_pref = query_df(sql, (prefecture, row_type))
            else:
                sql = """
                    SELECT * FROM mapcomplete_raw
                    WHERE prefecture = ? AND row_type = ?
                """
                df_pref = query_df(sql, (prefecture, row_type))

            return self._normalize_df(df_pref)

        except Exception as e:
            print(f"[ERROR] _get_prefecture_pattern_data failed: {e}")
            return pd.DataFrame()

    def _get_target_pattern_data(self, prefecture: str, municipality: str, row_type: str) -> pd.DataFrame:
        """ターゲット視点でパターンデータを取得（選択市町村を希望する人のデータ）

        従来の「municipality==選択市町村」ではなく、
        「co_desired_municipality==選択市町村」または「desired_municipality==選択市町村」で取得。
        つまり「選択市町村を希望する人が、他にどこを希望しているか／どこに住んでいるか」を返す。

        Args:
            prefecture: 都道府県名
            municipality: 市区町村名
            row_type: 'DESIRED_AREA_PATTERN' or 'RESIDENCE_FLOW'

        Returns:
            選択市町村を希望する人のパターンデータ（DataFrame）
        """
        # フィルタ用のカラム名を決定
        if row_type == 'DESIRED_AREA_PATTERN':
            target_col = 'co_desired_municipality'
            target_pref_col = 'co_desired_prefecture'
        elif row_type == 'RESIDENCE_FLOW':
            target_col = 'desired_municipality'
            target_pref_col = 'desired_prefecture'
        else:
            return pd.DataFrame()

        # CSVアップロードモードの場合
        if self.csv_uploaded and self.df_full is not None:
            # まず市区町村レベルで検索
            df_target = self.df_full[
                (self.df_full[target_pref_col] == prefecture) &
                (self.df_full[target_col] == municipality) &
                (self.df_full['row_type'] == row_type)
            ].copy()
            return df_target
        elif self.csv_uploaded and self.df is not None:
            df_target = self.df[
                (self.df[target_col] == municipality) &
                (self.df['row_type'] == row_type)
            ].copy()
            return df_target

        # Turso/DBモードの場合
        # CSVモード対応（USE_CSV_MODE=true）
        db_type = get_db_type()

        if db_type == "csv":
            # CSVモード: グローバルキャッシュからフィルタリング
            csv_df = _load_csv_data()
            if csv_df is None or csv_df.empty:
                return pd.DataFrame()
            df_target = csv_df[
                (csv_df[target_pref_col] == prefecture) &
                (csv_df[target_col] == municipality) &
                (csv_df['row_type'] == row_type)
            ].copy()
            return self._normalize_df(df_target)

        if not _DB_AVAILABLE:
            return pd.DataFrame()

        try:
            table_name = "job_seeker_data" if db_type == "turso" else "mapcomplete_raw"

            sql = f"""
                SELECT * FROM {table_name}
                WHERE {target_pref_col} = ? AND {target_col} = ? AND row_type = ?
            """
            df_target = query_df(sql, (prefecture, municipality, row_type))
            return self._normalize_df(df_target)

        except Exception as e:
            print(f"[ERROR] _get_target_pattern_data failed: {e}")
            return pd.DataFrame()

    def _get_target_prefecture_pattern_data(self, prefecture: str, row_type: str) -> pd.DataFrame:
        """ターゲット視点で都道府県全体のパターンデータを取得（フォールバック用）

        「co_desired_prefecture==選択都道府県」または「desired_prefecture==選択都道府県」で取得。

        Args:
            prefecture: 都道府県名
            row_type: 'DESIRED_AREA_PATTERN' or 'RESIDENCE_FLOW'

        Returns:
            選択都道府県を希望する人のパターンデータ（DataFrame）
        """
        if row_type == 'DESIRED_AREA_PATTERN':
            target_pref_col = 'co_desired_prefecture'
        elif row_type == 'RESIDENCE_FLOW':
            target_pref_col = 'desired_prefecture'
        else:
            return pd.DataFrame()

        # CSVアップロードモードの場合
        if self.csv_uploaded and self.df_full is not None:
            df_target = self.df_full[
                (self.df_full[target_pref_col] == prefecture) &
                (self.df_full['row_type'] == row_type)
            ].copy()
            return df_target
        elif self.csv_uploaded and self.df is not None:
            if 'row_type' not in self.df.columns:
                return pd.DataFrame()
            df_target = self.df[self.df['row_type'] == row_type].copy()
            return df_target

        # Turso/DBモードの場合
        # CSVモード対応（USE_CSV_MODE=true）
        db_type = get_db_type()

        if db_type == "csv":
            # CSVモード: グローバルキャッシュからフィルタリング
            csv_df = _load_csv_data()
            if csv_df is None or csv_df.empty:
                return pd.DataFrame()
            df_target = csv_df[
                (csv_df[target_pref_col] == prefecture) &
                (csv_df['row_type'] == row_type)
            ].copy()
            return self._normalize_df(df_target)

        if not _DB_AVAILABLE:
            return pd.DataFrame()

        try:
            table_name = "job_seeker_data" if db_type == "turso" else "mapcomplete_raw"

            sql = f"""
                SELECT * FROM {table_name}
                WHERE {target_pref_col} = ? AND row_type = ?
            """
            df_target = query_df(sql, (prefecture, row_type))
            return self._normalize_df(df_target)

        except Exception as e:
            print(f"[ERROR] _get_target_prefecture_pattern_data failed: {e}")
            return pd.DataFrame()

    def _get_source_pattern_data(self, prefecture: str, municipality: str, row_type: str) -> pd.DataFrame:
        """ソース視点でパターンデータを取得（選択市町村に住んでいる人のデータ）

        従来の _get_target_pattern_data とは逆で、
        「prefecture==選択都道府県」AND「municipality前方一致」でフィルタ。
        つまり「選択市町村に住んでいる人が、他にどこを希望しているか」を返す。

        注意: DESIRED_AREA_PATTERN等のデータでは市区町村名が「京都市中京区」のように
        区名付きで格納されている場合があるため、前方一致でフィルタリングする。

        Args:
            prefecture: 都道府県名
            municipality: 市区町村名
            row_type: 'DESIRED_AREA_PATTERN' or 'RESIDENCE_FLOW'

        Returns:
            選択市町村に住んでいる人のパターンデータ（DataFrame）
        """
        # CSVアップロードモードの場合
        if self.csv_uploaded and self.df_full is not None:
            # 前方一致でフィルタリング（「京都市」→「京都市中京区」等にマッチ）
            df_source = self.df_full[
                (self.df_full['prefecture'] == prefecture) &
                (self.df_full['municipality'].astype(str).str.startswith(municipality)) &
                (self.df_full['row_type'] == row_type)
            ].copy()
            return df_source
        elif self.csv_uploaded and self.df is not None:
            df_source = self.df[
                (self.df['prefecture'] == prefecture) &
                (self.df['municipality'].astype(str).str.startswith(municipality)) &
                (self.df['row_type'] == row_type)
            ].copy()
            return df_source

        # CSVモード対応（USE_CSV_MODE=true）
        db_type = get_db_type()

        if db_type == "csv":
            # CSVモード: グローバルキャッシュからフィルタリング
            csv_df = _load_csv_data()
            if csv_df is None or csv_df.empty:
                return pd.DataFrame()
            # 前方一致でフィルタリング（「京都市」→「京都市中京区」等にマッチ）
            df_source = csv_df[
                (csv_df['prefecture'] == prefecture) &
                (csv_df['municipality'].astype(str).str.startswith(municipality)) &
                (csv_df['row_type'] == row_type)
            ].copy()
            return self._normalize_df(df_source)

        # Turso/DBモードの場合
        if not _DB_AVAILABLE:
            return pd.DataFrame()

        try:
            table_name = "job_seeker_data" if db_type == "turso" else "mapcomplete_raw"

            # 前方一致でフィルタリング（LIKE 'xxx%'）
            sql = f"""
                SELECT * FROM {table_name}
                WHERE prefecture = ? AND municipality LIKE ? AND row_type = ?
            """
            df_source = query_df(sql, (prefecture, f"{municipality}%", row_type))
            return self._normalize_df(df_source)

        except Exception as e:
            print(f"[ERROR] _get_source_pattern_data failed: {e}")
            return pd.DataFrame()

    def _get_source_prefecture_pattern_data(self, prefecture: str, row_type: str) -> pd.DataFrame:
        """ソース視点で都道府県全体のパターンデータを取得（フォールバック用）

        「prefecture==選択都道府県」でフィルタ（municipalityは問わない）。

        Args:
            prefecture: 都道府県名
            row_type: 'DESIRED_AREA_PATTERN' or 'RESIDENCE_FLOW'

        Returns:
            選択都道府県に住んでいる人のパターンデータ（DataFrame）
        """
        # CSVアップロードモードの場合
        if self.csv_uploaded and self.df_full is not None:
            df_source = self.df_full[
                (self.df_full['prefecture'] == prefecture) &
                (self.df_full['row_type'] == row_type)
            ].copy()
            return df_source
        elif self.csv_uploaded and self.df is not None:
            df_source = self.df[
                (self.df['prefecture'] == prefecture) &
                (self.df['row_type'] == row_type)
            ].copy()
            return df_source

        # CSVモード対応（USE_CSV_MODE=true）
        db_type = get_db_type()

        if db_type == "csv":
            # CSVモード: グローバルキャッシュからフィルタリング
            csv_df = _load_csv_data()
            if csv_df is None or csv_df.empty:
                return pd.DataFrame()
            df_source = csv_df[
                (csv_df['prefecture'] == prefecture) &
                (csv_df['row_type'] == row_type)
            ].copy()
            return self._normalize_df(df_source)

        # Turso/DBモードの場合
        if not _DB_AVAILABLE:
            return pd.DataFrame()

        try:
            table_name = "job_seeker_data" if db_type == "turso" else "mapcomplete_raw"

            sql = f"""
                SELECT * FROM {table_name}
                WHERE prefecture = ? AND row_type = ?
            """
            df_source = query_df(sql, (prefecture, row_type))
            return self._normalize_df(df_source)

        except Exception as e:
            print(f"[ERROR] _get_source_prefecture_pattern_data failed: {e}")
            return pd.DataFrame()

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
                    self.prefectures = _sort_prefectures_by_jis(self.df['prefecture'].dropna().unique().tolist())
                    # 最初の都道府県を自動選択して市区町村リストも初期化
                    if len(self.prefectures) > 0:
                        first_pref = self.prefectures[0]
                        self.selected_prefecture = first_pref

                        # 市区町村リスト初期化（空文字列や"nan"を除外）
                        if 'municipality' in self.df.columns:
                            filtered = self.df[self.df['prefecture'] == first_pref]
                            muni_list = filtered['municipality'].dropna().unique().tolist()
                            self.municipalities = sorted([m for m in muni_list if m and str(m).lower() != 'nan'])

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
            # CSV全データから市区町村リストを抽出（空文字列や"nan"を除外）
            if 'municipality' in self.df_full.columns:
                filtered = self.df_full[self.df_full['prefecture'] == value]
                muni_list = filtered['municipality'].dropna().unique().tolist()
                self.municipalities = sorted([m for m in muni_list if m and str(m).lower() != 'nan'])

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
            # CSV使用時の従来ロジック（フォールバック・空文字列や"nan"を除外）
            if self.df is not None and 'municipality' in self.df.columns:
                filtered = self.df[self.df['prefecture'] == value]
                muni_list = filtered['municipality'].dropna().unique().tolist()
                self.municipalities = sorted([m for m in muni_list if m and str(m).lower() != 'nan'])

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

    def set_age_gender_view_mode(self, mode: str):
        """年齢×性別分析の表示モード切り替え

        Args:
            mode: "destination"（希望勤務地ベース）または "residence"（居住地ベース）
        """
        if mode in ("destination", "residence"):
            self.age_gender_view_mode = mode

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
        summary_rows = self._safe_filter_df_by_row_type(filtered, 'SUMMARY')
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
        summary_rows = self._safe_filter_df_by_row_type(filtered, 'SUMMARY')
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
        summary_rows = self._safe_filter_df_by_row_type(filtered, 'SUMMARY')
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
        age_gender_rows = self._safe_filter_df_by_row_type(filtered, 'AGE_GENDER')
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
                    for r in grouped.to_dict("records")
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
                result = [{"name": str(r['label']), "value": float(r['value'])} for r in grouped.to_dict("records")]
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
                result = [{"name": str(r['municipality']), "value": float(r['ratio'])} for r in grouped.to_dict("records")]
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
                    for r in grouped.to_dict("records")
                ]
                return result
            except Exception:
                pass

        # row_type='AGE_GENDER'のデータを抽出
        age_gender_rows = self._safe_filter_df_by_row_type(filtered, 'AGE_GENDER')
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

    @rx.var(cache=False)
    def overview_age_gender_residence_data(self) -> List[Dict[str, Any]]:
        """概要: 年齢×性別グラフデータ（居住地ベース版・Rechartsリスト形式）

        AGE_GENDER_RESIDENCEを使用。選択した市区町村に「住んでいる人」の年齢×性別分布。
        労働力供給分析向け。
        """
        # 依存: selected_prefecture, selected_municipality
        _ = self.selected_prefecture
        _ = self.selected_municipality

        if self.df is None or not self.is_loaded:
            return []

        filtered = self._get_filtered_df()
        if filtered.empty:
            return []

        # AGE_GENDER_RESIDENCEデータを使用（居住地ベース）
        age_gender_rows = self._safe_filter_df_by_row_type(filtered, 'AGE_GENDER_RESIDENCE')
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

        return []

    @rx.var(cache=False)
    def overview_age_gender_current_data(self) -> List[Dict[str, Any]]:
        """概要: 年齢×性別グラフデータ（現在の表示モードに応じて切替）

        age_gender_view_modeに基づき適切なデータを返す：
        - "destination": AGE_GENDER（希望勤務地ベース＝採用ターゲット向け）
        - "residence": AGE_GENDER_RESIDENCE（居住地ベース＝労働力供給分析向け）
        """
        _ = self.age_gender_view_mode  # 依存を明示
        if self.age_gender_view_mode == "residence":
            return self.overview_age_gender_residence_data
        return self.overview_age_gender_data

    @rx.var(cache=False)
    def age_gender_view_label(self) -> str:
        """年齢×性別グラフの現在の表示モードラベル"""
        _ = self.age_gender_view_mode
        if self.age_gender_view_mode == "residence":
            return "居住地ベース（この地域に住んでいる人）"
        return "希望勤務地ベース（この地域で働きたい人）"

    @rx.var(cache=False)
    def has_residence_data(self) -> bool:
        """AGE_GENDER_RESIDENCEデータが存在するか"""
        if self.df is None or not self.is_loaded:
            return False
        filtered = self._get_filtered_df()
        if filtered.empty:
            return False
        residence_rows = self._safe_filter_df_by_row_type(filtered, 'AGE_GENDER_RESIDENCE')
        return not residence_rows.empty

    def _get_filtered_df(self) -> pd.DataFrame:
        """フィルタ適用後のDataFrameを取得（サーバーサイドフィルタリング版）

        サーバーサイドフィルタリングでは、self.dfは既に選択地域のデータのみを含むため、
        追加のフィルタリングは不要。そのまま返す。
        """
        if self.df is None or self.df.empty:
            return pd.DataFrame()

        # サーバーサイドフィルタリング: dfは既にフィルタ済み
        return self.df

    def _safe_filter_by_row_type(self, row_type: str, copy: bool = False) -> pd.DataFrame:
        """row_typeでDataFrameを安全にフィルタリングするヘルパー

        row_typeカラムが存在しない場合は空のDataFrameを返す。

        Args:
            row_type: フィルタリングするrow_type値
            copy: Trueの場合、.copy()を呼び出して独立したDataFrameを返す

        Returns:
            フィルタリングされたDataFrame（row_typeがない場合は空のDataFrame）
        """
        if self.df is None or self.df.empty:
            return pd.DataFrame()
        if 'row_type' not in self.df.columns:
            return pd.DataFrame()
        result = self.df[self.df['row_type'] == row_type]
        return result.copy() if copy else result

    @staticmethod
    def _safe_filter_df_by_row_type(df: pd.DataFrame, row_type: str) -> pd.DataFrame:
        """任意のDataFrameからrow_typeで安全にフィルタリングするスタティックヘルパー

        row_typeカラムが存在しない場合は空のDataFrameを返す。

        Args:
            df: フィルタリング対象のDataFrame
            row_type: フィルタリングするrow_type値

        Returns:
            フィルタリングされたDataFrame（row_typeがない場合は空のDataFrame）
        """
        if df is None or df.empty:
            return pd.DataFrame()
        if 'row_type' not in df.columns:
            return pd.DataFrame()
        return df[df['row_type'] == row_type]

    # =====================================
    # 頻出フィルタのキャッシュ化ヘルパー（サーバーサイドフィルタリング版）
    # dfは既にフィルタ済みなので、row_typeフィルタのみ実行
    # =====================================

    @rx.var(cache=False)
    def _cached_persona_muni_filtered(self) -> pd.DataFrame:
        """PERSONA_MUNIフィルタ結果（キャッシュ無効化で常に最新データ）"""
        if self.df is None or self.df.empty:
            return pd.DataFrame()
        if 'row_type' not in self.df.columns:
            return pd.DataFrame()

        # サーバーサイドフィルタリング: dfは既に地域でフィルタ済み、row_typeのみフィルタ
        return self.df[self.df['row_type'] == 'PERSONA_MUNI']

    @rx.var(cache=False)
    def _cached_employment_age_filtered(self) -> pd.DataFrame:
        """EMPLOYMENT_AGE_CROSSフィルタ結果（キャッシュ無効化で常に最新データ）"""
        if self.df is None or self.df.empty:
            return pd.DataFrame()
        if 'row_type' not in self.df.columns:
            return pd.DataFrame()

        # サーバーサイドフィルタリング: dfは既に地域でフィルタ済み、row_typeのみフィルタ
        return self.df[self.df['row_type'] == 'EMPLOYMENT_AGE_CROSS']

    # _cached_urgency_age_filtered() 削除済み（URGENCY_AGE廃止により不要）

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
        summary_rows = self._safe_filter_df_by_row_type(filtered, 'SUMMARY')
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

        summary_rows = self._safe_filter_df_by_row_type(filtered, 'SUMMARY')
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
        形式: [{"name": "男性", "value": 1500, "fill": "#0072B2"}, {"name": "女性", "value": 2000, "fill": "#E69F00"}]
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
        summary_rows = self._safe_filter_df_by_row_type(filtered, 'SUMMARY')
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

        # AGE_GENDERから年齢層ごとに男女合計
        age_gender_rows = self._safe_filter_df_by_row_type(filtered, 'AGE_GENDER')
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

        # サーバーサイドフィルタリング: dfは既に地域でフィルタ済み、row_typeのみフィルタ
        filtered = self._safe_filter_by_row_type('PERSONA_MUNI', copy=True)

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
                    for r in grouped.to_dict("records")
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
        for row in grouped.to_dict("records"):
            result.append({
                "name": str(row['name']),
                "avg_qual": float(row['avg_qual'])
            })

        return result

    @rx.var(cache=False)
    def desired_area_pattern_top_muni(self) -> List[Dict[str, Any]]:
        """併願パターン: 選択市町村に住んでいる人の併願希望先Top10

        【ソース視点】選択市町村に住んでいる人が、他にどこを併願希望しているか
        row_type=DESIRED_AREA_PATTERN, prefecture/municipality==選択市町村 でフィルタ
        集計対象: co_desired_municipality（併願希望先市町村）
        """
        if not self.is_loaded:
            return []

        prefecture = self.selected_prefecture
        municipality = self.selected_municipality
        if not prefecture:
            return []

        # ソース視点でデータを取得（選択市町村に住んでいる人）
        if municipality:
            filtered = self._get_source_pattern_data(prefecture, municipality, 'DESIRED_AREA_PATTERN')
        else:
            filtered = pd.DataFrame()

        # 市区町村データがない場合は都道府県レベルにフォールバック
        is_fallback = False
        if filtered.empty:
            filtered = self._get_source_prefecture_pattern_data(prefecture, 'DESIRED_AREA_PATTERN')
            is_fallback = True

        if filtered.empty:
            return []

        needed = {'co_desired_prefecture', 'co_desired_municipality', 'count'}
        if not needed.issubset(filtered.columns):
            return []

        # 選択市町村に住んでいる人の、併願希望先（co_desired_municipality）を集計
        # 都道府県も含めてラベルを作成
        filtered['label'] = filtered['co_desired_prefecture'].astype(str) + ' ' + filtered['co_desired_municipality'].astype(str)
        agg = (
            filtered
            .groupby('label')['count']
            .sum()
            .reset_index()
            .sort_values('count', ascending=False)
            .head(10)
        )

        result = []
        for row in agg.to_dict("records"):
            label = str(row['label'])
            if is_fallback:
                label = f"【県】{label}"
            result.append({
                "label": label,
                "value": int(row['count'])
            })
        return result

    # =====================================
    # セクション3-1: 年齢×性別×併願パターン分析
    # =====================================

    @rx.var(cache=False)
    def desired_area_by_age(self) -> List[Dict[str, Any]]:
        """年齢層別の併願希望先（積み上げ横棒グラフ用）

        形式: [{"age": "20代", "locations": [{"name": "東京都 新宿区", "value": 10}, ...]}, ...]
        データソース: row_type='DESIRED_AREA_PATTERN', category1=年齢層
        """
        if not self.is_loaded or self.df is None:
            return []

        # DESIRED_AREA_PATTERNを取得
        filtered = self._safe_filter_by_row_type('DESIRED_AREA_PATTERN', copy=True)
        if filtered.empty:
            return []

        # 市区町村でフィルタ（選択された市区町村 or 都道府県全体）
        selected_muni = self.selected_municipality
        selected_pref = self.selected_prefecture

        if selected_muni and selected_muni != "すべて":
            filtered = filtered[filtered['municipality'] == selected_muni]
        elif selected_pref and selected_pref != "すべて":
            filtered = filtered[filtered['prefecture'] == selected_pref]

        if filtered.empty:
            return []

        # 年齢層別に集計
        age_groups = ["20代", "30代", "40代", "50代", "60代"]
        result = []

        for age in age_groups:
            age_data = filtered[filtered['category1'] == age]
            if age_data.empty:
                continue

            # 併願先を集計（copyを作って操作）
            age_data = age_data.copy()
            age_data['label'] = age_data['co_desired_prefecture'].astype(str) + ' ' + age_data['co_desired_municipality'].astype(str)
            agg = (
                age_data
                .groupby('label')['count']
                .sum()
                .reset_index()
                .sort_values('count', ascending=False)
                .head(5)
            )

            locations = [
                {"name": str(row['label']), "value": int(row['count'])}
                for row in agg.to_dict("records")
            ]

            if locations:
                result.append({
                    "age": age,
                    "locations": locations,
                    "total": sum(loc["value"] for loc in locations)
                })

        return result

    @rx.var(cache=False)
    def desired_area_by_gender(self) -> Dict[str, List[Dict[str, Any]]]:
        """性別別の併願希望先Top5

        形式: {"男性": [{"name": "東京都 新宿区", "value": 10}, ...], "女性": [...]}
        データソース: row_type='DESIRED_AREA_PATTERN', category2=性別
        """
        if not self.is_loaded or self.df is None:
            return {"男性": [], "女性": []}

        # DESIRED_AREA_PATTERNを取得
        filtered = self._safe_filter_by_row_type('DESIRED_AREA_PATTERN', copy=True)
        if filtered.empty:
            return {"男性": [], "女性": []}

        # 市区町村でフィルタ
        selected_muni = self.selected_municipality
        selected_pref = self.selected_prefecture

        if selected_muni and selected_muni != "すべて":
            filtered = filtered[filtered['municipality'] == selected_muni]
        elif selected_pref and selected_pref != "すべて":
            filtered = filtered[filtered['prefecture'] == selected_pref]

        if filtered.empty:
            return {"男性": [], "女性": []}

        result = {}
        for gender in ["男性", "女性"]:
            gender_data = filtered[filtered['category2'] == gender]
            if gender_data.empty:
                result[gender] = []
                continue

            # 併願先を集計（市区町村名のみ、短縮表示）
            gender_data = gender_data.copy()
            gender_data['label'] = gender_data['co_desired_municipality'].astype(str)
            agg = (
                gender_data
                .groupby('label')['count']
                .sum()
                .reset_index()
                .sort_values('count', ascending=False)
                .head(5)
            )

            result[gender] = [
                {"name": str(row['label']), "value": int(row['count'])}
                for row in agg.to_dict("records")
            ]

        return result

    @rx.var(cache=False)
    def desired_area_male(self) -> List[Dict[str, Any]]:
        """男性の併願希望先Top5（別varとして分離）"""
        data = self.desired_area_by_gender
        return data.get("男性", [])

    @rx.var(cache=False)
    def desired_area_female(self) -> List[Dict[str, Any]]:
        """女性の併願希望先Top5（別varとして分離）"""
        data = self.desired_area_by_gender
        return data.get("女性", [])

    # =====================================
    # 人材フロー分析（流入・地元・流出）
    # =====================================

    @rx.var(cache=False)
    def talent_flow_inflow(self) -> Dict[str, Any]:
        """流入データ: 選択市区町村への就職希望者（どこから来るか）

        Returns:
            {
                "total": 総数,
                "local_count": 地元志向数,
                "local_pct": 地元志向率,
                "top_sources": [{"name": "前橋市", "value": 621, "is_local": False}, ...]
            }
        """
        # 流入分析には全データが必要（df_fullを使用）
        # dfはフィルタ済みのため、他県からの流入データが欠落する
        if self.df_full is None or self.df_full.empty:
            return {"total": 0, "local_count": 0, "local_pct": 0, "top_sources": []}

        # df_fullから直接DESIRED_AREA_PATTERNをフィルタ
        if 'row_type' not in self.df_full.columns:
            return {"total": 0, "local_count": 0, "local_pct": 0, "top_sources": []}
        filtered = self.df_full[self.df_full['row_type'] == 'DESIRED_AREA_PATTERN'].copy()
        if filtered.empty:
            return {"total": 0, "local_count": 0, "local_pct": 0, "top_sources": []}

        selected_muni = self.selected_municipality
        selected_pref = self.selected_prefecture

        # 希望地（co_desired_municipality）でフィルタ
        if selected_muni and selected_muni != "すべて":
            inflow = filtered[filtered['co_desired_municipality'] == selected_muni]
        elif selected_pref and selected_pref != "すべて":
            inflow = filtered[filtered['co_desired_prefecture'] == selected_pref]
        else:
            return {"total": 0, "local_count": 0, "local_pct": 0, "top_sources": []}

        if inflow.empty:
            return {"total": 0, "local_count": 0, "local_pct": 0, "top_sources": []}

        # 総数
        total = int(inflow['count'].sum())

        # 地元志向（居住地 = 希望地）
        if selected_muni and selected_muni != "すべて":
            local_data = inflow[inflow['municipality'] == selected_muni]
        else:
            local_data = inflow[inflow['prefecture'] == selected_pref]

        local_count = int(local_data['count'].sum()) if not local_data.empty else 0
        local_pct = round(local_count / total * 100, 1) if total > 0 else 0

        # 流入元Top5（居住地別集計）
        agg = (
            inflow
            .groupby('municipality')['count']
            .sum()
            .reset_index()
            .sort_values('count', ascending=False)
            .head(7)
        )

        top_sources = []
        for _, row in agg.iterrows():
            muni_name = str(row['municipality'])
            is_local = (selected_muni and muni_name == selected_muni)
            top_sources.append({
                "name": muni_name,
                "value": int(row['count']),
                "is_local": is_local
            })

        return {
            "total": total,
            "local_count": local_count,
            "local_pct": local_pct,
            "top_sources": top_sources
        }

    @rx.var(cache=False)
    def talent_flow_inflow_total(self) -> int:
        """流入総数"""
        return self.talent_flow_inflow.get("total", 0)

    @rx.var(cache=False)
    def talent_flow_local_count(self) -> int:
        """地元志向数"""
        return self.talent_flow_inflow.get("local_count", 0)

    @rx.var(cache=False)
    def talent_flow_local_pct(self) -> float:
        """地元志向率"""
        return self.talent_flow_inflow.get("local_pct", 0.0)

    @rx.var(cache=False)
    def talent_flow_inflow_sources(self) -> List[Dict[str, Any]]:
        """流入元Top（Rechartsバーグラフ用）"""
        return self.talent_flow_inflow.get("top_sources", [])

    @rx.var(cache=False)
    def talent_flow_outflow(self) -> Dict[str, Any]:
        """流出データ: 選択市区町村在住者の希望先（どこへ流れるか）

        Returns:
            {
                "total": 総数,
                "top_destinations": [{"name": "東京都", "value": 25}, ...]
            }
        """
        # 流出分析には全データが必要（df_fullを使用）
        # dfはフィルタ済みのため、他県への流出データが欠落する
        if self.df_full is None or self.df_full.empty:
            return {"total": 0, "top_destinations": []}

        # df_fullから直接DESIRED_AREA_PATTERNをフィルタ
        if 'row_type' not in self.df_full.columns:
            return {"total": 0, "top_destinations": []}
        filtered = self.df_full[self.df_full['row_type'] == 'DESIRED_AREA_PATTERN'].copy()
        if filtered.empty:
            return {"total": 0, "top_destinations": []}

        selected_muni = self.selected_municipality
        selected_pref = self.selected_prefecture

        # 居住地（municipality）でフィルタ
        if selected_muni and selected_muni != "すべて":
            outflow = filtered[filtered['municipality'] == selected_muni]
        elif selected_pref and selected_pref != "すべて":
            outflow = filtered[filtered['prefecture'] == selected_pref]
        else:
            return {"total": 0, "top_destinations": []}

        if outflow.empty:
            return {"total": 0, "top_destinations": []}

        # 地元を除外（流出のみカウント）
        if selected_muni and selected_muni != "すべて":
            outflow_only = outflow[outflow['co_desired_municipality'] != selected_muni]
        else:
            outflow_only = outflow[outflow['co_desired_prefecture'] != selected_pref]

        total = int(outflow_only['count'].sum())

        # 流出先Top5
        agg = (
            outflow_only
            .groupby('co_desired_municipality')['count']
            .sum()
            .reset_index()
            .sort_values('count', ascending=False)
            .head(5)
        )

        top_destinations = [
            {"name": str(row['co_desired_municipality']), "value": int(row['count'])}
            for _, row in agg.iterrows()
        ]

        return {
            "total": total,
            "top_destinations": top_destinations
        }

    @rx.var(cache=False)
    def talent_flow_outflow_total(self) -> int:
        """流出総数"""
        return self.talent_flow_outflow.get("total", 0)

    @rx.var(cache=False)
    def talent_flow_outflow_destinations(self) -> List[Dict[str, Any]]:
        """流出先Top（Rechartsバーグラフ用）"""
        return self.talent_flow_outflow.get("top_destinations", [])

    @rx.var(cache=False)
    def talent_flow_ratio(self) -> str:
        """流入/流出比（人材吸引力）"""
        inflow = self.talent_flow_inflow_total
        outflow = self.talent_flow_outflow_total
        if outflow == 0:
            if inflow > 0:
                return "∞（流出なし）"
            return "-"
        ratio = inflow / outflow
        return f"{ratio:.1f}倍"

    @rx.var(cache=False)
    def talent_flow_has_data(self) -> bool:
        """人材フローデータが存在するか"""
        return self.talent_flow_inflow_total > 0 or self.talent_flow_outflow_total > 0

    @rx.var(cache=False)
    def desired_area_age_gender_heatmap_html(self) -> str:
        """年齢×希望地域のヒートマップ（Plotly HTML）

        X軸: 希望地域（Top8）- 短縮表示
        Y軸: 年齢層
        色分け: 人数（濃いほど多い）
        """
        if not self.is_loaded or self.df is None:
            return ""

        # DESIRED_AREA_PATTERNを取得
        filtered = self._safe_filter_by_row_type('DESIRED_AREA_PATTERN', copy=True)
        if filtered.empty:
            return ""

        # 市区町村でフィルタ
        selected_muni = self.selected_municipality
        selected_pref = self.selected_prefecture

        if selected_muni and selected_muni != "すべて":
            filtered = filtered[filtered['municipality'] == selected_muni]
        elif selected_pref and selected_pref != "すべて":
            filtered = filtered[filtered['prefecture'] == selected_pref]

        if filtered.empty:
            return ""

        # 希望地域ラベルを作成（市区町村名のみ）
        filtered = filtered.copy()
        filtered['dest_label'] = filtered['co_desired_municipality'].astype(str)

        # Top8の希望地域を特定（表示スペースのため8に削減）
        top_destinations = (
            filtered
            .groupby('dest_label')['count']
            .sum()
            .reset_index()
            .sort_values('count', ascending=False)
            .head(8)['dest_label']
            .tolist()
        )

        if not top_destinations:
            return ""

        # ラベルを短縮（8文字以上は省略）
        short_labels = [d[:8] + "…" if len(d) > 8 else d for d in top_destinations]

        # 年齢層
        age_groups = ["20代", "30代", "40代", "50代", "60代"]

        # ヒートマップ用のマトリックスを作成
        z_values = []
        for age in age_groups:
            row_values = []
            for dest in top_destinations:
                count = filtered[
                    (filtered['category1'] == age) &
                    (filtered['dest_label'] == dest)
                ]['count'].sum()
                row_values.append(int(count) if pd.notna(count) else 0)
            z_values.append(row_values)

        # Plotlyヒートマップ作成
        fig = go.Figure(data=go.Heatmap(
            z=z_values,
            x=short_labels,
            y=age_groups,
            colorscale='Blues',
            hoverongaps=False,
            hovertemplate='希望地域: %{x}<br>年齢層: %{y}<br>人数: %{z}人<extra></extra>'
        ))

        fig.update_layout(
            xaxis=dict(
                tickangle=-45,
                tickfont=dict(color='#94a3b8', size=11),
                side='bottom'
            ),
            yaxis=dict(
                tickfont=dict(color='#94a3b8', size=11),
                autorange='reversed'
            ),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=50, r=20, t=10, b=80),
            height=280
        )

        return fig.to_html(full_html=False, include_plotlyjs='cdn')

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

        # サーバーサイドフィルタリング: dfは既に地域でフィルタ済み、row_typeのみフィルタ
        filtered = self._safe_filter_by_row_type('EMPLOYMENT_AGE_CROSS', copy=True)

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
                    for r in grouped.to_dict("records")
                ]
                return result
            except Exception:
                pass

        # ピボットテーブル形式に変換: 年齢層 × 就業ステータス
        pivot_data = {}
        for row in filtered.to_dict("records"):
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
        filtered = self._safe_filter_by_row_type('EMPLOYMENT_AGE_CROSS', copy=True)

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
        filtered = self._safe_filter_by_row_type('EMPLOYMENT_AGE_CROSS', copy=True)

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
        filtered = self._safe_filter_by_row_type('URGENCY_AGE', copy=True)

        if filtered.empty:
            return []

        # category2が年齢帯、countが人数、avg_urgency_scoreが平均スコア
        result = []
        for row in filtered.to_dict("records"):
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
        filtered = self._safe_filter_by_row_type('URGENCY_EMPLOYMENT', copy=True)

        if filtered.empty:
            return []

        # category2が就業ステータス、countが人数、avg_urgency_scoreが平均スコア
        result = []
        for row in filtered.to_dict("records"):
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
        filtered = self._safe_filter_by_row_type('URGENCY_AGE')

        total = filtered['count'].sum() if not filtered.empty else 0
        return f"{int(total):,}"

    @rx.var(cache=False)
    def urgency_avg_score(self) -> str:
        """緊急度: 平均スコア（加重平均）"""
        if not self.is_loaded or self.df is None:
            return "0.0"

        df = self.df

        # サーバーサイドフィルタリング: dfは既に地域でフィルタ済み、row_typeのみフィルタ
        filtered = self._safe_filter_by_row_type('URGENCY_AGE', copy=True)

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
        filtered = self._safe_filter_by_row_type('FLOW')

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
        filtered = self._safe_filter_by_row_type('FLOW')

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
        filtered = self._safe_filter_by_row_type('FLOW')

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
        filtered = self._safe_filter_by_row_type('PERSONA_MUNI', copy=True)

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
        for row in top_personas.to_dict("records"):
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
        filtered = self._safe_filter_by_row_type('PERSONA_MUNI', copy=True)

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
        for row in all_personas.to_dict("records"):
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
    def qualification_detail_top(self) -> List[Dict[str, Any]]:
        """資格詳細: 全資格一覧（row_type=QUALIFICATION_DETAIL）

        表示形式: [{"qualification": "介護福祉士", "count": 1234, "national_ratio": "85.0%"}]

        NOTE:
        - 市町村にデータがない場合は都道府県レベルにフォールバック
        - 希少性のある資格も含め全資格を表示（TOP10制限なし）
        """
        if not self.is_loaded or self.df is None:
            return []

        df = self.df
        if 'row_type' not in df.columns or 'category1' not in df.columns:
            return []

        # まず市町村レベルで検索
        filtered = self._safe_filter_by_row_type('QUALIFICATION_DETAIL', copy=True)

        # 市町村データが空の場合は都道府県レベルにフォールバック
        if filtered.empty:
            prefecture = self.selected_prefecture
            if prefecture:
                filtered = self._get_prefecture_pattern_data(prefecture, 'QUALIFICATION_DETAIL')

        if filtered.empty:
            return []

        # 集計: 資格名ごとの件数 + 国家資格比率
        # is_national_license列が存在する場合に比率を算出
        grouped = filtered.groupby('category1').agg(
            total_count=pd.NamedAgg(column='count', aggfunc='sum'),
            national_count=pd.NamedAgg(column='is_national_license', aggfunc=lambda x: (x.astype(str).str.lower().isin(['true', '1', 'yes']).sum()))
            if 'is_national_license' in filtered.columns else pd.NamedAgg(column='count', aggfunc='sum')
        ).reset_index()

        grouped['national_ratio'] = grouped.apply(
            lambda r: (r['national_count'] / r['total_count'] * 100) if r['total_count'] else 0.0,
            axis=1
        )

        # 全資格を人数順にソート（TOP10制限なし - 希少資格も表示）
        all_quals = grouped.sort_values('total_count', ascending=False)

        result = []
        for row in all_quals.to_dict("records"):
            result.append({
                "qualification": str(row['category1']),
                "count": int(row['total_count']),
                "national_ratio": f"{row['national_ratio']:.1f}%"
            })

        return result

    @rx.var(cache=False)
    def qualification_persona_matrix(self) -> List[Dict[str, Any]]:
        """保有資格ペルソナ: 具体的資格×性別×年齢のクロス集計

        QUALIFICATION_PERSONAデータから主要資格Top10の性別×年齢別人数を算出
        形式: [{"qualification": "介護福祉士", "total": 100, "male_total": 30, "female_total": 70,
                "male_20s": 5, "male_30s": 10, ..., "female_20s": 15, ...}]
        """
        if not self.is_loaded:
            return []

        # QUALIFICATION_PERSONAデータを取得
        filtered = self._safe_filter_by_row_type('QUALIFICATION_PERSONA', copy=True)

        if filtered.empty:
            return []

        # 必須カラムチェック（category1=資格名, category2=年齢層, category3=性別, count=人数）
        required_cols = {'category1', 'category2', 'category3', 'count'}
        if not required_cols.issubset(filtered.columns):
            return []

        # 資格別の総人数を算出してTop10を取得
        qual_totals = filtered.groupby('category1')['count'].sum().sort_values(ascending=False)
        top_qualifications = qual_totals.head(10).index.tolist()

        age_order = ['20代', '30代', '40代', '50代', '60代', '70歳以上']
        result = []

        for qual in top_qualifications:
            qual_data = filtered[filtered['category1'] == qual]

            # 資格名の短縮表示（長すぎる場合）
            display_name = qual if len(qual) <= 20 else qual[:18] + "..."

            row = {
                "qualification": display_name,
                "full_name": qual,
                "total": int(qual_data['count'].sum()),
                "male_total": 0,
                "female_total": 0,
            }

            # 性別×年齢別の人数を集計
            for gender in ['男性', '女性']:
                gender_data = qual_data[qual_data['category3'] == gender]
                gender_key = 'male' if gender == '男性' else 'female'
                row[f"{gender_key}_total"] = int(gender_data['count'].sum())

                for age in age_order:
                    age_data = gender_data[gender_data['category2'] == age]
                    age_key = age.replace('歳以上', 's_plus').replace('代', 's')
                    row[f"{gender_key}_{age_key}"] = int(age_data['count'].sum()) if not age_data.empty else 0

            result.append(row)

        return result

    @rx.var(cache=False)
    def qualification_persona_chart_data(self) -> List[Dict[str, Any]]:
        """保有資格ペルソナ: Rechartsグループ化棒グラフ用データ

        主要資格Top10の男女別人数を表示
        形式: [{"name": "介護福祉士", "男性": 30, "女性": 70}, ...]
        """
        matrix = self.qualification_persona_matrix
        if not matrix:
            return []

        return [
            {
                "name": item["qualification"],
                "男性": item["male_total"],
                "女性": item["female_total"]
            }
            for item in matrix
        ]

    @rx.var(cache=False)
    def qualification_persona_age_chart_data(self) -> List[Dict[str, Any]]:
        """保有資格ペルソナ: 年齢層別の分布グラフ用データ

        Top1資格の年齢層×性別別人数を表示
        形式: [{"name": "20代", "男性": 5, "女性": 15}, ...]
        """
        matrix = self.qualification_persona_matrix
        if not matrix:
            return []

        # Top1資格のデータを使用
        top_qual = matrix[0]
        age_order = ['20s', '30s', '40s', '50s', '60s', '70s_plus']
        age_labels = ['20代', '30代', '40代', '50代', '60代', '70歳以上']

        return [
            {
                "name": label,
                "男性": top_qual.get(f"male_{age}", 0),
                "女性": top_qual.get(f"female_{age}", 0)
            }
            for age, label in zip(age_order, age_labels)
        ]

    @rx.var(cache=False)
    def qualification_persona_top1_name(self) -> str:
        """保有資格ペルソナ: Top1資格の名前"""
        matrix = self.qualification_persona_matrix
        if not matrix:
            return ""
        return matrix[0].get("qualification", "")

    @rx.var(cache=False)
    def available_qualifications(self) -> List[str]:
        """利用可能な資格リスト（プルダウン用）"""
        matrix = self.qualification_persona_matrix
        if not matrix:
            return []
        return [item.get("qualification", "") for item in matrix if item.get("qualification")]

    @rx.var(cache=False)
    def selected_qualification_display(self) -> str:
        """選択中の資格名（表示用）"""
        if self.selected_qualification:
            return self.selected_qualification
        # 未選択の場合はTop1を返す
        matrix = self.qualification_persona_matrix
        if matrix:
            return matrix[0].get("qualification", "")
        return ""

    @rx.var(cache=False)
    def selected_qualification_age_chart_data(self) -> List[Dict[str, Any]]:
        """選択した資格の年齢層×性別分布グラフ用データ

        selected_qualificationで選択した資格の年齢層×性別別人数を表示
        形式: [{"name": "20代", "男性": 5, "女性": 15}, ...]
        """
        matrix = self.qualification_persona_matrix
        if not matrix:
            return []

        # 選択した資格を探す（未選択ならTop1）
        target_qual = self.selected_qualification if self.selected_qualification else matrix[0].get("qualification", "")

        # 該当する資格データを探す
        qual_data = None
        for item in matrix:
            if item.get("qualification") == target_qual:
                qual_data = item
                break

        if not qual_data:
            qual_data = matrix[0]  # 見つからない場合はTop1

        age_order = ['20s', '30s', '40s', '50s', '60s', '70s_plus']
        age_labels = ['20代', '30代', '40代', '50代', '60代', '70歳以上']

        return [
            {
                "name": label,
                "男性": qual_data.get(f"male_{age}", 0),
                "女性": qual_data.get(f"female_{age}", 0)
            }
            for age, label in zip(age_order, age_labels)
        ]

    def set_qualification(self, value: str):
        """資格選択時のハンドラ"""
        self.selected_qualification = value

    @rx.var(cache=False)
    def desired_area_pattern_top(self) -> List[Dict[str, Any]]:
        """併願パターン: 選択都道府県を希望する人の居住県Top10

        【ターゲット視点】選択都道府県を希望する人が、どこに住んでいるか（居住県）
        row_type=DESIRED_AREA_PATTERN, co_desired_prefecture==選択都道府県 でフィルタ
        形式: [{"pref": "東京都", "count": 1234}]
        """
        if not self.is_loaded:
            return []

        prefecture = self.selected_prefecture
        if not prefecture:
            return []

        # ターゲット視点でデータを取得（選択都道府県を希望する人）
        filtered = self._get_target_prefecture_pattern_data(prefecture, 'DESIRED_AREA_PATTERN')

        if filtered.empty:
            return []

        if not {'prefecture', 'count'}.issubset(filtered.columns):
            return []

        # 選択都道府県を希望する人の、元の居住県（prefecture）を集計
        agg = (
            filtered
            .groupby('prefecture')['count']
            .sum()
            .reset_index()
            .sort_values('count', ascending=False)
            .head(10)
        )

        result = []
        for row in agg.to_dict("records"):
            result.append({
                "pref": str(row['prefecture']),
                "co_pref": prefecture,  # 希望先は選択都道府県
                "count": int(row['count'])
            })
        return result

    @rx.var(cache=False)
    def desired_area_pattern_heatmap_html(self) -> str:
        """併願パターンの都道府県ヒートマップ（Plotly HTML）

        【ターゲット視点】選択都道府県を希望する人が、どこから来ているかをヒートマップで表示
        """
        if not self.is_loaded:
            return "<div style='color:#94a3b8;padding:20px;text-align:center;min-height:100px;'>データを読み込んでください</div>"

        prefecture = self.selected_prefecture
        if not prefecture:
            return "<div style='color:#94a3b8;padding:20px;text-align:center;min-height:100px;'>都道府県を選択してください</div>"

        # ターゲット視点でデータを取得（選択都道府県を希望する人）
        filtered = self._get_target_prefecture_pattern_data(prefecture, 'DESIRED_AREA_PATTERN')

        if filtered.empty:
            return f"<div style='color:#94a3b8;padding:20px;text-align:center;'>{prefecture}を希望するデータがありません</div>"

        needed = {'prefecture', 'co_desired_prefecture', 'count'}
        if not needed.issubset(filtered.columns):
            return "<div style='color:#94a3b8;padding:20px;text-align:center;'>必要なカラムがありません</div>"

        # 居住県（prefecture）ごとの件数を集計
        agg = (
            filtered
            .groupby('prefecture')['count']
            .sum()
            .reset_index()
            .sort_values('count', ascending=True)
            .tail(15)
        )

        if agg.empty:
            return f"<div style='color:#94a3b8;padding:20px;text-align:center;'>{prefecture}を希望するデータがありません</div>"

        # 横棒グラフで表示
        fig = go.Figure(
            data=go.Bar(
                x=agg['count'].tolist(),
                y=agg['prefecture'].tolist(),
                orientation='h',
                marker=dict(color='#0072B2')  # Okabe-Ito: 青
            )
        )
        fig.update_layout(
            title=f"{prefecture}を希望する人の居住県",
            xaxis_title="人数",
            yaxis_title="居住県",
            margin=dict(l=100, r=20, t=50, b=40),
            height=400,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#e2e8f0')
        )
        fig.update_xaxes(gridcolor='rgba(255,255,255,0.1)')
        fig.update_yaxes(gridcolor='rgba(255,255,255,0.1)')
        return fig.to_html(include_plotlyjs='cdn', full_html=False)

    @rx.var(cache=False)
    def desired_area_pattern_heatmap_muni_html(self) -> str:
        """併願パターンの市区町村ヒートマップ（Plotly HTML）

        【ソース視点】選択市区町村に住んでいる人が、どこを併願希望しているかをヒートマップで表示
        都道府県レベルではなく市区町村レベルで表示
        """
        if not self.is_loaded:
            return "<div style='color:#94a3b8;padding:20px;text-align:center;min-height:100px;'>データを読み込んでください</div>"

        prefecture = self.selected_prefecture
        municipality = self.selected_municipality
        if not prefecture:
            return "<div style='color:#94a3b8;padding:20px;text-align:center;min-height:100px;'>都道府県を選択してください</div>"

        # ソース視点で市区町村レベルのデータを取得（選択市町村に住んでいる人）
        if municipality:
            filtered = self._get_source_pattern_data(prefecture, municipality, 'DESIRED_AREA_PATTERN')
        else:
            filtered = self._get_source_prefecture_pattern_data(prefecture, 'DESIRED_AREA_PATTERN')

        if filtered.empty:
            target = f"{municipality or prefecture}"
            return f"<div style='color:#94a3b8;padding:20px;text-align:center;'>{target}に住んでいる人の併願データがありません</div>"

        # 併願希望先カラムの存在チェック
        if 'co_desired_municipality' not in filtered.columns:
            return "<div style='color:#94a3b8;padding:20px;text-align:center;'>併願希望先市区町村カラムがありません</div>"

        if 'count' not in filtered.columns:
            return "<div style='color:#94a3b8;padding:20px;text-align:center;'>件数カラムがありません</div>"

        # 併願希望先市区町村ごとの件数を集計（都道府県も含む）
        filtered['label'] = filtered['co_desired_prefecture'].astype(str) + ' ' + filtered['co_desired_municipality'].astype(str)
        agg = (
            filtered
            .groupby('label')['count']
            .sum()
            .reset_index()
            .sort_values('count', ascending=True)
            .tail(15)
        )

        if agg.empty:
            target = f"{municipality or prefecture}"
            return f"<div style='color:#94a3b8;padding:20px;text-align:center;'>{target}に住んでいる人の併願データがありません</div>"

        # 色弱配慮: 青系グラデーション使用（赤緑を避ける）
        fig = go.Figure(
            data=go.Bar(
                x=agg['count'].tolist(),
                y=agg['label'].tolist(),
                orientation='h',
                marker=dict(
                    color=agg['count'].tolist(),
                    colorscale='Blues',
                    showscale=True,
                    colorbar=dict(title="件数", tickfont=dict(color='#e2e8f0'))
                )
            )
        )
        target = municipality if municipality else prefecture
        fig.update_layout(
            title=dict(
                text=f"{target}に住んでいる人の併願希望先 Top15",
                font=dict(color='#e2e8f0', size=14)
            ),
            xaxis_title="人数",
            yaxis_title="併願希望先市区町村",
            margin=dict(l=180, r=60, t=50, b=40),
            height=450,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#e2e8f0')
        )
        fig.update_xaxes(gridcolor='rgba(255,255,255,0.1)', tickfont=dict(color='#94a3b8'))
        fig.update_yaxes(gridcolor='rgba(255,255,255,0.1)', tickfont=dict(color='#94a3b8'))
        html = fig.to_html(include_plotlyjs='cdn', full_html=True)
        # ダークテーマ用にbody背景色を注入
        html = html.replace('<body>', '<body style="background:#0a0e17;margin:0;padding:0;">')
        return html

    @rx.var(cache=False)
    def residence_flow_top(self) -> List[Dict[str, Any]]:
        """居住地フロー: 選択都道府県を希望する人の居住県Top10

        【ターゲット視点】選択都道府県を希望する人が、どこに住んでいるか
        row_type=RESIDENCE_FLOW, desired_prefecture==選択都道府県 でフィルタ
        形式: [{"origin_pref": "東京都", "dest_pref": "群馬県", "count": 5}]
        """
        if not self.is_loaded:
            return []

        prefecture = self.selected_prefecture
        if not prefecture:
            return []

        # ターゲット視点でデータを取得（選択都道府県を希望する人）
        filtered = self._get_target_prefecture_pattern_data(prefecture, 'RESIDENCE_FLOW')

        if filtered.empty:
            return []

        needed_cols = {'prefecture', 'count'}
        if not needed_cols.issubset(filtered.columns):
            return []

        # 選択都道府県を希望する人の、居住県（prefecture）を集計
        agg = (
            filtered
            .groupby('prefecture')['count']
            .sum()
            .reset_index()
            .sort_values('count', ascending=False)
            .head(10)
        )

        result = []
        for row in agg.to_dict("records"):
            result.append({
                "origin_pref": str(row['prefecture']),
                "dest_pref": prefecture,  # 希望先は選択都道府県
                "count": int(row['count'])
            })
        return result

    @rx.var(cache=False)
    def residence_flow_top_muni(self) -> List[Dict[str, Any]]:
        """居住地フロー: 選択市町村に住んでいる人の希望勤務地Top10

        【ソース視点】選択市町村に住んでいる人が、どこを希望しているか
        row_type=RESIDENCE_FLOW, prefecture/municipality==選択市町村 でフィルタ
        集計対象: desired_prefecture/desired_municipality（希望勤務地）
        """
        if not self.is_loaded:
            return []

        prefecture = self.selected_prefecture
        municipality = self.selected_municipality
        if not prefecture:
            return []

        # ソース視点でデータを取得（選択市町村に住んでいる人）
        if municipality:
            filtered = self._get_source_pattern_data(prefecture, municipality, 'RESIDENCE_FLOW')
        else:
            filtered = pd.DataFrame()

        # 市区町村データがない場合は都道府県レベルにフォールバック
        is_fallback = False
        if filtered.empty:
            filtered = self._get_source_prefecture_pattern_data(prefecture, 'RESIDENCE_FLOW')
            is_fallback = True

        if filtered.empty:
            return []

        needed = {'desired_prefecture', 'desired_municipality', 'count'}
        if not needed.issubset(filtered.columns):
            return []

        # 選択市町村に住んでいる人の、希望勤務地（desired_municipality）を集計
        # 市区町村名のみ（短縮表示）
        filtered['muni_only'] = filtered['desired_municipality'].astype(str)
        agg = (
            filtered
            .groupby('muni_only')['count']
            .sum()
            .reset_index()
            .sort_values('count', ascending=False)
            .head(10)
        )

        result = []
        for row in agg.to_dict("records"):
            label = str(row['muni_only'])
            # 8文字以上は省略
            if len(label) > 10:
                label = label[:9] + "…"
            if is_fallback:
                label = f"[県]{label}"
            result.append({
                "label": label,
                "value": int(row['count'])
            })
        return result

    @rx.var(cache=False)
    def residence_flow_heatmap_html(self) -> str:
        """居住地フローの都道府県グラフ（Plotly HTML）

        【ターゲット視点】選択都道府県を希望する人が、どこに住んでいるかを棒グラフで表示
        """
        if not self.is_loaded:
            return "<div style='color:#94a3b8;padding:20px;text-align:center;min-height:100px;'>データを読み込んでください</div>"

        prefecture = self.selected_prefecture
        if not prefecture:
            return "<div style='color:#94a3b8;padding:20px;text-align:center;min-height:100px;'>都道府県を選択してください</div>"

        # ターゲット視点でデータを取得（選択都道府県を希望する人）
        filtered = self._get_target_prefecture_pattern_data(prefecture, 'RESIDENCE_FLOW')

        if filtered.empty:
            return f"<div style='color:#94a3b8;padding:20px;text-align:center;'>{prefecture}を希望するデータがありません</div>"

        needed = {'prefecture', 'count'}
        if not needed.issubset(filtered.columns):
            return "<div style='color:#94a3b8;padding:20px;text-align:center;'>必要なカラムがありません</div>"

        # 居住県（prefecture）ごとの件数を集計
        agg = (
            filtered
            .groupby('prefecture')['count']
            .sum()
            .reset_index()
            .sort_values('count', ascending=True)
            .tail(15)
        )

        if agg.empty:
            return f"<div style='color:#94a3b8;padding:20px;text-align:center;'>{prefecture}を希望するデータがありません</div>"

        # 横棒グラフで表示
        fig = go.Figure(
            data=go.Bar(
                x=agg['count'].tolist(),
                y=agg['prefecture'].tolist(),
                orientation='h',
                marker=dict(color='#E69F00')  # Okabe-Ito: オレンジ
            )
        )
        fig.update_layout(
            title=f"{prefecture}を希望する人の居住県",
            xaxis_title="人数",
            yaxis_title="居住県",
            margin=dict(l=100, r=20, t=50, b=40),
            height=400,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#e2e8f0')
        )
        fig.update_xaxes(gridcolor='#334155')
        fig.update_yaxes(gridcolor='#334155')
        return fig.to_html(include_plotlyjs='cdn', full_html=False)

    @rx.var(cache=False)
    def residence_flow_heatmap_muni_html(self) -> str:
        """居住地フローの市区町村ヒートマップ（Plotly HTML）

        【ソース視点】選択市区町村に住んでいる人が、どこを希望勤務地にしているかを棒グラフで表示
        居住地 → 希望勤務地 のフローを可視化
        色弱配慮: オレンジ系グラデーション使用（赤緑を避ける）
        """
        if not self.is_loaded:
            return "<div style='color:#94a3b8;padding:20px;text-align:center;min-height:100px;'>データを読み込んでください</div>"

        prefecture = self.selected_prefecture
        municipality = self.selected_municipality
        if not prefecture:
            return "<div style='color:#94a3b8;padding:20px;text-align:center;min-height:100px;'>都道府県を選択してください</div>"

        # ソース視点で市区町村レベルのデータを取得（選択市町村に住んでいる人）
        if municipality:
            filtered = self._get_source_pattern_data(prefecture, municipality, 'RESIDENCE_FLOW')
        else:
            filtered = self._get_source_prefecture_pattern_data(prefecture, 'RESIDENCE_FLOW')

        if filtered.empty:
            target = f"{municipality or prefecture}"
            return f"<div style='color:#94a3b8;padding:20px;text-align:center;'>{target}に住んでいる人の希望勤務地データがありません</div>"

        # 希望勤務地カラムの存在チェック
        if 'desired_municipality' not in filtered.columns:
            return "<div style='color:#94a3b8;padding:20px;text-align:center;'>希望勤務地市区町村カラムがありません</div>"

        if 'count' not in filtered.columns:
            return "<div style='color:#94a3b8;padding:20px;text-align:center;'>件数カラムがありません</div>"

        # 希望勤務地市区町村ごとの件数を集計（都道府県も含む）
        filtered['label'] = filtered['desired_prefecture'].astype(str) + ' ' + filtered['desired_municipality'].astype(str)
        agg = (
            filtered
            .groupby('label')['count']
            .sum()
            .reset_index()
            .sort_values('count', ascending=True)
            .tail(15)
        )

        if agg.empty:
            target = f"{municipality or prefecture}"
            return f"<div style='color:#94a3b8;padding:20px;text-align:center;'>{target}に住んでいる人の希望勤務地データがありません</div>"

        # 色弱配慮: オレンジ系グラデーション使用（赤緑を避ける）
        fig = go.Figure(
            data=go.Bar(
                x=agg['count'].tolist(),
                y=agg['label'].tolist(),
                orientation='h',
                marker=dict(
                    color=agg['count'].tolist(),
                    colorscale='Oranges',
                    showscale=True,
                    colorbar=dict(title="件数", tickfont=dict(color='#e2e8f0'))
                )
            )
        )
        target = municipality if municipality else prefecture
        fig.update_layout(
            title=dict(
                text=f"{target}に住んでいる人の希望勤務地 Top15",
                font=dict(color='#e2e8f0', size=14)
            ),
            xaxis_title="人数",
            yaxis_title="希望勤務地市区町村",
            margin=dict(l=180, r=60, t=50, b=40),
            height=450,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#e2e8f0')
        )
        fig.update_xaxes(gridcolor='rgba(255,255,255,0.1)', tickfont=dict(color='#94a3b8'))
        fig.update_yaxes(gridcolor='rgba(255,255,255,0.1)', tickfont=dict(color='#94a3b8'))
        html = fig.to_html(include_plotlyjs='cdn', full_html=True)
        # ダークテーマ用にbody背景色を注入
        html = html.replace('<body>', '<body style="background:#0a0e17;margin:0;padding:0;">')
        return html

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
        filtered = self._safe_filter_by_row_type('PERSONA_MUNI', copy=True)

        if filtered.empty:
            return []

        # ペルソナ名でグループ化してcountを合計
        persona_counts = filtered.groupby('category1')['count'].sum().reset_index()
        persona_counts.columns = ['name', 'count']

        # countの降順でソート（上位15件）
        top_personas = persona_counts.sort_values('count', ascending=False).head(15)

        # 辞書リストに変換
        result = []
        for row in top_personas.to_dict("records"):
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
        filtered = self._safe_filter_by_row_type('PERSONA_MUNI', copy=True)

        if filtered.empty:
            return []

        # ペルソナ名を分解（例: "50代・女性・就業中" → age_gender="50代・女性", employment="就業中"）
        breakdown_data = {}
        for row in filtered.to_dict("records"):
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
        filtered = self._safe_filter_by_row_type('PERSONA_MUNI', copy=True)

        if filtered.empty:
            return []

        # ペルソナ名でグループ化してcountを合計
        persona_counts = filtered.groupby('category1')['count'].sum().reset_index()
        persona_counts.columns = ['name', 'value']

        # countの降順でソート
        persona_counts = persona_counts.sort_values('value', ascending=False)

        # 辞書リストに変換（COLOR_PALETTEを順番に割り当て）
        result = []
        for row in persona_counts.to_dict("records"):
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
        filtered = self._safe_filter_by_row_type('EMPLOYMENT_AGE_CROSS', copy=True)

        if filtered.empty:
            return []

        # ピボットテーブル形式に変換: 年齢層 × 就業ステータス
        pivot_data = {}
        for row in filtered.to_dict("records"):
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
        for row in filtered.to_dict("records"):
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
        filtered = self._safe_filter_by_row_type('EMPLOYMENT_AGE_CROSS', copy=True)

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
        for row in grouped.to_dict("records"):
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
        filtered = self._safe_filter_by_row_type('EMPLOYMENT_AGE_CROSS', copy=True)

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
        for row in grouped.to_dict("records"):
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
        for persona_row in persona_df.to_dict("records"):
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
        for urgency_row in urgency_df.to_dict("records"):
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
        for persona_row in persona_df.to_dict("records"):
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

        # row_typeカラムの存在チェック
        if df.empty or 'row_type' not in df.columns:
            return []

        # サーバーサイドフィルタリング: dfは既に地域でフィルタ済み、row_typeのみフィルタ
        filtered = self._safe_filter_by_row_type('GAP')

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

        # row_typeカラムの存在チェック
        if df.empty or 'row_type' not in df.columns:
            return []

        # サーバーサイドフィルタリング: dfは既に地域でフィルタ済み、row_typeのみフィルタ
        filtered = self._safe_filter_by_row_type('GAP')

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

        # row_typeカラムの存在チェック
        if df.empty or 'row_type' not in df.columns:
            return "0"

        # サーバーサイドフィルタリング: dfは既に地域でフィルタ済み、row_typeのみフィルタ
        filtered = self._safe_filter_by_row_type('GAP')

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

        # row_typeカラムの存在チェック
        if df.empty or 'row_type' not in df.columns:
            return "0"

        # サーバーサイドフィルタリング: dfは既に地域でフィルタ済み、row_typeのみフィルタ
        filtered = self._safe_filter_by_row_type('GAP')

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

        # row_typeカラムの存在チェック
        if df.empty or 'row_type' not in df.columns:
            return "0.0"

        # サーバーサイドフィルタリング: dfは既に地域でフィルタ済み、row_typeのみフィルタ
        filtered = self._safe_filter_by_row_type('GAP')

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

        NOTE: サーバーサイドフィルタリング対応のため、都道府県全体のデータを直接DBからクエリ
        """
        if not self.is_loaded:
            return []

        prefecture = self.selected_prefecture
        if not prefecture:
            return []

        # 都道府県全体のGAPデータを取得（ヘルパーメソッド使用）
        df = self._get_prefecture_gap_data(prefecture)

        if df.empty:
            return []

        # gap > 0のみフィルタ
        filtered = df[
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
        for row in aggregated.to_dict("records"):
            result.append({
                "name": str(row.get('municipality', '不明')),
                "value": int(row.get('gap', 0)) if pd.notna(row.get('gap')) else 0
            })

        return result

    @rx.var(cache=False)
    def gap_surplus_ranking(self) -> List[Dict[str, Any]]:
        """需給: 供給超過ランキング Top 10（横棒グラフ用、絶対値）

        形式: [{"name": "京都市", "value": 450}, ...]

        NOTE: サーバーサイドフィルタリング対応のため、都道府県全体のデータを直接DBからクエリ
        """
        if not self.is_loaded:
            return []

        prefecture = self.selected_prefecture
        if not prefecture:
            return []

        # 都道府県全体のGAPデータを取得（ヘルパーメソッド使用）
        df = self._get_prefecture_gap_data(prefecture)

        if df.empty:
            return []

        # gap < 0のみフィルタ
        filtered = df[
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
        for row in aggregated.to_dict("records"):
            result.append({
                "name": str(row.get('municipality', '不明')),
                "value": int(row.get('abs_gap', 0)) if pd.notna(row.get('abs_gap')) else 0
            })

        return result

    @rx.var(cache=False)
    def gap_ratio_ranking(self) -> List[Dict[str, Any]]:
        """需給: 需給比率ランキング Top 10（横棒グラフ用）

        形式: [{"name": "京都市", "value": 3.5}, ...]

        NOTE: サーバーサイドフィルタリング対応のため、都道府県全体のデータを直接DBからクエリ
        """
        if not self.is_loaded:
            return []

        prefecture = self.selected_prefecture
        if not prefecture:
            return []

        # 都道府県全体のGAPデータを取得（ヘルパーメソッド使用）
        df = self._get_prefecture_gap_data(prefecture)

        if df.empty:
            return []

        # municipalityがあり、空文字・None・'None'でないもののみフィルタ
        filtered = df[
            df['municipality'].notna() &
            (df['municipality'].astype(str).str.strip() != '') &
            (df['municipality'].astype(str).str.lower() != 'none')
        ].copy()

        if filtered.empty:
            return []

        # 異常地名を除外（1文字、"府"/"県"/"市"/"区"/"町"/"村"単独など）
        def is_valid_municipality(name: str) -> bool:
            if not name or len(name) < 2:
                return False
            # 単独の行政単位名を除外
            invalid_singles = {'府', '県', '市', '区', '町', '村', '郡'}
            if name.strip() in invalid_singles:
                return False
            # スペース含みの不正な名前を除外（例: "京都 府"）
            if ' ' in name.strip():
                return False
            return True

        filtered = filtered[filtered['municipality'].apply(lambda x: is_valid_municipality(str(x)))]

        if filtered.empty:
            return []

        # 市区町村でgroupbyして集約（重複回避、平均を使用）
        aggregated = filtered.groupby('municipality', as_index=False).agg({
            'demand_supply_ratio': 'mean'
        })

        # demand_supply_ratioでソート（降順）
        aggregated = aggregated.sort_values('demand_supply_ratio', ascending=False).head(10)

        result = []
        for row in aggregated.to_dict("records"):
            muni_name = str(row.get('municipality', '')).strip()
            if not muni_name or muni_name.lower() == 'none':
                muni_name = '不明'
            result.append({
                "name": muni_name,
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
        filtered = self._safe_filter_by_row_type('FLOW')

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
        filtered = self._safe_filter_by_row_type('FLOW')

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
        filtered = self._safe_filter_by_row_type('FLOW')

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
        filtered = self._safe_filter_by_row_type('FLOW')

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
        filtered = self._safe_filter_by_row_type('FLOW')

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
        for row in aggregated.to_dict("records"):
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
        for row in aggregated.to_dict("records"):
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
        for row in aggregated.to_dict("records"):
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
        形式: [{"name": "S級", "value": 5, "fill": "#D55E00"}, {"name": "A級", "value": 15, "fill": "#CC79A7"}, ...] (Okabe-Ito)
        データソース: row_type='RARITY', category3=希少ランク
        """
        if not self.is_loaded or self.df is None:
            return []

        df = self.df

        # サーバーサイドフィルタリング: dfは既に地域でフィルタ済み、row_typeのみフィルタ
        filtered = self._safe_filter_by_row_type('RARITY', copy=True)

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
        filtered = self._safe_filter_by_row_type('RARITY', copy=True)

        if filtered.empty:
            return []

        # rarity_scoreで降順ソートして上位10件を取得
        filtered = filtered.sort_values('rarity_score', ascending=False).head(10)

        # ラベル作成: "年齢層・性別"
        result = []
        for row in filtered.to_dict("records"):
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
            (df['category3'].astype(str).str.startswith('S:', na=False))
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
            (df['category3'].astype(str).str.startswith('A:', na=False))
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
            (df['category3'].astype(str).str.startswith('B:', na=False))
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
        filtered = self._safe_filter_by_row_type('RARITY')

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
        filtered = self._safe_filter_by_row_type('RARITY')

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
        filtered = self._safe_filter_by_row_type('RARITY', copy=True)

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
        filtered = self._safe_filter_by_row_type('RARITY', copy=True)

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
        for row in filtered.to_dict("records"):
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
        形式: [{"name": "女性", "value": 3000, "fill": "#E69F00"}, {"name": "男性", "value": 2000, "fill": "#0072B2"}] (Okabe-Ito)
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
        for row in filtered.to_dict("records"):
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
        for row in filtered.to_dict("records"):
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
        for row in filtered.to_dict("records"):
            # municipalityを使用
            name = str(row.get('municipality', '不明'))
            result.append({
                "name": name,
                "value": float(row['female_ratio_calc'])
            })

        return result

    # =====================================
    # 3層比較（全国・都道府県・市区町村）
    # =====================================

    def _calc_municipality_desired_areas(self) -> float:
        """市区町村レベルの希望勤務地数を計算（SUMMARYのavg_desired_areasを使用）

        Phase1_Applicantsから算出された居住地ベースの1人あたり平均希望勤務地数を取得。
        DESIRED_AREA_PATTERNは2件以上の希望地を持つ求職者のみが対象のため不適切。
        """
        if self.df_full is None or self.df_full.empty:
            return 0.0

        prefecture = self.selected_prefecture
        municipality = self.selected_municipality
        if not prefecture or not municipality:
            return 0.0

        # SUMMARYからavg_desired_areasを取得（Phase1_Applicantsから算出された正確な値）
        summary = self.df_full[self.df_full['row_type'] == 'SUMMARY']
        muni_summary = summary[
            (summary['prefecture'] == prefecture) &
            (summary['municipality'].str.startswith(municipality, na=False))
        ]

        if len(muni_summary) == 0 or 'avg_desired_areas' not in muni_summary.columns:
            return 0.0

        valid_desired = muni_summary['avg_desired_areas'].dropna()
        if len(valid_desired) == 0:
            return 0.0

        return float(valid_desired.mean())

    def _calc_municipality_distance(self) -> float:
        """市区町村レベルの平均移動距離を計算"""
        if self.df_full is None or self.df_full.empty:
            return 0.0

        prefecture = self.selected_prefecture
        municipality = self.selected_municipality
        if not prefecture or not municipality:
            return 0.0

        rf = self.df_full[self.df_full['row_type'] == 'RESIDENCE_FLOW']
        muni_rf = rf[
            (rf['prefecture'] == prefecture) &
            (rf['municipality'].str.startswith(municipality, na=False))
        ]

        if len(muni_rf) == 0 or 'avg_reference_distance_km' not in muni_rf.columns:
            return 0.0

        return float(muni_rf['avg_reference_distance_km'].mean())

    def _calc_municipality_qualifications(self) -> float:
        """市区町村レベルの平均資格保有数を計算"""
        if self.df_full is None or self.df_full.empty:
            return 0.0

        prefecture = self.selected_prefecture
        municipality = self.selected_municipality
        if not prefecture or not municipality:
            return 0.0

        summary = self.df_full[self.df_full['row_type'] == 'SUMMARY']
        muni_summary = summary[
            (summary['prefecture'] == prefecture) &
            (summary['municipality'] == municipality)
        ]

        if len(muni_summary) == 0 or 'avg_qualifications' not in muni_summary.columns:
            return 0.0

        return float(muni_summary['avg_qualifications'].mean())

    def _calc_municipality_gender_stats(self) -> Dict[str, Any]:
        """市区町村レベルの性別統計を計算"""
        if self.df_full is None or self.df_full.empty:
            return {"male_count": 0, "female_count": 0, "female_ratio": 0}

        prefecture = self.selected_prefecture
        municipality = self.selected_municipality
        if not prefecture or not municipality:
            return {"male_count": 0, "female_count": 0, "female_ratio": 0}

        summary = self.df_full[self.df_full['row_type'] == 'SUMMARY']
        muni_summary = summary[
            (summary['prefecture'] == prefecture) &
            (summary['municipality'] == municipality)
        ]

        male = 0
        female = 0
        if len(muni_summary) > 0 and 'male_count' in muni_summary.columns and 'female_count' in muni_summary.columns:
            male = int(muni_summary['male_count'].sum())
            female = int(muni_summary['female_count'].sum())
        total = male + female
        female_ratio = round(female / total * 100, 1) if total > 0 else 0

        return {"male_count": male, "female_count": female, "female_ratio": female_ratio}

    def _calc_municipality_age_distribution(self) -> Dict[str, float]:
        """市区町村レベルの年齢層分布を計算"""
        if self.df_full is None or self.df_full.empty:
            return {}

        prefecture = self.selected_prefecture
        municipality = self.selected_municipality
        if not prefecture or not municipality:
            return {}

        age_gender = self.df_full[self.df_full['row_type'] == 'AGE_GENDER']
        muni_age_gender = age_gender[
            (age_gender['prefecture'] == prefecture) &
            (age_gender['municipality'] == municipality)
        ]

        age_order = ['20代', '30代', '40代', '50代', '60代', '70歳以上']
        age_dist = {}
        if len(muni_age_gender) > 0 and 'category1' in muni_age_gender.columns and 'count' in muni_age_gender.columns:
            for age in age_order:
                age_count = int(muni_age_gender[muni_age_gender['category1'] == age]['count'].sum())
                age_dist[age] = age_count

        age_total = sum(age_dist.values())
        age_ratio = {}
        for age in age_order:
            if age_total > 0:
                age_ratio[age] = round(age_dist.get(age, 0) / age_total * 100, 1)
            else:
                age_ratio[age] = 0

        return age_ratio

    @rx.var(cache=False)
    def comparison_data(self) -> List[Dict[str, Any]]:
        """3層比較データ（UI表示用）

        形式: [
            {
                "label": "希望勤務地数",
                "unit": "件",
                "national": 65.6,
                "prefecture": 52.3,
                "municipality": 24.1,
                "pref_pct": 80,  # 都道府県のバー幅%
                "muni_pct": 37,  # 市区町村のバー幅%
                "muni_arrow": "▼",  # 全国比較での矢印
                "pref_name": "埼玉県",
                "muni_name": "春日部市"
            },
            ...
        ]
        """
        if not self.is_loaded or not self.national_stats:
            return []

        pref = self.selected_prefecture
        muni = self.selected_municipality

        # 都道府県統計
        pref_stats = self.prefecture_stats_cache.get(pref, {})

        # 市区町村統計を計算
        muni_desired = self._calc_municipality_desired_areas()
        muni_distance = self._calc_municipality_distance()
        muni_qual = self._calc_municipality_qualifications()

        def _calc_pct(val: float, base: float) -> int:
            """バー幅%を計算（0-100）"""
            if base <= 0:
                return 0
            pct = int(val / base * 100)
            return min(max(pct, 0), 200)  # 200%上限

        def _calc_arrow(muni_val: float, nat_val: float) -> str:
            """比較矢印を計算"""
            if muni_val > nat_val:
                return "▲"
            elif muni_val < nat_val:
                return "▼"
            return ""

        nat_desired = self.national_stats.get("desired_areas", 0)
        nat_distance = self.national_stats.get("distance_km", 0)
        nat_qual = self.national_stats.get("qualifications", 0)

        pref_desired = pref_stats.get("desired_areas", 0)
        pref_distance = pref_stats.get("distance_km", 0)
        pref_qual = pref_stats.get("qualifications", 0)

        return [
            {
                "label": "希望勤務地数",
                "unit": "件",
                "national": nat_desired,
                "prefecture": pref_desired,
                "municipality": round(muni_desired, 1),
                "pref_pct": _calc_pct(pref_desired, nat_desired),
                "muni_pct": _calc_pct(muni_desired, nat_desired),
                "muni_arrow": _calc_arrow(muni_desired, nat_desired),
                "pref_name": pref,
                "muni_name": muni,
            },
            {
                "label": "平均移動距離",
                "unit": "km",
                "national": nat_distance,
                "prefecture": pref_distance,
                "municipality": round(muni_distance, 1),
                "pref_pct": _calc_pct(pref_distance, nat_distance),
                "muni_pct": _calc_pct(muni_distance, nat_distance),
                "muni_arrow": _calc_arrow(muni_distance, nat_distance),
                "pref_name": pref,
                "muni_name": muni,
            },
            {
                "label": "資格保有数",
                "unit": "個",
                "national": nat_qual,
                "prefecture": pref_qual,
                "municipality": round(muni_qual, 2),
                "pref_pct": _calc_pct(pref_qual, nat_qual),
                "muni_pct": _calc_pct(muni_qual, nat_qual),
                "muni_arrow": _calc_arrow(muni_qual, nat_qual),
                "pref_name": pref,
                "muni_name": muni,
            },
        ]

    # --- 性別比率: フラット化されたState変数（Reflex型安全対応） ---
    @rx.var(cache=False)
    def gender_national_male_pct(self) -> float:
        """全国: 男性比率"""
        if not self.is_loaded or not self.national_stats:
            return 0.0
        male = self.national_stats.get("male_count", 0)
        female = self.national_stats.get("female_count", 0)
        total = male + female
        return round(male / total * 100, 1) if total > 0 else 0.0

    @rx.var(cache=False)
    def gender_national_female_pct(self) -> float:
        """全国: 女性比率"""
        if not self.is_loaded or not self.national_stats:
            return 0.0
        male = self.national_stats.get("male_count", 0)
        female = self.national_stats.get("female_count", 0)
        total = male + female
        return round(female / total * 100, 1) if total > 0 else 0.0

    @rx.var(cache=False)
    def gender_pref_male_pct(self) -> float:
        """都道府県: 男性比率"""
        if not self.is_loaded:
            return 0.0
        pref_stats = self.prefecture_stats_cache.get(self.selected_prefecture, {})
        male = pref_stats.get("male_count", 0)
        female = pref_stats.get("female_count", 0)
        total = male + female
        return round(male / total * 100, 1) if total > 0 else 0.0

    @rx.var(cache=False)
    def gender_pref_female_pct(self) -> float:
        """都道府県: 女性比率"""
        if not self.is_loaded:
            return 0.0
        pref_stats = self.prefecture_stats_cache.get(self.selected_prefecture, {})
        male = pref_stats.get("male_count", 0)
        female = pref_stats.get("female_count", 0)
        total = male + female
        return round(female / total * 100, 1) if total > 0 else 0.0

    @rx.var(cache=False)
    def gender_muni_male_pct(self) -> float:
        """市区町村: 男性比率"""
        if not self.is_loaded:
            return 0.0
        muni_gender = self._calc_municipality_gender_stats()
        male = muni_gender.get("male_count", 0)
        female = muni_gender.get("female_count", 0)
        total = male + female
        return round(male / total * 100, 1) if total > 0 else 0.0

    @rx.var(cache=False)
    def gender_muni_female_pct(self) -> float:
        """市区町村: 女性比率"""
        if not self.is_loaded:
            return 0.0
        muni_gender = self._calc_municipality_gender_stats()
        male = muni_gender.get("male_count", 0)
        female = muni_gender.get("female_count", 0)
        total = male + female
        return round(female / total * 100, 1) if total > 0 else 0.0

    @rx.var(cache=False)
    def gender_has_data(self) -> bool:
        """性別データが存在するか"""
        if not self.is_loaded or not self.national_stats:
            return False
        male = self.national_stats.get("male_count", 0)
        female = self.national_stats.get("female_count", 0)
        return (male + female) > 0

    @rx.var(cache=False)
    def comparison_age_data(self) -> List[Dict[str, Any]]:
        """3層比較: 年齢層分布データ（UI表示用・Recharts用）

        形式: [
            {"name": "20代", "全国": 15.2, "都道府県": 12.8, "市区町村": 10.5},
            {"name": "30代", "全国": 22.1, "都道府県": 25.3, "市区町村": 28.0},
            ...
        ]
        """
        if not self.is_loaded or not self.national_stats:
            return []

        pref = self.selected_prefecture

        # 全国統計
        nat_age = self.national_stats.get("age_distribution", {})

        # 都道府県統計
        pref_stats = self.prefecture_stats_cache.get(pref, {})
        pref_age = pref_stats.get("age_distribution", {})

        # 市区町村統計
        muni_age = self._calc_municipality_age_distribution()

        age_order = ['20代', '30代', '40代', '50代', '60代', '70歳以上']
        result = []
        for age in age_order:
            result.append({
                "name": age,
                "全国": nat_age.get(age, 0),
                "都道府県": pref_age.get(age, 0),
                "市区町村": muni_age.get(age, 0)
            })

        return result

    # =====================================
    # 新機能: RARITY分析（複数選択対応）
    # =====================================

    def set_rarity_ages(self, ages: list[str]):
        """RARITY: 年齢層選択を更新"""
        self.rarity_selected_ages = ages

    def set_rarity_genders(self, genders: list[str]):
        """RARITY: 性別選択を更新"""
        self.rarity_selected_genders = genders

    def set_rarity_qualifications(self, qualifications: list[str]):
        """RARITY: 資格選択を更新"""
        self.rarity_selected_qualifications = qualifications

    def set_rarity_age_single(self, age: str):
        """RARITY: 年齢層を1つ選択（UI用）"""
        self.rarity_selected_ages = [age] if age else []

    def set_rarity_gender_single(self, gender: str):
        """RARITY: 性別を1つ選択（UI用）"""
        self.rarity_selected_genders = [gender] if gender else []

    def set_rarity_qualification_single(self, qualification: str):
        """RARITY: 資格を1つ選択（UI用）"""
        self.rarity_selected_qualifications = [qualification] if qualification else []

    @rx.var(cache=False)
    def rarity_age_options(self) -> list[str]:
        """RARITY: 選択可能な年齢層リスト"""
        return ['20代', '30代', '40代', '50代', '60代', '70歳以上']

    @rx.var(cache=False)
    def rarity_gender_options(self) -> list[str]:
        """RARITY: 選択可能な性別リスト"""
        return ['女性', '男性']

    @rx.var(cache=False)
    def rarity_qualification_options(self) -> list[str]:
        """RARITY: 選択可能な資格リスト（QUALIFICATION_DETAILから取得）"""
        if self.df_full is None or self.df_full.empty:
            return []

        prefecture = self.selected_prefecture
        municipality = self.selected_municipality

        qd = self.df_full[self.df_full['row_type'] == 'QUALIFICATION_DETAIL']
        if prefecture:
            qd = qd[qd['prefecture'] == prefecture]
        if municipality:
            qd = qd[qd['municipality'].str.startswith(municipality, na=False)]

        if len(qd) == 0 or 'category1' not in qd.columns:
            return []

        # 件数順でソート
        qual_counts = qd.groupby('category1')['count'].sum().sort_values(ascending=False)
        return qual_counts.index.tolist()[:30]  # Top30

    @rx.var(cache=False)
    def rarity_results(self) -> list[dict]:
        """RARITY: 選択条件に一致する結果リスト

        形式: [
            {"age": "30代", "gender": "女性", "qualification": "介護福祉士",
             "count": 12, "score": 0.85, "share_pct": "2.3%"},
            ...
        ]
        """
        if self.df_full is None or self.df_full.empty:
            return []

        prefecture = self.selected_prefecture
        municipality = self.selected_municipality

        # QUALIFICATION_PERSONAを使用（資格×年齢×性別のクロス）
        qp = self.df_full[self.df_full['row_type'] == 'QUALIFICATION_PERSONA']
        if prefecture:
            qp = qp[qp['prefecture'] == prefecture]
        if municipality:
            qp = qp[qp['municipality'].str.startswith(municipality, na=False)]

        if len(qp) == 0:
            return []

        # フィルタリング
        ages = self.rarity_selected_ages if self.rarity_selected_ages else self.rarity_age_options
        genders = self.rarity_selected_genders if self.rarity_selected_genders else self.rarity_gender_options
        quals = self.rarity_selected_qualifications if self.rarity_selected_qualifications else []

        # category1=資格, category2=年齢, category3=性別 の場合
        filtered = qp[
            (qp['category2'].isin(ages)) &
            (qp['category3'].isin(genders))
        ]

        if quals:
            filtered = filtered[filtered['category1'].isin(quals)]

        if len(filtered) == 0:
            return []

        # 集計
        total_count = filtered['count'].sum() if 'count' in filtered.columns else 0

        results = []
        for _, row in filtered.head(50).iterrows():  # 最大50件
            count = row.get('count', 0)
            share = (count / total_count * 100) if total_count > 0 else 0
            results.append({
                "qualification": str(row.get('category1', '-')),
                "age": str(row.get('category2', '-')),
                "gender": str(row.get('category3', '-')),
                "count": int(count) if pd.notna(count) else 0,
                "share_pct": f"{share:.1f}%"
            })

        return results

    @rx.var(cache=False)
    def rarity_summary(self) -> dict:
        """RARITY: 結果サマリー（合計人数、平均スコア）"""
        results = self.rarity_results
        if not results:
            return {"total_count": 0, "avg_share": "0.0%"}

        total = sum(r.get("count", 0) for r in results)
        return {
            "total_count": total,
            "combination_count": len(results)
        }

    @rx.var(cache=False)
    def has_rarity_results(self) -> bool:
        """RARITY: 結果があるかどうか（rx.cond用）"""
        return len(self.rarity_results) > 0

    @rx.var(cache=False)
    def rarity_total_count(self) -> int:
        """RARITY: 合計人数"""
        return sum(r.get("count", 0) for r in self.rarity_results)

    @rx.var(cache=False)
    def rarity_combination_count(self) -> int:
        """RARITY: 組み合わせ数"""
        return len(self.rarity_results)

    # =====================================
    # 新機能: COMPETITION地域サマリー
    # =====================================

    @rx.var(cache=False)
    def competition_summary(self) -> dict:
        """COMPETITION: 地域サマリーデータ

        形式: {
            "total_applicants": 1234,
            "female_ratio": "72.0%",
            "male_ratio": "28.0%",
            "top_age": "30代",
            "top_age_ratio": "35.0%",
            "top_employment": "就業中",
            "top_employment_ratio": "45.0%",
            "avg_qualification_count": "1.8"
        }
        """
        if self.df_full is None or self.df_full.empty:
            return {}

        prefecture = self.selected_prefecture
        municipality = self.selected_municipality

        comp = self.df_full[self.df_full['row_type'] == 'COMPETITION']
        if prefecture:
            comp = comp[comp['prefecture'] == prefecture]
        if municipality:
            comp = comp[comp['municipality'].str.startswith(municipality, na=False)]

        if len(comp) == 0:
            return {}

        row = comp.iloc[0]
        return {
            "total_applicants": int(row.get('total_applicants', 0)) if pd.notna(row.get('total_applicants')) else 0,
            "female_ratio": f"{float(row.get('female_ratio', 0)) * 100:.1f}%" if pd.notna(row.get('female_ratio')) else "0.0%",
            "male_ratio": f"{float(row.get('male_ratio', 0)) * 100:.1f}%" if pd.notna(row.get('male_ratio')) else "0.0%",
            "top_age": str(row.get('category1', '-')) if pd.notna(row.get('category1')) else '-',
            "top_age_ratio": f"{float(row.get('top_age_ratio', 0)) * 100:.1f}%" if pd.notna(row.get('top_age_ratio')) else "0.0%",
            "top_employment": str(row.get('category2', '-')) if pd.notna(row.get('category2')) else '-',
            "top_employment_ratio": f"{float(row.get('top_employment_ratio', 0)) * 100:.1f}%" if pd.notna(row.get('top_employment_ratio')) else "0.0%",
            "avg_qualification_count": f"{float(row.get('avg_qualification_count', 0)):.1f}" if pd.notna(row.get('avg_qualification_count')) else "0.0"
        }

    # =====================================
    # 新機能: mobility_type分析
    # =====================================

    def set_mobility_view_mode(self, mode: str):
        """mobility_type: 表示モード切替（residence/destination）"""
        self.mobility_view_mode = mode

    @rx.var(cache=False)
    def mobility_type_distribution(self) -> list[dict]:
        """mobility_type: 移動タイプ分布

        形式: [
            {"type": "地元希望", "count": 280, "pct": "25.5%"},
            {"type": "近隣移動", "count": 450, "pct": "41.0%"},
            {"type": "中距離移動", "count": 200, "pct": "18.2%"},
            {"type": "遠距離移動", "count": 168, "pct": "15.3%"},
        ]
        """
        if self.df_full is None or self.df_full.empty:
            return []

        prefecture = self.selected_prefecture
        municipality = self.selected_municipality

        rf = self.df_full[self.df_full['row_type'] == 'RESIDENCE_FLOW']

        # 表示モードによってフィルタ条件を変更
        if self.mobility_view_mode == "residence":
            # 居住地ベース: この地域に住む人がどこへ行くか
            if prefecture:
                rf = rf[rf['prefecture'] == prefecture]
            if municipality:
                rf = rf[rf['municipality'].str.startswith(municipality, na=False)]
        else:
            # 希望勤務地ベース: この地域で働きたい人がどこから来るか
            if prefecture:
                rf = rf[rf['desired_prefecture'] == prefecture]
            if municipality:
                rf = rf[rf['desired_municipality'].str.startswith(municipality, na=False)]

        if len(rf) == 0 or 'mobility_type' not in rf.columns:
            return []

        # 移動タイプ別集計
        type_counts = rf.groupby('mobility_type')['count'].sum()
        total = type_counts.sum()

        # 順序を定義
        type_order = ['地元希望', '近隣移動', '中距離移動', '遠距離移動']

        results = []
        for t in type_order:
            count = int(type_counts.get(t, 0))
            pct = (count / total * 100) if total > 0 else 0
            results.append({
                "type": t,
                "count": count,
                "pct": f"{pct:.1f}%"
            })

        return results

    @rx.var(cache=False)
    def mobility_distance_stats(self) -> dict:
        """mobility_type: 距離統計（Q25/中央値/Q75）

        形式: {
            "q25": "5.2",
            "median": "15.8",
            "q75": "32.5",
            "unit": "km"
        }
        """
        if self.df_full is None or self.df_full.empty:
            return {"q25": "-", "median": "-", "q75": "-", "unit": "km"}

        prefecture = self.selected_prefecture
        municipality = self.selected_municipality

        rf = self.df_full[self.df_full['row_type'] == 'RESIDENCE_FLOW']

        # 表示モードによってフィルタ条件を変更
        if self.mobility_view_mode == "residence":
            if prefecture:
                rf = rf[rf['prefecture'] == prefecture]
            if municipality:
                rf = rf[rf['municipality'].str.startswith(municipality, na=False)]
        else:
            if prefecture:
                rf = rf[rf['desired_prefecture'] == prefecture]
            if municipality:
                rf = rf[rf['desired_municipality'].str.startswith(municipality, na=False)]

        if len(rf) == 0:
            return {"q25": "-", "median": "-", "q75": "-", "unit": "km"}

        # 距離統計の平均を計算
        q25 = rf['q25_distance_km'].mean() if 'q25_distance_km' in rf.columns else 0
        median = rf['median_distance_km'].mean() if 'median_distance_km' in rf.columns else 0
        q75 = rf['q75_distance_km'].mean() if 'q75_distance_km' in rf.columns else 0

        return {
            "q25": f"{q25:.1f}" if pd.notna(q25) else "-",
            "median": f"{median:.1f}" if pd.notna(median) else "-",
            "q75": f"{q75:.1f}" if pd.notna(q75) else "-",
            "unit": "km"
        }

    # =====================================
    # 新機能: market_share_pct（ペルソナシェア）
    # =====================================

    @rx.var(cache=False)
    def persona_market_share(self) -> list[dict]:
        """market_share_pct: 年齢×性別のシェア（就業状況除外）

        形式: [
            {"label": "30代×女性", "count": 156, "share_pct": "12.6%"},
            {"label": "40代×女性", "count": 128, "share_pct": "10.2%"},
            ...
        ]
        """
        if self.df_full is None or self.df_full.empty:
            return []

        prefecture = self.selected_prefecture
        municipality = self.selected_municipality

        # AGE_GENDER_RESIDENCEを使用（居住地ベース）
        ag = self.df_full[self.df_full['row_type'] == 'AGE_GENDER_RESIDENCE']
        if prefecture:
            ag = ag[ag['prefecture'] == prefecture]
        if municipality:
            ag = ag[ag['municipality'].str.startswith(municipality, na=False)]

        if len(ag) == 0 or 'category1' not in ag.columns or 'category2' not in ag.columns:
            return []

        # 年齢×性別で集計
        grouped = ag.groupby(['category1', 'category2'])['count'].sum().reset_index()
        total = grouped['count'].sum()

        results = []
        for _, row in grouped.sort_values('count', ascending=False).head(12).iterrows():
            count = int(row['count'])
            share = (count / total * 100) if total > 0 else 0
            label = f"{row['category1']}×{row['category2']}"
            results.append({
                "label": label,
                "count": count,
                "share_pct": f"{share:.1f}%"
            })

        return results

    # =====================================
    # 新機能: retention_rate（資格別定着率）
    # =====================================

    @rx.var(cache=False)
    def qualification_retention_rates(self) -> list[dict]:
        """retention_rate: 資格別定着率

        形式: [
            {"qualification": "介護福祉士", "retention_rate": "1.09", "interpretation": "地元志向"},
            {"qualification": "看護師", "retention_rate": "0.82", "interpretation": "流出傾向"},
            ...
        ]
        """
        if self.df_full is None or self.df_full.empty:
            return []

        prefecture = self.selected_prefecture
        municipality = self.selected_municipality

        qd = self.df_full[self.df_full['row_type'] == 'QUALIFICATION_DETAIL']
        if prefecture:
            qd = qd[qd['prefecture'] == prefecture]
        if municipality:
            qd = qd[qd['municipality'].str.startswith(municipality, na=False)]

        if len(qd) == 0 or 'retention_rate' not in qd.columns:
            return []

        # 資格別に平均retention_rateを計算
        grouped = qd.groupby('category1').agg({
            'retention_rate': 'mean',
            'count': 'sum'
        }).reset_index()

        # 件数が多い順にソート
        grouped = grouped.sort_values('count', ascending=False).head(15)

        results = []
        for _, row in grouped.iterrows():
            rate = row['retention_rate']
            if pd.notna(rate):
                if rate >= 1.1:
                    interpretation = "地元志向強"
                elif rate >= 1.0:
                    interpretation = "地元志向"
                elif rate >= 0.9:
                    interpretation = "平均的"
                else:
                    interpretation = "流出傾向"

                results.append({
                    "qualification": str(row['category1']),
                    "retention_rate": f"{rate:.2f}",
                    "interpretation": interpretation,
                    "count": int(row['count'])
                })

        return results

    # =====================================
    # 新機能: avg_desired_areas/avg_qualifications（年齢×性別）
    # =====================================

    @rx.var(cache=False)
    def age_gender_stats_list(self) -> list[dict]:
        """avg_desired_areas/avg_qualifications: 年齢×性別のリスト形式

        形式: [
            {"label": "20代男性", "desired_areas": "2.8", "qualifications": "0.8"},
            {"label": "20代女性", "desired_areas": "3.1", "qualifications": "1.2"},
            ...
        ]
        """
        if self.df_full is None or self.df_full.empty:
            return []

        prefecture = self.selected_prefecture
        municipality = self.selected_municipality

        # AGE_GENDER_RESIDENCEを使用（正しいavg_desired_areas値）
        ag = self.df_full[self.df_full['row_type'] == 'AGE_GENDER_RESIDENCE']
        if prefecture:
            ag = ag[ag['prefecture'] == prefecture]
        if municipality:
            ag = ag[ag['municipality'].str.startswith(municipality, na=False)]

        if len(ag) == 0:
            return []

        # 年齢×性別で集計
        age_order = ['20代', '30代', '40代', '50代', '60代', '70歳以上']
        gender_order = ['男性', '女性']

        results = []
        for age in age_order:
            for gender in gender_order:
                subset = ag[(ag['category1'] == age) & (ag['category2'] == gender)]
                if len(subset) > 0:
                    desired = subset['avg_desired_areas'].mean() if 'avg_desired_areas' in subset.columns else 0
                    quals = subset['avg_qualifications'].mean() if 'avg_qualifications' in subset.columns else 0

                    results.append({
                        "label": f"{age}{gender}",
                        "desired_areas": f"{desired:.1f}" if pd.notna(desired) else "-",
                        "qualifications": f"{quals:.1f}" if pd.notna(quals) else "-"
                    })

        return results


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
    """概要: 年齢×性別グラフ（Recharts）

    表示モード切替機能付き：
    - 希望勤務地ベース（AGE_GENDER）: この地域で働きたい人 → 採用ターゲット分析
    - 居住地ベース（AGE_GENDER_RESIDENCE）: この地域に住んでいる人 → 労働力供給分析
    """
    return rx.box(
        # ヘッダー: タイトルと切替ボタン
        rx.hstack(
            rx.text(
                "年齢×性別分布",
                font_size="1rem",
                font_weight="600",
                color=TEXT_COLOR
            ),
            rx.spacer(),
            # 表示モード切替ボタン（居住地データがある場合のみ表示）
            rx.cond(
                DashboardState.has_residence_data,
                rx.hstack(
                    rx.button(
                        "🎯 希望勤務地",
                        size="1",
                        variant=rx.cond(
                            DashboardState.age_gender_view_mode == "destination",
                            "solid",
                            "outline"
                        ),
                        color_scheme=rx.cond(
                            DashboardState.age_gender_view_mode == "destination",
                            "blue",
                            "gray"
                        ),
                        on_click=lambda: DashboardState.set_age_gender_view_mode("destination"),
                        cursor="pointer",
                    ),
                    rx.button(
                        "🏠 居住地",
                        size="1",
                        variant=rx.cond(
                            DashboardState.age_gender_view_mode == "residence",
                            "solid",
                            "outline"
                        ),
                        color_scheme=rx.cond(
                            DashboardState.age_gender_view_mode == "residence",
                            "blue",
                            "gray"
                        ),
                        on_click=lambda: DashboardState.set_age_gender_view_mode("residence"),
                        cursor="pointer",
                    ),
                    spacing="1",
                ),
                rx.fragment(),  # 居住地データがない場合は何も表示しない
            ),
            width="100%",
            align="center",
            margin_bottom="0.5rem",
        ),
        # 現在のモードラベル
        rx.text(
            DashboardState.age_gender_view_label,
            font_size="0.75rem",
            color=MUTED_COLOR,
            margin_bottom="1rem",
        ),
        # グラフ本体（現在のモードに応じたデータを表示）
        rx.recharts.bar_chart(
            rx.recharts.bar(
                data_key="男性",
                name="男性",
                stroke=PRIMARY_COLOR,  # Okabe-Ito: 青 #0072B2
                fill=PRIMARY_COLOR,    # Okabe-Ito: 青 #0072B2
            ),
            rx.recharts.bar(
                data_key="女性",
                name="女性",
                stroke=SECONDARY_COLOR,  # Okabe-Ito: オレンジ #E69F00
                fill=SECONDARY_COLOR,    # Okabe-Ito: オレンジ #E69F00
            ),
            rx.recharts.x_axis(data_key="name", stroke="#94a3b8"),
            rx.recharts.y_axis(stroke="#94a3b8"),
            rx.recharts.legend(),
            rx.recharts.graphing_tooltip(),
            data=DashboardState.overview_age_gender_current_data,  # モード切替対応
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


# cross_urgency_career_age_chart() 削除済み（URGENCY_AGE廃止により不要）


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
                stroke="#0072B2",  # Okabe-Ito: 青
                fill="#0072B2",  # Okabe-Ito: 青
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
    """需給: 需要超過ランキング Top 10（横棒グラフ）

    NOTE: 都道府県内の全市区町村を比較するランキング。
    市区町村を選択しても、同じ都道府県内のランキングが表示される（仕様）。
    """
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.heading("需要超過ランキング Top 10", size="4", color=TEXT_COLOR),
                rx.text(
                    rx.text.span("（", color=MUTED_COLOR),
                    rx.text.span(DashboardState.selected_prefecture, color=ACCENT_5, font_weight="bold"),
                    rx.text.span("内）", color=MUTED_COLOR),
                    font_size="0.9rem"
                ),
                align="baseline",
                spacing="2",
                margin_bottom="0.5rem"
            ),
            rx.text("就業希望者数が居住者数を上回る市区町村（需要超過）", color=MUTED_COLOR, font_size="0.85rem", margin_bottom="1rem"),
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
    """需給: 供給超過ランキング Top 10（横棒グラフ）

    NOTE: 都道府県内の全市区町村を比較するランキング。
    市区町村を選択しても、同じ都道府県内のランキングが表示される（仕様）。
    """
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.heading("供給超過ランキング Top 10", size="4", color=TEXT_COLOR),
                rx.text(
                    rx.text.span("（", color=MUTED_COLOR),
                    rx.text.span(DashboardState.selected_prefecture, color=SUCCESS_COLOR, font_weight="bold"),
                    rx.text.span("内）", color=MUTED_COLOR),
                    font_size="0.9rem"
                ),
                align="baseline",
                spacing="2",
                margin_bottom="0.5rem"
            ),
            rx.text("居住者数が就業希望者数を上回る市区町村（供給超過）", color=MUTED_COLOR, font_size="0.85rem", margin_bottom="1rem"),
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
    """需給: 需給比率ランキング Top 10（横棒グラフ）

    NOTE: 都道府県内の全市区町村を比較するランキング。
    市区町村を選択しても、同じ都道府県内のランキングが表示される（仕様）。
    """
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.heading("需給比率ランキング Top 10", size="4", color=TEXT_COLOR),
                rx.text(
                    rx.text.span("（", color=MUTED_COLOR),
                    rx.text.span(DashboardState.selected_prefecture, color=ACCENT_5, font_weight="bold"),
                    rx.text.span("内）", color=MUTED_COLOR),
                    font_size="0.9rem"
                ),
                align="baseline",
                spacing="2",
                margin_bottom="0.5rem"
            ),
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


# rarity_national_license_ranking_chart() 削除済み（rarity_panel廃止により不要）


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


# urgency_age_chart(), urgency_employment_chart() 削除済み（urgency_panel廃止により不要）


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


# rarity_rank_chart(), rarity_score_chart() 削除済み（rarity_panel廃止により不要）


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


# =====================================
# 新機能UIコンポーネント
# =====================================

def rarity_analysis_section() -> rx.Component:
    """RARITY分析セクション: 年齢×性別×資格の複数選択分析"""
    def render_rarity_item(item):
        """RARITYリストの各アイテムを表示"""
        return rx.hstack(
            rx.text(item["qualification"], font_weight="600", color=TEXT_COLOR, font_size="0.85rem", min_width="120px"),
            rx.text(item["age"], color=MUTED_COLOR, font_size="0.8rem", min_width="50px"),
            rx.text(item["gender"], color=MUTED_COLOR, font_size="0.8rem", min_width="40px"),
            rx.spacer(),
            rx.text(f"{item['count']:,}人", color=PRIMARY_COLOR, font_size="0.85rem", font_weight="500"),
            rx.text(f"({item['share_pct']})", color=MUTED_COLOR, font_size="0.8rem"),
            width="100%", align_items="center"
        )

    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.text("🎯", font_size="1.2rem"),
                rx.heading("人材組み合わせ分析", size="5", color=TEXT_COLOR),
                spacing="2",
                align="center"
            ),
            rx.text("年代・性別・資格を組み合わせて人材を検索", color=MUTED_COLOR, font_size="0.85rem", margin_bottom="1rem"),

            # フィルタセクション
            rx.hstack(
                # 年代選択
                rx.vstack(
                    rx.text("年代", color=MUTED_COLOR, font_size="0.75rem", font_weight="600"),
                    rx.select(
                        DashboardState.rarity_age_options,
                        value=rx.cond(
                            DashboardState.rarity_selected_ages.length() > 0,
                            DashboardState.rarity_selected_ages[0],
                            ""
                        ),
                        placeholder="全年代",
                        on_change=DashboardState.set_rarity_age_single,
                        size="2",
                        style={"minWidth": "100px", "backgroundColor": CARD_BG, "color": TEXT_COLOR, "border": f"1px solid {BORDER_COLOR}", "borderRadius": "6px"}
                    ),
                    spacing="1"
                ),
                # 性別選択
                rx.vstack(
                    rx.text("性別", color=MUTED_COLOR, font_size="0.75rem", font_weight="600"),
                    rx.select(
                        DashboardState.rarity_gender_options,
                        value=rx.cond(
                            DashboardState.rarity_selected_genders.length() > 0,
                            DashboardState.rarity_selected_genders[0],
                            ""
                        ),
                        placeholder="全性別",
                        on_change=DashboardState.set_rarity_gender_single,
                        size="2",
                        style={"minWidth": "80px", "backgroundColor": CARD_BG, "color": TEXT_COLOR, "border": f"1px solid {BORDER_COLOR}", "borderRadius": "6px"}
                    ),
                    spacing="1"
                ),
                # 資格選択
                rx.vstack(
                    rx.text("資格", color=MUTED_COLOR, font_size="0.75rem", font_weight="600"),
                    rx.select(
                        DashboardState.rarity_qualification_options,
                        value=rx.cond(
                            DashboardState.rarity_selected_qualifications.length() > 0,
                            DashboardState.rarity_selected_qualifications[0],
                            ""
                        ),
                        placeholder="全資格",
                        on_change=DashboardState.set_rarity_qualification_single,
                        size="2",
                        style={"minWidth": "150px", "backgroundColor": CARD_BG, "color": TEXT_COLOR, "border": f"1px solid {BORDER_COLOR}", "borderRadius": "6px"}
                    ),
                    spacing="1"
                ),
                spacing="4",
                align="end",
                margin_bottom="1rem",
                wrap="wrap"
            ),

            # サマリー
            rx.cond(
                DashboardState.has_rarity_results,
                rx.hstack(
                    rx.badge(rx.text("該当: ", DashboardState.rarity_total_count, "人"), color_scheme="blue", size="2"),
                    rx.badge(rx.text("組み合わせ: ", DashboardState.rarity_combination_count, "件"), color_scheme="gray", size="2"),
                    spacing="2",
                    margin_bottom="0.5rem"
                ),
                rx.text("")
            ),

            # 結果リスト
            rx.cond(
                DashboardState.has_rarity_results,
                rx.scroll_area(
                    rx.vstack(
                        rx.foreach(DashboardState.rarity_results, render_rarity_item),
                        width="100%", spacing="2"
                    ),
                    type="always",
                    scrollbars="vertical",
                    style={"maxHeight": "300px"}
                ),
                rx.text("フィルタを選択すると結果が表示されます", color=MUTED_COLOR, font_size="0.85rem", padding="1rem", text_align="center")
            ),

            width="100%", spacing="2"
        ),
        background=CARD_BG,
        border_radius="12px",
        border=f"1px solid {BORDER_COLOR}",
        padding="1.5rem",
        width="100%"
    )


def competition_summary_card() -> rx.Component:
    """COMPETITION地域サマリーカード"""
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.text("📊", font_size="1.2rem"),
                rx.heading("地域サマリー", size="5", color=TEXT_COLOR),
                spacing="2",
                align="center"
            ),
            rx.text("選択地域の人材プロファイル概要", color=MUTED_COLOR, font_size="0.85rem", margin_bottom="1rem"),

            rx.cond(
                DashboardState.competition_summary.contains("total_applicants"),
                rx.grid(
                    # 総求職者数
                    rx.box(
                        rx.vstack(
                            rx.text("総求職者数", color=MUTED_COLOR, font_size="0.75rem"),
                            rx.text(f"{DashboardState.competition_summary['total_applicants']:,}人", color=TEXT_COLOR, font_size="1.5rem", font_weight="700"),
                            spacing="1", align="center"
                        ),
                        padding="1rem",
                        background="rgba(59, 130, 246, 0.1)",
                        border_radius="8px"
                    ),
                    # 女性比率
                    rx.box(
                        rx.vstack(
                            rx.text("女性比率", color=MUTED_COLOR, font_size="0.75rem"),
                            rx.text(DashboardState.competition_summary["female_ratio"], color="#E69F00", font_size="1.5rem", font_weight="700"),
                            spacing="1", align="center"
                        ),
                        padding="1rem",
                        background="rgba(230, 159, 0, 0.1)",
                        border_radius="8px"
                    ),
                    # 主要年齢層
                    rx.box(
                        rx.vstack(
                            rx.text("主要年齢層", color=MUTED_COLOR, font_size="0.75rem"),
                            rx.text(DashboardState.competition_summary["top_age"], color=PRIMARY_COLOR, font_size="1.3rem", font_weight="700"),
                            rx.text(f"({DashboardState.competition_summary['top_age_ratio']})", color=MUTED_COLOR, font_size="0.75rem"),
                            spacing="0", align="center"
                        ),
                        padding="1rem",
                        background="rgba(99, 102, 241, 0.1)",
                        border_radius="8px"
                    ),
                    # 平均資格数
                    rx.box(
                        rx.vstack(
                            rx.text("平均資格数", color=MUTED_COLOR, font_size="0.75rem"),
                            rx.hstack(
                                rx.text(DashboardState.competition_summary["avg_qualification_count"], color=SUCCESS_COLOR, font_size="1.5rem", font_weight="700"),
                                rx.text("個", color=MUTED_COLOR, font_size="0.9rem"),
                                align="end", spacing="1"
                            ),
                            spacing="1", align="center"
                        ),
                        padding="1rem",
                        background="rgba(16, 185, 129, 0.1)",
                        border_radius="8px"
                    ),
                    columns="4",
                    spacing="3",
                    width="100%"
                ),
                rx.text("地域データがありません", color=MUTED_COLOR, font_size="0.85rem", padding="1rem")
            ),
            width="100%", spacing="2"
        ),
        background=CARD_BG,
        border_radius="12px",
        border=f"1px solid {BORDER_COLOR}",
        padding="1.5rem",
        width="100%"
    )


def mobility_type_section() -> rx.Component:
    """mobility_type分布セクション（居住地/希望勤務地ベース切替）"""
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.text("🚗", font_size="1.2rem"),
                rx.heading("移動パターン分布", size="5", color=TEXT_COLOR),
                spacing="2",
                align="center"
            ),
            rx.text("居住地から希望勤務地までの移動距離の傾向", color=MUTED_COLOR, font_size="0.85rem", margin_bottom="1rem"),

            # 表示モード切替ボタン
            rx.hstack(
                rx.button(
                    "居住地ベース（地域特性）",
                    on_click=lambda: DashboardState.set_mobility_view_mode("residence"),
                    variant=rx.cond(DashboardState.mobility_view_mode == "residence", "solid", "outline"),
                    color_scheme="blue",
                    size="2"
                ),
                rx.button(
                    "希望勤務地ベース（人気特性）",
                    on_click=lambda: DashboardState.set_mobility_view_mode("destination"),
                    variant=rx.cond(DashboardState.mobility_view_mode == "destination", "solid", "outline"),
                    color_scheme="orange",
                    size="2"
                ),
                spacing="2",
                margin_bottom="1rem"
            ),

            # 説明テキスト
            rx.cond(
                DashboardState.mobility_view_mode == "residence",
                rx.text("この地域に住む人がどの程度の距離を移動して働きたいか", color=MUTED_COLOR, font_size="0.8rem", font_style="italic", margin_bottom="0.5rem"),
                rx.text("この地域で働きたい人がどの程度の距離から来るか", color=MUTED_COLOR, font_size="0.8rem", font_style="italic", margin_bottom="0.5rem")
            ),

            # 棒グラフ
            rx.cond(
                DashboardState.mobility_type_distribution.length() > 0,
                rx.recharts.bar_chart(
                    rx.recharts.bar(
                        data_key="count",
                        fill=rx.cond(DashboardState.mobility_view_mode == "residence", PRIMARY_COLOR, SECONDARY_COLOR),
                        name="人数",
                        radius=[8, 8, 0, 0]
                    ),
                    rx.recharts.x_axis(data_key="type", stroke=BORDER_COLOR),
                    rx.recharts.y_axis(stroke=BORDER_COLOR),
                    rx.recharts.cartesian_grid(stroke_dasharray="3 3", stroke="rgba(255,255,255,0.1)"),
                    rx.recharts.graphing_tooltip(),
                    data=DashboardState.mobility_type_distribution,
                    width="100%",
                    height=280
                ),
                rx.text("移動パターンデータがありません", color=MUTED_COLOR, font_size="0.85rem", padding="1rem")
            ),

            # パーセンテージ表示
            rx.cond(
                DashboardState.mobility_type_distribution.length() > 0,
                rx.hstack(
                    rx.foreach(
                        DashboardState.mobility_type_distribution,
                        lambda item: rx.box(
                            rx.vstack(
                                rx.text(item["type"], color=MUTED_COLOR, font_size="0.7rem"),
                                rx.text(item["pct"], color=TEXT_COLOR, font_size="0.9rem", font_weight="600"),
                                spacing="0", align="center"
                            ),
                            padding="0.5rem",
                            background="rgba(255, 255, 255, 0.05)",
                            border_radius="6px",
                            flex="1"
                        )
                    ),
                    spacing="2",
                    width="100%",
                    margin_top="0.5rem"
                ),
                rx.text("")
            ),

            width="100%", spacing="2"
        ),
        background=CARD_BG,
        border_radius="12px",
        border=f"1px solid {BORDER_COLOR}",
        padding="1.5rem",
        width="100%"
    )


def distance_stats_card() -> rx.Component:
    """距離統計カード（Q25/中央値/Q75）"""
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.text("📏", font_size="1rem"),
                rx.text("移動距離の統計", color=TEXT_COLOR, font_size="0.9rem", font_weight="600"),
                spacing="2",
                align="center"
            ),

            rx.hstack(
                # Q25
                rx.box(
                    rx.vstack(
                        rx.text("25%点", color=MUTED_COLOR, font_size="0.7rem"),
                        rx.hstack(
                            rx.text(DashboardState.mobility_distance_stats["q25"], color=ACCENT_4, font_size="1.2rem", font_weight="700"),
                            rx.text("km", color=MUTED_COLOR, font_size="0.75rem"),
                            align="end", spacing="1"
                        ),
                        spacing="0", align="center"
                    ),
                    padding="0.75rem",
                    background="rgba(20, 184, 166, 0.1)",
                    border_radius="6px",
                    flex="1"
                ),
                # 中央値
                rx.box(
                    rx.vstack(
                        rx.text("中央値", color=MUTED_COLOR, font_size="0.7rem"),
                        rx.hstack(
                            rx.text(DashboardState.mobility_distance_stats["median"], color=PRIMARY_COLOR, font_size="1.2rem", font_weight="700"),
                            rx.text("km", color=MUTED_COLOR, font_size="0.75rem"),
                            align="end", spacing="1"
                        ),
                        spacing="0", align="center"
                    ),
                    padding="0.75rem",
                    background="rgba(99, 102, 241, 0.1)",
                    border_radius="6px",
                    flex="1"
                ),
                # Q75
                rx.box(
                    rx.vstack(
                        rx.text("75%点", color=MUTED_COLOR, font_size="0.7rem"),
                        rx.hstack(
                            rx.text(DashboardState.mobility_distance_stats["q75"], color=SECONDARY_COLOR, font_size="1.2rem", font_weight="700"),
                            rx.text("km", color=MUTED_COLOR, font_size="0.75rem"),
                            align="end", spacing="1"
                        ),
                        spacing="0", align="center"
                    ),
                    padding="0.75rem",
                    background="rgba(236, 72, 153, 0.1)",
                    border_radius="6px",
                    flex="1"
                ),
                spacing="3",
                width="100%"
            ),
            width="100%", spacing="2"
        ),
        background=CARD_BG,
        border_radius="12px",
        border=f"1px solid {BORDER_COLOR}",
        padding="1rem",
        width="100%"
    )


def market_share_section() -> rx.Component:
    """market_share_pct: 年齢×性別のシェア棒グラフ"""
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.text("📊", font_size="1rem"),
                rx.heading("ペルソナシェア（年齢×性別）", size="5", color=TEXT_COLOR),
                spacing="2",
                align="center"
            ),
            rx.text("この地域の人材構成比（年齢×性別）", color=MUTED_COLOR, font_size="0.85rem", margin_bottom="1rem"),

            rx.cond(
                DashboardState.persona_market_share.length() > 0,
                rx.vstack(
                    # 横棒グラフ
                    rx.recharts.bar_chart(
                        rx.recharts.bar(
                            data_key="count",
                            fill=PRIMARY_COLOR,
                            name="人数",
                            radius=[0, 4, 4, 0]
                        ),
                        rx.recharts.x_axis(type_="number", stroke=BORDER_COLOR),
                        rx.recharts.y_axis(data_key="label", type_="category", stroke=BORDER_COLOR, width=100),
                        rx.recharts.cartesian_grid(stroke_dasharray="3 3", stroke="rgba(255,255,255,0.1)"),
                        rx.recharts.graphing_tooltip(),
                        data=DashboardState.persona_market_share,
                        layout="vertical",
                        width="100%",
                        height=350
                    ),
                    # シェア一覧
                    rx.hstack(
                        rx.foreach(
                            DashboardState.persona_market_share[:6],
                            lambda item: rx.badge(f"{item['label']}: {item['share_pct']}", color_scheme="gray", size="1")
                        ),
                        wrap="wrap",
                        spacing="2",
                        margin_top="0.5rem"
                    ),
                    width="100%", spacing="2"
                ),
                rx.text("シェアデータがありません", color=MUTED_COLOR, font_size="0.85rem", padding="1rem")
            ),
            width="100%", spacing="2"
        ),
        background=CARD_BG,
        border_radius="12px",
        border=f"1px solid {BORDER_COLOR}",
        padding="1.5rem",
        width="100%"
    )


def retention_rate_section() -> rx.Component:
    """retention_rate: 資格別定着率セクション"""
    def render_retention_item(item):
        """定着率リストの各アイテム"""
        # 色を定着率に応じて変更
        rate_color = rx.cond(
            item["interpretation"] == "地元志向強",
            SUCCESS_COLOR,
            rx.cond(
                item["interpretation"] == "地元志向",
                "#10b981",
                rx.cond(
                    item["interpretation"] == "平均的",
                    MUTED_COLOR,
                    WARNING_COLOR
                )
            )
        )

        return rx.hstack(
            rx.text(item["qualification"], font_weight="600", color=TEXT_COLOR, font_size="0.85rem", min_width="120px"),
            rx.spacer(),
            rx.text(item["retention_rate"], color=rate_color, font_size="0.9rem", font_weight="600", min_width="50px"),
            rx.badge(item["interpretation"], color_scheme=rx.cond(
                item["interpretation"] == "地元志向強", "green",
                rx.cond(
                    item["interpretation"] == "流出傾向", "red", "gray"
                )
            ), size="1"),
            rx.text(f"({item['count']:,}人)", color=MUTED_COLOR, font_size="0.75rem", min_width="60px"),
            width="100%", align_items="center"
        )

    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.text("🏠", font_size="1rem"),
                rx.heading("資格別定着率", size="5", color=TEXT_COLOR),
                spacing="2",
                align="center"
            ),
            rx.text("資格保有者の地元定着傾向（1.0以上＝地元志向）", color=MUTED_COLOR, font_size="0.85rem", margin_bottom="1rem"),

            rx.cond(
                DashboardState.qualification_retention_rates.length() > 0,
                rx.scroll_area(
                    rx.vstack(
                        rx.foreach(DashboardState.qualification_retention_rates, render_retention_item),
                        width="100%", spacing="2"
                    ),
                    type="always",
                    scrollbars="vertical",
                    style={"maxHeight": "350px"}
                ),
                rx.text("定着率データがありません", color=MUTED_COLOR, font_size="0.85rem", padding="1rem")
            ),

            # 凡例
            rx.hstack(
                rx.badge("≥1.1 地元志向強", color_scheme="green", size="1"),
                rx.badge("≥1.0 地元志向", color_scheme="blue", size="1"),
                rx.badge("≥0.9 平均的", color_scheme="gray", size="1"),
                rx.badge("<0.9 流出傾向", color_scheme="red", size="1"),
                wrap="wrap",
                spacing="2",
                margin_top="1rem"
            ),

            width="100%", spacing="2"
        ),
        background=CARD_BG,
        border_radius="12px",
        border=f"1px solid {BORDER_COLOR}",
        padding="1.5rem",
        width="100%"
    )


def age_gender_stats_section() -> rx.Component:
    """avg_desired_areas/avg_qualifications: 年齢×性別リスト形式"""
    def render_stats_item(item):
        return rx.hstack(
            rx.text(item["label"], font_weight="600", color=TEXT_COLOR, font_size="0.85rem", min_width="80px"),
            rx.spacer(),
            rx.hstack(
                rx.text("希望勤務地:", color=MUTED_COLOR, font_size="0.75rem"),
                rx.text(f"{item['desired_areas']}箇所", color=PRIMARY_COLOR, font_size="0.85rem", font_weight="500"),
                spacing="1"
            ),
            rx.hstack(
                rx.text("資格:", color=MUTED_COLOR, font_size="0.75rem"),
                rx.text(f"{item['qualifications']}個", color=SECONDARY_COLOR, font_size="0.85rem", font_weight="500"),
                spacing="1"
            ),
            width="100%", align_items="center"
        )

    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.text("📋", font_size="1rem"),
                rx.heading("希望勤務地数・資格保有数", size="5", color=TEXT_COLOR),
                spacing="2",
                align="center"
            ),
            rx.text("年齢×性別ごとの平均値", color=MUTED_COLOR, font_size="0.85rem", margin_bottom="1rem"),

            rx.cond(
                DashboardState.age_gender_stats_list.length() > 0,
                rx.vstack(
                    rx.foreach(DashboardState.age_gender_stats_list, render_stats_item),
                    width="100%", spacing="2"
                ),
                rx.text("統計データがありません", color=MUTED_COLOR, font_size="0.85rem", padding="1rem")
            ),
            width="100%", spacing="2"
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


# =====================================
# 3層比較パネル（全国・都道府県・市区町村）
# =====================================

def comparison_metric(metric_data: dict) -> rx.Component:
    """1メトリクスの3層比較表示（全国・都道府県・市区町村）

    Args:
        metric_data: {"label": "希望勤務地数", "unit": "件", "national": 65.6,
                      "pref_pct": 80, "muni_pct": 37, "muni_arrow": "▼", ...}
    """
    return rx.vstack(
        rx.text(
            metric_data["label"],
            color=TEXT_COLOR,
            font_size="0.85rem",
            font_weight="600",
            margin_bottom="0.5rem"
        ),
        # 全国バー（100%基準）
        rx.hstack(
            rx.text("全国", color=MUTED_COLOR, font_size="0.75rem", min_width="60px", text_align="right"),
            rx.box(
                rx.box(width="100%", height="100%", background=PRIMARY_COLOR, border_radius="4px"),
                width="100%", height="18px", background="rgba(255, 255, 255, 0.1)", border_radius="4px", overflow="hidden"
            ),
            rx.text(f"{metric_data['national']}{metric_data['unit']}", color=TEXT_COLOR, font_size="0.8rem", min_width="70px", text_align="right", font_weight="500"),
            width="100%", spacing="2", align_items="center"
        ),
        # 都道府県バー（事前計算済みpref_pct使用）
        rx.hstack(
            rx.text(metric_data["pref_name"], color=MUTED_COLOR, font_size="0.75rem", min_width="60px", text_align="right"),
            rx.box(
                rx.box(
                    width=f"{metric_data['pref_pct']}%",
                    height="100%", background=SECONDARY_COLOR, border_radius="4px", transition="width 0.3s ease"
                ),
                width="100%", height="18px", background="rgba(255, 255, 255, 0.1)", border_radius="4px", overflow="hidden"
            ),
            rx.text(f"{metric_data['prefecture']}{metric_data['unit']}", color=TEXT_COLOR, font_size="0.8rem", min_width="70px", text_align="right", font_weight="500"),
            width="100%", spacing="2", align_items="center"
        ),
        # 市区町村バー（事前計算済みmuni_pct, muni_arrow使用）
        rx.hstack(
            rx.text(metric_data["muni_name"], color=MUTED_COLOR, font_size="0.75rem", min_width="60px", text_align="right"),
            rx.box(
                rx.box(
                    width=f"{metric_data['muni_pct']}%",
                    height="100%", background=ACCENT_4, border_radius="4px", transition="width 0.3s ease"
                ),
                width="100%", height="18px", background="rgba(255, 255, 255, 0.1)", border_radius="4px", overflow="hidden"
            ),
            rx.hstack(
                rx.text(f"{metric_data['municipality']}{metric_data['unit']}", color=TEXT_COLOR, font_size="0.8rem", font_weight="500"),
                rx.text(metric_data["muni_arrow"], color=rx.cond(metric_data["muni_arrow"] == "▲", SUCCESS_COLOR, WARNING_COLOR), font_size="0.75rem"),
                spacing="1", min_width="70px", justify="end"
            ),
            width="100%", spacing="2", align_items="center"
        ),
        width="100%",
        spacing="1",
        margin_bottom="1rem"
    )


def comparison_panel() -> rx.Component:
    """3層比較パネル（全国・都道府県・市区町村）"""
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.text("📊", font_size="1.2rem"),
                rx.text(
                    "地域比較",
                    color=TEXT_COLOR,
                    font_size="1rem",
                    font_weight="600"
                ),
                spacing="2",
                align_items="center"
            ),
            rx.text(
                rx.cond(
                    DashboardState.selected_municipality != "",
                    f"全国 vs {DashboardState.selected_prefecture} vs {DashboardState.selected_municipality}",
                    "地域を選択してください"
                ),
                color=MUTED_COLOR,
                font_size="0.75rem",
                margin_bottom="1rem"
            ),
            # 3メトリクスの比較表示
            rx.cond(
                DashboardState.comparison_data.length() > 0,
                rx.foreach(
                    DashboardState.comparison_data,
                    comparison_metric
                ),
                rx.text(
                    "データがありません",
                    color=MUTED_COLOR,
                    font_size="0.85rem",
                    text_align="center",
                    padding="1rem"
                )
            ),

            # 性別比率セクション
            rx.vstack(
                rx.text(
                    "性別比率",
                    color=TEXT_COLOR,
                    font_size="0.85rem",
                    font_weight="600",
                    margin_bottom="0.5rem",
                    margin_top="1rem"
                ),
                rx.cond(
                    DashboardState.gender_has_data,
                    rx.vstack(
                        # 全国
                        rx.hstack(
                            rx.text("全国", color=PRIMARY_COLOR, font_size="0.75rem", min_width="60px"),
                            rx.box(
                                rx.hstack(
                                    rx.box(
                                        width=DashboardState.gender_national_male_pct.to(str) + "%",
                                        height="100%",
                                        background="#3b82f6",
                                        border_radius="2px 0 0 2px"
                                    ),
                                    rx.box(
                                        width=DashboardState.gender_national_female_pct.to(str) + "%",
                                        height="100%",
                                        background="#ec4899",
                                        border_radius="0 2px 2px 0"
                                    ),
                                    spacing="0",
                                    width="100%",
                                    height="100%"
                                ),
                                width="100%",
                                height="16px",
                                background=CARD_BG,
                                border_radius="2px",
                                overflow="hidden"
                            ),
                            rx.text(
                                rx.text.span("男", color="#3b82f6"),
                                DashboardState.gender_national_male_pct.to(str),
                                "% / ",
                                rx.text.span("女", color="#ec4899"),
                                DashboardState.gender_national_female_pct.to(str),
                                "%",
                                color=MUTED_COLOR,
                                font_size="0.7rem",
                                min_width="100px",
                                text_align="right"
                            ),
                            width="100%",
                            spacing="2",
                            align="center"
                        ),
                        # 都道府県
                        rx.hstack(
                            rx.text(DashboardState.selected_prefecture, color=SECONDARY_COLOR, font_size="0.75rem", min_width="60px"),
                            rx.box(
                                rx.hstack(
                                    rx.box(
                                        width=DashboardState.gender_pref_male_pct.to(str) + "%",
                                        height="100%",
                                        background="#3b82f6",
                                        border_radius="2px 0 0 2px"
                                    ),
                                    rx.box(
                                        width=DashboardState.gender_pref_female_pct.to(str) + "%",
                                        height="100%",
                                        background="#ec4899",
                                        border_radius="0 2px 2px 0"
                                    ),
                                    spacing="0",
                                    width="100%",
                                    height="100%"
                                ),
                                width="100%",
                                height="16px",
                                background=CARD_BG,
                                border_radius="2px",
                                overflow="hidden"
                            ),
                            rx.text(
                                rx.text.span("男", color="#3b82f6"),
                                DashboardState.gender_pref_male_pct.to(str),
                                "% / ",
                                rx.text.span("女", color="#ec4899"),
                                DashboardState.gender_pref_female_pct.to(str),
                                "%",
                                color=MUTED_COLOR,
                                font_size="0.7rem",
                                min_width="100px",
                                text_align="right"
                            ),
                            width="100%",
                            spacing="2",
                            align="center"
                        ),
                        # 市区町村
                        rx.hstack(
                            rx.text(DashboardState.selected_municipality, color=ACCENT_4, font_size="0.75rem", min_width="60px"),
                            rx.box(
                                rx.hstack(
                                    rx.box(
                                        width=DashboardState.gender_muni_male_pct.to(str) + "%",
                                        height="100%",
                                        background="#3b82f6",
                                        border_radius="2px 0 0 2px"
                                    ),
                                    rx.box(
                                        width=DashboardState.gender_muni_female_pct.to(str) + "%",
                                        height="100%",
                                        background="#ec4899",
                                        border_radius="0 2px 2px 0"
                                    ),
                                    spacing="0",
                                    width="100%",
                                    height="100%"
                                ),
                                width="100%",
                                height="16px",
                                background=CARD_BG,
                                border_radius="2px",
                                overflow="hidden"
                            ),
                            rx.text(
                                rx.text.span("男", color="#3b82f6"),
                                DashboardState.gender_muni_male_pct.to(str),
                                "% / ",
                                rx.text.span("女", color="#ec4899"),
                                DashboardState.gender_muni_female_pct.to(str),
                                "%",
                                color=MUTED_COLOR,
                                font_size="0.7rem",
                                min_width="100px",
                                text_align="right"
                            ),
                            width="100%",
                            spacing="2",
                            align="center"
                        ),
                        width="100%",
                        spacing="1"
                    ),
                    rx.text("データなし", color=MUTED_COLOR, font_size="0.8rem")
                ),
                # 性別凡例
                rx.hstack(
                    rx.hstack(
                        rx.box(width="12px", height="12px", background="#3b82f6", border_radius="2px"),
                        rx.text("男性", color=MUTED_COLOR, font_size="0.7rem"),
                        spacing="1"
                    ),
                    rx.hstack(
                        rx.box(width="12px", height="12px", background="#ec4899", border_radius="2px"),
                        rx.text("女性", color=MUTED_COLOR, font_size="0.7rem"),
                        spacing="1"
                    ),
                    spacing="4",
                    margin_top="0.5rem"
                ),
                width="100%",
                spacing="1"
            ),

            # 年齢層分布セクション
            rx.vstack(
                rx.text(
                    "年齢層分布",
                    color=TEXT_COLOR,
                    font_size="0.85rem",
                    font_weight="600",
                    margin_bottom="0.5rem",
                    margin_top="1rem"
                ),
                rx.cond(
                    DashboardState.comparison_age_data.length() > 0,
                    rx.recharts.bar_chart(
                        rx.recharts.bar(data_key="全国", fill=PRIMARY_COLOR, radius=[4, 4, 0, 0]),
                        rx.recharts.bar(data_key="都道府県", fill=SECONDARY_COLOR, radius=[4, 4, 0, 0]),
                        rx.recharts.bar(data_key="市区町村", fill=ACCENT_4, radius=[4, 4, 0, 0]),
                        rx.recharts.x_axis(data_key="name", stroke="#94a3b8", font_size=10),
                        rx.recharts.y_axis(stroke="#94a3b8", font_size=10, unit="%"),
                        rx.recharts.graphing_tooltip(),
                        rx.recharts.legend(),
                        data=DashboardState.comparison_age_data,
                        width="100%",
                        height=180
                    ),
                    rx.text("データなし", color=MUTED_COLOR, font_size="0.8rem")
                ),
                width="100%",
                spacing="1"
            ),

            # 凡例
            rx.hstack(
                rx.hstack(
                    rx.box(width="12px", height="12px", background=PRIMARY_COLOR, border_radius="2px"),
                    rx.text("全国", color=MUTED_COLOR, font_size="0.7rem"),
                    spacing="1"
                ),
                rx.hstack(
                    rx.box(width="12px", height="12px", background=SECONDARY_COLOR, border_radius="2px"),
                    rx.text("都道府県", color=MUTED_COLOR, font_size="0.7rem"),
                    spacing="1"
                ),
                rx.hstack(
                    rx.box(width="12px", height="12px", background=ACCENT_4, border_radius="2px"),
                    rx.text("市区町村", color=MUTED_COLOR, font_size="0.7rem"),
                    spacing="1"
                ),
                spacing="4",
                margin_top="0.5rem"
            ),
            width="100%",
            spacing="1"
        ),
        background=CARD_BG,
        border_radius="12px",
        border=f"1px solid {BORDER_COLOR}",
        padding="1.25rem",
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
            # 3層比較パネル（全国・都道府県・市区町村）
            rx.cond(
                DashboardState.is_loaded,
                rx.box(
                    comparison_panel(),
                    margin_top="1.5rem",
                    width="100%"
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


# supply_panel() 削除済み（V3タブ統合により不要）


# career_panel() 削除済み（V3タブ統合により不要）


# urgency_panel() 削除済み（V3タブ統合により不要）


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

                    # 資格詳細（QUALIFICATION_DETAIL）全資格一覧
                    rx.text("資格詳細（全資格一覧）", font_size="0.9rem", color=MUTED_COLOR, font_weight="600", margin_top="2rem", margin_bottom="1rem"),
                    rx.box(
                        rx.scroll_area(
                            rx.vstack(
                                rx.foreach(
                                    DashboardState.qualification_detail_top,
                                    lambda item: rx.hstack(
                                        rx.text(item["qualification"], font_weight="600", color=TEXT_COLOR, font_size="0.9rem"),
                                        rx.spacer(),
                                        rx.text(f"{item['count']:,}件", color=MUTED_COLOR, font_size="0.9rem"),
                                        rx.text(f"国家資格比率: {item['national_ratio']}", color=MUTED_COLOR, font_size="0.85rem"),
                                        width="100%", align_items="center"
                                    )
                                ),
                                width="100%", spacing="2"
                            ),
                            type="always",
                            scrollbars="vertical",
                            style={"maxHeight": "400px"}
                        ),
                        background=CARD_BG,
                        border_radius="12px",
                        border=f"1px solid {BORDER_COLOR}",
                        padding="1.5rem",
                        width="100%"
                    ),

                    # 保有資格ペルソナ（具体的資格×性別×年齢）クロス集計
                    rx.text("保有資格ペルソナ（主要資格Top10×性別×年齢）", font_size="0.9rem", color=MUTED_COLOR, font_weight="600", margin_top="2rem", margin_bottom="1rem"),
                    rx.box(
                        rx.vstack(
                            # グループ化棒グラフ（主要資格Top10の男女別保有者数）
                            rx.text("主要資格Top10 保有者数（男女別）", font_size="0.85rem", color=MUTED_COLOR, margin_bottom="0.5rem"),
                            rx.recharts.bar_chart(
                                rx.recharts.bar(
                                    data_key="男性",
                                    fill="#0072B2",  # Okabe-Ito: 男性（濃い青）
                                    name="男性",
                                ),
                                rx.recharts.bar(
                                    data_key="女性",
                                    fill="#E69F00",  # Okabe-Ito: 女性（オレンジ）
                                    name="女性",
                                ),
                                rx.recharts.x_axis(data_key="name", angle=-45, text_anchor="end", height=100),
                                rx.recharts.y_axis(),
                                rx.recharts.cartesian_grid(stroke_dasharray="3 3"),
                                rx.recharts.legend(),
                                rx.recharts.graphing_tooltip(),
                                data=DashboardState.qualification_persona_chart_data,
                                width="100%",
                                height=350,
                            ),

                            # 資格選択プルダウン付き年齢層×性別分布
                            rx.hstack(
                                rx.text("資格選択:", font_size="0.85rem", color=MUTED_COLOR, font_weight="600"),
                                rx.select(
                                    DashboardState.available_qualifications,
                                    value=DashboardState.selected_qualification_display,
                                    on_change=DashboardState.set_qualification,
                                    placeholder="資格を選択",
                                    size="2",
                                    style={
                                        "minWidth": "200px",
                                        "backgroundColor": CARD_BG,
                                        "color": TEXT_COLOR,
                                        "border": f"1px solid {BORDER_COLOR}",
                                        "borderRadius": "8px"
                                    }
                                ),
                                rx.text("の年齢層×性別分布", font_size="0.85rem", color=MUTED_COLOR),
                                align="center",
                                margin_top="1.5rem",
                                margin_bottom="0.5rem",
                                spacing="3"
                            ),
                            rx.recharts.bar_chart(
                                rx.recharts.bar(
                                    data_key="男性",
                                    fill="#0072B2",  # Okabe-Ito: 男性（濃い青）
                                    name="男性",
                                ),
                                rx.recharts.bar(
                                    data_key="女性",
                                    fill="#E69F00",  # Okabe-Ito: 女性（オレンジ）
                                    name="女性",
                                ),
                                rx.recharts.x_axis(data_key="name"),
                                rx.recharts.y_axis(),
                                rx.recharts.cartesian_grid(stroke_dasharray="3 3"),
                                rx.recharts.legend(),
                                rx.recharts.graphing_tooltip(),
                                data=DashboardState.selected_qualification_age_chart_data,
                                width="100%",
                                height=280,
                            ),

                            # マトリックステーブル（資格×性別×人数）
                            rx.text("資格別 男女別保有者数一覧", font_size="0.85rem", color=MUTED_COLOR, margin_top="1.5rem", margin_bottom="0.5rem"),
                            rx.scroll_area(
                                rx.table.root(
                                    rx.table.header(
                                        rx.table.row(
                                            rx.table.column_header_cell("資格名", style={"color": TEXT_COLOR, "backgroundColor": CARD_BG, "minWidth": "180px"}),
                                            rx.table.column_header_cell("合計", style={"color": TEXT_COLOR, "backgroundColor": CARD_BG}),
                                            rx.table.column_header_cell("男性", style={"color": "#0072B2", "backgroundColor": CARD_BG}),  # Okabe-Ito: 濃い青
                                            rx.table.column_header_cell("女性", style={"color": "#E69F00", "backgroundColor": CARD_BG}),
                                        )
                                    ),
                                    rx.table.body(
                                        rx.foreach(
                                            DashboardState.qualification_persona_matrix,
                                            lambda item: rx.table.row(
                                                rx.table.cell(item["qualification"], style={"color": TEXT_COLOR, "fontWeight": "600", "fontSize": "0.85rem"}),
                                                rx.table.cell(f"{item['total']:,}人", style={"color": TEXT_COLOR, "fontWeight": "bold"}),
                                                rx.table.cell(f"{item['male_total']:,}人", style={"color": "#0072B2"}),  # Okabe-Ito
                                                rx.table.cell(f"{item['female_total']:,}人", style={"color": "#E69F00"}),
                                            )
                                        )
                                    ),
                                    style={"width": "100%", "borderCollapse": "collapse"}
                                ),
                                type="always",
                                scrollbars="horizontal",
                                style={"maxWidth": "100%"}
                            ),
                            width="100%", spacing="3"
                        ),
                        background=CARD_BG,
                        border_radius="12px",
                        border=f"1px solid {BORDER_COLOR}",
                        padding="1.5rem",
                        width="100%"
                    ),

                    # === 新機能: 人材組み合わせ分析（RARITY） ===
                    rx.text("人材組み合わせ分析（年代×性別×資格）", font_size="0.9rem", color=MUTED_COLOR, font_weight="600", margin_top="2rem", margin_bottom="1rem"),
                    rarity_analysis_section(),

                    # === 新機能: ペルソナシェア（年齢×性別） ===
                    rx.text("ペルソナシェア（年齢×性別）", font_size="0.9rem", color=MUTED_COLOR, font_weight="600", margin_top="2rem", margin_bottom="1rem"),
                    market_share_section(),

                    # === 新機能: 希望勤務地数・資格保有数 ===
                    rx.text("希望勤務地数・資格保有数（年齢×性別）", font_size="0.9rem", color=MUTED_COLOR, font_weight="600", margin_top="2rem", margin_bottom="1rem"),
                    age_gender_stats_section(),

                    width="100%", spacing="3"
                ),
                rx.text("CSVファイルをアップロードしてください", color=MUTED_COLOR, font_size="0.9rem", text_align="center", padding="3rem")
            ),
            width="100%", spacing="3"
        ),
        display=rx.cond(DashboardState.active_tab == "persona", "block", "none"),
        width="100%", padding="2rem"
    )


# cross_panel() 削除済み（V3タブ統合により不要）


# flow_panel() 削除済み（V3タブ統合により不要）


def gap_panel() -> rx.Component:
    """gapパネル: 需給バランス（GAS完全再現版）

    NOTE: KPIカードは選択した市区町村のデータを表示。
    ランキングは都道府県内の全市区町村を比較（市区町村選択では変わらない）。
    """
    return rx.box(
        rx.vstack(
            rx.heading("需給バランス", size="6", color=TEXT_COLOR, margin_bottom="1.5rem"),
            rx.cond(
                DashboardState.is_loaded,
                rx.vstack(
                    # 選択地域表示
                    rx.hstack(
                        rx.text("📍 選択中: ", color=MUTED_COLOR, font_size="0.9rem"),
                        rx.text(DashboardState.selected_prefecture, color=ACCENT_5, font_weight="bold", font_size="0.9rem"),
                        rx.cond(
                            DashboardState.selected_municipality != "",
                            rx.text(
                                rx.text.span(" / ", color=MUTED_COLOR),
                                rx.text.span(DashboardState.selected_municipality, color=WARNING_COLOR, font_weight="bold"),
                                font_size="0.9rem"
                            ),
                            rx.text(" (都道府県全体)", color=MUTED_COLOR, font_size="0.85rem", font_style="italic")
                        ),
                        align="center",
                        margin_bottom="1rem"
                    ),
                    # KPIカード（5枚）- 選択地域のデータ
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


# rarity_panel() 削除済み（V3タブ統合により不要）


# competition_panel() 削除済み（V3タブ統合により不要）


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


def region_panel() -> rx.Component:
    """地域・移動パターンパネル（Tab 3）

    整理されたUI:
    - 人材フロー分析（流入・地元・流出）
    - 居住地→希望地フロー（どこからどこへ移動したいか）
    """
    return rx.box(
        rx.vstack(
            rx.cond(
                DashboardState.is_loaded,
                rx.vstack(
                    # タイトル
                    rx.heading("🗺️ 地域・移動パターン", size="7", color=TEXT_COLOR, margin_bottom="1.5rem"),

                    # カード1: 人材フロー分析（流入・地元・流出）
                    rx.box(
                        rx.vstack(
                            rx.hstack(
                                rx.text("📊", font_size="1.2rem"),
                                rx.heading("人材フロー分析", size="5", color=TEXT_COLOR),
                                spacing="2",
                                align="center"
                            ),
                            rx.text("選択エリアへの就職希望者の流入・流出を分析", color=MUTED_COLOR, font_size="0.85rem", margin_bottom="1rem"),

                            # サマリーKPI
                            rx.cond(
                                DashboardState.talent_flow_has_data,
                                rx.hstack(
                                    # 流入総数
                                    rx.box(
                                        rx.vstack(
                                            rx.text("流入（就職希望）", color=MUTED_COLOR, font_size="0.75rem"),
                                            rx.hstack(
                                                rx.text(DashboardState.talent_flow_inflow_total.to_string(), color="#10b981", font_size="1.8rem", font_weight="700"),
                                                rx.text("人", color=MUTED_COLOR, font_size="0.9rem"),
                                                align="end", spacing="1"
                                            ),
                                            spacing="1", align="center"
                                        ),
                                        padding="1rem",
                                        background="rgba(16, 185, 129, 0.1)",
                                        border_radius="8px",
                                        flex="1"
                                    ),
                                    # 地元志向
                                    rx.box(
                                        rx.vstack(
                                            rx.text("地元志向率", color=MUTED_COLOR, font_size="0.75rem"),
                                            rx.hstack(
                                                rx.text(DashboardState.talent_flow_local_pct.to_string(), color="#f59e0b", font_size="1.8rem", font_weight="700"),
                                                rx.text("%", color=MUTED_COLOR, font_size="0.9rem"),
                                                align="end", spacing="1"
                                            ),
                                            rx.text(f"({DashboardState.talent_flow_local_count.to_string()}人)", color=MUTED_COLOR, font_size="0.7rem"),
                                            spacing="1", align="center"
                                        ),
                                        padding="1rem",
                                        background="rgba(245, 158, 11, 0.1)",
                                        border_radius="8px",
                                        flex="1"
                                    ),
                                    # 流出総数
                                    rx.box(
                                        rx.vstack(
                                            rx.text("流出（他地域希望）", color=MUTED_COLOR, font_size="0.75rem"),
                                            rx.hstack(
                                                rx.text(DashboardState.talent_flow_outflow_total.to_string(), color="#ef4444", font_size="1.8rem", font_weight="700"),
                                                rx.text("人", color=MUTED_COLOR, font_size="0.9rem"),
                                                align="end", spacing="1"
                                            ),
                                            spacing="1", align="center"
                                        ),
                                        padding="1rem",
                                        background="rgba(239, 68, 68, 0.1)",
                                        border_radius="8px",
                                        flex="1"
                                    ),
                                    # 流入/流出比
                                    rx.box(
                                        rx.vstack(
                                            rx.text("人材吸引力", color=MUTED_COLOR, font_size="0.75rem"),
                                            rx.text(DashboardState.talent_flow_ratio, color=PRIMARY_COLOR, font_size="1.5rem", font_weight="700"),
                                            spacing="1", align="center"
                                        ),
                                        padding="1rem",
                                        background="rgba(59, 130, 246, 0.1)",
                                        border_radius="8px",
                                        flex="1"
                                    ),
                                    spacing="3",
                                    width="100%",
                                    margin_bottom="1.5rem"
                                ),
                                rx.text("市区町村を選択すると人材フローを表示します", color=MUTED_COLOR, font_size="0.85rem", padding="1rem")
                            ),

                            # 2カラムグリッド: 流入元 + 流出先
                            rx.cond(
                                DashboardState.talent_flow_has_data,
                                rx.grid(
                                    # 流入元Top
                                    rx.box(
                                        rx.hstack(
                                            rx.box(width="12px", height="12px", background="#10b981", border_radius="2px"),
                                            rx.text("流入元（どこから来るか）", color=TEXT_COLOR, font_size="0.9rem", font_weight="600"),
                                            spacing="2", align="center", margin_bottom="0.75rem"
                                        ),
                                        rx.vstack(
                                            rx.foreach(
                                                DashboardState.talent_flow_inflow_sources,
                                                lambda item: rx.hstack(
                                                    rx.cond(
                                                        item["is_local"],
                                                        rx.badge("地元", color_scheme="amber", size="1"),
                                                        rx.text("")
                                                    ),
                                                    rx.text(item["name"], color=TEXT_COLOR, font_size="0.85rem", flex="1"),
                                                    rx.text(f"{item['value']:,}人", color=MUTED_COLOR, font_size="0.85rem"),
                                                    width="100%", align_items="center"
                                                )
                                            ),
                                            spacing="2", width="100%"
                                        ),
                                        padding="1rem",
                                        background="rgba(16, 185, 129, 0.08)",
                                        border_radius="8px"
                                    ),
                                    # 流出先Top
                                    rx.box(
                                        rx.hstack(
                                            rx.box(width="12px", height="12px", background="#ef4444", border_radius="2px"),
                                            rx.text("流出先（どこへ流れるか）", color=TEXT_COLOR, font_size="0.9rem", font_weight="600"),
                                            spacing="2", align="center", margin_bottom="0.75rem"
                                        ),
                                        rx.cond(
                                            DashboardState.talent_flow_outflow_total > 0,
                                            rx.vstack(
                                                rx.foreach(
                                                    DashboardState.talent_flow_outflow_destinations,
                                                    lambda item: rx.hstack(
                                                        rx.text(item["name"], color=TEXT_COLOR, font_size="0.85rem", flex="1"),
                                                        rx.text(f"{item['value']:,}人", color=MUTED_COLOR, font_size="0.85rem"),
                                                        width="100%", align_items="center"
                                                    )
                                                ),
                                                spacing="2", width="100%"
                                            ),
                                            rx.text("流出データなし（地元志向が高いエリアです）", color=MUTED_COLOR, font_size="0.85rem", padding="0.5rem")
                                        ),
                                        padding="1rem",
                                        background="rgba(239, 68, 68, 0.08)",
                                        border_radius="8px"
                                    ),
                                    columns="2",
                                    spacing="4",
                                    width="100%"
                                ),
                                rx.text("")
                            ),
                            width="100%", spacing="2"
                        ),
                        background=CARD_BG,
                        border_radius="12px",
                        border=f"1px solid {BORDER_COLOR}",
                        padding="1.5rem",
                        margin_bottom="1.5rem",
                        width="100%"
                    ),

                    # カード2: 居住地→希望地フロー
                    rx.box(
                        rx.vstack(
                            rx.hstack(
                                rx.text("🔀", font_size="1.2rem"),
                                rx.heading("居住地→希望地フロー", size="5", color=TEXT_COLOR),
                                spacing="2",
                                align="center"
                            ),
                            rx.text("現住所からどこへ移動したいかの流れを可視化", color=MUTED_COLOR, font_size="0.85rem", margin_bottom="1rem"),

                            # 2カラム: 都道府県フロー + 市区町村フロー
                            rx.grid(
                                # 都道府県フローTop10
                                rx.box(
                                    rx.text("都道府県間の移動フロー Top10", color=TEXT_COLOR, font_size="0.9rem", font_weight="600", margin_bottom="0.75rem"),
                                    rx.vstack(
                                        rx.foreach(
                                            DashboardState.residence_flow_top,
                                            lambda item: rx.hstack(
                                                rx.text(item['origin_pref'], color=PRIMARY_COLOR, font_size="0.85rem", font_weight="500"),
                                                rx.text("→", color=MUTED_COLOR, font_size="0.85rem"),
                                                rx.text(item['dest_pref'], color=SECONDARY_COLOR, font_size="0.85rem", font_weight="500"),
                                                rx.spacer(),
                                                rx.text(f"{item['count']:,}件", color=MUTED_COLOR, font_size="0.8rem"),
                                                width="100%", align_items="center"
                                            )
                                        ),
                                        spacing="2",
                                        width="100%"
                                    ),
                                    padding="1rem",
                                    background="rgba(255, 255, 255, 0.03)",
                                    border_radius="8px",
                                    border=f"1px solid {BORDER_COLOR}"
                                ),
                                # 市区町村フローTop10（横棒グラフ）
                                rx.box(
                                    rx.text("市区町村間の移動フロー Top10", color=TEXT_COLOR, font_size="0.9rem", font_weight="600", margin_bottom="0.75rem"),
                                    rx.recharts.bar_chart(
                                        rx.recharts.bar(data_key="value", fill=SECONDARY_COLOR, radius=[0, 4, 4, 0]),
                                        rx.recharts.x_axis(data_key="value", type_="number", stroke=BORDER_COLOR, tick_font_size=10),
                                        rx.recharts.y_axis(data_key="label", type_="category", stroke=BORDER_COLOR, width=140, tick_font_size=10),
                                        rx.recharts.graphing_tooltip(),
                                        data=DashboardState.residence_flow_top_muni,
                                        layout="vertical",
                                        width="100%",
                                        height=320
                                    ),
                                    padding="0.5rem"
                                ),
                                columns="2",
                                spacing="4",
                                width="100%"
                            ),
                            width="100%", spacing="2"
                        ),
                        background=CARD_BG,
                        border_radius="12px",
                        border=f"1px solid {BORDER_COLOR}",
                        padding="1.5rem",
                        width="100%"
                    ),

                    # === 新機能: 地域サマリー（COMPETITION） ===
                    competition_summary_card(),

                    # === 新機能: 移動パターン分布（mobility_type） ===
                    mobility_type_section(),

                    # === 新機能: 距離統計（Q25/中央値/Q75） ===
                    distance_stats_card(),

                    # === 新機能: 資格別定着率（retention_rate） ===
                    retention_rate_section(),

                    width="100%", spacing="3"
                ),
                rx.text("CSVファイルをアップロードしてください", color=MUTED_COLOR, font_size="0.9rem", text_align="center", padding="3rem")
            ),
            width="100%", spacing="3"
        ),
        display=rx.cond(DashboardState.active_tab == "region", "block", "none"),
        width="100%", padding="2rem"
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
    """5パネル表示エリア（V3対応: TAB_CONSOLIDATION_PLAN_V2.md準拠）

    旧11タブから5タブに統合:
    - Tab 1: 市場概況（overview_panel）
    - Tab 2: 人材属性（persona_panel + QUALIFICATION_DETAIL）
    - Tab 3: 地域・移動パターン（region_panel: DESIRED_AREA_PATTERN + RESIDENCE_FLOW）
    - Tab 4: 需給バランス（gap_panel）
    - Tab 5: 求人地図（jobmap_panel: 別プロジェクト要件で維持）

    削除されたタブ: supply, career, urgency, cross, flow, rarity, competition
    """
    return rx.vstack(
        overview_panel(),
        persona_panel(),
        region_panel(),  # V3新規
        gap_panel(),
        jobmap_panel(),
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
app.add_page(index, route="/", on_load=DashboardState.on_mount_init)
