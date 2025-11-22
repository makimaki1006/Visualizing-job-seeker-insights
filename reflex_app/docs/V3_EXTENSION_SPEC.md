# V3 CSV拡張仕様書

## 目的

元の生CSVから個別詳細データを抽出し、ユーザー要件を満たす分析を可能にする。

## ユーザー要件（抽象度高い要件）

**「どの地域にどのような人がいるのか」**

### 具体的な要件

1. **資格×年齢×性別分析**
   - どんな資格を持っている人がいるのか？
   - その人たちの年齢・性別分布は？

2. **学歴×年齢×性別分析**
   - どんな学歴を持っている人がいるのか？
   - その人たちの年齢・性別分布は？

3. **希望地域複数選択パターン分析**
   - プルダウンで選択した市町村を希望している人は、他にどんな市町村を希望しているのか？
   - その人たちの年齢・性別分布は？

4. **居住地→希望地移動パターン分析**
   - プルダウンで選択した市町村を希望している人は、どこに住んでいるのか？
   - その人たちの年齢・性別分布は？

5. **通勤距離許容度分析**
   - プルダウンで選択した市町村を希望している人は、どの程度の通勤距離を許容しているのか？
   - 年齢・性別ごとの差はあるのか？

---

## V3 CSV拡張設計

### 新規追加row_type（5種類）

#### 1. QUALIFICATION_DETAIL（資格詳細）

**目的**: 個別資格ごとの保有者データ

**カラム構成**:
```
row_type: "QUALIFICATION_DETAIL"
prefecture: 都道府県
municipality: 市町村
category1: 資格名（例: "介護福祉士"）
category2: 年齢層（例: "50代"）
category3: 性別（例: "女性"）
count: 人数
age_gender: 年齢×性別（例: "57歳 女性"）
qualifications_list: 全保有資格（カンマ区切り）
```

**データ生成ロジック**:
```python
# 元データのqualificationsカラムを分解
# "介護福祉士,喀痰吸引,普通自動車運転免許" → 3行生成
# - 介護福祉士
# - 喀痰吸引
# - 普通自動車運転免許
```

**想定行数**: 約15,000-30,000行（1人が平均2-3資格保有と仮定）

---

#### 2. EDUCATION_DETAIL（学歴詳細）

**目的**: 学歴種別ごとのデータ

**カラム構成**:
```
row_type: "EDUCATION_DETAIL"
prefecture: 都道府県
municipality: 市町村
category1: 学歴種別（例: "専門学校", "高校", "大学", "大学院"）
category2: 年齢層（例: "40代"）
category3: 性別（例: "女性"）
count: 人数
graduation_year: 卒業年（例: "2002"）
career_detail: 学歴詳細（例: "介護福祉専門学校(専門学校)(2002年3月卒業)"）
```

**データ生成ロジック**:
```python
# 元データのcareerカラムから学歴種別を抽出
# "(専門学校)" → "専門学校"
# "(高校)" → "高校"
# "(大学)" → "大学"
```

**想定行数**: 約8,000-12,000行

---

#### 3. DESIRED_AREA_PATTERN（希望地域パターン）

**目的**: 希望地域の組み合わせパターン分析

**カラム構成**:
```
row_type: "DESIRED_AREA_PATTERN"
prefecture: 都道府県
municipality: 選択中の市町村（例: "熊本市"）
category1: 併願市町村1（例: "荒尾市"）
category2: 年齢層（例: "50代"）
category3: 性別（例: "女性"）
count: 人数
desired_areas_count: 希望地域数（例: 3）
all_desired_areas: 全希望地域（カンマ区切り）
```

**データ生成ロジック**:
```python
# 選択中の市町村（municipalityフィルタ）を希望している人のみ抽出
# その人たちが他にどこを希望しているか集計
# "熊本市, 荒尾市, 玉名市" → "荒尾市", "玉名市"を併願市町村として記録
```

**想定行数**: 約20,000-40,000行

---

#### 4. RESIDENCE_FLOW（居住地→希望地フロー）

**目的**: 居住地から希望地への移動パターン

**カラム構成**:
```
row_type: "RESIDENCE_FLOW"
prefecture: 都道府県（希望地側）
municipality: 市町村（希望地側）
category1: 居住都道府県
category2: 居住市町村
category3: 年齢層
count: 人数
gender: 性別
residence_full: 居住地フル（例: "熊本県熊本市"）
distance_km: 移動距離（km）※後で計算
```

**データ生成ロジック**:
```python
# 選択中の市町村を希望している人の居住地を集計
# location（居住地）から都道府県と市町村を分解
# "熊本県熊本市" → prefecture="熊本県", municipality="熊本市"
```

