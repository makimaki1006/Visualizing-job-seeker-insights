# オプションC: 完全統合 - 実装サマリー

**実装日**: 2025年10月28日
**バージョン**: v2.2
**ステータス**: Python実装完了 ✅ / GAS実装待機中

---

## 実装概要

データ品質フラグをすべてのCSV出力に直接埋め込み、GAS側で自動的に視覚的警告を表示する仕組みを構築しました。

### 完了した実装レイヤー

✅ **Layer 1: CSV Schema拡張** - 集計CSVに品質列を追加
✅ **Layer 2: Python品質ロジック** - セル単位の品質判定を実装
⏳ **Layer 3: GAS可視化統合** - 色分け・警告表示を自動化（次のステップ）

---

## Layer 1 & 2: Python実装詳細

### 修正ファイル

#### 1. `data_quality_validator.py` (+168行)

**新規メソッド追加**:

```python
class DataQualityValidator:
    # ========================================
    # 6. 品質フラグ直接追加メソッド（オプションC対応）
    # ========================================

    def add_quality_flags_to_aggregation(
        self,
        df: pd.DataFrame,
        count_column: str = 'カウント',
        validation_mode: str = None
    ) -> pd.DataFrame:
        """
        集計結果DataFrameに品質フラグを追加

        追加カラム:
        - サンプルサイズ区分: VERY_SMALL/SMALL/MEDIUM/LARGE
        - 信頼性レベル: CRITICAL/LOW/MEDIUM/HIGH/DESCRIPTIVE
        - 警告メッセージ: 日本語の警告文
        """
        # 実装済み

    def add_quality_flags_to_crosstab(
        self,
        df: pd.DataFrame,
        count_column: str = 'カウント'
    ) -> pd.DataFrame:
        """
        クロス集計結果DataFrameにセル単位の品質フラグを追加

        追加カラム:
        - セル品質: INSUFFICIENT/MARGINAL/SUFFICIENT
        - 警告フラグ: なし/要注意/使用不可
        - 警告メッセージ: 日本語の警告文
        """
        # 実装済み
```

**ヘルパーメソッド**:
- `_get_sample_size_category(count)`: サンプルサイズ区分判定
- `_get_reliability_level_from_count(count, mode)`: 信頼性レベル判定
- `_get_warning_message_from_count(count, mode)`: 警告メッセージ生成
- `_get_cell_quality(cell_count)`: クロス集計セル品質判定

#### 2. `run_complete_v2.py` (修正3箇所)

**Phase 1: AggDesired.csv に品質フラグ追加**

```python
def export_phase1(self):
    # ... 既存の集計処理 ...

    # 品質フラグを追加（観察的記述モード）
    agg_desired_with_quality = self.validator_descriptive.add_quality_flags_to_aggregation(
        agg_desired,
        count_column='カウント',
        validation_mode='descriptive'
    )

    agg_desired_with_quality.to_csv(
        phase1_dir / "AggDesired.csv",
        index=False,
        encoding='utf-8-sig'
    )
    print(f"[OK] AggDesired.csv: {len(agg_desired_with_quality)}件（品質フラグ付き）")
```

**Phase 10: UrgencyAgeCross.csv, UrgencyEmploymentCross.csv に品質フラグ追加**

```python
def export_phase10(self):
    # クロス集計（マトリックス形式）
    urgency_age_cross_matrix = pd.crosstab(...)
    urgency_age_cross_matrix.to_csv(phase10_dir / "UrgencyAgeCross_Matrix.csv")

    # ロング形式に変換して品質フラグ追加
    urgency_age_cross_long = pd.crosstab(...).stack().reset_index(name='カウント')
    urgency_age_cross_long.columns = ['年齢層', 'urgency_score', 'カウント']

    # 品質フラグ追加
    urgency_age_cross_with_quality = self.validator_inferential.add_quality_flags_to_crosstab(
        urgency_age_cross_long,
        count_column='カウント'
    )

    urgency_age_cross_with_quality.to_csv(
        phase10_dir / "UrgencyAgeCross.csv",
        index=False,
        encoding='utf-8-sig'
    )
```

**Phase 8: EducationAgeCross.csv に品質フラグ追加**

同様の実装パターンでPhase 8のクロス集計にも品質フラグを追加済み。

