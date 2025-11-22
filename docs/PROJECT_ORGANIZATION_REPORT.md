# プロジェクト整理レポート

**作成日**: 2025年11月13日
**目的**: プロジェクト全体の棚卸しと整理指針の策定
**ステータス**: 🔍 分析完了

---

## 📊 プロジェクト現状サマリー

### 基本情報

| 項目 | 値 |
|------|-----|
| **総ディレクトリ数** | 48個 |
| **総ドキュメント数** | 164個（プロジェクトルート25 + docs 139） |
| **総容量** | 約220MB（reflex_app 173MB含む） |
| **Git管理ファイル** | 変更30件、削除30件 |
| **Python実装** | 4種類（メイン、Streamlit、Reflex、Dash） |
| **GAS実装** | 3種類（gas_deployment、gas_files、gas_files_production） |

---

## 🗂️ ディレクトリ構成分析

### Phase 1: コアシステム（本番稼働中）

#### Python データ処理
```
python_scripts/                          20MB
├── run_complete_v2_perfect.py          # メインスクリプト（1,903行、85KB）✅
├── data/
│   └── output_v2/                      # Phase 1-10出力（43ファイル）✅
│       ├── phase1/ (11ファイル)
│       ├── phase2/ (3ファイル)
│       ├── phase3/ (4ファイル)
│       ├── phase6/ (5ファイル)
│       ├── phase7/ (6ファイル)
│       ├── phase8/ (6ファイル)
│       ├── phase10/ (10ファイル)
│       └── mapcomplete_complete_sheets/
│           └── MapComplete_Complete_All_FIXED.csv (20,590行)✅
└── tests/                              # テストスイート
```

**ステータス**: ✅ 完璧に動作、品質スコア82.86/100

#### GAS 本番環境
```
gas_deployment/                          3.0MB
├── MapCompleteDataBridge.gs            # 最新バグ修正版
├── PersonaLevelDataBridge.gs           # 高速化実装
├── RegionStateService.gs               # 地域別ダッシュボード
├── RegionDashboard.gs
├── MenuIntegration.gs
├── UnifiedDataImporter.gs
├── map_complete_integrated.html        # Phase 12-14統合（Phase 5実装待ち）
└── *.gs (15ファイル)
```

**ステータス**: 🟡 動作中、Phase 5改善待ち（7タスク）

---

### Phase 2: Web移行プロジェクト（並列開発中）

#### Streamlit実装（完了）
```
streamlit_app/                           81KB
├── complete_dashboard.py               # 10タブ完全実装（200行）✅
├── streamlit_dashboard.py
├── streamlit_dashboard_with_map.py
└── README_COMPLETE.md
```

**ステータス**: ✅ 完全実装済み、本番デプロイ可能

#### Reflex実装（30%完了）
```
reflex_app/                              173MB
├── mapcomplete_dashboard/
│   └── mapcomplete_dashboard.py        # MVP実装（150行）🔄
├── MapComplete_Complete_All_FIXED.csv
├── geocache.json
├── requirements.txt
└── rxconfig.py
```

**ステータス**: 🔄 MVP完了（CSVロード+サマリー）、10タブ実装待ち

#### Dash実装（10%完了）
```
dash_app/                                22KB
├── app.py                              # MVP実装（260行）🔄
├── requirements.txt
└── README.md
```

**ステータス**: 🔄 MVP完了（CSVロード+サマリー）、10タブ実装待ち

---

### Phase 3: レガシー・アーカイブ

#### 削除推奨（高優先度）

##### 1. 重複GASディレクトリ
```
gas_files/                               4.4MB ❌ 削除推奨
gas_files_production/                    490KB ❌ 削除推奨
```

**理由**: `gas_deployment/` に統合済み

**推奨アクション**:
```bash
mkdir -p archive/old_gas_files
mv gas_files archive/old_gas_files/
mv gas_files_production archive/old_gas_files/
```

##### 2. 旧出力ディレクトリ
```
gas_output_phase1/                       3.1MB ❌ 削除推奨
gas_output_phase2/                       5.0KB ❌ 削除推奨
gas_output_phase3/                       5.0KB ❌ 削除推奨
gas_output_phase6/                       1.6MB ❌ 削除推奨
```

**理由**: `python_scripts/data/output_v2/` に統合済み

**推奨アクション**:
```bash
mkdir -p archive/old_gas_output
mv gas_output_phase* archive/old_gas_output/
```

##### 3. プロジェクトルートのレガシーMDファイル（25個）
```
プロジェクトルート/*.md                  25ファイル ❌ 整理推奨
├── COMPLETE_TEST_REPORT.md
├── CORRECTION_PLAN.md
├── DEPLOYMENT_ACTION_PLAN.md
├── GAS_E2E_TEST_REPORT_FINAL.md
├── ULTRATHINK_REVIEW.md
└── ...（20個以上）
```

**理由**: docs/ に統合すべき

