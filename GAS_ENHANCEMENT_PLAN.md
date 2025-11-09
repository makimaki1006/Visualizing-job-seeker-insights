# GAS可視化機能 完成化改良計画

**作成日**: 2025-10-26
**目的**: Phase 7可視化の完成度を3/5 → 5/5に引き上げる
**方針**: 地図連携・クロス分析・インタラクティブ機能の追加

---

## 📊 現状分析

### 現在の実装レベル

| 機能カテゴリ | 実装状況 | 評価 | 改善余地 |
|------------|---------|------|---------|
| **データインポート** | ✅ 完全実装 | 5/5 | なし |
| **基本可視化** | ✅ 4種類のチャート | 4/5 | 小 |
| **地図連携** | ❌ 未実装 | 0/5 | **大** |
| **クロス分析** | ❌ 未実装 | 0/5 | **大** |
| **インタラクティブ性** | ⚠️ 限定的 | 2/5 | 中 |
| **ドリルダウン** | ❌ 未実装 | 0/5 | 中 |

**総合評価**: ⭐⭐⭐☆☆ (3/5)

### 課題の優先順位

| 優先度 | 課題 | 理由 | 実装難易度 | 効果 |
|--------|------|------|-----------|------|
| **HIGH** | ペルソナ地図連携 | 地理的洞察が最重要 | ⭐⭐⭐☆☆ | ⭐⭐⭐⭐⭐ |
| **HIGH** | 移動許容度×ペルソナクロス | 複合洞察で採用戦略高度化 | ⭐⭐☆☆☆ | ⭐⭐⭐⭐☆ |
| **MEDIUM** | インタラクティブフィルタ | ユーザビリティ向上 | ⭐⭐⭐⭐☆ | ⭐⭐⭐☆☆ |
| **MEDIUM** | ドリルダウン詳細表示 | 深掘り分析可能 | ⭐⭐⭐⭐☆ | ⭐⭐⭐☆☆ |
| **LOW** | チャート画像エクスポート | 報告書作成支援 | ⭐⭐☆☆☆ | ⭐⭐☆☆☆ |

---

## 🎯 改良計画（4つの主要機能）

### **機能1: ペルソナ地図連携** 🗺️

#### 概要
- ペルソナ別の地理的分布を地図上に可視化
- バブルマップでペルソナIDごとに色分け、人数で大きさ表現
- クリックで詳細情報表示（モーダル）

#### 実装方針

**新規ファイル**: `Phase7PersonaMapViz.gs`

**データ結合**:
```javascript
// MapMetrics.csv（座標付き）とDetailedPersonaProfile.csv（ペルソナ情報）を結合
// 居住地ベースでマージ

const mapData = [
  {
    municipality: '仙台市若林区',
    lat: 38.2682,
    lng: 140.8694,
    personaId: 0,
    personaName: '若年層・高資格',
    count: 120,
    avgAge: 28.5,
    femaleRatio: 0.65,
    qualifiedRate: 0.78
  },
  // ...
];
```

**可視化方法**:
1. **Google Maps JavaScript API**を使用
2. **バブルマーカー**で表示:
   - 色: ペルソナID別（10色のカラーパレット）
   - サイズ: 求職者数（count）
   - 透明度: 資格保有率（qualifiedRate）
3. **インタラクティブ**:
   - マーカークリック → 詳細情報ポップアップ
   - ペルソナフィルタ → 特定ペルソナのみ表示
   - ヒートマップモード切り替え

**HTML構造**:
```html
<div id="map-container">
  <div id="map" style="width: 100%; height: 600px;"></div>
  <div id="legend">
    <!-- ペルソナ別凡例 -->
  </div>
  <div id="filters">
    <label><input type="checkbox" data-persona="0"> 若年層・高資格</label>
    <label><input type="checkbox" data-persona="1"> 中年層・地元志向</label>
    <!-- ... -->
  </div>
</div>
```

**実装手順**:
1. MapMetrics.csvから座標データ取得
2. PersonaProfile.csvから居住地別ペルソナ分布計算
3. 2つのデータを居住地キーで結合
4. Google Maps APIでバブルマーカー描画
5. クリックイベントハンドラで詳細表示

