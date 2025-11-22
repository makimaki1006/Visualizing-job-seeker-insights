"""
MapComplete統合ダッシュボード - Streamlitプロトタイプ

実行方法:
    streamlit run streamlit_dashboard.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import io

# ページ設定
st.set_page_config(
    page_title="MapComplete統合ダッシュボード",
    page_icon="🗺️",
    layout="wide"
)

# キャッシュ: CSVロード（高速化）
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

# キャッシュ: 都道府県リスト
@st.cache_data
def get_prefectures(df):
    """ユニークな都道府県リストを取得"""
    prefectures = df['prefecture'].dropna().unique().tolist()
    prefectures.sort()
    return prefectures

# キャッシュ: 市区町村リスト
@st.cache_data
def get_municipalities(df, prefecture):
    """指定都道府県の市区町村リストを取得"""
    summary_df = df[(df['row_type'] == 'SUMMARY') & (df['prefecture'] == prefecture)]
    municipalities = summary_df['municipality'].dropna().unique().tolist()
    municipalities.sort()
    return municipalities

# データ取得関数
def get_summary_data(df, prefecture, municipality):
    """サマリーデータ取得"""
    summary = df[(df['row_type'] == 'SUMMARY') &
                 (df['prefecture'] == prefecture) &
                 (df['municipality'] == municipality)]
    return summary.iloc[0] if len(summary) > 0 else None

def get_age_gender_data(df, prefecture, municipality):
    """年齢×性別クロス分析データ取得"""
    age_gender = df[(df['row_type'] == 'AGE_GENDER') &
                    (df['prefecture'] == prefecture) &
                    (df['municipality'] == municipality)]
    return age_gender

def get_flow_data(df, prefecture, municipality):
    """フロー分析データ取得"""
    flow = df[(df['row_type'] == 'FLOW') &
              (df['prefecture'] == prefecture) &
              (df['municipality'] == municipality)]
    return flow.iloc[0] if len(flow) > 0 else None

def get_gap_data(df, prefecture, municipality):
    """需給ギャップデータ取得"""
    gap = df[(df['row_type'] == 'GAP') &
             (df['prefecture'] == prefecture) &
             (df['municipality'] == municipality)]
    return gap.iloc[0] if len(gap) > 0 else None

def get_persona_data(df, prefecture, municipality):
    """ペルソナ分析データ取得"""
    persona = df[(df['row_type'] == 'PERSONA_MUNI') &
                 (df['prefecture'] == prefecture) &
                 (df['municipality'] == municipality)]
    return persona

def get_career_cross_data(df, prefecture, municipality):
    """キャリア×年齢クロス分析データ取得"""
    career = df[(df['row_type'] == 'CAREER_CROSS') &
                (df['prefecture'] == prefecture) &
                (df['municipality'] == municipality)]
    return career

# メイン処理
def main():
    st.title("🗺️ MapComplete統合ダッシュボード")
    st.markdown("**データソース**: MapComplete_Complete_All_FIXED.csv")

    # データロード方法選択
    df = None

    # オプション1: パスから自動ロード
    df = load_data_from_path()

    # オプション2: ファイルアップロード
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
    selected_prefecture = st.sidebar.selectbox("都道府県", prefectures)

    municipalities = get_municipalities(df, selected_prefecture)
    selected_municipality = st.sidebar.selectbox("市区町村", municipalities)

    st.sidebar.markdown("---")
    st.sidebar.info(f"選択地域: **{selected_prefecture} {selected_municipality}**")

    # タブ: 6つの分析
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📊 サマリー",
        "👥 年齢×性別",
        "🌊 フロー分析",
        "📈 需給ギャップ",
        "🎯 ペルソナ分析",
        "💼 キャリア×年齢"
    ])

    # Tab 1: サマリー
    with tab1:
        st.header("📊 サマリー情報")
        summary = get_summary_data(df, selected_prefecture, selected_municipality)

        if summary is not None:
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("申請者数", f"{summary['applicant_count']:.0f}人")
            with col2:
                st.metric("平均年齢", f"{summary['avg_age']:.1f}歳")
            with col3:
                st.metric("男性比率", f"{summary['male_ratio']*100:.1f}%")
            with col4:
                st.metric("女性比率", f"{summary['female_ratio']*100:.1f}%")
        else:
            st.warning("サマリーデータがありません")

    # Tab 2: 年齢×性別
    with tab2:
        st.header("👥 年齢層×性別クロス分析")
        age_gender = get_age_gender_data(df, selected_prefecture, selected_municipality)

        if len(age_gender) > 0:
            fig = px.bar(
                age_gender,
                x='category1',
                y='count',
                color='category2',
                title=f"{selected_prefecture} {selected_municipality} - 年齢×性別分布",
                labels={'category1': '年齢層', 'count': '人数', 'category2': '性別'}
            )
            st.plotly_chart(fig, use_container_width=True)

            st.dataframe(age_gender[['category1', 'category2', 'count']], use_container_width=True)
        else:
            st.warning("年齢×性別データがありません")

    # Tab 3: フロー分析
    with tab3:
        st.header("🌊 フロー分析（人材流入・流出）")
        flow = get_flow_data(df, selected_prefecture, selected_municipality)

        if flow is not None:
            col1, col2, col3 = st.columns(3)

            with col1:
                inflow = flow['inflow'] if pd.notna(flow['inflow']) else 0
                st.metric("流入（Inflow）", f"{inflow:.0f}人", delta="流入")
            with col2:
                outflow = flow['outflow'] if pd.notna(flow['outflow']) else 0
                st.metric("流出（Outflow）", f"{outflow:.0f}人", delta="流出", delta_color="inverse")
            with col3:
                net_flow = flow['net_flow'] if pd.notna(flow['net_flow']) else 0
                st.metric("純流入（Net Flow）", f"{net_flow:.0f}人", delta=f"{net_flow:.0f}")

            # サンキー図（簡易版）
            fig = go.Figure(go.Sankey(
                node=dict(
                    label=["他地域", selected_municipality, "流出先"],
                    color=["blue", "green", "red"]
                ),
                link=dict(
                    source=[0, 1],
                    target=[1, 2],
                    value=[inflow, outflow]
                )
            ))
            fig.update_layout(title="人材フロー図", height=400)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning(f"選択地域（{selected_prefecture} {selected_municipality}）のフロー分析データがありません")

    # Tab 4: 需給ギャップ
    with tab4:
        st.header("📈 需給ギャップ分析")
        gap = get_gap_data(df, selected_prefecture, selected_municipality)

        if gap is not None:
            col1, col2, col3 = st.columns(3)

            with col1:
                demand = gap['demand_count'] if pd.notna(gap['demand_count']) else 0
                st.metric("需要（Demand）", f"{demand:.0f}人")
            with col2:
                supply = gap['supply_count'] if pd.notna(gap['supply_count']) else 0
                st.metric("供給（Supply）", f"{supply:.0f}人")
            with col3:
                gap_value = gap['gap'] if pd.notna(gap['gap']) else 0
                st.metric("ギャップ（Gap）", f"{gap_value:.0f}人", delta=f"{gap_value:.0f}")

            # 棒グラフ
            fig = go.Figure(data=[
                go.Bar(name='需要', x=['需給分析'], y=[demand], marker_color='indianred'),
                go.Bar(name='供給', x=['需給分析'], y=[supply], marker_color='lightsalmon')
            ])
            fig.update_layout(title="需要 vs 供給", barmode='group', height=400)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("需給ギャップデータがありません")

    # Tab 5: ペルソナ分析
    with tab5:
        st.header("🎯 ペルソナ分析")
        persona = get_persona_data(df, selected_prefecture, selected_municipality)

        if len(persona) > 0:
            fig = px.bar(
                persona,
                x='category1',
                y='count',
                title=f"{selected_prefecture} {selected_municipality} - ペルソナ分布",
                labels={'category1': 'ペルソナ', 'count': '人数'}
            )
            st.plotly_chart(fig, use_container_width=True)

            st.dataframe(persona[['category1', 'count']], use_container_width=True)
        else:
            st.warning("ペルソナデータがありません")

    # Tab 6: キャリア×年齢
    with tab6:
        st.header("💼 キャリア×年齢クロス分析")
        career = get_career_cross_data(df, selected_prefecture, selected_municipality)

        if len(career) > 0:
            fig = px.bar(
                career,
                x='category1',
                y='count',
                color='category2',
                title=f"{selected_prefecture} {selected_municipality} - キャリア×年齢分布",
                labels={'category1': 'キャリア', 'count': '人数', 'category2': '年齢層'}
            )
            st.plotly_chart(fig, use_container_width=True)

            st.dataframe(career[['category1', 'category2', 'count']], use_container_width=True)
        else:
            st.warning("キャリア×年齢データがありません")

if __name__ == "__main__":
    main()
