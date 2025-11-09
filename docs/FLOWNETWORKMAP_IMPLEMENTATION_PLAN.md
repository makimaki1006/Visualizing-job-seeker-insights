# FlowNetworkMap実装計画

**作成日**: 2025年11月1日
**ステータス**: 実装準備完了
**優先度**: 🔴 HIGH（MAP_ENHANCEMENT_PLAN 順位1位）

---

## 1. 概要

### 目的
求職者の「居住地→希望勤務地」フローを、**Leaflet.js地図上に矢印で可視化**し、地域間の人材移動傾向を直感的に把握可能にする。

### 既存機能との違い

| 機能名 | タイプ | 表示方法 | データソース | 地理的位置 |
|--------|--------|---------|-------------|-----------|
| **既存D3.jsネットワーク図** | GASダイアログ | 力学モデルノード配置 | Phase6_FlowEdges | ❌ なし |
| **MapComplete.html** | HTML地図 | マーカー/クラスター/ヒートマップ | Phase1_MapMetrics | ✅ あり |
| **FlowNetworkMap.html（新規）** | HTML地図 | 矢印フロー | Phase6 + Phase1 | ✅ あり |

**既存のD3.js実装（Phase1-6UnifiedVisualizations.gs:834）**は、地理的位置関係を無視したネットワーク図です。

**FlowNetworkMapは、地図上に地理的に正確な位置で矢印を表示**します。

---

## 2. データ構造分析

### 2.1 Phase 6フローデータ

**MunicipalityFlowEdges.csv** (2MB、約6,862エッジ):
```csv
origin,destination,origin_pref,origin_muni,destination_pref,destination_muni,applicant_id,age,gender
奈良県山辺郡山添村,奈良県奈良市,奈良県,山辺郡山添村,奈良県,奈良市,0,49,女性
```

- **origin**: 居住地（完全な地名）
- **destination**: 希望勤務地（完全な地名）
- **origin_pref/origin_muni**: 居住地の都道府県・市区町村
- **destination_pref/destination_muni**: 希望勤務地の都道府県・市区町村
- **applicant_id, age, gender**: 求職者属性

**MunicipalityFlowNodes.csv** (約600KB):
```csv
location,prefecture,municipality,inflow,outflow,net_flow,applicant_count
京都府京都市下京区,京都府,京都市下京区,677,257,420,780
```

- **inflow**: 流入数（他地域から希望される数）
- **outflow**: 流出数（他地域を希望する数）
- **net_flow**: 純流入数（inflow - outflow）
- **applicant_count**: 総求職者数

### 2.2 Phase 1座標データ

**MapMetrics.csv**:
```csv
prefecture,municipality,location_key,applicant_count,latitude,longitude
京都府,京都市伏見区,京都府京都市伏見区,1748,34.9327,135.7656
```

- **location_key**: 都道府県 + 市区町村（例: "京都府京都市伏見区"）
- **latitude, longitude**: 緯度経度（地図表示に必須）

### 2.3 データマージ戦略

**マージキー**: `location_key` (Phase1) = `origin` または `destination` (Phase6)

```javascript
// 疑似コード
flowEdges.forEach(edge => {
  const originCoord = mapMetrics.find(m => m.location_key === edge.origin);
  const destCoord = mapMetrics.find(m => m.location_key === edge.destination);

  if (originCoord && destCoord) {
    drawArrow(
      [originCoord.latitude, originCoord.longitude],
      [destCoord.latitude, destCoord.longitude],
      edge
    );
  }
});
```

**課題**: Phase6のEdgesデータ（2MB、6,862エッジ）は大量。ブラウザで全表示すると重い。

**解決策**:
1. **フィルター機能**: フロー数でフィルタリング（例: 5人以上のフローのみ表示）
2. **TOP表示**: フロー数上位100件のみ表示
3. **集約表示**: 都道府県レベルで集約して表示

---

## 3. 技術要件

### 3.1 必須ライブラリ

| ライブラリ | バージョン | 用途 |
|-----------|---------|------|
| **Leaflet.js** | 1.9.4 | 地図表示基盤 |
| **Leaflet.PolylineDecorator** | 1.6.0+ | 矢印装飾 |
| **Chart.js** | 3.9.1 | サイドバー統計グラフ（オプション） |

