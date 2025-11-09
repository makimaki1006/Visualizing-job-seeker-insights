# 品質レポートファイルの命名戦略

**作成日**: 2025年10月29日
**問題**: `QualityReport_Inferential.csv` が複数Phaseで重複
**解決策**: Phase別プレフィックス付きシート名

---

## 📋 問題の概要

### 重複するファイル名

```
data/output_v2/
├── phase2/QualityReport_Inferential.csv   # Phase 2
├── phase3/QualityReport_Inferential.csv   # Phase 3
├── phase6/QualityReport_Inferential.csv   # Phase 6
├── phase7/QualityReport_Inferential.csv   # Phase 7
├── phase8/QualityReport_Inferential.csv   # Phase 8
└── phase10/QualityReport_Inferential.csv  # Phase 10
```

**ローカル**: フォルダで分離されているため問題なし ✅

**GAS**: 同じスプレッドシート内でシート名が衝突 ❌

---

## ✅ 現在の解決策（実装済み）

### 1. ローカルファイル構成

各Phaseフォルダ内に**2種類**の品質レポートを保存：

| ファイル名 | 用途 | 例 |
|-----------|------|-----|
| **P{X}_QualityReport_Inferential.csv** | Phase別プレフィックス版（GAS用） | `P2_QualityReport_Inferential.csv` |
| **QualityReport_Inferential.csv** | 汎用名（Python内部処理用） | `QualityReport_Inferential.csv` |

### 2. GASインポート時のマッピング

`PythonCSVImporter.gs` で**Phase別シート名**に変換：

```javascript
// Phase 2
{name: 'QualityReport_Inferential.csv', sheetName: 'P2_QualityInfer', subfolder: 'phase2'}

// Phase 3
{name: 'QualityReport_Inferential.csv', sheetName: 'P3_QualityInfer', subfolder: 'phase3'}

// Phase 6
{name: 'QualityReport_Inferential.csv', sheetName: 'P6_QualityInfer', subfolder: 'phase6'}

// Phase 7
{name: 'QualityReport_Inferential.csv', sheetName: 'P7_QualityInfer', subfolder: 'phase7'}

// Phase 8
{name: 'QualityReport_Inferential.csv', sheetName: 'P8_QualityInfer', subfolder: 'phase8'}

// Phase 10
{name: 'QualityReport_Inferential.csv', sheetName: 'P10_QualityInfer', subfolder: 'phase10'}
```

### 3. GASシート名（最終結果）

```
Google Spreadsheet
├── P2_QualityInfer    # Phase 2推論的考察品質レポート
├── P3_QualityInfer    # Phase 3推論的考察品質レポート
├── P6_QualityInfer    # Phase 6推論的考察品質レポート
├── P7_QualityInfer    # Phase 7推論的考察品質レポート
├── P8_QualityInfer    # Phase 8推論的考察品質レポート
└── P10_QualityInfer   # Phase 10推論的考察品質レポート
```

**結果**: シート名の衝突なし ✅

---

## 📊 全品質レポートファイルのマッピング

### Phase 1（基礎集計）

| ローカルファイル | サブフォルダ | GASシート名 | 検証モード |
|----------------|-------------|------------|-----------|
| `QualityReport.csv` | `phase1/` | `P1_QualityReport` | 総合 |
| `QualityReport_Descriptive.csv` | `phase1/` | `P1_QualityDesc` | 観察的記述 |

### Phase 2（統計分析）

| ローカルファイル | サブフォルダ | GASシート名 | 検証モード |
|----------------|-------------|------------|-----------|
| `QualityReport_Inferential.csv` | `phase2/` | `P2_QualityInfer` | 推論的考察 |

### Phase 3（ペルソナ分析）

| ローカルファイル | サブフォルダ | GASシート名 | 検証モード |
|----------------|-------------|------------|-----------|
| `QualityReport_Inferential.csv` | `phase3/` | `P3_QualityInfer` | 推論的考察 |

### Phase 6（フロー分析）

| ローカルファイル | サブフォルダ | GASシート名 | 検証モード |
|----------------|-------------|------------|-----------|
| `QualityReport_Inferential.csv` | `phase6/` | `P6_QualityInfer` | 推論的考察 |

### Phase 7（高度分析）

| ローカルファイル | サブフォルダ | GASシート名 | 検証モード |
|----------------|-------------|------------|-----------|
| `QualityReport_Inferential.csv` | `phase7/` | `P7_QualityInfer` | 推論的考察 |

### Phase 8（キャリア・学歴分析）

