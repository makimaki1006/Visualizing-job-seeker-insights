# クロス集計・多重クロス集計拡張仕様

**作成日**: 2025年11月21日
**目的**: V2タブ構成に網羅的なクロス集計分析を追加

---

## 設計思想

### ベースデータ方式（推奨）

**原則**: 最も細かい粒度でデータを保持し、UI側で動的に集計

**メリット**:
- ✅ データ量が最小限（重複なし）
- ✅ 柔軟性が高い（任意のクロス集計が可能）
- ✅ 保守性が高い（1つのrow_typeから複数グラフ生成）
- ✅ パフォーマンスが良い（pandasのgroupbyは高速）

**実装例**:
```python
# ベースデータ（4次元）
QUALIFICATION_DETAIL: 資格×年齢×性別×就業状況

# UI側で動的集計（2次元）
qualification_age_cross = df.groupby(['qualification', 'age_group'])['count'].sum()
qualification_gender_cross = df.groupby(['qualification', 'gender'])['count'].sum()

# UI側で動的集計（3次元）
qualification_age_gender_cross = df.groupby(['qualification', 'age_group', 'gender'])['count'].sum()
```

---

## タブ2: 👥 人材属性（拡張版）

### セクション2-1: ペルソナ分析（既存）

**KPI**: 3個
**グラフ**: 5個
**使用row_type**: PERSONA_MUNI

### セクション2-2: 資格詳細分析（クロス集計拡張）

#### ベースデータ設計

**row_type**: QUALIFICATION_DETAIL（4次元）

**カラム構成**:
```csv
row_type,prefecture,municipality,qualification_name,is_national_license,age_group,gender,employment_status,count
```

**サンプルデータ**:
```csv
QUALIFICATION_DETAIL,京都府,京都市,介護福祉士,TRUE,30-34,女性,就業中,45
QUALIFICATION_DETAIL,京都府,京都市,介護福祉士,TRUE,30-34,女性,離職中,12
QUALIFICATION_DETAIL,京都府,京都市,介護福祉士,TRUE,30-34,男性,就業中,18
QUALIFICATION_DETAIL,京都府,京都市,介護福祉士,TRUE,35-39,女性,就業中,38
```

**推定行数**: 約3,000行

---

#### KPI（5個）

1. **資格種類数** - `len(df['qualification_name'].unique())`
2. **国家資格保有率** - `df[df['is_national_license']==True]['count'].sum() / df['count'].sum()`
3. **平均資格数** - `df.groupby('person_id')['qualification_name'].nunique().mean()`（要person_id）
4. **最多資格** - `df.groupby('qualification_name')['count'].sum().idxmax()`
5. **最多国家資格** - `df[df['is_national_license']==True].groupby('qualification_name')['count'].sum().idxmax()`

---

#### 基本クロス集計（2次元）- 6グラフ

##### グラフ2-2-1: 資格×年齢クロス（ヒートマップ）

**目的**: どの年齢層がどの資格を持っているか

**集計ロジック**:
```python
@rx.var(cache=False)
def qualification_age_cross(self) -> List[Dict]:
    df = self.df[(self.df['row_type'] == 'QUALIFICATION_DETAIL')]
    result = df.groupby(['qualification_name', 'age_group'])['count'].sum().reset_index()
    return result.to_dict('records')
```

**グラフ形式**: ヒートマップ（X軸: 年齢層、Y軸: 資格名、色: 人数）

**ビジネス価値**: 「若い世代は新資格を取得しているが、ベテランは古い資格のまま」などの傾向把握

---

##### グラフ2-2-2: 資格×性別クロス（棒グラフ）

**目的**: 資格ごとの性別比率

**集計ロジック**:
```python
@rx.var(cache=False)
def qualification_gender_cross(self) -> List[Dict]:
    df = self.df[(self.df['row_type'] == 'QUALIFICATION_DETAIL')]
    result = df.groupby(['qualification_name', 'gender'])['count'].sum().reset_index()
    return result.to_dict('records')
```

**グラフ形式**: グループ化棒グラフ（X軸: 資格名、Y軸: 人数、グループ: 性別）

**ビジネス価値**: 「介護福祉士は女性80%、理学療法士は男性60%」など性別偏りの把握

---

##### グラフ2-2-3: 資格×就業状況クロス（棒グラフ）

**目的**: 資格ごとの就業/離職状況

**集計ロジック**:
```python
@rx.var(cache=False)
def qualification_employment_cross(self) -> List[Dict]:
    df = self.df[(self.df['row_type'] == 'QUALIFICATION_DETAIL')]
    result = df.groupby(['qualification_name', 'employment_status'])['count'].sum().reset_index()
    return result.to_dict('records')
```

**グラフ形式**: 積み上げ棒グラフ（X軸: 資格名、Y軸: 人数、積み上げ: 就業状況）

**ビジネス価値**: 「看護師は就業中70%だが、介護福祉士は離職中が多い」など採用しやすさの把握

---

##### グラフ2-2-4: 資格別人数ランキングTOP20（棒グラフ）

