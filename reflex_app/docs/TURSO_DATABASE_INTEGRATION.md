# Turso データベース統合ドキュメント

**作成日**: 2025年11月19日
**ステータス**: 実装完了（サーバーサイドフィルタリング移行推奨）

---

## 概要

Reflex ダッシュボードアプリに Turso クラウドデータベースを統合し、CSVアップロード不要でデータを読み込めるようにしました。

### 導入したサービス

| サービス | 用途 | 費用 |
|----------|------|------|
| **Turso** | クラウドデータベース（SQLite互換） | 無料 |
| **Reflex Hosting** | アプリホスティング | 無料 |

---

## Turso 接続情報

| 項目 | 値 |
|------|-----|
| Organization | makimaki1006 |
| Database | job-jobseekeranalyzer |
| Region | ap-northeast-1 (Tokyo) |
| URL | `libsql://job-jobseekeranalyzer-makimaki1006.aws-ap-northeast-1.turso.io` |
| ストレージ使用量 | 4.55 MB |
| 総行数 | 18,877行 |

### 環境変数（.env）

```bash
TURSO_DATABASE_URL=libsql://job-jobseekeranalyzer-makimaki1006.aws-ap-northeast-1.turso.io
TURSO_AUTH_TOKEN=eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9...
```

**注意**: `.env` ファイルは `.gitignore` に含まれており、Gitにコミットされません。

---

## データベーススキーマ

### テーブル: `job_seeker_data`

```sql
CREATE TABLE job_seeker_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    row_type TEXT NOT NULL,
    prefecture TEXT NOT NULL,
    municipality TEXT,
    category1 TEXT,
    category2 TEXT,
    category3 TEXT,
    applicant_count REAL,
    avg_age REAL,
    male_count REAL,
    female_count REAL,
    avg_qualifications REAL,
    latitude REAL,
    longitude REAL,
    count REAL,
    avg_desired_areas REAL,
    employment_rate TEXT,
    national_license_rate REAL,
    has_national_license TEXT,
    avg_mobility_score REAL,
    total_in_municipality REAL,
    market_share_pct REAL,
    avg_urgency_score REAL,
    inflow REAL,
    outflow REAL,
    net_flow REAL,
    demand_count REAL,
    supply_count REAL,
    gap REAL,
    demand_supply_ratio REAL,
    rarity_score REAL,
    total_applicants REAL,
    top_age_ratio REAL,
    female_ratio REAL,
    male_ratio REAL,
    top_employment_ratio REAL,
    avg_qualification_count REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

### インデックス

```sql
CREATE INDEX idx_prefecture ON job_seeker_data(prefecture);
CREATE INDEX idx_municipality ON job_seeker_data(prefecture, municipality);
CREATE INDEX idx_row_type ON job_seeker_data(row_type);
CREATE INDEX idx_pref_type ON job_seeker_data(prefecture, row_type);
```

### データ統計

| row_type | 件数 |
|----------|------|
| PERSONA_MUNI | 3,249 |
| RARITY | 3,129 |
| EMPLOYMENT_AGE_CROSS | 3,113 |
| その他 | 9,386 |
| **合計** | **18,877** |

---

## 実装ファイル

### 1. `db_helper.py`

データベースアクセスを抽象化するヘルパーモジュール。

**機能**:
- Turso / PostgreSQL / SQLite の自動切り替え
- 非同期クエリ実行（Reflex対応）
- キャッシュシステム（TTL 30分、LRU 50件）

**主要関数**:

```python
get_db_type() -> str          # 使用中のDBタイプを取得
get_all_data() -> pd.DataFrame # 全データ取得（キャッシュ対応）
get_prefectures() -> list      # 都道府県一覧
get_municipalities(pref) -> list # 市区町村一覧
query_df(sql, params) -> pd.DataFrame # カスタムクエリ
```

### 2. `scripts/turso_setup.py`

Turso データベースの初期セットアップスクリプト。

**実行方法**:
```bash
cd reflex_app
python scripts/turso_setup.py
```

**処理内容**:
1. テーブル作成
2. インデックス作成
3. CSVデータインポート（MapComplete_Complete_All_FIXED.csv）

### 3. `mapcomplete_dashboard/mapcomplete_dashboard.py`

**追加メソッド**:
- `load_from_database()`: データベースからデータを読み込むイベントハンドラ

**追加UI**:
- 「データベースから読み込み」ボタン（青緑色、最上部に配置）

---

## 使用方法

### ローカル開発

1. `.env` ファイルに認証情報を設定
2. アプリを起動:
   ```bash
   cd reflex_app
   reflex run
   ```
3. ブラウザで http://localhost:3000 を開く
4. 「データベースから読み込み」ボタンをクリック

### 本番デプロイ（Reflex Hosting）

1. Reflex Hosting に環境変数を設定:
   ```bash
   reflex deployments secrets set TURSO_DATABASE_URL=libsql://...
   reflex deployments secrets set TURSO_AUTH_TOKEN=eyJ...
   ```
2. デプロイ実行:
   ```bash
   reflex deploy
   ```

---

## アーキテクチャ

### 現在の方式（クライアントサイドフィルタリング）

```
[ユーザー] → [Reflex Frontend] → [Reflex Backend]
                                        ↓
                                  State.df (18,877行)
                                        ↓
                              pandas でフィルタリング
                                        ↓
                                  表示データ生成
