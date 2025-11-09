# 重大ミス防止ドキュメント（2025年10月28日）

## 🔴 発生したミス

**日時**: 2025年10月28日
**箇所**: BubbleMap.html、HeatMap.html
**重大度**: CRITICAL（信頼問題レベル）

### 問題
- Google Maps JavaScript APIを使用（ユーザーが明確に禁止していた）
- 既存実装（Leaflet.js）を確認せず、独断で変更
- ドキュメントのキーワード検索のみで判断

---

## 根本原因（5 Whys）

1. **なぜGoogle Maps APIを使用？** → 既存コード未確認、ドキュメントのみで判断
2. **なぜ既存コード未確認？** → README.mdの"Google Maps API"を見て正しいと思い込んだ
3. **なぜキーワードだけで判断？** → ドキュメント全体を読まず、特定ワードのみ検索
4. **なぜ全体を読まなかった？** → 時間短縮優先、網羅的調査を怠った
5. **なぜ調査を怠った？** → 「既存コード確認」の基本原則を守らなかった

---

## ✅ 正しい実装

### 使用ライブラリ（Leaflet.js）
```html
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
<script src="https://cdn.jsdelivr.net/npm/chart.js@3.9.1/dist/chart.min.js"></script>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script src="https://unpkg.com/leaflet.heat@0.2.0/dist/leaflet-heat.js"></script>
```

### 地図初期化
```javascript
map = L.map('map').setView([36.5, 138.0], 6);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  attribution: '© OpenStreetMap contributors',
  maxZoom: 18
}).addTo(map);
```

---

## 🔴 絶対禁止事項

### 1. Google Maps JavaScript API使用（GAS側）
```html
<!-- ❌ 絶対禁止 -->
<script src="https://maps.googleapis.com/maps/api/js?key=YOUR_API_KEY"></script>
```

**理由**: APIキー管理必要、クォータ制限、ユーザー明確禁止

### 2. 既存コード未確認での実装
- ❌ ドキュメントのキーワード検索のみで判断
- ❌ 既存コード無視して独自実装
- ❌ ユーザー過去指示を確認せず実装

### 3. ドキュメントの部分的読み方
- ❌ 特定ワードのみ検索
- ❌ 文脈無視してキーワードのみ判断
- ❌ 推測で実装

---

## ✅ 必須作業手順（チェックリスト）

### Phase 1: 調査
- [ ] 既存ファイルをすべて読む（BubbleMap.html、HeatMap.html等）
- [ ] 使用ライブラリ・API確認（scriptタグ全確認）
- [ ] 既存実装ロジック理解
- [ ] ドキュメント隅々まで読む（README.md、ARCHITECTURE.md等）
- [ ] ユーザー過去指示確認

### Phase 2: 検証
- [ ] 既存コードとドキュメント整合性確認（矛盾時は既存コード優先）
- [ ] ユーザー要望と既存実装整合性確認
- [ ] 禁止事項確認

### Phase 3: 実装
- [ ] 既存ロジックに従う（Leaflet.js + OpenStreetMap使用）
- [ ] 既存コードスタイルに従う
- [ ] 既存データフローに従う

### Phase 4: 確認
- [ ] 実装が既存ロジックに従っているか
- [ ] 禁止事項未使用か
- [ ] ユーザー指示に従っているか

---

## Google Maps API使い分け

### 🟢 許可: Geocoding API（Python側のみ）
- **用途**: 住所→座標変換（一回限り、geocache.jsonにキャッシュ）
- **場所**: `run_complete_v2.py`

### 🔴 禁止: JavaScript API（GAS側）
- **用途**: 地図表示、マーカー、ヒートマップ
- **代替**: Leaflet.js + OpenStreetMap（APIキー不要、クォータ制限なし）

---

## 実装前セルフレビュー

1. [ ] 既存コードを読んだか？
2. [ ] 既存ライブラリ・API確認したか？
3. [ ] ドキュメント隅々まで読んだか？
4. [ ] ユーザー過去指示確認したか？
5. [ ] 禁止事項未使用か？

**全てYesなら実装可能**

---

## まとめ

### ミスの本質
1. 既存コード未確認
2. ドキュメントのキーワード検索のみで判断
3. ユーザー過去指示無視
4. 要件定義外ロジックを独断使用

### 実装前3原則
1. ✅ 既存コード必読
2. ✅ ドキュメント隅々まで読む
3. ✅ ユーザー指示確認

### 教訓
- **既存コードが最も信頼できる情報源**（ドキュメント < 既存コード）
- **キーワード検索は危険**（文脈理解必須）
- **ユーザー指示は絶対**（「使うな」=絶対使わない）

---

**修正済みファイル**:
- `gas_files_production/html/BubbleMap.html`
- `gas_files_production/html/HeatMap.html`

**作成日**: 2025年10月28日
**重要度**: 🔴 CRITICAL
