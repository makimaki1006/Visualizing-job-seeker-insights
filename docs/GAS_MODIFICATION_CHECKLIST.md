# GAS側の受け入れ態勢修正チェックリスト

**作成日**: 2025年10月29日
**目的**: Pythonで生成するPhase別ファイル名（`P{Phase}_QualityReport*.csv`）にGAS側を対応させる

---

## 📋 修正が必要なGASファイル（6ファイル）

### 1. PythonCSVImporter.gs ⭐ 最重要

**修正箇所**: 25-78行目（`requiredFiles`配列）

**修正内容**: 品質レポートのファイル名を旧形式 → Phase別形式に変更

#### 修正前後の比較

```javascript
// ❌ 修正前（旧形式）
// Phase 1
{name: 'QualityReport.csv', sheetName: 'P1_QualityReport', required: false, phase: 1, subfolder: 'phase1'},
{name: 'QualityReport_Descriptive.csv', sheetName: 'P1_QualityDesc', required: false, phase: 1, subfolder: 'phase1'},

// Phase 2
{name: 'QualityReport_Inferential.csv', sheetName: 'P2_QualityInfer', required: false, phase: 2, subfolder: 'phase2'},

// Phase 3
{name: 'QualityReport_Inferential.csv', sheetName: 'P3_QualityInfer', required: false, phase: 3, subfolder: 'phase3'},

// Phase 6
{name: 'QualityReport_Inferential.csv', sheetName: 'P6_QualityInfer', required: false, phase: 6, subfolder: 'phase6'},

// Phase 7
{name: 'QualityReport_Inferential.csv', sheetName: 'P7_QualityInfer', required: false, phase: 7, subfolder: 'phase7'},

// Phase 8
{name: 'QualityReport.csv', sheetName: 'P8_QualityReport', required: false, phase: 8, subfolder: 'phase8'},
{name: 'QualityReport_Inferential.csv', sheetName: 'P8_QualityInfer', required: false, phase: 8, subfolder: 'phase8'},

// Phase 10
{name: 'QualityReport.csv', sheetName: 'P10_QualityReport', required: false, phase: 10, subfolder: 'phase10'},
{name: 'QualityReport_Inferential.csv', sheetName: 'P10_QualityInfer', required: false, phase: 10, subfolder: 'phase10'},
```

```javascript
// ✅ 修正後（Phase別形式）
// Phase 1
{name: 'P1_QualityReport.csv', sheetName: 'P1_QualityReport', required: false, phase: 1, subfolder: 'phase1'},
{name: 'P1_QualityReport_Descriptive.csv', sheetName: 'P1_QualityDesc', required: false, phase: 1, subfolder: 'phase1'},

// Phase 2
{name: 'P2_QualityReport_Inferential.csv', sheetName: 'P2_QualityInfer', required: false, phase: 2, subfolder: 'phase2'},

// Phase 3
{name: 'P3_QualityReport_Inferential.csv', sheetName: 'P3_QualityInfer', required: false, phase: 3, subfolder: 'phase3'},

// Phase 6
{name: 'P6_QualityReport_Inferential.csv', sheetName: 'P6_QualityInfer', required: false, phase: 6, subfolder: 'phase6'},

// Phase 7
{name: 'P7_QualityReport_Inferential.csv', sheetName: 'P7_QualityInfer', required: false, phase: 7, subfolder: 'phase7'},

// Phase 8
{name: 'P8_QualityReport.csv', sheetName: 'P8_QualityReport', required: false, phase: 8, subfolder: 'phase8'},
{name: 'P8_QualityReport_Inferential.csv', sheetName: 'P8_QualityInfer', required: false, phase: 8, subfolder: 'phase8'},

// Phase 10
{name: 'P10_QualityReport.csv', sheetName: 'P10_QualityReport', required: false, phase: 10, subfolder: 'phase10'},
{name: 'P10_QualityReport_Inferential.csv', sheetName: 'P10_QualityInfer', required: false, phase: 10, subfolder: 'phase10'},
```

**変更箇所**: 12行（Phase 1, 2, 3, 6, 7, 8×2, 10×2）

---

### 2. MenuIntegration.gs

**修正箇所**: 191-246行目（ヘルプメッセージHTML内）