**期待効果**:
- 「若年層ペルソナは仙台市青葉区に集中」等の地理的洞察
- エリア別採用戦略の精緻化
- 支社配置の最適化提案

---

### **機能2: 移動許容度×ペルソナクロス分析** 📊

#### 概要
- ペルソナごとの移動許容度レベル分布を可視化
- 「若年層は広域移動OK率が高い」等の複合洞察獲得

#### 実装方針

**新規関数**: `Phase7MobilityScoreViz.gs`に追加

**データ結合**:
```javascript
// MobilityScore.csv（7,390行）とPersonaProfile.csv（10行）を結合
// 申請者IDベースで結合するため、中間シート作成が必要

// ステップ1: df_processedから申請者ID→ペルソナIDマッピング取得
// ステップ2: MobilityScore.csvにペルソナID追加
// ステップ3: ペルソナ×移動許容度レベルのクロス集計
```

**可視化方法**:
1. **積み上げ棒グラフ**:
   - X軸: ペルソナ名
   - Y軸: 人数
   - 色: 移動許容度レベル（A/B/C/D）
2. **100%積み上げ棒グラフ**:
   - 各ペルソナの移動許容度レベル割合
3. **ヒートマップ**:
   - 行: ペルソナ名
   - 列: 移動許容度レベル
   - 色: 人数（濃淡）

**HTML構造**:
```html
<div class="cross-analysis-container">
  <h2>ペルソナ×移動許容度クロス分析</h2>

  <div class="chart-row">
    <div id="stacked_bar_chart"></div>
    <div id="percentage_bar_chart"></div>
  </div>

  <div id="heatmap_chart"></div>

  <table id="cross-table">
    <thead>
      <tr>
        <th>ペルソナ</th>
        <th>Aランク</th>
        <th>Bランク</th>
        <th>Cランク</th>
        <th>Dランク</th>
        <th>合計</th>
      </tr>
    </thead>
    <!-- ... -->
  </table>
</div>
```

**実装手順**:
1. **Python側で前処理**（推奨）:
   - `phase7_advanced_analysis.py`に`_generate_persona_mobility_cross()`関数追加
   - `PersonaMobilityCross.csv`を新規出力
   - カラム: ペルソナID, ペルソナ名, レベルA, レベルB, レベルC, レベルD
2. **GAS側で可視化**:
   - `PersonaMobilityCross.csv`をインポート
   - Google Chartsで3種類のチャート描画

**期待効果**:
- 「若年層ペルソナは広域移動OK（Aランク）が15%、中年層は3%」等の洞察
- ペルソナ特性の多次元理解
- 採用難易度の精緻化

---

### **機能3: インタラクティブフィルタ** 🔍

#### 概要
- ユーザーが任意の条件でデータをフィルタリング
- レベル別表示、居住地別表示、スコア範囲指定等

#### 実装方針

**対象**: 全Phase 7可視化（MobilityScore, PersonaProfile等）

**フィルタ種類**:

1. **移動許容度レベルフィルタ**:
   ```html
   <div class="filter-panel">
     <h3>移動許容度レベル</h3>
     <label><input type="checkbox" value="A" checked> Aランク（広域移動OK）</label>
     <label><input type="checkbox" value="B" checked> Bランク（中距離OK）</label>
     <label><input type="checkbox" value="C" checked> Cランク（近距離のみ）</label>
     <label><input type="checkbox" value="D" checked> Dランク（地元限定）</label>
   </div>
   ```

2. **スコア範囲フィルタ**:
   ```html
   <div class="filter-panel">
     <h3>移動許容度スコア</h3>
     <label>最小: <input type="number" id="score-min" value="0" min="0" max="100"></label>
     <label>最大: <input type="number" id="score-max" value="100" min="0" max="100"></label>
   </div>
   ```

3. **居住地フィルタ**（ドロップダウン）:
   ```html
   <div class="filter-panel">
     <h3>居住地</h3>
     <select id="residence-filter" multiple>
       <option value="">すべて</option>
       <option value="仙台市">仙台市</option>
       <option value="名取市">名取市</option>
       <!-- ... -->
     </select>
   </div>
   ```

