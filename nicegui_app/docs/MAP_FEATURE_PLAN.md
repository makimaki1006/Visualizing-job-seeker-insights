# 地図機能実装計画

**作成日**: 2025-12-28
**目的**: NiceGUI組み込み地図による求職者データの地理的可視化

---

## 概要

NiceGUIの`ui.leaflet()`を活用し、以下の地図機能を段階的に実装：

1. **フロー可視化**: 居住地→希望勤務地の移動を線で表示
2. **クリック選択**: 地図上で市区町村を選択してフィルタ
3. **ヒートマップ**: 求職者密度を色分け表示

---

## 実装フェーズ

### Phase 1: 基盤構築（30分）

**目標**: 地図タブの追加と基本表示

```python
# NiceGUI Leaflet基本構文
from nicegui import ui

map = ui.leaflet(center=(35.6762, 139.6503), zoom=5)  # 東京中心
map.tile_layer(
    url_template='https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
    options={'attribution': '© OpenStreetMap'}
)
```

**タスク**:
- [ ] 新規タブ「🗺️ 人材地図」追加（既存の求人地図を置換）
- [ ] 日本全体表示（zoom=5, center=日本中心）
- [ ] 都道府県マーカー（47個）を表示

**データソース**: `PREFECTURE_SUMMARY` row_type
- lat, lng（緯度経度）
- count（求職者数）

---

### Phase 2: フロー可視化（1時間）

**目標**: 居住地→希望勤務地の移動パターンを線で表示

```python
# ポリライン描画
map.generic_layer(
    name='polyline',
    args=[[start_latlng, end_latlng]],
    options={'color': 'blue', 'weight': 2, 'opacity': 0.6}
)
```

**可視化内容**:
- **線の太さ**: 移動人数に比例
- **線の色**: 移動距離で色分け（短=緑、中=黄、長=赤）
- **アニメーション**: オプション（流れる線）

**データソース**: `RESIDENCE_FLOW` row_type
- category1: 居住地（都道府県）
- category2: 希望勤務地（都道府県）
- count: 移動人数
- ※座標は都道府県の重心を使用

**UI要素**:
- フロー表示ON/OFFトグル
- 最小移動人数フィルタ（スライダー）
- 移動距離フィルタ（地元/近隣/中距離/遠距離）

---

### Phase 3: クリック選択（1時間）

**目標**: 地図上のマーカーをクリックして市区町村を選択

```python
# マーカークリックイベント
marker = map.marker(latlng=(lat, lng))
marker.on('click', lambda: select_municipality(name))
```

**機能**:
- クリックでドロップダウンと連動
- 選択中の市区町村をハイライト表示
- ポップアップで基本情報表示（求職者数、主要資格など）

**データソース**: `MUNICIPALITY_SUMMARY` row_type
- lat, lng（市区町村の緯度経度）
- count（求職者数）

**UI要素**:
- クリック選択 ⇔ ドロップダウン選択の双方向連動
- 選択中マーカーの色変更
- ズームイン連動（市区町村選択時に自動ズーム）

---

### Phase 4: ヒートマップ/コロプレス（1.5時間）

**目標**: 求職者密度を地図上に色分け表示

**選択肢A: マーカーサイズ方式（簡易）**
```python
# サークルマーカー（サイズ=人数）
map.generic_layer(
    name='circle',
    args=[(lat, lng)],
    options={'radius': count / 100, 'color': '#ff6b6b', 'fillOpacity': 0.5}
)
```

**選択肢B: GeoJSONコロプレス（本格的）**
- 市区町村境界GeoJSONが必要
- 求職者数で塗り分け
- マウスオーバーで詳細表示

**データソース**:
- `MUNICIPALITY_SUMMARY` - 求職者数
- `GAP` - 需給ギャップ（供給過多=青、需要過多=赤）
- `COMPETITION` - 競争スコア

**UI要素**:
- 表示モード切替（人数/需給ギャップ/競争度）
- カラースケール凡例
- フィルタ（都道府県絞り込み）

---

## 技術要件

### 必要データ

| データ | 用途 | 取得元 |
|--------|------|--------|
| 都道府県座標 | マーカー配置 | geocache.json or API |
| 市区町村座標 | マーカー配置 | geocache.json |
| 市区町村GeoJSON | 境界表示（Phase 4） | 国土地理院 or 外部ソース |

### 座標データの確認

```python
# MapComplete_Complete_All_FIXED.csvに座標あり
# lat, lngカラムを使用
```

### パフォーマンス考慮

- **マーカー数制限**: 1,000個以上は重くなる可能性
- **クラスタリング**: 同一エリアのマーカーをグループ化
- **遅延読み込み**: ズームレベルに応じて表示

---

## 実装優先度

| Phase | 機能 | 工数 | ビジネス価値 | 優先度 |
|-------|------|------|-------------|--------|
| 1 | 基盤構築 | 30分 | 基盤 | ★★★ |
| 2 | フロー可視化 | 1時間 | 高（移動傾向把握） | ★★★ |
| 3 | クリック選択 | 1時間 | 中（UI改善） | ★★☆ |
| 4 | ヒートマップ | 1.5時間 | 高（密度把握） | ★★★ |

**推奨順序**: Phase 1 → Phase 2 → Phase 4 → Phase 3

理由: フロー可視化とヒートマップがビジネス価値が高く、クリック選択はUI改善なので後回し可能。

---

## 次のステップ

1. Phase 1実装開始前に、既存の座標データ確認
2. ui.leaflet()の動作確認（シンプルなサンプル）
3. 段階的に機能追加

---

## 参考リンク

- [NiceGUI Leaflet Documentation](https://nicegui.io/documentation/leaflet)
- [Leaflet.js Official](https://leafletjs.com/)
- [国土地理院 GeoJSON](https://nlftp.mlit.go.jp/ksj/)
