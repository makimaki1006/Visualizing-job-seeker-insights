# V3拡張実装仕様（最終版）

**作成日**: 2025年11月21日
**ステータス**: 実装開始

---

## 最終決定事項

### ユーザーフィードバック反映

1. ✅ **学歴詳細分析を削除** - 欠損率69.8%のため
2. ✅ **通勤距離を移動パターンに変更** - 市町村レベルの限界を考慮
3. ✅ **ジオコーディングは参考値として使用** - 市町村代表点間距離

---

## 新しいrow_type一覧

### 追加するrow_type（5個）

| row_type | 推定行数 | 目的 | 元データ |
|----------|----------|------|---------|
| **PERSONA_MUNI** | 2,500行 | ペルソナ×市町村分析 | Phase 3 PersonaSummaryByMunicipality.csv |
| **QUALIFICATION_DETAIL** | 3,000行 | 資格×年齢×性別×就業状況 | 元CSV qualifications列 |
| **DESIRED_AREA_PATTERN** | 2,000行 | 複数希望地パターン（併願分析） | 元CSV desired_area列（カンマ区切り） |
| **RESIDENCE_FLOW** | 2,500行 | 居住地→希望地フロー | 元CSV location + desired_area |
| **MOBILITY_PATTERN** | 2,000行 | 移動意欲分析（地元 vs 広域） | 元CSV location + desired_area |

### 削除するrow_type（5個）

| row_type | 現在行数 | 削除理由 |
|----------|----------|---------|
| RARITY | 4,950行 | 抽象的スコアリング、新資格分析と被る |
| URGENCY_AGE | 2,942行 | 計算根拠不明、ユーザー要件外 |
| URGENCY_EMPLOYMENT | 1,666行 | 計算根拠不明、ユーザー要件外 |
| FLOW | 966行 | UI未統合、完全未使用 |
| COMPETITION | 966行 | 薄い実装（1グラフのみ） |

---

## データ量変化

```
現在V3:   17,631行

削減:     -11,490行（5つのrow_type削除）
追加:     +12,000行（5つのrow_type追加）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
新V3:     18,141行（+2.9%増加）

効率性:   +5つの機能で+2.9%のみ
```

---

## 1. PERSONA_MUNI（ペルソナ×市町村）

### データ形式

```csv
row_type,prefecture,municipality,persona_category,age_group,gender,employment_status,count
PERSONA_MUNI,京都府,京都市,就業中×介護福祉士×30代,30-34,女性,就業中,67
PERSONA_MUNI,京都府,京都市,離職中×介護福祉士×40代,40-44,女性,離職中,23
```

### 元データ

- **Phase 3**: `PersonaSummaryByMunicipality.csv`
- **カラム**: persona, prefecture, municipality, count

### 生成ロジック

```python
def generate_persona_muni_rows(phase3_df):
    """
    Phase 3のPersonaSummaryByMunicipality.csvから
    PERSONA_MUNIデータを生成
    """
    rows = []
    for _, row in phase3_df.iterrows():
        # persona文字列から年齢・性別・就業状況を抽出
        persona = row['persona']
        # 例: "就業中×介護福祉士×30代×女性"
        parts = persona.split('×')

        employment_status = parts[0] if len(parts) > 0 else ''
        age_group = parts[2] if len(parts) > 2 else ''
        gender = parts[3] if len(parts) > 3 else ''

        rows.append({
            'row_type': 'PERSONA_MUNI',
            'prefecture': row['prefecture'],
            'municipality': row['municipality'],
            'persona_category': persona,
            'age_group': age_group,
            'gender': gender,
            'employment_status': employment_status,
            'count': row['count']
        })
    return rows
```

---

## 2. QUALIFICATION_DETAIL（資格詳細）

### データ形式

```csv
row_type,prefecture,municipality,qualification_name,is_national_license,age_group,gender,employment_status,count
QUALIFICATION_DETAIL,京都府,京都市,介護福祉士,TRUE,30-34,女性,就業中,45
QUALIFICATION_DETAIL,京都府,京都市,自動車運転免許,FALSE,30-34,女性,就業中,123
```

### 元データ

- **元CSV**: `qualifications`列（カンマ区切り）
- **例**: "介護福祉士,介護職員実務者研修,自動車運転免許"

### 生成ロジック

