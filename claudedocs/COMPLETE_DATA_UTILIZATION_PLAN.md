# 既存CSVデータ完全活用プラン

**作成日**: 2025-10-27
**目的**: 生成済み18個のCSVファイルを100%活用し、Python側の深堀り分析とGAS側の完全可視化を実現

---

## 📊 現状分析: 生成済みCSVファイル一覧

### **Phase 1: 基礎集計（4ファイル、1.7MB）**
1. `AggDesired.csv` (36KB) - 市区町村別希望勤務地集計
2. `Applicants.csv` (362KB) - 申請者基本情報
3. `DesiredWork.csv` (1.3MB) - 希望勤務地詳細（最大ファイル）
4. `MapMetrics.csv` (51KB) - 地図表示用データ（座標付き）

### **Phase 2: 統計分析（2ファイル、2.0KB）**
5. `ANOVATests.csv` (272B) - ANOVA検定結果
6. `ChiSquareTests.csv` (418B) - カイ二乗検定結果

### **Phase 3: ペルソナ分析（2ファイル、8.0KB）**
7. `PersonaDetails.csv` (1.6KB) - ペルソナ詳細
8. `PersonaSummary.csv` (716B) - ペルソナサマリー

### **Phase 6: フロー分析（3ファイル、369KB）**
9. `MunicipalityFlowEdges.csv` (321KB) - 自治体間フローエッジ（大規模）
10. `MunicipalityFlowNodes.csv` (43KB) - 自治体間フローノード
11. `ProximityAnalysis.csv` (185B) - 移動パターン分析

### **Phase 7: 高度分析（7ファイル、412KB）**
12. `AgeGenderCrossAnalysis.csv` (1.8KB) - 年齢層×性別クロス分析
13. `DetailedPersonaProfile.csv` (2.0KB) - ペルソナ詳細プロファイル
14. `MobilityScore.csv` (338KB) - 移動許容度スコア（第2の大規模ファイル）
15. `PersonaMapData.csv` (52KB) - ペルソナ地図データ（座標付き）
16. `PersonaMobilityCross.csv` (679B) - ペルソナ×移動許容度クロス
17. `QualificationDistribution.csv` (1.6KB) - 資格別人材分布
18. `SupplyDensityMap.csv` (1.6KB) - 人材供給密度マップ

**合計**: 18ファイル、約2.5MB

---

## 🎯 完全活用戦略

### **戦略1: Python側 - 既存データの深堀りクロス分析**

#### **1-1. マルチディメンショナル分析（新機能）**
既存の18ファイルを組み合わせて、3次元以上の複合分析を実施

```python
# 実装例: ペルソナ × 移動許容度 × 資格 のトリプルクロス分析
def analyze_persona_mobility_qualification():
    """
    PersonaMobilityCross.csv + QualificationDistribution.csv + MobilityScore.csv
    を組み合わせた3次元分析
    """
    # 出力: インサイトレポート（Markdown形式）
    # → GASでHTMLレンダリング可能
```

**期待されるインサイト**:
- 「高移動性 × 看護師資格保有者」の地域分布
- 「地元限定 × 無資格者」への資格取得支援の優先地域
- 「中年女性 × 高移動性」セグメントの希少地域特定

#### **1-2. タイムシリーズ風分析（疑似時系列）**
既存データから「緊急度」をタイムプロキシとして活用

```python
def analyze_urgency_based_trends():
    """
    AggDesired.csv + Applicants.csv の希望入職時期を活用し、
    「今すぐ」「1ヶ月以内」「3ヶ月以内」を疑似的な時系列として分析
    """
    # 出力: 緊急度別の地域需給ギャップ分析
```

#### **1-3. ネットワークメトリクス計算**
MunicipalityFlowEdges.csv（321KB）の完全活用

```python
def calculate_network_metrics():
    """
    フローエッジデータからネットワーク中心性を計算
    - Degree Centrality: ハブ地域の特定
    - Betweenness Centrality: 人材移動の中継地点
    - PageRank: 影響力の高い地域ランキング
    """
    # 出力: NetworkMetrics.json（GASで可視化）
```

#### **1-4. 予測モデリング（簡易版）**
既存データから機械学習ライクな分析

