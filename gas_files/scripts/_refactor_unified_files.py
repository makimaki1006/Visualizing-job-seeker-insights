# -*- coding: utf-8 -*-
"""
統合ファイルリファクタリングスクリプト

目的：
1. 共通スタイル定義を抽出
2. 共通ユーティリティ関数を抽出
3. コードの重複を削減
4. 可読性の向上
"""
import os
import re

# 共通スタイル定義（全Phase共通）
COMMON_STYLES = """
    /* 共通スタイル */
    body {
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      margin: 20px;
      background-color: #f5f5f5;
    }
    h1 {
      color: #1a73e8;
      border-bottom: 3px solid #1a73e8;
      padding-bottom: 10px;
    }
    h2 {
      color: #333;
      margin-top: 20px;
    }
    .container {
      background-color: white;
      padding: 20px;
      border-radius: 8px;
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
      margin-bottom: 20px;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      margin-top: 10px;
    }
    th, td {
      padding: 12px;
      text-align: left;
      border-bottom: 1px solid #ddd;
    }
    th {
      background-color: #1a73e8;
      color: white;
      font-weight: bold;
      position: sticky;
      top: 0;
      z-index: 10;
    }
    tr:hover {
      background-color: #f5f5f5;
    }
    .stat-card {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      padding: 20px;
      border-radius: 8px;
      text-align: center;
    }
    .stat-label {
      font-size: 12px;
      opacity: 0.9;
      margin-bottom: 5px;
    }
    .stat-value {
      font-size: 28px;
      font-weight: bold;
    }
"""

# 共通ユーティリティ関数（ファイル先頭に配置）
COMMON_UTILITIES = """
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 共通ユーティリティ関数
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

/**
 * データ読み込み共通エラーハンドリング
 * @param {string} sheetName - シート名
 * @param {number} columnCount - カラム数
 * @return {Array<Array>} データ配列
 */
function loadSheetData_(sheetName, columnCount) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName(sheetName);

  if (!sheet) {
    throw new Error(`${sheetName}シートが見つかりません`);
  }

  const lastRow = sheet.getLastRow();
  if (lastRow <= 1) {
    return [];
  }

  const range = sheet.getRange(2, 1, lastRow - 1, columnCount);
  return range.getValues();
}

/**
 * データなしアラート表示
 * @param {string} sheetName - シート名
 * @param {string} phaseName - Phase名
 */
function showNoDataAlert_(sheetName, phaseName) {
  const ui = SpreadsheetApp.getUi();
  ui.alert(
    'データなし',
    `${sheetName}シートにデータがありません。\\n` +
    `先に「${phaseName}データ取り込み」を実行してください。`,
    ui.ButtonSet.OK
  );
}

/**
 * エラーアラート表示
 * @param {Error} error - エラーオブジェクト
 * @param {string} context - エラーコンテキスト
 */
function showErrorAlert_(error, context) {
  const ui = SpreadsheetApp.getUi();
  ui.alert('エラー', `${context}中にエラーが発生しました:\\n${error.message}`, ui.ButtonSet.OK);
  Logger.log(`${context}エラー: ${error.stack}`);
}

/**
 * HTMLダイアログ表示
 * @param {string} html - HTML文字列
 * @param {string} title - ダイアログタイトル
 * @param {number} width - 幅（デフォルト: 1400）
 * @param {number} height - 高さ（デフォルト: 900）
 */
function showHtmlDialog_(html, title, width = 1400, height = 900) {
  const htmlOutput = HtmlService.createHtmlOutput(html)
    .setWidth(width)
    .setHeight(height);
  SpreadsheetApp.getUi().showModalDialog(htmlOutput, title);
}

"""