```python
def generate_qualification_detail_rows(source_df):
    """
    元CSVのqualifications列から
    QUALIFICATION_DETAILデータを生成
    """
    # 国家資格リスト
    national_licenses = [
        '介護福祉士', '看護師', '准看護師', '理学療法士', '作業療法士',
        '言語聴覚士', '社会福祉士', '精神保健福祉士', '管理栄養士', '栄養士'
    ]

    rows = []
    for _, person in source_df.iterrows():
        if pd.isna(person['qualifications']):
            continue

        # 年齢・性別を抽出
        age_gender = person['age_gender']  # "27歳 男性"
        match = re.match(r'(\d+)歳\s*(.+)', age_gender)
        if not match:
            continue

        age = int(match.group(1))
        gender = match.group(2)
        age_group = get_age_group(age)  # 30-34など

        # 資格をカンマ区切りで分割
        qualifications = [q.strip() for q in person['qualifications'].split(',')]

        # 市町村抽出
        prefecture, municipality = extract_prefecture_municipality(person['location'])

        for qual in qualifications:
            is_national = any(nl in qual for nl in national_licenses)

            rows.append({
                'row_type': 'QUALIFICATION_DETAIL',
                'prefecture': prefecture,
                'municipality': municipality,
                'qualification_name': qual,
                'is_national_license': is_national,
                'age_group': age_group,
                'gender': gender,
                'employment_status': person['employment_status'],
                'count': 1
            })

    # 集計（同じ組み合わせをまとめる）
    df = pd.DataFrame(rows)
    aggregated = df.groupby([
        'row_type', 'prefecture', 'municipality',
        'qualification_name', 'is_national_license',
        'age_group', 'gender', 'employment_status'
    ])['count'].sum().reset_index()

    return aggregated.to_dict('records')
```

---

## 3. DESIRED_AREA_PATTERN（併願パターン）

### データ形式

```csv
row_type,prefecture,municipality,co_desired_municipality,age_group,gender,count
DESIRED_AREA_PATTERN,京都府,京都市,大阪府大阪市,30-34,女性,67
DESIRED_AREA_PATTERN,京都府,京都市,兵庫県神戸市,30-34,女性,45
```

### 元データ

- **元CSV**: `desired_area`列（カンマ区切り）
- **例**: "奈良県奈良市,京都府木津川市,大阪府八尾市"

### 生成ロジック

```python
def generate_desired_area_pattern_rows(source_df):
    """
    元CSVのdesired_area列から
    DESIRED_AREA_PATTERNデータを生成
    """
    rows = []

    for _, person in source_df.iterrows():
        if pd.isna(person['desired_area']):
            continue

        # 年齢・性別を抽出
        age, gender, age_group = extract_age_gender(person['age_gender'])

        # 希望地をカンマ区切りで分割
        desired_areas = [a.strip() for a in person['desired_area'].split(',')]

        # 各希望地をペアで併願パターンとして記録
        for i, area1 in enumerate(desired_areas):
            for area2 in desired_areas[i+1:]:
                # area1を基準として、area2が併願地
                pref1, muni1 = extract_prefecture_municipality(area1)
                pref2, muni2 = extract_prefecture_municipality(area2)

                rows.append({
                    'row_type': 'DESIRED_AREA_PATTERN',
                    'prefecture': pref1,
                    'municipality': muni1,
                    'co_desired_municipality': f"{pref2}{muni2}",
                    'age_group': age_group,
                    'gender': gender,
                    'count': 1
                })

    # 集計
    df = pd.DataFrame(rows)
    aggregated = df.groupby([
        'row_type', 'prefecture', 'municipality',
        'co_desired_municipality', 'age_group', 'gender'
    ])['count'].sum().reset_index()

    return aggregated.to_dict('records')
```

---

## 4. RESIDENCE_FLOW（居住地→希望地フロー）

### データ形式

```csv
row_type,prefecture,municipality,residence_municipality,age_group,gender,count
RESIDENCE_FLOW,京都府,京都市,大阪府大阪市,30-34,女性,89
RESIDENCE_FLOW,京都府,京都市,京都府京都市,30-34,女性,234
```

### 元データ

- **元CSV**: `location`（居住地） + `desired_area`（希望地）

### 生成ロジック