**目的**: 最も多い資格の特定

**集計ロジック**:
```python
@rx.var(cache=False)
def qualification_ranking(self) -> List[Dict]:
    df = self.df[(self.df['row_type'] == 'QUALIFICATION_DETAIL')]
    result = df.groupby('qualification_name')['count'].sum().nlargest(20).reset_index()
    return result.to_dict('records')
```

**グラフ形式**: 横棒グラフ（X軸: 人数、Y軸: 資格名）

---

##### グラフ2-2-5: 国家資格TOP10（棒グラフ）

**目的**: 国家資格の人気ランキング

**集計ロジック**:
```python
@rx.var(cache=False)
def national_license_ranking(self) -> List[Dict]:
    df = self.df[(self.df['row_type'] == 'QUALIFICATION_DETAIL') & (self.df['is_national_license'] == True)]
    result = df.groupby('qualification_name')['count'].sum().nlargest(10).reset_index()
    return result.to_dict('records')
```

---

##### グラフ2-2-6: 資格保有分布（円グラフ）

**目的**: 国家資格 vs その他の割合

**集計ロジック**:
```python
@rx.var(cache=False)
def qualification_license_distribution(self) -> List[Dict]:
    df = self.df[(self.df['row_type'] == 'QUALIFICATION_DETAIL')]
    result = df.groupby('is_national_license')['count'].sum().reset_index()
    result['name'] = result['is_national_license'].map({True: '国家資格', False: 'その他資格'})
    return result.to_dict('records')
```

---

#### 多重クロス集計（3次元）- 4グラフ

##### グラフ2-2-7: 資格×年齢×性別クロス（3D棒グラフ）

**目的**: 資格ごとの年齢層・性別分布を同時把握

**集計ロジック**:
```python
@rx.var(cache=False)
def qualification_age_gender_cross(self) -> List[Dict]:
    df = self.df[(self.df['row_type'] == 'QUALIFICATION_DETAIL')]
    result = df.groupby(['qualification_name', 'age_group', 'gender'])['count'].sum().reset_index()
    return result.to_dict('records')
```

**グラフ形式**: グループ化棒グラフ（X軸: 年齢層、Y軸: 人数、グループ: 性別、ファセット: 資格TOP5）

**ビジネス価値**: 「介護福祉士の30代女性が最も多い」など、ピンポイントなターゲティング

---

##### グラフ2-2-8: 資格×年齢×就業状況クロス（ヒートマップ）

**目的**: 資格・年齢ごとの就業/離職状況

**集計ロジック**:
```python
@rx.var(cache=False)
def qualification_age_employment_cross(self) -> List[Dict]:
    df = self.df[(self.df['row_type'] == 'QUALIFICATION_DETAIL')]
    result = df.groupby(['qualification_name', 'age_group', 'employment_status'])['count'].sum().reset_index()
    return result.to_dict('records')
```

**グラフ形式**: ファセット付きヒートマップ（X軸: 年齢層、Y軸: 就業状況、ファセット: 資格TOP5）

**ビジネス価値**: 「20代の看護師は離職中が多く、狙い目」など採用戦略

---

##### グラフ2-2-9: 資格×性別×就業状況クロス（積み上げ棒グラフ）

**目的**: 資格・性別ごとの就業/離職比率

**集計ロジック**:
```python
@rx.var(cache=False)
def qualification_gender_employment_cross(self) -> List[Dict]:
    df = self.df[(self.df['row_type'] == 'QUALIFICATION_DETAIL')]
    result = df.groupby(['qualification_name', 'gender', 'employment_status'])['count'].sum().reset_index()
    return result.to_dict('records')
```

**グラフ形式**: グループ化積み上げ棒グラフ（X軸: 資格名、Y軸: 人数、グループ: 性別、積み上げ: 就業状況）

---

##### グラフ2-2-10: 資格×年齢×性別×就業状況クロス（4Dテーブル）

**目的**: 最も細かい粒度での全体把握

**集計ロジック**:
```python
@rx.var(cache=False)
def qualification_full_cross(self) -> List[Dict]:
    df = self.df[(self.df['row_type'] == 'QUALIFICATION_DETAIL')]
    result = df.groupby(['qualification_name', 'age_group', 'gender', 'employment_status'])['count'].sum().reset_index()
    return result.to_dict('records')
```

**グラフ形式**: データテーブル（ソート・フィルタ可能）

**ビジネス価値**: 詳細データのエクスポート、カスタム分析

---

**セクション2-2合計**: KPI 5個 + グラフ 10個 = **15要素**

---

### セクション2-3: 学歴詳細分析（クロス集計拡張）

#### ベースデータ設計

**row_type**: EDUCATION_DETAIL（4次元）

**カラム構成**:
```csv
row_type,prefecture,municipality,education_level,graduation_year,age_group,gender,count
```

**サンプルデータ**:
```csv
EDUCATION_DETAIL,京都府,京都市,大学卒,2015,25-29,女性,23
EDUCATION_DETAIL,京都府,京都市,大学卒,2015,25-29,男性,18
EDUCATION_DETAIL,京都府,京都市,専門学校卒,2018,20-24,女性,15
EDUCATION_DETAIL,京都府,京都市,高校卒,2010,30-34,男性,34
```

