# プロジェクト構造詳細

**バージョン**: 3.0 (Reflex統合版)
**最終更新**: 2025年11月22日
**ステータス**: 本番運用可能 ✅

このドキュメントでは、ジョブメドレー求職者データ分析・可視化システムの詳細なフォルダ構造とファイル配置を説明します。

---

## 📁 ルートディレクトリ構成

クリーンアップ後のプロジェクトルート（11項目のみ）：

```
job_medley_project/
├── python_scripts/          # V3 CSV生成エンジン（Pythonスクリプト集）
├── reflex_app/              # Reflexダッシュボード（Webアプリケーション）
├── data/                    # データファイル（入力・出力・キャッシュ）
├── docs/                    # プロジェクトドキュメント
├── archive_old_files/       # アーカイブ（380ファイル、14MB）
├── geocache.json            # ジオコーディングキャッシュ（ルート保管用）
├── pytest.ini               # pytest設定ファイル
├── requirements.txt         # Python依存パッケージ（Reflex用）
├── render.yaml              # Render.com デプロイ設定
├── README.md                # プロジェクトメインドキュメント
└── README_LOCAL.md          # ローカル開発環境用README
```

---

## 🔬 python_scripts/ - V3 CSV生成エンジン

Pythonスクリプトによるデータ分析・CSV生成を行うディレクトリ。

```
python_scripts/
│
├── 【V3メインスクリプト】
│   ├── run_complete_v2_perfect.py      # V2.2 MAP統合版（Phase 1-3, 6-8, 10, 12-14）
│   ├── run_complete_v3.py              # V3拡張版（将来用）
│   └── run_complete_v2_legacy.py       # V2レガシー版（参照用）
│
├── 【分析エンジン】
│   ├── phase7_advanced_analysis.py     # Phase 7高度分析エンジン
│   ├── generate_mapcomplete_prefecture_sheets.py   # 都道府県別シート生成
│   ├── generate_mapcomplete_complete_sheets.py     # 統合シート生成
│   └── generate_persona_level_sheets.py            # ペルソナレベルシート生成
│
├── 【データ処理モジュール】
│   ├── data_normalizer.py              # データ正規化（表記ゆれ対応）
│   ├── data_quality_validator.py       # データ品質検証
│   └── constants.py                    # 定数定義（雇用形態、学歴、年齢層等）
│
├── 【テストファイル】
│   ├── comprehensive_test_suite_v3.py  # 270テスト（4階層×27テスト×10回）
│   ├── generate_test_report.py         # テストレポート生成
│   └── final_validation.py             # 最終検証スクリプト
│
├── 【アーカイブ】
│   └── archive_old_scripts/            # 旧デバッグ・修正スクリプト（15ファイル、256KB）
│       ├── debug_flow_data.py
│       ├── debug_gap_generation.py
│       ├── debug_phase7.py
│       ├── fix_all_bugs.py
│       ├── fix_gap_calculation.py
│       ├── fix_print_statements.py
│       ├── fix_stdout_issue.py
│       ├── validate_v3_rowtype.py
│       └── run_complete_v2*.py（5バックアップファイル）
│
└── 【データ検証・分析結果】
    ├── test_results_v3_comprehensive.json   # V3テスト結果JSON
    ├── analysis_results_complete.json       # 完全分析結果
    └── processed_data_complete.csv          # 処理済みデータ完全版
```

---

## 🌐 reflex_app/ - Reflexダッシュボード

Reflexフレームワークを使用したWebダッシュボードアプリケーション。