| ローカルファイル | サブフォルダ | GASシート名 | 検証モード |
|----------------|-------------|------------|-----------|
| `QualityReport.csv` | `phase8/` | `P8_QualityReport` | 総合 |
| `QualityReport_Inferential.csv` | `phase8/` | `P8_QualityInfer` | 推論的考察 |

### Phase 10（転職意欲・緊急度分析）

| ローカルファイル | サブフォルダ | GASシート名 | 検証モード |
|----------------|-------------|------------|-----------|
| `QualityReport.csv` | `phase10/` | `P10_QualityReport` | 総合 |
| `QualityReport_Inferential.csv` | `phase10/` | `P10_QualityInfer` | 推論的考察 |

### 統合品質レポート（ルート）

| ローカルファイル | サブフォルダ | GASシート名 | 検証モード |
|----------------|-------------|------------|-----------|
| `OverallQualityReport.csv` | ルート | `OverallQuality` | 総合 |
| `OverallQualityReport_Inferential.csv` | ルート | `OverallQualityInfer` | 推論的考察 |

---

## 🔄 データフロー

```
【Pythonスクリプト実行】
run_complete_v2.py
    ↓
各Phaseフォルダに品質レポート生成
├── phase2/QualityReport_Inferential.csv
├── phase3/QualityReport_Inferential.csv
├── phase6/QualityReport_Inferential.csv
├── phase7/QualityReport_Inferential.csv
├── phase8/QualityReport_Inferential.csv
└── phase10/QualityReport_Inferential.csv
    ↓
【GASインポート】
PythonCSVImporter.gs
    ↓
サブフォルダ指定でファイル特定
• phase2/QualityReport_Inferential.csv → P2_QualityInfer
• phase3/QualityReport_Inferential.csv → P3_QualityInfer
• phase6/QualityReport_Inferential.csv → P6_QualityInfer
• phase7/QualityReport_Inferential.csv → P7_QualityInfer
• phase8/QualityReport_Inferential.csv → P8_QualityInfer
• phase10/QualityReport_Inferential.csv → P10_QualityInfer
    ↓
【GASシート作成】
Google Spreadsheet
├── P2_QualityInfer    ✅
├── P3_QualityInfer    ✅
├── P6_QualityInfer    ✅
├── P7_QualityInfer    ✅
├── P8_QualityInfer    ✅
└── P10_QualityInfer   ✅

衝突なし！
```

---

## 🎯 命名規則

### シート名の命名パターン

```
P{Phase番号}_{機能略称}

例:
P2_QualityInfer    # Phase 2 品質推論
P7_SupplyDensity   # Phase 7 供給密度
P10_UrgencyDist    # Phase 10 緊急度分布
```

### 略称一覧

| 略称 | 正式名称 | 説明 |
|------|---------|------|
| `QualityInfer` | Quality Report Inferential | 推論的考察品質レポート |
| `QualityDesc` | Quality Report Descriptive | 観察的記述品質レポート |
| `QualityReport` | Quality Report | 総合品質レポート |
| `SupplyDensity` | Supply Density Map | 人材供給密度マップ |
| `Qualification` | Qualification Distribution | 資格別分布 |
| `AgeGenderCross` | Age Gender Cross Analysis | 年齢×性別クロス |
| `MobilityScore` | Mobility Score | 移動許容度スコア |
| `PersonaProfile` | Detailed Persona Profile | ペルソナ詳細プロファイル |
| `EducationDist` | Education Distribution | 学歴分布 |
| `EduAgeCross` | Education Age Cross | 学歴×年齢クロス |
| `EduAgeMatrix` | Education Age Matrix | 学歴×年齢マトリクス |
| `GradYearDist` | Graduation Year Distribution | 卒業年分布 |
| `UrgencyDist` | Urgency Distribution | 緊急度分布 |
| `UrgencyAge` | Urgency Age Cross | 緊急度×年齢クロス |
| `UrgencyAgeMatrix` | Urgency Age Matrix | 緊急度×年齢マトリクス |
| `UrgencyEmp` | Urgency Employment Cross | 緊急度×就業状態クロス |
| `UrgencyEmpMatrix` | Urgency Employment Matrix | 緊急度×就業状態マトリクス |

---

## 🛡️ 衝突防止のメカニズム

### 1. サブフォルダ指定

```javascript
// PythonCSVImporter.gs
{
  name: 'QualityReport_Inferential.csv',  // ファイル名は同じ
  sheetName: 'P2_QualityInfer',           // シート名は異なる
  subfolder: 'phase2'                     // フォルダで特定
}
```

### 2. Phase番号プレフィックス

