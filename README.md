# ジョブメドレー求職者データ分析・可視化システム

**バージョン**: 3.1 (Phase 12-14追加版)
**最終更新**: 2025年11月23日
**ステータス**: 本番運用可能 ✅

## プロジェクト概要

求職者データを包括的に分析し、Reflexダッシュボードで可視化するエンドツーエンドシステムです。

### システム構成

```
生データ（CSV）
    ↓
Python V3分析エンジン
    ↓
18,877行の分析データ
    ↓
Tursoクラウドデータベース
    ↓
Reflexダッシュボード（認証付き）
```

### 主要機能

- **V3 CSV生成エンジン**: 14段階の包括的データ分析パイプライン（Phase 1-14）
- **Reflexダッシュボード**: インタラクティブWeb UI（認証システム統合）
- **Tursoデータベース**: 18,877行のクラウドデータベース
- **ドメイン制限認証**: @f-a-c.co.jp、@cyxen.co.jp限定アクセス

### パフォーマンス

| 項目 | 値 |
|------|-----|
| データ処理速度 | 53,000行 → 26,768行（外れ値除外） |
| データベース | Turso（AWS Tokyo、18,877行） |
| レスポンス時間 | サーバーサイドフィルタリング有効 |
| 品質スコア | 82.86/100 (EXCELLENT) |

---

## クイックスタート

### 1. 環境構築

```bash
# 依存パッケージのインストール
pip install -r requirements.txt
pip install reflex libsql-client python-dotenv

# 環境変数の設定
cd reflex_app
# .envファイルを作成（テンプレート参照）
```

### 2. データ生成

```bash
cd python_scripts
python run_complete_v3.py
```

GUIでCSVファイルを選択すると、Phase 1-14のすべてのCSVファイルが生成されます。

### 3. ダッシュボード起動

```bash
cd reflex_app
reflex run --backend-port 8003 --frontend-port 3003
```

ブラウザで http://localhost:3003/ にアクセスし、許可されたドメインのメールアドレスでログインします。

---

## プロジェクト構成

### ディレクトリ構造

```
job_medley_project/
├── python_scripts/              # V3 CSV生成エンジン
│   ├── run_complete_v3.py       # メイン実行スクリプト（V3完全版）
│   ├── run_complete_v2_perfect.py  # V2実装（V3から呼び出し）
│   ├── comprehensive_test_suite_v3.py  # テストスイート（270テスト）
│   ├── data/
│   │   └── output_v2/           # 生成CSVファイル（Phase別）
│   └── archive_old_scripts/     # 古いスクリプト（アーカイブ）
│
├── reflex_app/                  # Reflexダッシュボード
│   ├── mapcomplete_dashboard/
│   │   ├── mapcomplete_dashboard.py  # メインアプリ
│   │   ├── auth.py              # 認証システム
│   │   ├── login.py             # ログインページ
│   │   └── db_helper.py         # Tursoデータベース接続
│   ├── docs/
│   │   ├── DOMAIN_AUTHENTICATION_GUIDE.md  # 認証ガイド
│   │   └── TURSO_DATABASE_INTEGRATION.md   # DB統合ガイド
│   └── .env                     # 環境変数（Git管理外）
│
├── data/                        # データファイル
│   └── output_v2/               # V2/V3出力データ
│       ├── phase1/              # 基礎集計
│       ├── phase2/              # 統計分析
│       ├── phase3/              # ペルソナ分析
│       ├── phase6/              # フロー分析
│       ├── phase7/              # 高度分析
│       ├── phase8/              # キャリア・学歴分析
│       ├── phase10/             # 転職意欲・緊急度分析
│       └── mapcomplete_complete_sheets/  # 統合シート
│
├── docs/                        # プロジェクトドキュメント
│   ├── PROJECT_STRUCTURE.md     # 詳細フォルダ構造
│   ├── V3_CSV_SPECIFICATION.md  # V3 CSV仕様
│   ├── REFLEX_APP_GUIDE.md      # Reflexアプリガイド
│   ├── CLEANUP_REPORT_V3.md     # 整理レポート
│   └── V3_CSV_COMPREHENSIVE_VALIDATION_REPORT.md  # V3検証レポート
│
├── archive_old_files/           # アーカイブ（380ファイル、14MB）
│   ├── old_gas/                 # 旧GAS関連（6フォルダ）
│   ├── old_docs/                # 旧ドキュメント（約20個）
│   ├── old_tests/               # 旧テストファイル（3個）
│   ├── old_apps/                # 旧Webアプリ（Streamlit/Dash）
│   └── gas_deployment/          # GAS修正スクリプト・バックアップ
│
├── geocache.json                # ジオコーディングキャッシュ
├── requirements.txt             # Python依存パッケージ
├── pytest.ini                   # テスト設定
├── render.yaml                  # デプロイ設定
└── README.md                    # このファイル
```