**JavaScript実装**:
```javascript
// フィルタ適用関数
function applyFilters() {
  const selectedLevels = getSelectedLevels();  // ['A', 'B']
  const scoreRange = getScoreRange();          // {min: 20, max: 80}
  const residence = getSelectedResidence();    // '仙台市'

  // データフィルタリング
  const filteredData = data.filter(row => {
    return selectedLevels.includes(row.mobilityLevel) &&
           row.mobilityScore >= scoreRange.min &&
           row.mobilityScore <= scoreRange.max &&
           (residence === '' || row.residence === residence);
  });

  // チャート再描画
  drawChartsWithData(filteredData);
}

// イベントリスナー登録
document.querySelectorAll('.filter-panel input, .filter-panel select').forEach(el => {
  el.addEventListener('change', applyFilters);
});
```

**期待効果**:
- 「Aランクの求職者だけを見たい」等の柔軟な分析
- ユーザビリティ大幅向上
- 採用担当者の使いやすさ改善

---

### **機能4: ドリルダウン詳細表示** 🔎

#### 概要
- チャート要素をクリックすると詳細情報をモーダル表示
- ペルソナカードクリック → そのペルソナの全求職者リスト等

#### 実装方針

**対象**: PersonaProfile, MobilityScore, SupplyDensity

**実装例1: ペルソナ詳細モーダル**

```javascript
// ペルソナカードクリック時
function showPersonaDetailModal(personaId) {
  // 1. そのペルソナに属する全求職者データ取得
  const personaApplicants = getApplicantsByPersona(personaId);

  // 2. モーダルHTML生成
  const modalHtml = `
    <div class="modal">
      <h2>ペルソナ詳細: ${personaName}</h2>

      <h3>求職者リスト（${personaApplicants.length}名）</h3>
      <table>
        <tr><th>申請者ID</th><th>年齢</th><th>性別</th><th>資格</th><th>居住地</th><th>移動許容度</th></tr>
        ${personaApplicants.map(applicant => `
          <tr>
            <td>${applicant.id}</td>
            <td>${applicant.age}</td>
            <td>${applicant.gender}</td>
            <td>${applicant.qualifications}</td>
            <td>${applicant.residence}</td>
            <td>${applicant.mobilityLevel}</td>
          </tr>
        `).join('')}
      </table>

      <h3>資格詳細分布</h3>
      <div id="qualification-detail-chart"></div>

      <h3>希望勤務地マップ</h3>
      <div id="persona-location-map"></div>
    </div>
  `;

  // 3. モーダル表示
  showModal(modalHtml);
}
```

**実装例2: 地図マーカークリック詳細**

```javascript
// 地図マーカークリック時
marker.addListener('click', function() {
  const info = `
    <div class="info-window">
      <h3>${municipality}</h3>
      <p>ペルソナ: ${personaName}</p>
      <p>求職者数: ${count}名</p>
      <p>平均年齢: ${avgAge}歳</p>
      <p>女性比率: ${(femaleRatio * 100).toFixed(1)}%</p>
      <p>資格保有率: ${(qualifiedRate * 100).toFixed(1)}%</p>

      <button onclick="showPersonaDetailModal(${personaId})">
        詳細を見る →
      </button>
    </div>
  `;

  infoWindow.setContent(info);
  infoWindow.open(map, marker);
});
```

**期待効果**:
- 「このペルソナはどんな人たちで構成されているか？」の疑問に即答
- データ探索性の大幅向上
- 採用担当者の意思決定支援

---

## 📋 実装優先順位と工数見積もり

### フェーズ1: 最優先機能（2-3時間）

| 機能 | 工数 | 難易度 | ROI |
|------|------|--------|-----|
| **機能2: クロス分析（Python側）** | 1時間 | ⭐⭐☆☆☆ | 高 |
| **機能2: クロス分析（GAS側）** | 1時間 | ⭐⭐☆☆☆ | 高 |

**合計**: 2時間

**理由**:
- 最も効果が高く、実装が簡単
- Python側でCSV生成すれば、GAS側は既存パターンの応用
- 即効性のある洞察獲得

### フェーズ2: 地図連携（3-4時間）

