# Tursoデータベース検証手順書

**作成日**: 2026-01-03
**目的**: データベースの完全性を検証するための標準手順

---

## 1. 検証の基本原則

### 1.1 唯一の正しい検証方法

```
元のCSVデータの都道府県 = データベースの都道府県
```

**これ以外の方法（row_type数の確認など）は不十分。**

### 1.2 検証対象

| 項目 | 期待値 |
|------|--------|
| 職種数 | 12 |
| 各職種の都道府県数 | 47 |
| 各職種のrow_type数 | 28 |

---

## 2. 検証手順

### Step 1: 元CSVデータの都道府県数を確認

```python
import pandas as pd
import glob
import os

downloads = r'C:\Users\fuji1\Downloads'
files = glob.glob(os.path.join(downloads, 'results_*.csv'))

for f in sorted(files):
    job_type = os.path.basename(f).replace('results_', '').replace('.csv', '')
    df = pd.read_csv(f, encoding='utf-8-sig', nrows=500000)
    prefs = df['prefecture'].dropna().unique()
    status = '✅' if len(prefs) == 47 else f'❌ ({47-len(prefs)}県不足)'
    print(f'{job_type}: {len(prefs)}/47 {status}')
```

### Step 2: Tursoデータベースの都道府県数を確認

```sql
-- 全職種のSUMMARY row_typeで都道府県数を確認
SELECT job_type, COUNT(DISTINCT prefecture) as pref_count
FROM job_seeker_data
WHERE row_type = 'SUMMARY'
GROUP BY job_type
ORDER BY job_type;
```

### Step 3: 元データとデータベースを比較

| 職種 | 元CSV | Turso SUMMARY | 判定 |
|------|-------|---------------|------|
| ケアマネジャー | 47 | 47 | ✅ |
| サービス提供責任者 | 47 | 47 | ✅ |
| ... | ... | ... | ... |

### Step 4: 不一致がある場合の詳細調査

```sql
-- 特定の職種で不足している都道府県を特定
SELECT DISTINCT prefecture
FROM job_seeker_data
WHERE job_type = '調理師、調理スタッフ' AND row_type = 'SUMMARY'
ORDER BY prefecture;
```

47都道府県リストと比較して、不足している都道府県を特定。

### Step 5: MapComplete CSVの確認

```python
import pandas as pd

csv_path = r'path\to\MapComplete_職種名.csv'
df = pd.read_csv(csv_path, encoding='utf-8-sig', low_memory=False)

# SUMMARYの都道府県数
summary = df[df['row_type'] == 'SUMMARY']
print(f'SUMMARY都道府県数: {len(summary["prefecture"].unique())}')
```

### Step 6: 問題がある場合の修正

1. 既存データを削除
   ```sql
   DELETE FROM job_seeker_data WHERE job_type = '職種名';
   ```

2. MapComplete CSVから再インポート
   ```bash
   python turso_job_type_import_optimized.py
   ```

3. Step 2-4を再実行して検証

---

## 3. 検証クエリ集

### 3.1 全職種サマリー

```sql
SELECT
    job_type,
    COUNT(DISTINCT prefecture) as pref_count,
    COUNT(DISTINCT row_type) as row_type_count,
    COUNT(*) as total_rows
FROM job_seeker_data
GROUP BY job_type
ORDER BY job_type;
```

### 3.2 row_type別都道府県数

```sql
SELECT
    job_type,
    row_type,
    COUNT(DISTINCT prefecture) as pref_count
FROM job_seeker_data
GROUP BY job_type, row_type
HAVING COUNT(DISTINCT prefecture) < 47
ORDER BY job_type, row_type;
```

### 3.3 特定都道府県のデータ確認

```sql
SELECT row_type, COUNT(*) as cnt
FROM job_seeker_data
WHERE job_type = '看護師' AND prefecture = '東京都'
GROUP BY row_type
ORDER BY row_type;
```

---

## 4. 47都道府県リスト

```python
all_47 = [
    '北海道', '青森県', '岩手県', '宮城県', '秋田県', '山形県', '福島県',
    '茨城県', '栃木県', '群馬県', '埼玉県', '千葉県', '東京都', '神奈川県',
    '新潟県', '富山県', '石川県', '福井県', '山梨県', '長野県', '岐阜県',
    '静岡県', '愛知県', '三重県', '滋賀県', '京都府', '大阪府', '兵庫県',
    '奈良県', '和歌山県', '鳥取県', '島根県', '岡山県', '広島県', '山口県',
    '徳島県', '香川県', '愛媛県', '高知県', '福岡県', '佐賀県', '長崎県',
    '熊本県', '大分県', '宮崎県', '鹿児島県', '沖縄県'
]
```

---