**修正内容**: ファイル名の表示を Phase別形式に更新

#### 修正前後の比較

```javascript
// ❌ 修正前
<div class="file-item">→ MapMetrics.csv, QualityReport.csv, QualityReport_Descriptive.csv</div>

// Phase 2
<div class="file-item">→ ChiSquareTests.csv, ANOVATests.csv, QualityReport_Inferential.csv</div>

// Phase 3
<div class="file-item">→ PersonaSummary.csv, PersonaDetails.csv, QualityReport_Inferential.csv</div>

// Phase 6
<div class="file-item">→ ProximityAnalysis.csv, QualityReport_Inferential.csv</div>

// Phase 7
<div class="file-item">→ DetailedPersonaProfile.csv, QualityReport_Inferential.csv</div>

// Phase 8
<div class="file-item">→ QualityReport.csv, QualityReport_Inferential.csv</div>

// Phase 10
<div class="file-item">→ QualityReport.csv, QualityReport_Inferential.csv</div>
```

```javascript
// ✅ 修正後
<div class="file-item">→ MapMetrics.csv, P1_QualityReport.csv, P1_QualityReport_Descriptive.csv</div>

// Phase 2
<div class="file-item">→ ChiSquareTests.csv, ANOVATests.csv, P2_QualityReport_Inferential.csv</div>

// Phase 3
<div class="file-item">→ PersonaSummary.csv, PersonaDetails.csv, P3_QualityReport_Inferential.csv</div>

// Phase 6
<div class="file-item">→ ProximityAnalysis.csv, P6_QualityReport_Inferential.csv</div>

// Phase 7
<div class="file-item">→ DetailedPersonaProfile.csv, P7_QualityReport_Inferential.csv</div>

// Phase 8
<div class="file-item">→ P8_QualityReport.csv, P8_QualityReport_Inferential.csv</div>

// Phase 10
<div class="file-item">→ P10_QualityReport.csv, P10_QualityReport_Inferential.csv</div>
```

**変更箇所**: 7箇所（Phase 1, 2, 3, 6, 7, 8, 10）

**重要度**: 🟡 MEDIUM（表示のみなので動作には影響なし）

---

### 3. Phase8DataImporter.gs

**修正箇所**: なし

**理由**: このファイルはシート名（`P8_EducationDist`等）を参照しているだけで、CSVファイル名は参照していない

**確認事項**: シート名が正しく作成されるか確認（PythonCSVImporter.gsの修正で対応済み）

---

### 4. Phase10DataImporter.gs

**修正箇所**: なし

**理由**: このファイルはシート名（`P10_UrgencyDist`等）を参照しているだけで、CSVファイル名は参照していない

**確認事項**: シート名が正しく作成されるか確認（PythonCSVImporter.gsの修正で対応済み）

---

### 5. QualityDashboard.gs

**確認が必要**: 品質レポートシート名を参照している可能性

**確認コマンド**:
```bash
grep -n "P._Quality" QualityDashboard.gs
```

**想定される参照**:
- `P1_QualityReport`, `P1_QualityDesc`
- `P2_QualityInfer`
- `P3_QualityInfer`
- `P6_QualityInfer`
- `P7_QualityInfer`
- `P8_QualityReport`, `P8_QualityInfer`
- `P10_QualityReport`, `P10_QualityInfer`

**修正内容**: シート名は変わらないので、修正不要の可能性が高い

---

### 6. RegionDashboard.gs

**確認が必要**: 品質レポートを統合表示する場合に参照している可能性

**確認コマンド**:
```bash
grep -n "Quality" RegionDashboard.gs
```

**修正内容**: シート名参照のみであれば修正不要

---

## 🎯 修正優先順位

| ファイル | 優先度 | 所要時間 | 影響範囲 | 修正行数 |
|---------|-------|---------|---------|---------|
| **PythonCSVImporter.gs** | 🔴 CRITICAL | 10分 | 全Phase | 12行 |
| **MenuIntegration.gs** | 🟡 MEDIUM | 5分 | ヘルプ表示 | 7箇所 |
| **QualityDashboard.gs** | 🟢 LOW（確認のみ） | 5分 | 品質ダッシュボード | 0行（想定） |
| **RegionDashboard.gs** | 🟢 LOW（確認のみ） | 5分 | 地域ダッシュボード | 0行（想定） |

