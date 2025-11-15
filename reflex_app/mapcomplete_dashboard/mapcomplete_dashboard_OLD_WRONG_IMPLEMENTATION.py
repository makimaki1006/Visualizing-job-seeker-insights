"""
MapComplete統合ダッシュボード - Reflex完全移行版（MVP→段階的実装）
GAS統合ダッシュボードの10タブ + 11 row_types を完全再現

Phase 1: CSVロード + サマリー表示（MVP）
Phase 2: 10タブ完全実装
Phase 3: Plotlyグラフ統合
"""

import reflex as rx
import pandas as pd
import plotly.graph_objects as go
from typing import List, Dict, Any
import json
from pathlib import Path

# カラースキーム（GAS統合ダッシュボード配色）
BG_COLOR = "#0d1525"                    # 深いネイビー基調
PANEL_BG = "rgba(12, 20, 37, 0.95)"    # サイドバー：半透明濃紺
CARD_BG = "rgba(15, 23, 42, 0.82)"     # カード背景
TEXT_COLOR = "#f8fafc"                  # 文字
MUTED_COLOR = "rgba(226, 232, 240, 0.75)"  # 補助文字
BORDER_COLOR = "rgba(148, 163, 184, 0.22)" # 枠線
PRIMARY_COLOR = "#38bdf8"               # メインアクセント（青）
SECONDARY_COLOR = "#f97316"             # オレンジ
WARNING_COLOR = "#FF6B6B"
INFO_COLOR = "#95A5A6"

# 都道府県リスト
PREFECTURE_LIST = [
    "北海道", "青森県", "岩手県", "宮城県", "秋田県", "山形県", "福島県",
    "茨城県", "栃木県", "群馬県", "埼玉県", "千葉県", "東京都", "神奈川県",
    "新潟県", "富山県", "石川県", "福井県", "山梨県", "長野県", "岐阜県",
    "静岡県", "愛知県", "三重県", "滋賀県", "京都府", "大阪府", "兵庫県",
    "奈良県", "和歌山県", "鳥取県", "島根県", "岡山県", "広島県", "山口県",
    "徳島県", "香川県", "愛媛県", "高知県", "福岡県", "佐賀県", "長崎県",
    "熊本県", "大分県", "宮崎県", "鹿児島県", "沖縄県"
]


