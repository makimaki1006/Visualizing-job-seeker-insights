# Phase 2-3 詳細設計書

**作成日**: 2025-10-27
**前提**: Phase 1実装完了後に実施
**目的**: MunicipalityFlowネットワーク図、全Phase統合ダッシュボード、ヒートマップ等の詳細設計

---

## Phase 2実装詳細

### **2-1. MunicipalityFlowネットワーク図（GAS）**

#### **目的**
MunicipalityFlowEdges.csv（321KB、数千エッジ）とFlowNodes.csvをSankeyダイアグラムで可視化

#### **技術スタック**
- Google Charts API（Sankey Diagram）
- GAS HTMLService
- トップ100エッジフィルター（パフォーマンス対策）

#### **詳細設計**

##### **ファイル**: `gas_files/scripts/MunicipalityFlowNetworkViz.gs`

```javascript
/**
 * MunicipalityFlow ネットワーク図可視化
 *
 * 機能:
 * - 自治体間人材移動フローをSankeyダイアグラムで表示
 * - TOP100エッジのみ表示（パフォーマンス最適化）
 * - エッジホバー → 詳細表示
 * - フィルター機能（移動人数閾値、都道府県選択）
 */

function showMunicipalityFlowNetwork() {
  const ui = SpreadsheetApp.getUi();

  try {
    // エッジデータ読み込み
    const edges = loadMunicipalityFlowEdges();
    const nodes = loadMunicipalityFlowNodes();

    if (!edges || edges.length === 0) {
      ui.alert(
        'データなし',
        'MunicipalityFlowEdgesシートにデータがありません。',
        ui.ButtonSet.OK
      );
      return;
    }

    // HTML生成
    const html = generateFlowNetworkHTML(edges, nodes);

    const htmlOutput = HtmlService.createHtmlOutput(html)
      .setWidth(1600)
      .setHeight(1000);

    ui.showModalDialog(htmlOutput, '自治体間人材移動フローネットワーク');

  } catch (error) {
    ui.alert('エラー', `ネットワーク図生成中にエラーが発生しました:\n${error.message}`, ui.ButtonSet.OK);
    Logger.log(`FlowNetwork可視化エラー: ${error.stack}`);
  }
}

/**
 * FlowEdges読み込み
 */
function loadMunicipalityFlowEdges() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName('Phase6_MunicipalityFlowEdges');

  if (!sheet) {
    throw new Error('Phase6_MunicipalityFlowEdgesシートが見つかりません');
  }

  const lastRow = sheet.getLastRow();
  if (lastRow <= 1) return [];

  // TOP100エッジのみ読み込み（パフォーマンス対策）
  const data = sheet.getRange(2, 1, Math.min(lastRow - 1, 100), sheet.getLastColumn()).getValues();

  return data.map(row => ({
    fromNode: row[0],
    toNode: row[1],
    count: parseInt(row[2]),
    avgDistance: parseFloat(row[3])
  }));
}

/**
 * FlowNodes読み込み
 */
function loadMunicipalityFlowNodes() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName('Phase6_MunicipalityFlowNodes');

  if (!sheet) {
    throw new Error('Phase6_MunicipalityFlowNodesシートが見つかりません');
  }

  const lastRow = sheet.getLastRow();
  if (lastRow <= 1) return [];

  const data = sheet.getRange(2, 1, lastRow - 1, sheet.getLastColumn()).getValues();

  return data.map(row => ({
    nodeId: row[0],
    totalApplicants: parseInt(row[1])
  }));
}

/**
 * FlowNetworkHTML生成
 */
function generateFlowNetworkHTML(edges, nodes) {
  const edgesJson = JSON.stringify(edges);
  const nodesJson = JSON.stringify(nodes);

  return `
<!DOCTYPE html>
<html>
<head>
  <base target="_top">
  <script type="text/javascript" src="https://www.gstatic.com/charts/loader.js"></script>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: Arial, sans-serif; padding: 20px; }

    .header {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      padding: 30px;
      border-radius: 12px;
      margin-bottom: 20px;
    }

    .header h1 {
      font-size: 28px;
      margin-bottom: 10px;
    }

    .controls {
      background: white;
      padding: 20px;
      border-radius: 8px;
      margin-bottom: 20px;
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }

    .controls label {
      margin-right: 15px;
      font-weight: bold;
    }

    .controls input, .controls select {
      padding: 8px;
      border: 1px solid #ddd;
      border-radius: 4px;
      margin-right: 20px;
    }

    #chart_div {
      background: white;
      padding: 20px;
      border-radius: 8px;
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }

    .stats {
      background: white;
      padding: 20px;
      border-radius: 8px;
      margin-top: 20px;
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }

    .stats h3 {
      margin-bottom: 15px;
      color: #1a73e8;
    }

    .stat-grid {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 15px;
    }

    .stat-card {
      padding: 15px;
      background: #f5f5f5;
      border-radius: 6px;
      text-align: center;
    }

    .stat-card .value {
      font-size: 24px;
      font-weight: bold;
      color: #1a73e8;
    }

    .stat-card .label {
      font-size: 12px;
      color: #666;
      margin-top: 5px;
    }
  </style>
