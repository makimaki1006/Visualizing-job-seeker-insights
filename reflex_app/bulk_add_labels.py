"""
残りのグラフに日本語軸ラベルを一括追加
"""

#ファイル読み込み
with open('mapcomplete_dashboard/mapcomplete_dashboard.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 置換対象の定義（関数名と対応するラベル）
replacements = [
    # 純流入ランキング（flow_netflow_ranking_chart）
    ('flow_netflow_ranking_chart', '人数（人）', '市区町村'),
    # 需要超過ランキング（gap_shortage_ranking_chart）
    ('gap_shortage_ranking_chart', '需要超過（人）', '市区町村'),
    # 供給超過ランキング（gap_surplus_ranking_chart）
    ('gap_surplus_ranking_chart', '供給超過（人）', '市区町村'),
    # 国家資格（カイ二乗値）
    ('rarity_national_chisq_ranking_chart', 'カイ二乗値', '資格・職種'),
    # 国家資格（希少性スコア）
    ('rarity_national_rarity_ranking_chart', '希少性スコア', '資格・職種'),
    # 国家資格非保有者
    ('rarity_nonnational_ranking_chart', '希少性スコア', '資格・職種'),
    # 国家資格保有率
    ('competition_national_license_ranking_chart', '国家資格保有率（%）', '職種'),
    # 平均資格数
    ('competition_qualification_ranking_chart', '平均資格数', '職種'),
    # 女性比率
    ('competition_female_ratio_ranking_chart', '女性比率（%）', '年齢層'),
]

# 各関数内の軸定義を置換
i = 0
while i < len(lines):
    # 対象関数を検索
    for func_name, x_label, y_label in replacements:
        if f'def {func_name}()' in lines[i]:
            print(f"処理中: {func_name}")

            # この関数内のx_axisとy_axisを探す（次の関数定義まで）
            j = i + 1
            while j < len(lines) and 'def ' not in lines[j]:
                # X軸の置換
                if 'rx.recharts.x_axis(type_="number", stroke="#94a3b8")' in lines[j]:
                    lines[j] = f'                rx.recharts.x_axis(\n'
                    lines.insert(j+1, f'                    type_="number",\n')
                    lines.insert(j+2, f'                    stroke="#94a3b8",\n')
                    lines.insert(j+3, f'                    label={{"value": "{x_label}", "position": "insideBottom", "offset": -10, "style": {{"fill": "#94a3b8", "fontSize": 12}}}}\n')
                    lines.insert(j+4, f'                ),\n')
                    print(f"  ✅ X軸修正: {x_label}")
                    j += 4  # 挿入した行数分スキップ

                # Y軸の置換
                elif 'rx.recharts.y_axis(data_key="name", type_="category", width=120, stroke="#94a3b8")' in lines[j]:
                    lines[j] = f'                rx.recharts.y_axis(\n'
                    lines.insert(j+1, f'                    data_key="name",\n')
                    lines.insert(j+2, f'                    type_="category",\n')
                    lines.insert(j+3, f'                    width=120,\n')
                    lines.insert(j+4, f'                    stroke="#94a3b8",\n')
                    lines.insert(j+5, f'                    label={{"value": "{y_label}", "angle": -90, "position": "insideLeft", "style": {{"fill": "#94a3b8", "fontSize": 12}}}}\n')
                    lines.insert(j+6, f'                ),\n')
                    print(f"  ✅ Y軸修正: {y_label}")
                    j += 6  # 挿入した行数分スキップ

                j += 1
            break
    i += 1

# ファイルに書き込み
with open('mapcomplete_dashboard/mapcomplete_dashboard.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("\n✅ 日本語軸ラベルの一括追加が完了しました")
