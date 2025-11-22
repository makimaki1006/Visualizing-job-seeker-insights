"""
Rechartsグラフの凡例分析スクリプト

すべてのグラフで`name`パラメータが設定されているか確認
"""

import re
from pathlib import Path

def analyze_recharts_graphs(file_path):
    """Rechartsグラフを分析して凡例の状態を確認"""

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        lines = content.split('\n')

    # グラフ開始行を検索
    chart_pattern = r'rx\.recharts\.(bar|line|area|radar|pie|scatter)_chart'

    results = []

    for i, line in enumerate(lines, 1):
        if re.search(chart_pattern, line):
            # グラフの範囲を特定（次のreturnまたは次の関数定義まで）
            chart_start = i
            chart_end = i + 100  # 最大100行先まで見る

            # グラフのコードブロックを取得
            chart_block = '\n'.join(lines[chart_start-1:min(chart_end, len(lines))])

            # 凡例の有無
            has_legend = 'rx.recharts.legend()' in chart_block

            # グラフ系列要素（bar, line, area, scatter, radar）のみからdata_keyとnameを抽出
            # 軸（x_axis, y_axis）のdata_keyは除外
            series_pattern = r'rx\.recharts\.(bar|line|area|scatter|radar)\([^)]*data_key="([^"]+)"[^)]*\)'
            series_matches = re.findall(series_pattern, chart_block)
            data_keys = [match[1] for match in series_matches]

            # グラフ系列要素からnameパラメータを抽出
            name_pattern = r'rx\.recharts\.(bar|line|area|scatter|radar)\([^)]*name="([^"]+)"[^)]*\)'
            name_matches = re.findall(name_pattern, chart_block)
            names = [match[1] for match in name_matches]

            # pie_chartの場合は、name_keyを使用するのでスキップ（常に正常）
            is_pie_chart = 'rx.recharts.pie(' in chart_block
            if is_pie_chart and 'name_key=' in chart_block:
                # pie_chartでname_keyが設定されている場合は問題なし
                data_keys = []
                names = []

            # 関数名を探す
            func_match = None
            for j in range(max(0, chart_start - 30), chart_start):
                if 'def ' in lines[j]:
                    func_match = re.search(r'def (\w+)\(', lines[j])
                    break

            func_name = func_match.group(1) if func_match else "不明"

            # 分析結果
            result = {
                'line': chart_start,
                'function': func_name,
                'has_legend': has_legend,
                'data_keys': data_keys,
                'names': names,
                'needs_fix': has_legend and len(data_keys) > 0 and len(names) < len(data_keys)
            }

            results.append(result)

    return results

def print_results(results):
    """結果を表示"""
    print("=" * 100)
    print("Rechartsグラフ凡例分析結果")
    print("=" * 100)
    print()

    # 問題のあるグラフ
    issues = [r for r in results if r['needs_fix']]

    if issues:
        print(f"[NG] 修正が必要なグラフ: {len(issues)}個")
        print()

        for r in issues:
            print(f"Line {r['line']}: {r['function']}()")
            print(f"  凡例: {'あり' if r['has_legend'] else 'なし'}")
            print(f"  data_key: {', '.join(r['data_keys'])} ({len(r['data_keys'])}個)")
            print(f"  name: {', '.join(r['names'])} ({len(r['names'])}個)")
            print(f"  [NG] {len(r['data_keys']) - len(r['names'])}個のdata_keyにname未設定")
            print()
    else:
        print("[OK] すべてのグラフでnameパラメータが正しく設定されています")
        print()

    # 正常なグラフ
    ok_graphs = [r for r in results if not r['needs_fix']]
    print(f"[OK] 正常なグラフ: {len(ok_graphs)}個")
    print()

    # サマリー
    print("=" * 100)
    print("サマリー")
    print("=" * 100)
    print(f"総グラフ数: {len(results)}")
    print(f"凡例あり: {sum(1 for r in results if r['has_legend'])}")
    print(f"修正必要: {len(issues)}")
    print(f"正常: {len(ok_graphs)}")
    print()

    if issues:
        print("[NG] 修正が必要な箇所があります！")
    else:
        print("[OK] すべて正常です！")

if __name__ == "__main__":
    file_path = r"C:\Users\fuji1\OneDrive\Pythonスクリプト保管\job_medley_project\reflex_app\mapcomplete_dashboard\mapcomplete_dashboard.py"

    results = analyze_recharts_graphs(file_path)
    print_results(results)