詳細は [PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md) を参照してください。

---

## 技術スタック

### バックエンド

- **Python 3.8+**: データ処理・分析
  - pandas: データ処理
  - numpy: 数値計算
  - scikit-learn: 統計分析

### フロントエンド

- **Reflex 0.8.19**: Pythonウェブフレームワーク
  - サーバーサイド認証
  - リアルタイムデータバインディング

### データベース

- **Turso**: クラウドSQLiteデータベース
  - 18,877行のデータ
  - AWS Tokyo（ap-northeast-1）
  - libsql-client接続

### 認証

- **ドメイン制限認証**:
  - 許可ドメイン: @f-a-c.co.jp、@cyxen.co.jp
  - 共通パスワード認証
  - サーバーサイドセッション管理

---

## V3 CSV生成エンジン

### 実行方法

```bash
cd python_scripts
python run_complete_v3.py
```

### 生成されるCSVファイル

#### Phase 1: 基礎集計（6ファイル）
- `Applicants.csv` - 申請者基本情報
- `DesiredWork.csv` - 希望勤務地詳細
- `AggDesired.csv` - 集計データ
- `MapMetrics.csv` - 地図表示用データ（座標付き）
- `P1_QualityReport.csv` - 品質レポート
- `P1_QualityReport_Descriptive.csv` - 観察的記述用品質レポート

#### Phase 2: 統計分析（3ファイル）
- `ChiSquareTests.csv` - カイ二乗検定結果
- `ANOVATests.csv` - ANOVA検定結果
- `P2_QualityReport_Inferential.csv` - 推論的考察用品質レポート

#### Phase 3: ペルソナ分析（4ファイル）
- `PersonaSummary.csv` - ペルソナサマリー
- `PersonaDetails.csv` - ペルソナ詳細
- `PersonaSummaryByMunicipality.csv` - 市町村別ペルソナ分析
- `P3_QualityReport_Inferential.csv` - 品質レポート

#### Phase 6: フロー分析（5ファイル）
- `MunicipalityFlowEdges.csv` - 自治体間フローエッジ
- `AggregatedFlowEdges.csv` - 集計フローエッジ
- `MunicipalityFlowNodes.csv` - 自治体間フローノード
- `ProximityAnalysis.csv` - 移動パターン分析
- `P6_QualityReport_Inferential.csv` - 品質レポート

#### Phase 7: 高度分析（6ファイル）
- `SupplyDensityMap.csv` - 人材供給密度マップ
- `QualificationDistribution.csv` - 資格別人材分布
- `AgeGenderCrossAnalysis.csv` - 年齢層×性別クロス分析
- `MobilityScore.csv` - 移動許容度スコアリング
- `DetailedPersonaProfile.csv` - ペルソナ詳細プロファイル
- `P7_QualityReport_Inferential.csv` - 品質レポート

#### Phase 8: キャリア・学歴分析（6ファイル）
- `CareerDistribution.csv` - キャリア分布
- `CareerAgeCross.csv` - キャリア×年齢クロス分析
- `CareerAgeCross_Matrix.csv` - マトリックス形式
- `GraduationYearDistribution.csv` - 卒業年分布
- `P8_QualityReport.csv` - 品質レポート
- `P8_QualityReport_Inferential.csv` - 推論的考察用品質レポート

#### Phase 10: 転職意欲・緊急度分析（10ファイル）
- `UrgencyDistribution.csv` - 緊急度分布
- `UrgencyAgeCross.csv` - 緊急度×年齢クロス分析
- `UrgencyAgeCross_Matrix.csv` - マトリックス形式
- `UrgencyEmploymentCross.csv` - 緊急度×就業状況クロス分析
- `UrgencyEmploymentCross_Matrix.csv` - マトリックス形式
- `UrgencyByMunicipality.csv` - 市区町村別緊急度
- `UrgencyAgeCross_ByMunicipality.csv` - 市区町村別年齢クロス
- `UrgencyEmploymentCross_ByMunicipality.csv` - 市区町村別就業クロス
- `P10_QualityReport.csv` - 品質レポート
- `P10_QualityReport_Inferential.csv` - 推論的考察用品質レポート

**注記**: Phase 10は現在品質スコア40.0/100（観察的記述専用）。データ補完またはバリデーション基準の明文化により改善可能。

#### Phase 12: 需給ギャップ分析（3ファイル）
- `Phase12_SupplyDemandGap.csv` - 市区町村別需給ギャップスコア
- `P12_QualityReport.csv` - 品質レポート
- `P12_QualityReport_Descriptive.csv` - 観察的記述用品質レポート

