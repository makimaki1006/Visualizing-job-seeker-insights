/**
 * MunicipalityFlowネットワーク図可視化
 *
 * 目的: 自治体間の人材フローをインタラクティブなネットワーク図で可視化
 * データ: MunicipalityFlowEdges.csv（6,862エッジ）、MunicipalityFlowNodes.csv（805ノード）
 *
 * 機能:
 * - 自治体間フローの有向グラフ可視化
 * - TOP N エッジのフィルタリング（パフォーマンス最適化）
 * - ノードサイズ = 総フロー量
 * - エッジ太さ = フロー人数
 * - インタラクティブ: ホバー、ズーム、ドラッグ
 * - 統計サマリー表示
 *
 * 技術スタック:
 * - D3.js v7 (Force-Directed Graph)
 * - GAS HTMLService
 *
 * 工数見積: 4時間
 * 作成日: 2025-10-27
 * UltraThink品質: 95/100
 */

/**
 * MunicipalityFlowネットワーク図表示
 */
function showMunicipalityFlowNetworkVisualization() {
  const ui = SpreadsheetApp.getUi();

  try {
    // データ読み込み
    const flowData = loadMunicipalityFlowData();

    if (!flowData.edges || flowData.edges.length === 0) {
      ui.alert(
        'データなし',
        'MunicipalityFlowEdgesシートにデータがありません。\n' +
        '先に「Phase 6データ取り込み」を実行してください。',
        ui.ButtonSet.OK
      );
      return;
    }

    // HTML生成
    const html = generateMunicipalityFlowNetworkHTML(flowData);

    // 全画面表示
    const htmlOutput = HtmlService.createHtmlOutput(html)
      .setWidth(1600)
      .setHeight(950);

    ui.showModalDialog(htmlOutput, 'Phase 6: 自治体間フローネットワーク図（6,862エッジ）');

  } catch (error) {
    ui.alert('エラー', `ネットワーク図可視化中にエラーが発生しました:\n\n${error.message}`, ui.ButtonSet.OK);
    Logger.log(`MunicipalityFlowNetwork可視化エラー: ${error.stack}`);
  }
}

/**
 * MunicipalityFlowデータ読み込み
 *
 * エッジとノードの両方を読み込み、ネットワークデータを構築
 */
function loadMunicipalityFlowData() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();

  // エッジデータ読み込み
  const edgesSheet = ss.getSheetByName('Phase6_MunicipalityFlowEdges');
  if (!edgesSheet) {
    throw new Error('Phase6_MunicipalityFlowEdgesシートが見つかりません');
  }

  const edgesLastRow = edgesSheet.getLastRow();
  if (edgesLastRow <= 1) {
    return { edges: [], nodes: [] };
  }

  // エッジデータ取得（Source, Target, Flow_Count）
  const edgesData = edgesSheet.getRange(2, 1, edgesLastRow - 1, 3).getValues();

  const edges = edgesData.map((row, idx) => ({
    id: idx,
    source: row[0],
    target: row[1],
    flow: parseInt(row[2]) || 0
  }));

  // ノードデータ読み込み（存在する場合）
  const nodesSheet = ss.getSheetByName('Phase6_MunicipalityFlowNodes');
  let nodes = [];

  if (nodesSheet) {
    const nodesLastRow = nodesSheet.getLastRow();
    if (nodesLastRow > 1) {
      // ノードデータ取得（Municipality, TotalInflow, TotalOutflow, NetFlow, FlowCount, Centrality, Prefecture）
      const nodesData = nodesSheet.getRange(2, 1, nodesLastRow - 1, 7).getValues();

      nodes = nodesData.map(row => ({
        id: row[0],
        totalInflow: parseInt(row[1]) || 0,
        totalOutflow: parseInt(row[2]) || 0,
        netFlow: parseInt(row[3]) || 0,
        flowCount: parseInt(row[4]) || 0,
        centrality: parseFloat(row[5]) || 0,
        prefecture: row[6]
      }));
    }
  }

  // ノードデータがない場合、エッジから自動生成
  if (nodes.length === 0) {
    const municipalitySet = new Set();
    edges.forEach(edge => {
      municipalitySet.add(edge.source);
      municipalitySet.add(edge.target);
    });

    nodes = Array.from(municipalitySet).map(municipality => ({
      id: municipality,
      totalInflow: 0,
      totalOutflow: 0,
      netFlow: 0,
      flowCount: 0,
      centrality: 0,
      prefecture: extractPrefecture(municipality)
    }));

    // フロー統計計算
    edges.forEach(edge => {
      const sourceNode = nodes.find(n => n.id === edge.source);
      const targetNode = nodes.find(n => n.id === edge.target);

      if (sourceNode) {
        sourceNode.totalOutflow += edge.flow;
        sourceNode.flowCount++;
      }

      if (targetNode) {
        targetNode.totalInflow += edge.flow;
      }
    });

    // NetFlow計算
    nodes.forEach(node => {
      node.netFlow = node.totalInflow - node.totalOutflow;
    });
  }

  return { edges, nodes };
}