def analyze_file(filepath):
    """ファイルの統計情報を取得"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    lines = content.count('\n')
    functions = len(re.findall(r'^\s*function\s+\w+', content, re.MULTILINE))
    comments = len(re.findall(r'/\*\*[\s\S]*?\*/', content))

    return {
        'lines': lines,
        'functions': functions,
        'comments': comments,
        'size_kb': len(content.encode('utf-8')) / 1024
    }

def add_common_utilities(content, phase_name):
    """共通ユーティリティ関数を追加"""
    # ヘッダーコメントの後に共通関数を挿入
    header_end = content.find('\n\n// ━━━━')
    if header_end == -1:
        header_end = content.find('\n\n/**')

    if header_end != -1:
        before = content[:header_end]
        after = content[header_end:]
        return before + '\n' + COMMON_UTILITIES + after

    return COMMON_UTILITIES + '\n' + content

def optimize_styles(content):
    """スタイル定義を最適化"""
    # 重複するスタイルブロックを検出
    style_blocks = re.findall(r'<style>(.*?)</style>', content, re.DOTALL)

    if not style_blocks:
        return content

    # 最初のstyleブロックを共通スタイルで置き換え
    first_style = re.search(r'<style>.*?</style>', content, re.DOTALL)
    if first_style:
        # 既存のスタイルを保持しつつ、共通スタイルを追加
        new_style = '<style>' + COMMON_STYLES + '\n    /* Phase固有スタイル */' + style_blocks[0] + '</style>'
        content = content.replace(first_style.group(0), new_style, 1)

    return content

def remove_duplicate_functions(content):
    """重複する関数を削除"""
    # 関数名の出現回数をカウント
    function_pattern = r'function\s+(\w+)\s*\('
    functions = re.findall(function_pattern, content)

    # 重複している関数を特定
    from collections import Counter
    duplicates = [name for name, count in Counter(functions).items() if count > 1]

    if duplicates:
        print(f'  重複関数検出: {", ".join(duplicates)}')

    return content

def refactor_file(filepath, phase_name):
    """ファイルをリファクタリング"""
    print(f'\nリファクタリング: {os.path.basename(filepath)}')

    # 元のファイルを読み込み
    with open(filepath, 'r', encoding='utf-8') as f:
        original = f.read()

    # リファクタリング前の統計
    before_stats = analyze_file(filepath)
    print(f'  リファクタリング前: {before_stats["lines"]}行, {before_stats["functions"]}関数')

    # リファクタリング実行
    content = original

    # 1. 共通ユーティリティ関数を追加
    content = add_common_utilities(content, phase_name)

    # 2. スタイルを最適化
    content = optimize_styles(content)

    # 3. 重複関数を削除
    content = remove_duplicate_functions(content)

    # バックアップファイル作成
    backup_path = filepath.replace('.gs', '_before_refactor.gs')
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(original)
    print(f'  バックアップ作成: {os.path.basename(backup_path)}')

    # リファクタリング後のファイルを保存
    refactored_path = filepath.replace('.gs', '_refactored.gs')
    with open(refactored_path, 'w', encoding='utf-8') as f:
        f.write(content)

    # リファクタリング後の統計
    after_lines = content.count('\n')
    print(f'  リファクタリング後: {after_lines}行 ({before_stats["lines"] - after_lines:+d}行)')

    return {
        'file': os.path.basename(filepath),
        'before': before_stats,
        'after': {
            'lines': after_lines,
            'size_kb': len(content.encode('utf-8')) / 1024
        }
    }

def main():
    """メイン処理"""
    script_dir = os.path.dirname(os.path.abspath(__file__))

    files = [
        ('Phase7UnifiedVisualizations.gs', 'Phase 7'),
        ('Phase8UnifiedVisualizations.gs', 'Phase 8'),
        ('Phase10UnifiedVisualizations.gs', 'Phase 10'),
    ]

    results = []

    for filename, phase_name in files:
        filepath = os.path.join(script_dir, filename)
        if os.path.exists(filepath):
            result = refactor_file(filepath, phase_name)
            results.append(result)
        else:
            print(f'警告: {filename} が見つかりません')

    print('\n' + '=' * 60)
    print('リファクタリング完了サマリー')
    print('=' * 60)

    total_before = sum(r['before']['lines'] for r in results)
    total_after = sum(r['after']['lines'] for r in results)

    print(f'\n総行数: {total_before}行 → {total_after}行 ({total_before - total_after:+d}行削減)')

    for result in results:
        before = result['before']['lines']
        after = result['after']['lines']
        reduction = ((before - after) / before * 100) if before > 0 else 0
        print(f'\n{result["file"]}:')
        print(f'  {before}行 → {after}行 ({reduction:.1f}%削減)')

if __name__ == '__main__':
    main()
