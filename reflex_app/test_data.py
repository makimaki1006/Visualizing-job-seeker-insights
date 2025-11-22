import pandas as pd

# CSVファイルを読み込み
csv_path = r"C:\Users\fuji1\OneDrive\Pythonスクリプト保管\job_medley_project\python_scripts\data\output_v2\mapcomplete_complete_sheets\MapComplete_Complete_All_FIXED.csv"
df = pd.read_csv(csv_path, low_memory=False)

print("=== データ確認 ===")
print(f"総行数: {len(df)}")
print(f"\nrow_typeの種類: {df['row_type'].unique()}")

# 群馬県のFLOWデータ確認
print("\n=== 群馬県FLOWデータ ===")
flow = df[
    (df['row_type'] == 'FLOW') &
    (df['prefecture'] == '群馬県')
].copy()
print(f"FLOW件数: {len(flow)}")
if len(flow) > 0:
    print("\n最初の5件:")
    print(flow[['municipality', 'inflow', 'outflow', 'net_flow']].head())

    # 流入ランキング
    print("\n流入ランキング Top 5:")
    inflow_ranking = flow.sort_values('inflow', ascending=False).head(5)
    print(inflow_ranking[['municipality', 'inflow']])

# 群馬県のGAPデータ確認
print("\n=== 群馬県GAPデータ ===")
gap = df[
    (df['row_type'] == 'GAP') &
    (df['prefecture'] == '群馬県') &
    (df['municipality'].notna()) &
    (df['gap'] > 0)
].copy()
print(f"GAP shortage件数: {len(gap)}")
if len(gap) > 0:
    print("\n需要超過ランキング Top 5:")
    shortage_ranking = gap.sort_values('gap', ascending=False).head(5)
    print(shortage_ranking[['municipality', 'gap']])

# 群馬県のRARITYデータ確認
print("\n=== 群馬県RARITYデータ ===")
rarity = df[
    (df['row_type'] == 'RARITY') &
    (df['prefecture'] == '群馬県')
].copy()
print(f"RARITY件数: {len(rarity)}")
if len(rarity) > 0:
    rarity_national = rarity[rarity['has_national_license'] == True]
    print(f"国家資格保有者: {len(rarity_national)}件")
    if len(rarity_national) > 0:
        print("\n国家資格保有者 Top 5:")
        ranking = rarity_national.sort_values('rarity_score', ascending=False).head(5)
        print(ranking[['category1', 'category2', 'category3', 'rarity_score']])

# 群馬県のCOMPETITIONデータ確認
print("\n=== 群馬県COMPETITIONデータ ===")
competition = df[
    (df['row_type'] == 'COMPETITION') &
    (df['prefecture'] == '群馬県')
].copy()
print(f"COMPETITION件数: {len(competition)}")
if len(competition) > 0:
    print("\n国家資格保有率 Top 5:")
    ranking = competition.sort_values('national_license_rate', ascending=False).head(5)
    print(ranking[['category1', 'category2', 'national_license_rate']])