**Leaflet.PolylineDecoratorの追加**:
```html
<script src="https://cdn.jsdelivr.net/npm/leaflet-polylinedecorator@1.6.0/dist/leaflet.polylineDecorator.min.js"></script>
```

### 3.2 矢印表示実装例

```javascript
// フロー矢印の描画
function drawFlowArrow(originLatLng, destLatLng, flowCount, color) {
  // ポリライン作成
  const polyline = L.polyline([originLatLng, destLatLng], {
    color: color,
    weight: Math.min(flowCount / 10, 10), // フロー数に応じた太さ
    opacity: 0.6
  }).addTo(map);

  // 矢印装飾
  const decorator = L.polylineDecorator(polyline, {
    patterns: [
      {
        offset: '100%',
        repeat: 0,
        symbol: L.Symbol.arrowHead({
          pixelSize: 12,
          polygon: false,
          pathOptions: { stroke: true, color: color, weight: 2 }
        })
      }
    ]
  }).addTo(map);

  // ツールチップ
  polyline.bindPopup(`
    <strong>${originName} → ${destName}</strong><br>
    フロー数: ${flowCount}人
  `);
}
```

### 3.3 色分け戦略

**フロー強度による色分け**:
```javascript
function getFlowColor(flowCount) {
  if (flowCount >= 50) return '#e74c3c'; // 赤（強フロー）
  if (flowCount >= 20) return '#f39c12'; // オレンジ（中フロー）
  if (flowCount >= 10) return '#3498db'; // 青（弱フロー）
  return '#95a5a6'; // グレー（微フロー）
}
```

**純流入/流出による色分け**（代替案）:
- **流入（赤系）**: 他地域から希望される地域
- **流出（青系）**: 他地域を希望する地域

---

## 4. UI設計

### 4.1 レイアウト構成

```
┌─────────────────────────────────────────────────────────────┐
│ ヘッダー: Phase 6 自治体間フローマップ                        │
├──────────────────────────────┬──────────────────────────────┤
│                              │ サイドバー（360px）           │
│                              │ ┌─────────────────────────┐ │
│                              │ │ フィルター設定           │ │
│                              │ │ ├ フロー数: 10人以上    │ │
│   地図領域（Leaflet.js）      │ │ ├ 表示モード: TOP100    │ │
│                              │ │ ├ 都道府県: 全て        │ │
│                              │ │ └ 年齢層: 全て          │ │
│   矢印フロー表示              │ └─────────────────────────┘ │
│                              │ ┌─────────────────────────┐ │
│                              │ │ 統計サマリー             │ │
│                              │ │ ├ 総フロー数: 6,862     │ │
│                              │ │ ├ 表示中: 150           │ │
│                              │ │ └ TOP流入地: 京都市下京区│ │
│                              │ └─────────────────────────┘ │
│                              │ ┌─────────────────────────┐ │
│                              │ │ フローランキング         │ │
│                              │ │ 1. 京都市→大阪市 (67件) │ │
│                              │ │ 2. 奈良市→京都市 (52件) │ │
│                              │ │ ...                     │ │
│                              │ └─────────────────────────┘ │
└──────────────────────────────┴──────────────────────────────┘
```

### 4.2 フィルター機能

| フィルター名 | 説明 | デフォルト |
|------------|------|----------|
| **フロー数** | 最小フロー数でフィルタ | 10人以上 |
| **表示件数** | TOP N件のみ表示 | TOP 100 |
| **都道府県** | 出発地または目的地の都道府県 | 全て |
| **年齢層** | 20代、30代等でフィルタ | 全て |
| **性別** | 男性/女性 | 全て |

### 4.3 インタラクティブ機能

- **矢印クリック**: フロー詳細をポップアップ表示
- **ノードクリック**: その地域の流入/流出統計を表示
- **ズーム連動**: ズームレベルに応じて表示密度調整
- **ランキングクリック**: 該当フローにズーム・ハイライト

---

## 5. 実装アプローチ

### 5.1 ベースファイル選定