class State(rx.State):
    """Reflexセッション管理State（各ユーザー独立）"""

    # データ
    df: pd.DataFrame = pd.DataFrame()
    is_loaded: bool = False

    # UI状態
    selected_prefecture: str = "東京都"
    selected_municipality: str = ""

    # 統計
    total_rows: int = 0
    row_type_counts: Dict[str, int] = {}

    # フィルタ済みデータ
    filtered_summary: Dict[str, Any] = {}
    filtered_age_gender: List[Dict[str, Any]] = []
    filtered_persona: List[Dict[str, Any]] = []
    filtered_flow: List[Dict[str, Any]] = []
    filtered_gap: List[Dict[str, Any]] = []
    filtered_rarity: List[Dict[str, Any]] = []
    filtered_competition: List[Dict[str, Any]] = []
    filtered_career: List[Dict[str, Any]] = []
    filtered_urgency_age: List[Dict[str, Any]] = []
    filtered_urgency_employment: List[Dict[str, Any]] = []

    async def handle_upload(self, files: list[rx.UploadFile]):
        """CSVファイルアップロード処理"""
        if not files:
            return

        for file in files:
            upload_data = await file.read()

            try:
                # pandasでCSV読み込み
                import io
                self.df = pd.read_csv(io.BytesIO(upload_data), encoding='utf-8-sig', low_memory=False)
                self.total_rows = len(self.df)
                self.is_loaded = True

                # row_type別件数
                if 'row_type' in self.df.columns:
                    self.row_type_counts = self.df['row_type'].value_counts().to_dict()

                print(f"[SUCCESS] CSVロード成功: {self.total_rows}行 x {len(self.df.columns)}列")

                # 初期フィルタ
                self.update_filtered_data()

            except Exception as e:
                print(f"[ERROR] CSVロードエラー: {e}")

    def load_default_csv(self):
        """デフォルトCSVを読み込み（起動時のフォールバック）"""
        csv_path = Path(__file__).parent / "MapComplete_Complete_All_FIXED.csv"

        if not csv_path.exists():
            print(f"[INFO] デフォルトCSVが見つかりません: {csv_path}")
            print(f"[INFO] CSVファイルをアップロードしてください")
            return

        try:
            self.df = pd.read_csv(csv_path, encoding='utf-8-sig', low_memory=False)
            self.total_rows = len(self.df)
            self.is_loaded = True

            # row_type別件数
            if 'row_type' in self.df.columns:
                self.row_type_counts = self.df['row_type'].value_counts().to_dict()

            print(f"[SUCCESS] デフォルトCSVロード成功: {self.total_rows}行 x {len(self.df.columns)}列")

            # 初期フィルタ
            self.update_filtered_data()

        except Exception as e:
            print(f"[ERROR] CSVロードエラー: {e}")

    def on_prefecture_change(self, value: str):
        """都道府県選択変更"""
        self.selected_prefecture = value
        self.selected_municipality = ""
        self.update_filtered_data()

    def on_municipality_change(self, value: str):
        """市区町村選択変更"""
        self.selected_municipality = value
        self.update_filtered_data()

    def update_filtered_data(self):
        """選択地域のデータをフィルタ"""
        if self.df.empty:
            return

        # 都道府県フィルタ
        df_pref = self.df[self.df['prefecture'] == self.selected_prefecture].copy()

        # 市区町村フィルタ（選択時のみ）
        if self.selected_municipality:
            df_filtered = df_pref[df_pref['municipality'] == self.selected_municipality].copy()
        else:
            df_filtered = df_pref

        # SUMMARYデータフィルタ
        summary_rows = df_filtered[df_filtered['row_type'] == 'SUMMARY']
        if len(summary_rows) > 0:
            row = summary_rows.iloc[0]
            self.filtered_summary = {
                'applicant_count': int(row.get('applicant_count', 0)) if pd.notna(row.get('applicant_count')) else 0,
                'avg_age': float(row.get('avg_age', 0)) if pd.notna(row.get('avg_age')) else 0,
                'male_ratio': float(row.get('male_ratio', 0)) if pd.notna(row.get('male_ratio')) else 0,
                'female_ratio': float(row.get('female_ratio', 0)) if pd.notna(row.get('female_ratio')) else 0
            }
        else:
            self.filtered_summary = {}

        # AGE_GENDERデータフィルタ
        age_gender_rows = df_filtered[df_filtered['row_type'] == 'AGE_GENDER']
        if len(age_gender_rows) > 0:
            self.filtered_age_gender = age_gender_rows[['category1', 'category2', 'count']].to_dict('records')
        else:
            self.filtered_age_gender = []

        # PERSONA_MUNIデータフィルタ
        persona_rows = df_filtered[df_filtered['row_type'] == 'PERSONA_MUNI']
        if len(persona_rows) > 0:
            self.filtered_persona = persona_rows[['category1', 'count']].to_dict('records')
        else:
            self.filtered_persona = []

        # FLOWデータフィルタ
        flow_rows = df_filtered[df_filtered['row_type'] == 'FLOW']
        if len(flow_rows) > 0:
            # municipalityがある行のみ（NaNは都道府県全体なので除外）
            flow_rows_muni = flow_rows[flow_rows['municipality'].notna()].copy()
            self.filtered_flow = flow_rows_muni[['municipality', 'inflow', 'outflow', 'net_flow']].to_dict('records')
        else:
            self.filtered_flow = []

        # GAPデータフィルタ
        gap_rows = df_filtered[df_filtered['row_type'] == 'GAP']
        if len(gap_rows) > 0:
            # municipalityがある行のみ
            gap_rows_muni = gap_rows[gap_rows['municipality'].notna()].copy()
            self.filtered_gap = gap_rows_muni[['municipality', 'demand_count', 'supply_count', 'gap']].to_dict('records')
        else:
            self.filtered_gap = []

        # RARITYデータフィルタ
        rarity_rows = df_filtered[df_filtered['row_type'] == 'RARITY']
        if len(rarity_rows) > 0:
            # municipalityがある行のみ、重複削除
            rarity_rows_muni = rarity_rows[rarity_rows['municipality'].notna()].copy()
            rarity_rows_muni = rarity_rows_muni.drop_duplicates(subset=['municipality'])
            self.filtered_rarity = rarity_rows_muni[['municipality', 'rarity_score']].to_dict('records')
        else:
            self.filtered_rarity = []

        # COMPETITIONデータフィルタ
        competition_rows = df_filtered[df_filtered['row_type'] == 'COMPETITION']
        if len(competition_rows) > 0:
            # municipalityがある行のみ、市町村ごとに集約
            competition_rows_muni = competition_rows[competition_rows['municipality'].notna()].copy()
            # 市町村ごとにfemale_ratioとtop_age_ratioの平均を計算
            comp_grouped = competition_rows_muni.groupby('municipality').agg({
                'female_ratio': 'mean',
                'top_age_ratio': 'mean'
            }).reset_index()
            self.filtered_competition = comp_grouped.to_dict('records')
        else:
            self.filtered_competition = []

        # CAREER_CROSSデータフィルタ
        career_rows = df_filtered[df_filtered['row_type'] == 'CAREER_CROSS']
        if len(career_rows) > 0:
            # 学歴（category1）と年齢層（category2）の組み合わせでカウント集計
            career_grouped = career_rows.groupby(['category1', 'category2']).size().reset_index(name='count')
            self.filtered_career = career_grouped.to_dict('records')
        else:
            self.filtered_career = []

        # URGENCY_AGEデータフィルタ
        urgency_age_rows = df_filtered[df_filtered['row_type'] == 'URGENCY_AGE']
        if len(urgency_age_rows) > 0:
            # municipalityがある行のみ、市町村×年齢層でグループ化
            urgency_muni = urgency_age_rows[urgency_age_rows['municipality'].notna()].copy()
            if len(urgency_muni) > 0:
                # 市町村×年齢層で集計（countの合計）
                urgency_grouped = urgency_muni.groupby(['municipality', 'category2'])['count'].sum().reset_index()
                self.filtered_urgency_age = urgency_grouped.to_dict('records')
            else:
                self.filtered_urgency_age = []
        else:
            self.filtered_urgency_age = []

        # URGENCY_EMPLOYMENTデータフィルタ
        urgency_emp_rows = df_filtered[df_filtered['row_type'] == 'URGENCY_EMPLOYMENT']
        if len(urgency_emp_rows) > 0:
            # municipalityがある行のみ、市町村×就業状況でグループ化
            urgency_emp_muni = urgency_emp_rows[urgency_emp_rows['municipality'].notna()].copy()
            if len(urgency_emp_muni) > 0:
                # 市町村×就業状況で集計（countの合計）
                urgency_emp_grouped = urgency_emp_muni.groupby(['municipality', 'category2'])['count'].sum().reset_index()
                self.filtered_urgency_employment = urgency_emp_grouped.to_dict('records')
            else:
                self.filtered_urgency_employment = []
        else:
            self.filtered_urgency_employment = []

    @rx.var
    def municipality_list(self) -> List[str]:
        """選択都道府県の市区町村リスト"""
        if self.df.empty:
            return []

        munis = self.df[
            self.df['prefecture'] == self.selected_prefecture
        ]['municipality'].dropna().unique().tolist()

        return sorted(munis)

    @rx.var
    def has_summary_data(self) -> bool:
        """SUMMARYデータ存在チェック"""
        return len(self.filtered_summary) > 0

    @rx.var
    def has_age_gender_data(self) -> bool:
        """AGE_GENDERデータ存在チェック"""
        return len(self.filtered_age_gender) > 0

    @rx.var
    def age_gender_chart_data(self) -> str:
        """AGE_GENDER Plotlyグラフデータ（JSON）"""
        if not self.has_age_gender_data:
            return "{}"

        # データを年齢層と性別で集計
        df_chart = pd.DataFrame(self.filtered_age_gender)

        # 年齢層の順序定義
        age_order = ['20代', '30代', '40代', '50代', '60代', '70代以上']

        # Plotly図作成
        fig = go.Figure()

        # 女性データ
        female_data = df_chart[df_chart['category2'] == '女性'].copy()
        if len(female_data) > 0:
            female_data['category1'] = pd.Categorical(female_data['category1'], categories=age_order, ordered=True)
            female_data = female_data.sort_values('category1')
            fig.add_trace(go.Bar(
                name='女性',
                x=female_data['category1'],
                y=female_data['count'],
                marker_color='#FF69B4'
            ))

        # 男性データ
        male_data = df_chart[df_chart['category2'] == '男性'].copy()
        if len(male_data) > 0:
            male_data['category1'] = pd.Categorical(male_data['category1'], categories=age_order, ordered=True)
            male_data = male_data.sort_values('category1')
            fig.add_trace(go.Bar(
                name='男性',
                x=male_data['category1'],
                y=male_data['count'],
                marker_color='#4169E1'
            ))

        # レイアウト設定
        fig.update_layout(
            title='年齢層×性別 求職者分布',
            xaxis_title='年齢層',
            yaxis_title='求職者数（人）',
            barmode='group',
            height=500,
            template='plotly_white',
            font=dict(family='Noto Sans JP, sans-serif', size=12),
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
        )

        return fig.to_json()

    @rx.var
    def has_persona_data(self) -> bool:
        """PERSONA_MUNIデータ存在チェック"""
        return len(self.filtered_persona) > 0

    @rx.var
    def persona_chart_data(self) -> str:
        """PERSONA_MUNI Plotlyグラフデータ（JSON）"""
        if not self.has_persona_data:
            return "{}"

        # データを人数降順でソート
        df_chart = pd.DataFrame(self.filtered_persona)
        df_chart = df_chart.sort_values('count', ascending=True)  # Plotlyは下から上なので昇順

        # 上位20件のみ表示（多すぎる場合）
        if len(df_chart) > 20:
            df_chart = df_chart.tail(20)

        # Plotly図作成（横棒グラフ）
        fig = go.Figure()

        fig.add_trace(go.Bar(
            y=df_chart['category1'],
            x=df_chart['count'],
            orientation='h',
            marker_color=PRIMARY_COLOR,
            text=df_chart['count'],
            textposition='outside'
        ))

        # レイアウト設定
        fig.update_layout(
            title='ペルソナ別 求職者分布（上位20件）',
            xaxis_title='求職者数（人）',
            yaxis_title='ペルソナ',
            height=600,
            template='plotly_white',
            font=dict(family='Noto Sans JP, sans-serif', size=10),
            margin=dict(l=250, r=50, t=60, b=50)
        )

        return fig.to_json()

    @rx.var
    def has_flow_data(self) -> bool:
        """FLOWデータ存在チェック"""
        return len(self.filtered_flow) > 0

    @rx.var
    def flow_chart_data(self) -> str:
        """FLOW Plotlyグラフデータ（JSON）"""
        if not self.has_flow_data:
            return "{}"

        # データを純流入数の降順でソート
        df_chart = pd.DataFrame(self.filtered_flow)
        df_chart = df_chart.sort_values('net_flow', ascending=True)  # Plotlyは下から上

        # 上位15件のみ表示
        if len(df_chart) > 15:
            df_chart = df_chart.tail(15)

        # Plotly図作成（グループ化棒グラフ）
        fig = go.Figure()

        fig.add_trace(go.Bar(
            name='流入',
            y=df_chart['municipality'],
            x=df_chart['inflow'],
            orientation='h',
            marker_color='#50C878'
        ))

        fig.add_trace(go.Bar(
            name='流出',
            y=df_chart['municipality'],
            x=df_chart['outflow'],
            orientation='h',
            marker_color='#FF6B6B'
        ))

        fig.add_trace(go.Bar(
            name='純流入',
            y=df_chart['municipality'],
            x=df_chart['net_flow'],
            orientation='h',
            marker_color=PRIMARY_COLOR
        ))

        # レイアウト設定
        fig.update_layout(
            title='市区町村別 人材フロー分析（上位15件）',
            xaxis_title='人数',
            yaxis_title='市区町村',
            barmode='group',
            height=600,
            template='plotly_white',
            font=dict(family='Noto Sans JP, sans-serif', size=10),
            margin=dict(l=150, r=50, t=60, b=50),
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
        )

        return fig.to_json()

    @rx.var
    def has_gap_data(self) -> bool:
        """GAPデータ存在チェック"""
        return len(self.filtered_gap) > 0

    @rx.var
    def gap_chart_data(self) -> str:
        """GAP Plotlyグラフデータ（JSON）"""
        if not self.has_gap_data:
            return "{}"

        # データをギャップ降順でソート
        df_chart = pd.DataFrame(self.filtered_gap)
        df_chart = df_chart.sort_values('gap', ascending=True)  # Plotlyは下から上

        # 上位15件のみ表示
        if len(df_chart) > 15:
            df_chart = df_chart.tail(15)

        # Plotly図作成（複合グラフ）
        fig = go.Figure()

        # 需要（棒グラフ）
        fig.add_trace(go.Bar(
            name='需要',
            y=df_chart['municipality'],
            x=df_chart['demand_count'],
            orientation='h',
            marker_color='#FF6B6B'
        ))

        # 供給（棒グラフ）
        fig.add_trace(go.Bar(
            name='供給',
            y=df_chart['municipality'],
            x=df_chart['supply_count'],
            orientation='h',
            marker_color='#50C878'
        ))

        # ギャップ（折れ線グラフ）
        fig.add_trace(go.Scatter(
            name='ギャップ',
            y=df_chart['municipality'],
            x=df_chart['gap'],
            mode='lines+markers',
            marker=dict(size=8, color=PRIMARY_COLOR),
            line=dict(width=3, color=PRIMARY_COLOR)
        ))

        # レイアウト設定
        fig.update_layout(
            title='市区町村別 需給ギャップ分析（上位15件）',
            xaxis_title='人数',
            yaxis_title='市区町村',
            height=600,
            template='plotly_white',
            font=dict(family='Noto Sans JP, sans-serif', size=10),
            margin=dict(l=150, r=50, t=60, b=50),
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
        )

        return fig.to_json()

    @rx.var
    def has_rarity_data(self) -> bool:
        """RARITYデータ存在チェック"""
        return len(self.filtered_rarity) > 0

    @rx.var
    def rarity_chart_data(self) -> str:
        """RARITY Plotlyグラフデータ（JSON）"""
        if not self.has_rarity_data:
            return "{}"

        # データを希少度スコア降順でソート
        df_chart = pd.DataFrame(self.filtered_rarity)
        df_chart = df_chart.sort_values('rarity_score', ascending=True)  # Plotlyは下から上

        # 上位20件のみ表示
        if len(df_chart) > 20:
            df_chart = df_chart.tail(20)

        # Plotly図作成（横棒グラフ）
        fig = go.Figure()

        fig.add_trace(go.Bar(
            y=df_chart['municipality'],
            x=df_chart['rarity_score'],
            orientation='h',
            marker_color='#FFD700',
            text=[f"{s:.2f}" for s in df_chart['rarity_score']],
            textposition='outside'
        ))

        # レイアウト設定
        fig.update_layout(
            title='市区町村別 希少人材スコア（上位20件）',
            xaxis_title='希少度スコア',
            yaxis_title='市区町村',
            height=600,
            template='plotly_white',
            font=dict(family='Noto Sans JP, sans-serif', size=10),
            margin=dict(l=150, r=50, t=60, b=50),
            xaxis=dict(range=[0, 1.1])
        )

        return fig.to_json()

    @rx.var
    def has_competition_data(self) -> bool:
        """COMPETITIONデータ存在チェック"""
        return len(self.filtered_competition) > 0

    @rx.var
    def competition_chart_data(self) -> str:
        """COMPETITION Plotlyグラフデータ（JSON）"""
        if not self.has_competition_data:
            return "{}"

        # データを女性比率降順でソート
        df_chart = pd.DataFrame(self.filtered_competition)
        df_chart = df_chart.sort_values('female_ratio', ascending=True)  # Plotlyは下から上

        # 上位15件のみ表示
        if len(df_chart) > 15:
            df_chart = df_chart.tail(15)

        # Plotly図作成（グループ化棒グラフ）
        fig = go.Figure()

        fig.add_trace(go.Bar(
            name='女性比率',
            y=df_chart['municipality'],
            x=df_chart['female_ratio'] * 100,  # パーセント表示
            orientation='h',
            marker_color='#FF69B4'
        ))

        fig.add_trace(go.Bar(
            name='主要年齢層比率',
            y=df_chart['municipality'],
            x=df_chart['top_age_ratio'] * 100,  # パーセント表示
            orientation='h',
            marker_color=PRIMARY_COLOR
        ))

        # レイアウト設定
        fig.update_layout(
            title='市区町村別 競争プロファイル（上位15件）',
            xaxis_title='比率（%）',
            yaxis_title='市区町村',
            barmode='group',
            height=600,
            template='plotly_white',
            font=dict(family='Noto Sans JP, sans-serif', size=10),
            margin=dict(l=150, r=50, t=60, b=50),
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
            xaxis=dict(range=[0, 105])
        )

        return fig.to_json()

    @rx.var
    def has_career_data(self) -> bool:
        """CAREER_CROSSデータ存在チェック"""
        return len(self.filtered_career) > 0

    @rx.var
    def career_chart_data(self) -> str:
        """CAREER_CROSS Plotlyヒートマップデータ（JSON）"""
        if not self.has_career_data:
            return "{}"

        # データをDataFrameに変換
        df_career = pd.DataFrame(self.filtered_career)

        # ピボットテーブル作成（学歴×年齢層）
        pivot = df_career.pivot_table(
            index='category1',
            columns='category2',
            values='count',
            aggfunc='sum',
            fill_value=0
        )

        # 年齢層の順序を定義
        age_order = ['20代', '30代', '40代', '50代', '60代', '70歳以上']
        existing_ages = [age for age in age_order if age in pivot.columns]
        pivot = pivot[existing_ages]

        # 合計数でソート（降順）
        pivot['total'] = pivot.sum(axis=1)
        pivot = pivot.sort_values('total', ascending=False)
        pivot = pivot.drop('total', axis=1)

        # 上位15件のみ表示
        if len(pivot) > 15:
            pivot = pivot.head(15)

        # Plotlyヒートマップ作成
        fig = go.Figure(data=go.Heatmap(
            z=pivot.values,
            x=pivot.columns,
            y=pivot.index,
            colorscale='YlOrRd',
            text=pivot.values,
            texttemplate='%{text}',
            textfont={"size": 10},
            colorbar=dict(title='件数')
        ))

        fig.update_layout(
            title='学歴×年齢層 ヒートマップ（上位15学歴）',
            xaxis_title='年齢層',
            yaxis_title='学歴',
            height=700,
            template='plotly_white',
            font=dict(family='Noto Sans JP, sans-serif', size=10),
            margin=dict(l=250, r=50, t=60, b=80)
        )

        return fig.to_json()

    @rx.var
    def has_urgency_age_data(self) -> bool:
        """URGENCY_AGEデータ存在チェック"""
        return len(self.filtered_urgency_age) > 0

    @rx.var
    def urgency_age_chart_data(self) -> str:
        """URGENCY_AGE Plotly積み上げ棒グラフデータ（JSON）"""
        if not self.has_urgency_age_data:
            return "{}"

        # データをDataFrameに変換
        df_urgency = pd.DataFrame(self.filtered_urgency_age)

        # ピボットテーブル作成（市町村×年齢層）
        pivot = df_urgency.pivot_table(
            index='municipality',
            columns='category2',
            values='count',
            aggfunc='sum',
            fill_value=0
        )

        # 年齢層の順序を定義
        age_order = ['20代', '30代', '40代', '50代', '60代', '70歳以上']
        existing_ages = [age for age in age_order if age in pivot.columns]
        pivot = pivot[existing_ages]

        # 合計数でソート（降順）
        pivot['total'] = pivot.sum(axis=1)
        pivot = pivot.sort_values('total', ascending=True)  # 水平棒グラフのため昇順
        pivot = pivot.drop('total', axis=1)

        # 上位15件のみ表示
        if len(pivot) > 15:
            pivot = pivot.tail(15)

        # Plotly積み上げ棒グラフ作成
        fig = go.Figure()

        colors = ['#FF6B6B', '#FFA07A', '#FFD700', '#98D8C8', '#6495ED', '#9370DB']
        for i, age_group in enumerate(pivot.columns):
            fig.add_trace(go.Bar(
                name=age_group,
                y=pivot.index,
                x=pivot[age_group],
                orientation='h',
                marker_color=colors[i % len(colors)]
            ))

        fig.update_layout(
            title='市区町村別 年齢層分布（上位15件）',
            xaxis_title='件数',
            yaxis_title='市区町村',
            barmode='stack',
            height=600,
            template='plotly_white',
            font=dict(family='Noto Sans JP, sans-serif', size=10),
            margin=dict(l=150, r=50, t=60, b=50),
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
        )

        return fig.to_json()

    @rx.var
    def has_urgency_employment_data(self) -> bool:
        """URGENCY_EMPLOYMENTデータ存在チェック"""
        return len(self.filtered_urgency_employment) > 0

    @rx.var
    def urgency_employment_chart_data(self) -> str:
        """URGENCY_EMPLOYMENT Plotly積み上げ棒グラフデータ（JSON）"""
        if not self.has_urgency_employment_data:
            return "{}"

        # データをDataFrameに変換
        df_urgency_emp = pd.DataFrame(self.filtered_urgency_employment)

        # ピボットテーブル作成（市町村×就業状況）
        pivot = df_urgency_emp.pivot_table(
            index='municipality',
            columns='category2',
            values='count',
            aggfunc='sum',
            fill_value=0
        )

        # 就業状況の順序を定義
        employment_order = ['在学中', '無職中', '在職中']
        existing_emp = [emp for emp in employment_order if emp in pivot.columns]
        pivot = pivot[existing_emp]

        # 合計数でソート（降順）
        pivot['total'] = pivot.sum(axis=1)
        pivot = pivot.sort_values('total', ascending=True)  # 水平棒グラフのため昇順
        pivot = pivot.drop('total', axis=1)

        # 上位15件のみ表示
        if len(pivot) > 15:
            pivot = pivot.tail(15)

        # Plotly積み上げ棒グラフ作成
        fig = go.Figure()

        colors = ['#4ECDC4', '#FF6B6B', '#95E1D3']
        for i, emp_status in enumerate(pivot.columns):
            fig.add_trace(go.Bar(
                name=emp_status,
                y=pivot.index,
                x=pivot[emp_status],
                orientation='h',
                marker_color=colors[i % len(colors)]
            ))

        fig.update_layout(
            title='市区町村別 就業状況分布（上位15件）',
            xaxis_title='件数',
            yaxis_title='市区町村',
            barmode='stack',
            height=600,
            template='plotly_white',
            font=dict(family='Noto Sans JP, sans-serif', size=10),
            margin=dict(l=150, r=50, t=60, b=50),
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
        )

        return fig.to_json()


