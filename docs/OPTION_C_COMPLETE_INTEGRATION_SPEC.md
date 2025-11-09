# オプションC: 完全統合 - 実装仕様書

**バージョン**: 1.0
**作成日**: 2025年10月28日
**目的**: データ品質フラグを全CSV出力とGAS可視化に完全統合する

---

## 1. 概要

### 1.1 実装目的

現状のv2.1システムでは、品質検証レポート（QualityReport_*.csv）が別ファイルとして出力されているが、以下の課題がある：

1. **AggDesired.csv**: 集計結果のみでサンプルサイズ・信頼性情報が欠落
2. **クロス集計CSV**: セル単位の品質警告が無い（5件未満のセルも警告なし）
3. **GAS統合**: 品質フラグを読み取らず、全データを同等に扱う

これにより、**小サンプルデータを誤って推論に使用するリスク**が残存している。

### 1.2 完全統合の定義

すべてのCSV出力に品質フラグを直接埋め込み、GAS側で自動的に視覚的警告を表示する仕組みを構築する。

**3つの統合レイヤー**:

1. **Layer 1: CSV Schema拡張** - 集計CSVに品質列を追加
2. **Layer 2: Python品質ロジック** - セル単位の品質判定を実装
3. **Layer 3: GAS可視化統合** - 色分け・警告表示を自動化

---

## 2. Layer 1: CSV Schema拡張

### 2.1 AggDesired.csv 拡張仕様

#### 現在のスキーマ
```csv
希望勤務地_都道府県,希望勤務地_市区町村,キー,カウント
京都府,京都市,京都府京都市,450
京都府,○○村,京都府○○村,1
```

#### 拡張後のスキーマ
```csv
希望勤務地_都道府県,希望勤務地_市区町村,キー,カウント,サンプルサイズ区分,信頼性レベル,警告メッセージ
京都府,京都市,京都府京都市,450,LARGE,HIGH,なし
京都府,○○村,京都府○○村,1,VERY_SMALL,CRITICAL,推論には使用不可（n=1 < 30）
```

#### 新規カラム定義

| カラム名 | データ型 | 説明 | 例 |
|---------|---------|------|-----|
| サンプルサイズ区分 | str | VERY_SMALL/SMALL/MEDIUM/LARGE | VERY_SMALL |
| 信頼性レベル | str | CRITICAL/LOW/MEDIUM/HIGH/EXCELLENT | CRITICAL |
| 警告メッセージ | str | 日本語の警告文（なし/参考データのみ/推論には使用不可） | 推論には使用不可（n=1 < 30） |

#### サンプルサイズ区分の閾値