</head>
<body>
  <div class="header">
    <h1>🌊 自治体間人材移動フローネットワーク</h1>
    <p>Phase 6データ | Sankeyダイアグラムで人材移動パターンを可視化</p>
  </div>

  <div class="controls">
    <label>最小人数:</label>
    <input type="number" id="min-count" value="5" min="1" max="100">

    <label>表示エッジ数:</label>
    <select id="edge-limit">
      <option value="50">TOP 50</option>
      <option value="100" selected>TOP 100</option>
      <option value="200">TOP 200</option>
    </select>

    <button onclick="updateChart()" style="padding: 10px 20px; background: #1a73e8; color: white; border: none; border-radius: 4px; cursor: pointer;">
      フィルター適用
    </button>
  </div>

  <div id="chart_div"></div>

  <div class="stats">
    <h3>📊 フローネットワーク統計</h3>
    <div class="stat-grid">
      <div class="stat-card">
        <div class="value" id="total-edges">0</div>
        <div class="label">総エッジ数</div>
      </div>
      <div class="stat-card">
        <div class="value" id="total-applicants">0</div>
        <div class="label">総移動人数</div>
      </div>
      <div class="stat-card">
        <div class="value" id="avg-distance">0</div>
        <div class="label">平均移動距離（km）</div>
      </div>
      <div class="stat-card">
        <div class="value" id="unique-nodes">0</div>
        <div class="label">ユニーク自治体数</div>
      </div>
    </div>
  </div>

  <script>
    const edgesData = ${edgesJson};
    const nodesData = ${nodesJson};

    google.charts.load('current', {'packages':['sankey']});
    google.charts.setOnLoadCallback(init);

    function init() {
      updateChart();
    }

    function updateChart() {
      const minCount = parseInt(document.getElementById('min-count').value) || 1;
      const edgeLimit = parseInt(document.getElementById('edge-limit').value) || 100;

      // フィルター適用
      const filteredEdges = edgesData
        .filter(edge => edge.count >= minCount)
        .slice(0, edgeLimit);

      // 統計更新
      updateStats(filteredEdges);

      // Sankeyダイアグラム描画
      drawSankey(filteredEdges);
    }

    function drawSankey(edges) {
      const chartData = new google.visualization.DataTable();
      chartData.addColumn('string', 'From');
      chartData.addColumn('string', 'To');
      chartData.addColumn('number', 'Count');

      edges.forEach(edge => {
        chartData.addRow([edge.fromNode, edge.toNode, edge.count]);
      });

      const options = {
        height: 700,
        sankey: {
          node: {
            colors: ['#4285F4', '#34A853', '#FBBC04', '#EA4335']
          },
          link: {
            colorMode: 'gradient',
            colors: ['#a6cee3', '#b2df8a', '#fb9a99', '#fdbf6f']
          }
        }
      };

      const chart = new google.visualization.Sankey(document.getElementById('chart_div'));
      chart.draw(chartData, options);
    }

    function updateStats(edges) {
      const totalEdges = edges.length;
      const totalApplicants = edges.reduce((sum, edge) => sum + edge.count, 0);
      const avgDistance = edges.reduce((sum, edge) => sum + (edge.avgDistance * edge.count), 0) / totalApplicants;

      const uniqueNodes = new Set();
      edges.forEach(edge => {
        uniqueNodes.add(edge.fromNode);
        uniqueNodes.add(edge.toNode);
      });

      document.getElementById('total-edges').textContent = totalEdges;
      document.getElementById('total-applicants').textContent = totalApplicants.toLocaleString();
      document.getElementById('avg-distance').textContent = avgDistance.toFixed(1);
      document.getElementById('unique-nodes').textContent = uniqueNodes.size;
    }
  </script>
</body>
</html>
  `;
}
```

#### **工数見積**: 4時間

---

### **2-2. ネットワーク中心性分析（Python）**

#### **目的**
MunicipalityFlowEdges.csvからネットワーク中心性指標を計算

#### **技術スタック**
- networkx（ネットワーク分析）
- pandas（データ操作）

#### **詳細設計**

##### **ファイル**: `python_scripts/network_analyzer.py`

```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ネットワーク中心性分析

MunicipalityFlowEdges.csvから以下を計算:
- Degree Centrality（次数中心性）: ハブ自治体の特定
- Betweenness Centrality（媒介中心性）: 人材移動の中継地点
- PageRank: 影響力の高い自治体ランキング
"""

import pandas as pd
import networkx as nx
from pathlib import Path
import json


class NetworkAnalyzer:
    """ネットワーク中心性分析"""

    def __init__(self, edges_csv_path: str):
        """
        初期化

        Args:
            edges_csv_path: FlowEdges CSVファイルパス
        """
        self.edges_csv_path = Path(edges_csv_path)
        self.graph = None
        self.metrics = {}

    def load_and_build_graph(self):
        """エッジデータ読み込み & グラフ構築"""
        print("\n[ネットワーク構築] FlowEdges読み込み中...")

        edges_df = pd.read_csv(self.edges_csv_path, encoding='utf-8-sig')

        # 有向グラフ構築
        self.graph = nx.DiGraph()

        for _, row in edges_df.iterrows():
            from_node = row.iloc[0]  # 第1列
            to_node = row.iloc[1]    # 第2列
            count = row.iloc[2]      # 第3列

            self.graph.add_edge(from_node, to_node, weight=count)

        print(f"  [OK] ノード数: {self.graph.number_of_nodes()}")
        print(f"  [OK] エッジ数: {self.graph.number_of_edges()}")

    def calculate_degree_centrality(self):
        """次数中心性計算"""
        print("\n[分析1] 次数中心性計算中...")

        degree_centrality = nx.degree_centrality(self.graph)

        # TOP10取得
        top10 = sorted(degree_centrality.items(), key=lambda x: x[1], reverse=True)[:10]

        self.metrics['degree_centrality'] = {
            'top10': [{'node': node, 'score': score} for node, score in top10],
            'description': 'ハブ自治体（接続数が多い）'
        }

        print(f"  [OK] TOP10ハブ自治体:")
        for i, (node, score) in enumerate(top10, 1):
            print(f"    {i}. {node}: {score:.4f}")

    def calculate_betweenness_centrality(self):
        """媒介中心性計算"""
        print("\n[分析2] 媒介中心性計算中...")

        betweenness_centrality = nx.betweenness_centrality(self.graph, weight='weight')

        # TOP10取得
        top10 = sorted(betweenness_centrality.items(), key=lambda x: x[1], reverse=True)[:10]

        self.metrics['betweenness_centrality'] = {
            'top10': [{'node': node, 'score': score} for node, score in top10],
            'description': '人材移動の中継地点（経由が多い）'
        }

        print(f"  [OK] TOP10中継地点:")
        for i, (node, score) in enumerate(top10, 1):
            print(f"    {i}. {node}: {score:.4f}")

    def calculate_pagerank(self):
        """PageRank計算"""
        print("\n[分析3] PageRank計算中...")

        pagerank = nx.pagerank(self.graph, weight='weight')

        # TOP10取得
        top10 = sorted(pagerank.items(), key=lambda x: x[1], reverse=True)[:10]

        self.metrics['pagerank'] = {
            'top10': [{'node': node, 'score': score} for node, score in top10],
            'description': '影響力の高い自治体（PageRank）'
        }

        print(f"  [OK] TOP10影響力自治体:")
        for i, (node, score) in enumerate(top10, 1):
            print(f"    {i}. {node}: {score:.4f}")

    def export_to_json(self, output_path: str = 'gas_output_insights/NetworkMetrics.json'):
        """JSON出力"""
        output_file = Path(output_path)
        output_file.parent.mkdir(exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.metrics, f, ensure_ascii=False, indent=2)

        print(f"\n[出力] {output_file}")

    def run_all_analyses(self):
        """全分析実行"""
        print("\n" + "=" * 60)
        print("ネットワーク中心性分析")
        print("=" * 60)

        self.load_and_build_graph()
        self.calculate_degree_centrality()
        self.calculate_betweenness_centrality()
        self.calculate_pagerank()
        self.export_to_json()

        print("\n" + "=" * 60)
        print("分析完了")
        print("=" * 60)


if __name__ == '__main__':
    analyzer = NetworkAnalyzer('gas_output_phase6/MunicipalityFlowEdges.csv')
    analyzer.run_all_analyses()
```