def metric_card(title: str, value: str, icon: str, color: str = PRIMARY_COLOR) -> rx.Component:
    """メトリックカード"""
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.text(icon, font_size="2rem"),
                rx.heading(title, size="3", color="#6C757D"),
                spacing="2"
            ),
            rx.heading(value, size="6", color=color),
            spacing="2",
            align="start"
        ),
        padding="1.5rem",
        border_radius="12px",
        box_shadow="0 4px 6px rgba(0,0,0,0.1)",
        background="white",
        width="100%"
    )


def sidebar() -> rx.Component:
    """サイドバー（地域選択）- GAS配色適用"""
    return rx.box(
        rx.vstack(
            rx.heading("MapComplete Dashboard", size="5", margin_bottom="1.5rem", color=TEXT_COLOR, letter_spacing="0.08em"),

            # CSVアップロード
            rx.vstack(
                rx.text("CSVファイル", font_weight="600", margin_bottom="0.5rem", font_size="0.9rem", color=MUTED_COLOR),
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
                            "または、ドラッグ&ドロップ",
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
                rx.foreach(
                    rx.selected_files("csv_upload"),
                    lambda file: rx.text(file, font_size="0.8rem", color=PRIMARY_COLOR)
                ),
                rx.button(
                    "読み込み開始",
                    on_click=State.handle_upload(rx.upload_files(upload_id="csv_upload")),
                    bg=SECONDARY_COLOR,
                    color=TEXT_COLOR,
                    border_radius="8px",
                    padding="0.6rem 1.2rem",
                    font_size="0.85rem",
                    width="100%",
                    margin_top="0.5rem"
                ),
                width="100%"
            ),

            rx.divider(margin_y="1.5rem", border_color=BORDER_COLOR),

            # 都道府県
            rx.text("都道府県", font_weight="600", margin_bottom="0.5rem", font_size="0.9rem", color=MUTED_COLOR),
            rx.select(
                PREFECTURE_LIST,
                value=State.selected_prefecture,
                on_change=State.on_prefecture_change,
                size="3",
                width="100%"
            ),

            # 市区町村
            rx.text("市区町村", font_weight="600", margin_top="1rem", margin_bottom="0.5rem", font_size="0.9rem", color=MUTED_COLOR),
            rx.select(
                State.municipality_list,
                value=State.selected_municipality,
                on_change=State.on_municipality_change,
                placeholder="全市区町村",
                size="3",
                width="100%"
            ),

            rx.divider(margin_y="1.5rem", border_color=BORDER_COLOR),

            # データ統計
            rx.heading("データ統計", size="4", margin_bottom="1rem", color=TEXT_COLOR),
            rx.text(f"総行数: {State.total_rows:,}行", font_size="0.9rem", color=MUTED_COLOR),

            rx.cond(
                State.row_type_counts,
                rx.vstack(
                    rx.text("row_type別件数:", font_weight="600", margin_top="1rem", font_size="0.9rem", color=MUTED_COLOR),
                    rx.foreach(
                        State.row_type_counts.items(),
                        lambda item: rx.text(f"{item[0]}: {item[1]:,}件", font_size="0.85rem", color=MUTED_COLOR)
                    ),
                    spacing="1",
                    align="start",
                    width="100%"
                )
            ),

            spacing="2",
            width="100%",
            padding="1.5rem",
            align="start"
        ),
        width="300px",
        height="100vh",
        background=PANEL_BG,
        border_right=f"1px solid {BORDER_COLOR}",
        overflow_y="auto",
        position="fixed",
        box_shadow="-18px 0 40px rgba(10, 20, 40, 0.35)",
        backdrop_filter="blur(12px)"
    )