| 機能 | 工数 | 難易度 | ROI |
|------|------|--------|-----|
| **機能1: ペルソナ地図（データ結合）** | 1時間 | ⭐⭐⭐☆☆ | 高 |
| **機能1: ペルソナ地図（Google Maps API）** | 2時間 | ⭐⭐⭐☆☆ | 高 |
| **機能1: ペルソナ地図（インタラクティブ）** | 1時間 | ⭐⭐⭐☆☆ | 中 |

**合計**: 4時間

**理由**:
- 効果が非常に高い
- Google Maps API統合に若干の学習コストあり
- ビジュアルインパクト大

### フェーズ3: インタラクティブ機能（2-3時間）

| 機能 | 工数 | 難易度 | ROI |
|------|------|--------|-----|
| **機能3: フィルタUI** | 1時間 | ⭐⭐⭐☆☆ | 中 |
| **機能3: フィルタロジック** | 1時間 | ⭐⭐⭐☆☆ | 中 |
| **機能4: ドリルダウン** | 1時間 | ⭐⭐⭐⭐☆ | 中 |

**合計**: 3時間

**理由**:
- ユーザビリティ向上
- フェーズ1-2の価値を最大化
- 実装はやや複雑だが標準的パターン

### 総工数見積もり

**合計**: 9時間（1.5日）

**内訳**:
- Python側: 1時間（クロス分析CSV生成）
- GAS側: 8時間（可視化実装）

---

## 🔍 技術的考慮事項

### 1. データ結合の課題

**問題**: MobilityScore.csvには申請者IDがあるが、ペルソナIDがない

**解決策**:

**Option A: Python側で事前結合（推奨）**
```python
# phase7_advanced_analysis.py に追加

def _generate_persona_mobility_cross(self):
    """ペルソナ×移動許容度クロス分析CSV生成"""

    # MobilityScore.csvにペルソナID追加
    mobility_with_persona = self.df_processed.merge(
        self.results['mobility_score'],
        left_on='id',
        right_on='申請者ID'
    )

    # クロス集計
    cross_table = pd.crosstab(
        mobility_with_persona['cluster'],
        mobility_with_persona['移動許容度レベル']
    )

    # CSV出力
    cross_table.to_csv('gas_output_phase7/PersonaMobilityCross.csv')
```

**Option B: GAS側で結合**
- 複雑性が増す
- パフォーマンス低下
- 推奨しない

**推奨**: Option A（Python側で事前結合）

### 2. Google Maps API利用

**必要な設定**:
1. Google Cloud Platformでプロジェクト作成
2. Maps JavaScript API有効化
3. APIキー取得
4. 使用量制限設定（コスト管理）

**コスト**:
- 月間28,000マップロード: 無料
- それ以降: $7/1000ロード
- 想定使用量: 月100ロード程度 → **無料範囲内**

**セキュリティ**:
- APIキー制限（HTTPリファラー制限）
- スクリプトプロパティで管理

```javascript
// GAS側でAPIキー取得
const API_KEY = PropertiesService.getScriptProperties().getProperty('MAPS_API_KEY');
```

### 3. パフォーマンス最適化

**課題**: MobilityScore.csv（7,390行）の読み込み・描画

**対策**:

1. **サンプリング**（既存実装）:
   ```javascript
   const maxRows = Math.min(lastRow - 1, 1000);
   ```

2. **遅延ロード**:
   ```javascript
   // タブ切り替え時のみチャート描画
   function showTab(tabName) {
     if (!loadedTabs[tabName]) {
       loadChartData(tabName);
       loadedTabs[tabName] = true;
     }
   }
   ```

3. **キャッシング**:
   ```javascript
   // データを一度だけ読み込み
   const cachedData = CacheService.getScriptCache();
   ```

### 4. テスト戦略

**ユニットテスト**:
- データ読み込み関数（`loadPersonaProfileData()`）
- 統計計算関数（`calculateMobilityStats()`）
- フィルタロジック（`applyFilters()`）

**統合テスト**:
- HTML生成（`generatePersonaProfileHTML()`）
- チャート描画（`drawRadarChart()`）

**E2Eテスト**:
- メニューから可視化呼び出し → 表示確認
- フィルタ操作 → チャート更新確認
- ドリルダウン → モーダル表示確認