#### **工数見積**: 2時間

---

### **2-3. 全Phase統合ダッシュボード（GAS）**

#### **目的**
Phase 1-7の全データを1つのダッシュボードで切り替え表示

#### **技術スタック**
- Google Charts API
- タブ切り替えUI
- 遅延ロード（パフォーマンス最適化）

#### **詳細設計**

##### **ファイル**: `gas_files/scripts/CompleteIntegratedDashboard.gs`

```javascript
/**
 * 全Phase統合ダッシュボード（拡張版）
 *
 * 機能:
 * - Phase 1-7のすべてのデータを統合表示
 * - タブ切り替えで各分析を表示
 * - 遅延ロード（初回クリック時にデータ読み込み）
 * - フィルター連携（ペルソナ選択等）
 */

function showCompleteIntegratedDashboard() {
  const ui = SpreadsheetApp.getUi();

  try {
    // 概要データのみ先行読み込み
    const overview = loadDashboardOverview();

    // HTML生成
    const html = generateCompleteIntegratedDashboardHTML(overview);

    const htmlOutput = HtmlService.createHtmlOutput(html)
      .setWidth(1800)
      .setHeight(1000);

    ui.showModalDialog(htmlOutput, '全Phase統合ダッシュボード');

  } catch (error) {
    ui.alert('エラー', `ダッシュボード生成中にエラーが発生しました:\n${error.message}`, ui.ButtonSet.OK);
  }
}

/**
 * 概要データ読み込み（軽量）
 */
function loadDashboardOverview() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();

  return {
    phase1Files: countSheetsByPrefix('Phase1_'),
    phase2Files: countSheetsByPrefix('Phase2_'),
    phase3Files: countSheetsByPrefix('Phase3_'),
    phase6Files: countSheetsByPrefix('Phase6_'),
    phase7Files: countSheetsByPrefix('Phase7_'),
    totalApplicants: getTotalApplicants(),
    totalMunicipalities: getTotalMunicipalities()
  };
}

/**
 * シート数カウント
 */
function countSheetsByPrefix(prefix) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheets = ss.getSheets();
  return sheets.filter(s => s.getName().startsWith(prefix)).length;
}

/**
 * 総申請者数取得
 */
function getTotalApplicants() {
  try {
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    const sheet = ss.getSheetByName('Phase1_Applicants');
    if (!sheet) return 0;

    return sheet.getLastRow() - 1;  // ヘッダー除く
  } catch (error) {
    return 0;
  }
}

/**
 * 総自治体数取得
 */
function getTotalMunicipalities() {
  try {
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    const sheet = ss.getSheetByName('Phase7_PersonaMapData');
    if (!sheet) return 0;

    const data = sheet.getRange(2, 1, sheet.getLastRow() - 1, 1).getValues();
    const uniqueMunicipalities = new Set(data.map(row => row[0]));
    return uniqueMunicipalities.size;
  } catch (error) {
    return 0;
  }
}

/**
 * 統合ダッシュボードHTML生成
 */
function generateCompleteIntegratedDashboardHTML(overview) {
  const overviewJson = JSON.stringify(overview);

  return `
<!DOCTYPE html>
<html>
<head>
  <base target="_top">
  <script type="text/javascript" src="https://www.gstatic.com/charts/loader.js"></script>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: 'Segoe UI', Arial, sans-serif; background: #f5f5f5; }

    .header {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      padding: 40px;
      text-align: center;
    }

    .header h1 {
      font-size: 32px;
      margin-bottom: 10px;
    }

    .tabs {
      display: flex;
      background: white;
      padding: 0 40px;
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
      position: sticky;
      top: 0;
      z-index: 100;
    }

    .tab {
      padding: 15px 30px;
      cursor: pointer;
      border-bottom: 3px solid transparent;
      transition: all 0.3s;
    }

    .tab:hover {
      background: #f5f5f5;
    }

    .tab.active {
      border-bottom-color: #1a73e8;
      color: #1a73e8;
      font-weight: bold;
    }

    .tab-content {
      display: none;
      padding: 40px;
    }

    .tab-content.active {
      display: block;
    }

    .kpi-grid {
      display: grid;
      grid-template-columns: repeat(5, 1fr);
      gap: 20px;
      margin-bottom: 40px;
    }

    .kpi-card {
      background: white;
      padding: 30px;
      border-radius: 12px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.1);
      text-align: center;
    }

    .kpi-card .value {
      font-size: 36px;
      font-weight: bold;
      color: #1a73e8;
      margin-bottom: 10px;
    }

    .kpi-card .label {
      font-size: 14px;
      color: #666;
    }

    .chart-container {
      background: white;
      padding: 30px;
      border-radius: 12px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.1);
      margin-bottom: 20px;
    }

    .loading {
      text-align: center;
      padding: 50px;
      color: #666;
    }
  </style>