def tab_summary() -> rx.Component:
    """📊 サマリータブ"""
    return rx.box(
        rx.vstack(
            rx.heading("📊 基礎集計サマリー", size="6", margin_bottom="2rem"),

            rx.cond(
                State.has_summary_data,
                rx.grid(
                    metric_card(
                        "申請者数",
                        f"{State.filtered_summary.get('applicant_count', 0):,}人",
                        "👥",
                        PRIMARY_COLOR
                    ),
                    metric_card(
                        "平均年齢",
                        f"{State.filtered_summary.get('avg_age', 0):.1f}歳",
                        "📅",
                        SECONDARY_COLOR
                    ),
                    metric_card(
                        "男性比率",
                        f"{State.filtered_summary.get('male_ratio', 0):.1f}%",
                        "♂",
                        "#3498DB"
                    ),
                    metric_card(
                        "女性比率",
                        f"{State.filtered_summary.get('female_ratio', 0):.1f}%",
                        "♀",
                        "#E74C3C"
                    ),
                    columns="4",
                    spacing="4",
                    width="100%"
                ),
                rx.box(
                    rx.text("❌ 選択地域のサマリーデータがありません", color=WARNING_COLOR, font_size="1.2rem"),
                    padding="2rem",
                    border_radius="8px",
                    background="#FFF3CD",
                    border="1px solid #FFC107"
                )
            ),

            spacing="4",
            width="100%"
        ),
        padding="2rem"
    )


