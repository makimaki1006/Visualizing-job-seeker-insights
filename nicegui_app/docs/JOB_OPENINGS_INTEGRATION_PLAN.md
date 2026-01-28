# 求人データ統合計画

**作成日**: 2026-01-28
**ステータス**: 計画段階（求人数調査開始前）

---

## 概要

需給バランスタブ（TAB7）に求人データを統合し、求職者数との比較分析を可能にする。

### 目的
- 求人数に対する求職者数の比率を計算
- 地域別の需給ギャップを可視化
- 採用難易度・競争率の定量化

---

## データ仕様

### 入力CSVフォーマット

```csv
prefecture,municipality,job_type,job_count
群馬県,伊勢崎市,介護職,45
群馬県,伊勢崎市,看護師,32
東京都,渋谷区,介護職,80
東京都,渋谷区,看護師,70
```

| カラム | 型 | 説明 |
|--------|-----|------|
| prefecture | TEXT | 都道府県名（必須） |
| municipality | TEXT | 市区町村名（必須） |
| job_type | TEXT | 職種名（必須、12種類対応） |
| job_count | INTEGER | 求人件数（必須） |

### 対応職種（12種類）
1. 介護職
2. 看護師
3. 保育士
4. 歯科衛生士
5. 歯科助手
6. 理学療法士
7. 作業療法士
8. 言語聴覚士
9. 柔道整復師
10. 鍼灸師
11. あん摩マッサージ指圧師
12. 医療事務

---

## データベース設計

### テーブル: `job_openings`

```sql
CREATE TABLE IF NOT EXISTS job_openings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prefecture TEXT NOT NULL,
    municipality TEXT NOT NULL,
    job_type TEXT NOT NULL,
    job_count INTEGER NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(prefecture, municipality, job_type)
);

-- インデックス（検索高速化）
CREATE INDEX IF NOT EXISTS idx_job_openings_job_type
ON job_openings(job_type);

CREATE INDEX IF NOT EXISTS idx_job_openings_prefecture
ON job_openings(prefecture);

CREATE INDEX IF NOT EXISTS idx_job_openings_municipality
ON job_openings(prefecture, municipality);
```

### 想定データ量
- 市区町村数: 約1,900
- 職種数: 12
- 理論最大行数: 約23,000行
- 実際の行数: 求人がある地域のみなので数千〜1万行程度と予想

---

## 計算指標

### 1. 需給比率（Supply-Demand Ratio）
```
需給比率 = 求職者数 ÷ 求人数
```
- 1.0未満: 求人過多（人手不足）
- 1.0: 均衡
- 1.0超: 求職者過多（競争激しい）

### 2. 競争率（Competition Rate）
```
競争率 = 求職者数 ÷ 求人数
```
- 表示例: 「1件あたり3.2人が応募」

### 3. 充足見込み（Fill Rate Potential）
```
充足見込み = 流入求職者数 ÷ 求人数 × 100%
```
- 流入する求職者で求人をどれだけ埋められるか

### 4. GAP影響度
```
GAP影響度 = (流入数 - 流出数) ÷ 求人数
```
- 正: 流入超過で採用しやすい
- 負: 流出超過で採用難

---

## 実装計画

### Phase 1: データ準備
- [ ] 求人数調査の実施
- [ ] CSVファイル作成（上記フォーマット）
- [ ] データ検証（市区町村名の表記揺れチェック）

### Phase 2: DB構築
- [ ] テーブル作成SQL実行（ユーザー手動）
- [ ] インポートスクリプト作成
- [ ] CSVインポート実行（ユーザー手動）
- [ ] データ検証

### Phase 3: バックエンド実装
- [ ] db_helper.pyに取得関数追加
  - `get_job_openings(prefecture, municipality, job_type)`
  - `get_supply_demand_ratio(prefecture, municipality)`
- [ ] キャッシュ機構の追加

### Phase 4: フロントエンド実装
- [ ] 需給バランスタブ（TAB7）に指標追加
  - 需給比率カード
  - 競争率表示
  - 求人数vs求職者数グラフ
- [ ] 流入元×GAP分析セクションに求人データ連携

### Phase 5: テスト・検証
- [ ] E2Eテスト
- [ ] 数値整合性チェック
- [ ] パフォーマンス確認

---

## ファイル構成（予定）

```
nicegui_app/
├── data/
│   └── job_openings.csv          # 入力CSVファイル
├── scripts/
│   └── import_job_openings.py    # インポートスクリプト
├── db_helper.py                  # 取得関数追加
└── main.py                       # TAB7表示更新
```

---

## 注意事項

### データ品質
- 市区町村名は `job_seeker_data` テーブルと完全一致させる
- 同名市区町村（府中市、伊達市等）は都道府県で区別
- 求人0件の地域もデータとして含めるか要検討

### 更新頻度
- 求人データは定期更新が必要（月次？四半期？）
- `updated_at` カラムで最終更新日を管理

### Turso制限
- 2026年2月1日に無料枠リセット予定
- インポートはリセット後に実施推奨

---

## 参考：現在のTAB7（需給バランス）の構成

```
┌─────────────────────────────────────────┐
│ 需給バランス                              │
├─────────────────────────────────────────┤
│ [概要カード]                             │
│  - 流入数 / 流出数 / GAP                 │
│  - 求職者数                              │
│                                         │
│ [流入元×GAP分析] ← ここに求人データ連携    │
│  - 流入元Top5とGAP                       │
│  - 隣接県フィルタ適用済み                 │
│                                         │
│ [追加予定]                               │
│  - 需給比率カード                        │
│  - 競争率表示                            │
│  - 求人数vs求職者数比較                   │
└─────────────────────────────────────────┘
```

---

## 変更履歴

| 日付 | 内容 |
|------|------|
| 2026-01-28 | 初版作成（計画段階） |
