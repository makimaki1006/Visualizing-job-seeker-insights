# 品質レポートファイル名重複問題の解決提案

**作成日**: 2025年10月29日
**問題**: ドラッグ&ドロップ時にすべて同じ`QualityReport_Inferential.csv`で区別不可
**優先度**: 🔴 HIGH（ユーザビリティに直接影響）

---

## 📋 問題の詳細

### 現状のファイル構成

```
data/output_v2/
├── phase2/
│   ├── QualityReport_Inferential.csv          # ❌ 重複
│   └── P2_QualityReport_Inferential.csv       # ✅ Phase別版（既存）
├── phase3/
│   ├── QualityReport_Inferential.csv          # ❌ 重複
│   └── P3_QualityReport_Inferential.csv       # ✅ Phase別版（既存）
├── phase6/
│   ├── QualityReport_Inferential.csv          # ❌ 重複
│   └── P6_QualityReport_Inferential.csv       # ✅ Phase別版（既存）
├── phase7/
│   ├── QualityReport_Inferential.csv          # ❌ 重複
│   └── P7_QualityReport_Inferential.csv       # ✅ Phase別版（既存）
├── phase8/
│   ├── QualityReport.csv                      # ❌ 重複
│   ├── QualityReport_Inferential.csv          # ❌ 重複
│   ├── P8_QualityReport.csv                   # ✅ Phase別版（既存）
│   └── P8_QualityReport_Inferential.csv       # ✅ Phase別版（既存）
└── phase10/
    ├── QualityReport.csv                      # ❌ 重複
    ├── QualityReport_Inferential.csv          # ❌ 重複
    ├── P10_QualityReport.csv                  # ✅ Phase別版（既存）
    └── P10_QualityReport_Inferential.csv      # ✅ Phase別版（既存）
```

### 問題シナリオ

**ユーザーの操作**:
1. Windowsエクスプローラーで複数のphaseフォルダを開く
2. すべての`QualityReport_Inferential.csv`を選択してドラッグ&ドロップ
3. **問題**: ファイル名が同じなので、どれがどのPhaseか区別できない

**影響**:
- ❌ ファイル選択時に混乱
- ❌ 間違ったPhaseのファイルをインポート
- ❌ ファイルが上書きされる可能性

---

## ✅ 解決策

### オプションA: 旧形式ファイルの生成を停止（推奨）

**変更内容**:
- `QualityReport_Inferential.csv` の生成を停止
- `P{Phase}_QualityReport_Inferential.csv` のみ生成
- GASインポーターも Phase別ファイル名のみを読み込む

**メリット**:
- ✅ 完全に重複を解消
- ✅ ファイル数が減る（37→25ファイル）
- ✅ ディスク容量削減

**デメリット**:
- ⚠️ 既存のPythonスクリプトでファイル名を直接参照している箇所の修正が必要

---

### オプションB: 旧形式ファイルを削除する追加処理（中間案）

**変更内容**:
- Pythonスクリプト実行後、旧形式ファイルを自動削除
- Phase別ファイル名のみを残す

**メリット**:
- ✅ 既存のロジックを変更不要
- ✅ 完全に重複を解消

**デメリット**:
- ⚠️ 旧形式を期待する既存スクリプトがあれば影響

---

### オプションC: 両方を生成（現状維持・非推奨）

**変更内容**:
- なし（現状維持）

**メリット**:
- ✅ 既存スクリプトとの互換性維持

**デメリット**:
- ❌ 重複問題が解決しない
- ❌ ユーザビリティが悪い
- ❌ ディスク容量の無駄

---

## 🎯 推奨解決策: オプションA

### 実装手順

#### 1. Pythonスクリプト修正

**ファイル**: `data_quality_validator.py`

**修正箇所**: `save_quality_report()` メソッド