**推定行数**: 約2,000行

---

#### KPI（3個）

1. **最多学歴** - `df.groupby('education_level')['count'].sum().idxmax()`
2. **大卒以上割合** - `df[df['education_level'].isin(['大学卒', '大学院卒'])]['count'].sum() / df['count'].sum()`
3. **平均卒業年** - `df.groupby('person_id')['graduation_year'].mean().mean()`（要person_id）

---

#### 基本クロス集計（2次元）- 4グラフ

##### グラフ2-3-1: 学歴×年齢クロス（ヒートマップ）

**集計ロジック**:
```python
@rx.var(cache=False)
def education_age_cross(self) -> List[Dict]:
    df = self.df[(self.df['row_type'] == 'EDUCATION_DETAIL')]
    result = df.groupby(['education_level', 'age_group'])['count'].sum().reset_index()
    return result.to_dict('records')
```

**ビジネス価値**: 「若い世代ほど大卒が多い」などの世代間学歴差の把握

---

##### グラフ2-3-2: 学歴×性別クロス（棒グラフ）

**集計ロジック**:
```python
@rx.var(cache=False)
def education_gender_cross(self) -> List[Dict]:
    df = self.df[(self.df['row_type'] == 'EDUCATION_DETAIL')]
    result = df.groupby(['education_level', 'gender'])['count'].sum().reset_index()
    return result.to_dict('records')
```

**ビジネス価値**: 「男性の大卒比率60%、女性の専門学校卒比率70%」など性別学歴差

---

##### グラフ2-3-3: 学歴分布（円グラフ）

**集計ロジック**:
```python
@rx.var(cache=False)
def education_distribution(self) -> List[Dict]:
    df = self.df[(self.df['row_type'] == 'EDUCATION_DETAIL')]
    result = df.groupby('education_level')['count'].sum().reset_index()
    return result.to_dict('records')
```

---

##### グラフ2-3-4: 卒業年度分布（折れ線グラフ）

**集計ロジック**:
```python
@rx.var(cache=False)
def graduation_year_distribution(self) -> List[Dict]:
    df = self.df[(self.df['row_type'] == 'EDUCATION_DETAIL')]
    result = df.groupby('graduation_year')['count'].sum().reset_index()
    return result.to_dict('records')
```

**ビジネス価値**: 「2015年卒が最も多い」など採用ターゲット年代の特定

---

#### 多重クロス集計（3次元）- 4グラフ

##### グラフ2-3-5: 学歴×年齢×性別クロス（3D棒グラフ）

**集計ロジック**:
```python
@rx.var(cache=False)
def education_age_gender_cross(self) -> List[Dict]:
    df = self.df[(self.df['row_type'] == 'EDUCATION_DETAIL')]
    result = df.groupby(['education_level', 'age_group', 'gender'])['count'].sum().reset_index()
    return result.to_dict('records')
```

**グラフ形式**: グループ化棒グラフ（X軸: 年齢層、Y軸: 人数、グループ: 性別、ファセット: 学歴）

---

##### グラフ2-3-6: 学歴×卒業年×性別クロス（折れ線グラフ）

**集計ロジック**:
```python
@rx.var(cache=False)
def education_year_gender_cross(self) -> List[Dict]:
    df = self.df[(self.df['row_type'] == 'EDUCATION_DETAIL')]
    result = df.groupby(['education_level', 'graduation_year', 'gender'])['count'].sum().reset_index()
    return result.to_dict('records')
```

**グラフ形式**: 複数折れ線グラフ（X軸: 卒業年、Y軸: 人数、線: 性別、ファセット: 学歴）

**ビジネス価値**: 「2015年以降、女性の大卒が急増」などトレンド把握

---

##### グラフ2-3-7: 学歴×年齢×卒業年クロス（ヒートマップ）

**集計ロジック**:
```python
@rx.var(cache=False)
def education_age_year_cross(self) -> List[Dict]:
    df = self.df[(self.df['row_type'] == 'EDUCATION_DETAIL')]
    result = df.groupby(['education_level', 'age_group', 'graduation_year'])['count'].sum().reset_index()
    return result.to_dict('records')
```

**グラフ形式**: ファセット付きヒートマップ（X軸: 卒業年、Y軸: 年齢層、ファセット: 学歴）

**ビジネス価値**: 年齢・卒業年・学歴の整合性チェック

---

##### グラフ2-3-8: 学歴×年齢×性別×卒業年クロス（4Dテーブル）

**集計ロジック**:
```python
@rx.var(cache=False)
def education_full_cross(self) -> List[Dict]:
    df = self.df[(self.df['row_type'] == 'EDUCATION_DETAIL')]
    result = df.groupby(['education_level', 'age_group', 'gender', 'graduation_year'])['count'].sum().reset_index()
    return result.to_dict('records')
```

**グラフ形式**: データテーブル（エクスポート可能）