## 5. 12職種リスト

1. 介護職
2. 看護師
3. 保育士
4. 栄養士
5. 生活相談員
6. 理学療法士
7. 作業療法士
8. ケアマネジャー
9. サービス管理責任者
10. サービス提供責任者
11. 学童支援
12. 調理師、調理スタッフ

---

## 6. 28 row_typeリスト

| # | row_type | 用途 |
|---|----------|------|
| 1 | SUMMARY | 基本統計 |
| 2 | AGE_GENDER | 年齢×性別 |
| 3 | AGE_GENDER_RESIDENCE | 居住地年齢×性別 |
| 4 | PERSONA_MUNI | 市区町村ペルソナ |
| 5 | EMPLOYMENT_AGE_CROSS | 雇用形態×年齢 |
| 6 | URGENCY_AGE | 緊急度×年齢 |
| 7 | URGENCY_EMPLOYMENT | 緊急度×雇用形態 |
| 8 | URGENCY_GENDER | 緊急度×性別 |
| 9 | URGENCY_START_CATEGORY | 緊急度×開始時期 |
| 10 | FLOW | 人材フロー |
| 11 | GAP | 需給ギャップ |
| 12 | RARITY | 希少性スコア |
| 13 | COMPETITION | 競合分析 |
| 14 | QUALIFICATION_DETAIL | 資格詳細 |
| 15 | QUALIFICATION_PERSONA | 資格ペルソナ |
| 16 | DESIRED_AREA_PATTERN | 希望エリアパターン |
| 17 | RESIDENCE_FLOW | 居住地フロー |
| 18 | WORKSTYLE_DISTRIBUTION | 雇用形態分布 |
| 19 | WORKSTYLE_AGE_CROSS | 雇用形態×年齢 |
| 20 | WORKSTYLE_GENDER_CROSS | 雇用形態×性別 |
| 21 | WORKSTYLE_AGE_GENDER_CROSS | 雇用形態×年齢×性別 |
| 22 | WORKSTYLE_EMPLOYMENT_STATUS | 雇用形態×就業状況 |
| 23 | WORKSTYLE_QUALIFICATION | 雇用形態×資格 |
| 24 | WORKSTYLE_DESIRED_AREA_COUNT | 雇用形態×希望地域数 |
| 25 | WORKSTYLE_CAREER | 雇用形態×キャリア |
| 26 | WORKSTYLE_URGENCY | 雇用形態×緊急度 |
| 27 | WORKSTYLE_REGION | 雇用形態×地域 |
| 28 | WORKSTYLE_MOBILITY | 雇用形態×移動パターン |

---

## 7. 検証チェックリスト

### 完全性検証

- [ ] 12職種すべてが存在する
- [ ] 各職種が28 row_typeを持つ
- [ ] 各職種×各row_typeが47都道府県を持つ
- [ ] 元CSVの都道府県数とTursoの都道府県数が一致

### データ品質検証

- [ ] 空文字列やNULLの都道府県がない
- [ ] 表記揺れがない（「東京」vs「東京都」など）
- [ ] 重複IDがない

### 可視化動作検証

- [ ] 全職種で市場概況タブが表示される
- [ ] 全都道府県で需給バランスが計算される
- [ ] 人材地図で全エリアがレンダリングされる

---

## 8. 問題発生時の対応フロー

```
問題発見
    ↓
元CSVデータ確認（都道府県数）
    ↓
MapComplete CSV確認（都道府県数）
    ↓
[CSVに問題あり] → run_complete_v2_perfect.py再実行
[CSVは正常] → Tursoインポート問題
    ↓
既存データ削除 → 再インポート
    ↓
検証クエリで確認
    ↓
ダッシュボードで動作確認
```

---

## 9. 関連ファイル

| ファイル | パス | 用途 |
|----------|------|------|
| 元CSV | `C:\Users\fuji1\Downloads\results_*.csv` | スクレイピング結果 |
| MapComplete CSV | `python_scripts\data\output_v2\mapcomplete_complete_sheets\` | 加工済みデータ |
| インポートスクリプト | `nicegui_app\turso_job_type_import_optimized.py` | Tursoインポート |
| 環境変数 | `nicegui_app\.env` | Turso認証情報 |

---

## 10. 重要な教訓

1. **row_type数だけで安心しない**: row_typeが28あっても、各row_typeに47都道府県があるとは限らない

2. **元データとの比較が唯一の検証**: 「元のCSVデータの都道府県 = データベースの都道府県」これだけが正しい検証

3. **インポート時に欠落が発生しうる**: CSVが正しくてもインポート時にデータが欠落することがある

4. **表記揺れに注意**: 「東京」vs「東京都」などの表記揺れがあるとカウントがずれる