**変更前**:
```python
def save_quality_report(self, report: Dict, output_path: str):
    """
    品質レポートをCSVファイルに保存

    Args:
        report: 品質レポート辞書
        output_path: 出力パス（例: phase2/QualityReport_Inferential.csv）
    """
    # ...既存の処理...
    df_columns.to_csv(output_path, index=False, encoding='utf-8-sig')
```

**変更後**:
```python
def save_quality_report(self, report: Dict, output_path: str, phase_prefix: str = None):
    """
    品質レポートをCSVファイルに保存（Phase別ファイル名対応）

    Args:
        report: 品質レポート辞書
        output_path: 出力パス（例: phase2/QualityReport_Inferential.csv）
        phase_prefix: Phaseプレフィックス（例: 'P2'） ※指定時はPhase別ファイル名のみ生成
    """
    from pathlib import Path

    # Phase別ファイル名を生成
    if phase_prefix:
        # phase_prefix が指定された場合はPhase別ファイル名のみ生成
        output_dir = Path(output_path).parent
        original_filename = Path(output_path).name
        phase_filename = f"{phase_prefix}_{original_filename}"
        final_output_path = output_dir / phase_filename
    else:
        # 後方互換性のため、phase_prefix が未指定の場合は両方生成
        final_output_path = output_path

    # カラム検証結果をDataFrameに変換
    column_data = []
    for col_name, validation in report['column_validations'].items():
        column_data.append({
            'カラム名': col_name,
            '有効データ数': validation['valid_count'],
            'ユニーク値数': validation['unique_values'],
            '最小グループサイズ': validation['min_group_size'],
            '信頼性レベル': validation['reliability_level'],
            '警告': validation['warning']
        })

    df_columns = pd.DataFrame(column_data)
    df_columns.to_csv(final_output_path, index=False, encoding='utf-8-sig')

    print(f"品質レポート出力: {final_output_path}")
```

---

#### 2. 各Phase処理での呼び出し修正

**ファイル**: `run_complete_v2.py` または各Phase処理スクリプト

**Phase 2の例**:

**変更前**:
```python
# Phase 2品質レポート生成
validator = DataQualityValidator(validation_mode='inferential')
report = validator.generate_quality_report(df_phase2)
validator.save_quality_report(report, 'data/output_v2/phase2/QualityReport_Inferential.csv')
```

**変更後**:
```python
# Phase 2品質レポート生成
validator = DataQualityValidator(validation_mode='inferential')
report = validator.generate_quality_report(df_phase2)
# Phase別ファイル名のみ生成（phase_prefixを指定）
validator.save_quality_report(
    report,
    'data/output_v2/phase2/QualityReport_Inferential.csv',
    phase_prefix='P2'  # ← 追加
)
```

**すべてのPhaseで同様に修正**:
- Phase 1: `phase_prefix='P1'`
- Phase 2: `phase_prefix='P2'`
- Phase 3: `phase_prefix='P3'`
- Phase 6: `phase_prefix='P6'`
- Phase 7: `phase_prefix='P7'`
- Phase 8: `phase_prefix='P8'`
- Phase 10: `phase_prefix='P10'`

---

#### 3. GASインポーター修正

**ファイル**: `PythonCSVImporter.gs`

**変更前**:
```javascript
// Phase 2
{name: 'QualityReport_Inferential.csv', sheetName: 'P2_QualityInfer', subfolder: 'phase2'},
```

**変更後**:
```javascript
// Phase 2（Phase別ファイル名を直接指定）
{name: 'P2_QualityReport_Inferential.csv', sheetName: 'P2_QualityInfer', subfolder: 'phase2'},
```