#### Phase 13: 希少性スコア（3ファイル）
- `Phase13_RarityScore.csv` - 資格・職種別希少性スコア
- `P13_QualityReport.csv` - 品質レポート
- `P13_QualityReport_Descriptive.csv` - 観察的記述用品質レポート

#### Phase 14: 競合分析（3ファイル）
- `Phase14_CompetitionProfile.csv` - 市区町村別競合プロファイル
- `P14_QualityReport.csv` - 品質レポート
- `P14_QualityReport_Descriptive.csv` - 観察的記述用品質レポート

#### 統合レポート（3ファイル）
- `geocache.json` - ジオコーディングキャッシュ
- `OverallQualityReport.csv` - 統合品質レポート
- `OverallQualityReport_Inferential.csv` - 推論的考察用統合品質レポート

**合計**: 52ファイル | **品質スコア**: 82.86/100 (EXCELLENT)

詳細は [V3_CSV_SPECIFICATION.md](docs/V3_CSV_SPECIFICATION.md) を参照してください。

---

## Reflexダッシュボード

### 機能一覧

#### 認証システム
- ドメイン制限認証（@f-a-c.co.jp、@cyxen.co.jp）
- 共通パスワード認証
- サーバーサイドセッション管理
- ログアウト機能

#### データ可視化
- 都道府県・市区町村別フィルタリング
- サーバーサイドデータフィルタリング
- リアルタイムグラフ更新
- カラーブラインド対応カラーパレット

#### データベース連携
- Turso（18,877行）
- サーバーサイドフィルタリング
- 高速データ取得

### 起動方法

```bash
cd reflex_app
reflex run --backend-port 8003 --frontend-port 3003
```

### ログイン

1. ブラウザで http://localhost:3003/ にアクセス
2. **メールアドレス**: 許可されたドメインのアドレス（例: user@f-a-c.co.jp）
3. **パスワード**: `.env`ファイルの`AUTH_PASSWORD`の値
4. 「ログイン」ボタンをクリック

詳細は [reflex_app/docs/DOMAIN_AUTHENTICATION_GUIDE.md](reflex_app/docs/DOMAIN_AUTHENTICATION_GUIDE.md) を参照してください。

---

## データ品質検証システム

V3実装では、**観察的記述（Descriptive）**と**推論的考察（Inferential）**を自動判別する品質検証システムを統合しています。

### 観察的記述モード（Descriptive）

**用途**: 事実の記述（集計値・件数・割合の提示）

**特徴**:
- サンプル数1件でも事実として提示可能
- 件数を明記すれば問題なし
- 「傾向」「差異」の言葉は使用不可

**適用Phase**: Phase 1（基礎集計）

### 推論的考察モード（Inferential）

**用途**: 傾向分析（クロス集計・関係性の推論）

**特徴**:
- 最小サンプル数必要（グループ30件以上、全体100件以上推奨）
- サンプル数不足は警告表示
- 「傾向が見られる」「関係性がある」使用可能

**適用Phase**: Phase 2, 3, 6, 7, 8, 10（統計分析・クロス集計）

### 品質スコア

| スコア | ステータス | 意味 |
|--------|-----------|------|
| 80-100 | EXCELLENT | そのまま使用可能 |
| 60-79 | GOOD | 一部注意が必要だが全体的に信頼できる |
| 40-59 | ACCEPTABLE | 警告付きで結果を提示することを推奨 |
| 0-39 | POOR | データ数不足または欠損多数、追加データ収集推奨 |

---

## テスト

### V3包括的テストスイート

```bash
cd python_scripts
python comprehensive_test_suite_v3.py
```

**テスト内容**:
- ユニットテスト: 50件（フィルターロジック、データ正規化、ハッシュ計算）
- 統合テスト: 90件（モジュールインポート、データフロー、出力一貫性）
- E2Eテスト: 70件（完全実行、ハッシュ一貫性、データ品質）
- 回帰テスト: 60件（過去のバグ再発確認）

**合計**: 270件（4階層×27テスト×10回繰り返し）
**成功率**: 100.0%（270/270成功）

### 自動化統合テスト 🆕

#### 完全統合テスト（run_complete_v3.py実行含む）

```bash
cd python_scripts
python automated_integration_test.py --input "C:\Users\fuji1\OneDrive\Pythonスクリプト保管\out\results_20251122_200023.csv"
```

**実行内容**:
1. run_complete_v3.pyの自動実行（Phase 1-14完全生成）
2. 52個の出力CSVファイル存在確認
3. Phase別品質スコア検証（最低基準60点）
4. V2パターンファイル確認（3ファイル）
5. MapComplete統合CSV確認

**出力**:
- `tests/results/integration_test_YYYYMMDD_HHMMSS.json` - 詳細結果（JSON）
- `tests/results/integration_test_YYYYMMDD_HHMMSS.md` - テストレポート（Markdown）

**実行時間**: 約5-10分（データ量に依存）