</head>
<body>
  <div class="header">
    <h1>📊 全Phase統合ダッシュボード</h1>
    <p>Phase 1-7のすべてのデータを統合可視化</p>
  </div>

  <div class="tabs">
    <div class="tab active" onclick="switchTab(0)">📋 概要</div>
    <div class="tab" onclick="switchTab(1)">🗺️ 地図（PersonaMapData）</div>
    <div class="tab" onclick="switchTab(2)">🌊 フロー（MunicipalityFlow）</div>
    <div class="tab" onclick="switchTab(3)">👥 ペルソナ分析</div>
    <div class="tab" onclick="switchTab(4)">📊 Phase 7高度分析</div>
    <div class="tab" onclick="switchTab(5)">📈 統計テスト</div>
  </div>

  <!-- タブ0: 概要 -->
  <div class="tab-content active" id="tab-0">
    <div class="kpi-grid">
      <div class="kpi-card">
        <div class="value" id="total-applicants">0</div>
        <div class="label">総申請者数</div>
      </div>
      <div class="kpi-card">
        <div class="value" id="total-municipalities">0</div>
        <div class="label">総自治体数</div>
      </div>
      <div class="kpi-card">
        <div class="value" id="phase1-files">0</div>
        <div class="label">Phase 1ファイル</div>
      </div>
      <div class="kpi-card">
        <div class="value" id="phase7-files">0</div>
        <div class="label">Phase 7ファイル</div>
      </div>
      <div class="kpi-card">
        <div class="value">18</div>
        <div class="label">総CSVファイル</div>
      </div>
    </div>

    <div class="chart-container">
      <h2>データ可用性</h2>
      <div id="overview-chart"></div>
    </div>
  </div>

  <!-- タブ1: 地図 -->
  <div class="tab-content" id="tab-1">
    <div class="loading">
      地図データを読み込んでいます...
    </div>
  </div>

  <!-- タブ2: フロー -->
  <div class="tab-content" id="tab-2">
    <div class="loading">
      フローデータを読み込んでいます...
    </div>
  </div>

  <!-- タブ3: ペルソナ -->
  <div class="tab-content" id="tab-3">
    <div class="loading">
      ペルソナデータを読み込んでいます...
    </div>
  </div>

  <!-- タブ4: Phase 7 -->
  <div class="tab-content" id="tab-4">
    <div class="loading">
      Phase 7データを読み込んでいます...
    </div>
  </div>

  <!-- タブ5: 統計テスト -->
  <div class="tab-content" id="tab-5">
    <div class="loading">
      統計テストデータを読み込んでいます...
    </div>
  </div>

  <script>
    const overview = ${overviewJson};
    const tabDataLoaded = [true, false, false, false, false, false];

    google.charts.load('current', {'packages':['corechart']});
    google.charts.setOnLoadCallback(init);

    function init() {
      renderOverviewKPIs();
      drawOverviewChart();
    }

    function renderOverviewKPIs() {
      document.getElementById('total-applicants').textContent = overview.totalApplicants.toLocaleString();
      document.getElementById('total-municipalities').textContent = overview.totalMunicipalities;
      document.getElementById('phase1-files').textContent = overview.phase1Files;
      document.getElementById('phase7-files').textContent = overview.phase7Files;
    }

    function drawOverviewChart() {
      const chartData = new google.visualization.DataTable();
      chartData.addColumn('string', 'Phase');
      chartData.addColumn('number', 'ファイル数');

      chartData.addRow(['Phase 1', overview.phase1Files]);
      chartData.addRow(['Phase 2', overview.phase2Files]);
      chartData.addRow(['Phase 3', overview.phase3Files]);
      chartData.addRow(['Phase 6', overview.phase6Files]);
      chartData.addRow(['Phase 7', overview.phase7Files]);

      const options = {
        title: 'Phase別ファイル数',
        colors: ['#4285F4'],
        legend: {position: 'none'}
      };

      const chart = new google.visualization.ColumnChart(
        document.getElementById('overview-chart')
      );

      chart.draw(chartData, options);
    }

    function switchTab(tabIndex) {
      // タブ切り替え
      document.querySelectorAll('.tab').forEach((tab, i) => {
        tab.classList.toggle('active', i === tabIndex);
      });

      document.querySelectorAll('.tab-content').forEach((content, i) => {
        content.classList.toggle('active', i === tabIndex);
      });

      // 遅延ロード（初回のみ）
      if (!tabDataLoaded[tabIndex] && tabIndex > 0) {
        loadTabData(tabIndex);
        tabDataLoaded[tabIndex] = true;
      }
    }

    function loadTabData(tabIndex) {
      // TODO: GAS関数を呼び出してデータ読み込み
      console.log(\`Loading data for tab \${tabIndex}\`);
    }
  </script>
</body>
</html>
  `;
}
```

#### **工数見積**: 4時間

---

## Phase 3実装詳細

### **3-1. MapMetricsヒートマップ（GAS）**

#### **目的**
MapMetrics.csv（座標付き基礎集計データ）をGoogle Maps Heatmap Layerで可視化

#### **技術スタック**
- Google Maps JavaScript API（Heatmap Layer）
- Google Maps APIキー管理（GoogleMapsAPIConfig.gs使用）
- レスポンシブデザイン

#### **詳細設計**

##### **ファイル**: `gas_files/scripts/MapMetricsHeatmap.gs`

```javascript
/**
 * MapMetricsヒートマップ可視化
 *
 * 機能:
 * - MapMetrics.csvの座標データをヒートマップ表示
 * - 申請者数の密度を色で表現
 * - ズーム・パン操作対応
 * - 凡例・統計情報表示
 */

function showMapMetricsHeatmap() {
  const ui = SpreadsheetApp.getUi();

  try {
    // MapMetricsデータ読み込み
    const mapData = loadMapMetricsData();

    if (!mapData || mapData.length === 0) {
      ui.alert(
        'データなし',
        'Phase1_MapMetricsシートにデータがありません。\n' +
        '先に「Phase 1データ取り込み」を実行してください。',
        ui.ButtonSet.OK
      );
      return;
    }

    // HTML生成
    const html = generateMapMetricsHeatmapHTML(mapData);

    const htmlOutput = HtmlService.createHtmlOutput(html)
      .setWidth(1400)
      .setHeight(900);

    ui.showModalDialog(htmlOutput, 'MapMetricsヒートマップ可視化');

  } catch (error) {
    ui.alert('エラー', `ヒートマップ生成中にエラーが発生しました:\n${error.message}`, ui.ButtonSet.OK);
    Logger.log(`MapMetricsHeatmap可視化エラー: ${error.stack}`);
  }
}

/**
 * MapMetricsデータ読み込み
 */
function loadMapMetricsData() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName('Phase1_MapMetrics');

  if (!sheet) {
    throw new Error('Phase1_MapMetricsシートが見つかりません');
  }

  const lastRow = sheet.getLastRow();
  if (lastRow <= 1) return [];

  const data = sheet.getRange(2, 1, lastRow - 1, sheet.getLastColumn()).getValues();

  return data.map(row => ({
    municipality: row[0],
    lat: parseFloat(row[1]),
    lng: parseFloat(row[2]),
    applicantCount: parseInt(row[3]),
    avgAge: parseFloat(row[4])
  })).filter(item => !isNaN(item.lat) && !isNaN(item.lng));
}

/**
 * MapMetricsヒートマップHTML生成
 */