---

**セクション2-3合計**: KPI 3個 + グラフ 8個 = **11要素**

---

## タブ3: 🗺️ 地域・移動パターン（拡張版）

### セクション3-1: 複数希望地パターン（クロス集計拡張）

#### ベースデータ設計

**row_type**: DESIRED_AREA_PATTERN（4次元）

**カラム構成**:
```csv
row_type,prefecture,municipality,co_desired_municipality,age_group,gender,count
```

**サンプルデータ**:
```csv
DESIRED_AREA_PATTERN,京都府,京都市,大阪市,30-34,女性,67
DESIRED_AREA_PATTERN,京都府,京都市,神戸市,30-34,女性,45
DESIRED_AREA_PATTERN,京都府,京都市,大津市,35-39,女性,38
```

**推定行数**: 約2,000行

---

#### KPI（3個）

1. **平均希望地域数** - `df.groupby('person_id')['municipality'].nunique().mean()`（要person_id）
2. **複数希望率** - `df.groupby('person_id')['municipality'].nunique().gt(1).mean()`
3. **最多併願地** - `df.groupby('co_desired_municipality')['count'].sum().idxmax()`

---

#### 基本クロス集計（2次元）- 3グラフ

##### グラフ3-1-1: 併願TOP20市町村（棒グラフ）

**集計ロジック**:
```python
@rx.var(cache=False)
def co_desired_ranking(self) -> List[Dict]:
    df = self.df[(self.df['row_type'] == 'DESIRED_AREA_PATTERN')]
    result = df.groupby('co_desired_municipality')['count'].sum().nlargest(20).reset_index()
    return result.to_dict('records')
```

**ビジネス価値**: 「京都市希望者は大阪市も67人が併願」など競合地域の特定

---

##### グラフ3-1-2: 併願×年齢クロス（棒グラフ）

**集計ロジック**:
```python
@rx.var(cache=False)
def co_desired_age_cross(self) -> List[Dict]:
    df = self.df[(self.df['row_type'] == 'DESIRED_AREA_PATTERN')]
    result = df.groupby(['co_desired_municipality', 'age_group'])['count'].sum().reset_index()
    top_cities = df.groupby('co_desired_municipality')['count'].sum().nlargest(10).index
    result = result[result['co_desired_municipality'].isin(top_cities)]
    return result.to_dict('records')
```

**グラフ形式**: グループ化棒グラフ（X軸: 併願地、Y軸: 人数、グループ: 年齢層）

---

##### グラフ3-1-3: 併願×性別クロス（棒グラフ）

**集計ロジック**:
```python
@rx.var(cache=False)
def co_desired_gender_cross(self) -> List[Dict]:
    df = self.df[(self.df['row_type'] == 'DESIRED_AREA_PATTERN')]
    result = df.groupby(['co_desired_municipality', 'gender'])['count'].sum().reset_index()
    top_cities = df.groupby('co_desired_municipality')['count'].sum().nlargest(10).index
    result = result[result['co_desired_municipality'].isin(top_cities)]
    return result.to_dict('records')
```

---

#### 多重クロス集計（3次元）- 3グラフ

##### グラフ3-1-4: 併願パターンマトリクス（ヒートマップ）

**目的**: どの市町村とどの市町村が併願されやすいか

**集計ロジック**:
```python
@rx.var(cache=False)
def co_desired_pattern_matrix(self) -> List[Dict]:
    df = self.df[(self.df['row_type'] == 'DESIRED_AREA_PATTERN')]
    # 現在選択中の市町村を基準に、併願地との関係をマトリクス化
    result = df.groupby(['municipality', 'co_desired_municipality'])['count'].sum().reset_index()
    return result.to_dict('records')
```

**グラフ形式**: ヒートマップ（X軸: 希望地、Y軸: 併願地、色: 人数）

**ビジネス価値**: 「京都市希望者は大阪市と神戸市を併願する傾向」など地域クラスタの発見

---

##### グラフ3-1-5: 併願×年齢×性別クロス（3D棒グラフ）

**集計ロジック**:
```python
@rx.var(cache=False)
def co_desired_age_gender_cross(self) -> List[Dict]:
    df = self.df[(self.df['row_type'] == 'DESIRED_AREA_PATTERN')]
    result = df.groupby(['co_desired_municipality', 'age_group', 'gender'])['count'].sum().reset_index()
    top_cities = df.groupby('co_desired_municipality')['count'].sum().nlargest(5).index
    result = result[result['co_desired_municipality'].isin(top_cities)]
    return result.to_dict('records')
```

**グラフ形式**: グループ化棒グラフ（X軸: 年齢層、Y軸: 人数、グループ: 性別、ファセット: 併願地TOP5）

---

##### グラフ3-1-6: 併願地×年齢×性別×距離クロス（4Dテーブル）

**集計ロジック**:
```python
@rx.var(cache=False)
def co_desired_full_cross(self) -> List[Dict]:
    df = self.df[(self.df['row_type'] == 'DESIRED_AREA_PATTERN')]
    # 距離計算を追加（geocache.jsonから座標取得）
    result = df.groupby(['co_desired_municipality', 'age_group', 'gender'])['count'].sum().reset_index()
    return result.to_dict('records')
```