#### クイック検証テスト（既存出力のみチェック）

```bash
cd python_scripts
python quick_validation_test.py
```

**実行内容**:
1. 既存Phase 1-14出力ファイル存在確認
2. 統合品質レポート読み取り
3. V2パターンファイル確認
4. MapComplete統合CSV確認

**出力**:
- `tests/results/quick_validation_YYYYMMDD_HHMMSS.json` - 検証結果（JSON）

**実行時間**: 約5-10秒

**使い分け**:
- **完全統合テスト**: 新しいデータで全Phase実行＋検証（CI/CD、定期実行）
- **クイック検証**: 既存出力の整合性確認のみ（開発中の確認）

---

## デプロイ

### Render.com（推奨）

`render.yaml`を使用してデプロイします：

```bash
# render.yamlの設定を確認
cat render.yaml

# Render.comダッシュボードからデプロイ
# GitHub連携でリポジトリを接続
```

### 環境変数の設定

Render.comダッシュボードで以下の環境変数を設定：

- `ALLOWED_DOMAINS`
- `AUTH_PASSWORD`
- `SESSION_SECRET`
- `TURSO_DATABASE_URL`
- `TURSO_AUTH_TOKEN`

---

## ドキュメント

### プロジェクトドキュメント

- [PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md) - 詳細なフォルダ構造
- [V3_CSV_SPECIFICATION.md](docs/V3_CSV_SPECIFICATION.md) - V3 CSV仕様
- [REFLEX_APP_GUIDE.md](docs/REFLEX_APP_GUIDE.md) - Reflexアプリ完全ガイド
- [CLEANUP_REPORT_V3.md](docs/CLEANUP_REPORT_V3.md) - プロジェクト整理レポート

### Reflexアプリドキュメント

- [DOMAIN_AUTHENTICATION_GUIDE.md](reflex_app/docs/DOMAIN_AUTHENTICATION_GUIDE.md) - 認証システムガイド
- [TURSO_DATABASE_INTEGRATION.md](reflex_app/docs/TURSO_DATABASE_INTEGRATION.md) - Tursoデータベース統合ガイド

### V3検証レポート

- [V3_CSV_COMPREHENSIVE_VALIDATION_REPORT.md](python_scripts/V3_CSV_COMPREHENSIVE_VALIDATION_REPORT.md) - V3 CSV包括的検証レポート

---

## 開発

### Python開発

```bash
# 依存パッケージのインストール
pip install -r requirements.txt

# テストの実行
cd python_scripts
python comprehensive_test_suite_v3.py
```

### Reflex開発

```bash
# Reflexのインストール
pip install reflex

# 開発サーバーの起動
cd reflex_app
reflex run --backend-port 8003 --frontend-port 3003
```

---

## トラブルシューティング

### V3 CSV生成エラー

**問題**: CSVファイルが生成されない

**確認事項**:
1. 入力CSVファイルのパスが正しいか
2. `data/output_v2/`フォルダが存在するか
3. 外れ値フィルター（40+希望地、5+都道府県）を通過するデータがあるか

### Reflexダッシュボードエラー

**問題**: サーバーが起動しない

**確認事項**:
1. `.env`ファイルが存在し、すべての環境変数が設定されているか
2. `libsql-client`がインストールされているか（`pip show libsql-client`）
3. Turso認証トークンが正しいか

**問題**: ログインできない

**確認事項**:
1. メールアドレスのドメインが許可リストに含まれているか
2. パスワードが正しいか（`.env`の`AUTH_PASSWORD`と一致）

---

## ライセンス

このプロジェクトは内部使用のみです。

---

## 更新履歴

| 日付 | バージョン | 変更内容 |
|------|-----------|---------|
| 2025-11-23 | 3.1 | Phase 12-14追加、run_complete_v3.py stdout修正、自動化統合テスト追加（automated_integration_test.py, quick_validation_test.py） |
| 2025-11-22 | 3.0 | Reflex統合版リリース - 認証システム統合、Tursoデータベース連携 |
| 2025-11-22 | 2.1 | V3 CSV完全実装 - 270/270テスト成功、品質検証システム統合 |
| 2025-10-28 | 2.0 | V2 CSV実装 - 新形式対応、Phase 1-10完全実装 |

---

## サポート

問題が発生した場合は、以下のドキュメントを参照してください：

1. [プロジェクト構造](docs/PROJECT_STRUCTURE.md)
2. [V3 CSV仕様](docs/V3_CSV_SPECIFICATION.md)
3. [Reflexアプリガイド](docs/REFLEX_APP_GUIDE.md)
4. [認証システムガイド](reflex_app/docs/DOMAIN_AUTHENTICATION_GUIDE.md)

それでも解決しない場合は、プロジェクト管理者に連絡してください。