function generateMapMetricsHeatmapHTML(mapData) {
  const mapDataJson = JSON.stringify(mapData);
  const apiKeyScript = GoogleMapsAPIConfig.generateGoogleMapsScriptTag(['visualization']);

  return `
<!DOCTYPE html>
<html>
<head>
  <base target="_top">
  ${apiKeyScript}
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: Arial, sans-serif; height: 100vh; display: flex; flex-direction: column; }

    .header {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      padding: 20px 40px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    .header h1 {
      font-size: 24px;
    }

    .controls {
      display: flex;
      gap: 15px;
    }

    .controls button {
      padding: 10px 20px;
      background: white;
      color: #667eea;
      border: none;
      border-radius: 6px;
      cursor: pointer;
      font-weight: bold;
    }

    .controls button:hover {
      background: #f0f0f0;
    }

    #map {
      flex: 1;
    }

    .legend {
      position: absolute;
      bottom: 30px;
      right: 30px;
      background: white;
      padding: 20px;
      border-radius: 8px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.3);
      z-index: 1000;
    }

    .legend h3 {
      margin-bottom: 10px;
      font-size: 14px;
      color: #333;
    }

    .gradient {
      width: 200px;
      height: 20px;
      background: linear-gradient(to right, #00ff00, #ffff00, #ff0000);
      border-radius: 4px;
      margin-bottom: 5px;
    }

    .gradient-labels {
      display: flex;
      justify-content: space-between;
      font-size: 12px;
      color: #666;
    }

    .stats {
      margin-top: 15px;
      padding-top: 15px;
      border-top: 1px solid #ddd;
      font-size: 12px;
      color: #666;
    }

    .stats div {
      margin-bottom: 5px;
    }

    .stats .value {
      font-weight: bold;
      color: #1a73e8;
    }
  </style>
</head>
<body>
  <div class="header">
    <h1>🗺️ MapMetricsヒートマップ可視化</h1>
    <div class="controls">
      <button onclick="toggleHeatmap()">ヒートマップON/OFF</button>
      <button onclick="resetView()">表示リセット</button>
    </div>
  </div>

  <div id="map"></div>

  <div class="legend">
    <h3>申請者密度</h3>
    <div class="gradient"></div>
    <div class="gradient-labels">
      <span>低</span>
      <span>中</span>
      <span>高</span>
    </div>
    <div class="stats">
      <div>総地点数: <span class="value" id="total-points">0</span></div>
      <div>総申請者: <span class="value" id="total-applicants">0</span></div>
      <div>平均年齢: <span class="value" id="avg-age">0</span>歳</div>
    </div>
  </div>

  <script>
    const mapData = ${mapDataJson};
    let map;
    let heatmap;

    function initMap() {
      // 地図の中心を日本に設定
      const centerLat = mapData.reduce((sum, item) => sum + item.lat, 0) / mapData.length;
      const centerLng = mapData.reduce((sum, item) => sum + item.lng, 0) / mapData.length;

      map = new google.maps.Map(document.getElementById('map'), {
        center: {lat: centerLat, lng: centerLng},
        zoom: 6,
        mapTypeId: 'roadmap'
      });

      // ヒートマップデータ準備
      const heatmapData = mapData.map(item => ({
        location: new google.maps.LatLng(item.lat, item.lng),
        weight: item.applicantCount
      }));

      // ヒートマップレイヤー作成
      heatmap = new google.maps.visualization.HeatmapLayer({
        data: heatmapData,
        map: map,
        radius: 30,
        opacity: 0.7,
        gradient: [
          'rgba(0, 255, 255, 0)',
          'rgba(0, 255, 255, 1)',
          'rgba(0, 191, 255, 1)',
          'rgba(0, 127, 255, 1)',
          'rgba(0, 63, 255, 1)',
          'rgba(0, 0, 255, 1)',
          'rgba(0, 0, 223, 1)',
          'rgba(0, 0, 191, 1)',
          'rgba(0, 0, 159, 1)',
          'rgba(0, 0, 127, 1)',
          'rgba(63, 0, 91, 1)',
          'rgba(127, 0, 63, 1)',
          'rgba(191, 0, 31, 1)',
          'rgba(255, 0, 0, 1)'
        ]
      });

      // 統計更新
      updateStats();
    }

    function updateStats() {
      const totalPoints = mapData.length;
      const totalApplicants = mapData.reduce((sum, item) => sum + item.applicantCount, 0);
      const avgAge = mapData.reduce((sum, item) => sum + (item.avgAge * item.applicantCount), 0) / totalApplicants;

      document.getElementById('total-points').textContent = totalPoints.toLocaleString();
      document.getElementById('total-applicants').textContent = totalApplicants.toLocaleString();
      document.getElementById('avg-age').textContent = avgAge.toFixed(1);
    }

    function toggleHeatmap() {
      if (heatmap.getMap()) {
        heatmap.setMap(null);
      } else {
        heatmap.setMap(map);
      }
    }

    function resetView() {
      const centerLat = mapData.reduce((sum, item) => sum + item.lat, 0) / mapData.length;
      const centerLng = mapData.reduce((sum, item) => sum + item.lng, 0) / mapData.length;

      map.setCenter({lat: centerLat, lng: centerLng});
      map.setZoom(6);

      if (!heatmap.getMap()) {
        heatmap.setMap(map);
      }
    }

    window.onload = function() {
      initMap();
    };
  </script>
</body>
</html>
  `;
}
```

#### **工数見積**: 3時間

---

### **3-2. 自動レポート生成（Python）**

#### **目的**
全18 CSVファイルから経営判断用のExecutiveReport.mdを自動生成

#### **技術スタック**
- pandas（データ集計）
- Markdown生成
- 自動グラフ埋め込み（Base64エンコード）

#### **詳細設計**

##### **ファイル**: `python_scripts/auto_report_generator.py`

```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
自動レポート生成エンジン