```
reflex_app/
│
├── mapcomplete_dashboard/              # メインダッシュボードモジュール
│   ├── __init__.py                     # パッケージ初期化
│   ├── mapcomplete_dashboard.py        # メインダッシュボード（10パネル、1,800行）
│   ├── auth.py                         # 認証ロジック（AuthState、ドメイン検証）
│   ├── login.py                        # ログインページUI
│   └── db_helper.py                    # データベース接続（Turso統合）
│
├── docs/                               # Reflexアプリ専用ドキュメント
│   ├── DOMAIN_AUTHENTICATION_GUIDE.md  # ドメイン制限認証ガイド（492行）
│   ├── TURSO_DATABASE_INTEGRATION.md   # Tursoデータベース統合ガイド
│   └── DEPLOYMENT_GUIDE.md             # デプロイガイド
│
├── scripts/                            # ユーティリティスクリプト
│   └── turso_setup.py                  # Tursoセットアップスクリプト
│
├── tests/                              # テストファイル
│   ├── test_dashboard_e2e.py           # E2Eテスト
│   └── test_dashboard_state.py         # State管理テスト
│
├── .gitignore                          # Git除外設定
├── .env                                # 環境変数（Git管理外）
├── requirements.txt                    # Python依存パッケージ
├── rxconfig.py                         # Reflex設定ファイル
└── README.md                           # Reflexアプリ README
```

### .env 環境変数構成

```env
# ドメイン制限認証設定
ALLOWED_DOMAINS=f-a-c.co.jp,cyxen.co.jp
AUTH_PASSWORD=cyxen_2025_12_01
SESSION_SECRET=[64文字の秘密鍵]

# Tursoクラウドデータベース設定
TURSO_DATABASE_URL=libsql://job-jobseekeranalyzer-makimaki1006.aws-ap-northeast-1.turso.io
TURSO_AUTH_TOKEN=[JWT認証トークン]
```

---

## 💾 data/ - データファイル

入力データ、出力データ、キャッシュファイルを格納。

