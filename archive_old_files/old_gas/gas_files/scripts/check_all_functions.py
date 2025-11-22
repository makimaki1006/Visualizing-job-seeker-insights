import re
import os

# MenuIntegration.gsから関数名を抽出
with open('MenuIntegration.gs', 'r', encoding='utf-8') as f:
    menu_content = f.read()

# .addItem('...', 'functionName')のパターンで関数名を抽出
function_pattern = r"\.addItem\(['\"].*?['\"]\s*,\s*['\"](\w+)['\"]"
menu_functions = re.findall(function_pattern, menu_content)

# 重複を削除してソート
menu_functions = sorted(set(menu_functions))

print(f"=== MenuIntegration.gsで参照される関数 ({len(menu_functions)}個) ===\n")

# すべてのGASファイルを読み込んで関数定義を検索
gas_files = [f for f in os.listdir('.') if f.endswith('.gs') and not f.endswith('.bak') and not f.endswith('.bak2')]
all_functions = {}

for gas_file in gas_files:
    with open(gas_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # function functionName()のパターンで関数定義を抽出
    func_defs = re.findall(r'^function\s+(\w+)\s*\(', content, re.MULTILINE)
    
    for func_name in func_defs:
        if func_name not in all_functions:
            all_functions[func_name] = []
        all_functions[func_name].append(gas_file)

# メニュー関数の存在チェック
missing = []
found = []

for func in menu_functions:
    if func in all_functions:
        found.append((func, all_functions[func]))
    else:
        missing.append(func)

# 結果出力
print(f"✅ 定義済み関数: {len(found)}個")
for func, files in found:
    print(f"  {func:<40} -> {', '.join(files)}")

print(f"\n❌ 欠損関数: {len(missing)}個")
for func in missing:
    print(f"  {func}")

print(f"\n=== サマリー ===")
print(f"メニューに登録された関数: {len(menu_functions)}個")
print(f"定義済み: {len(found)}個 ({len(found)/len(menu_functions)*100:.1f}%)")
print(f"欠損: {len(missing)}個 ({len(missing)/len(menu_functions)*100:.1f}%)")
