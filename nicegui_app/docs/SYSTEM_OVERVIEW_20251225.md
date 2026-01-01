# job_ap_analyzer_gui システム概要

**作成日**: 2025年12月25日
**ステータス**: 本番稼働中 ✅

---

## 1. システム概要

### 1.1 目的

ジョブメドレーの求職者データを可視化・分析するダッシュボードアプリケーション。
都道府県・市区町村単位での人材分布、属性分析、移動パターンなどを提供。

### 1.2 本番URL

**https://visualizationj-job-ap-analyzer-gui.onrender.com**

### 1.3 技術スタック

| レイヤー | 技術 | 備考 |
|---------|------|------|
| フロントエンド | NiceGUI | Python製WebUIフレームワーク |
| バックエンド | Python 3.11 | pandas, httpx |
| データベース | Turso (libSQL) | クラウドSQLite |
| ホスティング | Render | Starterプラン ($7/月) |

---

## 2. アーキテクチャ

### 2.1 全体構成

```
┌─────────────────────────────────────────────────────────┐
│                    Render ($7/月)                       │
│  ┌───────────────────────────────────────────────────┐ │
│  │              NiceGUI App (main.py)                │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌───────────┐ │ │
│  │  │ ログイン    │→│ ダッシュボード│→│ 各種分析  │ │ │
│  │  └─────────────┘  └─────────────┘  └───────────┘ │ │
│  │                        ↓                          │ │
│  │              db_helper.py (キャッシュ層)           │ │
│  └───────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
                            ↓ HTTPS
┌─────────────────────────────────────────────────────────┐
│                 Turso Database (無料枠)                 │
│  ┌───────────────────────────────────────────────────┐ │
│  │ job_seeker_data テーブル (1,336,297行)            │ │
│  │ インデックス: prefecture, municipality, row_type  │ │
│  └───────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### 2.2 データフロー

```
CSVファイル (659,949行)
    ↓ turso_fast_import.py
Turso Database (1,336,297行)
    ↓ HTTP API (libsql)
db_helper.py (キャッシュ)
    ↓ 永続キャッシュ
NiceGUI State
    ↓ リアクティブ更新
ブラウザ表示
```

---

## 3. データベース設計

### 3.1 テーブル構造

```sql
CREATE TABLE job_seeker_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    row_type TEXT,           -- APPLICANT, DESIRED, MAP_METRICS, etc.
    prefecture TEXT,         -- 都道府県
    municipality TEXT,       -- 市区町村

    -- 基本属性
    age TEXT,
    gender TEXT,
    employment_status TEXT,

    -- 資格・経験
    qualifications TEXT,
    qualification_count INTEGER,

    -- 希望条件
    desired_salary TEXT,
    desired_workstyle TEXT,

    -- 移動パターン
    mobility_pattern TEXT,

    -- 集計値 (row_type別)
    count INTEGER,
    percentage REAL,
    lat REAL,
    lng REAL,

    -- その他多数のカラム...
);
```

### 3.2 インデックス

| インデックス名 | カラム | 用途 |
|---------------|--------|------|
| idx_prefecture | prefecture | 都道府県フィルタ |
| idx_municipality | prefecture, municipality | 市区町村フィルタ |
| idx_row_type | row_type | データ種別フィルタ |
| idx_pref_type | prefecture, row_type | 複合フィルタ |

### 3.3 row_type一覧

| row_type | 説明 | 件数目安 |
|----------|------|---------|
| APPLICANT | 求職者基本情報 | 数万件 |
| DESIRED | 希望勤務地 | 数十万件 |
| MAP_METRICS | 地図用集計 | 数千件 |
| FLOW_EDGE | 移動フロー | 数千件 |
| PERSONA | ペルソナ分析 | 数百件 |
| STATS | 統計データ | 数百件 |

---

## 4. キャッシュ戦略

### 4.1 2層キャッシュ

```python
# レガシーキャッシュ（TTL付き）
_cache: dict = {}           # 30分TTL、最大100件
_cache_time: dict = {}

