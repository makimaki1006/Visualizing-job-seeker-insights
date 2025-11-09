# simple_analyzer.py のギャップ分析

**作成日**: 2025年10月29日
**目的**: `simple_analyzer.py`が新しい要件（output_v2フォルダ、Phase別ファイル名、品質レポート）に対応しているか検証

---

## 🔍 調査結果サマリー

### ❌ 不足している機能（重大）

| 項目 | 現状 | 必要 | 影響度 |
|------|------|------|--------|
| **出力先** | `gas_output_phase1/` など（旧形式） | `data/output_v2/phase1/` など（新形式） | 🔴 HIGH |
| **Phase別ファイル名** | なし（`QualityReport.csv`のような汎用名） | `P1_QualityReport.csv`など | 🔴 HIGH |
| **品質レポート生成** | なし | 全Phase必須 | 🔴 HIGH |
| **Phase 8実装** | なし | キャリア・学歴分析（6ファイル） | 🔴 HIGH |
| **Phase 10実装** | なし | 転職意欲・緊急度分析（10ファイル） | 🔴 HIGH |
| **data_normalizer統合** | なし | 表記ゆれ正規化 | 🟡 MEDIUM |
| **data_quality_validator統合** | なし | 品質検証システム | 🔴 HIGH |

---

## 📁 Phase別の詳細ギャップ

### Phase 1: 基礎集計

#### 現状の出力
```python
def export_phase1_data(self, output_dir='gas_output_phase1'):
    # ...
    output_path / 'MapMetrics.csv'
    output_path / 'Applicants.csv'
    output_path / 'DesiredWork.csv'
    output_path / 'AggDesired.csv'
```

**出力先**: `gas_output_phase1/`（❌ 旧形式）
**ファイル数**: 4ファイル

#### 必要な出力
```
data/output_v2/phase1/
├── Applicants.csv                     ✅ あり
├── DesiredWork.csv                    ✅ あり
├── AggDesired.csv                     ✅ あり
├── MapMetrics.csv                     ✅ あり
├── P1_QualityReport.csv               ❌ なし
└── P1_QualityReport_Descriptive.csv   ❌ なし
```

**不足**: 品質レポート2ファイル

---

### Phase 2: 統計分析

#### 現状の出力
```python
def export_phase2_data(self, output_dir='gas_output_phase2'):
    # ...
    output_path / 'ChiSquareTests.csv'
    output_path / 'ANOVATests.csv'
```

**出力先**: `gas_output_phase2/`（❌ 旧形式）
**ファイル数**: 2ファイル

#### 必要な出力
```
data/output_v2/phase2/
├── ChiSquareTests.csv                 ✅ あり
├── ANOVATests.csv                     ✅ あり
└── P2_QualityReport_Inferential.csv   ❌ なし
```

**不足**: 品質レポート1ファイル

---

### Phase 3: ペルソナ分析

#### 現状の出力
```python
def export_phase3_data(self, output_dir='gas_output_phase3'):
    # ...
    output_path / 'PersonaSummary.csv'
    output_path / 'PersonaDetails.csv'
```

**出力先**: `gas_output_phase3/`（❌ 旧形式）
**ファイル数**: 2ファイル

#### 必要な出力
```
data/output_v2/phase3/
├── PersonaSummary.csv                 ✅ あり
├── PersonaDetails.csv                 ✅ あり
└── P3_QualityReport_Inferential.csv   ❌ なし
```

**不足**: 品質レポート1ファイル

---

### Phase 6: フロー分析

#### 現状の出力
```python
def export_phase6_data(self, output_dir='gas_output_phase6'):
    # ...
    output_path / 'MunicipalityFlowEdges.csv'
    output_path / 'MunicipalityFlowNodes.csv'
    output_path / 'ProximityAnalysis.csv'
```

**出力先**: `gas_output_phase6/`（❌ 旧形式）
**ファイル数**: 3ファイル

#### 必要な出力
```
data/output_v2/phase6/
├── MunicipalityFlowEdges.csv          ✅ あり
├── MunicipalityFlowNodes.csv          ✅ あり
├── ProximityAnalysis.csv              ✅ あり
└── P6_QualityReport_Inferential.csv   ❌ なし
```

**不足**: 品質レポート1ファイル

---

### Phase 7: 高度分析

#### 現状の出力
```python
def export_phase7_data(self, output_dir='gas_output_phase7'):
    # ...
    output_path / 'SupplyDensity.csv'
    output_path / 'QualificationDistribution.csv'
    output_path / 'AgeGenderCross.csv'
    output_path / 'MobilityScore.csv'
    output_path / 'PersonaProfile.csv'
    output_path / 'PersonaMapData.csv'
    output_path / 'PersonaMobilityCross.csv'
```

**出力先**: `gas_output_phase7/`（❌ 旧形式）
**ファイル数**: 7ファイル