---

## CSV出力スキーマ

### AggDesired.csv（Phase 1）

| カラム名 | 例 | 説明 |
|---------|-----|------|
| 希望勤務地_都道府県 | 京都府 | 都道府県名 |
| 希望勤務地_市区町村 | 京都市 | 市区町村名 |
| キー | 京都府京都市 | 都道府県+市区町村 |
| カウント | 450 | 希望者数 |
| **サンプルサイズ区分** | **LARGE** | **VERY_SMALL/SMALL/MEDIUM/LARGE** |
| **信頼性レベル** | **DESCRIPTIVE** | **DESCRIPTIVE/NO_DATA** |
| **警告メッセージ** | **なし（観察的記述）** | **日本語の警告文** |

**実際の出力例**:
```csv
希望勤務地_都道府県,希望勤務地_市区町村,キー,カウント,サンプルサイズ区分,信頼性レベル,警告メッセージ
京都府,京都市伏見区,京都府京都市伏見区,1748,LARGE,DESCRIPTIVE,なし（観察的記述）
京都府,○○村,京都府○○村,1,VERY_SMALL,DESCRIPTIVE,なし（観察的記述）
```

### クロス集計CSV（Phase 8, 10）

| カラム名 | 例 | 説明 |
|---------|-----|------|
| education_level | 高校 | 学歴レベル |
| 年齢層 | 20代 | 年齢層 |
| カウント | 45 | セル内件数 |
| **セル品質** | **SUFFICIENT** | **INSUFFICIENT/MARGINAL/SUFFICIENT** |
| **警告フラグ** | **なし** | **なし/要注意/使用不可** |
| **警告メッセージ** | **なし** | **日本語の警告文** |

**実際の出力例**:
```csv
education_level,年齢層,カウント,セル品質,警告フラグ,警告メッセージ
高校,20代,45,SUFFICIENT,なし,なし
高校,30代,12,MARGINAL,要注意,セル数不足（n=12 < 30）
専門,40代,3,INSUFFICIENT,使用不可,セル数不足（n=3 < 5）
```

---

## 品質フラグ判定ロジック

### サンプルサイズ区分（集計データ）