**テストツール**:
- Node.js + gas_e2e_test.js（既存）
- 手動テスト（GASエディタ）

---

## 📝 実装チェックリスト

### Python側（1時間）

#### クロス分析CSV生成
- [ ] `phase7_advanced_analysis.py`に`_generate_persona_mobility_cross()`関数追加
- [ ] df_processedとmobility_scoreをマージ
- [ ] クロス集計（ペルソナ×移動許容度レベル）
- [ ] `PersonaMobilityCross.csv`出力
- [ ] E2Eテストで検証

### GAS側（8時間）

#### 機能2: クロス分析（1時間）
- [ ] `Phase7PersonaMobilityCrossViz.gs`作成
- [ ] `PersonaMobilityCross.csv`読み込み関数
- [ ] 積み上げ棒グラフ描画
- [ ] 100%積み上げ棒グラフ描画
- [ ] ヒートマップ描画（オプション）
- [ ] メニュー統合

#### 機能1: ペルソナ地図（4時間）
- [ ] `Phase7PersonaMapViz.gs`作成
- [ ] MapMetrics.csvとPersonaProfile.csvの結合ロジック
- [ ] Google Maps API統合
- [ ] バブルマーカー描画（ペルソナ別色分け）
- [ ] インフォウィンドウ実装
- [ ] ペルソナフィルタUI実装
- [ ] メニュー統合

#### 機能3: インタラクティブフィルタ（2時間）
- [ ] フィルタパネルHTML実装
- [ ] レベル別フィルタ
- [ ] スコア範囲フィルタ
- [ ] 居住地フィルタ
- [ ] フィルタロジック実装
- [ ] チャート再描画ロジック

#### 機能4: ドリルダウン（1時間）
- [ ] モーダルコンポーネント実装
- [ ] ペルソナ詳細モーダル
- [ ] 地図マーカークリック詳細
- [ ] 求職者リスト表示

#### テスト・ドキュメント
- [ ] 全機能のE2Eテスト
- [ ] README.md更新
- [ ] GAS_COMPLETE_FEATURE_LIST.md更新

---

## 🎯 成功基準

### 定量的基準

| 指標 | 現状 | 目標 | 測定方法 |
|------|------|------|---------|
| **可視化深度** | 3/5 | **5/5** | 機能カウント |
| **インタラクティブ性** | 2/5 | **5/5** | フィルタ・ドリルダウン有無 |
| **地図連携** | 0/5 | **5/5** | ペルソナ地図実装有無 |
| **クロス分析** | 0/5 | **5/5** | クロス分析チャート有無 |
| **ユーザー操作数** | 平均2回 | **平均5回以上** | クリック・フィルタ操作数 |

### 定性的基準

- [ ] 採用担当者が「どのペルソナをどこで採用すべきか」を即座に判断できる
- [ ] 地図上でペルソナ分布を直感的に理解できる
- [ ] フィルタで任意の条件に絞り込んで分析できる
- [ ] ドリルダウンで深掘り分析ができる
- [ ] 他社のBIツール（Tableau等）と遜色ない可視化品質

---

## 📚 参考資料

### Google Maps JavaScript API
- 公式ドキュメント: https://developers.google.com/maps/documentation/javascript
- バブルマーカー実装例: https://developers.google.com/maps/documentation/javascript/examples/marker-animations

### Google Charts
- 積み上げ棒グラフ: https://developers.google.com/chart/interactive/docs/gallery/columnchart#stacked
- ヒートマップ: https://developers.google.com/chart/interactive/docs/gallery/table#heatmap

### GAS HTMLService
- モーダルダイアログ: https://developers.google.com/apps-script/guides/html/communication

---

## 🔄 次のステップ

1. **ultrathinkセルフレビュー（10回繰り返し）**
   - 実現可能性検証
   - リスク分析
   - 代替案検討
   - 実装順序最適化

2. **ユーザー承認**
   - 改良計画の承認
   - 優先順位の合意

3. **実装開始**
   - フェーズ1（クロス分析）から着手
   - フェーズ2（地図連携）
   - フェーズ3（インタラクティブ機能）

---

**作成者**: Claude Code
**ステータス**: レビュー待ち
**次のアクション**: ultrathinkセルフレビュー実行