---

**セクション3-1合計**: KPI 3個 + グラフ 6個 = **9要素**

---

### セクション3-2: 居住地→希望地フロー（クロス集計拡張）

#### ベースデータ設計

**row_type**: RESIDENCE_FLOW（4次元）

**カラム構成**:
```csv
row_type,prefecture,municipality,residence_municipality,age_group,gender,count
```

**サンプルデータ**:
```csv
RESIDENCE_FLOW,京都府,京都市,大阪市,30-34,女性,89
RESIDENCE_FLOW,京都府,京都市,神戸市,30-34,女性,56
RESIDENCE_FLOW,京都府,京都市,京都市,30-34,女性,234
```

**推定行数**: 約2,500行

---

#### KPI（3個）

1. **流入TOP1市町村** - `df.groupby('residence_municipality')['count'].sum().idxmax()`
2. **流入率** - `df[df['residence_municipality'] != df['municipality']]['count'].sum() / df['count'].sum()`
3. **地元希望率** - `df[df['residence_municipality'] == df['municipality']]['count'].sum() / df['count'].sum()`

---

#### 基本クロス集計（2次元）- 4グラフ

##### グラフ3-2-1: 流入元TOP20（棒グラフ）

**集計ロジック**:
```python
@rx.var(cache=False)
def residence_inflow_ranking(self) -> List[Dict]:
    df = self.df[(self.df['row_type'] == 'RESIDENCE_FLOW')]
    result = df.groupby('residence_municipality')['count'].sum().nlargest(20).reset_index()
    return result.to_dict('records')
```

**ビジネス価値**: 「大阪市から89人、神戸市から56人が京都市を希望」など流入元の特定

---

##### グラフ3-2-2: 流入×年齢クロス（棒グラフ）

**集計ロジック**:
```python
@rx.var(cache=False)
def residence_inflow_age_cross(self) -> List[Dict]:
    df = self.df[(self.df['row_type'] == 'RESIDENCE_FLOW')]
    result = df.groupby(['residence_municipality', 'age_group'])['count'].sum().reset_index()
    top_cities = df.groupby('residence_municipality')['count'].sum().nlargest(10).index
    result = result[result['residence_municipality'].isin(top_cities)]
    return result.to_dict('records')
```

---

##### グラフ3-2-3: 流入×性別クロス（棒グラフ）

**集計ロジック**:
```python
@rx.var(cache=False)
def residence_inflow_gender_cross(self) -> List[Dict]:
    df = self.df[(self.df['row_type'] == 'RESIDENCE_FLOW')]
    result = df.groupby(['residence_municipality', 'gender'])['count'].sum().reset_index()
    top_cities = df.groupby('residence_municipality')['count'].sum().nlargest(10).index
    result = result[result['residence_municipality'].isin(top_cities)]
    return result.to_dict('records')
```

---

##### グラフ3-2-4: 地元 vs 流入比率（円グラフ）

**集計ロジック**:
```python
@rx.var(cache=False)
def residence_local_vs_inflow(self) -> List[Dict]:
    df = self.df[(self.df['row_type'] == 'RESIDENCE_FLOW')]
    df['is_local'] = df['residence_municipality'] == df['municipality']
    result = df.groupby('is_local')['count'].sum().reset_index()
    result['name'] = result['is_local'].map({True: '地元希望', False: '流入'})
    return result.to_dict('records')
```

**ビジネス価値**: 「地元希望60% vs 流入40%」など採用ターゲットの優先順位決定

---

#### 多重クロス集計（3次元）- 4グラフ

##### グラフ3-2-5: 流入元×希望地マトリクス（ヒートマップ）

**目的**: どの居住地からどの希望地へ流れているか

**集計ロジック**:
```python
@rx.var(cache=False)
def residence_flow_matrix(self) -> List[Dict]:
    df = self.df[(self.df['row_type'] == 'RESIDENCE_FLOW')]
    result = df.groupby(['residence_municipality', 'municipality'])['count'].sum().reset_index()
    return result.to_dict('records')
```

**グラフ形式**: ヒートマップ（X軸: 希望地、Y軸: 居住地、色: 人数）

**ビジネス価値**: 「大阪市在住者は京都市・神戸市を希望する傾向」など地域間フローの可視化

---

##### グラフ3-2-6: 流入×年齢×性別クロス（3D棒グラフ）

**集計ロジック**:
```python
@rx.var(cache=False)
def residence_inflow_age_gender_cross(self) -> List[Dict]:
    df = self.df[(self.df['row_type'] == 'RESIDENCE_FLOW')]
    result = df.groupby(['residence_municipality', 'age_group', 'gender'])['count'].sum().reset_index()
    top_cities = df.groupby('residence_municipality')['count'].sum().nlargest(5).index
    result = result[result['residence_municipality'].isin(top_cities)]
    return result.to_dict('records')
```

