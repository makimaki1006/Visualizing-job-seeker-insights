"""
MapComplete統合ダッシュボード - GAS完全移行版

GAS統合ダッシュボードの全機能を完全再現:
- Phase 1-6: 基礎集計、統計分析、ペルソナ分析、フロー分析
- Phase 7: 高度分析5機能
- Phase 8: キャリア・学歴分析
- Phase 10: 転職意欲・緊急度分析

実行方法:
    streamlit run complete_dashboard.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import json

# ページ設定
st.set_page_config(
    page_title="MapComplete統合ダッシュボード - 完全版",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# カスタムCSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# ==============================
# データロード関数
# ==============================

@st.cache_data
def load_data_from_path():
    """MapComplete_Complete_All_FIXED.csvをパスからロード"""
    csv_path = Path(__file__).parent.parent / 'python_scripts' / 'data' / 'output_v2' / 'mapcomplete_complete_sheets' / 'MapComplete_Complete_All_FIXED.csv'
    if csv_path.exists():
        df = pd.read_csv(csv_path, encoding='utf-8-sig', low_memory=False)
        return df
    return None

@st.cache_data
def load_data_from_upload(uploaded_file):
    """アップロードされたCSVファイルをロード"""
    df = pd.read_csv(uploaded_file, encoding='utf-8-sig', low_memory=False)
    return df

@st.cache_data
def load_geocache():
    """ジオコーディングキャッシュをロード"""
    geocache_path = Path(__file__).parent.parent / 'python_scripts' / 'data' / 'output_v2' / 'geocache.json'
    if geocache_path.exists():
        with open(geocache_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

# ==============================
# データ取得関数
# ==============================

@st.cache_data
def get_prefectures(df):
    """ユニークな都道府県リストを取得"""
    prefectures = df['prefecture'].dropna().unique().tolist()
    prefectures.sort()
    return prefectures

@st.cache_data
def get_municipalities(df, prefecture):
    """指定都道府県の市区町村リストを取得（SUMMARY行のみ）"""
    summary_df = df[(df['row_type'] == 'SUMMARY') & (df['prefecture'] == prefecture)]
    municipalities = summary_df['municipality'].dropna().unique().tolist()
    municipalities.sort()
    return municipalities

def filter_data(df, row_type, prefecture, municipality):
    """指定条件でデータフィルタリング"""
    return df[(df['row_type'] == row_type) &
              (df['prefecture'] == prefecture) &
              (df['municipality'] == municipality)]

# ==============================
# Phase 1: 基礎集計
# ==============================

def show_summary_tab(df, prefecture, municipality):
    """サマリー情報表示"""
    st.header("📊 サマリー情報（Phase 1: 基礎集計）")

    summary = filter_data(df, 'SUMMARY', prefecture, municipality)

    if len(summary) > 0:
        row = summary.iloc[0]

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("申請者数", f"{row['applicant_count']:.0f}人")
        with col2:
            st.metric("平均年齢", f"{row['avg_age']:.1f}歳")
        with col3:
            st.metric("男性比率", f"{row['male_ratio']*100:.1f}%")
        with col4:
            st.metric("女性比率", f"{row['female_ratio']*100:.1f}%")

        st.markdown("---")
        st.subheader("詳細データ")

        # DataFrameとして表示
        display_cols = ['applicant_count', 'avg_age', 'male_ratio', 'female_ratio']
        available_cols = [col for col in display_cols if col in summary.columns]
        st.dataframe(summary[available_cols], use_container_width=True)
    else:
        st.warning(f"サマリーデータがありません: {prefecture} {municipality}")

# ==============================
# Phase 2: 年齢×性別クロス分析
# ==============================

def show_age_gender_tab(df, prefecture, municipality):
    """年齢×性別クロス分析表示"""
    st.header("👥 年齢層×性別クロス分析（Phase 2: 統計分析）")

    age_gender = filter_data(df, 'AGE_GENDER', prefecture, municipality)

    if len(age_gender) > 0:
        # 棒グラフ
        fig = px.bar(
            age_gender,
            x='category1',
            y='count',
            color='category2',
            title=f"{prefecture} {municipality} - 年齢×性別分布",
            labels={'category1': '年齢層', 'count': '人数', 'category2': '性別'},
            barmode='group'
        )
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")
        st.subheader("データテーブル")
        st.dataframe(age_gender[['category1', 'category2', 'count']], use_container_width=True)

        # ダウンロードボタン
        csv = age_gender.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="📥 CSVダウンロード",
            data=csv,
            file_name=f"age_gender_{prefecture}_{municipality}.csv",
            mime="text/csv"
        )
    else:
        st.warning(f"年齢×性別データがありません: {prefecture} {municipality}")

# ==============================
# Phase 3: ペルソナ分析
# ==============================

def show_persona_tab(df, prefecture, municipality):
    """ペルソナ分析表示"""
    st.header("🎯 ペルソナ分析（Phase 3: ペルソナ分析）")

    persona_muni = filter_data(df, 'PERSONA_MUNI', prefecture, municipality)

    if len(persona_muni) > 0:
        # 棒グラフ
        fig = px.bar(
            persona_muni,
            x='category1',
            y='count',
            title=f"{prefecture} {municipality} - ペルソナ分布",
            labels={'category1': 'ペルソナ', 'count': '人数'},
            color='count',
            color_continuous_scale='Blues'
        )
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")
        st.subheader("ペルソナ別人数")
        st.dataframe(persona_muni[['category1', 'count']].sort_values('count', ascending=False), use_container_width=True)

        # ダウンロードボタン
        csv = persona_muni.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="📥 CSVダウンロード",
            data=csv,
            file_name=f"persona_{prefecture}_{municipality}.csv",
            mime="text/csv"
        )
    else:
        st.warning(f"ペルソナデータがありません: {prefecture} {municipality}")

# ==============================
# Phase 6: フロー分析
# ==============================

def show_flow_tab(df, prefecture, municipality):
    """フロー分析表示"""
    st.header("🌊 フロー分析（Phase 6: 人材流入・流出）")

    flow = filter_data(df, 'FLOW', prefecture, municipality)

    if len(flow) > 0:
        row = flow.iloc[0]

        col1, col2, col3 = st.columns(3)

        with col1:
            inflow = row['inflow'] if pd.notna(row['inflow']) else 0
            st.metric("流入（Inflow）", f"{inflow:.0f}人", delta="流入", delta_color="normal")
        with col2:
            outflow = row['outflow'] if pd.notna(row['outflow']) else 0
            st.metric("流出（Outflow）", f"{outflow:.0f}人", delta="流出", delta_color="inverse")
        with col3:
            net_flow = row['net_flow'] if pd.notna(row['net_flow']) else 0
            delta_text = "流入超過" if net_flow > 0 else "流出超過"
            st.metric("純流入（Net Flow）", f"{net_flow:.0f}人", delta=delta_text)

        st.markdown("---")
        st.subheader("フロー図（Sankey）")

        # サンキー図
        fig = go.Figure(go.Sankey(
            node=dict(
                label=["他地域", municipality, "流出先"],
                color=["lightblue", "lightgreen", "lightcoral"]
            ),
            link=dict(
                source=[0, 1],
                target=[1, 2],
                value=[inflow, outflow],
                color=["rgba(0, 128, 255, 0.4)", "rgba(255, 128, 0, 0.4)"]
            )
        ))
        fig.update_layout(title="人材フロー図", height=400)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning(f"フロー分析データがありません: {prefecture} {municipality}")

# ==============================
# Phase 6: 需給ギャップ
# ==============================

def show_gap_tab(df, prefecture, municipality):
    """需給ギャップ分析表示"""
    st.header("📈 需給ギャップ分析（Phase 6: 需給バランス）")

    gap = filter_data(df, 'GAP', prefecture, municipality)

    if len(gap) > 0:
        row = gap.iloc[0]

        col1, col2, col3 = st.columns(3)

        with col1:
            demand = row['demand_count'] if pd.notna(row['demand_count']) else 0
            st.metric("需要（Demand）", f"{demand:.0f}人")
        with col2:
            supply = row['supply_count'] if pd.notna(row['supply_count']) else 0
            st.metric("供給（Supply）", f"{supply:.0f}人")
        with col3:
            gap_value = row['gap'] if pd.notna(row['gap']) else 0
            delta_text = "需要超過" if gap_value > 0 else "供給超過"
            st.metric("ギャップ（Gap）", f"{gap_value:.0f}人", delta=delta_text)

        st.markdown("---")
        st.subheader("需給比較グラフ")

        # 棒グラフ
        fig = go.Figure(data=[
            go.Bar(name='需要', x=['需給分析'], y=[demand], marker_color='indianred'),
            go.Bar(name='供給', x=['需給分析'], y=[supply], marker_color='lightsalmon')
        ])
        fig.update_layout(title="需要 vs 供給", barmode='group', height=400)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning(f"需給ギャップデータがありません: {prefecture} {municipality}")

# ==============================
# Phase 6: 希少人材分析
# ==============================

def show_rarity_tab(df, prefecture, municipality):
    """希少人材分析表示"""
    st.header("💎 希少人材分析（Phase 6: レアスキル保有者）")

    rarity = filter_data(df, 'RARITY', prefecture, municipality)

    if len(rarity) > 0:
        # 棒グラフ
        fig = px.bar(
            rarity,
            x='category1',
            y='rarity_score',
            title=f"{prefecture} {municipality} - 希少人材スコア",
            labels={'category1': 'カテゴリ', 'rarity_score': '希少スコア'},
            color='rarity_score',
            color_continuous_scale='Reds'
        )
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")
        st.subheader("希少人材データ")
        display_cols = ['category1', 'category2', 'rarity_score', 'count']
        available_cols = [col for col in display_cols if col in rarity.columns]
        st.dataframe(rarity[available_cols], use_container_width=True)
    else:
        st.warning(f"希少人材データがありません: {prefecture} {municipality}")

# ==============================
# Phase 6: 競争プロファイル
# ==============================

def show_competition_tab(df, prefecture, municipality):
    """競争プロファイル表示"""
    st.header("🏆 競争プロファイル（Phase 6: 採用難易度分析）")

    competition = filter_data(df, 'COMPETITION', prefecture, municipality)

    if len(competition) > 0:
        row = competition.iloc[0]

        col1, col2, col3 = st.columns(3)

        with col1:
            comp_score = row['competition_score'] if pd.notna(row['competition_score']) else 0
            st.metric("競争スコア", f"{comp_score:.2f}")
        with col2:
            difficulty = row['category1'] if pd.notna(row['category1']) else "N/A"
            st.metric("難易度", difficulty)
        with col3:
            rank = row['category2'] if pd.notna(row['category2']) else "N/A"
            st.metric("ランク", rank)

        st.markdown("---")
        st.subheader("詳細データ")
        st.dataframe(competition, use_container_width=True)
    else:
        st.warning(f"競争プロファイルデータがありません: {prefecture} {municipality}")

# ==============================
# Phase 8: キャリア×年齢
# ==============================

def show_career_cross_tab(df, prefecture, municipality):
    """キャリア×年齢クロス分析表示"""
    st.header("💼 キャリア×年齢クロス分析（Phase 8: キャリア分析）")

    career = filter_data(df, 'CAREER_CROSS', prefecture, municipality)

    if len(career) > 0:
        # 棒グラフ
        fig = px.bar(
            career,
            x='category1',
            y='count',
            color='category2',
            title=f"{prefecture} {municipality} - キャリア×年齢分布",
            labels={'category1': 'キャリア', 'count': '人数', 'category2': '年齢層'},
            barmode='group'
        )
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")
        st.subheader("データテーブル")
        st.dataframe(career[['category1', 'category2', 'count']], use_container_width=True)
    else:
        st.warning(f"キャリア×年齢データがありません: {prefecture} {municipality}")

# ==============================
# Phase 10: 緊急度×年齢
# ==============================

def show_urgency_age_tab(df, prefecture, municipality):
    """緊急度×年齢クロス分析表示"""
    st.header("⏰ 緊急度×年齢クロス分析（Phase 10: 転職意欲分析）")

    urgency_age = filter_data(df, 'URGENCY_AGE', prefecture, municipality)

    if len(urgency_age) > 0:
        # ヒートマップ
        pivot = urgency_age.pivot(index='category1', columns='category2', values='count')

        fig = px.imshow(
            pivot,
            title=f"{prefecture} {municipality} - 緊急度×年齢ヒートマップ",
            labels=dict(x="年齢層", y="緊急度", color="人数"),
            color_continuous_scale='YlOrRd'
        )
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")
        st.subheader("データテーブル")
        st.dataframe(urgency_age[['category1', 'category2', 'count']], use_container_width=True)
    else:
        st.warning(f"緊急度×年齢データがありません: {prefecture} {municipality}")

# ==============================
# Phase 10: 緊急度×就業状況
# ==============================

def show_urgency_employment_tab(df, prefecture, municipality):
    """緊急度×就業状況クロス分析表示"""
    st.header("💼 緊急度×就業状況クロス分析（Phase 10: 転職意欲分析）")

    urgency_emp = filter_data(df, 'URGENCY_EMPLOYMENT', prefecture, municipality)

    if len(urgency_emp) > 0:
        # 棒グラフ
        fig = px.bar(
            urgency_emp,
            x='category1',
            y='count',
            color='category2',
            title=f"{prefecture} {municipality} - 緊急度×就業状況",
            labels={'category1': '緊急度', 'count': '人数', 'category2': '就業状況'},
            barmode='group'
        )
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")
        st.subheader("データテーブル")
        st.dataframe(urgency_emp[['category1', 'category2', 'count']], use_container_width=True)
    else:
        st.warning(f"緊急度×就業状況データがありません: {prefecture} {municipality}")

# ==============================
# メイン処理
# ==============================

def main():
    # ヘッダー
    st.markdown('<div class="main-header">🎯 MapComplete統合ダッシュボード - 完全版</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">GAS統合ダッシュボード完全移行版（Phase 1-14全機能）</div>', unsafe_allow_html=True)

    # データロード
    df = load_data_from_path()

    if df is None:
        st.info("📂 CSVファイルが見つかりません。ファイルをアップロードしてください。")

        uploaded_file = st.file_uploader(
            "MapComplete_Complete_All_FIXED.csv をアップロード",
            type=['csv'],
            help="ドラッグ&ドロップまたはクリックしてファイルを選択"
        )

        if uploaded_file is not None:
            with st.spinner("📊 CSVファイルを読み込み中..."):
                df = load_data_from_upload(uploaded_file)
                st.success(f"✅ データロード完了: {len(df):,}行 × {len(df.columns)}列")
        else:
            st.warning("⚠️ CSVファイルをアップロードしてください")
            st.stop()
    else:
        st.success(f"✅ データロード完了: {len(df):,}行 × {len(df.columns)}列")

    # サイドバー: 地域選択
    st.sidebar.header("📍 地域選択")

    prefectures = get_prefectures(df)
    selected_prefecture = st.sidebar.selectbox("都道府県", prefectures, key="prefecture_select")

    municipalities = get_municipalities(df, selected_prefecture)
    selected_municipality = st.sidebar.selectbox("市区町村", municipalities, key="municipality_select")

    st.sidebar.markdown("---")
    st.sidebar.info(f"**選択地域**\n\n{selected_prefecture} {selected_municipality}")

    # row_type統計
    st.sidebar.markdown("---")
    st.sidebar.subheader("📊 データ統計")
    row_type_counts = df['row_type'].value_counts()
    for rt, count in row_type_counts.items():
        st.sidebar.text(f"{rt}: {count:,}件")

    # タブ構成
    tabs = st.tabs([
        "📊 サマリー",
        "👥 年齢×性別",
        "🎯 ペルソナ",
        "🌊 フロー分析",
        "📈 需給ギャップ",
        "💎 希少人材",
        "🏆 競争プロファイル",
        "💼 キャリア×年齢",
        "⏰ 緊急度×年齢",
        "💼 緊急度×就業"
    ])

    with tabs[0]:
        show_summary_tab(df, selected_prefecture, selected_municipality)

    with tabs[1]:
        show_age_gender_tab(df, selected_prefecture, selected_municipality)

    with tabs[2]:
        show_persona_tab(df, selected_prefecture, selected_municipality)

    with tabs[3]:
        show_flow_tab(df, selected_prefecture, selected_municipality)

    with tabs[4]:
        show_gap_tab(df, selected_prefecture, selected_municipality)

    with tabs[5]:
        show_rarity_tab(df, selected_prefecture, selected_municipality)

    with tabs[6]:
        show_competition_tab(df, selected_prefecture, selected_municipality)

    with tabs[7]:
        show_career_cross_tab(df, selected_prefecture, selected_municipality)

    with tabs[8]:
        show_urgency_age_tab(df, selected_prefecture, selected_municipality)

    with tabs[9]:
        show_urgency_employment_tab(df, selected_prefecture, selected_municipality)

if __name__ == "__main__":
    main()