def tab_age_gender() -> rx.Component:
    """👥 年齢×性別タブ"""
    return rx.box(
        rx.vstack(
            rx.heading("👥 年齢層×性別 求職者分布", size="6", margin_bottom="2rem"),

            rx.cond(
                State.has_age_gender_data,
                rx.box(
                    rx.html(
                        f"""
                        <div id="age-gender-chart"></div>
                        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
                        <script>
                            var data = {State.age_gender_chart_data};
                            Plotly.newPlot('age-gender-chart', data.data, data.layout, {{responsive: true}});
                        </script>
                        """
                    ),
                    width="100%"
                ),
                rx.box(
                    rx.text("❌ 選択地域の年齢×性別データがありません", color=WARNING_COLOR, font_size="1.2rem"),
                    padding="2rem",
                    border_radius="8px",
                    background="#FFF3CD",
                    border="1px solid #FFC107"
                )
            ),

            spacing="4",
            width="100%"
        ),
        padding="2rem"
    )


def tab_persona() -> rx.Component:
    """🎯 ペルソナ分析タブ"""
    return rx.box(
        rx.vstack(
            rx.heading("🎯 ペルソナ別 求職者分布", size="6", margin_bottom="2rem"),

            rx.cond(
                State.has_persona_data,
                rx.box(
                    rx.html(
                        f"""
                        <div id="persona-chart"></div>
                        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
                        <script>
                            var data = {State.persona_chart_data};
                            Plotly.newPlot('persona-chart', data.data, data.layout, {{responsive: true}});
                        </script>
                        """
                    ),
                    width="100%"
                ),
                rx.box(
                    rx.text("❌ 選択地域のペルソナデータがありません", color=WARNING_COLOR, font_size="1.2rem"),
                    padding="2rem",
                    border_radius="8px",
                    background="#FFF3CD",
                    border="1px solid #FFC107"
                )
            ),

            spacing="4",
            width="100%"
        ),
        padding="2rem"
    )