**グラフ形式**: グループ化棒グラフ（X軸: 年齢層、Y軸: 人数、グループ: 性別、ファセット: 居住地TOP5）

---

##### グラフ3-2-7: 距離帯×年齢×性別クロス（ヒートマップ）

**目的**: 居住地→希望地の距離と年齢・性別の関係

**集計ロジック**:
```python
@rx.var(cache=False)
def residence_distance_age_gender_cross(self) -> List[Dict]:
    df = self.df[(self.df['row_type'] == 'RESIDENCE_FLOW')]
    # 距離計算（geocache.jsonから座標取得）
    # 距離帯（0-10km, 10-20km, 20-50km, 50km以上）に分類
    result = df.groupby(['distance_range', 'age_group', 'gender'])['count'].sum().reset_index()
    return result.to_dict('records')
```

**グラフ形式**: ファセット付きヒートマップ（X軸: 年齢層、Y軸: 距離帯、ファセット: 性別）

**ビジネス価値**: 「若い世代は遠距離でも可、ベテランは近距離希望」など年齢別移動意欲の把握

---

##### グラフ3-2-8: 流入×年齢×性別×距離クロス（4Dテーブル）

**集計ロジック**:
```python
@rx.var(cache=False)
def residence_full_cross(self) -> List[Dict]:
    df = self.df[(self.df['row_type'] == 'RESIDENCE_FLOW')]
    # 距離計算追加
    result = df.groupby(['residence_municipality', 'age_group', 'gender', 'distance_range'])['count'].sum().reset_index()
    return result.to_dict('records')
```

---

**セクション3-2合計**: KPI 3個 + グラフ 8個 = **11要素**

---

### セクション3-3: 通勤距離許容度（クロス集計拡張）

#### ベースデータ設計

**row_type**: COMMUTE_TOLERANCE（4次元）

**カラム構成**:
```csv
row_type,prefecture,municipality,distance_range,age_group,gender,employment_status,count
```

**サンプルデータ**:
```csv
COMMUTE_TOLERANCE,京都府,京都市,0-5km,30-34,女性,就業中,45
COMMUTE_TOLERANCE,京都府,京都市,5-10km,30-34,女性,就業中,78
COMMUTE_TOLERANCE,京都府,京都市,10-20km,30-34,女性,就業中,56
COMMUTE_TOLERANCE,京都府,京都市,20km以上,30-34,女性,就業中,23
```

**推定行数**: 約2,000行

---

#### KPI（4個）

1. **平均許容距離** - `df.groupby('person_id')['distance'].mean().mean()`（要person_id、要distance）
2. **遠距離OK率（20km以上）** - `df[df['distance_range'] == '20km以上']['count'].sum() / df['count'].sum()`
3. **近距離希望率（5km以内）** - `df[df['distance_range'] == '0-5km']['count'].sum() / df['count'].sum()`
4. **最多距離帯** - `df.groupby('distance_range')['count'].sum().idxmax()`

---

#### 基本クロス集計（2次元）- 4グラフ

##### グラフ3-3-1: 許容距離分布（棒グラフ）

**集計ロジック**:
```python
@rx.var(cache=False)
def commute_distance_distribution(self) -> List[Dict]:
    df = self.df[(self.df['row_type'] == 'COMMUTE_TOLERANCE')]
    result = df.groupby('distance_range')['count'].sum().reset_index()
    return result.to_dict('records')
```

**ビジネス価値**: 「5-10kmが最多（45%）」など通勤範囲の把握

---

##### グラフ3-3-2: 許容距離×年齢クロス（ヒートマップ）

**集計ロジック**:
```python
@rx.var(cache=False)
def commute_distance_age_cross(self) -> List[Dict]:
    df = self.df[(self.df['row_type'] == 'COMMUTE_TOLERANCE')]
    result = df.groupby(['distance_range', 'age_group'])['count'].sum().reset_index()
    return result.to_dict('records')
```

**グラフ形式**: ヒートマップ（X軸: 年齢層、Y軸: 距離帯、色: 人数）

**ビジネス価値**: 「20代は遠距離OK、50代は近距離希望」など年齢別通勤意欲

---

##### グラフ3-3-3: 許容距離×性別クロス（棒グラフ）

**集計ロジック**:
```python
@rx.var(cache=False)
def commute_distance_gender_cross(self) -> List[Dict]:
    df = self.df[(self.df['row_type'] == 'COMMUTE_TOLERANCE')]
    result = df.groupby(['distance_range', 'gender'])['count'].sum().reset_index()
    return result.to_dict('records')
```

**グラフ形式**: グループ化棒グラフ（X軸: 距離帯、Y軸: 人数、グループ: 性別）

**ビジネス価値**: 「女性は近距離希望が多い（65%が10km以内）」など性別差の把握

---

##### グラフ3-3-4: 許容距離×就業状況クロス（棒グラフ）

**集計ロジック**:
```python
@rx.var(cache=False)
def commute_distance_employment_cross(self) -> List[Dict]:
    df = self.df[(self.df['row_type'] == 'COMMUTE_TOLERANCE')]
    result = df.groupby(['distance_range', 'employment_status'])['count'].sum().reset_index()
    return result.to_dict('records')
```