**すべてのPhaseで修正**:
```javascript
// Phase 1
{name: 'P1_QualityReport.csv', sheetName: 'P1_QualityReport', subfolder: 'phase1'},
{name: 'P1_QualityReport_Descriptive.csv', sheetName: 'P1_QualityDesc', subfolder: 'phase1'},

// Phase 2
{name: 'P2_QualityReport_Inferential.csv', sheetName: 'P2_QualityInfer', subfolder: 'phase2'},

// Phase 3
{name: 'P3_QualityReport_Inferential.csv', sheetName: 'P3_QualityInfer', subfolder: 'phase3'},

// Phase 6
{name: 'P6_QualityReport_Inferential.csv', sheetName: 'P6_QualityInfer', subfolder: 'phase6'},

// Phase 7
{name: 'P7_QualityReport_Inferential.csv', sheetName: 'P7_QualityInfer', subfolder: 'phase7'},

// Phase 8
{name: 'P8_QualityReport.csv', sheetName: 'P8_QualityReport', subfolder: 'phase8'},
{name: 'P8_QualityReport_Inferential.csv', sheetName: 'P8_QualityInfer', subfolder: 'phase8'},

// Phase 10
{name: 'P10_QualityReport.csv', sheetName: 'P10_QualityReport', subfolder: 'phase10'},
{name: 'P10_QualityReport_Inferential.csv', sheetName: 'P10_QualityInfer', subfolder: 'phase10'},
```

---

#### 4. 旧形式ファイルのクリーンアップ

**実行コマンド**:
```bash
# 旧形式ファイルを削除（backup除く）
cd "C:\Users\fuji1\OneDrive\Pythonスクリプト保管\job_medley_project\data\output_v2"

# Phase 2-10の旧形式品質レポートを削除
rm phase2/QualityReport_Inferential.csv
rm phase3/QualityReport_Inferential.csv
rm phase6/QualityReport_Inferential.csv
rm phase7/QualityReport_Inferential.csv
rm phase8/QualityReport.csv
rm phase8/QualityReport_Inferential.csv
rm phase10/QualityReport.csv
rm phase10/QualityReport_Inferential.csv
```

または、Pythonスクリプトで自動削除：
```python
import os
from pathlib import Path

def cleanup_old_quality_reports(output_dir: Path):
    """
    旧形式の品質レポートファイルを削除

    Args:
        output_dir: output_v2ディレクトリのパス
    """
    old_files = [
        'phase2/QualityReport_Inferential.csv',
        'phase3/QualityReport_Inferential.csv',
        'phase6/QualityReport_Inferential.csv',
        'phase7/QualityReport_Inferential.csv',
        'phase8/QualityReport.csv',
        'phase8/QualityReport_Inferential.csv',
        'phase10/QualityReport.csv',
        'phase10/QualityReport_Inferential.csv',
    ]

    for file_path in old_files:
        full_path = output_dir / file_path
        if full_path.exists():
            full_path.unlink()
            print(f"削除: {full_path}")
```

---

## 📊 変更後のファイル構成