**推奨アクション**:
```bash
mkdir -p docs/archive_legacy_reports
mv *.md docs/archive_legacy_reports/
# ただし README.md は除外
mv docs/archive_legacy_reports/README.md ./
```

##### 4. 旧テストファイル
```
test_gas_enhancement.py                  7KB ❌ 削除推奨
test_gas_enhancement_comprehensive.py    39KB ❌ 削除推奨
test_phase7_complete.py                  10KB ❌ 削除推奨
```

**理由**: `tests/` ディレクトリに統合済み

**推奨アクション**:
```bash
mkdir -p tests/archive_old_tests
mv test_*.py tests/archive_old_tests/
```

---

### Phase 4: ドキュメント整理

#### docs/ ディレクトリ（139ファイル、3.1MB）

**課題**: ドキュメントが多すぎて探しにくい

**推奨構造**:
```
docs/
├── 00_PROJECT_OVERVIEW/              # プロジェクト概要（最重要）
│   ├── README.md                     # プロジェクト全体説明
│   ├── QUICK_START.md                # クイックスタートガイド
│   └── ARCHITECTURE.md               # アーキテクチャ
│
├── 01_PYTHON/                        # Python実装ドキュメント
│   ├── RUN_COMPLETE_V2_PERFECT_IMPLEMENTATION.md
│   ├── DATA_USAGE_GUIDELINES.md
│   └── PHASE*_IMPLEMENTATION.md
│
├── 02_GAS/                           # GAS実装ドキュメント
│   ├── GAS_COMPLETE_FEATURE_LIST.md
│   ├── MAPCOMPLETE_INTEGRATION_DEBUG_REPORT.md
│   └── REGIONAL_DASHBOARD_*.md
│
├── 03_WEB_MIGRATION/                 # Web移行プロジェクト
│   ├── PARALLEL_DEVELOPMENT_MASTER_PLAN.md  # 最新
│   ├── REQUIREMENTS_SPECIFICATION.md
│   ├── IMPLEMENTATION_GUIDE.md
│   ├── DASHBOARD_MIGRATION_PLAN.md
│   ├── WEB_FRAMEWORK_COMPARISON.md
│   └── PERSONA_LEVEL_INTEGRATION_GUIDE.md
│
├── 04_TEST_REPORTS/                  # テストレポート
│   ├── WORK_COMPLETION_REPORT_20251030.md
│   ├── GAS_E2E_TEST_REPORT.md
│   └── TEST_RESULTS_*.md
│
├── 05_ARCHIVE/                       # アーカイブ（古いドキュメント）
│   ├── legacy_reports/
│   ├── old_specifications/
│   └── deprecated/
│
└── 99_MAINTENANCE/                   # メンテナンス
    ├── PROJECT_ORGANIZATION_REPORT.md  # 本ドキュメント
    └── CLEANUP_SCRIPTS.md
```

---

## 🎯 整理アクションプラン

### 優先度A: 即座に実行（データ損失リスクなし）

#### A-1: レガシーファイルのアーカイブ化
```bash
# アーカイブディレクトリ作成
mkdir -p archive/old_gas_files
mkdir -p archive/old_gas_output
mkdir -p archive/legacy_reports
mkdir -p tests/archive_old_tests

# ファイル移動
mv gas_files archive/old_gas_files/
mv gas_files_production archive/old_gas_files/
mv gas_output_phase* archive/old_gas_output/
mv test_gas_*.py tests/archive_old_tests/
mv test_phase7_complete.py tests/archive_old_tests/

# プロジェクトルートのMDファイル整理
mkdir -p docs/archive_legacy_reports
mv COMPLETE_TEST_REPORT.md docs/archive_legacy_reports/
mv CORRECTION_PLAN.md docs/archive_legacy_reports/
mv DEPLOYMENT_ACTION_PLAN.md docs/archive_legacy_reports/
mv GAS_E2E_TEST_REPORT_FINAL.md docs/archive_legacy_reports/
mv GAS_ENHANCEMENT_*.md docs/archive_legacy_reports/
mv OPTION*.md docs/archive_legacy_reports/
mv PHASE*.md docs/archive_legacy_reports/
mv PRODUCTION_READINESS_CRITICAL_ANALYSIS.md docs/archive_legacy_reports/
mv SIMPLIFIED_TEST_PROCEDURE.md docs/archive_legacy_reports/
mv ULTRATHINK_*.md docs/archive_legacy_reports/
mv GAS新規作成手順書.md docs/archive_legacy_reports/
mv GAS統合テスト完全版レポート.md docs/archive_legacy_reports/
mv MISSING_FUNCTIONS_REPORT.md docs/archive_legacy_reports/

# gitignore更新
echo "archive/" >> .gitignore
echo "tests/archive_old_tests/" >> .gitignore
```

**推定削減容量**: 約10MB
**推定削減ファイル数**: 約35ファイル

---