| 区分 | 件数範囲 | 利用目的 | GAS表示色（予定） |
|------|---------|---------|------------------|
| VERY_SMALL | 1-9件 | 観察的記述のみ | 赤色 (#ff0000) |
| SMALL | 10-29件 | 参考データ（傾向分析は慎重に） | オレンジ色 (#ff9900) |
| MEDIUM | 30-99件 | 傾向分析可能（信頼区間に注意） | 黄色 (#ffcc00) |
| LARGE | 100件以上 | 統計的推論に十分 | 緑色 (#00cc00) |

### 信頼性レベル（観察的記述モード）

| レベル | 条件 | 意味 |
|--------|------|------|
| DESCRIPTIVE | count > 0 | データ存在確認のみ |
| NO_DATA | count == 0 | データなし |

### 信頼性レベル（推論的考察モード）

| レベル | 条件 | 意味 |
|--------|------|------|
| HIGH | count ≥ 100 | 統計的推論に十分 |
| MEDIUM | 30 ≤ count < 100 | 傾向分析可能 |
| LOW | 10 ≤ count < 30 | 参考データのみ |
| CRITICAL | count < 10 | 推論には使用不可 |

### セル品質（クロス集計）

| 品質レベル | 件数範囲 | 推論利用可否 | GAS表示（予定） |
|-----------|---------|------------|----------------|
| INSUFFICIENT | 0-4件 | 推論不可（χ²検定の前提崩壊） | 灰色 + 警告アイコン |
| MARGINAL | 5-29件 | 慎重な推論のみ（Fisherの正確確率検定推奨） | 黄色 + 警告アイコン |
| SUFFICIENT | 30件以上 | 統計的推論に十分 | 緑色（通常表示） |

---

## テスト結果

### ユニットテスト（16テスト）

```
実行テスト数: 16
成功: 16
失敗: 0
エラー: 0

[OK] すべてのテストが成功しました！
```

**テスト内容**:
- ✅ 集計データへの品質フラグ追加（5テスト）
  - 大サンプル（n≥100）
  - 中サンプル（30≤n<100）
  - 小サンプル（10≤n<30）
  - 極小サンプル（n<10）
  - 観察的記述モード
- ✅ クロス集計への品質フラグ追加（4テスト）
  - 十分なセル（n≥30）
  - 限界的なセル（5≤n<30）
  - 不十分なセル（n<5）
  - 複数セルの一括処理
- ✅ サンプルサイズ区分判定（4テスト）
- ✅ セル品質判定（3テスト）

### E2Eテスト（実データ検証）

**テストデータ**: `results_20251027_180947.csv` (7,487行)

**出力ファイル検証**:

| ファイル名 | 件数 | 品質フラグ | 検証結果 |
|-----------|------|-----------|---------|
| AggDesired.csv | 898件 | サンプルサイズ区分、信頼性レベル、警告メッセージ | ✅ |
| UrgencyAgeCross.csv | 30件 | セル品質、警告フラグ、警告メッセージ | ✅ |
| UrgencyEmploymentCross.csv | 18件 | セル品質、警告フラグ、警告メッセージ | ✅ |
| EducationAgeCross.csv | 35件 | セル品質、警告フラグ、警告メッセージ | ✅ |

**品質フラグ動作確認**:

AggDesired.csv:
```csv
京都府,京都市伏見区,京都府京都市伏見区,1748,LARGE,DESCRIPTIVE,なし（観察的記述）
京都府,○○村,京都府○○村,1,VERY_SMALL,DESCRIPTIVE,なし（観察的記述）
```

EducationAgeCross.csv:
```csv
大学院,20代以下,2,INSUFFICIENT,使用不可,セル数不足（n=2 < 5）
大学院,30代,5,MARGINAL,要注意,セル数不足（n=5 < 30）
大学,20代,73,SUFFICIENT,なし,なし
```

---

## 次のステップ（Layer 3: GAS実装）

### GAS側実装要件

#### 1. AggDesired.csv 可視化

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
```

**プルダウンの警告表示**:
```javascript
function createMunicipalityDropdown(aggDesiredData) {
  const options = aggDesiredData.map(row => {
    const display = row['警告メッセージ'] !== 'なし（観察的記述）'
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

#### 2. クロス集計テーブル可視化

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
        <td>${row['年齢層']}</td>
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

### GAS実装優先度

| タスク | 所要時間 | 優先度 |
|-------|---------|--------|
| マーカー色分けロジック実装 | 1時間 | 高 |
| クロス集計テーブル可視化 | 1時間 | 高 |
| プルダウン警告表示 | 30分 | 中 |
| GAS E2Eテスト | 1時間 | 中 |

---

## 統計的根拠

### サンプルサイズ閾値の理論的背景

- **30件基準**: 中心極限定理の適用下限（一般的な統計学の慣例）
- **5件基準**: χ²検定の期待度数下限（Cochranの基準）
- **100件基準**: 信頼区間±10%を達成する最小サンプル（母集団比率50%の場合）

### 品質区分の定義

| 区分 | 信頼区間（95%） | 推定誤差 | 利用可否 |
|------|----------------|---------|---------|
| LARGE (n≥100) | ±9.8% | 小 | 統計的推論OK |
| MEDIUM (30≤n<100) | ±18.0% | 中 | 傾向分析のみ |
| SMALL (10≤n<30) | ±31.2% | 大 | 参考データのみ |
| VERY_SMALL (n<10) | ±62.0% | 極大 | 推論不可 |

※母集団比率50%、信頼水準95%の場合の近似値

---

## まとめ

### 完了したタスク

✅ **Layer 1: CSV Schema拡張**
- AggDesired.csv に3つの品質列を追加
- クロス集計CSV に3つのセル品質列を追加

✅ **Layer 2: Python品質ロジック**
- `add_quality_flags_to_aggregation()` メソッド実装
- `add_quality_flags_to_crosstab()` メソッド実装
- サンプルサイズ区分判定ロジック
- セル品質判定ロジック
- ユニットテスト16件全パス
- E2Eテスト実データ検証済み

### 次のステップ

⏳ **Layer 3: GAS可視化統合**
- マーカー色分けロジック実装
- プルダウン警告表示実装
- クロス集計テーブル可視化実装
- GAS E2Eテスト実行

---

**文書終了**