全18 CSVファイルから以下を自動生成:
1. エグゼクティブサマリー
2. Phase別分析結果
3. アクションアイテム
4. 推奨戦略
"""

import pandas as pd
from pathlib import Path
from datetime import datetime
import json


class AutoReportGenerator:
    """自動レポート生成"""

    def __init__(self, output_dir: str = 'gas_output_insights'):
        """
        初期化

        Args:
            output_dir: レポート出力ディレクトリ
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        self.report_sections = []
        self.action_items = []

    def load_all_data(self):
        """全CSVデータ読み込み"""
        print("\n[データ読み込み] 全18 CSVファイル読み込み中...")

        self.data = {
            # Phase 1
            'MapMetrics': self._safe_read_csv('gas_output_phase1/MapMetrics.csv'),
            'Applicants': self._safe_read_csv('gas_output_phase1/Applicants.csv'),
            'DesiredWork': self._safe_read_csv('gas_output_phase1/DesiredWork.csv'),
            'AggDesired': self._safe_read_csv('gas_output_phase1/AggDesired.csv'),

            # Phase 2
            'ChiSquareTests': self._safe_read_csv('gas_output_phase2/ChiSquareTests.csv'),
            'ANOVATests': self._safe_read_csv('gas_output_phase2/ANOVATests.csv'),

            # Phase 3
            'PersonaSummary': self._safe_read_csv('gas_output_phase3/PersonaSummary.csv'),
            'PersonaDetails': self._safe_read_csv('gas_output_phase3/PersonaDetails.csv'),

            # Phase 6
            'MunicipalityFlowEdges': self._safe_read_csv('gas_output_phase6/MunicipalityFlowEdges.csv'),
            'MunicipalityFlowNodes': self._safe_read_csv('gas_output_phase6/MunicipalityFlowNodes.csv'),
            'ProximityAnalysis': self._safe_read_csv('gas_output_phase6/ProximityAnalysis.csv'),

            # Phase 7
            'PersonaMapData': self._safe_read_csv('gas_output_phase7/PersonaMapData.csv'),
            'PersonaMobilityCross': self._safe_read_csv('gas_output_phase7/PersonaMobilityCross.csv'),
            'PersonaQualificationCross': self._safe_read_csv('gas_output_phase7/PersonaQualificationCross.csv'),
            'TopDestinations': self._safe_read_csv('gas_output_phase7/TopDestinations.csv'),
            'SegmentComparison': self._safe_read_csv('gas_output_phase7/SegmentComparison.csv'),
            'MobilityRankDistribution': self._safe_read_csv('gas_output_phase7/MobilityRankDistribution.csv'),
            'QualificationRateSegments': self._safe_read_csv('gas_output_phase7/QualificationRateSegments.csv')
        }

        print(f"  [OK] {len([v for v in self.data.values() if v is not None])} / 18 ファイル読み込み成功")

    def _safe_read_csv(self, path: str):
        """安全なCSV読み込み"""
        try:
            return pd.read_csv(path, encoding='utf-8-sig')
        except FileNotFoundError:
            print(f"  [SKIP] {path} が見つかりません")
            return None

    def generate_executive_summary(self):
        """エグゼクティブサマリー生成"""
        print("\n[セクション1] エグゼクティブサマリー生成中...")

        # 総申請者数
        total_applicants = len(self.data['Applicants']) if self.data['Applicants'] is not None else 0

        # 総自治体数
        total_municipalities = len(self.data['MapMetrics']) if self.data['MapMetrics'] is not None else 0

        # ペルソナ数
        total_personas = len(self.data['PersonaSummary']) if self.data['PersonaSummary'] is not None else 0

        # フローエッジ数
        total_flow_edges = len(self.data['MunicipalityFlowEdges']) if self.data['MunicipalityFlowEdges'] is not None else 0

        summary = f"""
# 求職者データ分析レポート

**生成日時**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## エグゼクティブサマリー

### 📊 データ概要

- **総申請者数**: {total_applicants:,}名
- **総自治体数**: {total_municipalities}箇所
- **ペルソナセグメント数**: {total_personas}個
- **人材移動フローエッジ数**: {total_flow_edges:,}本

### 🎯 主要な発見

"""

        # PersonaSummaryから上位3ペルソナを抽出
        if self.data['PersonaSummary'] is not None:
            top3_personas = self.data['PersonaSummary'].nlargest(3, self.data['PersonaSummary'].columns[1])

            summary += "#### TOP 3 ペルソナ（申請者数）\n\n"
            for i, row in enumerate(top3_personas.itertuples(), 1):
                persona_name = row[1]
                persona_count = row[2]
                summary += f"{i}. **{persona_name}**: {persona_count:,}名\n"

        summary += "\n"

        self.report_sections.append(summary)
        print("  [OK] エグゼクティブサマリー生成完了")

    def generate_persona_insights(self):
        """ペルソナ分析インサイト生成"""
        print("\n[セクション2] ペルソナ分析インサイト生成中...")

        if self.data['PersonaMobilityCross'] is None:
            print("  [SKIP] PersonaMobilityCross.csv がありません")
            return

        section = "\n---\n\n## ペルソナ別移動性分析\n\n"

        df = self.data['PersonaMobilityCross']

        # A/Bランク（広域志向）が多いペルソナ
        df['high_mobility'] = df.iloc[:, 2] + df.iloc[:, 3]  # A% + B%
        top_mobile_personas = df.nlargest(3, 'high_mobility')

        section += "### 広域志向ペルソナ（TOP 3）\n\n"
        section += "| ペルソナ | A+Bランク割合 | アクション |\n"
        section += "|---------|--------------|----------|\n"

        for row in top_mobile_personas.itertuples():
            persona_name = row[1]
            high_mobility_rate = row[-1]
            section += f"| {persona_name} | {high_mobility_rate:.1f}% | 全国エリアでの求人露出を強化 |\n"

        # D/Eランク（地元志向）が多いペルソナ
        df['low_mobility'] = df.iloc[:, 5] + df.iloc[:, 6]  # D% + E%
        top_local_personas = df.nlargest(3, 'low_mobility')

        section += "\n### 地元志向ペルソナ（TOP 3）\n\n"
        section += "| ペルソナ | D+Eランク割合 | アクション |\n"
        section += "|---------|--------------|----------|\n"

        for row in top_local_personas.itertuples():
            persona_name = row[1]
            low_mobility_rate = row[-1]
            section += f"| {persona_name} | {low_mobility_rate:.1f}% | 地元密着型求人で訴求 |\n"

        self.report_sections.append(section)
        print("  [OK] ペルソナ分析インサイト生成完了")

    def generate_flow_insights(self):
        """フロー分析インサイト生成"""
        print("\n[セクション3] フロー分析インサイト生成中...")

        if self.data['MunicipalityFlowEdges'] is None:
            print("  [SKIP] MunicipalityFlowEdges.csv がありません")
            return

        section = "\n---\n\n## 人材移動フロー分析\n\n"

        df = self.data['MunicipalityFlowEdges']

        # TOP 5 人材移動フロー
        top5_flows = df.nlargest(5, df.columns[2])

        section += "### TOP 5 人材移動フロー\n\n"
        section += "| 順位 | 居住地 → 希望勤務地 | 人数 | 平均距離（km） |\n"
        section += "|-----|-------------------|------|---------------|\n"

        for i, row in enumerate(top5_flows.itertuples(), 1):
            from_node = row[1]
            to_node = row[2]
            count = row[3]
            avg_distance = row[4] if len(row) > 4 else 0
            section += f"| {i} | {from_node} → {to_node} | {count:,}名 | {avg_distance:.1f} km |\n"

        self.report_sections.append(section)
        print("  [OK] フロー分析インサイト生成完了")

    def generate_action_items(self):
        """アクションアイテム生成"""
        print("\n[セクション4] アクションアイテム生成中...")

        section = "\n---\n\n## 推奨アクションアイテム\n\n"

        section += "### 🎯 短期施策（1-3ヶ月）\n\n"
        section += "1. **広域志向ペルソナへの全国求人露出強化**\n"
        section += "   - PersonaMobilityCross.csvでA+Bランク≥30%のペルソナを特定\n"
        section += "   - 該当ペルソナに全国エリアの求人を優先表示\n\n"

        section += "2. **地元志向ペルソナへの地域密着型求人訴求**\n"
        section += "   - PersonaMobilityCross.csvでD+Eランク≥80%のペルソナを特定\n"
        section += "   - 「通勤時間15分以内」「地元で働く」をキーワードに訴求\n\n"

        section += "3. **TOP 5人材移動フローへの求人集中投下**\n"
        section += "   - MunicipalityFlowEdges.csvのTOP 5エッジを特定\n"
        section += "   - 該当エリアの求人数を20%増強\n\n"

        section += "### 🚀 中長期施策（3-6ヶ月）\n\n"
        section += "1. **3次元クロス分析によるターゲティング精度向上**\n"
        section += "   - Persona × Mobility × Qualification のクロス分析実施\n"
        section += "   - セグメント別最適化戦略の策定\n\n"

        section += "2. **ネットワーク中心性分析によるハブ自治体特定**\n"
        section += "   - networkxでDegree/Betweenness/PageRank計算\n"
        section += "   - ハブ自治体への求人投資を優先\n\n"

        self.report_sections.append(section)
        print("  [OK] アクションアイテム生成完了")

    def export_to_markdown(self, output_path: str = None):
        """Markdown出力"""
        if output_path is None:
            output_path = self.output_dir / f"ExecutiveReport_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        else:
            output_path = Path(output_path)

        full_report = "\n".join(self.report_sections)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(full_report)

        print(f"\n[出力] {output_path}")

    def run_all(self):
        """全セクション生成 & 出力"""
        print("\n" + "=" * 60)
        print("自動レポート生成エンジン")
        print("=" * 60)

        self.load_all_data()
        self.generate_executive_summary()
        self.generate_persona_insights()
        self.generate_flow_insights()
        self.generate_action_items()
        self.export_to_markdown()

        print("\n" + "=" * 60)
        print("レポート生成完了")
        print("=" * 60)


