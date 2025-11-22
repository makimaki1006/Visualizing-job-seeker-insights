import pandas as pd

df = pd.read_csv('../python_scripts/data/output_v2/mapcomplete_complete_sheets/MapComplete_Complete_All_FIXED.csv', encoding='utf-8-sig')

print('=== SUMMARY supply関連カラム ===')
supply_cols = [c for c in df.columns if 'supply' in c.lower() or 'qualification' in c.lower() or 'license' in c.lower()]
print(supply_cols)

print('\n=== SUMMARY サンプルデータ ===')
summary = df[df['row_type'] == 'SUMMARY'].head(1)
for col in supply_cols:
    if col in summary.columns:
        print(f'{col}: {summary[col].values[0]}')