| 区分 | 件数範囲 | 利用目的 | GAS表示色 |
|------|---------|---------|----------|
| VERY_SMALL | 1-9件 | 観察的記述のみ | 赤色 (#ff0000) |
| SMALL | 10-29件 | 参考データ（傾向分析は慎重に） | オレンジ色 (#ff9900) |
| MEDIUM | 30-99件 | 傾向分析可能（信頼区間に注意） | 黄色 (#ffcc00) |
| LARGE | 100件以上 | 統計的推論に十分 | 緑色 (#00cc00) |

#### 信頼性レベルの判定ロジック

```python
def get_reliability_level(count: int) -> str:
    if count >= 100:
        return 'HIGH'
    elif count >= 30:
        return 'MEDIUM'
    elif count >= 10:
        return 'LOW'
    else:
        return 'CRITICAL'
```

#### 警告メッセージのロジック

```python
def get_warning_message(count: int, mode: str = 'inferential') -> str:
    if mode == 'descriptive':
        return 'なし（観察的記述）'

    if count >= 30:
        return 'なし'
    elif count >= 10:
        return f'参考データのみ（n={count} < 30）'
    else:
        return f'推論には使用不可（n={count} < 30）'
```

### 2.2 クロス集計CSV 拡張仕様

#### 対象ファイル
- Phase 8: `CareerCrossTabs.csv`, `EducationCrossTabs.csv`
- Phase 10: `UrgencyCrossTabs.csv`

#### 現在のスキーマ例（EducationCrossTabs.csv）
```csv
education_level,age_group,カウント
高校,20代,45
高校,30代,12
専門,40代,3
```

#### 拡張後のスキーマ
```csv
education_level,age_group,カウント,セル品質,警告フラグ,警告メッセージ
高校,20代,45,SUFFICIENT,なし,なし
高校,30代,12,MARGINAL,要注意,セル数不足（n=12 < 30）
専門,40代,3,INSUFFICIENT,使用不可,セル数不足（n=3 < 5）
```

#### 新規カラム定義

| カラム名 | データ型 | 説明 | 例 |
|---------|---------|------|-----|
| セル品質 | str | INSUFFICIENT/MARGINAL/SUFFICIENT | MARGINAL |
| 警告フラグ | str | なし/要注意/使用不可 | 要注意 |
| 警告メッセージ | str | 日本語の警告文 | セル数不足（n=12 < 30） |

#### セル品質の閾値

| 品質レベル | 件数範囲 | 推論利用可否 | GAS表示 |
|-----------|---------|------------|---------|
| INSUFFICIENT | 0-4件 | 推論不可（χ²検定の前提崩壊） | 灰色 + 警告アイコン |
| MARGINAL | 5-29件 | 慎重な推論のみ（Fisherの正確確率検定推奨） | 黄色 + 警告アイコン |
| SUFFICIENT | 30件以上 | 統計的推論に十分 | 緑色（通常表示） |

#### クロス集計セル品質判定ロジック

```python
def get_cell_quality(cell_count: int) -> Dict[str, str]:
    if cell_count < 5:
        return {
            'セル品質': 'INSUFFICIENT',
            '警告フラグ': '使用不可',
            '警告メッセージ': f'セル数不足（n={cell_count} < 5）'
        }
    elif cell_count < 30:
        return {
            'セル品質': 'MARGINAL',
            '警告フラグ': '要注意',
            '警告メッセージ': f'セル数不足（n={cell_count} < 30）'
        }
    else:
        return {
            'セル品質': 'SUFFICIENT',
            '警告フラグ': 'なし',
            '警告メッセージ': 'なし'
        }
```

---

## 3. Layer 2: Python品質ロジック実装

### 3.1 DataQualityValidator 拡張

#### 新規メソッド: `add_quality_flags_to_aggregation()`

```python
def add_quality_flags_to_aggregation(
    self,
    df: pd.DataFrame,
    count_column: str = 'カウント',
    validation_mode: str = 'inferential'
) -> pd.DataFrame:
    """
    集計結果DataFrameに品質フラグを追加

    Args:
        df: 集計結果DataFrame
        count_column: カウント列名
        validation_mode: 'descriptive' or 'inferential'

    Returns:
        品質フラグが追加されたDataFrame
    """
    df_copy = df.copy()

    # サンプルサイズ区分
    df_copy['サンプルサイズ区分'] = df_copy[count_column].apply(
        lambda x: self._get_sample_size_category(x)
    )

    # 信頼性レベル
    df_copy['信頼性レベル'] = df_copy[count_column].apply(
        lambda x: self._get_reliability_level_from_count(x)
    )

    # 警告メッセージ
    df_copy['警告メッセージ'] = df_copy[count_column].apply(
        lambda x: self._get_warning_message(x, validation_mode)
    )

    return df_copy
```

#### 新規メソッド: `add_quality_flags_to_crosstab()`

```python
def add_quality_flags_to_crosstab(
    self,
    df: pd.DataFrame,
    count_column: str = 'カウント'
) -> pd.DataFrame:
    """
    クロス集計結果DataFrameにセル単位の品質フラグを追加

    Args:
        df: クロス集計結果DataFrame
        count_column: カウント列名

    Returns:
        セル品質フラグが追加されたDataFrame
    """
    df_copy = df.copy()

    # セル品質情報を取得
    cell_quality = df_copy[count_column].apply(
        lambda x: self._get_cell_quality(x)
    )

    # 品質列を追加
    df_copy['セル品質'] = cell_quality.apply(lambda x: x['セル品質'])
    df_copy['警告フラグ'] = cell_quality.apply(lambda x: x['警告フラグ'])
    df_copy['警告メッセージ'] = cell_quality.apply(lambda x: x['警告メッセージ'])

    return df_copy
```

### 3.2 run_complete_v2.py 修正箇所

#### Phase 1: export_phase1() 修正

```python
def export_phase1(self):
    # ... 既存の集計処理 ...

    # AggDesired.csvに品質フラグを追加
    agg_desired_with_quality = self.validator_descriptive.add_quality_flags_to_aggregation(
        agg_desired,
        count_column='カウント',
        validation_mode='descriptive'  # Phase 1は観察的記述
    )

    agg_desired_with_quality.to_csv(
        str(phase1_dir / "AggDesired.csv"),
        index=False,
        encoding='utf-8-sig'
    )
```

#### Phase 8: export_phase8() 修正

```python
def export_phase8(self):
    # ... 既存の集計処理 ...

    # クロス集計に品質フラグを追加
    career_cross_with_quality = self.validator_inferential.add_quality_flags_to_crosstab(
        career_cross,
        count_column='カウント'
    )

    career_cross_with_quality.to_csv(
        str(phase8_dir / "CareerCrossTabs.csv"),
        index=False,
        encoding='utf-8-sig'
    )
```

#### Phase 10: export_phase10() 修正

```python
def export_phase10(self):
    # ... 既存の集計処理 ...

    # クロス集計に品質フラグを追加
    urgency_cross_with_quality = self.validator_inferential.add_quality_flags_to_crosstab(
        urgency_cross,
        count_column='カウント'
    )

    urgency_cross_with_quality.to_csv(
        str(phase10_dir / "UrgencyCrossTabs.csv"),
        index=False,
        encoding='utf-8-sig'
    )
```

---

## 4. Layer 3: GAS可視化統合

### 4.1 GAS側の実装要件

#### 4.1.1 AggDesired.csv 可視化

**地図マーカーの色分け**:

```javascript
function getMarkerColor(sampleSizeCategory) {
  const colorMap = {
    'VERY_SMALL': '#ff0000',  // 赤色（1-9件）
    'SMALL': '#ff9900',       // オレンジ色（10-29件）
    'MEDIUM': '#ffcc00',      // 黄色（30-99件）
    'LARGE': '#00cc00'        // 緑色（100件以上）
  };
  return colorMap[sampleSizeCategory] || '#cccccc';
}

function createMarkerWithWarning(lat, lng, count, warning) {
  const color = getMarkerColor(getSampleSizeCategory(count));
  const marker = {
    lat: lat,
    lng: lng,
    color: color,
    title: warning !== 'なし' ? `${count}件（${warning}）` : `${count}件`
  };
  return marker;
}
```

**プルダウンの警告表示**:

```javascript
function createMunicipalityDropdown(aggDesiredData) {
  const options = aggDesiredData.map(row => {
    const display = row['警告メッセージ'] !== 'なし'
      ? `${row['希望勤務地_市区町村']}（${row['カウント']}件・${row['警告メッセージ']}）`
      : `${row['希望勤務地_市区町村']}（${row['カウント']}件）`;

    return {
      value: row['キー'],
      display: display,
      color: getMarkerColor(row['サンプルサイズ区分'])
    };
  });
  return options;
}
```

#### 4.1.2 クロス集計テーブル可視化

**セルの色分け**:

```javascript
function getCellBackgroundColor(cellQuality) {
  const colorMap = {
    'INSUFFICIENT': '#ffcccc',  // 薄い赤（0-4件）
    'MARGINAL': '#ffffcc',      // 薄い黄色（5-29件）
    'SUFFICIENT': '#ccffcc'     // 薄い緑（30件以上）
  };
  return colorMap[cellQuality] || '#ffffff';
}

function renderCrossTabTable(crossTabData) {
  const html = crossTabData.map(row => {
    const bgColor = getCellBackgroundColor(row['セル品質']);
    const warningIcon = row['警告フラグ'] !== 'なし' ? '⚠️' : '';

    return `
      <tr>
        <td>${row['education_level']}</td>
        <td>${row['age_group']}</td>
        <td style="background-color: ${bgColor}">
          ${row['カウント']} ${warningIcon}
        </td>
        <td>${row['警告メッセージ']}</td>
      </tr>
    `;
  }).join('');

  return `<table>${html}</table>`;
}
```

### 4.2 GAS実装ファイル一覧

| ファイル名 | 修正内容 | 優先度 |
|-----------|---------|--------|
| Code_Complete.gs | マーカー色分けロジック追加 | 高 |
| MenuIntegration.gs | 品質フラグ読み取り機能追加 | 高 |
| PersonaDifficultyChecker.gs | クロス集計セル警告表示 | 中 |
| PythonCSVImporter.gs | 品質列の自動認識 | 中 |

---

## 5. テスト計画

### 5.1 ユニットテスト（Python）

#### test_quality_flags_aggregation.py

```python
def test_add_quality_flags_to_aggregation():
    """AggDesired.csvへの品質フラグ追加をテスト"""
    validator = DataQualityValidator(validation_mode='inferential')

    test_df = pd.DataFrame({
        'キー': ['京都府京都市', '京都府○○村'],
        'カウント': [450, 1]
    })

    result = validator.add_quality_flags_to_aggregation(test_df)

    # 大サンプルの検証
    assert result.loc[0, 'サンプルサイズ区分'] == 'LARGE'
    assert result.loc[0, '信頼性レベル'] == 'HIGH'
    assert result.loc[0, '警告メッセージ'] == 'なし'

    # 小サンプルの検証
    assert result.loc[1, 'サンプルサイズ区分'] == 'VERY_SMALL'
    assert result.loc[1, '信頼性レベル'] == 'CRITICAL'
    assert '推論には使用不可' in result.loc[1, '警告メッセージ']
```

#### test_quality_flags_crosstab.py

```python
def test_add_quality_flags_to_crosstab():
    """クロス集計への品質フラグ追加をテスト"""
    validator = DataQualityValidator(validation_mode='inferential')

    test_df = pd.DataFrame({
        'education_level': ['高校', '高校', '専門'],
        'age_group': ['20代', '30代', '40代'],
        'カウント': [45, 12, 3]
    })

    result = validator.add_quality_flags_to_crosstab(test_df)

    # 十分なセル
    assert result.loc[0, 'セル品質'] == 'SUFFICIENT'
    assert result.loc[0, '警告フラグ'] == 'なし'

    # 限界的なセル
    assert result.loc[1, 'セル品質'] == 'MARGINAL'
    assert result.loc[1, '警告フラグ'] == '要注意'

    # 不十分なセル
    assert result.loc[2, 'セル品質'] == 'INSUFFICIENT'
    assert result.loc[2, '警告フラグ'] == '使用不可'
```

### 5.2 E2Eテスト（Python）

#### test_e2e_quality_integration.py

```python
def test_e2e_phase1_quality_flags():
    """Phase 1のE2Eテスト（品質フラグ付きCSV生成）"""
    csv_path = "test_data/results_test.csv"
    analyzer = JobMedleyAnalyzerV2(csv_path)
    analyzer.export_phase1()

    # AggDesired.csvを読み込み
    agg_desired = pd.read_csv("data/output_v2/phase1/AggDesired.csv")

    # 必須カラムの存在確認
    assert 'サンプルサイズ区分' in agg_desired.columns
    assert '信頼性レベル' in agg_desired.columns
    assert '警告メッセージ' in agg_desired.columns

    # 品質フラグの妥当性確認
    small_sample = agg_desired[agg_desired['カウント'] < 10]
    assert (small_sample['サンプルサイズ区分'] == 'VERY_SMALL').all()
    assert (small_sample['信頼性レベル'] == 'CRITICAL').all()
```

### 5.3 GASテスト（Node.js）

#### test_gas_quality_visualization.js

```javascript
function testMarkerColorMapping() {
  const testData = [
    { count: 500, expected: '#00cc00' },  // LARGE → green
    { count: 50, expected: '#ffcc00' },   // MEDIUM → yellow
    { count: 15, expected: '#ff9900' },   // SMALL → orange
    { count: 3, expected: '#ff0000' }     // VERY_SMALL → red
  ];

  testData.forEach(test => {
    const category = getSampleSizeCategory(test.count);
    const color = getMarkerColor(category);
    assert.equal(color, test.expected, `Count ${test.count} should be ${test.expected}`);
  });
}

function testCellQualityRendering() {
  const testRow = {
    'education_level': '高校',
    'age_group': '30代',
    'カウント': 3,
    'セル品質': 'INSUFFICIENT',
    '警告フラグ': '使用不可',
    '警告メッセージ': 'セル数不足（n=3 < 5）'
  };

  const html = renderCrossTabRow(testRow);

  assert.include(html, '#ffcccc', 'Should have red background');
  assert.include(html, '⚠️', 'Should have warning icon');
  assert.include(html, 'セル数不足', 'Should show warning message');
}
```

---

## 6. 実装スケジュール

### フェーズ1: Python実装（優先度: 高）

| タスク | 所要時間 | 担当 |
|-------|---------|------|
| DataQualityValidator拡張 | 2時間 | Claude |
| run_complete_v2.py修正 | 1時間 | Claude |
| ユニットテスト作成 | 1時間 | Claude |
| E2Eテスト実行 | 30分 | Claude |

**完了条件**:
- すべてのCSVに品質フラグが追加される
- ユニットテスト全パス
- E2Eテストで実際のCSVファイルが生成される

### フェーズ2: GAS実装（優先度: 中）

| タスク | 所要時間 | 担当 |
|-------|---------|------|
| マーカー色分けロジック実装 | 1時間 | Claude |
| クロス集計テーブル可視化 | 1時間 | Claude |
| プルダウン警告表示 | 30分 | Claude |
| GAS E2Eテスト | 1時間 | Claude |

**完了条件**:
- 地図マーカーが4色に色分けされる
- クロス集計テーブルにセル品質色分けが表示される
- プルダウンに警告メッセージが表示される

### フェーズ3: ドキュメント更新（優先度: 中）

| タスク | 所要時間 | 担当 |
|-------|---------|------|
| CLAUDE.md更新 | 30分 | Claude |
| README.md更新 | 30分 | Claude |
| DATA_USAGE_GUIDELINES.md更新 | 30分 | Claude |
| GAS統合ガイド作成 | 1時間 | Claude |

---

## 7. リスク管理

### 7.1 技術的リスク

| リスク | 影響度 | 対策 |
|-------|-------|------|
| CSV列数増加によるGAS処理遅延 | 中 | 列数を最小限に抑える（最大3列追加） |
| 既存GASコードとの非互換 | 高 | 後方互換性を保つ（品質列がなくても動作） |
| 品質フラグの誤判定 | 高 | 閾値を保守的に設定（30件基準を維持） |

### 7.2 運用リスク

| リスク | 影響度 | 対策 |
|-------|-------|------|
| ユーザーが警告を無視 | 中 | 視覚的に目立つ色分け（赤色使用） |
| 品質基準の理解不足 | 中 | DATA_USAGE_GUIDELINES.mdで明確化 |
| GAS側の実装漏れ | 高 | GASテストスイートで完全性を検証 |

---

## 8. 完了基準

### 8.1 Python側完了基準

- [ ] AggDesired.csvに3つの品質列が追加される
- [ ] すべてのクロス集計CSVに3つのセル品質列が追加される
- [ ] ユニットテスト10件全パス
- [ ] E2Eテスト3件全パス
- [ ] 実際のデータで全フェーズ実行成功

### 8.2 GAS側完了基準

- [ ] 地図マーカーが4色に色分けされる
- [ ] プルダウンに警告メッセージが表示される
- [ ] クロス集計テーブルにセル品質色分けが表示される
- [ ] GAS E2Eテスト5件全パス
- [ ] 既存機能に影響なし（後方互換性確認）

### 8.3 ドキュメント完了基準

- [ ] CLAUDE.mdにv2.2として記載
- [ ] README.mdに新機能を追加
- [ ] DATA_USAGE_GUIDELINES.mdにGAS可視化例を追加
- [ ] GAS統合ガイドを新規作成

---

## 9. 参考資料

### 9.1 関連ドキュメント

- [DATA_USAGE_GUIDELINES.md](DATA_USAGE_GUIDELINES.md) - データ利用ガイドライン
- [data_quality_validator.py](../python_scripts/data_quality_validator.py) - 品質検証クラス
- [run_complete_v2.py](../python_scripts/run_complete_v2.py) - 統合実行スクリプト

### 9.2 統計的根拠

- **30件基準**: 中心極限定理の適用下限（一般的な統計学の慣例）
- **5件基準**: χ²検定の期待度数下限（Cochranの基準）
- **100件基準**: 信頼区間±10%を達成する最小サンプル（母集団比率50%の場合）

---

## 10. 付録

### 10.1 サンプル出力例

#### AggDesired.csv（品質フラグ付き）

```csv
希望勤務地_都道府県,希望勤務地_市区町村,キー,カウント,サンプルサイズ区分,信頼性レベル,警告メッセージ
京都府,京都市,京都府京都市,450,LARGE,HIGH,なし
京都府,宇治市,京都府宇治市,85,MEDIUM,MEDIUM,なし
京都府,亀岡市,京都府亀岡市,22,SMALL,LOW,参考データのみ（n=22 < 30）
京都府,○○村,京都府○○村,1,VERY_SMALL,CRITICAL,推論には使用不可（n=1 < 30）
```

#### CareerCrossTabs.csv（セル品質フラグ付き）

```csv
education_level,age_group,カウント,セル品質,警告フラグ,警告メッセージ
高校,20代,45,SUFFICIENT,なし,なし
高校,30代,28,MARGINAL,要注意,セル数不足（n=28 < 30）
専門,40代,3,INSUFFICIENT,使用不可,セル数不足（n=3 < 5）
大学,50代,62,SUFFICIENT,なし,なし
```

### 10.2 GAS HTMLサンプル

```html
<!-- 品質フラグ付きプルダウン -->
<select id="municipality-select">
  <option value="京都府京都市" style="color: #00cc00">京都市（450件）</option>
  <option value="京都府亀岡市" style="color: #ff9900">亀岡市（22件・参考データのみ）</option>
  <option value="京都府○○村" style="color: #ff0000">○○村（1件・推論には使用不可）</option>
</select>

<!-- セル品質付きクロス集計テーブル -->
<table>
  <tr>
    <th>学歴</th>
    <th>年齢層</th>
    <th>件数</th>
    <th>警告</th>
  </tr>
  <tr>
    <td>高校</td>
    <td>20代</td>
    <td style="background-color: #ccffcc">45</td>
    <td>なし</td>
  </tr>
  <tr>
    <td>専門</td>
    <td>40代</td>
    <td style="background-color: #ffcccc">3 ⚠️</td>
    <td>セル数不足（n=3 < 5）</td>
  </tr>
</table>
```

---

**文書終了**

次のステップ: この仕様書に基づいてPython実装（フェーズ1）を開始します。