**ビジネス価値**: 「離職中の人は遠距離OKが多い（柔軟性高い）」など就業状況別通勤意欲

---

#### 多重クロス集計（3次元）- 4グラフ

##### グラフ3-3-5: 許容距離×年齢×性別クロス（3D棒グラフ）

**集計ロジック**:
```python
@rx.var(cache=False)
def commute_distance_age_gender_cross(self) -> List[Dict]:
    df = self.df[(self.df['row_type'] == 'COMMUTE_TOLERANCE')]
    result = df.groupby(['distance_range', 'age_group', 'gender'])['count'].sum().reset_index()
    return result.to_dict('records')
```

**グラフ形式**: グループ化棒グラフ（X軸: 年齢層、Y軸: 人数、グループ: 性別、ファセット: 距離帯）

**ビジネス価値**: 「30代女性の80%は10km以内希望」などピンポイントなターゲティング

---

##### グラフ3-3-6: 許容距離×年齢×就業状況クロス（ヒートマップ）

**集計ロジック**:
```python
@rx.var(cache=False)
def commute_distance_age_employment_cross(self) -> List[Dict]:
    df = self.df[(self.df['row_type'] == 'COMMUTE_TOLERANCE')]
    result = df.groupby(['distance_range', 'age_group', 'employment_status'])['count'].sum().reset_index()
    return result.to_dict('records')
```

**グラフ形式**: ファセット付きヒートマップ（X軸: 年齢層、Y軸: 距離帯、ファセット: 就業状況）

---

##### グラフ3-3-7: 許容距離×性別×就業状況クロス（積み上げ棒グラフ）

**集計ロジック**:
```python
@rx.var(cache=False)
def commute_distance_gender_employment_cross(self) -> List[Dict]:
    df = self.df[(self.df['row_type'] == 'COMMUTE_TOLERANCE')]
    result = df.groupby(['distance_range', 'gender', 'employment_status'])['count'].sum().reset_index()
    return result.to_dict('records')
```

**グラフ形式**: グループ化積み上げ棒グラフ（X軸: 距離帯、Y軸: 人数、グループ: 性別、積み上げ: 就業状況）

---

##### グラフ3-3-8: 許容距離×年齢×性別×就業状況クロス（4Dテーブル）

**集計ロジック**:
```python
@rx.var(cache=False)
def commute_full_cross(self) -> List[Dict]:
    df = self.df[(self.df['row_type'] == 'COMMUTE_TOLERANCE')]
    result = df.groupby(['distance_range', 'age_group', 'gender', 'employment_status'])['count'].sum().reset_index()
    return result.to_dict('records')
```

---

**セクション3-3合計**: KPI 4個 + グラフ 8個 = **12要素**

---

## 全体サマリー

### タブ構成（最終版）

#### タブ1: 📊 市場概況
- **KPI**: 4個
- **グラフ**: 3個
- **合計**: 7要素

#### タブ2: 👥 人材属性
- **セクション2-1（ペルソナ）**: KPI 3個 + グラフ 5個 = 8要素
- **セクション2-2（資格）**: KPI 5個 + グラフ 10個 = 15要素
- **セクション2-3（学歴）**: KPI 3個 + グラフ 8個 = 11要素
- **合計**: **34要素**

#### タブ3: 🗺️ 地域・移動パターン
- **セクション3-1（併願）**: KPI 3個 + グラフ 6個 = 9要素
- **セクション3-2（居住地フロー）**: KPI 3個 + グラフ 8個 = 11要素
- **セクション3-3（通勤距離）**: KPI 4個 + グラフ 8個 = 12要素
- **合計**: **32要素**

#### タブ4: ⚖️ 需給バランス
- **KPI**: 4個
- **グラフ**: 5個
- **合計**: 9要素

### 総計

```
総KPI数: 32個
総グラフ数: 50個
━━━━━━━━━━━━━━━━━━━━━━━━
総要素数: 82要素

タブ数: 4タブ
データ量: 20,141行（+14.2%増加）
```

---

## データ量詳細

### row_type別行数

| row_type | 行数 | 次元 | クロス集計対象 |
|----------|------|------|--------------|
| SUMMARY | 944 | 1D | - |
| AGE_GENDER | 4,231 | 2D | 年齢×性別 |
| GAP | 966 | 2D | 需要×供給 |
| PERSONA_MUNI | 2,500 | 4D | ペルソナ×市町村×年齢×性別 |
| QUALIFICATION_DETAIL | 3,000 | 4D | 資格×年齢×性別×就業状況 |
| EDUCATION_DETAIL | 2,000 | 4D | 学歴×年齢×性別×卒業年 |
| DESIRED_AREA_PATTERN | 2,000 | 4D | 希望地×併願地×年齢×性別 |
| RESIDENCE_FLOW | 2,500 | 4D | 居住地×希望地×年齢×性別 |
| COMMUTE_TOLERANCE | 2,000 | 4D | 通勤距離×年齢×性別×就業状況 |
| **合計** | **20,141** | - | - |