# 永続キャッシュ（TTLなし）
_static_cache: dict = {
    "prefectures": None,        # 都道府県リスト
    "municipalities": {},       # 都道府県→市区町村
    "filtered_data": {},        # 地域別データ
}
```

### 4.2 キャッシュ動作

| データ種別 | キャッシュ | TTL | 共有 |
|-----------|----------|-----|------|
| 都道府県リスト | 永続 | なし | 全ユーザー |
| 市区町村リスト | 永続 | なし | 全ユーザー |
| フィルタ済みデータ | 永続 | なし | 全ユーザー |

**効果**: 100人が同時に「東京都」を選択しても、DBクエリは初回の1回のみ

### 4.3 キャッシュクリア

```python
from db_helper import refresh_all_cache
refresh_all_cache()  # 明示的にクリア（データ更新時）
```

---

## 5. Turso制限と使用状況

### 5.1 無料プラン制限

| 項目 | 制限 | 現在の使用 |
|------|------|-----------|
| ストレージ | 9 GB | ~500 MB |
| Row Reads | 1B/月 | ~0.3% |
| Row Writes | 25M/月 | インポート時のみ |

### 5.2 Row Reads最適化

1. **インデックス使用**: 全クエリでINDEX SCAN（フルスキャンなし）
2. **永続キャッシュ**: 同じデータへの再クエリなし
3. **サーバーサイドフィルタ**: WHERE句で絞り込み後に転送

---

## 6. デプロイ設定

### 6.1 Render設定

| 項目 | 値 |
|------|-----|
| サービス名 | visualizationj-job-ap-analyzer-gui |
| プラン | Starter ($7/月) |
| リージョン | Oregon |
| ビルドコマンド | `pip install -r requirements.txt` |
| スタートコマンド | `python main.py` |

### 6.2 環境変数

| 変数名 | 説明 |
|--------|------|
| TURSO_DATABASE_URL | Turso接続URL |
| TURSO_AUTH_TOKEN | 認証トークン |
| PYTHON_VERSION | 3.11 |

### 6.3 requirements.txt（主要）

```
nicegui>=1.4.0
pandas>=2.0.0
httpx>=0.25.0
python-dotenv>=1.0.0
```

---

## 7. ダッシュボード機能

### 7.1 タブ構成

| タブ | 機能 |
|------|------|
| 市場概況 | KPI、年齢分布、性別分布、雇用形態 |
| 人材属性 | 資格分布、年齢×性別クロス分析 |
| 地域・移動パターン | 移動パターン分布、ペルソナ分析 |
| 需給バランス | 供給・需要分析 |
| 求人地図 | 地図表示（将来実装） |

### 7.2 フィルター

- 都道府県プルダウン（47都道府県、北→南順）
- 市区町村プルダウン（都道府県連動）

---

## 8. 今後の展開計画

### 8.1 複数職種対応

**コンセプト**: 1アプリ、複数DB

```
┌─────────────────────────────────────┐
│         NiceGUI App（1つ）          │
│  ┌─────────────────────────────┐   │
│  │ 職種プルダウン: [介護▼]     │   │
│  └─────────────────────────────┘   │
└─────────────────────────────────────┘
              ↓ 動的切替
    ┌────────┼────────┐
    ↓        ↓        ↓
┌──────┐ ┌──────┐ ┌──────┐
│Turso │ │Turso │ │Turso │
│介護DB│ │看護DB│ │PT/OTDB│
└──────┘ └──────┘ └──────┘
```

### 8.2 実装方針

```python
# db_helper.py
JOB_TYPE_CONFIGS = {
    "介護": {
        "db_url": "libsql://job-kaigo-...",
        "token": "...",
    },
    "看護": {
        "db_url": "libsql://job-kango-...",
        "token": "...",
    },
}

def switch_database(job_type: str):
    config = JOB_TYPE_CONFIGS[job_type]
    # 接続先切替 + キャッシュクリア
```

### 8.3 コストメリット

| 方式 | Render費用 | Turso費用 |
|------|-----------|-----------|
| アプリ別々 | $7 × 職種数 | 無料枠内 |
| **アプリ統一** | **$7 固定** | 無料枠内 |

---

## 9. 新職種追加手順（将来用）

### Step 1: Turso DB作成

```bash
turso db create job-{職種名}
turso db tokens create job-{職種名}
```

### Step 2: テーブル＆インデックス作成

```sql
-- 既存のCREATE TABLE文をコピー
-- 既存のCREATE INDEX文をコピー
```

### Step 3: データインポート

```bash
# 環境変数を新DBに設定
export TURSO_DATABASE_URL="libsql://job-{職種名}-..."
export TURSO_AUTH_TOKEN="..."

# インポート実行
python turso_fast_import.py
```

### Step 4: アプリ設定追加

```python
# db_helper.py の JOB_TYPE_CONFIGS に追加
"{職種名}": {
    "db_url": "...",
    "token": "...",
},
```

---

## 10. トラブルシューティング

### 10.1 よくある問題

| 症状 | 原因 | 対処 |
|------|------|------|
| ログイン後白画面 | Turso接続エラー | 環境変数確認 |
| データがありません | キャッシュ不整合 | refresh_all_cache() |
| Row Reads急増 | デプロイ連発 | デプロイ頻度を下げる |

### 10.2 ログ確認

Renderダッシュボード → Logs で以下を確認:

```
[DB] Fetching prefectures (first time only)...  ← 正常
[DB] Fetching data for 東京都/千代田区 (first time only)...  ← 正常
[CACHE] All cache cleared  ← デプロイ時のみ
```

---

## 11. ファイル構成

```
nicegui_app/
├── main.py                 # メインアプリ (2000行)
├── db_helper.py            # DB接続＆キャッシュ (1700行)
├── requirements.txt        # 依存パッケージ
├── .env.production         # 本番環境変数
├── turso_fast_import.py    # データインポートスクリプト
└── docs/
    └── SYSTEM_OVERVIEW_20251225.md  # このファイル
```

---

## 12. 連絡先・参考

- **Turso Dashboard**: https://turso.tech/app
- **Render Dashboard**: https://dashboard.render.com
- **NiceGUI Docs**: https://nicegui.io/documentation

---

*このドキュメントは2025年12月25日時点の情報です。*
