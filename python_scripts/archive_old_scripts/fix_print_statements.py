# -*- coding: utf-8 -*-
"""comprehensive_test_suite_v3.py内のprint文をself.safe_print()に置換"""
from pathlib import Path
import re

file_path = Path(__file__).parent / 'comprehensive_test_suite_v3.py'

content = file_path.read_text(encoding='utf-8')

# クラスメソッド内のprint文をself.safe_print()に置換
# ただし、log_test内のprintは既にtry-exceptで囲まれているので除外
# また、__main__のprintも除外

# まず、クラス定義開始から__main__までの範囲を特定
class_start = content.find('class V3TestSuite:')
main_start = content.find("if __name__ == '__main__':")

if class_start == -1 or main_start == -1:
    print("クラス定義または__main__が見つかりません")
    exit(1)

# クラス部分を抽出
class_part = content[class_start:main_start]

# クラス内のprint文を置換（インデントあり）
# 4スペース以上のインデントがあるprint文を対象
class_part = re.sub(r'(\s{4,})print\(', r'\1self.safe_print(', class_part)

# ファイルを再構成
new_content = content[:class_start] + class_part + content[main_start:]

# 書き込み
file_path.write_text(new_content, encoding='utf-8')

print("✅ print文をself.safe_print()に置換完了")
