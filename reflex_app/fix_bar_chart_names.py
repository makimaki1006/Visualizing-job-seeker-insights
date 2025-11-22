"""
横棒グラフのdata_keyに日本語のname属性を追加
"""

with open('mapcomplete_dashboard/mapcomplete_dashboard.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 置換対象の定義（関数名とname属性）
replacements = [
    # FLOW系
    ('flow_inflow_ranking_chart', '流入人数'),
    ('flow_outflow_ranking_chart', '流出人数'),
    ('flow_netflow_ranking_chart', '純流入'),
    # GAP系
    ('gap_shortage_ranking_chart', '需要超過'),
    ('gap_surplus_ranking_chart', '供給超過'),
    ('gap_ratio_ranking_chart', '需給比率'),
    # RARITY系
    ('rarity_national_license_ranking_chart', '希少性スコア'),
    # COMPETITION系
    ('competition_national_license_ranking_chart', '国家資格保有率'),
    ('competition_qualification_ranking_chart', '平均資格数'),
    ('competition_female_ratio_ranking_chart', '女性比率'),
    # その他
    ('supply_persona_qual_chart', '平均資格数'),
    ('persona_bar_chart', '人数'),
    ('rarity_score_chart', '希少性スコア'),
]

modified_count = 0

i = 0
while i < len(lines):
    for func_name, japanese_name in replacements:
        if f'def {func_name}()' in lines[i]:
            print(f"処理中: {func_name}")

            # この関数内のrx.recharts.bar(data_key="value"を探す
            j = i + 1
            while j < len(lines) and 'def ' not in lines[j]:
                # data_key="value"を含むbar定義を探す
                if 'rx.recharts.bar(' in lines[j] and 'data_key="value"' in lines[j+1]:
                    # 次の行を確認
                    if 'data_key="value"' in lines[j+1]:
                        # nameパラメータを追加
                        old_line = lines[j+1]
                        new_line = old_line.replace(
                            'data_key="value",',
                            f'data_key="value",\n                    name="{japanese_name}",'
                        )
                        lines[j+1] = new_line
                        print(f"  修正: name=\"{japanese_name}\"を追加")
                        modified_count += 1
                        break

                # 別パターン: インライン記述
                if 'rx.recharts.bar(' in lines[j]:
                    # 同じ行または次の数行にdata_key="value"がある場合
                    for k in range(j, min(j+5, len(lines))):
                        if 'data_key="value",' in lines[k] and 'name=' not in lines[k]:
                            lines[k] = lines[k].replace(
                                'data_key="value",',
                                f'data_key="value", name="{japanese_name}",'
                            )
                            print(f"  修正（インライン）: name=\"{japanese_name}\"を追加")
                            modified_count += 1
                            break
                    break

                j += 1
            break
    i += 1

# ファイルに書き込み
with open('mapcomplete_dashboard/mapcomplete_dashboard.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print(f"\n横棒グラフのname属性追加が完了しました")
print(f"修正箇所: {modified_count}個のグラフ")
