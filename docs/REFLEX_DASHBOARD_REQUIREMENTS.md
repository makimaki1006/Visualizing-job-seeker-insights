# Reflexダッシュボード要件定義書

**作成日**: 2025-11-13
**ステータス**: 要件確定
**目的**: GAS統合ダッシュボード（map_complete_integrated.html）のReflex完全再現

---

## 📋 プロジェクト概要

### 目標
GAS統合ダッシュボード（map_complete_integrated.html, 4,293行）をReflexで**完全再現**する。

### 重要な原則
- ✅ **完全再現**: GASの構造・機能を100%再現すること
- ❌ **独自解釈禁止**: 勝手な判断・編集・改変は行わない
- ❌ **機能追加禁止**: 要求されていない機能は実装しない

---

## 🎨 デザイン仕様

### カラースキーム（GAS統合ダッシュボード配色）

```css
/* 背景 */
--bg: #0d1525;                           /* 深いネイビー基調 */
--panel-bg: rgba(12, 20, 37, 0.95);      /* サイドバー：半透明濃紺 */
--card: rgba(15, 23, 42, 0.82);          /* カード背景 */

/* テキスト */
--text: #f8fafc;                         /* 文字 */
--muted: rgba(226, 232, 240, 0.75);      /* 補助文字 */

/* 枠線・装飾 */
--border: rgba(148, 163, 184, 0.22);     /* 枠線 */
--shadow: -18px 0 40px rgba(10, 20, 40, 0.35); /* シャドウ */

/* アクセントカラー */
--accent: #38bdf8;                       /* メインアクセント（青） */
--accent-2: #f97316;                     /* オレンジ */
--accent-3: #a855f7;                     /* 紫 */
--accent-4: #22c55e;                     /* 緑 */
--accent-5: #facc15;                     /* 黄 */
--accent-6: #ec4899;                     /* ピンク */
```

### レイアウト

```
┌─────────────────────────────────────────────────────┐
│  全画面（100vh）                                      │
│  ┌──────────┬────────────────────────────────────┐  │
│  │          │  メインエリア                        │  │
│  │  地図    │  ┌──────────────────────────────┐  │  │
│  │  （背景  │  │  右サイドバー（440px）           │  │  │
│  │  Leaflet │  │  ┌────────────────────────┐  │  │  │
│  │  ）      │  │  │ ヘッダ                  │  │  │  │
│  │          │  │  │ - タイトル              │  │  │  │
│  │          │  │  │ - 都道府県選択          │  │  │  │
│  │          │  │  │ - 市区町村選択          │  │  │  │
│  │          │  │  │ - 選択地域サマリー      │  │  │  │
│  │          │  │  ├────────────────────────┤  │  │  │
│  │          │  │  │ タブバー（10タブ）       │  │  │  │
│  │          │  │  ├────────────────────────┤  │  │  │
│  │          │  │  │ パネルコンテンツ        │  │  │  │
│  │          │  │  │ （スクロール可能）      │  │  │  │
│  │          │  │  └────────────────────────┘  │  │  │
│  │          │  └──────────────────────────────┘  │  │
│  └──────────┴────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

**右サイドバー仕様**:
- 幅: 440px（最小280px、最大100vw-40px）
- リサイズ対応: 左端ドラッグでサイドバー幅調整可能
- 背景: `rgba(12, 20, 37, 0.95)` + `backdrop-filter: blur(12px)`
- シャドウ: `-18px 0 40px rgba(10, 20, 40, 0.35)`

---

## 🏗️ 構造仕様

### 1. 右サイドバー構成

#### ヘッダセクション
```html
<header class="app">
  <div class="app-head">
    <span class="app-title">求職者分析ダッシュボード</span>
  </div>
  <div class="app-controls">
    <div class="selector">
      <label>都道府県</label>
      <select id="prefectureSelect"></select>
    </div>
    <div class="selector">
      <label>市区町村</label>
      <select id="municipalitySelect"></select>
    </div>
    <div class="summary">
      <h1 id="cityName">-</h1>
      <p id="cityMeta">-</p>
      <div id="qualityBadge" class="quality-badge">品質未評価</div>
    </div>
  </div>
</header>
```

#### タブバー（10個）
```html
<nav class="tabbar" id="tabbar">
  <!-- JavaScriptで動的生成 -->