#### 必要な出力
```
data/output_v2/phase7/
├── SupplyDensityMap.csv               ⚠️ ファイル名違い（SupplyDensity.csv）
├── QualificationDistribution.csv      ✅ あり
├── AgeGenderCrossAnalysis.csv         ⚠️ ファイル名違い（AgeGenderCross.csv）
├── MobilityScore.csv                  ✅ あり
├── DetailedPersonaProfile.csv         ⚠️ ファイル名違い（PersonaProfile.csv）
└── P7_QualityReport_Inferential.csv   ❌ なし
```

**不足**:
- 品質レポート1ファイル
- ファイル名が3つ不一致

**余分**:
- `PersonaMapData.csv`（不要）
- `PersonaMobilityCross.csv`（不要）

---

### Phase 8: キャリア・学歴分析

#### 現状の出力
```
❌ Phase 8の実装なし
```

#### 必要な出力
```
data/output_v2/phase8/
├── EducationDistribution.csv
├── EducationAgeCross.csv
├── EducationAgeCross_Matrix.csv
├── GraduationYearDistribution.csv
├── P8_QualityReport.csv
└── P8_QualityReport_Inferential.csv
```

**不足**: Phase 8全体（6ファイル）

---

### Phase 10: 転職意欲・緊急度分析

#### 現状の出力
```
❌ Phase 10の実装なし
```

#### 必要な出力
```
data/output_v2/phase10/
├── UrgencyDistribution.csv
├── UrgencyDistribution_ByMunicipality.csv
├── UrgencyAgeCross.csv
├── UrgencyAgeCross_ByMunicipality.csv
├── UrgencyAgeCross_Matrix.csv
├── UrgencyEmploymentCross.csv
├── UrgencyEmploymentCross_ByMunicipality.csv
├── UrgencyEmploymentCross_Matrix.csv
├── P10_QualityReport.csv
└── P10_QualityReport_Inferential.csv
```

**不足**: Phase 10全体（10ファイル）

---

## 📊 ギャップサマリー

### ファイル数の比較

| Phase | 現状 | 必要 | 不足 | 余分 |
|-------|------|------|------|------|
| Phase 1 | 4 | 6 | -2 | 0 |
| Phase 2 | 2 | 3 | -1 | 0 |
| Phase 3 | 2 | 3 | -1 | 0 |
| Phase 6 | 3 | 4 | -1 | 0 |
| Phase 7 | 7 | 6 | -1 (+2余分) | 2 |
| Phase 8 | 0 | 6 | -6 | 0 |
| Phase 10 | 0 | 10 | -10 | 0 |
| **合計** | **18** | **38** | **-22** | **2** |

### 重大な問題点

#### 🔴 HIGH（即座に対応必須）

1. **出力先が旧形式**
   - 現状: `gas_output_phase1/` など
   - 必要: `data/output_v2/phase1/` など
   - 影響: GASインポーターが新しいフォルダ構造を前提としている

2. **品質レポートが未生成**
   - 全Phaseで品質レポートが欠落（12ファイル）
   - `data_quality_validator.py`の統合が必要

3. **Phase 8, 10が未実装**
   - 16ファイルが完全に欠落
   - 新規実装が必要

4. **Phase別ファイル名がない**
   - 品質レポートに `P{Phase}_` プレフィックスがない
   - ドラッグ&ドロップ時の識別不可

#### 🟡 MEDIUM（対応推奨）

5. **Phase 7のファイル名不一致**
   - `SupplyDensity.csv` → `SupplyDensityMap.csv`
   - `AgeGenderCross.csv` → `AgeGenderCrossAnalysis.csv`
   - `PersonaProfile.csv` → `DetailedPersonaProfile.csv`

6. **data_normalizer未統合**
   - 表記ゆれ正規化が行われない
   - データ品質に影響

7. **Phase 7の余分なファイル**
   - `PersonaMapData.csv`, `PersonaMobilityCross.csv` は不要

---

## 🔧 必要な修正内容

### 修正1: 出力先の変更

```python
# 修正前
def export_phase1_data(self, output_dir='gas_output_phase1'):

# 修正後
def export_phase1_data(self, output_dir='data/output_v2/phase1'):
```

**全Phaseで同様の修正が必要**

---

### 修正2: 品質レポート生成の追加

```python
def export_phase1_data(self, output_dir='data/output_v2/phase1'):
    # ... 既存のエクスポート処理 ...

    # 品質レポート生成（追加）
    from data_quality_validator import DataQualityValidator

    validator = DataQualityValidator(validation_mode='descriptive')
    report = validator.generate_quality_report(self.df)
    validator.save_quality_report(
        report,
        output_path / 'P1_QualityReport.csv',
        phase_prefix='P1'
    )

    validator_desc = DataQualityValidator(validation_mode='descriptive')
    report_desc = validator_desc.generate_quality_report(self.df)
    validator_desc.save_quality_report(
        report_desc,
        output_path / 'P1_QualityReport_Descriptive.csv',
        phase_prefix='P1'
    )
```

**全Phaseで同様の追加が必要**

---

### 修正3: Phase 7のファイル名修正