すべての品質レポートに `P{Phase番号}_` を付与：

- ✅ 一意性保証
- ✅ Phase識別容易
- ✅ ソート時にPhase順に並ぶ

### 3. 略称の統一

シート名の長さ制限（31文字）を考慮し、機能名を略称化：

- `QualityReport_Inferential` → `QualityInfer`（14→12文字）
- `EducationDistribution` → `EducationDist`（22→14文字）
- `UrgencyEmploymentCross` → `UrgencyEmp`（22→10文字）

---

## 📝 実装確認チェックリスト

### Pythonスクリプト側

- [x] 各Phaseフォルダに `QualityReport_Inferential.csv` を生成
- [x] ルートに `OverallQualityReport_Inferential.csv` を生成
- [x] フォルダ構造が正しい（`data/output_v2/phase{X}/`）

### GASスクリプト側

- [x] `PythonCSVImporter.gs` にすべてのPhaseのマッピングが定義されている
- [x] `subfolder` パラメータでサブフォルダを正しく指定
- [x] `sheetName` が一意（`P{Phase}_` プレフィックス付き）
- [x] Phase 7専用のインポーター（`Phase7HTMLUploader.gs`）も対応

### GAS可視化側

- [x] 各可視化スクリプトが正しいシート名を参照
- [x] 品質ダッシュボードが全Phaseの品質レポートを表示可能

---

## 🔍 検証方法

### 1. ローカルファイルの確認

```bash
cd "C:\Users\fuji1\OneDrive\Pythonスクリプト保管\job_medley_project\data\output_v2"
find . -name "*QualityReport*.csv" | grep -v backup
```

**期待結果**: 各Phaseフォルダに品質レポートが存在

### 2. GASインポート後の確認

GASメニュー: `🐍 Python連携` → `📥 Python結果CSVを取り込み`

**期待結果**:
- シート一覧に以下が表示される:
  - `P1_QualityDesc`
  - `P1_QualityReport`
  - `P2_QualityInfer`
  - `P3_QualityInfer`
  - `P6_QualityInfer`
  - `P7_QualityInfer`
  - `P8_QualityInfer`
  - `P8_QualityReport`
  - `P10_QualityInfer`
  - `P10_QualityReport`
  - `OverallQuality`
  - `OverallQualityInfer`

### 3. シート名の一意性確認

```javascript
// GASスクリプトエディタで実行
function checkSheetNameUniqueness() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheets = ss.getSheets();
  var sheetNames = sheets.map(function(sheet) {
    return sheet.getName();
  });

  var uniqueNames = sheetNames.filter(function(name, index) {
    return sheetNames.indexOf(name) === index;
  });

  if (sheetNames.length === uniqueNames.length) {
    Logger.log('✅ すべてのシート名が一意です');
  } else {
    Logger.log('❌ 重複するシート名があります');
    Logger.log('重複: ' + sheetNames.filter(function(name, index) {
      return sheetNames.indexOf(name) !== index;
    }).join(', '));
  }
}
```

---

## 💡 今後の拡張時の注意

### 新しいPhaseを追加する場合

1. **Pythonスクリプト**: `data/output_v2/phase{X}/` フォルダに品質レポートを生成
2. **GASインポーター**: `PythonCSVImporter.gs` の `requiredFiles` 配列に追加
   ```javascript
   {
     name: 'QualityReport_Inferential.csv',
     sheetName: 'P{X}_QualityInfer',  // Phase番号を置き換え
     subfolder: 'phase{X}'            // Phase番号を置き換え
   }
   ```
3. **テスト**: インポート後にシート名の一意性を確認

### 新しい品質レポートタイプを追加する場合

1. **命名規則**: `P{Phase}_{TypeAbbr}` 形式を維持
2. **略称**: 31文字制限を考慮して決定
3. **ドキュメント更新**: 本文書の「略称一覧」に追加

---

## ✅ まとめ

| 項目 | ステータス | 詳細 |
|------|-----------|------|
| **ローカルファイル名** | ✅ 問題なし | フォルダで分離 |
| **GASシート名** | ✅ 対策済み | Phase別プレフィックス |
| **命名規則** | ✅ 統一済み | `P{Phase}_{略称}` |
| **衝突防止** | ✅ 実装済み | サブフォルダ指定 + 一意シート名 |
| **実装確認** | ✅ 完了 | PythonCSVImporter.gs で全Phase対応 |
| **拡張性** | ✅ 確保 | 新Phase追加時の手順明確 |

**結論**: 品質レポートファイル名の重複問題は、**Phase別プレフィックス付きシート名**により完全に解決されています。