---

## 実装工数見積もり（更新）

### フェーズ1: データ生成

| タスク | 工数 |
|--------|------|
| PERSONA_MUNI生成 | 4時間 |
| QUALIFICATION_DETAIL生成 | 4時間 |
| EDUCATION_DETAIL生成 | 3時間 |
| DESIRED_AREA_PATTERN生成 | 4時間 |
| RESIDENCE_FLOW生成 | 4時間 |
| COMMUTE_TOLERANCE生成 | 3時間 |
| 不要なrow_type削除 | 2時間 |
| V3再生成・テスト | 2時間 |
| **合計** | **26時間（約3.5日）** |

### フェーズ2: UI実装

| タスク | 工数 |
|--------|------|
| タブ1実装 | 2時間 |
| タブ2-セクション2-1（ペルソナ） | 3時間 |
| タブ2-セクション2-2（資格、10グラフ） | 8時間 |
| タブ2-セクション2-3（学歴、8グラフ） | 6時間 |
| タブ3-セクション3-1（併願、6グラフ） | 5時間 |
| タブ3-セクション3-2（居住地、8グラフ） | 6時間 |
| タブ3-セクション3-3（通勤、8グラフ） | 6時間 |
| タブ4実装 | 0時間（既存） |
| メインページのタブ構成変更 | 1時間 |
| **合計** | **37時間（約4.5日）** |

### フェーズ3: テスト・品質保証

| タスク | 工数 |
|--------|------|
| ユニットテスト（50グラフ分） | 10時間 |
| E2Eテスト | 4時間 |
| ブラウザ実機テスト | 3時間 |
| Pylintチェック | 1時間 |
| **合計** | **18時間（約2日）** |

### 総合工数

```
フェーズ1: 26時間（3.5日）
フェーズ2: 37時間（4.5日）
フェーズ3: 18時間（2日）
━━━━━━━━━━━━━━━━━━━━━
合計: 81時間（約10日）

バッファ込み: 約13日
```

---

## 投資対効果

### 投資

- **工数**: 10-13日
- **データ量**: +14.2%増加（20,141行）

### 効果

- **グラフ数**: 7 → 50グラフ（+614%）
- **KPI数**: 4 → 32個（+700%）
- **総要素数**: 82要素
- **ユーザー要件対応**: 100%
- **クロス集計網羅性**:
  - 2次元クロス: 21グラフ
  - 3次元クロス: 20グラフ
  - 4次元クロス: 9グラフ（データテーブル）

### ROI評価

```
工数増加: +40時間（V2比+58%）
効果増加: グラフ+40個（V2比+400%）

ROI: 非常に高い
理由:
1. ユーザーのビジネスニーズに100%対応
2. あらゆる角度からの分析が可能
3. ベースデータ方式により保守性が高い
4. データ量増加は最小限
```

---

## 成功基準

### 定量的基準

1. **タブ数**: 7 → 4タブ ✅
2. **データ量**: +14.2%（2万行以下）✅
3. **グラフ数**: 50グラフ ✅
4. **クロス集計網羅性**: 2D/3D/4Dすべて対応 ✅
5. **テスト成功率**: 100%
6. **Pylintスコア**: 8.0以上

### 定性的基準

1. **ビジネス価値**: ユーザーの5つの質問すべてに多角的に回答
2. **柔軟性**: あらゆる組み合わせのクロス集計が可能
3. **保守性**: ベースデータから動的集計により、コード重複なし
4. **パフォーマンス**: pandasのgroupbyによる高速集計

---

## 次のステップ

### ステップ1: ユーザー確認

以下を確認：
- [ ] 4タブ構成に同意
- [ ] 82要素（KPI 32 + グラフ 50）の規模に同意
- [ ] クロス集計の網羅性（2D/3D/4D）が要件を満たすか
- [ ] 工数10-13日を承認
- [ ] データ量+14.2%増加を許容

### ステップ2: 元データ検証

**最優先**: 元CSVに必要なカラムがあるか確認

### ステップ3: 段階的実装

**フェーズ1-1**: PERSONA_MUNIデータ生成（最優先）
**フェーズ1-2**: QUALIFICATION_DETAIL生成
**フェーズ2-1**: タブ2-セクション2-2実装（資格10グラフ）
**フェーズ2-2**: 残りセクション実装

---

## まとめ

**クロス集計拡張の強み**:
- ✅ **網羅性**: 2次元、3次元、4次元すべてのクロス集計に対応
- ✅ **効率性**: ベースデータ方式により、データ量+14.2%で50グラフ実現
- ✅ **柔軟性**: UI側の動的集計により、将来の要件変更にも対応可能
- ✅ **ビジネス価値**: あらゆる角度から「どの地域にどのような人がいるのか」を分析

**推奨アクション**:
✅ **元データ検証を最優先で実施**（カラム存在確認）
✅ **承認後、段階的実装を開始**（タブ2-資格から着手）