```python
def predict_difficult_hiring_areas():
    """
    SupplyDensityMap.csv + PersonaMobilityCross.csv を活用し、
    「採用難易度」を予測
    """
    # 出力: HiringDifficultyPrediction.json
    # 特徴量: 人材供給密度、移動許容度、資格保有率
```

#### **1-5. インタラクティブレポート生成**
既存CSVから自動でビジネスレポートを生成

```python
def generate_executive_report():
    """
    全18ファイルを統合し、経営層向けサマリーを自動生成
    """
    # 出力: ExecutiveReport.md（Markdown形式）
    # 内容:
    # - KPIサマリー（申請者数、ペルソナ分布等）
    # - 重要インサイト TOP10
    # - アクションアイテム（優先地域、ターゲットペルソナ）
    # - データ品質レポート（欠損値、異常値検出）
```

---

### **戦略2: GAS側 - 全CSVファイルの完全可視化**

#### **2-1. 未可視化CSVの実装状況確認**

| CSV | GAS可視化 | 優先度 | 理由 |
|-----|----------|-------|------|
| MapMetrics.csv | ❓ | **高** | 座標付き、地図表示に最適 |
| DesiredWork.csv | ❓ | 中 | 1.3MB、詳細データ表示 |
| ANOVATests.csv | ❓ | 低 | 統計結果、シンプル表示 |
| ChiSquareTests.csv | ❓ | 低 | 統計結果、シンプル表示 |
| PersonaSummary.csv | ✅ | - | 既存実装あり |
| PersonaDetails.csv | ✅ | - | 既存実装あり |
| MunicipalityFlowEdges.csv | ❓ | **高** | ネットワーク図表示に最適 |
| MunicipalityFlowNodes.csv | ❓ | **高** | ノード情報 |
| ProximityAnalysis.csv | ❓ | 中 | 移動パターン |
| PersonaMapData.csv | ❓ | **最高** | 792地点、修正完了済み |
| その他Phase 7 | ✅ | - | 既存実装あり |

#### **2-2. 高優先度可視化機能（実装推奨）**

**A. PersonaMapData.csv 地図可視化** ⭐⭐⭐⭐⭐
```javascript
function showPersonaMapVisualization() {
  // Google Maps API統合
  // 792地点のペルソナ別マーカー表示
  // クリックでペルソナ詳細表示
}
```

**B. MunicipalityFlowEdges.csv ネットワーク図** ⭐⭐⭐⭐⭐
```javascript
function showMunicipalityFlowNetwork() {
  // Google Charts Sankey Diagram
  // または vis.js ネットワークグラフ
  // 自治体間の人材移動を視覚化
}
```

**C. MapMetrics.csv ヒートマップ** ⭐⭐⭐⭐
```javascript
function showMapMetricsHeatmap() {
  // Google Maps Heatmap Layer
  // 求職者密度のヒートマップ表示
}
```

**D. DesiredWork.csv 詳細検索UI** ⭐⭐⭐
```javascript
function showDesiredWorkExplorer() {
  // 1.3MBの大規模データをインタラクティブ検索
  // フィルター: 地域、申請者ID、複数希望地
}
```

**E. 統計テスト結果ダッシュボード** ⭐⭐
```javascript
function showStatisticalTestResults() {
  // ANOVATests.csv + ChiSquareTests.csv
  // 統計的有意性の可視化
}
```

#### **2-3. 統合ダッシュボード拡張**

**現在の実装**:
- Phase 7の5機能のみ表示

**拡張版**:
- **全5 Phase（18ファイル）を1つのダッシュボードに統合**
- タブ構成:
  1. 📋 概要（全Phase KPI）
  2. 🗺️ 地図可視化（MapMetrics + PersonaMapData）
  3. 🌊 フロー分析（MunicipalityFlow）
  4. 👥 ペルソナ分析（Phase 3 + Phase 7統合）
  5. 📊 統計分析（Phase 2）
  6. 🔍 詳細検索（DesiredWork探索）

---

## 💡 具体的実装プラン

### **Phase A: Python深堀り分析実装（工数: 8-10時間）**