```python
def generate_residence_flow_rows(source_df):
    """
    元CSVのlocation（居住地）とdesired_area（希望地）から
    RESIDENCE_FLOWデータを生成
    """
    rows = []

    for _, person in source_df.iterrows():
        if pd.isna(person['desired_area']) or pd.isna(person['location']):
            continue

        # 年齢・性別を抽出
        age, gender, age_group = extract_age_gender(person['age_gender'])

        # 居住地を抽出
        residence_pref, residence_muni = extract_prefecture_municipality(person['location'])

        # 希望地をカンマ区切りで分割
        desired_areas = [a.strip() for a in person['desired_area'].split(',')]

        for desired in desired_areas:
            desired_pref, desired_muni = extract_prefecture_municipality(desired)

            rows.append({
                'row_type': 'RESIDENCE_FLOW',
                'prefecture': desired_pref,
                'municipality': desired_muni,
                'residence_municipality': f"{residence_pref}{residence_muni}",
                'age_group': age_group,
                'gender': gender,
                'count': 1
            })

    # 集計
    df = pd.DataFrame(rows)
    aggregated = df.groupby([
        'row_type', 'prefecture', 'municipality',
        'residence_municipality', 'age_group', 'gender'
    ])['count'].sum().reset_index()

    return aggregated.to_dict('records')
```

---

## 5. MOBILITY_PATTERN（移動パターン）

### データ形式

```csv
row_type,prefecture,municipality,mobility_type,target_municipality,reference_distance,age_group,gender,employment_status,count
MOBILITY_PATTERN,京都府,京都市,地元希望,京都府京都市,0,30-34,女性,就業中,234
MOBILITY_PATTERN,京都府,京都市,近隣移動,大阪府大阪市,50,30-34,女性,就業中,89
MOBILITY_PATTERN,京都府,京都市,中距離移動,兵庫県神戸市,75,30-34,女性,就業中,23
MOBILITY_PATTERN,京都府,京都市,遠距離移動,東京都千代田区,400,30-34,女性,離職中,5
```

### 移動タイプ分類

| mobility_type | 条件 | ビジネス意味 |
|--------------|------|-------------|
| **地元希望** | 居住地 = 希望地 | 地元採用しやすい |
| **近隣移動** | 同一都道府県、距離<30km | 通勤圏内の人材 |
| **中距離移動** | 同一都道府県、距離30-80km | 県内人材流動 |
| **遠距離移動** | 異なる都道府県、距離>80km | UIターン人材 |

### 元データ

- **元CSV**: `location`（居住地） + `desired_area`（希望地）
- **geocache.json**: 市町村の座標データ（1,901件）

### 生成ロジック

```python
import math

def haversine_distance(coord1, coord2):
    """
    2つの座標間の距離をkm単位で計算（ヒュベニの公式）
    coord1, coord2: (latitude, longitude)
    """
    R = 6371  # 地球の半径（km）

    lat1, lon1 = math.radians(coord1[0]), math.radians(coord1[1])
    lat2, lon2 = math.radians(coord2[0]), math.radians(coord2[1])

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))

    return R * c

def classify_mobility_type(residence_muni, desired_muni, distance):
    """
    移動タイプを分類
    """
    # 同一市町村
    if residence_muni == desired_muni:
        return '地元希望'

    # 異なる都道府県
    residence_pref = residence_muni.split('県')[0] + '県' if '県' in residence_muni else residence_muni.split('府')[0] + '府'
    desired_pref = desired_muni.split('県')[0] + '県' if '県' in desired_muni else desired_muni.split('府')[0] + '府'

    if residence_pref != desired_pref:
        return '遠距離移動'

    # 同一都道府県内で距離による分類
    if distance < 30:
        return '近隣移動'
    elif distance < 80:
        return '中距離移動'
    else:
        return '遠距離移動'

def generate_mobility_pattern_rows(source_df, geocache):
    """
    元CSVのlocation（居住地）とdesired_area（希望地）から
    MOBILITY_PATTERNデータを生成
    """
    rows = []

    for _, person in source_df.iterrows():
        if pd.isna(person['desired_area']) or pd.isna(person['location']):
            continue

        # 年齢・性別を抽出
        age, gender, age_group = extract_age_gender(person['age_gender'])

        # 居住地を抽出
        residence_pref, residence_muni = extract_prefecture_municipality(person['location'])
        residence_full = f"{residence_pref}{residence_muni}"

        # 希望地をカンマ区切りで分割
        desired_areas = [a.strip() for a in person['desired_area'].split(',')]

        for desired in desired_areas:
            desired_pref, desired_muni = extract_prefecture_municipality(desired)
            desired_full = f"{desired_pref}{desired_muni}"

            # 距離を計算（geocache使用）
            distance = 0
            if residence_full in geocache and desired_full in geocache:
                coord1 = (geocache[residence_full]['lat'], geocache[residence_full]['lng'])
                coord2 = (geocache[desired_full]['lat'], geocache[desired_full]['lng'])
                distance = haversine_distance(coord1, coord2)

            # 移動タイプを分類
            mobility_type = classify_mobility_type(residence_full, desired_full, distance)

            rows.append({
                'row_type': 'MOBILITY_PATTERN',
                'prefecture': desired_pref,
                'municipality': desired_muni,
                'mobility_type': mobility_type,
                'target_municipality': desired_full,
                'reference_distance': round(distance, 1),
                'age_group': age_group,
                'gender': gender,
                'employment_status': person['employment_status'],
                'count': 1
            })

    # 集計
    df = pd.DataFrame(rows)
    aggregated = df.groupby([
        'row_type', 'prefecture', 'municipality',
        'mobility_type', 'target_municipality', 'reference_distance',
        'age_group', 'gender', 'employment_status'
    ])['count'].sum().reset_index()

    return aggregated.to_dict('records')
```