**ベース**: MapComplete.html（20KB、Leaflet.js実装済み）

**理由**:
- ✅ Leaflet.js地図基盤が完成
- ✅ サイドバーUI構造が利用可能
- ✅ データロード関数（google.script.run）が整備済み

### 5.2 実装ステップ

#### Phase 1: データロード基盤（1-2日）

1. **GAS側データ提供関数追加**（UnifiedDataImporter.gs または新規.gs）
   ```javascript
   function getFlowMapData() {
     const mapMetrics = loadPhase1MapMetrics(); // 座標データ
     const flowEdges = loadPhase6FlowEdges();   // フローデータ
     const flowNodes = loadPhase6FlowNodes();   // 集約データ

     return {
       mapMetrics: mapMetrics,
       flowEdges: flowEdges.slice(0, 1000), // 最初の1000件（パフォーマンス対策）
       flowNodes: flowNodes
     };
   }
   ```

2. **HTML側データロード**
   ```javascript
   google.script.run
     .withSuccessHandler(onFlowDataLoaded)
     .withFailureHandler(onError)
     .getFlowMapData();
   ```

#### Phase 2: 矢印表示実装（2-3日）

1. **Leaflet.PolylineDecorator追加**
   ```html
   <script src="https://cdn.jsdelivr.net/npm/leaflet-polylinedecorator@1.6.0/dist/leaflet.polylineDecorator.min.js"></script>
   ```

2. **座標マージ関数**
   ```javascript
   function mergeFlowWithCoordinates(flowEdges, mapMetrics) {
     const coordMap = new Map();
     mapMetrics.forEach(m => {
       coordMap.set(m.location_key, [m.latitude, m.longitude]);
     });

     return flowEdges.filter(edge => {
       edge.originCoord = coordMap.get(edge.origin);
       edge.destCoord = coordMap.get(edge.destination);
       return edge.originCoord && edge.destCoord; // 座標が両方揃っている場合のみ
     });
   }
   ```

3. **矢印描画関数**
   ```javascript
   function drawFlowArrows(flowEdges) {
     flowEdges.forEach(edge => {
       const color = getFlowColor(edge.count); // カウントは集約が必要
       const polyline = L.polyline([edge.originCoord, edge.destCoord], {
         color: color,
         weight: 3,
         opacity: 0.6
       }).addTo(map);

       L.polylineDecorator(polyline, {
         patterns: [{
           offset: '100%',
           repeat: 0,
           symbol: L.Symbol.arrowHead({ pixelSize: 10 })
         }]
       }).addTo(map);

       polyline.bindPopup(`
         <strong>${edge.origin} → ${edge.destination}</strong><br>
         求職者: ${edge.applicant_id}<br>
         年齢: ${edge.age}歳<br>
         性別: ${edge.gender}
       `);
     });
   }
   ```

#### Phase 3: フィルター機能実装（1-2日）

1. **フィルターUI追加**
   ```html
   <select id="flowFilter" onchange="applyFlowFilter()">
     <option value="all">全フロー</option>
     <option value="top100">TOP 100</option>
     <option value="top50">TOP 50</option>
     <option value="min10">10人以上</option>
     <option value="min20">20人以上</option>
   </select>
   ```

2. **フィルタリング関数**
   ```javascript
   function applyFlowFilter() {
     const filterType = document.getElementById('flowFilter').value;
     let filteredEdges = flowEdgesData;

     if (filterType === 'top100') {
       filteredEdges = flowEdgesData
         .sort((a, b) => b.count - a.count)
         .slice(0, 100);
     }

     clearFlowArrows();
     drawFlowArrows(filteredEdges);
   }
   ```

#### Phase 4: 統計サマリー実装（1日）

1. **サイドバー統計追加**
   ```javascript
   function updateFlowStats(flowNodes) {
     const topInflow = flowNodes
       .sort((a, b) => b.inflow - a.inflow)
       .slice(0, 10);

     document.getElementById('topInflowList').innerHTML = topInflow
       .map((node, idx) => `
         <li>${idx + 1}. ${node.location} (${node.inflow}人)</li>
       `).join('');
   }
   ```

#### Phase 5: 最適化・テスト（1-2日）

