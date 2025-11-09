#!/bin/bash

# MenuIntegration.gsから関数名を抽出
menu_functions=$(grep -oP "(?<=addItem\()[^)]*'(\w+)'(?=\))" MenuIntegration.gs | grep -oP "'\K\w+(?=')" | sort -u)

# 全gsファイルから関数定義を抽出
all_functions=$(find . -maxdepth 1 -name "*.gs" -exec grep -h "^function " {} \; | grep -oP "function \K\w+" | sort -u)

echo "=== Menu Function Check ==="
echo "Total menu functions: $(echo "$menu_functions" | wc -l)"
echo ""
echo "Checking each function..."

missing=0
found=0

for func in $menu_functions; do
  if echo "$all_functions" | grep -q "^${func}$"; then
    echo "[OK] $func"
    ((found++))
  else
    echo "[NG] $func - NOT FOUND"
    ((missing++))
  fi
done

echo ""
echo "=== Summary ==="
echo "Found: $found functions"
echo "Missing: $missing functions"
echo "Completion: $(( found * 100 / (found + missing) ))%"