---

## 📝 修正手順（ステップバイステップ）

### ステップ1: PythonCSVImporter.gs 修正 ⭐

1. GASエディタで `PythonCSVImporter.gs` を開く
2. 25-78行目の `requiredFiles` 配列を表示
3. 以下の12行を修正：

```javascript
// 31行目
{name: 'QualityReport.csv', sheetName: 'P1_QualityReport', ...}
↓
{name: 'P1_QualityReport.csv', sheetName: 'P1_QualityReport', ...}

// 32行目
{name: 'QualityReport_Descriptive.csv', sheetName: 'P1_QualityDesc', ...}
↓
{name: 'P1_QualityReport_Descriptive.csv', sheetName: 'P1_QualityDesc', ...}

// 37行目
{name: 'QualityReport_Inferential.csv', sheetName: 'P2_QualityInfer', ...}
↓
{name: 'P2_QualityReport_Inferential.csv', sheetName: 'P2_QualityInfer', ...}

// 42行目
{name: 'QualityReport_Inferential.csv', sheetName: 'P3_QualityInfer', ...}
↓
{name: 'P3_QualityReport_Inferential.csv', sheetName: 'P3_QualityInfer', ...}

// 48行目
{name: 'QualityReport_Inferential.csv', sheetName: 'P6_QualityInfer', ...}
↓
{name: 'P6_QualityReport_Inferential.csv', sheetName: 'P6_QualityInfer', ...}

// 56行目
{name: 'QualityReport_Inferential.csv', sheetName: 'P7_QualityInfer', ...}
↓
{name: 'P7_QualityReport_Inferential.csv', sheetName: 'P7_QualityInfer', ...}

// 63行目
{name: 'QualityReport.csv', sheetName: 'P8_QualityReport', ...}
↓
{name: 'P8_QualityReport.csv', sheetName: 'P8_QualityReport', ...}

// 64行目
{name: 'QualityReport_Inferential.csv', sheetName: 'P8_QualityInfer', ...}
↓
{name: 'P8_QualityReport_Inferential.csv', sheetName: 'P8_QualityInfer', ...}

// 72行目
{name: 'QualityReport.csv', sheetName: 'P10_QualityReport', ...}
↓
{name: 'P10_QualityReport.csv', sheetName: 'P10_QualityReport', ...}

// 73行目
{name: 'QualityReport_Inferential.csv', sheetName: 'P10_QualityInfer', ...}
↓
{name: 'P10_QualityReport_Inferential.csv', sheetName: 'P10_QualityInfer', ...}
```

4. 保存（Ctrl+S）

---

### ステップ2: MenuIntegration.gs 修正

1. GASエディタで `MenuIntegration.gs` を開く
2. 191-246行目のHTML内のファイル名を修正
3. 7箇所を Phase別形式に変更（上記の修正前後を参照）
4. 保存（Ctrl+S）

---

### ステップ3: QualityDashboard.gs 確認

1. GASエディタで `QualityDashboard.gs` を開く
2. `Ctrl+F` で "Quality" を検索
3. シート名参照（`getSheetByName('P{X}_Quality*')`）を確認
4. ファイル名参照がなければ修正不要

---

### ステップ4: RegionDashboard.gs 確認

1. GASエディタで `RegionDashboard.gs` を開く
2. `Ctrl+F` で "Quality" を検索
3. シート名参照を確認
4. ファイル名参照がなければ修正不要

---

## ✅ 修正後の検証手順

### 1. Pythonスクリプト実行

```bash
cd "C:\Users\fuji1\OneDrive\Pythonスクリプト保管\job_medley_project\python_scripts"
python run_complete_v2.py
```

**確認事項**:
- [ ] Phase別ファイル名（`P{Phase}_QualityReport*.csv`）が生成される
- [ ] 旧形式ファイル（`QualityReport*.csv`）が生成されない

---

### 2. GASインポート実行

GASメニュー: `🐍 Python連携` → `📥 Python結果CSVを取り込み`