```python
# 修正前
supply_density_df.to_csv(output_path / 'SupplyDensity.csv', ...)
age_gender_cross_df.to_csv(output_path / 'AgeGenderCross.csv', ...)
persona_profile_df.to_csv(output_path / 'PersonaProfile.csv', ...)

# 修正後
supply_density_df.to_csv(output_path / 'SupplyDensityMap.csv', ...)
age_gender_cross_df.to_csv(output_path / 'AgeGenderCrossAnalysis.csv', ...)
persona_profile_df.to_csv(output_path / 'DetailedPersonaProfile.csv', ...)
```

**余分なファイル（PersonaMapData.csv, PersonaMobilityCross.csv）は削除**

---

### 修正4: Phase 8の新規実装

```python
def export_phase8_data(self, output_dir='data/output_v2/phase8'):
    """Phase 8: キャリア・学歴分析"""
    print("\n[PHASE8] Phase 8: キャリア・学歴分析")
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # 1. EducationDistribution.csv
    # 2. EducationAgeCross.csv
    # 3. EducationAgeCross_Matrix.csv
    # 4. GraduationYearDistribution.csv
    # 5. P8_QualityReport.csv
    # 6. P8_QualityReport_Inferential.csv
```

**完全な新規実装が必要（約200行）**

---

### 修正5: Phase 10の新規実装

```python
def export_phase10_data(self, output_dir='data/output_v2/phase10'):
    """Phase 10: 転職意欲・緊急度分析"""
    print("\n[PHASE10] Phase 10: 転職意欲・緊急度分析")
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # 1. UrgencyDistribution.csv
    # 2. UrgencyDistribution_ByMunicipality.csv
    # 3. UrgencyAgeCross.csv
    # 4. UrgencyAgeCross_ByMunicipality.csv
    # 5. UrgencyAgeCross_Matrix.csv
    # 6. UrgencyEmploymentCross.csv
    # 7. UrgencyEmploymentCross_ByMunicipality.csv
    # 8. UrgencyEmploymentCross_Matrix.csv
    # 9. P10_QualityReport.csv
    # 10. P10_QualityReport_Inferential.csv
```

**完全な新規実装が必要（約300行）**

---

### 修正6: data_normalizer統合

```python
def load_data(self):
    """データ読み込み"""
    self.df = pd.read_csv(self.filepath, encoding='utf-8-sig')

    # 正規化処理を追加
    from data_normalizer import DataNormalizer
    normalizer = DataNormalizer()
    self.df = normalizer.normalize_dataframe(self.df)

    return self.df
```

---

## 📝 修正の優先順位

### フェーズ1: 最小限の動作（1時間）

1. ✅ 出力先を `data/output_v2/phase*/` に変更（全Phase）
2. ✅ Phase 7のファイル名を修正（3ファイル）
3. ⬜ Phase 7の余分なファイルを削除（2ファイル）

**結果**: Phase 1-7が新しいフォルダ構造に対応（品質レポートなし）

---

### フェーズ2: 品質レポート追加（1.5時間）

4. ⬜ `data_quality_validator`の統合
5. ⬜ 全Phaseに品質レポート生成を追加（12ファイル）

**結果**: Phase 1-7が完全対応（Phase別ファイル名付き品質レポート）

---

### フェーズ3: Phase 8, 10実装（3時間）

6. ⬜ Phase 8の完全実装（6ファイル、約200行）
7. ⬜ Phase 10の完全実装（10ファイル、約300行）

**結果**: 全Phase完全対応（38ファイル）

---

### フェーズ4: データ正規化（30分）

8. ⬜ `data_normalizer`の統合

**結果**: 表記ゆれ正規化対応

---

## ✅ 推奨アクション

### オプションA: simple_analyzer.pyを段階的に修正（推奨）

**メリット**:
- ✅ 既存の動作するコードをベースにできる
- ✅ 段階的に修正可能（フェーズ1だけでも価値あり）
- ✅ テスト済みのロジックを再利用

**デメリット**:
- ⚠️ Phase 8, 10の実装が必要（約500行）
- ⚠️ 品質レポート統合が必要

**所要時間**: 合計5-6時間

---

### オプションB: 正しいrun_complete_v2.pyを別途作成

**メリット**:
- ✅ 最初から正しい構造で実装
- ✅ 全機能を一度に実装

**デメリット**:
- ❌ ゼロから実装（約1000行）
- ❌ テストが必要

**所要時間**: 合計8-10時間

---

### オプションC: 既存のバックアップを探す

**メリット**:
- ✅ 即座に動作可能（見つかれば）

**デメリット**:
- ❌ 正しいファイルが存在しない可能性

**所要時間**: 不明（ファイルが見つからない）

---

## 🎯 結論

**simple_analyzer.pyは以下の点で不完全**:

1. ❌ 出力先が旧形式（`gas_output_*`）
2. ❌ 品質レポートが未生成（12ファイル欠落）
3. ❌ Phase 8, 10が未実装（16ファイル欠落）
4. ❌ Phase別ファイル名なし
5. ⚠️ Phase 7のファイル名が3つ不一致
6. ⚠️ data_normalizer未統合

**推奨**: オプションAで段階的に修正（まずフェーズ1だけでも実施）

これにより、最小限の工数で新しいフォルダ構造に対応できます。
