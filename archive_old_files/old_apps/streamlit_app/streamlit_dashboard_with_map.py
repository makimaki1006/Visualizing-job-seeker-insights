"""
MapComplete統合ダッシュボード - 地図表示デモ版

実行方法:
    pip install streamlit pandas plotly folium streamlit-folium
    streamlit run streamlit_dashboard_with_map.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import folium
from folium import plugins
from streamlit_folium import st_folium
from pathlib import Path

# ページ設定
st.set_page_config(
    page_title="MapComplete統合ダッシュボード - 地図表示デモ",
    page_icon="🗺️",
    layout="wide"
)

# キャッシュ: CSVロード
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

# 都道府県の中心座標（主要都道府県）
PREFECTURE_COORDS = {
    "北海道": [43.064, 141.347],
    "青森県": [40.824, 140.740],
    "岩手県": [39.703, 141.153],
    "宮城県": [38.269, 140.872],
    "秋田県": [39.719, 140.102],
    "山形県": [38.240, 140.363],
    "福島県": [37.750, 140.467],
    "茨城県": [36.341, 140.447],
    "栃木県": [36.566, 139.883],
    "群馬県": [36.391, 139.060],
    "埼玉県": [35.857, 139.649],
    "千葉県": [35.605, 140.123],
    "東京都": [35.689, 139.692],
    "神奈川県": [35.448, 139.642],
    "新潟県": [37.902, 139.023],
    "富山県": [36.696, 137.211],
    "石川県": [36.595, 136.626],
    "福井県": [36.065, 136.222],
    "山梨県": [35.664, 138.568],
    "長野県": [36.651, 138.181],
    "岐阜県": [35.391, 136.722],
    "静岡県": [34.977, 138.383],
    "愛知県": [35.180, 136.907],
    "三重県": [34.730, 136.509],
    "滋賀県": [35.004, 135.869],
    "京都府": [35.012, 135.768],
    "大阪府": [34.686, 135.520],
    "兵庫県": [34.691, 135.183],
    "奈良県": [34.685, 135.833],
    "和歌山県": [34.226, 135.167],
    "鳥取県": [35.504, 134.238],
    "島根県": [35.472, 133.051],
    "岡山県": [34.662, 133.935],
    "広島県": [34.397, 132.460],
    "山口県": [34.186, 131.471],
    "徳島県": [34.066, 134.559],
    "香川県": [34.340, 134.043],
    "愛媛県": [33.842, 132.766],
    "高知県": [33.560, 133.531],
    "福岡県": [33.606, 130.418],
    "佐賀県": [33.250, 130.299],
    "長崎県": [32.745, 129.874],
    "熊本県": [32.790, 130.742],
    "大分県": [33.238, 131.613],
    "宮崎県": [31.911, 131.424],
    "鹿児島県": [31.560, 130.558],
    "沖縄県": [26.212, 127.681],
}

@st.cache_data
def get_prefectures(df):
    """ユニークな都道府県リストを取得"""
    prefectures = df['prefecture'].dropna().unique().tolist()
    prefectures.sort()
    return prefectures

@st.cache_data
def get_municipalities(df, prefecture):
    """指定都道府県の市区町村リストを取得"""
    summary_df = df[(df['row_type'] == 'SUMMARY') & (df['prefecture'] == prefecture)]
    municipalities = summary_df['municipality'].dropna().unique().tolist()
    municipalities.sort()
    return municipalities

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

def get_all_summary_for_prefecture(df, prefecture):
    """指定都道府県の全市区町村サマリーを取得"""
    summary = df[(df['row_type'] == 'SUMMARY') & (df['prefecture'] == prefecture)]
    return summary

def create_bubble_map(df, prefecture):
    """バブルマップ作成（申請者数に応じた円サイズ）"""
    summary_data = get_all_summary_for_prefecture(df, prefecture)

    if len(summary_data) == 0:
        return None

    # 都道府県の中心座標を取得
    center = PREFECTURE_COORDS.get(prefecture, [35.0, 135.0])

    # 地図作成
    m = folium.Map(
        location=center,
        zoom_start=10,
        tiles='OpenStreetMap'
    )

    # 市区町村ごとにマーカー追加（仮の座標）
    for idx, row in summary_data.iterrows():
        municipality = row['municipality']
        count = row['applicant_count']
        avg_age = row['avg_age']
        male_ratio = row['male_ratio'] * 100 if pd.notna(row['male_ratio']) else 0

        # 簡易的な座標（実際はジオコーディングが必要）
        # ここでは都道府県中心からランダムにオフセット
        import random
        lat = center[0] + random.uniform(-0.2, 0.2)
        lon = center[1] + random.uniform(-0.2, 0.2)

        # バブルサイズ（申請者数に比例）
        radius = max(5, count / 10)

        # ポップアップ内容
        popup_html = f"""
        <div style="font-family: Arial; font-size: 14px;">
            <b>{municipality}</b><br>
            申請者数: {count:.0f}人<br>
            平均年齢: {avg_age:.1f}歳<br>
            男性比率: {male_ratio:.1f}%
        </div>
        """

        folium.CircleMarker(
            location=[lat, lon],
            radius=radius,
            popup=folium.Popup(popup_html, max_width=300),
            color='red',
            fill=True,
            fillColor='red',
            fillOpacity=0.6,
            weight=2
        ).add_to(m)

    return m

def create_heatmap(df, prefecture):
    """ヒートマップ作成（申請者密度）"""
    summary_data = get_all_summary_for_prefecture(df, prefecture)

    if len(summary_data) == 0:
        return None

    # 都道府県の中心座標を取得
    center = PREFECTURE_COORDS.get(prefecture, [35.0, 135.0])

    # 地図作成
    m = folium.Map(
        location=center,
        zoom_start=10,
        tiles='OpenStreetMap'
    )

    # ヒートマップ用データ準備
    heat_data = []
    for idx, row in summary_data.iterrows():
        count = row['applicant_count']

        # 簡易的な座標
        import random
        lat = center[0] + random.uniform(-0.2, 0.2)
        lon = center[1] + random.uniform(-0.2, 0.2)

        heat_data.append([lat, lon, count])

    # ヒートマップレイヤー追加
    plugins.HeatMap(heat_data, radius=15, blur=25, max_zoom=13).add_to(m)

    return m

# メイン処理
def main():
    st.title("🗺️ MapComplete統合ダッシュボード - 地図表示デモ")
    st.markdown("**地図表示機能追加版**（Folium使用）")

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
    selected_prefecture = st.sidebar.selectbox("都道府県", prefectures)
    municipalities = get_municipalities(df, selected_prefecture)
    selected_municipality = st.sidebar.selectbox("市区町村", municipalities)

    st.sidebar.markdown("---")
    st.sidebar.info(f"選択地域: **{selected_prefecture} {selected_municipality}**")

    # タブ: 地図表示 + 既存の分析
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
        "🗺️ 地図（バブル）",
        "🔥 地図（ヒート）",
        "📊 サマリー",
        "👥 年齢×性別",
        "🌊 フロー分析",
        "📈 需給ギャップ",
        "🎯 ペルソナ分析",
        "💼 キャリア×年齢"
    ])

    # Tab 1: バブルマップ
    with tab1:
        st.header(f"🗺️ {selected_prefecture} - バブルマップ（申請者数）")
        st.markdown("円のサイズ = 申請者数｜クリックで詳細表示")

        with st.spinner("地図を生成中..."):
            bubble_map = create_bubble_map(df, selected_prefecture)
            if bubble_map:
                st_folium(bubble_map, width=1200, height=600)
            else:
                st.warning("地図データがありません")

    # Tab 2: ヒートマップ
    with tab2:
        st.header(f"🔥 {selected_prefecture} - ヒートマップ（申請者密度）")
        st.markdown("色の濃さ = 申請者密度")

        with st.spinner("ヒートマップを生成中..."):
            heat_map = create_heatmap(df, selected_prefecture)
            if heat_map:
                st_folium(heat_map, width=1200, height=600)
            else:
                st.warning("ヒートマップデータがありません")

    # Tab 3: サマリー
    with tab3:
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

    # Tab 4: 年齢×性別
    with tab4:
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

    # Tab 5: フロー分析
    with tab5:
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

            # サンキー図
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

    # Tab 6: 需給ギャップ
    with tab6:
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

    # Tab 7: ペルソナ分析（省略）
    with tab7:
        st.header("🎯 ペルソナ分析")
        st.info("ペルソナ分析タブ（実装予定）")

    # Tab 8: キャリア×年齢（省略）
    with tab8:
        st.header("💼 キャリア×年齢クロス分析")
        st.info("キャリア×年齢タブ（実装予定）")

if __name__ == "__main__":
    main()