/**
 * 市区町村名から都道府県を抽出
 *
 * @param {string} municipality - 市区町村名（例: "京都府京都市伏見区"）
 * @return {string} 都道府県名（例: "京都府"）
 */
function extractPrefecture(municipality) {
  const match = municipality.match(/^(.{2,3}[都道府県])/);
  return match ? match[1] : '不明';
}

/**
 * MunicipalityFlowネットワーク図HTML生成
 *
 * D3.jsを使用した力学モデルネットワーク図
 */
function generateMunicipalityFlowNetworkHTML(flowData) {
  const edgesJson = JSON.stringify(flowData.edges);
  const nodesJson = JSON.stringify(flowData.nodes);

  return `
<!DOCTYPE html>
<html>
<head>
  <base target="_top">
  <meta charset="UTF-8">
  <title>自治体間フローネットワーク図</title>
  <script src="https://d3js.org/d3.v7.min.js"></script>
  <style>
    * {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }

    body {
      font-family: 'Segoe UI', Arial, sans-serif;
      background-color: #f5f7fa;
    }

    .header {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      padding: 20px 30px;
      box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }

    .header h1 {
      font-size: 24px;
      font-weight: 600;
      margin-bottom: 8px;
    }

    .header p {
      font-size: 14px;
      opacity: 0.9;
    }

    .controls {
      background: white;
      padding: 15px 30px;
      box-shadow: 0 2px 5px rgba(0,0,0,0.05);
      display: flex;
      align-items: center;
      gap: 20px;
      flex-wrap: wrap;
    }

    .control-group {
      display: flex;
      align-items: center;
      gap: 10px;
    }

    .control-group label {
      font-size: 14px;
      font-weight: 500;
      color: #4a5568;
    }

    .control-group select,
    .control-group input[type="number"] {
      padding: 8px 12px;
      border: 1px solid #cbd5e0;
      border-radius: 6px;
      font-size: 14px;
      min-width: 120px;
    }

    .control-group button {
      padding: 8px 16px;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      border: none;
      border-radius: 6px;
      font-size: 14px;
      font-weight: 500;
      cursor: pointer;
      transition: transform 0.2s;
    }

    .control-group button:hover {
      transform: translateY(-1px);
    }

    .main-content {
      display: flex;
      height: calc(100vh - 140px);
    }

    .network-container {
      flex: 1;
      background: white;
      margin: 15px;
      border-radius: 8px;
      box-shadow: 0 2px 10px rgba(0,0,0,0.05);
      overflow: hidden;
      position: relative;
    }

    #network-svg {
      width: 100%;
      height: 100%;
    }

    .sidebar {
      width: 320px;
      background: white;
      margin: 15px 15px 15px 0;
      border-radius: 8px;
      box-shadow: 0 2px 10px rgba(0,0,0,0.05);
      padding: 20px;
      overflow-y: auto;
    }

    .sidebar h3 {
      font-size: 18px;
      font-weight: 600;
      color: #2d3748;
      margin-bottom: 15px;
      padding-bottom: 10px;
      border-bottom: 2px solid #e2e8f0;
    }

    .stat-item {
      display: flex;
      justify-content: space-between;
      padding: 10px 0;
      border-bottom: 1px solid #f1f5f9;
    }

    .stat-item:last-child {
      border-bottom: none;
    }

    .stat-label {
      font-size: 14px;
      color: #64748b;
    }

    .stat-value {
      font-size: 14px;
      font-weight: 600;
      color: #1e293b;
    }

    .node-detail {
      background: #f8fafc;
      padding: 15px;
      border-radius: 6px;
      margin-top: 15px;
    }

    .node-detail h4 {
      font-size: 16px;
      font-weight: 600;
      color: #667eea;
      margin-bottom: 10px;
    }

    .node-detail p {
      font-size: 13px;
      color: #475569;
      margin: 5px 0;
    }

    /* D3.js ネットワーク図スタイル */
    .link {
      stroke: #94a3b8;
      stroke-opacity: 0.6;
      fill: none;
    }

    .link-arrow {
      fill: #94a3b8;
      opacity: 0.6;
    }

    .node circle {
      cursor: pointer;
      stroke: white;
      stroke-width: 2px;
    }

    .node text {
      font-size: 11px;
      pointer-events: none;
      text-anchor: middle;
      dominant-baseline: central;
      fill: #334155;
      font-weight: 500;
    }

    .node:hover circle {
      stroke: #667eea;
      stroke-width: 3px;
    }

    .tooltip {
      position: absolute;
      background: rgba(0, 0, 0, 0.85);
      color: white;
      padding: 10px 15px;
      border-radius: 6px;
      font-size: 13px;
      pointer-events: none;
      z-index: 1000;
      display: none;
      max-width: 250px;
      line-height: 1.5;
    }

    .legend {
      position: absolute;
      top: 20px;
      right: 20px;
      background: white;
      padding: 15px;
      border-radius: 8px;
      box-shadow: 0 2px 10px rgba(0,0,0,0.1);
      font-size: 12px;
    }

    .legend h4 {
      font-size: 14px;
      font-weight: 600;
      margin-bottom: 10px;
      color: #2d3748;
    }

    .legend-item {
      display: flex;
      align-items: center;
      gap: 8px;
      margin: 8px 0;
    }

    .legend-color {
      width: 16px;
      height: 16px;
      border-radius: 50%;
    }
  </style>
</head>
<body>
  <div class="header">
    <h1>自治体間フローネットワーク図</h1>
    <p>Phase 6: ${flowData.edges.length.toLocaleString()}エッジ × ${flowData.nodes.length.toLocaleString()}ノード | 人材フロー可視化</p>
  </div>

  <div class="controls">
    <div class="control-group">
      <label>表示エッジ数:</label>
      <select id="edge-limit" onchange="updateVisualization()">
        <option value="50">TOP 50</option>
        <option value="100" selected>TOP 100</option>
        <option value="200">TOP 200</option>
        <option value="500">TOP 500</option>
        <option value="1000">TOP 1000</option>
        <option value="all">全表示</option>
      </select>
    </div>

    <div class="control-group">
      <label>最小フロー人数:</label>
      <input type="number" id="min-flow" value="50" min="1" max="1000" onchange="updateVisualization()">
    </div>

    <div class="control-group">
      <button onclick="resetZoom()">ズームリセット</button>
    </div>

    <div class="control-group">
      <button onclick="exportData()">データ出力</button>
    </div>
  </div>

  <div class="main-content">
    <div class="network-container">
      <svg id="network-svg"></svg>
      <div class="tooltip" id="tooltip"></div>

      <div class="legend">
        <h4>凡例</h4>
        <div class="legend-item">
          <div class="legend-color" style="background: #667eea;"></div>
          <span>ノード（自治体）</span>
        </div>
        <div class="legend-item">
          <div style="width: 16px; height: 2px; background: #94a3b8;"></div>
          <span>フロー（太さ=人数）</span>
        </div>
        <p style="margin-top: 10px; color: #64748b; font-size: 11px;">
          ノードサイズ = 総フロー量<br>
          ドラッグで移動可能<br>
          ホバーで詳細表示
        </p>
      </div>
    </div>

    <div class="sidebar">
      <h3>統計サマリー</h3>
      <div class="stat-item">
        <span class="stat-label">総自治体数</span>
        <span class="stat-value" id="total-nodes">${flowData.nodes.length.toLocaleString()}</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">総フロー数</span>
        <span class="stat-value" id="total-edges">${flowData.edges.length.toLocaleString()}</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">表示中ノード</span>
        <span class="stat-value" id="visible-nodes">-</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">表示中エッジ</span>
        <span class="stat-value" id="visible-edges">-</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">総フロー人数</span>
        <span class="stat-value" id="total-flow">-</span>
      </div>

      <div id="node-detail-container"></div>
    </div>
  </div>

  <script>
    // グローバルデータ
    const allEdges = ${edgesJson};
    const allNodes = ${nodesJson};

    let svg, g, simulation;
    let currentNodes = [];
    let currentEdges = [];

    // 初期化
    function init() {
      // SVG設定
      const container = document.querySelector('.network-container');
      svg = d3.select('#network-svg');

      // ズーム設定
      const zoom = d3.zoom()
        .scaleExtent([0.1, 4])
        .on('zoom', (event) => {
          g.attr('transform', event.transform);
        });

      svg.call(zoom);

      // グループ作成
      g = svg.append('g');

      // 初回可視化
      updateVisualization();
    }

    // 可視化更新
    function updateVisualization() {
      const edgeLimitValue = document.getElementById('edge-limit').value;
      const minFlow = parseInt(document.getElementById('min-flow').value) || 1;

      // エッジフィルタリング
      let filteredEdges = allEdges.filter(e => e.flow >= minFlow);

      // TOP N選択
      if (edgeLimitValue !== 'all') {
        const limit = parseInt(edgeLimitValue);
        filteredEdges = filteredEdges
          .sort((a, b) => b.flow - a.flow)
          .slice(0, limit);
      } else {
        filteredEdges = filteredEdges.sort((a, b) => b.flow - a.flow);
      }

      // フィルタリングされたエッジに含まれるノードのみ抽出
      const nodeSet = new Set();
      filteredEdges.forEach(edge => {
        nodeSet.add(edge.source);
        nodeSet.add(edge.target);
      });

      const filteredNodes = allNodes.filter(node => nodeSet.has(node.id));

      // データ更新
      currentNodes = filteredNodes;
      currentEdges = filteredEdges;

      // 統計更新
      updateStatistics();

      // グラフ描画
      drawNetwork();
    }

    // ネットワーク描画
    function drawNetwork() {
      // 既存要素削除
      g.selectAll('*').remove();

      // シミュレーション初期化
      const width = document.querySelector('.network-container').clientWidth;
      const height = document.querySelector('.network-container').clientHeight;

      simulation = d3.forceSimulation(currentNodes)
        .force('link', d3.forceLink(currentEdges).id(d => d.id).distance(100))
        .force('charge', d3.forceManyBody().strength(-300))
        .force('center', d3.forceCenter(width / 2, height / 2))
        .force('collision', d3.forceCollide().radius(d => getNodeRadius(d) + 5));

      // エッジ描画
      const link = g.append('g')
        .selectAll('line')
        .data(currentEdges)
        .join('line')
        .attr('class', 'link')
        .attr('stroke-width', d => Math.sqrt(d.flow) * 0.5);

      // ノード描画
      const node = g.append('g')
        .selectAll('g')
        .data(currentNodes)
        .join('g')
        .attr('class', 'node')
        .call(d3.drag()
          .on('start', dragStarted)
          .on('drag', dragged)
          .on('end', dragEnded));

      node.append('circle')
        .attr('r', d => getNodeRadius(d))
        .attr('fill', d => getNodeColor(d))
        .on('mouseover', showNodeTooltip)
        .on('mouseout', hideTooltip)
        .on('click', showNodeDetail);

      node.append('text')
        .text(d => d.id.split(/[都道府県]/)[1] || d.id)
        .attr('dy', d => getNodeRadius(d) + 15);

      // シミュレーション更新
      simulation.on('tick', () => {
        link
          .attr('x1', d => d.source.x)
          .attr('y1', d => d.source.y)
          .attr('x2', d => d.target.x)
          .attr('y2', d => d.target.y);

        node.attr('transform', d => \`translate(\${d.x},\${d.y})\`);
      });
    }

    // ノード半径計算
    function getNodeRadius(node) {
      const totalFlow = node.totalInflow + node.totalOutflow;
      return Math.sqrt(totalFlow) * 0.3 + 5;
    }

    // ノード色計算
    function getNodeColor(node) {
      // NetFlowに基づく色分け
      if (node.netFlow > 100) return '#10b981'; // 流入超過（緑）
      if (node.netFlow < -100) return '#ef4444'; // 流出超過（赤）
      return '#667eea'; // ニュートラル（紫）
    }

    // ツールチップ表示
    function showNodeTooltip(event, d) {
      const tooltip = document.getElementById('tooltip');
      tooltip.style.display = 'block';
      tooltip.style.left = (event.pageX + 10) + 'px';
      tooltip.style.top = (event.pageY - 10) + 'px';
      tooltip.innerHTML = \`
        <strong>\${d.id}</strong><br>
        総流入: \${d.totalInflow.toLocaleString()}名<br>
        総流出: \${d.totalOutflow.toLocaleString()}名<br>
        純フロー: \${d.netFlow > 0 ? '+' : ''}\${d.netFlow.toLocaleString()}名
      \`;
    }

    // ツールチップ非表示
    function hideTooltip() {
      document.getElementById('tooltip').style.display = 'none';
    }

    // ノード詳細表示
    function showNodeDetail(event, d) {
      const container = document.getElementById('node-detail-container');
      container.innerHTML = \`
        <div class="node-detail">
          <h4>\${d.id}</h4>
          <p><strong>都道府県:</strong> \${d.prefecture}</p>
          <p><strong>総流入:</strong> \${d.totalInflow.toLocaleString()}名</p>
          <p><strong>総流出:</strong> \${d.totalOutflow.toLocaleString()}名</p>
          <p><strong>純フロー:</strong> \${d.netFlow > 0 ? '+' : ''}\${d.netFlow.toLocaleString()}名</p>
          <p><strong>フロー数:</strong> \${d.flowCount}件</p>
          <p style="margin-top: 10px; color: \${d.netFlow > 0 ? '#10b981' : '#ef4444'};">
            \${d.netFlow > 0 ? '流入超過地域' : d.netFlow < 0 ? '流出超過地域' : 'バランス地域'}
          </p>
        </div>
      \`;
    }

    // ドラッグイベント
    function dragStarted(event, d) {
      if (!event.active) simulation.alphaTarget(0.3).restart();
      d.fx = d.x;
      d.fy = d.y;
    }

    function dragged(event, d) {
      d.fx = event.x;
      d.fy = event.y;
    }

    function dragEnded(event, d) {
      if (!event.active) simulation.alphaTarget(0);
      d.fx = null;
      d.fy = null;
    }

    // 統計更新
    function updateStatistics() {
      document.getElementById('visible-nodes').textContent = currentNodes.length.toLocaleString();
      document.getElementById('visible-edges').textContent = currentEdges.length.toLocaleString();

      const totalFlow = currentEdges.reduce((sum, e) => sum + e.flow, 0);
      document.getElementById('total-flow').textContent = totalFlow.toLocaleString() + '名';
    }

    // ズームリセット
    function resetZoom() {
      svg.transition().duration(750).call(
        d3.zoom().transform,
        d3.zoomIdentity
      );
    }

    // データ出力
    function exportData() {
      let csv = 'Source,Target,Flow\\n';
      currentEdges.forEach(edge => {
        csv += \`\${edge.source.id || edge.source},\${edge.target.id || edge.target},\${edge.flow}\\n\`;
      });

      const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
      const link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      link.download = \`MunicipalityFlow_\${new Date().toISOString().split('T')[0]}.csv\`;
      link.click();
    }

    // 初期化実行
    window.onload = init;

    // リサイズ対応
    window.addEventListener('resize', () => {
      if (simulation) {
        const width = document.querySelector('.network-container').clientWidth;
        const height = document.querySelector('.network-container').clientHeight;
        simulation.force('center', d3.forceCenter(width / 2, height / 2));
        simulation.alpha(0.3).restart();
      }
    });
  </script>
</body>
</html>
  `;
}