```

**特徴**:
- 初回に全データをロード
- フィルタ変更は高速（メモリ内処理）
- メモリ消費: 約70MB/ユーザー

---

## スケーラビリティの課題

### メモリ消費の問題

| ユーザー数 | メモリ消費 | 評価 |
|------------|-----------|------|
| 1-5人 | 70-350MB | 問題なし |
| 10人 | 700MB | 注意 |
| 30人 | 2.1GB | **問題あり** |
| 100人 | 7GB | 運用不可 |

### Reflex Hosting 無料枠の制限

- **メモリ**: 512MB
- 現状の方式では30人利用時に**2.1GB必要**で、無料枠を大幅に超過

---

## 推奨: サーバーサイドフィルタリングへの移行

### 概要

全データをStateに保持せず、必要なデータのみをDBにクエリする方式。

```
[ユーザー] → [Reflex Frontend] → [Reflex Backend]
                                        ↓
                                   DBクエリ実行
                                        ↓
                                 [Turso Database]
                                        ↓
                              フィルタ済みデータ（数十〜数百行）
                                        ↓
                                  表示データ生成
```

### メリット

| 項目 | 改善効果 |
|------|----------|
| メモリ/ユーザー | 70MB → 0.1-1MB |
| 30人利用時の合計 | 2.1GB → 30MB |
| Reflex Hosting無料枠 | 対応可能 |

### デメリット

- フィルタ変更時に毎回DB通信（10-50ms の遅延）
- 実装の複雑化

### 移行作業の見積もり

| タスク | 時間 |
|--------|------|
| State構造の変更 | 30分 |
| フィルタハンドラの実装 | 30分 |
| 計算プロパティのDB化 | 1-1.5時間 |
| テスト・デバッグ | 30分 |
| **合計** | **2.5-3時間** |

### 移行の判断基準

| 想定ユーザー数 | 推奨 |
|----------------|------|
| 1-5人 | 現状維持 |
| 5-10人 | 状況に応じて判断 |
| **10人以上** | **移行必須** |

---

## 費用まとめ

### 無料枠の範囲

| サービス | 無料枠 | 30人利用時 |
|----------|--------|-----------|
| **Turso** | 9GB ストレージ、10億行/月 | 余裕あり |
| **Reflex Hosting** | 512MB メモリ | 移行後は対応可能 |

### 想定費用

| 項目 | 費用 |
|------|------|
| Turso | 無料 |
| Reflex Hosting | 無料 |
| カスタムドメイン（オプション） | 年間1,000-2,000円 |
| **合計** | **0円〜2,000円/年** |

---

## 次のステップ

### 30人規模での公開を予定している場合

1. **サーバーサイドフィルタリングへの移行**
   - `load_from_database` を軽量化（都道府県リストのみ取得）
   - `on_prefecture_change` でDB直接クエリ
   - `on_municipality_change` でDB直接クエリ
   - 各パネルの計算プロパティをDBクエリに置き換え

2. **Reflex Hosting への環境変数設定**
   ```bash
   reflex deployments secrets set TURSO_DATABASE_URL=...
   reflex deployments secrets set TURSO_AUTH_TOKEN=...
   ```

3. **本番デプロイ**
   ```bash
   reflex deploy
   ```

### 少人数（5人以下）での利用の場合

現状の実装で問題なく動作します。

---

## トラブルシューティング

### 「Tursoからデータを取得できませんでした」エラー

**原因**: Reflexのイベントループとの競合

**解決**: `db_helper.py` の `query_df` 関数で `ThreadPoolExecutor` を使用して別スレッドで非同期クエリを実行（実装済み）

### 環境変数が読み込まれない

**確認事項**:
1. `.env` ファイルが `reflex_app/` 直下にあるか
2. `python-dotenv` がインストールされているか
3. 変数名が正確か（`TURSO_DATABASE_URL`, `TURSO_AUTH_TOKEN`）

### データベース接続テスト

```bash
cd reflex_app
python db_helper.py
```

期待される出力:
```
Database Type: turso
都道府県一覧:
  48都道府県
```

---

## 参考リンク

- [Turso ドキュメント](https://docs.turso.tech/)
- [Reflex Hosting ドキュメント](https://reflex.dev/docs/hosting/deploy-quick-start/)
- [libsql-client Python](https://github.com/libsql/libsql-client-py)
