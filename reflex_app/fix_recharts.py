"""Rechartsグラフ関数を修正するスクリプト"""
import re

# ファイル読み込み
with open('mapcomplete_dashboard/mapcomplete_dashboard.py', 'r', encoding='utf-8') as f:
    content = f.read()

# recharts_bar_chart()関数全体を削除（def から次のdef の直前まで）
pattern1 = r'def recharts_bar_chart\(.*?\n(?=def |class )'
content = re.sub(pattern1, '', content, flags=re.DOTALL)

# recharts_qualification_chart()関数全体を削除
pattern2 = r'def recharts_qualification_chart\(.*?\n(?=def |class )'
content = re.sub(pattern2, '', content, flags=re.DOTALL)

# kpi_card()関数の直前に新しい2つの関数を挿入
new_functions = '''def overview_age_gender_chart() -> rx.Component:
    """概要: 年齢×性別グラフ（Recharts）"""
    return rx.box(
        rx.recharts.bar_chart(
            rx.recharts.bar(
                data_key="男性",
                stroke="#38bdf8",
                fill="#38bdf8",
            ),
            rx.recharts.bar(
                data_key="女性",
                stroke="#ec4899",
                fill="#ec4899",
            ),
            rx.recharts.x_axis(data_key="name", stroke="#94a3b8"),
            rx.recharts.y_axis(stroke="#94a3b8"),
            rx.recharts.legend(),
            rx.recharts.graphing_tooltip(),
            data=DashboardState.overview_age_gender_data,
            width="100%",
            height="400px",
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
                stroke="#8b5cf6",
                fill="#8b5cf6",
            ),
            rx.recharts.x_axis(data_key="name", stroke="#94a3b8"),
            rx.recharts.y_axis(stroke="#94a3b8"),
            rx.recharts.graphing_tooltip(),
            data=DashboardState.supply_qualification_buckets_data,
            width="100%",
            height="350px",
        ),
        background=CARD_BG,
        border_radius="12px",
        border=f"1px solid {BORDER_COLOR}",
        padding="1.5rem",
        width="100%"
    )


'''

# kpi_card()の直前に挿入
content = content.replace('def kpi_card(label: str, value: str, unit: str = "") -> rx.Component:',
                          new_functions + 'def kpi_card(label: str, value: str, unit: str = "") -> rx.Component:')

# 関数呼び出しを更新
content = content.replace('recharts_bar_chart(DashboardState.overview_age_gender_data)', 'overview_age_gender_chart()')
content = content.replace('recharts_qualification_chart(DashboardState.supply_qualification_buckets_data, height="350px")', 'supply_qualification_chart()')

# ファイル書き込み
with open('mapcomplete_dashboard/mapcomplete_dashboard.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("修正完了: Rechartsグラフ関数をStateプロパティ直接参照に変更しました")