**確認事項**:
- [ ] エラーなくインポート完了
- [ ] すべての品質レポートシートが作成される:
  - `P1_QualityReport`
  - `P1_QualityDesc`
  - `P2_QualityInfer`
  - `P3_QualityInfer`
  - `P6_QualityInfer`
  - `P7_QualityInfer`
  - `P8_QualityReport`
  - `P8_QualityInfer`
  - `P10_QualityReport`
  - `P10_QualityInfer`
  - `OverallQuality`
  - `OverallQualityInfer`

---

### 3. 品質ダッシュボード確認

GASメニュー: `データ管理` → `✅ データ検証レポート`

**確認事項**:
- [ ] 品質ダッシュボードが正常に表示される
- [ ] 全Phaseの品質レポートが表示される
- [ ] エラーメッセージがない

---

### 4. ファイル名の一意性確認

Windowsエクスプローラーで複数のphaseフォルダを開く

**確認事項**:
- [ ] 品質レポートファイル名が Phase別プレフィックス付き
- [ ] ファイル名が一意で識別可能
- [ ] ドラッグ&ドロップ時に混乱しない

---

## 🚨 トラブルシューティング

### エラー: 「ファイルが見つかりません」

**原因**: Pythonで旧形式ファイル名を生成しているが、GASはPhase別形式を探している

**解決策**:
1. Pythonスクリプトを再実行してPhase別ファイル名を生成
2. または、GASインポーターのファイル名を旧形式に戻す（非推奨）

---

### エラー: 「シートが見つかりません」

**原因**: シート名の不一致

**解決策**:
1. 品質ダッシュボードや可視化スクリプトのシート名参照を確認
2. `P{Phase}_Quality*` 形式で統一されているか確認

---

### 警告: 「一部のファイルがインポートされませんでした」

**原因**: Pythonで生成されるファイル数とGASの期待値が不一致

**解決策**:
1. Pythonスクリプトの出力ログを確認
2. 各Phaseで期待されるファイル数を確認:
   - Phase 1: 6ファイル
   - Phase 2: 3ファイル
   - Phase 3: 3ファイル
   - Phase 6: 4ファイル
   - Phase 7: 6ファイル
   - Phase 8: 6ファイル
   - Phase 10: 7ファイル
   - Root: 2ファイル
   - **合計**: 37 → 25ファイル（旧形式削除後）

---

## 📚 関連ドキュメント

- **FILE_NAMING_FIX_PROPOSAL.md**: Python側の修正提案
- **QUALITY_REPORT_NAMING_STRATEGY.md**: Phase別命名戦略
- **DATA_FLOW_CORRELATION.md**: データフロー全体図
- **GAS_COMPLETE_FEATURE_LIST.md**: GAS機能一覧

---

## ✅ 最終チェックリスト

### Python側
- [ ] `data_quality_validator.py` の `save_quality_report()` に `phase_prefix` パラメータ追加
- [ ] `run_complete_v2.py` で全Phaseの呼び出しに `phase_prefix='P{X}'` 指定
- [ ] テスト実行して Phase別ファイル名が生成されることを確認

### GAS側
- [ ] `PythonCSVImporter.gs` の `requiredFiles` 配列を Phase別ファイル名に修正（12行）
- [ ] `MenuIntegration.gs` のヘルプメッセージを Phase別ファイル名に修正（7箇所）
- [ ] `QualityDashboard.gs` でファイル名参照がないか確認
- [ ] `RegionDashboard.gs` でファイル名参照がないか確認

### 動作確認
- [ ] Pythonスクリプト実行 → Phase別ファイル名生成
- [ ] GASインポート → エラーなく完了
- [ ] 品質ダッシュボード → 正常表示
- [ ] ファイル名の一意性 → ドラッグ&ドロップで識別可能

### クリーンアップ
- [ ] 旧形式ファイル削除（`QualityReport*.csv`）
- [ ] バックアップ確認
- [ ] ドキュメント更新（CLAUDE.md, README.md）

---

## 🎯 完了条件

✅ **全ての品質レポートファイル名がPhase別プレフィックス付き**
✅ **GASインポートがエラーなく完了**
✅ **ファイル名の一意性が確保され、ドラッグ&ドロップで識別可能**
✅ **品質ダッシュボードが正常に動作**