def tab_flow() -> rx.Component:
    """🌊 フロー分析タブ"""
    return rx.box(
        rx.vstack(
            rx.heading("🌊 市区町村別 人材フロー分析", size="6", margin_bottom="2rem"),

            rx.cond(
                State.has_flow_data,
                rx.box(
                    rx.html(
                        f"""
                        <div id="flow-chart"></div>
                        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
                        <script>
                            var data = {State.flow_chart_data};
                            Plotly.newPlot('flow-chart', data.data, data.layout, {{responsive: true}});
                        </script>
                        """
                    ),
                    width="100%"
                ),
                rx.box(
                    rx.text("❌ 選択地域のフローデータがありません", color=WARNING_COLOR, font_size="1.2rem"),
                    padding="2rem",
                    border_radius="8px",
                    background="#FFF3CD",
                    border="1px solid #FFC107"
                )
            ),

            spacing="4",
            width="100%"
        ),
        padding="2rem"
    )


def tab_gap() -> rx.Component:
    """📈 需給ギャップタブ"""
    return rx.box(
        rx.vstack(
            rx.heading("📈 市区町村別 需給ギャップ分析", size="6", margin_bottom="2rem"),

            rx.cond(
                State.has_gap_data,
                rx.box(
                    rx.html(
                        f"""
                        <div id="gap-chart"></div>
                        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
                        <script>
                            var data = {State.gap_chart_data};
                            Plotly.newPlot('gap-chart', data.data, data.layout, {{responsive: true}});
                        </script>
                        """
                    ),
                    width="100%"
                ),
                rx.box(
                    rx.text("❌ 選択地域の需給ギャップデータがありません", color=WARNING_COLOR, font_size="1.2rem"),
                    padding="2rem",
                    border_radius="8px",
                    background="#FFF3CD",
                    border="1px solid #FFC107"
                )
            ),

            spacing="4",
            width="100%"
        ),
        padding="2rem"
    )


