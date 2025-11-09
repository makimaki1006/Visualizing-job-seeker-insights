# ジョブメドレー求職者データ分析 - 完全データフローガイド

**バージョン**: v2.1 完璧版 + FlowNetworkMap対応
**メインスクリプト**: `run_complete_v2_perfect.py`
**最終更新**: 2025年11月1日
**出力ファイル数**: 43ファイル（Phase 6に集約フローエッジ追加）

---

## 📊 目次

1. [データフロー概要](#データフロー概要)
2. [ステップ1: 入力CSVデータ](#ステップ1-入力csvデータ)
3. [ステップ2: Python分析処理](#ステップ2-python分析処理)
4. [ステップ3: データアウトプット](#ステップ3-データアウトプット)
5. [ステップ4: GAS連携・可視化](#ステップ4-gas連携可視化)
6. [実行手順](#実行手順)

---

## データフロー概要

```
【ステップ1】入力CSVデータ（ジョブメドレー生データ）
    ↓
【ステップ2】Python分析処理（run_complete_v2_perfect.py）
    ├─ データ正規化（DataNormalizer）
    ├─ データ処理（PerfectJobSeekerAnalyzer）
    ├─ Phase 1, 2, 3, 6, 7, 8, 10分析
    └─ 品質検証（DataQualityValidator）
    ↓
【ステップ3】データアウトプット（42ファイル）
    └─ data/output_v2/phase*/
    ↓
【ステップ4】GAS連携・可視化
    ├─ データインポート（DataImportAndValidation.gs）
    ├─ 各Phase可視化（UnifiedVisualizations.gs）
    └─ 統合ダッシュボード
```

---

## ステップ1: 入力CSVデータ

### 保存場所
```
C:\Users\fuji1\OneDrive\Pythonスクリプト保管\out\
├── results_20251027_180947.csv  # 最新データ
└── results_20251028_112441.csv  # 追加データ
```

### データ形式（13カラム）

| カラム名 | 説明 | 例 |
|---------|------|-----|
| page | ページ番号 | 1, 2 |
| card_index | カード番号 | 1-30 |
| age_gender | 年齢・性別 | "49歳 女性" |
| location | 居住地 | "奈良県山辺郡山添村" |
| member_id | 会員ID | "00636683" |
| status | ステータス | "HOT" |
| desired_area | 希望勤務地（複数） | "奈良県奈良市,京都府木津川市" |
| desired_workstyle | 希望勤務形態 | "パート・バイト" |
| desired_start | 転職希望時期 | "機会があれば転職を検討したい" |
| career | 学歴・キャリア | "(専門学校)(1992年3月卒業)" |
| employment_status | 就業状態 | "就業中", "離職中", "在学中" |
| desired_job | 希望職種 | "介護職/ヘルパー (10年以上)" |
| qualifications | 資格（複数） | "介護福祉士,自動車運転免許" |

---

## ステップ2: Python分析処理

### メインスクリプト

**`run_complete_v2_perfect.py`**
- **サイズ**: 1,903行、85KB
- **最終更新**: 2025/10/30 9:39
- **バージョン**: v2.1 完璧版
- **対応Phase**: Phase 1, 2, 3, 6, 7, 8, 10

### 実行方法

```bash
cd "C:\Users\fuji1\OneDrive\Pythonスクリプト保管\job_medley_project\python_scripts"
python run_complete_v2_perfect.py
```

### 処理フロー

```python
if __name__ == "__main__":
    # 1. GUIでCSVファイル選択
    csv_path = filedialog.askopenfilename(
        title="CSVファイルを選択",
        initialdir=r"C:\Users\fuji1\OneDrive\Pythonスクリプト保管\out"
    )

    # 2. PerfectJobSeekerAnalyzer初期化
    analyzer = PerfectJobSeekerAnalyzer(csv_path)

    # 3. データ読み込み + 正規化
    analyzer.load_data()        # DataNormalizer統合
    analyzer.process_data()     # データ処理

    # 4. Phase 1-10実行
    analyzer.export_phase1()    # 基礎集計（6ファイル）
    analyzer.export_phase2()    # 統計分析（3ファイル）
    analyzer.export_phase3()    # ペルソナ分析（4ファイル）
    analyzer.export_phase6()    # フロー分析（5ファイル：個別+集約エッジ、ノード、近接性、品質）
    analyzer.export_phase7()    # 高度分析（6ファイル）
    analyzer.export_phase8()    # キャリア・学歴分析（6ファイル）
    analyzer.export_phase10()   # 転職意欲・緊急度分析（10ファイル）

    # 5. 統合品質レポート（2ファイル）
    analyzer.generate_overall_quality_report()
```

### 依存モジュール（3つ）

#### 1. DataNormalizer (`data_normalizer.py`)

**機能**: 表記ゆれの正規化

- 年齢・性別の分離: "49歳 女性" → (49, "女性")
- 居住地の分離: "京都府京都市上京区" → ("京都府", "京都市上京区")
- 希望勤務地の解析（カンマ区切り）
- 資格の解析（カンマ区切り）
- キャリア（学歴）の正規化
- 就業状態の正規化

#### 2. DataQualityValidator (`data_quality_validator.py`)

**機能**: データ品質検証

**2つの検証モード**:

| モード | 対象Phase | 特徴 |
|--------|----------|------|
| `descriptive` | Phase 1 | サンプル数1件でも事実として提示可能 |
| `inferential` | Phase 2, 3, 6, 7, 8, 10 | 最小サンプル数: 全体100件、グループ30件 |

**品質スコア基準**:
- **80-100点**: EXCELLENT - そのまま使用可能
- **60-79点**: GOOD - 一部注意が必要
- **40-59点**: ACCEPTABLE - 警告付き提示推奨
- **0-39点**: POOR - 追加データ収集推奨

#### 3. constants (`constants.py`)

**機能**: 定数定義

- `EmploymentStatus`: 就業状態（EMPLOYED, UNEMPLOYED, STUDENT）
- `EducationLevel`: 学歴レベル
- `AgeGroup`: 年齢層
- `Gender`: 性別

---

## ステップ3: データアウトプット

### 出力先

```
C:\Users\fuji1\OneDrive\Pythonスクリプト保管\
job_medley_project\python_scripts\data\output_v2\
```

### Phase別ファイル構成（合計42ファイル）

#### **Phase 1: 基礎集計** (6ファイル)

```
phase1/
├── MapMetrics.csv                     # 地図表示用データ（座標付き）
├── Applicants.csv                     # 申請者基本情報
├── DesiredWork.csv                    # 希望勤務地詳細
├── AggDesired.csv                     # 集計データ
├── P1_QualityReport.csv               # 総合品質レポート
└── P1_QualityReport_Descriptive.csv   # 観察的記述用品質レポート
```

**主要カラム**:
- MapMetrics: `prefecture`, `municipality`, `applicant_count`, `avg_age`, `latitude`, `longitude`
- Applicants: `applicant_id`, `age`, `gender`, `residence_prefecture`, `qualification_count`
- DesiredWork: `applicant_id`, `desired_prefecture`, `desired_municipality`

**検証モード**: Descriptive（観察的記述）

---

#### **Phase 2: 統計分析** (3ファイル)

```
phase2/
├── ChiSquareTests.csv                 # カイ二乗検定結果
├── ANOVATests.csv                     # ANOVA検定結果
└── P2_QualityReport_Inferential.csv   # 推論的考察用品質レポート
```

**検定内容**:
- カイ二乗検定: 性別×年齢層、資格保有×年齢層など
- ANOVA検定: 年齢層間の希望勤務地数の差異など

**検証モード**: Inferential（推論的考察）

---

#### **Phase 3: ペルソナ分析** (4ファイル)

```
phase3/
├── PersonaSummary.csv                 # ペルソナサマリー
├── PersonaDetails.csv                 # ペルソナ詳細
├── PersonaSummaryByMunicipality.csv   # 市町村別ペルソナ分析 🆕
└── P3_QualityReport_Inferential.csv   # 推論的考察用品質レポート
```

**ペルソナ軸**:
- 年齢層、性別、居住都道府県、資格保有、希望勤務地数

**🆕 市町村別ペルソナ分析**:
- **ファイル**: `PersonaSummaryByMunicipality.csv`
- **内容**: 各市町村における年齢層×性別×資格有無のペルソナ分布
- **主要カラム**:
  - `municipality` - 市町村名
  - `persona_name` - ペルソナ名（例: "20代・女性・国家資格あり"）
  - `count` - 人数
  - `market_share_pct` - 市町村内シェア（%）
  - `avg_age`, `avg_desired_areas`, `avg_qualifications`, `employment_rate`

**使用例**:
- 「京都市中京区で働きたい人材のうち、30代女性・国家資格ありは何%か？」
- 「各市町村で最もシェアの高いペルソナは？」

**検証モード**: Inferential（推論的考察）

---

#### **Phase 6: フロー分析** (5ファイル)

```
phase6/
├── MunicipalityFlowEdges.csv          # 自治体間フローエッジ（個別データ）
├── AggregatedFlowEdges.csv            # 集約フローエッジ（Origin→Destination集約）🆕
├── MunicipalityFlowNodes.csv          # 自治体間フローノード
├── ProximityAnalysis.csv              # 移動パターン分析
└── P6_QualityReport_Inferential.csv   # 推論的考察用品質レポート
```

**分析内容**:
- エッジ（個別）: `origin`, `destination`, `applicant_id`, `age`, `gender`（各求職者の移動希望）
- エッジ（集約）: `origin`, `destination`, `flow_count`, `avg_age`, `gender_mode`（Origin→Destinationごと集約）🆕
- ノード: `inflow`, `outflow`, `net_flow`（流入・流出・純流量）
- 近接性: `same_pref_ratio`, `mobility_score`（県内希望率、移動許容度）

**検証モード**: Inferential（推論的考察）

---

#### **Phase 7: 高度分析** (6ファイル)

```
phase7/
├── SupplyDensityMap.csv               # 人材供給密度マップ
├── QualificationDistribution.csv      # 資格別人材分布
├── AgeGenderCrossAnalysis.csv         # 年齢層×性別クロス分析
├── MobilityScore.csv                  # 移動許容度スコアリング
├── DetailedPersonaProfile.csv         # ペルソナ詳細プロファイル
└── P7_QualityReport_Inferential.csv   # 推論的考察用品質レポート
```

**分析内容**:
- 供給密度: `location`, `supply_count`, `avg_age`, `national_license_count`
- 資格分布: `qualification`, `count`, `avg_age`
- 年齢×性別: `age_group`, `gender`, `count`
- 移動許容度: `applicant_id`, `mobility_score`（都道府県外希望率）

**検証モード**: Inferential（推論的考察）

---

#### **Phase 8: キャリア・学歴分析** (6ファイル)

```
phase8/
├── CareerDistribution.csv             # キャリア（学歴）分布
├── CareerAgeCross.csv                 # キャリア×年齢層クロス分析
├── CareerAgeCross_Matrix.csv          # マトリックス形式
├── GraduationYearDistribution.csv     # 卒業年分布（1957-2030）
├── P8_QualityReport.csv               # 総合品質レポート
└── P8_QualityReport_Inferential.csv   # 推論的考察用品質レポート
```

**注意**: ファイル名は「Career」ですが、データは学歴（education）を含みます

**分析内容**:
- キャリア分布: `career`, `count`, `avg_age`, `avg_qualifications`
- キャリア×年齢: `career`, `age_group`, `count`
- 卒業年分布: `graduation_year`, `count`

**検証モード**: Inferential（推論的考察）

---

#### **Phase 10: 転職意欲・緊急度分析** (10ファイル)

```
phase10/
├── UrgencyDistribution.csv                    # 緊急度分布（A-Dランク）
├── UrgencyAgeCross.csv                        # 緊急度×年齢層クロス
├── UrgencyAgeCross_Matrix.csv                 # マトリックス形式
├── UrgencyEmploymentCross.csv                 # 緊急度×就業状態クロス
├── UrgencyEmploymentCross_Matrix.csv          # マトリックス形式
├── UrgencyByMunicipality.csv                  # 市区町村別緊急度分布
├── UrgencyAgeCross_ByMunicipality.csv         # 市区町村別 緊急度×年齢
├── UrgencyEmploymentCross_ByMunicipality.csv  # 市区町村別 緊急度×就業状態
├── P10_QualityReport.csv                      # 総合品質レポート
└── P10_QualityReport_Inferential.csv          # 推論的考察用品質レポート
```

**緊急度スコアリング**:

| 項目 | 配点 |
|------|------|
| 希望勤務地数 | 0-3点 |
| 資格数 | 0-2点 |
| 国家資格保有 | +2点 |
| 就業状態 | 0-2点 |

**合計スコア → ランク分類**:
- **A**: 9-10点（最高緊急度）
- **B**: 6-8点（高緊急度）
- **C**: 3-5点（中緊急度）
- **D**: 0-2点（低緊急度）

**検証モード**: Inferential（推論的考察）

---

#### **統合品質レポート（output_v2ルート）** (3ファイル)

```
output_v2/
├── geocache.json                      # ジオコーディングキャッシュ（1,901件）
├── OverallQualityReport.csv           # 全Phase統合品質レポート
└── OverallQualityReport_Inferential.csv  # 推論的考察用統合レポート
```

---

### ファイル数集計

| Phase | ファイル数 | 検証モード |
|-------|----------|----------|
| Phase 1 | 6ファイル | Descriptive |
| Phase 2 | 3ファイル | Inferential |
| Phase 3 | 4ファイル | Inferential |
| Phase 6 | 5ファイル | Inferential |
| Phase 7 | 6ファイル | Inferential |
| Phase 8 | 6ファイル | Inferential |
| Phase 10 | 10ファイル | Inferential |
| 統合 | 3ファイル | - |
| **合計** | **42ファイル** | - |

---

## ステップ4: GAS連携・可視化

### GAS主要スクリプト（16ファイル）

#### データインポート

- **DataImportAndValidation.gs** - 統合データインポート・検証
  - `batchImportPythonResults()` - Python結果一括インポート
  - `importPythonCSVDialog()` - 個別CSVインポート

- **UnifiedDataImporter.gs** - Phase別データインポーター
  - `importPhase7Data()` - Phase 7専用
  - `importPhase8Data()` - Phase 8専用
  - `importPhase10Data()` - Phase 10専用

#### 可視化

- **Phase1-6UnifiedVisualizations.gs** - Phase 1-6統合可視化
- **Phase7UnifiedVisualizations.gs** - Phase 7統合可視化（6タブ）
- **Phase8UnifiedVisualizations.gs** - Phase 8統合可視化（4機能）
- **Phase10UnifiedVisualizations.gs** - Phase 10統合可視化（5機能）
- **MapVisualization.gs** - 地図可視化（バブル・ヒートマップ）

#### データ管理・UI

- **MenuIntegration.gs** - メニュー統合（全Phase対応）
- **DataServiceProvider.gs** - データサービス提供
- **DataManagementUtilities.gs** - データ管理ユーティリティ
- **QualityAndRegionDashboards.gs** - 品質・地域ダッシュボード
- **PersonaDifficultyChecker.gs** - ペルソナ難易度分析

### GASメニュー構成

```
📊 データ処理
│
├── 📥 データインポート
│   ├── 🎯 Python結果を自動インポート（推奨）
│   ├── 📁 フォルダを指定してインポート
│   └── ⚡ CSVファイルを個別アップロード
│
├── 🗺️ 地図表示
│   ├── 🗺️ 地図表示（バブル）
│   └── 📍 地図表示（ヒートマップ）
│
├── 📈 統計分析・ペルソナ（Phase 2-3）
│   ├── 🔬 カイ二乗検定結果
│   ├── 📊 ANOVA検定結果
│   ├── 👥 ペルソナサマリー
│   ├── 📋 ペルソナ詳細
│   └── 🎯 ペルソナ難易度確認
│
├── 🌊 フロー・移動パターン分析（Phase 6）
│   ├── 🔀 自治体間フロー分析
│   └── 🎯 フロー・移動統合ビュー
│
├── 📈 Phase 7: 高度分析
│   ├── 📊 個別分析（5機能）
│   └── 🎯 Phase 7統合ダッシュボード
│
├── 🎓 Phase 8: キャリア・学歴分析
│   ├── 📊 個別分析（4機能）
│   └── 🎯 Phase 8統合ダッシュボード
│
├── 🚀 Phase 10: 転職意欲・緊急度分析
│   ├── 📊 個別分析（5機能）
│   └── 🎯 Phase 10統合ダッシュボード
│
└── ✅ 品質管理
    ├── 📊 品質ダッシュボード
    ├── ✅ データ検証レポート
    └── 🔍 Phase品質比較
```

---

## 実行手順

### ステップ1: Python分析実行

```bash
cd "C:\Users\fuji1\OneDrive\Pythonスクリプト保管\job_medley_project\python_scripts"
python run_complete_v2_perfect.py
```

### ステップ2: GUIでCSV選択

- デフォルトディレクトリ: `out/`
- ファイル選択: `results_20251027_180947.csv`

### ステップ3: 自動処理（約30秒-1分）

```
[LOAD] データ読み込み
[NORMALIZE] データ正規化
[PROCESS] データ処理

[PHASE1] Phase 1: 基礎集計 → 6ファイル出力
[PHASE2] Phase 2: 統計分析 → 3ファイル出力
[PHASE3] Phase 3: ペルソナ分析 → 4ファイル出力
[PHASE6] Phase 6: フロー分析 → 5ファイル出力（個別+集約エッジ、ノード、近接性、品質）
[PHASE7] Phase 7: 高度分析 → 6ファイル出力
[PHASE8] Phase 8: キャリア・学歴分析 → 6ファイル出力
[PHASE10] Phase 10: 転職意欲・緊急度分析 → 10ファイル出力
[統合品質レポート] → 2ファイル出力

合計: 42ファイル出力完了✅
```

### ステップ4: GASインポート

```
GASメニュー: 📥 データインポート
    → 🎯 Python結果を自動インポート（推奨）
    → フォルダ選択: data/output_v2/
    → 全Phaseのシート自動作成・更新
```

### ステップ5: GAS可視化

各Phase統合ダッシュボードを使用：

- 🎯 Phase 7統合ダッシュボード（6タブ統合UI）
- 🎯 Phase 8統合ダッシュボード（4機能）
- 🎯 Phase 10統合ダッシュボード（5機能）
- 📊 品質ダッシュボード（Phase比較）

---

## 重要なポイント

### run_complete_v2_perfect.pyの特徴

1. **完全な依存モジュール統合**
   - DataNormalizer（表記ゆれ正規化）
   - DataQualityValidator（品質検証）
   - constants（定数定義）

2. **2つの品質検証モード**
   - Descriptive（観察的記述）: Phase 1
   - Inferential（推論的考察）: Phase 2, 3, 6, 7, 8, 10

3. **市区町村座標データ優先**
   - `municipality_coords.csv`から座標取得
   - geocache.jsonでキャッシュ
   - Google Maps APIフォールバック

4. **品質ゲートチェック**
   - 各Phase実行前に品質スコア算出
   - 基準未満の場合はスキップ可能

5. **Phase 3の新機能**
   - `PersonaSummaryByMunicipality.csv` - 市町村別ペルソナ分析
   - 市町村内シェア（market_share_pct）を算出

6. **Phase 8のファイル名**
   - コード内: `_generate_education_distribution()`
   - 実際の出力: `CareerDistribution.csv`
   - データ内容: 学歴（education）を含む

### 現在の品質スコア（実測値）

- **Phase 1**: 82.0/100点 (EXCELLENT)
- **Phase 8**: 70.0/100点 (GOOD)
- **Phase 10**: 90.0/100点 (EXCELLENT)
- **統合**: 82.86/100点 (EXCELLENT)

---

## トラブルシューティング

### よくある問題

**問題1**: Phase 3で4ファイルではなく3ファイルしか出力されない

**原因**: `PersonaSummaryByMunicipality.csv`は条件付き生成

**解決方法**:
- `DesiredWork.csv`が正しく生成されているか確認
- 市町村別データが存在するか確認

---

**問題2**: GASインポートでエラーが発生

**原因**: ファイルパスまたはフォルダ構造の問題

**解決方法**:
- `data/output_v2/`ディレクトリが存在することを確認
- 各Phaseフォルダ（phase1, phase2, ...）が存在することを確認

---

**問題3**: 品質スコアが低い

**原因**: サンプルサイズ不足

**解決方法**:
- より多くのデータを収集
- Phase別に警告メッセージを確認
- 品質レポートCSVで詳細を確認

---

## 関連ドキュメント

- **[DATA_USAGE_GUIDELINES.md](DATA_USAGE_GUIDELINES.md)** - データ利用ガイドライン
- **[RUN_COMPLETE_V2_PERFECT_IMPLEMENTATION.md](RUN_COMPLETE_V2_PERFECT_IMPLEMENTATION.md)** - 実装詳細
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - アーキテクチャ設計
- **[GAS_COMPLETE_FEATURE_LIST.md](GAS_COMPLETE_FEATURE_LIST.md)** - GAS機能一覧

---

**更新履歴**:
- 2025/11/01: 初版作成（run_complete_v2_perfect.pyベース、42ファイル対応）