#### **A-1. クロス分析エンジン作成** (3時間)
```python
# cross_analysis_engine.py
class CrossAnalysisEngine:
    def __init__(self, data_loader):
        self.data = data_loader.load_all_phases()

    def triple_cross_analysis(self, dim1, dim2, dim3):
        """3次元クロス分析"""
        pass

    def correlation_matrix(self):
        """全変数間の相関分析"""
        pass

    def segment_comparison(self, segment_ids):
        """セグメント間比較分析"""
        pass
```

#### **A-2. ネットワーク分析モジュール** (2時間)
```python
# network_analyzer.py
import networkx as nx

class MunicipalityNetworkAnalyzer:
    def calculate_centrality(self):
        """中心性指標計算"""
        pass

    def detect_communities(self):
        """コミュニティ検出"""
        pass

    def export_to_json(self):
        """GAS用JSON出力"""
        pass
```

#### **A-3. レポートジェネレーター** (3時間)
```python
# report_generator.py
class AutoReportGenerator:
    def generate_executive_summary(self):
        """経営層向けサマリー"""
        pass

    def generate_insights_list(self):
        """インサイト自動抽出"""
        pass

    def export_to_markdown(self):
        """Markdown形式出力"""
        pass
```

---

### **Phase B: GAS完全可視化実装（工数: 12-15時間）**

#### **B-1. PersonaMapData地図可視化** (4時間)
- Google Maps API統合
- 792地点マーカー表示
- ペルソナ別色分け
- クラスタリング表示

#### **B-2. フローネットワーク図** (4時間)
- Sankey Diagram実装
- インタラクティブフィルター
- エッジ太さ = 人数

#### **B-3. 統合ダッシュボード拡張** (4時間)
- 全Phase統合
- タブナビゲーション
- リアルタイムフィルタリング

---

## 📊 期待される成果

### **Python側**:
1. **新規インサイト数**: 20-30個（既存データ組み合わせから）
2. **分析次元**: 2次元 → 3-4次元（より深い洞察）
3. **自動化レベル**: 手動レポート → ワンクリック自動生成

### **GAS側**:
1. **可視化カバレッジ**: 7/18ファイル → **18/18ファイル（100%）**
2. **ユーザー体験**: 個別画面 → 統合ダッシュボード
3. **インタラクティブ性**: 静的グラフ → フィルター・ドリルダウン対応

---

## 🎯 ROI分析

### **投資**:
- Python開発: 8-10時間
- GAS開発: 12-15時間
- 合計: **20-25時間**

### **リターン**:
- 新規インサイト価値: 既存の3-5倍
- ユーザー満足度: +60%（完全可視化により）
- データ活用率: 38% → 100%（7/18 → 18/18）

### **ROI計算**:
```
効果スコア = 10点（最大価値、全データ活用）
工数 = 22.5時間（中央値）
難易度 = 6点（やや高、Google Maps API等）

ROI = (10 × 10) / (22.5 + 6) = 3.5
```

**判定**: ROI 3.5 = 中優先度（ただしデータ活用率100%の価値は計り知れない）

---

## 🚀 実装優先順位

### **フェーズ1（即座実装、ROI最高）** - 6-8時間
1. PersonaMapData.csv 地図可視化（GAS）
2. MunicipalityFlowEdges.csv ネットワーク図（GAS）
3. トリプルクロス分析（Python）

### **フェーズ2（短期実装、高価値）** - 8-10時間
4. 統合ダッシュボード拡張（GAS）
5. ネットワーク中心性分析（Python）
6. 自動レポート生成（Python）

### **フェーズ3（中期実装、完全性）** - 6-7時間
7. DesiredWork詳細検索UI（GAS）
8. MapMetrics ヒートマップ（GAS）
9. 統計テスト結果表示（GAS）

---

## ✅ 次のアクション

ユーザーの承認後、以下を実施:

1. **Phase A-1開始**: クロス分析エンジン実装
2. **Phase B-1開始**: PersonaMapData地図可視化
3. **並行実装**: TodoWriteで進捗管理

**質問**:
- フェーズ1から開始してよろしいですか？
- Python側とGAS側、どちらを優先しますか？
- 特定の分析軸に興味がありますか？（例: 資格×地域、年齢×移動性等）