if __name__ == '__main__':
    generator = AutoReportGenerator()
    generator.run_all()
```

#### **工数見積**: 3時間

---

### **3-3. DesiredWork詳細検索UI（GAS）**

#### **目的**
DesiredWork.csv（1.3MB、大規模データ）をインタラクティブに検索・フィルター

#### **技術スタック**
- GAS HTMLService
- クライアントサイドフィルタリング（パフォーマンス対策）
- ページネーション（100件/ページ）

#### **詳細設計**

##### **ファイル**: `gas_files/scripts/DesiredWorkSearchUI.gs`

```javascript
/**
 * DesiredWork詳細検索UI
 *
 * 機能:
 * - DesiredWork.csvの全データをインタラクティブ検索
 * - フィルター: 都道府県、市区町村、年齢範囲、性別、資格有無
 * - ページネーション（100件/ページ）
 * - CSVエクスポート機能
 */

function showDesiredWorkSearchUI() {
  const ui = SpreadsheetApp.getUi();

  try {
    // DesiredWorkデータ読み込み（サンプリング or 全件）
    const desiredWorkData = loadDesiredWorkDataSampled(5000);  // 最大5000件

    if (!desiredWorkData || desiredWorkData.length === 0) {
      ui.alert(
        'データなし',
        'Phase1_DesiredWorkシートにデータがありません。',
        ui.ButtonSet.OK
      );
      return;
    }

    // HTML生成
    const html = generateDesiredWorkSearchHTML(desiredWorkData);

    const htmlOutput = HtmlService.createHtmlOutput(html)
      .setWidth(1600)
      .setHeight(1000);

    ui.showModalDialog(htmlOutput, 'DesiredWork詳細検索');

  } catch (error) {
    ui.alert('エラー', `検索UI生成中にエラーが発生しました:\n${error.message}`, ui.ButtonSet.OK);
    Logger.log(`DesiredWorkSearchUI生成エラー: ${error.stack}`);
  }
}

/**
 * DesiredWorkデータ読み込み（サンプリング版）
 */
function loadDesiredWorkDataSampled(maxRows) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName('Phase1_DesiredWork');

  if (!sheet) {
    throw new Error('Phase1_DesiredWorkシートが見つかりません');
  }

  const lastRow = sheet.getLastRow();
  if (lastRow <= 1) return [];

  const rowsToRead = Math.min(lastRow - 1, maxRows);
  const data = sheet.getRange(2, 1, rowsToRead, sheet.getLastColumn()).getValues();

  return data.map(row => ({
    applicantId: row[0],
    prefecture: row[1],
    municipality: row[2],
    age: parseInt(row[3]),
    gender: row[4],
    hasQualification: row[5]
  }));
}

/**
 * DesiredWork検索HTML生成
 */