**想定行数**: 約15,000-25,000行

---

#### 5. COMMUTE_TOLERANCE（通勤距離許容度）

**目的**: 居住地→希望地の距離による通勤許容度分析

**カラム構成**:
```
row_type: "COMMUTE_TOLERANCE"
prefecture: 都道府県（希望地側）
municipality: 市町村（希望地側）
category1: 距離帯（例: "0-10km", "10-20km", "20-50km", "50km以上"）
category2: 年齢層
category3: 性別
count: 人数
avg_distance_km: 平均距離
residence_municipality: 居住市町村
```

**データ生成ロジック**:
```python
# 居住地と希望地の緯度経度から距離を計算
# ※geocache.jsonから座標を取得
# 距離帯でグループ化して集計
```

**想定行数**: 約10,000-20,000行

---

## V3 CSV全体構成（拡張後）

### 既存row_type（8種類）
1. SUMMARY（944行）
2. AGE_GENDER（4,231行）
3. RARITY（4,950行）
4. URGENCY_AGE（2,942行）
5. URGENCY_EMPLOYMENT（1,666行）
6. GAP（966行）
7. FLOW（966行）
8. COMPETITION（966行）

**既存合計**: 17,631行

### 新規row_type（5種類）
9. QUALIFICATION_DETAIL（約20,000行）
10. EDUCATION_DETAIL（約10,000行）
11. DESIRED_AREA_PATTERN（約30,000行）
12. RESIDENCE_FLOW（約20,000行）
13. COMMUTE_TOLERANCE（約15,000行）

**新規合計**: 約95,000行

### 拡張後合計: 約112,000行

---

## カラム構成（拡張後）

### 既存カラム（36個）
- 変更なし

### 新規カラム候補（10個）
1. `age_gender`: 年齢×性別詳細（例: "57歳 女性"）
2. `qualifications_list`: 全保有資格リスト
3. `graduation_year`: 卒業年
4. `career_detail`: 学歴詳細
5. `desired_areas_count`: 希望地域数
6. `all_desired_areas`: 全希望地域リスト
7. `residence_full`: 居住地フル
8. `distance_km`: 移動距離
9. `avg_distance_km`: 平均移動距離
10. `residence_municipality`: 居住市町村

**拡張後カラム数**: 46カラム

---

## Reflexアプリ受け入れ準備

### 1. データロード対応

**現状**:
```python
# CSV読み込み時にrow_typeでフィルタ
df = df[df['row_type'].isin(['SUMMARY', 'AGE_GENDER', ...])]
```

**拡張後**:
```python
# 新規row_typeも受け入れ
VALID_ROW_TYPES = [
    'SUMMARY', 'AGE_GENDER', 'RARITY', 'URGENCY_AGE', 'URGENCY_EMPLOYMENT',
    'GAP', 'FLOW', 'COMPETITION',
    # 新規
    'QUALIFICATION_DETAIL', 'EDUCATION_DETAIL', 'DESIRED_AREA_PATTERN',
    'RESIDENCE_FLOW', 'COMMUTE_TOLERANCE'
]
df = df[df['row_type'].isin(VALID_ROW_TYPES)]
```

---

### 2. 新規タブ追加（5個）

#### タブ9: 📚 資格分析

**グラフ構成**:
1. 資格保有者ランキングTop 20（横棒グラフ）
   - データソース: `QUALIFICATION_DETAIL`
   - x軸: 人数、y軸: 資格名

2. 資格×年齢層クロス（グループ化棒グラフ）
   - データソース: `QUALIFICATION_DETAIL`
   - x軸: 資格名（Top 10）、y軸: 人数、グループ: 年齢層

3. 資格×性別クロス（積み上げ棒グラフ）
   - データソース: `QUALIFICATION_DETAIL`
   - x軸: 資格名（Top 10）、y軸: 人数、積み上げ: 性別

---

#### タブ10: 🎓 学歴分析

**グラフ構成**:
1. 学歴種別分布（円グラフ）
   - データソース: `EDUCATION_DETAIL`
   - 種別: 専門学校、高校、大学、大学院、その他

2. 学歴×年齢層クロス（ヒートマップ）
   - データソース: `EDUCATION_DETAIL`
   - x軸: 学歴種別、y軸: 年齢層、色: 人数

3. 卒業年分布（ヒストグラム）
   - データソース: `EDUCATION_DETAIL`
   - x軸: 卒業年、y軸: 人数

---

#### タブ11: 🗺️ 希望地域パターン