---

## ヘルパー関数

### 共通関数

```python
import re

def extract_prefecture_municipality(location):
    """
    "京都府京都市" → ("京都府", "京都市")
    "奈良県山辺郡山添村" → ("奈良県", "山添村")
    """
    # 都道府県を抽出
    pref_match = re.match(r'^(.+?県|.+?府|.+?都|.+?道)', location)
    if not pref_match:
        return ('不明', '不明')

    prefecture = pref_match.group(1)

    # 市区町村を抽出（都道府県を除いた部分）
    municipality_part = location[len(prefecture):]

    # 郡がある場合は除去
    if '郡' in municipality_part:
        parts = municipality_part.split('郡')
        municipality = parts[1] if len(parts) > 1 else municipality_part
    else:
        municipality = municipality_part

    return (prefecture, municipality)

def extract_age_gender(age_gender_str):
    """
    "27歳 男性" → (27, "男性", "25-29")
    """
    match = re.match(r'(\d+)歳\s*(.+)', age_gender_str)
    if not match:
        return (None, None, None)

    age = int(match.group(1))
    gender = match.group(2)
    age_group = get_age_group(age)

    return (age, gender, age_group)

def get_age_group(age):
    """
    年齢を年齢層に変換
    27歳 → "25-29"
    """
    if age < 20:
        return '〜19'
    elif age < 25:
        return '20-24'
    elif age < 30:
        return '25-29'
    elif age < 35:
        return '30-34'
    elif age < 40:
        return '35-39'
    elif age < 45:
        return '40-44'
    elif age < 50:
        return '45-49'
    elif age < 55:
        return '50-54'
    elif age < 60:
        return '55-59'
    elif age < 65:
        return '60-64'
    else:
        return '65〜'
```

---

## 実装スケジュール

### フェーズ1: データ生成（23時間、3日）

| タスク | 工数 | 完了条件 |
|--------|------|---------|
| 1-1. PERSONA_MUNI生成 | 4時間 | Phase 3データから2,500行生成 |
| 1-2. QUALIFICATION_DETAIL生成 | 4時間 | 元CSVから3,000行生成 |
| 1-3. DESIRED_AREA_PATTERN生成 | 4時間 | 元CSVから2,000行生成 |
| 1-4. RESIDENCE_FLOW生成 | 4時間 | 元CSVから2,500行生成 |
| 1-5. MOBILITY_PATTERN生成 | 3時間 | 元CSV+geocacheから2,000行生成 |
| 1-6. 不要なrow_type削除 | 2時間 | 5つのrow_type削除 |
| 1-7. V3再生成・検証 | 2時間 | 新V3 18,141行を確認 |

### フェーズ2: UI実装（31時間、4日）

後続タスク（詳細は別ドキュメント）

### フェーズ3: テスト（14時間、2日）

後続タスク（詳細は別ドキュメント）

---

## 成功基準

### フェーズ1完了の条件

1. ✅ 5つの新row_typeが生成されている
2. ✅ 合計行数が約12,000行（±10%）
3. ✅ 各row_typeのデータ品質チェック成功
4. ✅ 不要な5つのrow_typeが削除されている
5. ✅ 新V3のサイズが18,141行（±5%）
6. ✅ CSV形式が正しい（カラム数、エンコーディング）

---

## リスク対策

### リスク1: Phase 3データが存在しない

**対策**: Phase 3がない場合、PERSONA_MUNIはスキップ

### リスク2: geocache.jsonが不完全

**対策**: キャッシュにない市町村は距離0として記録、後で補完

### リスク3: データ量が想定より大きい

**対策**: Top N filtering（上位1000市町村のみ）

---

## 次のステップ

1. ✅ 仕様確定（本ドキュメント）
2. → V3生成スクリプトの実装開始
3. → データ生成実行
4. → データ品質検証
5. → UI実装へ進む