def tab_rarity() -> rx.Component:
    """💎 希少人材タブ"""
    return rx.box(
        rx.vstack(
            rx.heading("💎 市区町村別 希少人材スコア", size="6", margin_bottom="2rem"),

            rx.cond(
                State.has_rarity_data,
                rx.box(
                    rx.html(
                        f"""
                        <div id="rarity-chart"></div>
                        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
                        <script>
                            var data = {State.rarity_chart_data};
                            Plotly.newPlot('rarity-chart', data.data, data.layout, {{responsive: true}});
                        </script>
                        """
                    ),
                    width="100%"
                ),
                rx.box(
                    rx.text("❌ 選択地域の希少人材データがありません", color=WARNING_COLOR, font_size="1.2rem"),
                    padding="2rem",
                    border_radius="8px",
                    background="#FFF3CD",
                    border="1px solid #FFC107"
                )
            ),

            spacing="4",
            width="100%"
        ),
        padding="2rem"
    )


def tab_competition() -> rx.Component:
    """🏆 競争プロファイルタブ"""
    return rx.box(
        rx.vstack(
            rx.heading("🏆 市区町村別 競争プロファイル", size="6", margin_bottom="2rem"),

            rx.cond(
                State.has_competition_data,
                rx.box(
                    rx.html(
                        f"""
                        <div id="competition-chart"></div>
                        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
                        <script>
                            var data = {State.competition_chart_data};
                            Plotly.newPlot('competition-chart', data.data, data.layout, {{responsive: true}});
                        </script>
                        """
                    ),
                    width="100%"
                ),
                rx.box(
                    rx.text("❌ 選択地域の競争プロファイルデータがありません", color=WARNING_COLOR, font_size="1.2rem"),
                    padding="2rem",
                    border_radius="8px",
                    background="#FFF3CD",
                    border="1px solid #FFC107"
                )
            ),

            spacing="4",
            width="100%"
        ),
        padding="2rem"
    )