function generateDesiredWorkSearchHTML(data) {
  const dataJson = JSON.stringify(data);

  // ユニーク都道府県リスト
  const uniquePrefectures = [...new Set(data.map(item => item.prefecture))].sort();
  const prefectureOptions = uniquePrefectures.map(p => `<option value="${p}">${p}</option>`).join('');

  return `
<!DOCTYPE html>
<html>
<head>
  <base target="_top">
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: Arial, sans-serif; background: #f5f5f5; }

    .header {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      padding: 30px;
      text-align: center;
    }

    .header h1 {
      font-size: 28px;
      margin-bottom: 10px;
    }

    .filters {
      background: white;
      padding: 30px;
      margin: 20px;
      border-radius: 12px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }

    .filter-grid {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 20px;
      margin-bottom: 20px;
    }

    .filter-item label {
      display: block;
      font-weight: bold;
      margin-bottom: 8px;
      color: #333;
    }

    .filter-item select,
    .filter-item input {
      width: 100%;
      padding: 10px;
      border: 1px solid #ddd;
      border-radius: 6px;
    }

    .filter-actions {
      display: flex;
      gap: 15px;
      justify-content: flex-end;
    }

    .filter-actions button {
      padding: 12px 30px;
      border: none;
      border-radius: 6px;
      cursor: pointer;
      font-weight: bold;
    }

    .btn-primary {
      background: #1a73e8;
      color: white;
    }

    .btn-secondary {
      background: #e8e8e8;
      color: #333;
    }

    .results {
      background: white;
      margin: 20px;
      border-radius: 12px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.1);
      overflow: hidden;
    }

    .results-header {
      padding: 20px 30px;
      border-bottom: 1px solid #ddd;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    .results-header h2 {
      font-size: 18px;
      color: #333;
    }

    .results-count {
      font-size: 14px;
      color: #666;
    }

    table {
      width: 100%;
      border-collapse: collapse;
    }

    th {
      background: #f5f5f5;
      padding: 15px;
      text-align: left;
      font-weight: bold;
      border-bottom: 2px solid #ddd;
    }

    td {
      padding: 15px;
      border-bottom: 1px solid #eee;
    }

    tr:hover {
      background: #f9f9f9;
    }

    .pagination {
      padding: 20px 30px;
      display: flex;
      justify-content: center;
      gap: 10px;
    }

    .pagination button {
      padding: 8px 16px;
      border: 1px solid #ddd;
      background: white;
      border-radius: 4px;
      cursor: pointer;
    }

    .pagination button:hover {
      background: #f5f5f5;
    }

    .pagination button.active {
      background: #1a73e8;
      color: white;
      border-color: #1a73e8;
    }

    .pagination button:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }
  </style>
</head>
<body>
  <div class="header">
    <h1>🔍 DesiredWork詳細検索</h1>
    <p>Phase 1データ | 希望勤務地データのインタラクティブ検索</p>
  </div>

  <div class="filters">
    <div class="filter-grid">
      <div class="filter-item">
        <label>都道府県</label>
        <select id="filter-prefecture">
          <option value="">全て</option>
          ${prefectureOptions}
        </select>
      </div>

      <div class="filter-item">
        <label>市区町村</label>
        <input type="text" id="filter-municipality" placeholder="部分一致検索">
      </div>

      <div class="filter-item">
        <label>年齢範囲</label>
        <div style="display: flex; gap: 10px;">
          <input type="number" id="filter-age-min" placeholder="最小" min="18" max="100">
          <input type="number" id="filter-age-max" placeholder="最大" min="18" max="100">
        </div>
      </div>

      <div class="filter-item">
        <label>性別</label>
        <select id="filter-gender">
          <option value="">全て</option>
          <option value="男性">男性</option>
          <option value="女性">女性</option>
        </select>
      </div>

      <div class="filter-item">
        <label>資格</label>
        <select id="filter-qualification">
          <option value="">全て</option>
          <option value="有">有</option>
          <option value="無">無</option>
        </select>
      </div>
    </div>

    <div class="filter-actions">
      <button class="btn-secondary" onclick="resetFilters()">リセット</button>
      <button class="btn-primary" onclick="applyFilters()">検索</button>
    </div>
  </div>

  <div class="results">
    <div class="results-header">
      <h2>検索結果</h2>
      <span class="results-count" id="results-count">0件</span>
    </div>

    <table>
      <thead>
        <tr>
          <th>申請者ID</th>
          <th>都道府県</th>
          <th>市区町村</th>
          <th>年齢</th>
          <th>性別</th>
          <th>資格</th>
        </tr>
      </thead>
      <tbody id="results-tbody">
      </tbody>
    </table>

    <div class="pagination" id="pagination">
    </div>
  </div>

  <script>
    const allData = ${dataJson};
    let filteredData = allData;
    let currentPage = 1;
    const rowsPerPage = 100;

    function applyFilters() {
      const prefecture = document.getElementById('filter-prefecture').value;
      const municipality = document.getElementById('filter-municipality').value.toLowerCase();
      const ageMin = parseInt(document.getElementById('filter-age-min').value) || 0;
      const ageMax = parseInt(document.getElementById('filter-age-max').value) || 999;
      const gender = document.getElementById('filter-gender').value;
      const qualification = document.getElementById('filter-qualification').value;

      filteredData = allData.filter(item => {
        if (prefecture && item.prefecture !== prefecture) return false;
        if (municipality && !item.municipality.toLowerCase().includes(municipality)) return false;
        if (item.age < ageMin || item.age > ageMax) return false;
        if (gender && item.gender !== gender) return false;
        if (qualification && item.hasQualification !== qualification) return false;
        return true;
      });

      currentPage = 1;
      renderResults();
    }

    function resetFilters() {
      document.getElementById('filter-prefecture').value = '';
      document.getElementById('filter-municipality').value = '';
      document.getElementById('filter-age-min').value = '';
      document.getElementById('filter-age-max').value = '';
      document.getElementById('filter-gender').value = '';
      document.getElementById('filter-qualification').value = '';

      filteredData = allData;
      currentPage = 1;
      renderResults();
    }

    function renderResults() {
      const startIndex = (currentPage - 1) * rowsPerPage;
      const endIndex = startIndex + rowsPerPage;
      const pageData = filteredData.slice(startIndex, endIndex);

      const tbody = document.getElementById('results-tbody');
      tbody.innerHTML = '';

      pageData.forEach(item => {
        const row = tbody.insertRow();
        row.insertCell(0).textContent = item.applicantId;
        row.insertCell(1).textContent = item.prefecture;
        row.insertCell(2).textContent = item.municipality;
        row.insertCell(3).textContent = item.age;
        row.insertCell(4).textContent = item.gender;
        row.insertCell(5).textContent = item.hasQualification;
      });

      document.getElementById('results-count').textContent = \`\${filteredData.length.toLocaleString()}件\`;

      renderPagination();
    }

    function renderPagination() {
      const totalPages = Math.ceil(filteredData.length / rowsPerPage);
      const pagination = document.getElementById('pagination');
      pagination.innerHTML = '';

      // 前へボタン
      const prevBtn = document.createElement('button');
      prevBtn.textContent = '前へ';
      prevBtn.disabled = currentPage === 1;
      prevBtn.onclick = () => {
        if (currentPage > 1) {
          currentPage--;
          renderResults();
        }
      };
      pagination.appendChild(prevBtn);

      // ページ番号
      const maxButtons = 10;
      let startPage = Math.max(1, currentPage - Math.floor(maxButtons / 2));
      let endPage = Math.min(totalPages, startPage + maxButtons - 1);

      if (endPage - startPage < maxButtons - 1) {
        startPage = Math.max(1, endPage - maxButtons + 1);
      }

      for (let i = startPage; i <= endPage; i++) {
        const pageBtn = document.createElement('button');
        pageBtn.textContent = i;
        pageBtn.className = i === currentPage ? 'active' : '';
        pageBtn.onclick = () => {
          currentPage = i;
          renderResults();
        };
        pagination.appendChild(pageBtn);
      }

      // 次へボタン
      const nextBtn = document.createElement('button');
      nextBtn.textContent = '次へ';
      nextBtn.disabled = currentPage === totalPages;
      nextBtn.onclick = () => {
        if (currentPage < totalPages) {
          currentPage++;
          renderResults();
        }
      };
      pagination.appendChild(nextBtn);
    }

    // 初期表示
    renderResults();
  </script>
</body>
</html>
  `;
}
```

#### **工数見積**: 4時間

---

## Phase 2-3 総工数見積

### Phase 2（10時間）
- 2-1. MunicipalityFlowネットワーク図（GAS）: 4時間
- 2-2. ネットワーク中心性分析（Python）: 2時間
- 2-3. 全Phase統合ダッシュボード（GAS）: 4時間

### Phase 3（10時間）
- 3-1. MapMetricsヒートマップ（GAS）: 3時間
- 3-2. 自動レポート生成（Python）: 3時間
- 3-3. DesiredWork詳細検索UI（GAS）: 4時間

### 合計: 20時間

---

## 次のステップ

1. **Phase 1実装完了後**:
   - ユーザーフィードバック収集
   - Phase 1機能のE2Eテスト実施

2. **Phase 2実装開始**:
   - MunicipalityFlowネットワーク図から実装
   - ネットワーク中心性分析を並行実施

3. **Phase 3実装開始**:
   - MapMetricsヒートマップ実装
   - 自動レポート生成エンジン実装

4. **最終統合**:
   - 全Phase統合ダッシュボードで全機能を統合
   - E2Eテスト・デプロイ