1. **パフォーマンス最適化**
   - クラスタリング（多数の矢印がある場合）
   - 遅延読み込み（viewport外の矢印は非表示）
   - Canvas Rendererの使用（Leaflet.Canvas）

2. **E2Eテスト**
   - データロード検証
   - 矢印表示検証
   - フィルター動作検証

---

## 6. データ集約の必要性

### 6.1 課題: Edgesデータの粒度

**現状**: MunicipalityFlowEdges.csvは、**各求職者の各希望勤務地**が1行になっている（6,862行）。

例:
```csv
奈良県生駒郡平群町,奈良県五條市,奈良県,生駒郡平群町,奈良県,五條市,1,27,男性
奈良県生駒郡平群町,奈良県葛城市,奈良県,生駒郡平群町,奈良県,葛城市,1,27,男性
```

同一求職者（applicant_id=1）が複数の希望勤務地を持つため、**Origin→Destinationの組み合わせでグループ化**する必要があります。

### 6.2 集約処理

**JavaScript側で集約**:
```javascript
function aggregateFlowEdges(rawEdges) {
  const flowMap = new Map();

  rawEdges.forEach(edge => {
    const key = `${edge.origin}→${edge.destination}`;
    if (!flowMap.has(key)) {
      flowMap.set(key, {
        origin: edge.origin,
        destination: edge.destination,
        count: 0,
        applicants: []
      });
    }

    const flow = flowMap.get(key);
    flow.count++;
    flow.applicants.push({
      id: edge.applicant_id,
      age: edge.age,
      gender: edge.gender
    });
  });

  return Array.from(flowMap.values());
}
```

**集約結果例**:
```javascript
{
  origin: "奈良県生駒郡平群町",
  destination: "奈良県五條市",
  count: 15, // 15人が希望
  applicants: [...]
}
```

### 6.3 Python側での事前集約（推奨）

**理由**: ブラウザ側で6,862行を処理するのは重い。Python側で集約した「AggregatedFlowEdges.csv」を生成する方が効率的。

**run_complete_v2_perfect.py への追加**:
```python
def aggregate_flow_edges(flow_edges_df):
    """
    Origin→Destinationの組み合わせでフローを集約
    """
    agg = flow_edges_df.groupby(['origin', 'destination', 'origin_pref', 'origin_muni', 'destination_pref', 'destination_muni']).agg({
        'applicant_id': 'count',  # フロー数
        'age': 'mean',            # 平均年齢
        'gender': lambda x: x.mode()[0] if len(x.mode()) > 0 else '不明'  # 最頻性別
    }).reset_index()

    agg.rename(columns={'applicant_id': 'flow_count'}, inplace=True)
    return agg

# Phase 6エクスポート時に追加
aggregated_edges = aggregate_flow_edges(flow_edges_df)
aggregated_edges.to_csv(output_dir / 'AggregatedFlowEdges.csv', index=False, encoding='utf-8-sig')
```

**出力例**:
```csv
origin,destination,origin_pref,origin_muni,destination_pref,destination_muni,flow_count,age,gender
奈良県生駒郡平群町,大阪府東大阪市,奈良県,生駒郡平群町,大阪府,東大阪市,87,35.2,男性
```

---

## 7. 実装スケジュール

| フェーズ | タスク | 期間 | 担当 | 成果物 |
|---------|-------|-----|------|--------|
| **Phase 1** | データロード基盤 | 1-2日 | Claude | getFlowMapData()関数 |
| **Phase 2** | 矢印表示実装 | 2-3日 | Claude | FlowNetworkMap.html（基本版） |
| **Phase 3** | フィルター機能 | 1-2日 | Claude | フィルター完全実装 |
| **Phase 4** | 統計サマリー | 1日 | Claude | サイドバー統計完成 |
| **Phase 5** | 最適化・テスト | 1-2日 | Claude | E2Eテスト合格 |
| **オプション** | Python集約実装 | 1日 | Claude | AggregatedFlowEdges.csv生成 |

**合計期間**: 6-10日（オプション含む7-11日）

---

## 8. 成功指標

### 8.1 機能要件

