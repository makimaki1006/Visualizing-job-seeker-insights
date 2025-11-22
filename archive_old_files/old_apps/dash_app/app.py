"""
MapComplete統合ダッシュボード - Dash完全移行版
GAS統合ダッシュボードの10タブ + 11 row_types を完全再現

Phase 1 (MVP): CSVロード + サマリー表示
Phase 2: 10タブ完全実装
"""

from dash import Dash, html, dcc, Input, Output, State
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path

# ========================================
# アプリ初期化
# ========================================

app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True
)

# ========================================
# データロード
# ========================================

# CSVパス（相対パスで指定）
CSV_PATH = Path(__file__).parent.parent / "python_scripts" / "data" / "output_v2" / "mapcomplete_complete_sheets" / "MapComplete_Complete_All_FIXED.csv"

def load_data():
    """CSVを読み込み"""
    try:
        df = pd.read_csv(CSV_PATH, encoding='utf-8-sig', low_memory=False)
        print(f"✅ CSVロード成功: {len(df)}行 × {len(df.columns)}列")
        return df
    except FileNotFoundError:
        print(f"❌ CSVが見つかりません: {CSV_PATH}")
        return pd.DataFrame()
    except Exception as e:
        print(f"❌ CSVロードエラー: {e}")
        return pd.DataFrame()

# グローバルデータ
DF = load_data()

# ========================================
# 定数・ユーティリティ
# ========================================

PREFECTURE_LIST = [
    "北海道", "青森県", "岩手県", "宮城県", "秋田県", "山形県", "福島県",
    "茨城県", "栃木県", "群馬県", "埼玉県", "千葉県", "東京都", "神奈川県",
    "新潟県", "富山県", "石川県", "福井県", "山梨県", "長野県", "岐阜県",
    "静岡県", "愛知県", "三重県", "滋賀県", "京都府", "大阪府", "兵庫県",
    "奈良県", "和歌山県", "鳥取県", "島根県", "岡山県", "広島県", "山口県",
    "徳島県", "香川県", "愛媛県", "高知県", "福岡県", "佐賀県", "長崎県",
    "熊本県", "大分県", "宮崎県", "鹿児島県", "沖縄県"
]

def get_municipalities(prefecture):
    """指定都道府県の市区町村リストを取得"""
    if DF.empty:
        return []

    munis = DF[DF['prefecture'] == prefecture]['municipality'].dropna().unique().tolist()
    return sorted(munis)

def filter_data(prefecture, municipality=None):
    """データをフィルタリング"""
    if DF.empty:
        return pd.DataFrame()

    df_filtered = DF[DF['prefecture'] == prefecture].copy()

    if municipality:
        df_filtered = df_filtered[df_filtered['municipality'] == municipality].copy()

    return df_filtered

def get_summary_metrics(df_filtered):
    """SUMMARYメトリクスを取得"""
    summary_rows = df_filtered[df_filtered['row_type'] == 'SUMMARY']

    if len(summary_rows) == 0:
        return {
            'applicant_count': 0,
            'avg_age': 0,
            'male_ratio': 0,
            'female_ratio': 0
        }

    row = summary_rows.iloc[0]
    return {
        'applicant_count': int(row.get('applicant_count', 0)) if pd.notna(row.get('applicant_count')) else 0,
        'avg_age': float(row.get('avg_age', 0)) if pd.notna(row.get('avg_age')) else 0,
        'male_ratio': float(row.get('male_ratio', 0)) if pd.notna(row.get('male_ratio')) else 0,
        'female_ratio': float(row.get('female_ratio', 0)) if pd.notna(row.get('female_ratio')) else 0
    }

# ========================================
# レイアウト
# ========================================

def create_metric_card(title, value, icon, color="#4A90E2"):
    """メトリックカード"""
    return dbc.Card(
        dbc.CardBody([
            html.Div([
                html.Span(icon, style={"fontSize": "2rem", "marginRight": "10px"}),
                html.H5(title, className="text-muted"),
            ], style={"display": "flex", "alignItems": "center"}),
            html.H2(value, style={"color": color, "marginTop": "10px"})
        ]),
        style={
            "boxShadow": "0 4px 6px rgba(0,0,0,0.1)",
            "borderRadius": "12px",
            "padding": "1rem"
        }
    )

app.layout = dbc.Container([
    # ヘッダー
    dbc.Row([
        dbc.Col([
            html.H1("🗺️ MapComplete統合ダッシュボード", className="text-primary"),
            html.P("Dash実装版 - GAS統合ダッシュボード完全再現", className="text-muted")
        ])
    ], className="my-4"),

    dbc.Row([
        # サイドバー
        dbc.Col([
            dbc.Card([
                dbc.CardHeader(html.H4("📍 地域選択")),
                dbc.CardBody([
                    html.Label("都道府県", className="fw-bold"),
                    dcc.Dropdown(
                        id='prefecture-dropdown',
                        options=[{'label': p, 'value': p} for p in PREFECTURE_LIST],
                        value='東京都',
                        clearable=False
                    ),
                    html.Hr(),
                    html.Label("市区町村", className="fw-bold"),
                    dcc.Dropdown(
                        id='municipality-dropdown',
                        options=[],
                        value=None,
                        placeholder="都道府県全体"
                    ),
                    html.Hr(),
                    html.Div(id='data-stats', className="mt-3")
                ])
            ], className="mb-3")
        ], width=3),

        # メインコンテンツ
        dbc.Col([
            # タブ
            dcc.Tabs(id='tabs', value='tab-summary', children=[
                dcc.Tab(label='📊 サマリー', value='tab-summary'),
                dcc.Tab(label='👥 年齢×性別', value='tab-age-gender'),
                dcc.Tab(label='🎯 ペルソナ', value='tab-persona'),
                dcc.Tab(label='🌊 フロー分析', value='tab-flow'),
                dcc.Tab(label='📈 需給ギャップ', value='tab-gap'),
                dcc.Tab(label='💎 希少人材', value='tab-rarity'),
                dcc.Tab(label='🏆 競争プロファイル', value='tab-competition'),
                dcc.Tab(label='💼 キャリア×年齢', value='tab-career'),
                dcc.Tab(label='⏰ 緊急度×年齢', value='tab-urgency-age'),
                dcc.Tab(label='💼 緊急度×就業', value='tab-urgency-employment'),
            ]),
            html.Div(id='tab-content', className="mt-4")
        ], width=9)
    ])
], fluid=True, style={"backgroundColor": "#f8f9fa", "minHeight": "100vh", "padding": "20px"})