```
data/
│
├── input/                              # 入力CSVファイル（未使用、将来用）
│
├── output_v2/                          # V2/V3出力データ（現行）
│   │
│   ├── phase1/                         # Phase 1: 基礎集計（6ファイル）
│   │   ├── Applicants.csv              # 申請者基本情報
│   │   ├── DesiredWork.csv             # 希望勤務地詳細
│   │   ├── AggDesired.csv              # 希望勤務地集計
│   │   ├── MapMetrics.csv              # 地図表示用データ（座標付き）
│   │   ├── P1_QualityReport.csv        # 品質レポート
│   │   └── P1_QualityReport_Descriptive.csv  # 観察的記述用品質レポート
│   │
│   ├── phase2/                         # Phase 2: 統計分析（3ファイル）
│   │   ├── ChiSquareTests.csv          # カイ二乗検定結果
│   │   ├── ANOVATests.csv              # ANOVA検定結果
│   │   └── P2_QualityReport_Inferential.csv  # 推論的考察用品質レポート
│   │
│   ├── phase3/                         # Phase 3: ペルソナ分析（4ファイル）
│   │   ├── PersonaSummary.csv          # ペルソナサマリー
│   │   ├── PersonaDetails.csv          # ペルソナ詳細
│   │   ├── PersonaSummaryByMunicipality.csv  # 市町村別ペルソナ分析
│   │   └── P3_QualityReport_Inferential.csv  # 推論的考察用品質レポート
│   │
│   ├── phase6/                         # Phase 6: フロー分析（5ファイル）
│   │   ├── MunicipalityFlowEdges.csv   # 自治体間フローエッジ
│   │   ├── AggregatedFlowEdges.csv     # 集約フローエッジ
│   │   ├── MunicipalityFlowNodes.csv   # 自治体間フローノード
│   │   ├── ProximityAnalysis.csv       # 移動パターン分析
│   │   └── P6_QualityReport_Inferential.csv  # 推論的考察用品質レポート
│   │
│   ├── phase7/                         # Phase 7: 高度分析（6ファイル）
│   │   ├── SupplyDensityMap.csv        # 人材供給密度マップ
│   │   ├── QualificationDistribution.csv     # 資格別人材分布
│   │   ├── AgeGenderCrossAnalysis.csv  # 年齢層×性別クロス分析
│   │   ├── MobilityScore.csv           # 移動許容度スコアリング
│   │   ├── DetailedPersonaProfile.csv  # ペルソナ詳細プロファイル
│   │   └── P7_QualityReport_Inferential.csv  # 推論的考察用品質レポート
│   │
│   ├── phase8/                         # Phase 8: キャリア・学歴分析（6ファイル）
│   │   ├── CareerDistribution.csv      # キャリア分布
│   │   ├── CareerAgeCross.csv          # キャリア×年齢クロス集計
│   │   ├── CareerAgeCross_Matrix.csv   # キャリア×年齢マトリクス
│   │   ├── GraduationYearDistribution.csv    # 卒業年分布
│   │   ├── P8_QualityReport.csv        # 品質レポート
│   │   └── P8_QualityReport_Inferential.csv  # 推論的考察用品質レポート
│   │
│   ├── phase10/                        # Phase 10: 転職意欲・緊急度分析（10ファイル）
│   │   ├── UrgencyDistribution.csv     # 緊急度分布
│   │   ├── UrgencyAgeCross.csv         # 緊急度×年齢クロス集計
│   │   ├── UrgencyAgeCross_Matrix.csv  # 緊急度×年齢マトリクス
│   │   ├── UrgencyEmploymentCross.csv  # 緊急度×就業状況クロス集計
│   │   ├── UrgencyEmploymentCross_Matrix.csv  # 緊急度×就業状況マトリクス
│   │   ├── UrgencyByMunicipality.csv   # 市区町村別緊急度
│   │   ├── UrgencyAgeCross_ByMunicipality.csv          # 市区町村別緊急度×年齢
│   │   ├── UrgencyEmploymentCross_ByMunicipality.csv   # 市区町村別緊急度×就業状況
│   │   ├── P10_QualityReport.csv       # 品質レポート
│   │   └── P10_QualityReport_Inferential.csv  # 推論的考察用品質レポート
│   │
│   ├── phase12/                        # Phase 12: 需給ギャップ分析（2ファイル）
│   │   ├── Phase12_SupplyDemandGap.csv # 需給ギャップ分析
│   │   └── P12_QualityReport_Descriptive.csv  # 観察的記述用品質レポート
│   │
│   ├── phase13/                        # Phase 13: 希少性スコア（2ファイル）
│   │   ├── Phase13_RarityScore.csv     # 希少性スコアリング
│   │   └── P13_QualityReport_Descriptive.csv  # 観察的記述用品質レポート
│   │
│   ├── phase14/                        # Phase 14: 競合分析（2ファイル）
│   │   ├── Phase14_CompetitionProfile.csv    # 人材プロファイル
│   │   └── P14_QualityReport_Descriptive.csv  # 観察的記述用品質レポート
│   │
│   ├── mapcomplete_complete_sheets/    # MAP統合シート（都道府県別）
│   │   └── [都道府県名]_Complete.csv（48ファイル）
│   │
│   ├── persona_level_sheets/           # ペルソナレベルシート
│   │   └── [ペルソナID]_Profile.csv
│   │
│   ├── geocache.json                   # ジオコーディングキャッシュ（1,901件）
│   ├── OverallQualityReport.csv        # 統合品質レポート
│   └── OverallQualityReport_Inferential.csv  # 統合推論的品質レポート
│
├── municipality_coords.csv             # 市区町村座標マスターデータ
│
└── archive/                            # アーカイブ（旧データ保管）
    └── output_v1/                      # V1出力データ（387KB、参照用）
```

**合計CSV出力**: 43ファイル（Phase別39 + 統合3 + マスター1）
**品質スコア**: 82.86/100 (EXCELLENT)

---

## 📚 docs/ - プロジェクトドキュメント

プロジェクトに関する各種ドキュメント。