#### A-2: 不要な一時ファイル削除
```bash
# 一時ファイル削除
rm -f nul
rm -f _tmp.py
rm -f *.log

# キャッシュディレクトリ削除
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type d -name ".pytest_cache" -exec rm -rf {} +

# reflex_appの.webディレクトリ（173MBの大部分）
cd reflex_app
rm -rf .web
cd ..
```

**推定削減容量**: 約170MB

---

### 優先度B: docs/ ディレクトリの再構成（要慎重）

#### B-1: カテゴリ別ディレクトリ作成
```bash
cd docs
mkdir -p 00_PROJECT_OVERVIEW
mkdir -p 01_PYTHON
mkdir -p 02_GAS
mkdir -p 03_WEB_MIGRATION
mkdir -p 04_TEST_REPORTS
mkdir -p 05_ARCHIVE
mkdir -p 99_MAINTENANCE
```

#### B-2: ファイル分類・移動（手動推奨）
**理由**: ファイル名だけでは分類困難、内容確認が必要

**推奨手順**:
1. 各カテゴリの最重要ドキュメント5-10個を手動配置
2. 残りは `05_ARCHIVE/uncategorized/` に一時配置
3. 必要に応じて段階的に整理

---

### 優先度C: Git管理の整理

#### C-1: 現在のgit状態確認
```bash
git status --short
# M: 変更30件
# D: 削除30件（gas_import_completeディレクトリ）
```

#### C-2: 不要な削除ファイルをgitから除外
```bash
# 削除されたファイルをステージング
git add python_scripts/data/output_v2/gas_import_complete/

# または全て除外
git rm -r python_scripts/data/output_v2/gas_import_complete/
```

#### C-3: .gitignore更新
```bash
cat >> .gitignore << 'EOF'

# アーカイブディレクトリ
archive/

# 一時ファイル
nul
_tmp.py
*.log

# Pythonキャッシュ
__pycache__/
.pytest_cache/

# Reflex生成ファイル
reflex_app/.web/
reflex_app/.states/

# Dash一時ファイル
dash_app/__pycache__/

# データファイル（サイズ大）
*.csv
geocache.json
EOF
```

---

## 📈 整理後の期待効果

### ディスク容量
- **整理前**: 約220MB
- **整理後**: 約40MB
- **削減率**: 約82%削減

### ファイル数
- **整理前**: 200+ファイル
- **整理後**: 約120ファイル（アクティブ）
- **削減率**: 約40%削減

### 検索性
- ドキュメント探索時間: 5分 → 30秒（90%削減）
- カテゴリ別整理により目的のファイルが即座に発見可能

---

## ✅ 実行チェックリスト

### ステップ1: バックアップ
- [ ] プロジェクト全体を外部にバックアップ
- [ ] git commitで現在の状態を保存

### ステップ2: レガシーファイル整理（優先度A）
- [ ] gas_files, gas_files_production をアーカイブ
- [ ] gas_output_phase* をアーカイブ
- [ ] プロジェクトルートの古いMDファイルをdocs/archive/へ
- [ ] 古いテストファイルをtests/archive/へ

### ステップ3: 一時ファイル削除（優先度A）
- [ ] nul, _tmp.py, *.log削除
- [ ] __pycache__, .pytest_cache削除
- [ ] reflex_app/.web削除

### ステップ4: Git管理整理（優先度C）
- [ ] .gitignore更新
- [ ] 削除ファイルのステージング
- [ ] git commit -m "プロジェクト整理: レガシーファイルのアーカイブ化"

### ステップ5: docs/ 再構成（優先度B）
- [ ] カテゴリ別ディレクトリ作成
- [ ] 重要ドキュメント10個を手動配置
- [ ] 残りをuncategorizedに一時配置

---

## 🚨 注意事項

### 絶対に削除してはいけないファイル・ディレクトリ

1. **python_scripts/data/output_v2/** - 本番データ出力
2. **gas_deployment/** - GAS本番環境
3. **reflex_app/mapcomplete_dashboard/** - Reflex実装
4. **dash_app/app.py** - Dash実装
5. **streamlit_app/complete_dashboard.py** - Streamlit実装
6. **docs/PARALLEL_DEVELOPMENT_MASTER_PLAN.md** - 最新計画書
7. **README.md** - プロジェクト説明

### 削除前の確認事項

- [ ] 該当ファイルが他のスクリプトから参照されていないか確認
- [ ] git historyから復元可能か確認
- [ ] バックアップが存在するか確認

---

## 🎯 次のステップ

### オプション1: 自動整理スクリプト実行
**推奨**: 安全性重視

```bash
# 整理スクリプト作成・実行
# （別途作成）
```

### オプション2: 手動整理
**推奨**: 慎重派向け

上記のチェックリストに従って、1つずつ確認しながら実行

### オプション3: 段階的整理
**推奨**: リスク最小化

1. **Week 1**: 優先度A（レガシーファイル整理）のみ実行
2. **Week 2**: Git管理整理
3. **Week 3**: docs/ 再構成

---

**最終更新**: 2025年11月13日
**次回レビュー**: 整理実行後
