# データインポートルール

**最終更新**: 2025-12-27
**目的**: Tursoデータベースへのインポート時の重複・バグを防止するための公式ルール

---

## 1. 問題の背景

### 過去に発生した問題

| 日付 | 問題 | 原因 | 影響 |
|------|------|------|------|
| 2025-12 | Tursoに2倍のデータ (1,436,302行 vs 期待1,392,078行) | AUTOINCREMENT IDによる重複インポート | データ集計値が2倍に |
| 2025-12 | CSV自体の重複 (198,097行) | CSV生成スクリプトのバグ | WORKSTYLE_MOBILITYで59%重複 |

### 根本原因

1. **Tursoテーブル設計の問題**:
   ```sql
   CREATE TABLE job_seeker_data (
       id INTEGER PRIMARY KEY AUTOINCREMENT,  -- ← これが問題
       ...
   )
   ```
   - CSVに`id`カラムがないため、毎回新しいIDが生成される
   - `INSERT OR REPLACE`が機能しない（IDが常に新規）

2. **CSV生成スクリプトの問題**:
   - `WORKSTYLE_MOBILITY`で59.1%の完全重複行が発生
   - 原因: 生成ロジックのバグ（詳細は別途調査）

---

## 2. 正しいインポート手順

### ステップ1: CSVの重複除去（必須）

```python
import pandas as pd

# CSVを読み込み
df = pd.read_csv(csv_path, dtype=str, low_memory=False)
print(f"読み込み行数: {len(df):,}")

# 重複除去（全カラムが同一の行を削除）
df_dedup = df.drop_duplicates()
print(f"重複除去後: {len(df_dedup):,}")
print(f"削除行数: {len(df) - len(df_dedup):,}")

# 検証: row_type別の行数を確認
print(df_dedup.groupby('row_type').size())
```

### ステップ2: Tursoへのインポート前チェック

```python
# 現在のTurso行数を確認
current_count = execute_sql(url, token, 'SELECT COUNT(*) FROM job_seeker_data')
print(f"Turso現在行数: {current_count}")

# 既存データがある場合は確認を求める
if current_count > 0:
    print("⚠️ 既存データがあります。クリーンアップしますか？")
```

### ステップ3: インポート実行

```bash
# nicegui_appディレクトリで実行
cd C:\Users\fuji1\OneDrive\Pythonスクリプト保管\job_medley_project\nicegui_app
python turso_fast_import.py
```

### ステップ4: インポート後の検証（必須）

```python
# 検証クエリ
queries = [
    "SELECT COUNT(*) FROM job_seeker_data",
    "SELECT row_type, COUNT(*) as cnt FROM job_seeker_data GROUP BY row_type ORDER BY cnt DESC"
]

# 期待値と比較
expected_total = 1_193_981  # 重複除去後の総行数
```

---

## 3. row_type一覧と期待行数

### 重複除去後の期待値（2025-12-27時点）

| row_type | 期待行数 | 用途 | アプリで使用 |
|----------|----------|------|-------------|
| WORKSTYLE_MOBILITY | 135,422 | 雇用形態×移動距離 | ❌ (今後実装予定) |
| PREFECTURE_SUMMARY | 47 | 都道府県サマリー | ✅ |
| MUNICIPALITY_SUMMARY | 1,896 | 市区町村サマリー | ✅ |
| QUALIFICATION_PERSONA | 56,715 | 資格×ペルソナ | ✅ |
| QUALIFICATION_DETAIL | 23,006 | 資格詳細 | ✅ |
| URGENCY_DISTRIBUTION | 5,439 | 緊急度分布 | ✅ |
| URGENCY_AGE_CROSS | 27,116 | 緊急度×年齢 | ✅ |
| ... | ... | ... | ... |
| **合計** | **1,193,981** | - | - |

### 重複が多いrow_type（要注意）

| row_type | 元の行数 | 重複除去後 | 重複率 | 原因 |
|----------|----------|-----------|--------|------|
| WORKSTYLE_MOBILITY | 331,019 | 135,422 | 59.1% | CSV生成バグ |
| QUALIFICATION_DETAIL | 24,618 | 23,006 | 6.5% | CSV生成バグ |
| QUALIFICATION_PERSONA | 57,603 | 56,715 | 1.5% | CSV生成バグ |

---

## 4. 禁止事項

### ❌ 絶対にやってはいけないこと

1. **重複除去せずにインポート**
   ```python
   # ❌ これは禁止
   df = pd.read_csv(csv_path)
   insert_to_turso(df)  # 重複したままインポート
   ```

2. **検証なしでインポート完了と判断**
   ```python
   # ❌ これは禁止
   insert_to_turso(df)
   print("完了！")  # 検証していない
   ```

3. **既存データを確認せず追加インポート**
   ```python
   # ❌ これは禁止
   # Tursoに既にデータがあるのに追加インポート
   insert_to_turso(df)  # 重複が発生
   ```

---

## 5. トラブルシューティング

### 症状: Tursoの行数が期待値の2倍

**原因**: 同じCSVを2回インポートした
**解決**:
```sql
-- 全データ削除
DELETE FROM job_seeker_data;
-- 重複除去済みCSVを再インポート
```

### 症状: 特定のrow_typeだけ行数が多い

**原因**: CSV生成時に重複が発生している
**解決**:
1. CSVの重複を確認: `df[df.duplicated(keep=False)]`
2. CSV生成スクリプトのバグを修正
3. 重複除去してインポート

### 症状: アプリの集計値が2倍になる

**原因**: データベースに重複行がある
**確認方法**:
```sql
SELECT row_type, COUNT(*) as cnt
FROM job_seeker_data
GROUP BY row_type
ORDER BY cnt DESC;
```
**解決**: 期待値と比較し、差異があれば再インポート

---

## 6. チェックリスト

### インポート前

- [ ] CSVの総行数を確認した
- [ ] `df.drop_duplicates()`で重複除去した
- [ ] 重複除去後の行数が期待値と一致する
- [ ] Tursoの現在行数を確認した
- [ ] 既存データがある場合、クリーンアップを検討した

### インポート後

- [ ] Tursoの総行数が期待値と一致する
- [ ] row_type別の行数が期待値と一致する
- [ ] アプリで正しくデータが表示される
- [ ] 集計値が2倍になっていない

---

## 7. 関連ファイル

| ファイル | 役割 |
|----------|------|
| `turso_fast_import.py` | 高速インポートスクリプト |
| `db_helper.py` | データベースアクセス関数 |
| `MapComplete_Complete_All_FIXED.csv` | インポート元CSV |

---

## 8. 更新履歴

| 日付 | 変更内容 |
|------|----------|
| 2025-12-27 | 初版作成。重複問題の原因と防止策を文書化 |