```
docs/
│
├── 【メインドキュメント】
│   ├── PROJECT_STRUCTURE.md            # このファイル
│   ├── V3_CSV_SPECIFICATION.md         # V3 CSV完全仕様
│   ├── REFLEX_APP_GUIDE.md             # Reflexアプリ完全ガイド
│   ├── DATA_USAGE_GUIDELINES.md        # データ利用ガイドライン
│   └── CLEANUP_REPORT_V3.md            # クリーンアップレポート（2025-11-22）
│
├── 【アーキテクチャ・仕様】
│   ├── ARCHITECTURE.md                 # システムアーキテクチャ
│   ├── DATA_SPECIFICATION.md           # データ仕様書
│   └── CODE_REFERENCE.md               # コードリファレンス
│
├── 【テスト・検証】
│   ├── FINAL_TEST_REPORT.md            # 最終テストレポート
│   ├── TEST_RESULTS_2025-10-26_FINAL.md      # Phase 7テスト結果
│   └── CRITICAL_VERIFICATION_REPORT.md # 重要検証レポート
│
├── 【GAS関連（アーカイブ参照用）】
│   ├── GAS_INTEGRATION_CHECKLIST.md    # GAS統合チェックリスト
│   ├── GAS_COMPLETE_FEATURE_LIST.md    # GAS完全機能一覧（50ページ）
│   └── GAS_E2E_TEST_REPORT.md          # GAS E2Eテスト結果
│
└── 【その他100+ドキュメント】
    ├── Phase実装関連（PHASE*.md）
    ├── バグ修正関連（BUGFIX*.md、FIX*.md）
    ├── 品質改善関連（QUALITY*.md、IMPROVEMENT*.md）
    └── ハンドオーバー関連（HANDOVER*.md）
```

**注**: 大部分のドキュメントはGAS統合時代の資料であり、現在のReflex統合版では参照用となっています。

---

## 🗃️ archive_old_files/ - アーカイブ

クリーンアップにより整理されたファイル群（380ファイル、14MB）。

```
archive_old_files/
│
├── old_gas/                            # 旧GAS関連フォルダ（6フォルダ）
│   ├── gas_deployment/                 # GAS本番デプロイ用
│   ├── gas_deployment_reflex/          # Reflex統合試作版
│   ├── gas_files/                      # GASファイル開発版
│   ├── gas_files_production/           # GAS本番ファイル
│   ├── gas_test/                       # GASテストファイル
│   └── apps_script_bundle/             # Apps Scriptバンドル
│
├── old_docs/                           # 旧ドキュメント（約20個）
│   ├── COMPLETE_TEST_REPORT.md
│   ├── GAS_ENHANCEMENT_PLAN.md
│   ├── PHASE7_FIX_SUMMARY.md
│   └── [その他18ファイル]
│
├── old_tests/                          # 旧テストファイル（3個）
│   ├── test_gas_enhancement.py
│   ├── test_gas_enhancement_comprehensive.py
│   └── test_phase7_complete.py
│
├── old_apps/                           # 旧Webアプリ（11ファイル）
│   ├── streamlit_app/                  # Streamlit実装（7ファイル）
│   │   ├── complete_dashboard.py
│   │   ├── streamlit_dashboard.py
│   │   └── [その他5ファイル]
│   └── dash_app/                       # Dash実装（4ファイル）
│       ├── app.py
│       ├── requirements.txt
│       └── [その他2ファイル]
│
├── old_misc/                           # その他の旧ファイル
│   ├── 一時ファイル（_tmp.py, nul等）
│   ├── JSONレポート（GAS_E2E_TEST_10X_RESULTS.json等）
│   ├── 古いフォルダ（archive, temp, tools, dist, claudedocs, tests）
│   └── [その他350+ファイル]
│
└── gas_deployment/                     # GAS修正スクリプト・バックアップ（7ファイル）
    ├── fix_optional_chaining.py
    ├── fix_optional_chaining_final.py
    ├── fix_optional_safe.py
    ├── fix_remaining.sh
    ├── map_complete_integrated.html.backup
    ├── map_complete_integrated.html.bak3
    └── MapCompleteDataBridge.gs.backup_20251112_141610
```

**アーカイブ理由**:
- GAS統合からReflex統合への移行完了
- Streamlit/Dash実装は非現行化（Reflexに統合）
- デバッグ・修正スクリプトは役割を終えた
- 参照用として保管（6ヶ月後に削除検討）

---

## 🔑 重要ファイル詳細

### run_complete_v2_perfect.py
- **行数**: 1,903行
- **サイズ**: 85KB
- **機能**: Phase 1-3, 6-8, 10, 12-14の全CSVファイル生成
- **出力**: 43ファイル
- **品質スコア**: 82.86/100 (EXCELLENT)
- **特徴**: データ正規化、品質検証、外れ値フィルタリング統合