```
data/output_v2/
├── phase1/
│   ├── Applicants.csv
│   ├── DesiredWork.csv
│   ├── AggDesired.csv
│   ├── MapMetrics.csv
│   ├── P1_QualityReport.csv                   # ✅ Phase別版のみ
│   └── P1_QualityReport_Descriptive.csv       # ✅ Phase別版のみ
│
├── phase2/
│   ├── ChiSquareTests.csv
│   ├── ANOVATests.csv
│   └── P2_QualityReport_Inferential.csv       # ✅ Phase別版のみ
│
├── phase3/
│   ├── PersonaSummary.csv
│   ├── PersonaDetails.csv
│   └── P3_QualityReport_Inferential.csv       # ✅ Phase別版のみ
│
├── phase6/
│   ├── MunicipalityFlowEdges.csv
│   ├── MunicipalityFlowNodes.csv
│   ├── ProximityAnalysis.csv
│   └── P6_QualityReport_Inferential.csv       # ✅ Phase別版のみ
│
├── phase7/
│   ├── SupplyDensityMap.csv
│   ├── QualificationDistribution.csv
│   ├── AgeGenderCrossAnalysis.csv
│   ├── MobilityScore.csv
│   ├── DetailedPersonaProfile.csv
│   └── P7_QualityReport_Inferential.csv       # ✅ Phase別版のみ
│
├── phase8/
│   ├── EducationDistribution.csv
│   ├── EducationAgeCross.csv
│   ├── EducationAgeCross_Matrix.csv
│   ├── GraduationYearDistribution.csv
│   ├── P8_QualityReport.csv                   # ✅ Phase別版のみ
│   └── P8_QualityReport_Inferential.csv       # ✅ Phase別版のみ
│
├── phase10/
│   ├── UrgencyDistribution.csv
│   ├── UrgencyAgeCross.csv
│   ├── UrgencyAgeCross_Matrix.csv
│   ├── UrgencyEmploymentCross.csv
│   ├── UrgencyEmploymentCross_Matrix.csv
│   ├── P10_QualityReport.csv                  # ✅ Phase別版のみ
│   └── P10_QualityReport_Inferential.csv      # ✅ Phase別版のみ
│
├── OverallQualityReport.csv
└── OverallQualityReport_Inferential.csv

合計: 37 → 25ファイル（12ファイル削減） ✅
```

---

## ✅ 検証チェックリスト

### Pythonスクリプト実行後

- [ ] 各Phaseフォルダに`P{Phase}_QualityReport*.csv`が存在
- [ ] 旧形式の`QualityReport*.csv`が存在しない
- [ ] ファイル数が25個（品質レポート含む）

### GASインポート後

- [ ] すべてのPhaseの品質レポートシートが作成される
- [ ] シート名が`P{Phase}_Quality*`形式
- [ ] エラーなくインポート完了

### ユーザビリティ確認

- [ ] エクスプローラーで複数Phaseフォルダを開いた時、品質レポートファイル名が一意
- [ ] ドラッグ&ドロップ時にPhaseを識別可能
- [ ] ファイル検索時にPhase番号で絞り込み可能

---

## 📝 実装優先度

| タスク | 優先度 | 所要時間 | 影響範囲 |
|--------|-------|---------|---------|
| 1. `data_quality_validator.py`修正 | 🔴 HIGH | 15分 | 全Phase |
| 2. `run_complete_v2.py`修正 | 🔴 HIGH | 30分 | 全Phase |
| 3. `PythonCSVImporter.gs`修正 | 🟡 MEDIUM | 10分 | GAS |
| 4. 旧形式ファイル削除 | 🟢 LOW | 5分 | クリーンアップ |
| 5. テスト実行 | 🔴 HIGH | 20分 | 検証 |

**合計所要時間**: 約1.5時間

---

## 🚀 次のステップ

1. ✅ この提案書をレビュー
2. ⏳ `data_quality_validator.py` の `save_quality_report()` メソッド修正
3. ⏳ `run_complete_v2.py` で全Phaseの呼び出しに `phase_prefix` 追加
4. ⏳ `PythonCSVImporter.gs` のファイル名マッピング修正
5. ⏳ テスト実行（Python → GASインポート → 可視化）
6. ⏳ 旧形式ファイルのクリーンアップ
7. ✅ ドキュメント更新（CLAUDE.md, README.md）

---

## 💡 補足: 既存スクリプトへの影響

### 影響なし
- ✅ GAS可視化スクリプト（シート名は変わらない）
- ✅ テストスクリプト（既にPhase別ファイル名を参照）

### 確認が必要
- ⚠️ 品質レポートを直接読み込むPythonスクリプト（あれば）
- ⚠️ 手動でファイル名を指定しているドキュメント

---

## 📚 参考資料

- **QUALITY_REPORT_NAMING_STRATEGY.md**: GASシート名のマッピング戦略
- **DATA_FLOW_CORRELATION.md**: データフロー全体図
- **DATA_USAGE_GUIDELINES.md**: 品質レポートの利用ガイドライン