# ========================================
# コールバック
# ========================================

@app.callback(
    Output('municipality-dropdown', 'options'),
    Output('municipality-dropdown', 'value'),
    Input('prefecture-dropdown', 'value')
)
def update_municipalities(prefecture):
    """都道府県変更時に市区町村リストを更新"""
    munis = get_municipalities(prefecture)
    options = [{'label': m, 'value': m} for m in munis]
    return options, None

@app.callback(
    Output('data-stats', 'children'),
    Input('prefecture-dropdown', 'value'),
    Input('municipality-dropdown', 'value')
)
def update_data_stats(prefecture, municipality):
    """データ統計を更新"""
    df_filtered = filter_data(prefecture, municipality)

    if df_filtered.empty:
        return html.Div("データなし", className="text-danger")

    row_type_counts = df_filtered['row_type'].value_counts().to_dict()

    stats = [
        html.H5("データ統計", className="fw-bold mb-3"),
        html.P(f"総行数: {len(df_filtered):,}行", className="mb-2")
    ]

    for row_type, count in sorted(row_type_counts.items()):
        stats.append(html.P(f"• {row_type}: {count}件", className="mb-1 small"))

    return html.Div(stats)

@app.callback(
    Output('tab-content', 'children'),
    Input('tabs', 'value'),
    Input('prefecture-dropdown', 'value'),
    Input('municipality-dropdown', 'value')
)
def render_tab_content(active_tab, prefecture, municipality):
    """タブコンテンツをレンダリング"""
    df_filtered = filter_data(prefecture, municipality)

    if df_filtered.empty:
        return dbc.Alert("選択地域のデータがありません", color="warning")

    if active_tab == 'tab-summary':
        return render_summary_tab(df_filtered)
    elif active_tab == 'tab-age-gender':
        return render_age_gender_tab(df_filtered)
    elif active_tab == 'tab-persona':
        return render_persona_tab(df_filtered)
    else:
        return dbc.Alert(f"タブ「{active_tab}」は未実装です", color="info")

# ========================================
# タブ描画関数
# ========================================

def render_summary_tab(df_filtered):
    """サマリータブ"""
    metrics = get_summary_metrics(df_filtered)

    return dbc.Container([
        dbc.Row([
            dbc.Col(create_metric_card(
                "申請者数",
                f"{metrics['applicant_count']:,}人",
                "👥",
                "#4A90E2"
            ), width=3),
            dbc.Col(create_metric_card(
                "平均年齢",
                f"{metrics['avg_age']:.1f}歳",
                "🎂",
                "#50C878"
            ), width=3),
            dbc.Col(create_metric_card(
                "男性比率",
                f"{metrics['male_ratio']:.1f}%",
                "👨",
                "#5DADE2"
            ), width=3),
            dbc.Col(create_metric_card(
                "女性比率",
                f"{metrics['female_ratio']:.1f}%",
                "👩",
                "#F1948A"
            ), width=3)
        ])
    ], fluid=True)

def render_age_gender_tab(df_filtered):
    """年齢×性別タブ（簡易実装）"""
    age_gender_rows = df_filtered[df_filtered['row_type'] == 'AGE_GENDER']

    if len(age_gender_rows) == 0:
        return dbc.Alert("AGE_GENDERデータがありません", color="warning")

    return html.Div([
        html.H4("👥 年齢層×性別クロス集計"),
        html.P(f"データ件数: {len(age_gender_rows)}件", className="text-muted"),
        html.P("📊 グラフ実装予定", className="text-info")
    ])

def render_persona_tab(df_filtered):
    """ペルソナタブ（簡易実装）"""
    persona_rows = df_filtered[df_filtered['row_type'] == 'PERSONA_MUNI']

    if len(persona_rows) == 0:
        return dbc.Alert("PERSONA_MUNIデータがありません", color="warning")

    return html.Div([
        html.H4("🎯 ペルソナ分析"),
        html.P(f"データ件数: {len(persona_rows)}件", className="text-muted"),
        html.P("📊 グラフ実装予定", className="text-info")
    ])

# ========================================
# アプリ起動
# ========================================

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 Dashアプリ起動中...")
    print(f"📂 CSV: {CSV_PATH}")
    print(f"📊 データ: {len(DF)}行 × {len(DF.columns) if not DF.empty else 0}列")
    print("=" * 60)
    app.run_server(debug=True, host='127.0.0.1', port=8050)