</nav>
```

#### パネル（10個）
```html
<div class="panels">
  <section class="panel active" data-panel="overview"></section>
  <section class="panel" data-panel="supply"></section>
  <section class="panel" data-panel="career"></section>
  <section class="panel" data-panel="urgency"></section>
  <section class="panel" data-panel="persona"></section>
  <section class="panel" data-panel="cross"></section>
  <section class="panel" data-panel="flow"></section>
  <section class="panel" data-panel="gap"></section>
  <section class="panel" data-panel="rarity"></section>
  <section class="panel" data-panel="competition"></section>
</div>
```

---

## 📊 10個のパネル仕様

### 1. overview - 概要パネル
**data-panel**: `overview`
**タブラベル**: `総合概要`（GAS: Line 2196）
**機能**: 選択地域の基本統計情報を表示

### 2. supply - 供給分析パネル
**data-panel**: `supply`
**タブラベル**: `人材供給`（GAS: Line 2197）
**機能**: Phase 7データ（人材供給密度、資格分布など）

### 3. career - キャリア分析パネル
**data-panel**: `career`
**タブラベル**: `キャリア分析`（GAS: Line 2198）
**機能**: Phase 8データ（学歴・キャリア分析）

### 4. urgency - 緊急度分析パネル
**data-panel**: `urgency`
**タブラベル**: `緊急度分析`（GAS: Line 2199）
**機能**: Phase 10データ（転職意欲・緊急度分析）

### 5. persona - ペルソナ分析パネル
**data-panel**: `persona`
**タブラベル**: `ペルソナ分析`（GAS: Line 2200）
**機能**: Phase 3データ（ペルソナ分析・難易度評価）

### 6. cross - クロス分析パネル
**data-panel**: `cross`
**タブラベル**: `クロス分析`（GAS: Line 2201）
**機能**: 多次元クロス集計（年齢×性別、年齢×就業状況など）

### 7. flow - フロー分析パネル
**data-panel**: `flow`
**タブラベル**: `フロー分析`
**機能**: Phase 6データ（地域間人材移動パターン）

**データ構造**:
```javascript
"flow": {
  "nearby_regions": [
    {
      "prefecture": "東京都",
      "municipality": "新宿区",
      "lat": 35.6938,
      "lng": 139.7036,
      "key": "tokyo-shinjuku",
      "type": "inflow",      // 流入
      "flow_count": 234
    },
    {
      "prefecture": "東京都",
      "municipality": "港区",
      "type": "outflow",     // 流出
      "flow_count": 287
    }
  ]
}
```

**表示内容**:
- 近隣地域へのフロー（inflow/outflow）
- 地図上での矢印表示
- フロー件数テーブル

### 8. gap - 需給ギャップパネル
**data-panel**: `gap`
**タブラベル**: `需給バランス`（GAS: Line 2203）
**機能**: Phase 12データ（需要・供給・ギャップ分析）

### 9. rarity - 希少性パネル
**data-panel**: `rarity`
**タブラベル**: `希少人材分析`（GAS: Line 2204）
**機能**: Phase 13データ（希少人材スコアリング）

### 10. competition - 競争プロファイルパネル
**data-panel**: `competition`
**タブラベル**: `人材プロファイル`（GAS: Line 2205）
**機能**: Phase 14データ（競争プロファイル分析）

---

## 🔧 実装要件

### 必須機能

#### 1. CSVデータロード
- ✅ ドラッグ&ドロップでCSVアップロード
- ✅ `MapComplete_Complete_All_FIXED.csv`（20,590行×36列）対応
- ✅ UTF-8 BOM対応（`encoding='utf-8-sig'`）

#### 2. 地域フィルタリング
- ✅ 都道府県選択（プルダウン）
- ✅ 市区町村選択（都道府県に応じて動的更新）
- ✅ フィルタ変更時に全パネルデータ自動更新

#### 3. パネル切り替え
- ✅ タブクリックでアクティブパネル切り替え
- ✅ アクティブタブのハイライト表示
- ✅ スムーズなトランジション

#### 4. データ表示
- ✅ 各パネルで適切なグラフ・テーブル表示
- ✅ データがない場合のプレースホルダー表示
- ✅ レスポンシブ対応

#### 5. 地図表示（Phase 2実装予定）
- ⏳ Leaflet.js統合
- ⏳ 市区町村境界ポリゴン表示
- ⏳ クリックで市区町村選択
- ⏳ プルダウン選択と地図ハイライトの双方向同期

---

## 📁 データ構造

### CSVファイル仕様

**ファイル名**: `MapComplete_Complete_All_FIXED.csv`
**行数**: 20,590行
**列数**: 36列
**エンコーディング**: UTF-8 BOM

### row_type（データ種別）

| row_type | 説明 | 対応パネル | 件数 |
|----------|------|-----------|------|
| SUMMARY | サマリー情報 | overview | - |
| AGE_GENDER | 年齢×性別クロス集計 | cross | - |
| PERSONA_MUNI | 市区町村別ペルソナ | persona | - |
| FLOW | フロー分析 | flow | - |
| GAP | 需給ギャップ | gap | - |
| RARITY | 希少性スコア | rarity | - |
| COMPETITION | 競争プロファイル | competition | - |
| CAREER_CROSS | 学歴×年齢クロス集計 | career | 2,105 |
| URGENCY_AGE | 緊急度×年齢クロス集計 | urgency | 2,942 |
| URGENCY_EMPLOYMENT | 緊急度×就業状況クロス集計 | urgency | 1,666 |
| SUPPLY_* | 供給分析系 | supply | - |

### 主要カラム

```python
[
    'row_type',           # データ種別
    'prefecture',         # 都道府県
    'municipality',       # 市区町村
    'category1',          # カテゴリ1（学歴、緊急度など）
    'category2',          # カテゴリ2（年齢層、就業状況など）
    'category3',          # カテゴリ3
    'count',              # 件数
    'applicant_count',    # 申請者数
    'avg_age',            # 平均年齢
    'male_count',         # 男性数
    'female_count',       # 女性数
    'latitude',           # 緯度
    'longitude',          # 経度
    'rarity_score',       # 希少性スコア
    'gap',                # 需給ギャップ
    'demand_count',       # 需要数
    'supply_count',       # 供給数
    # ... 他20カラム
]
```

---

## 🚫 実装禁止事項

### ❌ やってはいけないこと

1. **GASの構造を変更する**
   - タブ数を変える
   - タブ名を変える
   - パネルの順序を変える

2. **独自機能を追加する**
   - 要求されていないグラフを追加
   - 独自のフィルタを追加
   - 独自のダッシュボードを追加

3. **デザインを勝手に変える**
   - 配色を変える
   - レイアウトを変える
   - フォントを変える

4. **データ構造を変更する**
   - CSVフォーマットを変える
   - カラム名を変える
   - row_typeを追加/削除する

### ⚠️ 確認が必要なこと

以下の変更を行う場合は、必ず事前に確認すること：
- 新しいグラフタイプの追加
- データ集計ロジックの変更
- UIコンポーネントの追加
- パフォーマンス最適化による構造変更

---

## 🎯 実装優先順位

### Phase 1: 基盤実装（完了）
- ✅ GAS配色適用
- ✅ サイドバーレイアウト
- ✅ CSVアップロード機能
- ✅ 都道府県・市区町村フィルタ

### Phase 2: パネル実装（次のステップ）
- ⏳ 10個のパネルコンポーネント作成
- ⏳ タブ切り替え機能実装
- ⏳ 各パネルのデータ表示機能

### Phase 3: グラフ・可視化
- ⏳ Plotly.jsグラフ統合
- ⏳ テーブル表示
- ⏳ KPIカード表示

### Phase 4: 地図統合（将来）
- ⏳ Leaflet.js統合
- ⏳ 地図クリック連動
- ⏳ ポリゴン表示

---

## 📝 変更履歴

### 2025-11-13 v1.1
- **完全構造解読完了**: map_complete_integrated.html（4,293行）を完全解析
- **10パネルデータ構造確定**: 各パネルの正確なデータ構造をJavaScriptコードから抽出
- **タブラベル修正**: GAS実装の正確な表記に修正（絵文字なし）
  - overview: `総合概要` (Line 2196)
  - supply: `人材供給` (Line 2197)
  - career: `キャリア分析` (Line 2198)
  - urgency: `緊急度分析` (Line 2199)
  - persona: `ペルソナ分析` (Line 2200)
  - cross: `クロス分析` (Line 2201)
  - flow: `フロー分析` (Line 2202)
  - gap: `需給バランス` (Line 2203)
  - rarity: `希少人材分析` (Line 2204)
  - competition: `人材プロファイル` (Line 2205)
- **flow パネル構造追加**: nearby_regions配列（inflow/outflow）の詳細構造を追記

### 2025-11-13 v1.0
- 初版作成
- GAS統合ダッシュボードの基本構造解析
- 10個のパネル仕様（基本）確定
- デザイン仕様確定
- 実装禁止事項明確化

---

## 🔗 関連ドキュメント

- [GAS統合ダッシュボード](../gas_deployment/map_complete_integrated.html)
- [MapComplete統合CSV仕様](../python_scripts/data/output_v2/)
- [GAS完全機能一覧](./GAS_COMPLETE_FEATURE_LIST.md)
