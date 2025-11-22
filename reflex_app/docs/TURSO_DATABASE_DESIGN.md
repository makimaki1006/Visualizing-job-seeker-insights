# Turso データベース設計書

**作成日**: 2025年11月19日
**ステータス**: 設計完了・実装待ち

---

## 1. 概要

### 目的
CSVファイルの都度アップロードから、クラウドデータベースへの移行により：
- アプリの動作を軽量化
- 都度作業の工数削減
- 複数職種データの一元管理

### 選定サービス: Turso

| 項目 | 内容 |
|------|------|
| サービス | Turso (https://turso.tech) |
| DB種類 | SQLite互換（libSQL） |
| 無料枠ストレージ | 5GB |
| 無料枠DB数 | 500個 |
| 読み取り制限 | 5億行/月 |
| 書き込み制限 | 1,000万行/月 |

---

## 2. データ規模の推定

### 現状データ（群馬県起点）
- 行数: 18,877行
- カラム数: 36
- サイズ: 2.06MB

### 本番データ（全国・人口ベース推定）

| 項目 | 値 |
|------|-----|
| 全国推定行数 | 1,228,570行 |
| 推定サイズ | 134MB |
| インデックス込み | 201MB |

### 複数職種対応

| 職種数 | データ量 | Turso対応 |
|--------|----------|-----------|
| 3職種 | 600MB | OK |
| 5職種 | 1GB | OK |
| 10職種 | 2GB | OK |

---

## 3. 制限の運用想定

### 書き込み制限（1,000万行/月）

| シナリオ | 使用率 | 判定 |
|----------|--------|------|
| 初回インポートのみ | 12.3% | OK |
| 月1回全データ更新 | 24.6% | OK |
| 週1回全データ更新 | 98.3% | WARNING |
| 日次差分更新（1%） | 3.7% | OK |

**推奨**: 月2〜3回の全データ更新

### 読み取り制限（5億行/月）

#### 最適化なしの場合（問題あり）

| シナリオ | 使用率 | 判定 |
|----------|--------|------|
| 個人利用（10回/日） | 85.6% | WARNING |
| チーム利用（50回/日） | 428% | NG |

#### 最適化後（市区町村単位クエリ）

| 職種数 | 利用頻度 | 使用率 | 判定 |
|--------|----------|--------|------|
| 3職種 | 個人（10回/日） | 0.36% | OK |
| 3職種 | チーム（50回/日） | 1.68% | OK |
| 10職種 | 業務（100回/日） | 3.41% | OK |

---

## 4. アーキテクチャ設計

### データベース構成

```
Tursoアカウント
├── kaigo-db      （介護職データ）
├── kango-db      （看護職データ）
├── hoiku-db      （保育職データ）
└── ...
```

### アプリでの切り替え

```python
databases = {
    '介護職': 'libsql://kaigo-db.turso.io',
    '看護職': 'libsql://kango-db.turso.io',
    '保育職': 'libsql://hoiku-db.turso.io',
}

def get_connection(job_type):
    return libsql.connect(
        databases[job_type],
        auth_token=os.environ['TURSO_AUTH_TOKEN']
    )
```

---

## 5. クエリ最適化戦略

### 問題: 全データ取得は非効率

```python
# 悪い例: 全データ取得
df = db.query("SELECT * FROM data")  # 123万行
filtered = df[df['prefecture'] == '東京都']  # メモリ内フィルタ
```

### 解決: 市区町村単位でクエリ

```python
# 良い例: 必要なデータのみ取得
data = db.query(
    "SELECT * FROM data WHERE prefecture = ? AND municipality = ?",
    [prefecture, municipality]
)  # 2,000行程度
```

### 読み取り量の比較

| 操作 | 全データ取得 | 市区町村単位 |
|------|-------------|-------------|
| 東京都・新宿区 | 1,228,570行 | 2,000行 |
| 東京都・渋谷区 | 1,228,570行 | 2,000行 |
| **削減率** | - | **99.8%** |

---

## 6. キャッシュ戦略

### 方式: TTL + LRUキャッシュ

| 設定 | 値 | 理由 |
|------|-----|------|
| キャッシュ単位 | 市区町村 | 最小クエリ単位 |
| TTL | 30分 | データ更新への対応 |
| 最大エントリ | 50 | メモリ制限内（約250MB） |

### 実装イメージ

```python
class DashboardState(rx.State):
    _cache: dict = {}
    _cache_time: dict = {}
    _max_cache_items = 50
    _ttl_minutes = 30

    def get_data(self, job_type, prefecture, municipality):
        cache_key = f"{job_type}_{prefecture}_{municipality}"

        # キャッシュチェック
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached  # DBアクセスなし

        # DBから取得
        data = self._query_db(job_type, prefecture, municipality)

        # キャッシュに保存
        self._set_cache(cache_key, data)

        return data

    def _get_cached(self, key):
        if key not in self._cache:
            return None

        # TTLチェック
        elapsed = datetime.now() - self._cache_time[key]
        if elapsed > timedelta(minutes=self._ttl_minutes):
            del self._cache[key]
            del self._cache_time[key]
            return None

        return self._cache[key]

    def _set_cache(self, key, data):
        # LRU: 古いエントリを削除
        if len(self._cache) >= self._max_cache_items:
            oldest = min(self._cache_time, key=self._cache_time.get)
            del self._cache[oldest]
            del self._cache_time[oldest]

        self._cache[key] = data
        self._cache_time[key] = datetime.now()
```

### キャッシュの効果

| 操作 | キャッシュなし | キャッシュあり |
|------|--------------|----------------|
| 同じ条件で10回アクセス | 10クエリ | 1クエリ |
| 東京→大阪→東京 | 3クエリ | 2クエリ |

### キャッシュの寿命

| 状況 | 挙動 |
|------|------|
| 30分経過 | 該当エントリ削除、再クエリ |
| アプリ再起動 | 全キャッシュ消失 |
| メモリ上限 | 古いエントリから削除 |

**許容するトレードオフ**: キャッシュクリア時に一瞬のローディングが発生

---

## 7. テーブル設計

### メインテーブル: `job_seeker_data`

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
);
```

### インデックス

```sql
-- 主要クエリ用インデックス
CREATE INDEX idx_prefecture ON job_seeker_data(prefecture);
CREATE INDEX idx_municipality ON job_seeker_data(prefecture, municipality);
CREATE INDEX idx_row_type ON job_seeker_data(row_type);
CREATE INDEX idx_pref_type ON job_seeker_data(prefecture, row_type);
```

---

## 8. 接続設定

### 環境変数

```bash
# .env
TURSO_DATABASE_URL=libsql://your-db.turso.io
TURSO_AUTH_TOKEN=your-token-here
```

### Python接続

```python
import libsql_experimental as libsql
import os

