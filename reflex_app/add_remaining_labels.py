"""
残りのグラフに日本語軸ラベルを追加
"""
import re

# ファイル読み込み
with open('mapcomplete_dashboard/mapcomplete_dashboard.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 置換パターン1: supply_persona_qual_chart (Line 3534-3535)
pattern1 = r'(def supply_persona_qual_chart.*?)(rx\.recharts\.x_axis\(type_="number", stroke="#94a3b8"\),\s+rx\.recharts\.y_axis\(data_key="name", type_="category", stroke="#94a3b8"\))'
replacement1 = r'''\1rx.recharts.x_axis(
                type_="number",
                stroke="#94a3b8",
                label={"value": "平均資格数", "position": "insideBottom", "offset": -10, "style": {"fill": "#94a3b8", "fontSize": 12}}
            ),
            rx.recharts.y_axis(
                data_key="name",
                type_="category",
                stroke="#94a3b8",
                label={"value": "ペルソナ", "angle": -90, "position": "insideLeft", "style": {"fill": "#94a3b8", "fontSize": 12}}
            )'''

content = re.sub(pattern1, replacement1, content, flags=re.DOTALL)
print("1. supply_persona_qual_chart修正完了")

# 置換パターン2: gap_ratio_ranking関数内 (Line 3782-3783)
pattern2 = r'(需給比率ランキング.*?)(rx\.recharts\.x_axis\(type_="number", stroke="#94a3b8"\),\s+rx\.recharts\.y_axis\(data_key="name", type_="category", width=120, stroke="#94a3b8"\))'
replacement2 = r'''\1rx.recharts.x_axis(
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
                )'''

content = re.sub(pattern2, replacement2, content, flags=re.DOTALL)
print("2. gap_ratio_ranking修正完了")

# 置換パターン3: rarity_national_license_ranking_chart (Line 3817-3818)
pattern3 = r'(国家資格保有者ランキング.*?)(rx\.recharts\.x_axis\(type_="number", stroke="#94a3b8"\),\s+rx\.recharts\.y_axis\(data_key="name", type_="category", width=200, stroke="#94a3b8"\))'
replacement3 = r'''\1rx.recharts.x_axis(
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
                )'''

content = re.sub(pattern3, replacement3, content, flags=re.DOTALL)
print("3. rarity_national_license_ranking_chart修正完了")

# 置換パターン4: persona_bar_chart (Line 4107-4108)
pattern4 = r'(def persona_bar_chart.*?)(rx\.recharts\.x_axis\(type_="number", stroke="#94a3b8"\),  # 値軸として明示\s+rx\.recharts\.y_axis\(data_key="name", type_="category", width=180, stroke="#94a3b8"\))'
replacement4 = r'''\1rx.recharts.x_axis(
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
            )'''

content = re.sub(pattern4, replacement4, content, flags=re.DOTALL)
print("4. persona_bar_chart修正完了")

# 置換パターン5: rarity_score_chart (Line 4271-4272)
pattern5 = r'(def rarity_score_chart.*?)(rx\.recharts\.x_axis\(type_="number", stroke="#94a3b8"\),\s+rx\.recharts\.y_axis\(data_key="label", type_="category", stroke="#94a3b8"\))'
replacement5 = r'''\1rx.recharts.x_axis(
                type_="number",
                stroke="#94a3b8",
                label={"value": "希少性スコア", "position": "insideBottom", "offset": -10, "style": {"fill": "#94a3b8", "fontSize": 12}}
            ),
            rx.recharts.y_axis(
                data_key="label",
                type_="category",
                stroke="#94a3b8",
                label={"value": "職種・資格", "angle": -90, "position": "insideLeft", "style": {"fill": "#94a3b8", "fontSize": 12}}
            )'''

content = re.sub(pattern5, replacement5, content, flags=re.DOTALL)
print("5. rarity_score_chart修正完了")

# ファイルに書き込み
with open('mapcomplete_dashboard/mapcomplete_dashboard.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("\n全ての残りグラフへの日本語軸ラベル追加が完了しました")
