# map_complete_prototype_Ver2.html - 完全分析レポート

**ファイル**: `gas_files/html/map_complete_prototype_Ver2.html`
**サイズ**: 73KB、2361行
**最終更新**: 2025年10月31日
**ステータス**: 本番運用可能なプロトタイプ

---

## 📋 目次

1. [概要](#概要)
2. [技術スタック](#技術スタック)
3. [UI構成](#ui構成)
4. [データ構造](#データ構造)
5. [タブ別機能](#タブ別機能)
6. [GAS連携](#gas連携)
7. [フロー分析タブ追加設計](#フロー分析タブ追加設計)

---

## 概要

### 特徴

**Job Medley Insight Suite - MapComplete プロトタイプ**は、求職者データを市区町村別に可視化する統合ダッシュボードです。

**主要機能**:
- ✅ Leaflet.js地図表示（OpenStreetMap）
- ✅ 右サイドバー（リサイズ可能、280px-最大幅）
- ✅ 6タブ式UI（総合概要、人材供給、キャリア分析、緊急度分析、ペルソナ分析、クロス分析）
- ✅ 市区町村選択機能
- ✅ 動的チャート表示（Chart.js v4）
- ✅ GAS連携（google.script.run）
- ✅ フォールバックデータ（ローカル実行対応）

**デザイン特性**:
- **配色**: 深いネイビー基調（前システム「Talent Insight」を踏襲）
- **レスポンシブ**: サイドバーリサイズ対応
- **アクセシビリティ**: ARIA属性対応

---

## 技術スタック

### 外部ライブラリ

| ライブラリ | バージョン | CDN | 用途 |
|-----------|---------|-----|------|
| **Leaflet.js** | 1.9.4 | unpkg.com | 地図表示基盤 |
| **Chart.js** | 4.4.1 | jsdelivr | チャート描画 |

**Integrity属性**: セキュリティ検証あり

### 内部実装

| 要素 | 行数（概算） | 説明 |
|------|------------|------|
| **CSS** | ~250行 | カスタムCSS変数、レスポンシブデザイン |
| **HTML構造** | ~60行 | 最小限のマークアップ、動的生成前提 |
| **JavaScript** | ~1,700行 | ロジック、チャート、GAS連携 |
| **埋め込みデータ** | ~400行 | サンプルデータ（JSON） |

---

## UI構成

### レイアウト構造

```
┌─────────────────────────────────────────────────────────────────┐
│ #map（全画面背景、Leaflet.js地図）                                 │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ .sidebar（右サイドバー、440px、リサイズ可能）              │   │
│  │ ┌───────────────────────────────────────────────────┐   │   │
│  │ │ header.app                                       │   │   │
│  │ │ ├ Job Medley Insight Suite                       │   │   │
│  │ │ ├ 対象エリア選択（select#citySelect）             │   │   │
│  │ │ └ 選択地域名表示（#cityName, #cityMeta）          │   │   │
│  │ └───────────────────────────────────────────────────┘   │   │
│  │ ┌───────────────────────────────────────────────────┐   │   │
│  │ │ nav.tabbar（6タブボタン）                         │   │   │
│  │ └───────────────────────────────────────────────────┘   │   │
│  │ ┌───────────────────────────────────────────────────┐   │   │
│  │ │ .panels（タブコンテンツ、スクロール可能）          │   │   │
│  │ │ ├ .panel[data-panel="overview"]（総合概要）       │   │   │
│  │ │ ├ .panel[data-panel="supply"]（人材供給）         │   │   │
│  │ │ ├ .panel[data-panel="career"]（キャリア分析）     │   │   │
│  │ │ ├ .panel[data-panel="urgency"]（緊急度分析）      │   │   │
│  │ │ ├ .panel[data-panel="persona"]（ペルソナ分析）    │   │   │
│  │ │ └ .panel[data-panel="cross"]（クロス分析）        │   │   │
│  │ └───────────────────────────────────────────────────┘   │   │
│  │                                                          │   │
│  │ .resize-handle（左端、14px幅、ドラッグ可能）            │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### リサイズ機能

**仕様**:
- 最小幅: 280px
- 最大幅: `calc(100vw - 40px)`
- リサイズハンドル: 左端14px幅、グラデーション背景
- リサイズ中: `body.resizing`クラス付与、カーソル固定

**実装** (行1692-1725):
```javascript
handle.addEventListener('pointerdown', (e)=>{
  pointerId = e.pointerId;
  startX = e.clientX;
  startW = sidebar.getBoundingClientRect().width;
  handle.setPointerCapture(pointerId);
  document.body.classList.add('resizing');
  sidebar.classList.add('resizing');
});

handle.addEventListener('pointermove', (e)=>{
  if(pointerId===null) return;
  const delta = startX - e.clientX; // 右サイドバーなので逆向き
  const maxW = Math.max(MIN_W, window.innerWidth - 40);
  let w = startW + delta;
  w = Math.max(MIN_W, Math.min(maxW, w));
  sidebar.style.width = w + 'px';
  requestAnimationFrame(()=> Object.values(charts).forEach(ch=> ch.resize()));
});
```

---

## データ構造

### Payload形式

**GASから受信するデータ構造** (normalizePayload関数、行1643-1654):

```javascript
{
  cities: [          // 市区町村データ配列
    {
      id: "kyoto-fushimi",
      name: "京都府 京都市伏見区",
      center: [34.9327, 135.7656],  // 地図中心座標
      region: {
        key: "京都府京都市伏見区",
        prefecture: "京都府",
        municipality: "京都市伏見区"
      },
      quality: {
        score: 82,
        level: "EXCELLENT",
        color: "#38bdf8"
      },
      overview: { /* 総合概要データ */ },
      supply: { /* 人材供給データ */ },
      career: { /* キャリア分析データ */ },
      urgency: { /* 緊急度分析データ */ },
      persona: { /* ペルソナ分析データ */ },
      cross: { /* クロス分析データ */ }
    }
  ],
  selectedRegion: {  // 選択中地域
    key: "京都府京都市伏見区",
    prefecture: "京都府",
    municipality: "京都市伏見区"
  },
  regionOptions: null,  // 地域選択オプション（未使用）
  availableRegions: [   // 選択可能地域リスト
    {
      key: "京都府京都市伏見区",
      prefecture: "京都府",
      municipality: "京都市伏見区",
      label: "京都府 京都市伏見区"
    }
  ]
}
```

### 各タブのデータ構造

#### 1. overview（総合概要）

```javascript
overview: {
  kpis: [
    {
      label: "総求職者数",
      value: 1748,
      unit: "人"
    },
    {
      label: "平均年齢",
      value: 48.7,
      unit: "歳"
    },
    {
      label: "男女比",
      labels: ["男性", "女性"],
      values: [628, 1120],
      unit: "人"
    }
  ],
  age_gender: {
    age_labels: ["20代", "30代", "40代", "50代", "60代以上"],
    age_totals: [150, 280, 420, 560, 338],
    gender_labels: ["男性", "女性"],
    gender_totals: [628, 1120]
  },
  averages: {
    "平均年齢": 48.7,
    "平均資格数": 1.72
  }
}
```

#### 2. supply（人材供給）

```javascript
supply: {
  status_counts: {
    "就業中": 1200,
    "離職中": 450,
    "在学中": 98
  },
  national_license_count: 856,
  avg_qualifications: 1.72,
  qualification_buckets: [
    { label: "介護・福祉", value: 920 },
    { label: "医療", value: 450 },
    { label: "その他", value: 378 }
  ]
}
```

#### 3. career（キャリア分析）

```javascript
career: {
  summary: {
    "介護職": 850,
    "看護職": 320,
    "事務職": 280
  },
  employment_age: {
    age_labels: ["20代", "30代", "40代", "50代", "60代以上"],
    rows: [
      { label: "就業中", values: [80, 200, 320, 450, 150] },
      { label: "離職中", values: [50, 60, 80, 90, 170] },
      { label: "在学中", values: [20, 20, 20, 20, 18] }
    ]
  }
}
```

#### 4. urgency（緊急度分析）

```javascript
urgency: {
  summary: {
    "A:高い": 520,
    "B:中": 780,
    "C:低": 448
  },
  age_cross: {
    age_labels: ["20代", "30代", "40代", "50代", "60代以上"],
    rows: [
      { label: "A:高い", values: [50, 100, 150, 120, 100] },
      { label: "B:中", values: [70, 120, 180, 250, 160] },
      { label: "C:低", values: [30, 60, 90, 190, 78] }
    ]
  }
}
```

#### 5. persona（ペルソナ分析）

```javascript
persona: {
  counts: {
    "積極転職型": 420,
    "慎重検討型": 680,
    "情報収集型": 648
  },
  qualification_summary: [
    {
      persona: "積極転職型",
      avg_qualifications: 2.1,
      top_bucket: "介護・福祉",
      count: 420
    }
  ]
}
```

#### 6. cross（クロス分析）

```javascript
cross: {
  ageGenderMatrix: {
    rows: ["20代", "30代", "40代", "50代", "60代以上"],
    columns: ["男性", "女性"],
    values: [
      [60, 90],
      [110, 170],
      [165, 255],
      [220, 340],
      [133, 205]
    ],
    row_totals: [150, 280, 420, 560, 338],
    column_totals: [688, 1060],
    total: 1748
  },
  careerMatrix: { /* 同様の構造 */ },
  urgencyAgeMatrix: { /* 同様の構造 */ },
  urgencyEmploymentMatrix: { /* 同様の構造 */ }
}
```

---

## タブ別機能

### タブ構成（TABS配列、行1728-1735）

```javascript
const TABS = [
  {id:'overview',label:'総合概要'},
  {id:'supply',label:'人材供給'},
  {id:'career',label:'キャリア分析'},
  {id:'urgency',label:'緊急度分析'},
  {id:'persona',label:'ペルソナ分析'},
  {id:'cross',label:'クロス分析'}
];
```

### 1. 総合概要（overview）

**関数**: `renderOverview(city)` (行1854-1890)

**表示内容**:
- **KPIカード**: 総求職者数、平均年齢、男女比等
- **主要指標の平均値**: テーブル形式
- **ビジュアルサマリー**:
  - 性別構成（ドーナツチャート）
  - 年齢帯別求職者数（棒グラフ）

**チャート**:
- `ovGender`: ドーナツチャート（Chart.js doughnut）
- `ovAge`: 棒グラフ（Chart.js bar）

### 2. 人材供給（supply）

**関数**: `renderSupply(city)` (行1892-1949)

**表示内容**:
- **ステータスサマリー**: 就業中/離職中/在学中の人数
- **資格保有情報**: 国家資格保有者数、平均資格保有数
- **ビジュアル**:
  - 就業ステータス（棒グラフ）
  - 保有資格カテゴリ（ドーナツチャート）
- **保有資格カテゴリテーブル**: 詳細内訳
- **ペルソナ別平均資格保有数**: チャート+テーブル

**チャート**:
- `spStatus`: 棒グラフ（就業ステータス）
- `spQual`: ドーナツチャート（資格カテゴリ）
- `spPersonaQual`: 横棒グラフ（ペルソナ別平均資格数）

### 3. キャリア分析（career）

**関数**: `renderCareer(city)` (行1951-1969)

**表示内容**:
- **キャリアサマリー**: 職種別人数
- **就業状態×年齢層クロス集計**: 積み上げ棒グラフ
- **マトリクステーブル**: 詳細数値

**チャート**:
- `crCareer`: 棒グラフ（職種別）
- `crEmploymentAge`: 積み上げ棒グラフ（就業状態×年齢）

### 4. 緊急度分析（urgency）

**関数**: `renderUrgency(city)` (行1971-2012)

**表示内容**:
- **緊急度サマリー**: A（高い）/B（中）/C（低）の人数
- **年齢層×緊急度クロス集計**: 積み上げ棒グラフ
- **マトリクステーブル**: 詳細数値

**チャート**:
- `ugSummary`: ドーナツチャート（緊急度分布）
- `ugAgeCross`: 積み上げ棒グラフ（年齢層×緊急度）

### 5. ペルソナ分析（persona）

**関数**: `renderPersona(city)` (行2014-2048)

**表示内容**:
- **ペルソナ別人数**: 積極転職型、慎重検討型、情報収集型
- **ペルソナ分布**: ドーナツチャート
- **ペルソナ詳細レコードテーブル**: ペルソナ別詳細情報

**チャート**:
- `psPersona`: ドーナツチャート（ペルソナ分布）

### 6. クロス分析（cross）

**関数**: `renderCross(city)` (行2131-2224)

**表示内容**:
- **4つのマトリクス分析**:
  1. 年齢層×性別
  2. キャリア×年齢層
  3. 年齢層×緊急度
  4. 就業状態×緊急度

**各マトリクス**:
- ヒートマップ風テーブル（行・列・セル値、合計行・合計列）
- 積み上げ棒グラフ（行ごとの内訳）

**チャート**:
- `crAgeGender`: 積み上げ棒グラフ（年齢層×性別）
- `crCareerAge`: 積み上げ棒グラフ（キャリア×年齢）
- `crUrgencyAge`: 積み上げ棒グラフ（年齢層×緊急度）
- `crUrgencyEmployment`: 積み上げ棒グラフ（就業状態×緊急度）

---

## GAS連携

### データ取得フロー

```
起動時
  ↓
loadData() (行2320-2348)
  ↓
google.script.run.getMapCompleteData(pref, muni)
  ↓
GAS側で処理
  ↓
withSuccessHandler(applyPayload)
  ↓
applyPayload(payload) (行2295-2318)
  ↓
normalizePayload(payload) (行1643-1654)
  ↓
DATA配列に格納
  ↓
renderAll() (行2287-2293)
  ↓
各タブをレンダリング
```

### GAS側関数名

**必須関数**: `getMapCompleteData(prefecture, municipality)`

**期待される戻り値**:
```javascript
{
  cities: [ /* 市区町村データ配列 */ ],
  selectedRegion: { /* 選択中地域 */ },
  availableRegions: [ /* 選択可能地域リスト */ ]
}
```

### フォールバック機能

**embeddedData** (行295-1641):
- 埋め込みサンプルデータ（JSON形式）
- GAS環境外（ローカル実行）でも動作確認可能
- 約400行のサンプルデータ

**フォールバックロジック** (行2320-2348):
1. `google.script.run`が利用可能か確認
2. 利用可能 → GASからデータ取得
3. 利用不可またはエラー → embeddedDataを使用

---

## 地図機能

### Leaflet.js実装

**初期化**: `initMap()` (行1681-1689)

```javascript
function initMap(){
  map = L.map('map',{zoomControl:true});
  baseLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{
    maxZoom:19,
    attribution:'&copy; OpenStreetMap'
  });
  baseLayer.addTo(map);
  markersLayer = L.layerGroup().addTo(map);
  const center = (DATA?.[activeCity]?.center && Array.isArray(DATA[activeCity].center))
    ? DATA[activeCity].center
    : [35.68, 139.76];
  map.setView(center, 11);
  renderMarkers();
}
```

**マーカー描画**: `renderMarkers()` (行1809-1831)

```javascript
function renderMarkers(){
  if(!map || !markersLayer){
    return;
  }
  markersLayer.clearLayers();
  DATA.forEach((city, idx)=>{
    if(!city || !Array.isArray(city.center) || city.center.length < 2){
      return;
    }
    const color = city.quality?.color || '#38bdf8';
    const isActive = idx === activeCity;
    const marker = L.circleMarker(city.center, {
      radius: isActive ? 11 : 8,
      weight: isActive ? 3 : 1.6,
      color: color,
      fillColor: color,
      fillOpacity: isActive ? 0.92 : 0.72
    });
    marker.on('click', ()=> selectCityByIndex(idx, city));
    marker.bindTooltip(city.name || '地域', {direction:'top'});
    markersLayer.addLayer(marker);
  });
}
```

**特徴**:
- **CircleMarker**: 各市区町村を円形マーカーで表示
- **色分け**: 品質スコアに応じた色（デフォルト: `#38bdf8`）
- **サイズ**: アクティブ地域は大きく表示（11px vs 8px）
- **インタラクティブ**: クリックで地域選択、ツールチップ表示

---

## チャート機能

### Chart.js統合

**管理**: `charts`オブジェクト（行1671）

```javascript
let charts = {};
```

**作成・更新**: `upsertChart(id, config)` (行不明、推定実装あり)

**色パレット**: `COLOR`配列（推定）
```javascript
const COLOR = [
  '#38bdf8',  // 青（アクセント）
  '#f97316',  // オレンジ
  '#a855f7',  // 紫
  '#22c55e',  // 緑
  '#facc15',  // 黄
  '#ec4899'   // ピンク
];
```

**共通オプション**: `chartBase()` (推定実装あり)
```javascript
function chartBase(){
  return {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        labels: { color: '#f8fafc' }
      }
    }
  };
}
```

### チャート一覧

| ID | タブ | 種類 | データソース |
|----|------|------|-------------|
| `ovGender` | overview | doughnut | age_gender.gender_totals |
| `ovAge` | overview | bar | age_gender.age_totals |
| `spStatus` | supply | bar | status_counts |
| `spQual` | supply | doughnut | qualification_buckets |
| `spPersonaQual` | supply | bar (horizontal) | persona.qualification_summary |
| `crCareer` | career | bar | career.summary |
| `crEmploymentAge` | career | bar (stacked) | career.employment_age |
| `ugSummary` | urgency | doughnut | urgency.summary |
| `ugAgeCross` | urgency | bar (stacked) | urgency.age_cross |
| `psPersona` | persona | doughnut | persona.counts |
| `crAgeGender` | cross | bar (stacked) | cross.ageGenderMatrix |
| `crCareerAge` | cross | bar (stacked) | cross.careerMatrix |
| `crUrgencyAge` | cross | bar (stacked) | cross.urgencyAgeMatrix |
| `crUrgencyEmployment` | cross | bar (stacked) | cross.urgencyEmploymentMatrix |

---

## フロー分析タブ追加設計

### 現状の課題

**❌ フロー分析機能が未実装**:
- 居住地→希望勤務地の矢印フロー表示なし
- Phase 6データ（AggregatedFlowEdges.csv）が活用されていない
- 地域間の人材移動傾向が可視化されていない

### 追加するタブ: 「フロー分析」

**タブID**: `flow`
**タブラベル**: `フロー分析`

### データ構造（新規）

**city.flowに追加**:

```javascript
flow: {
  inflows: [  // この地域への流入フロー（TOP10）
    {
      origin: "奈良県生駒郡平群町",
      origin_pref: "奈良県",
      origin_muni: "生駒郡平群町",
      flow_count: 87,
      avg_age: 35.2,
      gender_mode: "男性"
    }
  ],
  outflows: [  // この地域からの流出フロー（TOP10）
    {
      destination: "大阪府東大阪市",
      destination_pref: "大阪府",
      destination_muni: "東大阪市",
      flow_count: 52,
      avg_age: 41.5,
      gender_mode: "女性"
    }
  ],
  summary: {
    total_inflow: 677,   // 総流入数
    total_outflow: 257,  // 総流出数
    net_flow: 420        // 純流入数（inflow - outflow）
  }
}
```

### UI設計

**構成**:

```
┌─────────────────────────────────────────────────────────────┐
│ フロー分析タブ                                               │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│ 【フローサマリー】                                           │
│ ┌──────────┬──────────┬──────────┐                       │
│ │ 総流入数 │ 総流出数 │ 純流入数 │                       │
│ │  677人  │  257人  │  +420人 │                       │
│ └──────────┴──────────┴──────────┘                       │
│                                                              │
│ 【ビジュアル】                                               │
│ ┌────────────────────┬────────────────────┐               │
│ │ 流入TOP10          │ 流出TOP10          │               │
│ │ (横棒グラフ)       │ (横棒グラフ)       │               │
│ └────────────────────┴────────────────────┘               │
│                                                              │
│ 【詳細テーブル】                                             │
│ ┌──────────────────────────────────────────┐               │
│ │ 流入元地域 | フロー数 | 平均年齢 | 性別   │               │
│ ├──────────────────────────────────────────┤               │
│ │ 奈良県生駒郡平群町 | 87人 | 35.2歳 | 男性 │               │
│ │ ...                                       │               │
│ └──────────────────────────────────────────┘               │
│                                                              │
│ ┌──────────────────────────────────────────┐               │
│ │ 流出先地域 | フロー数 | 平均年齢 | 性別   │               │
│ ├──────────────────────────────────────────┤               │
│ │ 大阪府東大阪市 | 52人 | 41.5歳 | 女性     │               │
│ │ ...                                       │               │
│ └──────────────────────────────────────────┘               │
└─────────────────────────────────────────────────────────────┘
```

### 地図上の矢印フロー表示（拡張機能）

**Phase 2機能として追加**:

1. **Leaflet.PolylineDecorator導入**:
   ```html
   <script src="https://cdn.jsdelivr.net/npm/leaflet-polylinedecorator@1.6.0/dist/leaflet.polylineDecorator.min.js"></script>
   ```

2. **矢印描画関数追加**:
   ```javascript
   function renderFlowArrows(city){
     if(!map || !city.flow) return;

     // 既存の矢印をクリア
     if(flowArrowsLayer){
       flowArrowsLayer.clearLayers();
     } else {
       flowArrowsLayer = L.layerGroup().addTo(map);
     }

     // 流入フローを描画
     city.flow.inflows.forEach(flow => {
       const originCoords = getCoordinates(flow.origin);
       const destCoords = city.center;

       if(originCoords && destCoords){
         drawFlowArrow(originCoords, destCoords, flow.flow_count, '#22c55e'); // 緑（流入）
       }
     });

     // 流出フローを描画
     city.flow.outflows.forEach(flow => {
       const originCoords = city.center;
       const destCoords = getCoordinates(flow.destination);

       if(originCoords && destCoords){
         drawFlowArrow(originCoords, destCoords, flow.flow_count, '#f97316'); // オレンジ（流出）
       }
     });
   }

   function drawFlowArrow(originLatLng, destLatLng, flowCount, color){
     const polyline = L.polyline([originLatLng, destLatLng], {
       color: color,
       weight: Math.min(flowCount / 10, 8),
       opacity: 0.6
     });

     const decorator = L.polylineDecorator(polyline, {
       patterns: [
         {
           offset: '100%',
           repeat: 0,
           symbol: L.Symbol.arrowHead({
             pixelSize: 10,
             polygon: false,
             pathOptions: { stroke: true, color: color }
           })
         }
       ]
     });

     polyline.bindPopup(`フロー数: ${flowCount}人`);
     flowArrowsLayer.addLayer(polyline);
     flowArrowsLayer.addLayer(decorator);
   }

   function getCoordinates(locationKey){
     // DATAから該当地域の座標を取得
     const city = DATA.find(c => c.region && c.region.key === locationKey);
     return city ? city.center : null;
   }
   ```

### renderFlow()関数（新規実装）

```javascript
function renderFlow(city){
  const panel = qs('.panel[data-panel="flow"]');
  const f = city.flow || {inflows:[], outflows:[], summary:{}};

  const summaryHTML = `
    <div class="kpis">
      <div class="kpi"><div class="label">総流入数</div><div class="value">${numberFmt.format(f.summary.total_inflow||0)}人</div></div>
      <div class="kpi"><div class="label">総流出数</div><div class="value">${numberFmt.format(f.summary.total_outflow||0)}人</div></div>
      <div class="kpi"><div class="label">純流入数</div><div class="value">${f.summary.net_flow>=0?'+':''}${numberFmt.format(f.summary.net_flow||0)}人</div></div>
    </div>
  `;

  const inflowRows = f.inflows.map(flow => `
    <tr>
      <td>${flow.origin}</td>
      <td>${numberFmt.format(flow.flow_count)}人</td>
      <td>${Number(flow.avg_age).toFixed(1)}歳</td>
      <td>${flow.gender_mode}</td>
    </tr>
  `).join('');

  const outflowRows = f.outflows.map(flow => `
    <tr>
      <td>${flow.destination}</td>
      <td>${numberFmt.format(flow.flow_count)}人</td>
      <td>${Number(flow.avg_age).toFixed(1)}歳</td>
      <td>${flow.gender_mode}</td>
    </tr>
  `).join('');

  panel.innerHTML = `
    <div class="section">
      <h2>フローサマリー</h2>
      ${summaryHTML}
    </div>

    <div class="section">
      <h2>ビジュアル</h2>
      <div class="chart-grid">
        <div class="chart-card"><header>流入TOP10</header><div class="chart-body"><canvas id="flInflow"></canvas></div></div>
        <div class="chart-card"><header>流出TOP10</header><div class="chart-body"><canvas id="flOutflow"></canvas></div></div>
      </div>
    </div>

    <div class="section">
      <h2>流入詳細（TOP10）</h2>
      <div class="table-wrap">
        <table class="data-table">
          <thead><tr><th>流入元地域</th><th>フロー数</th><th>平均年齢</th><th>性別</th></tr></thead>
          <tbody>${inflowRows}</tbody>
        </table>
      </div>
    </div>

    <div class="section">
      <h2>流出詳細（TOP10）</h2>
      <div class="table-wrap">
        <table class="data-table">
          <thead><tr><th>流出先地域</th><th>フロー数</th><th>平均年齢</th><th>性別</th></tr></thead>
          <tbody>${outflowRows}</tbody>
        </table>
      </div>
    </div>
  `;

  // チャート描画
  upsertChart('flInflow', {
    type: 'bar',
    data: {
      labels: f.inflows.map(flow => flow.origin.split('').slice(-6).join('')), // 最後6文字のみ
      datasets: [{
        label: 'フロー数',
        data: f.inflows.map(flow => flow.flow_count),
        backgroundColor: '#22c55e' // 緑（流入）
      }]
    },
    options: {
      ...chartBase(),
      indexAxis: 'y',
      scales: { x: { beginAtZero: true } },
      plugins: { legend: { display: false } }
    }
  });

  upsertChart('flOutflow', {
    type: 'bar',
    data: {
      labels: f.outflows.map(flow => flow.destination.split('').slice(-6).join('')),
      datasets: [{
        label: 'フロー数',
        data: f.outflows.map(flow => flow.flow_count),
        backgroundColor: '#f97316' // オレンジ（流出）
      }]
    },
    options: {
      ...chartBase(),
      indexAxis: 'y',
      scales: { x: { beginAtZero: true } },
      plugins: { legend: { display: false } }
    }
  });

  // 地図上に矢印フローを描画（Phase 2機能）
  // renderFlowArrows(city);
}
```

### GAS側対応（必須）

**getMapCompleteData()の拡張**:

```javascript
function getMapCompleteData(prefecture, municipality){
  // 既存処理...

  const city = {
    // 既存データ...
    flow: getFlowData(prefecture, municipality)  // 新規追加
  };

  return {
    cities: [city],
    selectedRegion: { /* ... */ },
    availableRegions: [ /* ... */ ]
  };
}

function getFlowData(prefecture, municipality){
  const ss = SpreadsheetApp.getActiveSpreadsheet();

  // Phase6_AggregatedFlowEdgesを読み込み
  const aggregatedFlowSheet = ss.getSheetByName('Phase6_AggregatedFlowEdges');
  if(!aggregatedFlowSheet){
    return { inflows: [], outflows: [], summary: {} };
  }

  const data = aggregatedFlowSheet.getDataRange().getValues();
  const headers = data[0];
  const locationKey = `${prefecture}${municipality}`;

  const inflows = [];
  const outflows = [];
  let totalInflow = 0;
  let totalOutflow = 0;

  for(let i = 1; i < data.length; i++){
    const row = data[i];
    const origin = row[headers.indexOf('origin')];
    const destination = row[headers.indexOf('destination')];
    const flowCount = row[headers.indexOf('flow_count')];

    // 流入（destination = この地域）
    if(destination === locationKey){
      inflows.push({
        origin: origin,
        origin_pref: row[headers.indexOf('origin_pref')],
        origin_muni: row[headers.indexOf('origin_muni')],
        flow_count: flowCount,
        avg_age: row[headers.indexOf('avg_age')],
        gender_mode: row[headers.indexOf('gender_mode')]
      });
      totalInflow += flowCount;
    }

    // 流出（origin = この地域）
    if(origin === locationKey){
      outflows.push({
        destination: destination,
        destination_pref: row[headers.indexOf('destination_pref')],
        destination_muni: row[headers.indexOf('destination_muni')],
        flow_count: flowCount,
        avg_age: row[headers.indexOf('avg_age')],
        gender_mode: row[headers.indexOf('gender_mode')]
      });
      totalOutflow += flowCount;
    }
  }

  // フロー数でソートしてTOP10のみ
  inflows.sort((a, b) => b.flow_count - a.flow_count);
  outflows.sort((a, b) => b.flow_count - a.flow_count);

  return {
    inflows: inflows.slice(0, 10),
    outflows: outflows.slice(0, 10),
    summary: {
      total_inflow: totalInflow,
      total_outflow: totalOutflow,
      net_flow: totalInflow - totalOutflow
    }
  };
}
```

---

## 実装ステップ

### Phase 1: フロー分析タブの基本実装（1-2日）

1. **TABS配列に追加** (行1728):
   ```javascript
   {id:'flow',label:'フロー分析'}
   ```

2. **パネル要素追加** (行284):
   ```html
   <section class="panel" data-panel="flow"></section>
   ```

3. **renderFlow()関数実装** (行2226以降):
   - 上記の`renderFlow()`関数を追加

4. **renderCity()に追加** (行2226-2285):
   ```javascript
   if(activeTab === 'flow'){ renderFlow(c); }
   ```

### Phase 2: 地図上矢印フロー表示（2-3日）

1. **Leaflet.PolylineDecorator追加** (行11以降):
   ```html
   <script src="https://cdn.jsdelivr.net/npm/leaflet-polylinedecorator@1.6.0/dist/leaflet.polylineDecorator.min.js"></script>
   ```

2. **flowArrowsLayer変数追加** (行1672):
   ```javascript
   let flowArrowsLayer;
   ```

3. **renderFlowArrows()関数実装**:
   - 上記の関数を追加

4. **renderFlow()からの呼び出し**:
   - コメントアウトを解除

### Phase 3: GAS側データ提供（1日）

1. **getFlowData()関数追加**:
   - 上記のGAS側関数を実装

2. **getMapCompleteData()の拡張**:
   - `flow: getFlowData(prefecture, municipality)`を追加

### Phase 4: テスト・最適化（1日）

1. **E2Eテスト**: 各タブの動作確認
2. **パフォーマンステスト**: 矢印フロー表示時のレンダリング速度
3. **UI調整**: 配色、レイアウト微調整

---

## まとめ

### 現状の強み

- ✅ 堅牢なタブ式UI
- ✅ 豊富なチャート機能（Chart.js v4）
- ✅ GAS連携とフォールバック機能
- ✅ リサイズ可能なサイドバー
- ✅ 統一された配色（Talent Insight踏襲）

### フロー分析タブ追加によるメリット

- ✅ Phase 6データ（AggregatedFlowEdges.csv）を完全活用
- ✅ 地域間の人材移動傾向を直感的に可視化
- ✅ 流入/流出のバランスを一目で把握
- ✅ 矢印フロー表示で地理的関係性を明確化

### 実装見積もり

| フェーズ | 内容 | 期間 |
|---------|------|------|
| Phase 1 | タブ基本実装 | 1-2日 |
| Phase 2 | 矢印フロー表示 | 2-3日 |
| Phase 3 | GAS側実装 | 1日 |
| Phase 4 | テスト・最適化 | 1日 |
| **合計** | | **5-7日** |

---

## 付録

### ファイル構成

```
map_complete_prototype_Ver2.html
├── HEAD（行1-253）
│   ├── Leaflet.js 1.9.4
│   ├── Chart.js 4.4.1
│   └── CSS（250行）
├── BODY（行254-2356）
│   ├── #app
│   │   ├── #map（Leaflet地図）
│   │   └── #sidebar（右サイドバー）
│   │       ├── header.app
│   │       ├── nav.tabbar
│   │       └── .panels（6タブパネル）
│   ├── embeddedData（JSON、行295-1641）
│   └── SCRIPT（行1642-2353）
│       ├── 変数定義・初期化（行1643-1679）
│       ├── Leaflet初期化（行1680-1689）
│       ├── リサイズ処理（行1691-1725）
│       ├── タブ処理（行1727-1744）
│       ├── 地域選択（行1746-1852）
│       ├── レンダリング関数（行1854-2224）
│       │   ├── renderOverview()
│       │   ├── renderSupply()
│       │   ├── renderCareer()
│       │   ├── renderUrgency()
│       │   ├── renderPersona()
│       │   └── renderCross()
│       ├── renderCity()（行2226-2285）
│       ├── renderAll()（行2287-2293）
│       ├── applyPayload()（行2295-2318）
│       └── loadData()（行2320-2348）
└── 起動（行2351）
```

---

**作成者**: Claude Code
**作成日**: 2025年11月1日
**ステータス**: 分析完了 ✅