def get_db_connection():
    return libsql.connect(
        os.environ['TURSO_DATABASE_URL'],
        auth_token=os.environ['TURSO_AUTH_TOKEN']
    )
```

---

## 9. 実装手順

### Phase 1: セットアップ
1. [ ] Tursoアカウント作成
2. [ ] テスト用DB作成（kaigo-test-db）
3. [ ] 認証トークン取得
4. [ ] 環境変数設定

### Phase 2: データ投入
1. [ ] テーブル作成スクリプト
2. [ ] CSVインポートスクリプト
3. [ ] インデックス作成
4. [ ] データ検証

### Phase 3: アプリ改修
1. [ ] libsql依存関係追加
2. [ ] DB接続モジュール作成
3. [ ] キャッシュ機能実装
4. [ ] State変数のDB読み込み対応
5. [ ] CSVアップロード機能の無効化/削除

### Phase 4: テスト・デプロイ
1. [ ] ローカルテスト
2. [ ] パフォーマンス検証
3. [ ] 本番デプロイ（許可制）

---

## 10. 注意事項

### セキュリティ
- 認証トークンは絶対にGitHubにコミットしない
- 環境変数で管理（Reflex Hostingの設定画面）

### パフォーマンス
- `SELECT *` を避け、必要なカラムのみ取得
- インデックスを活用したクエリ設計
- キャッシュを積極的に活用

### 運用
- 月間使用量をモニタリング
- データ更新は月2〜3回に抑える
- 問題発生時はCSVフォールバックを用意

---

## 11. 決定事項サマリー

| 項目 | 決定内容 |
|------|----------|
| DBサービス | Turso |
| クエリ単位 | 市区町村 |
| キャッシュTTL | 30分 |
| 最大キャッシュ | 50エントリ |
| 複数職種 | 職種ごとに別DB |
| データ更新頻度 | 月2〜3回 |

---

## 12. 参考リンク

- [Turso公式](https://turso.tech)
- [Turso料金](https://turso.tech/pricing)
- [libsql Python SDK](https://github.com/libsql/libsql-experimental-python)
- [Turso CLIドキュメント](https://docs.turso.tech/cli)
