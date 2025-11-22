"""
色盲対応カラーパレット統一スクリプト

問題:
- Okabe-Itoカラーパレットが定義されているが、実際のグラフでは使用されていない
- 特に横棒グラフで色が設定されていない（デフォルト色になっている）

修正内容:
1. 横棒グラフにfill属性を追加（COLOR_PALETTE[0]を使用）
2. ドーナツチャートの色を統一
3. 折れ線グラフの色を統一
"""

import re

def fix_colorblind_palette():
    """色盲対応カラーパレットをすべてのグラフに適用"""

    file_path = r"C:\Users\fuji1\OneDrive\Pythonスクリプト保管\job_medley_project\reflex_app\mapcomplete_dashboard\mapcomplete_dashboard.py"

    # 読み込み
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. 横棒グラフの色を修正（rx.recharts.bar_chart）
    # すべてのbar_chartにfill属性を追加
    print("横棒グラフの色を修正中...")

    # COLOR_PALETTEの定義を確認（46行目付近にある）
    if "COLOR_PALETTE" not in content[:2000]:
        print("ERROR: COLOR_PALETTEが定義されていません")
        return False

    # 横棒グラフのパターンを探す
    bar_chart_pattern = r'(rx\.recharts\.bar_chart\([^)]*)'

    def add_fill_to_bar_chart(match):
        chart_call = match.group(1)
        # すでにfillが含まれているか確認
        if 'fill=' in chart_call:
            return chart_call
        # fillがない場合、追加
        # layoutが含まれている場合はその前に追加
        if 'layout=' in chart_call:
            chart_call = chart_call.replace('layout=', 'fill=COLOR_PALETTE[0],\n                        layout=')
        else:
            # 最後にfillを追加
            chart_call = chart_call + ',\n                        fill=COLOR_PALETTE[0]'
        return chart_call

    content = re.sub(bar_chart_pattern, add_fill_to_bar_chart, content)

    # 2. ドーナツチャートの色の統一
    print("ドーナツチャートの色を修正中...")

    # gender_dataの色を修正（男性=青、女性=オレンジ）
    old_gender_colors = [
        '"fill": "#3b82f6"',  # 男性（青）
        '"fill": "#f97316"',  # 女性（オレンジ）
    ]
    new_gender_colors = [
        '"fill": COLOR_PALETTE[0]',  # 男性（色盲対応青）
        '"fill": COLOR_PALETTE[1]',  # 女性（色盲対応オレンジ）
    ]

    for old, new in zip(old_gender_colors, new_gender_colors):
        content = content.replace(old, new)

    # 3. 折れ線グラフの色を修正
    print("折れ線グラフの色を修正中...")

    # rx.recharts.lineのstroke属性を修正
    line_pattern = r'(rx\.recharts\.line\([^)]*stroke="[^"]*")'

    def fix_line_stroke(match):
        line_call = match.group(1)
        # 固定の色文字列をCOLOR_PALETTEに置き換え
        line_call = re.sub(r'stroke="#[0-9a-fA-F]{6}"', 'stroke=COLOR_PALETTE[0]', line_call)
        return line_call

    content = re.sub(line_pattern, fix_line_stroke, content)

    # 4. エリアチャートの色を修正
    print("エリアチャートの色を修正中...")

    area_pattern = r'(rx\.recharts\.area\([^)]*)'

    def fix_area_colors(match):
        area_call = match.group(1)
        # fillとstrokeをCOLOR_PALETTEに置き換え
        if 'fill=' not in area_call:
            area_call = area_call.replace('stroke=', 'fill=COLOR_PALETTE[2],\n                        stroke=')
        return area_call

    content = re.sub(area_pattern, fix_area_colors, content)

    # 5. 固定カラーコードをCOLOR_PALETTEに置き換え
    print("固定カラーコードを置き換え中...")

    # よくある固定カラーのマッピング
    color_replacements = {
        '#3b82f6': 'COLOR_PALETTE[0]',  # 青
        '#f97316': 'COLOR_PALETTE[1]',  # オレンジ
        '#ec4899': 'COLOR_PALETTE[5]',  # ピンク
        '#8b5cf6': 'COLOR_PALETTE[2]',  # 紫
        '#10b981': 'COLOR_PALETTE[3]',  # 緑
        '#f59e0b': 'COLOR_PALETTE[4]',  # 黄
        '#6366f1': 'COLOR_PALETTE[6]',  # 濃紫
        '#ef4444': 'COLOR_PALETTE[7]',  # 赤
    }

    for old_color, new_color in color_replacements.items():
        # "fill": "#xxx" パターン
        content = content.replace(f'"fill": "{old_color}"', f'"fill": {new_color}')
        # fill="#xxx" パターン
        content = content.replace(f'fill="{old_color}"', f'fill={new_color}')
        # stroke="#xxx" パターン
        content = content.replace(f'stroke="{old_color}"', f'stroke={new_color}')

    # 保存
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print("\n色盲対応カラーパレットの適用が完了しました")
    return True

if __name__ == "__main__":
    fix_colorblind_palette()