**グラフ構成**:
1. 併願市町村ランキングTop 20（横棒グラフ）
   - データソース: `DESIRED_AREA_PATTERN`
   - フィルタ: 選択中の市町村を希望している人の併願先
   - x軸: 人数、y軸: 併願市町村

2. 希望地域数分布（ヒストグラム）
   - データソース: `DESIRED_AREA_PATTERN`
   - x軸: 希望地域数（1個、2個、3個...）、y軸: 人数

3. 併願パターン×年齢層（グループ化棒グラフ）
   - データソース: `DESIRED_AREA_PATTERN`
   - x軸: 併願市町村（Top 10）、y軸: 人数、グループ: 年齢層

---

#### タブ12: 🏠 居住地フロー

**グラフ構成**:
1. 居住市町村ランキングTop 20（横棒グラフ）
   - データソース: `RESIDENCE_FLOW`
   - フィルタ: 選択中の市町村を希望している人の居住地
   - x軸: 人数、y軸: 居住市町村

2. 居住地→希望地Sankeyダイアグラム（Top 10）
   - データソース: `RESIDENCE_FLOW`
   - 左: 居住地、右: 希望地、太さ: 人数

3. 居住地×年齢層クロス（ヒートマップ）
   - データソース: `RESIDENCE_FLOW`
   - x軸: 居住市町村（Top 10）、y軸: 年齢層、色: 人数

---

#### タブ13: 🚗 通勤距離許容度

**グラフ構成**:
1. 距離帯別分布（横棒グラフ）
   - データソース: `COMMUTE_TOLERANCE`
   - x軸: 人数、y軸: 距離帯（0-10km、10-20km...）

2. 距離×年齢層クロス（グループ化棒グラフ）
   - データソース: `COMMUTE_TOLERANCE`
   - x軸: 距離帯、y軸: 人数、グループ: 年齢層

3. 距離×性別クロス（積み上げ棒グラフ）
   - データソース: `COMMUTE_TOLERANCE`
   - x軸: 距離帯、y軸: 人数、積み上げ: 性別

---

### 3. State変数拡張

**新規追加が必要な計算プロパティ（約15個）**:

```python
# タブ9: 資格分析
@rx.var(cache=False)
def qualification_ranking(self) -> List[Dict[str, Any]]:
    """資格保有者ランキングTop 20"""
    ...

@rx.var(cache=False)
def qualification_age_cross(self) -> List[Dict[str, Any]]:
    """資格×年齢層クロス"""
    ...

# タブ10: 学歴分析
@rx.var(cache=False)
def education_distribution(self) -> List[Dict[str, Any]]:
    """学歴種別分布"""
    ...

# タブ11: 希望地域パターン
@rx.var(cache=False)
def desired_area_pattern_ranking(self) -> List[Dict[str, Any]]:
    """併願市町村ランキング"""
    ...

# タブ12: 居住地フロー
@rx.var(cache=False)
def residence_flow_ranking(self) -> List[Dict[str, Any]]:
    """居住市町村ランキング"""
    ...

# タブ13: 通勤距離許容度
@rx.var(cache=False)
def commute_distance_distribution(self) -> List[Dict[str, Any]]:
    """距離帯別分布"""
    ...
```

---

## 実装順序

### Step 1: Python側V3拡張（1-2日）

1. `run_complete_v2_perfect.py`を拡張
2. 5種類の新規row_type生成ロジック実装
3. 距離計算機能実装（geocache.json活用）
4. テスト実行・検証

### Step 2: Reflexアプリ基盤準備（半日）

1. VALID_ROW_TYPES拡張
2. CSVアップロード対応
3. データロード確認

### Step 3: 新規タブ実装（2-3日）

1. タブ9: 資格分析（半日）
2. タブ10: 学歴分析（半日）
3. タブ11: 希望地域パターン（半日）
4. タブ12: 居住地フロー（1日・Sankey実装含む）
5. タブ13: 通勤距離許容度（半日）

### Step 4: E2Eテスト・検証（半日）

**合計工数**: 4-6日

---

## 懸念点とリスク

### 1. データ量増加（17,631行 → 112,000行）

**対策**:
- Reflexのキャッシュ機能活用
- 必要に応じてページネーション実装
- フィルタリングを徹底（都道府県・市町村で絞り込み）

### 2. 距離計算の精度

**対策**:
- geocache.jsonに座標がない市町村は距離計算不可
- その場合は"距離不明"として扱う

### 3. カラム数増加（36 → 46）

**対策**:
- 新規カラムは新規row_typeでのみ使用
- 既存row_typeには影響なし

---

## 次のステップ

このV3拡張仕様で進めてよろしいでしょうか？

承認いただければ、すぐにStep 1（Python側V3拡張）から実装を開始します。
