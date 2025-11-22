"""
グラフに日本語の軸ラベルを追加するスクリプト
"""

import re

# ファイルを読み込み
with open('mapcomplete_dashboard/mapcomplete_dashboard.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 各グラフの軸ラベル定義
axis_labels = {
    # FLOWグラフ
    'flow_inflow_ranking_chart': {'x': '人数（人）', 'y': '市区町村'},
    'flow_outflow_ranking_chart': {'x': '人数（人）', 'y': '市区町村'},
    'flow_netflow_ranking_chart': {'x': '人数（人）', 'y': '市区町村'},

    # GAPグラフ
    'gap_shortage_ranking_chart': {'x': '需要超過（人）', 'y': '市区町村'},
    'gap_surplus_ranking_chart': {'x': '供給超過（人）', 'y': '市区町村'},

    # RARITYグラフ
    'rarity_national_chisq_ranking_chart': {'x': 'カイ二乗値', 'y': '資格・職種'},
    'rarity_national_rarity_ranking_chart': {'x': '希少性スコア', 'y': '資格・職種'},
    'rarity_nonnational_ranking_chart': {'x': '希少性スコア', 'y': '資格・職種'},

    # COMPETITIONグラフ
    'competition_national_license_ranking_chart': {'x': '国家資格保有率（%）', 'y': '職種'},
    'competition_qualification_ranking_chart': {'x': '平均資格数', 'y': '職種'},
    'competition_female_ratio_ranking_chart': {'x': '女性比率（%）', 'y': '年齢層'},
}

# 各関数内のx_axisとy_axisを修正
for func_name, labels in axis_labels.items():
    # 関数の開始位置を検索
    pattern = rf'(def {func_name}\(\) -> rx\.Component:.*?)(rx\.recharts\.x_axis\(type_="number", stroke="#94a3b8"\))'

    # X軸にlabel追加
    replacement_x = r'\1' + f'rx.recharts.x_axis(type_="number", stroke="#94a3b8", label={{"value": "{labels["x"]}", "position": "insideBottom", "offset": -10, "style": {{"fill": "#94a3b8", "fontSize": 12}}}})'

    content = re.sub(pattern, replacement_x, content, flags=re.DOTALL)

    # Y軸にlabel追加
    pattern_y = rf'(def {func_name}\(\) -> rx\.Component:.*?)(rx\.recharts\.y_axis\(data_key="name", type_="category", width=120, stroke="#94a3b8"\))'

    replacement_y = r'\1' + f'rx.recharts.y_axis(data_key="name", type_="category", width=120, stroke="#94a3b8", label={{"value": "{labels["y"]}", "angle": -90, "position": "insideLeft", "style": {{"fill": "#94a3b8", "fontSize": 12}}}})'

    content = re.sub(pattern_y, replacement_y, content, flags=re.DOTALL)

print("軸ラベル追加完了")

# ファイルに書き込み
with open('mapcomplete_dashboard/mapcomplete_dashboard.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ 日本語軸ラベルの追加が完了しました")