### mapcomplete_dashboard.py
- **行数**: 約1,800行
- **機能**: 10パネル統合ダッシュボード
- **認証**: ドメイン制限認証（@f-a-c.co.jp、@cyxen.co.jp）
- **データベース**: Tursoクラウドデータベース（18,877行）
- **フィルタリング**: サーバーサイドフィルタリング（メモリ70MB→0.1-1MB/ユーザー）
- **配色**: 色覚バリアフリー対応（Okabe-Itoカラーパレット）

### geocache.json
- **件数**: 1,901件
- **目的**: Google Maps API呼び出し削減（コスト削減・高速化）
- **形式**: `{"都道府県市区町村": {"lat": 緯度, "lng": 経度}}`
- **保管場所**: `data/output_v2/geocache.json`（およびルート）

---

## 📊 ファイル統計

### プロジェクト全体
- **ルート項目**: 11個（クリーンアップ後）
- **Pythonスクリプト**: 約20個（メイン）+ 3個（テスト）
- **Reflexモジュール**: 4個（dashboard, auth, login, db_helper）
- **出力CSVファイル**: 43個（V3完全版）
- **ドキュメント**: 100+個（大部分はGAS時代の資料）
- **アーカイブ**: 380ファイル（14MB）

### 開発言語・フレームワーク
- **Python**: 3.x（pandas, numpy, scikit-learn等）
- **Reflex**: v0.8.19（Pythonウェブフレームワーク）
- **Turso**: クラウドSQLiteデータベース
- **libsql-client**: Turso接続用Pythonクライアント

### データ規模
- **入力データ**: 可変（results_*.csv、約5万行想定）
- **出力データ**: 43ファイル、合計数万行
- **データベース**: 18,877行（48都道府県、22市区町村）
- **ジオコーディングキャッシュ**: 1,901件

---

## 🚀 実行フロー

```
1. 入力CSVファイル（results_*.csv）
    ↓
2. Python: run_complete_v2_perfect.py
    ↓ Phase 1-3, 6-8, 10, 12-14実行
    ↓
3. 43個のCSVファイル生成（data/output_v2/phase*/）
    ↓
4. Tursoデータベースへデータ投入（オプション）
    ↓
5. Reflexダッシュボード起動（reflex run --backend-port 8003 --frontend-port 3003）
    ↓
6. ブラウザでログイン（http://localhost:3003/）
    ↓
7. ドメイン認証（@f-a-c.co.jp、@cyxen.co.jp）
    ↓
8. 10パネルダッシュボード表示
```

---

## 📝 メンテナンス方針

### 現行ファイル
- **python_scripts/**: V3 CSV生成エンジン（定期的な品質チェック）
- **reflex_app/**: Reflexダッシュボード（機能追加・改善）
- **data/output_v2/**: 出力データ（定期的なバックアップ）

### アーカイブファイル
- **参照用として保管**（修正履歴、デバッグ手法の記録）
- **削除タイミング**: V3運用が6ヶ月以上安定稼働後
- **バックアップ対象**: 定期的なバックアップに含める

### ドキュメント
- **現行ドキュメント**: README.md、PROJECT_STRUCTURE.md、V3_CSV_SPECIFICATION.md、REFLEX_APP_GUIDE.md
- **アーカイブ対象**: GAS関連ドキュメント（参照用として保管）

---

## 🔗 関連ドキュメント

- **[README.md](../README.md)** - プロジェクトメインドキュメント
- **[V3_CSV_SPECIFICATION.md](V3_CSV_SPECIFICATION.md)** - V3 CSV完全仕様
- **[REFLEX_APP_GUIDE.md](REFLEX_APP_GUIDE.md)** - Reflexアプリ完全ガイド
- **[DATA_USAGE_GUIDELINES.md](DATA_USAGE_GUIDELINES.md)** - データ利用ガイドライン
- **[CLEANUP_REPORT_V3.md](CLEANUP_REPORT_V3.md)** - クリーンアップレポート
- **[DOMAIN_AUTHENTICATION_GUIDE.md](../reflex_app/docs/DOMAIN_AUTHENTICATION_GUIDE.md)** - 認証システムガイド

---

**作成**: Claude Code
**日付**: 2025年11月22日
**プロジェクト**: ジョブメドレー求職者データ分析・可視化システム v3.0
