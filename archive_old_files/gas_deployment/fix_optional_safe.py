#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Optional Chainingを安全に修正するスクリプト
個別の修正パターンを慎重に適用
"""
import re

def safe_replace(content, old_pattern, new_pattern):
    """パターンマッチングで安全に置換"""
    count = len(re.findall(old_pattern, content))
    if count > 0:
        content = re.sub(old_pattern, new_pattern, content)
        print(f'  - Replaced {count} occurrence(s)')
    return content

# ファイル読み込み
with open('map_complete_integrated.html', 'r', encoding='utf-8') as f:
    content = f.read()

print('Before:', len(re.findall(r'\?\.', content)), 'optional chaining')

# 個別パターンを慎重に置換
print('\n1. selectedRegion?.prefecture')
content = safe_replace(
    content,
    r'selectedRegion\?\.prefecture',
    '(selectedRegion && selectedRegion.prefecture)'
)

print('2. selectedRegion?.municipality')
content = safe_replace(
    content,
    r'selectedRegion\?\.municipality',
    '(selectedRegion && selectedRegion.municipality)'
)

print('3. selectedRegion?.key')
content = safe_replace(
    content,
    r'selectedRegion\?\.key',
    '(selectedRegion && selectedRegion.key)'
)

print('4. municipalities[0]?.key')
content = safe_replace(
    content,
    r'municipalities\[0\]\?\.key',
    '(municipalities[0] && municipalities[0].key)'
)

print('5. currentCity?.flow?.nearby_regions')
content = safe_replace(
    content,
    r'currentCity\?\.flow\?\.nearby_regions',
    '(currentCity && currentCity.flow && currentCity.flow.nearby_regions)'
)

print('6. DATA?.[activeCity]?.center')
content = safe_replace(
    content,
    r'DATA\?\.\[activeCity\]\?\.center',
    '(DATA && DATA[activeCity] && DATA[activeCity].center)'
)

print('7. c?.center')
content = safe_replace(
    content,
    r'c\?\.center',
    '(c && c.center)'
)

print('8. k.labels?.[i]')
content = safe_replace(
    content,
    r'k\.labels\?\.\[i\]',
    '(k.labels && k.labels[i])'
)

print('9. options?.limit')
content = safe_replace(
    content,
    r'options\?\.limit',
    '(options && options.limit)'
)

print('10. options?.exclude')
content = safe_replace(
    content,
    r'options\?\.exclude',
    '(options && options.exclude)'
)

print('11. options?.keys')
content = safe_replace(
    content,
    r'options\?\.keys',
    '(options && options.keys)'
)

print('12. options?.maxColumns')
content = safe_replace(
    content,
    r'options\?\.maxColumns',
    '(options && options.maxColumns)'
)

print('13. options?.rowLabel')
content = safe_replace(
    content,
    r'options\?\.rowLabel',
    '(options && options.rowLabel)'
)

print('14. options?.columnLabel')
content = safe_replace(
    content,
    r'options\?\.columnLabel',
    '(options && options.columnLabel)'
)

print('15. options?.chartId')
content = safe_replace(
    content,
    r'options\?\.chartId',
    '(options && options.chartId)'
)

print('16. options?.chartTitle')
content = safe_replace(
    content,
    r'options\?\.chartTitle',
    '(options && options.chartTitle)'
)

print('17. qs(...)?.selectedOptions (difficultyFilter)')
content = safe_replace(
    content,
    r"qs\('#difficultyFilter'\)\?\.selectedOptions",
    "(qs('#difficultyFilter') && qs('#difficultyFilter').selectedOptions)"
)

print('18. qs(...)?.selectedOptions (ageGroupFilter)')
content = safe_replace(
    content,
    r"qs\('#ageGroupFilter'\)\?\.selectedOptions",
    "(qs('#ageGroupFilter') && qs('#ageGroupFilter').selectedOptions)"
)

print('19. qs(...)?.selectedOptions (genderFilter)')
content = safe_replace(
    content,
    r"qs\('#genderFilter'\)\?\.selectedOptions",
    "(qs('#genderFilter') && qs('#genderFilter').selectedOptions)"
)

print('20. qs(...)?.selectedOptions (qualificationFilter)')
content = safe_replace(
    content,
    r"qs\('#qualificationFilter'\)\?\.selectedOptions",
    "(qs('#qualificationFilter') && qs('#qualificationFilter').selectedOptions)"
)

print('21. qs(...)?.selectedOptions (residenceFilter)')
content = safe_replace(
    content,
    r"qs\('#residenceFilter'\)\?\.selectedOptions",
    "(qs('#residenceFilter') && qs('#residenceFilter').selectedOptions)"
)

print('22. (c.overview && c.overview.kpis)?.find')
content = safe_replace(
    content,
    r'\(c\.overview && c\.overview\.kpis\)\?\.find',
    '((c.overview && c.overview.kpis) && (c.overview.kpis).find)'
)

print('23. regionOptions?.prefectures?.length')
content = safe_replace(
    content,
    r'regionOptions\?\.prefectures\?\.length',
    '(regionOptions && regionOptions.prefectures && regionOptions.prefectures.length)'
)

print('\nAfter:', len(re.findall(r'\?\.', content)), 'optional chaining')

# ファイル書き込み
with open('map_complete_integrated.html', 'w', encoding='utf-8') as f:
    f.write(content)

print('\nOK: Safe replacement completed')