- ✅ 地図上に矢印フローが表示される
- ✅ フロー数に応じた色分け・太さ調整
- ✅ フィルター機能（フロー数、都道府県、年齢層）
- ✅ インタラクティブ性（クリック、ズーム連動）
- ✅ 統計サマリー表示（TOP流入地、フローランキング）

### 8.2 パフォーマンス要件

- ✅ 初期ロード時間: 3秒以内
- ✅ フィルター適用: 1秒以内
- ✅ ズーム・パン: 滑らかな操作性
- ✅ 1000本の矢印を表示可能

### 8.3 品質要件

- ✅ E2Eテスト合格率: 100%
- ✅ ブラウザ互換性: Chrome, Edge, Firefox
- ✅ レスポンシブ対応: 最小1280x720px

---

## 9. リスク・課題

| リスク | 影響度 | 対策 |
|-------|--------|------|
| **データ量多大（6,862エッジ）** | 🔴 HIGH | Python側で集約、TOP表示のみ |
| **座標マッチング失敗** | 🟡 MEDIUM | エラーハンドリング、ログ出力 |
| **ブラウザ動作重い** | 🟡 MEDIUM | Canvas Renderer、クラスタリング |
| **矢印が重なって見づらい** | 🟢 LOW | 透明度調整、ズーム推奨 |

---

## 10. 次のステップ

### 即座に実装可能

1. **Phase 1データロード基盤**の実装（GAS関数追加）
2. **FlowNetworkMap.html**の作成（MapComplete.htmlをベースに）

### 検討・協議が必要

1. **Python側集約実装**の採用可否
2. **フィルターのデフォルト値**（TOP 100 or フロー数10人以上?）
3. **色分け戦略**（フロー強度 or 純流入/流出?）

---

## 11. 参考資料

### 関連ドキュメント
- **[MAP_ENHANCEMENT_PLAN.md](MAP_ENHANCEMENT_PLAN.md)** - MAP機能全体の拡張計画
- **[COMPLETE_DATA_FLOW_GUIDE.md](COMPLETE_DATA_FLOW_GUIDE.md)** - データフロー完全ガイド
- **[PYTHON_GAS_COVERAGE_REPORT.md](PYTHON_GAS_COVERAGE_REPORT.md)** - GASカバレッジ分析

### 関連ファイル
- **MapComplete.html** (`gas_files/html/MapComplete.html`) - ベースファイル
- **Phase1-6UnifiedVisualizations.gs** (`gas_files/scripts/`) - 既存D3.js実装
- **MunicipalityFlowEdges.csv** (`python_scripts/data/output_v2/phase6/`) - フローデータ
- **MapMetrics.csv** (`python_scripts/data/output_v2/phase1/`) - 座標データ

### 技術参考
- **Leaflet.PolylineDecorator**: https://github.com/bbecquet/Leaflet.PolylineDecorator
- **Leaflet公式ドキュメント**: https://leafletjs.com/reference.html
- **D3.js Force-Directed Graph**: https://d3js.org/d3-force

---

## 付録A: データサンプル

### Phase6_FlowEdges（生データ）
```csv
origin,destination,origin_pref,origin_muni,destination_pref,destination_muni,applicant_id,age,gender
奈良県生駒郡平群町,大阪府東大阪市,奈良県,生駒郡平群町,大阪府,東大阪市,1,27,男性
奈良県生駒郡平群町,大阪府松原市,奈良県,生駒郡平群町,大阪府,松原市,1,27,男性
```

### Phase1_MapMetrics（座標データ）
```csv
prefecture,municipality,location_key,latitude,longitude
奈良県,生駒郡平群町,奈良県生駒郡平群町,34.6123,135.6956
大阪府,東大阪市,大阪府東大阪市,34.6794,135.6005
```

### 集約後のAggregatedFlowEdges（推奨）
```csv
origin,destination,flow_count,avg_age,gender_mode
奈良県生駒郡平群町,大阪府東大阪市,87,35.2,男性
```

---

## 改訂履歴

| 日付 | バージョン | 変更内容 | 担当 |
|------|----------|---------|------|
| 2025-11-01 | 1.0 | 初版作成 | Claude |