def tab_career() -> rx.Component:
    """💼 キャリア×年齢タブ"""
    return rx.box(
        rx.vstack(
            rx.heading("💼 学歴×年齢層 クロス分析", size="6", margin_bottom="2rem"),

            rx.cond(
                State.has_career_data,
                rx.box(
                    rx.html(
                        f"""
                        <div id="career-chart"></div>
                        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
                        <script>
                            var data = {State.career_chart_data};
                            Plotly.newPlot('career-chart', data.data, data.layout, {{responsive: true}});
                        </script>
                        """
                    ),
                    width="100%"
                ),
                rx.box(
                    rx.text("❌ 選択地域のキャリア×年齢データがありません", color=WARNING_COLOR, font_size="1.2rem"),
                    padding="2rem",
                    border_radius="8px",
                    background="#FFF3CD",
                    border="1px solid #FFC107"
                )
            ),

            spacing="4",
            width="100%"
        ),
        padding="2rem"
    )


def tab_urgency_age() -> rx.Component:
    """⏰ 緊急度×年齢タブ"""
    return rx.box(
        rx.vstack(
            rx.heading("⏰ 市区町村別 年齢層分布（緊急度分析）", size="6", margin_bottom="2rem"),

            rx.cond(
                State.has_urgency_age_data,
                rx.box(
                    rx.html(
                        f"""
                        <div id="urgency-age-chart"></div>
                        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
                        <script>
                            var data = {State.urgency_age_chart_data};
                            Plotly.newPlot('urgency-age-chart', data.data, data.layout, {{responsive: true}});
                        </script>
                        """
                    ),
                    width="100%"
                ),
                rx.box(
                    rx.text("❌ 選択地域の緊急度×年齢データがありません", color=WARNING_COLOR, font_size="1.2rem"),
                    padding="2rem",
                    border_radius="8px",
                    background="#FFF3CD",
                    border="1px solid #FFC107"
                )
            ),

            spacing="4",
            width="100%"
        ),
        padding="2rem"
    )


def tab_urgency_employment() -> rx.Component:
    """💼 緊急度×就業タブ"""
    return rx.box(
        rx.vstack(
            rx.heading("💼 市区町村別 就業状況分布（緊急度分析）", size="6", margin_bottom="2rem"),

            rx.cond(
                State.has_urgency_employment_data,
                rx.box(
                    rx.html(
                        f"""
                        <div id="urgency-employment-chart"></div>
                        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
                        <script>
                            var data = {State.urgency_employment_chart_data};
                            Plotly.newPlot('urgency-employment-chart', data.data, data.layout, {{responsive: true}});
                        </script>
                        """
                    ),
                    width="100%"
                ),
                rx.box(
                    rx.text("❌ 選択地域の緊急度×就業データがありません", color=WARNING_COLOR, font_size="1.2rem"),
                    padding="2rem",
                    border_radius="8px",
                    background="#FFF3CD",
                    border="1px solid #FFC107"
                )
            ),

            spacing="4",
            width="100%"
        ),
        padding="2rem"
    )


def tab_placeholder(title: str, icon: str) -> rx.Component:
    """プレースホルダータブ（Phase 2で実装）"""
    return rx.box(
        rx.vstack(
            rx.heading(f"{icon} {title}", size="6", margin_bottom="1rem"),
            rx.text("このタブは次のフェーズで実装予定です。", color=INFO_COLOR),
            spacing="4"
        ),
        padding="2rem"
    )


def main_content() -> rx.Component:
    """メインコンテンツ（タブ）"""
    return rx.box(
        rx.tabs.root(
            rx.tabs.list(
                rx.tabs.trigger("📊 サマリー", value="summary"),
                rx.tabs.trigger("👥 年齢×性別", value="age_gender"),
                rx.tabs.trigger("🎯 ペルソナ", value="persona"),
                rx.tabs.trigger("🌊 フロー", value="flow"),
                rx.tabs.trigger("📈 需給", value="gap"),
                rx.tabs.trigger("💎 希少", value="rarity"),
                rx.tabs.trigger("🏆 競争", value="competition"),
                rx.tabs.trigger("💼 キャリア", value="career"),
                rx.tabs.trigger("⏰ 緊急度×年齢", value="urgency_age"),
                rx.tabs.trigger("💼 緊急度×就業", value="urgency_employment"),
                justify="start"
            ),

            rx.tabs.content(tab_summary(), value="summary"),
            rx.tabs.content(tab_age_gender(), value="age_gender"),
            rx.tabs.content(tab_persona(), value="persona"),
            rx.tabs.content(tab_flow(), value="flow"),
            rx.tabs.content(tab_gap(), value="gap"),
            rx.tabs.content(tab_rarity(), value="rarity"),
            rx.tabs.content(tab_competition(), value="competition"),
            rx.tabs.content(tab_career(), value="career"),
            rx.tabs.content(tab_urgency_age(), value="urgency_age"),
            rx.tabs.content(tab_urgency_employment(), value="urgency_employment"),

            default_value="summary",
            width="100%"
        ),
        margin_left="300px",
        height="100vh",
        overflow_y="auto",
        background=BG_COLOR,
        padding="2rem"
    )


def index() -> rx.Component:
    """メインページ"""
    return rx.fragment(
        # CSVロード（初回レンダリング時）
        rx.script("console.log('MapComplete Dashboard initialized')"),
        rx.moment(on_mount=State.load_default_csv),

        # レイアウト
        rx.box(
            sidebar(),
            main_content(),
            width="100%",
            height="100vh",
            background=f"radial-gradient(circle at top left, #0f172a 0%, #1e293b 65%)"
        )
    )


# Reflexアプリ
app = rx.App(
    style={
        "font_family": "Noto Sans JP, -apple-system, BlinkMacSystemFont, sans-serif",
        "color": TEXT_COLOR,
    }
)
app.add_page(index, title="MapComplete統合ダッシュボード")
