import re

# ファイルを読み込み
with open('mapcomplete_dashboard/mapcomplete_dashboard.py', 'r', encoding='utf-8') as f:
    content = f.read()

# パターン1: margin_top="2rem" の後に width= がない場合
pattern1 = r'(margin_top="2rem")\s*\)'
replacement1 = r'\1, width="100%")'

# パターン2: padding="1.5rem" の後に width= がない場合（margin_topがない）
pattern2 = r'(padding="1.5rem")\s*\)(?!.*width=)'
replacement2 = r'\1, width="100%")'

# 既にwidth="100%"が設定されている行はスキップ
# パターン1を適用
count1 = 0
def replace1(match):
    global count1
    line = match.group(0)
    # すでにwidthが設定されている場合はスキップ
    if 'width=' in line or 'width =' in line:
        return line
    count1 += 1
    return match.group(1) + ', width="100%")'

# パターン2を適用
count2 = 0
def replace2(match):
    global count2
    line = match.group(0)
    # すでにwidthが設定されている場合、またはmargin_topがある場合はスキップ
    if 'width=' in line or 'width =' in line or 'margin_top=' in line:
        return line
    count2 += 1
    return match.group(1) + ', width="100%")'

# 置換実行
new_content = re.sub(pattern1, replace1, content)
# new_content = re.sub(pattern2, replace2, new_content)

print(f"置換回数:")
print(f"  pattern1 (margin_top): {count1}箇所")
# print(f"  pattern2 (padding): {count2}箇所")

# ファイルに書き込み
with open('mapcomplete_dashboard/mapcomplete_dashboard.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("完了!")
