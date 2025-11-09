/**
 * Phase 10 転職意欲・緊急度分析統合ダッシュボード
 *
 * Phase 10のすべての分析結果を1つのダッシュボードに統合します。
 * - Tab 1: 緊急度分布
 * - Tab 2: 緊急度×年齢クロス
 * - Tab 3: 緊急度×就業状態クロス
 * - Tab 4: 緊急度×年齢マトリックス
 * - Tab 5: 市区町村別緊急度
 */

/**
 * Phase 10統合ダッシュボード表示（メニューから呼び出し）
 */
function showPhase10CompleteDashboard() {
  const ui = SpreadsheetApp.getUi();

  try {
    // すべてのデータ読み込み
    const urgencyDistData = loadUrgencyDistData();
    const urgencyAgeData = loadUrgencyAgeCrossData();
    const urgencyEmpData = loadUrgencyEmploymentCrossData();
    const urgencyMatrixData = loadUrgencyAgeMatrixData();
    const urgencyMuniData = loadUrgencyByMunicipalityData();

    // データ検証
    if (!urgencyDistData || urgencyDistData.length === 0) {
      ui.alert(
        'データなし',
        'Phase 10のデータがありません。\n' +
        '先に「Python結果CSVを取り込み」を実行してください。',
        ui.ButtonSet.OK
      );
      return;
    }

    // HTML生成
    const html = generatePhase10DashboardHTML({
      urgencyDist: urgencyDistData,
      urgencyAge: urgencyAgeData,
      urgencyEmp: urgencyEmpData,
      urgencyMatrix: urgencyMatrixData,
      urgencyMuni: urgencyMuniData
    });

    // ダイアログ表示
    const htmlOutput = HtmlService.createHtmlOutput(html)
      .setWidth(1500)
      .setHeight(950);

    ui.showModalDialog(htmlOutput, 'Phase 10: 転職意欲・緊急度分析統合ダッシュボード');

  } catch (error) {
    ui.alert('エラー', `ダッシュボード表示中にエラーが発生しました:\n${error.message}`, ui.ButtonSet.OK);
    Logger.log(`Phase 10ダッシュボードエラー: ${error.stack}`);
  }
}


/**
 * Phase 10統合ダッシュボードHTML生成
 * @param {Object} allData - すべてのデータオブジェクト
 * @return {string} HTML文字列
 */
function generatePhase10DashboardHTML(allData) {
  const urgencyDistJson = JSON.stringify(allData.urgencyDist);
  const urgencyAgeJson = JSON.stringify(allData.urgencyAge);
  const urgencyEmpJson = JSON.stringify(allData.urgencyEmp);
  const urgencyMatrixJson = JSON.stringify(allData.urgencyMatrix);
  const urgencyMuniJson = JSON.stringify(allData.urgencyMuni);

  return `
<!DOCTYPE html>
<html>
<head>
  <base target="_top">
  <script type="text/javascript" src="https://www.gstatic.com/charts/loader.js"></script>
  <style>
    * {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }
    body {
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      overflow: hidden;
    }
    .header {
      background: rgba(255, 255, 255, 0.95);
      padding: 20px 30px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    h1 {
      color: #1a73e8;
      font-size: 24px;
      display: flex;
      align-items: center;
      gap: 10px;
    }
    .subtitle {
      color: #666;
      font-size: 14px;
      margin-top: 5px;
    }
    .tabs {
      display: flex;
      gap: 5px;
      padding: 15px 30px 0;
      background: rgba(255, 255, 255, 0.3);
    }
    .tab {
      padding: 12px 24px;
      background: rgba(255, 255, 255, 0.6);
      border: none;
      border-radius: 8px 8px 0 0;
      cursor: pointer;
      font-size: 14px;
      font-weight: 600;
      color: #555;
      transition: all 0.3s ease;
    }
    .tab:hover {
      background: rgba(255, 255, 255, 0.8);
      transform: translateY(-2px);
    }
    .tab.active {
      background: white;
      color: #1a73e8;
      box-shadow: 0 -2px 8px rgba(0,0,0,0.1);
    }
    .content {
      background: white;
      height: calc(100vh - 140px);
      overflow-y: auto;
      padding: 30px;
    }
    .tab-content {
      display: none;
      animation: fadeIn 0.5s ease;
    }
    .tab-content.active {
      display: block;
    }
    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(10px); }
      to { opacity: 1; transform: translateY(0); }
    }
    .chart-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 20px;
      margin-bottom: 20px;
    }
    .chart-container {
      background: #f8f9fa;
      padding: 20px;
      border-radius: 8px;
      box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .chart-container h3 {
      color: #333;
      margin-bottom: 15px;
      font-size: 16px;
    }
    .chart {
      width: 100%;
      height: 400px;
    }
    .stats-summary {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 15px;
      margin-bottom: 20px;
    }
    .stat-card {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      padding: 20px;
      border-radius: 8px;
      text-align: center;
    }
    .stat-label {
      font-size: 12px;
      opacity: 0.9;
      margin-bottom: 5px;
    }
    .stat-value {
      font-size: 28px;
      font-weight: bold;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      margin-top: 20px;
      font-size: 13px;
      background: white;
    }
    th {
      background-color: #1a73e8;
      color: white;
      padding: 12px;
      text-align: left;
      font-weight: bold;
      position: sticky;
      top: 0;
      z-index: 10;
    }
    td {
      padding: 10px 12px;
      border-bottom: 1px solid #ddd;
    }
    tr:hover {
      background-color: #f5f5f5;
    }
    .table-container {
      max-height: 400px;
      overflow-y: auto;
      border: 1px solid #ddd;
      border-radius: 8px;
    }
    .urgency-badge {
      display: inline-block;
      padding: 4px 8px;
      border-radius: 12px;
      font-weight: bold;
      font-size: 11px;
    }
    .urgency-A { background-color: #dc3545; color: white; }
    .urgency-B { background-color: #ffc107; color: #333; }
    .urgency-C { background-color: #17a2b8; color: white; }
    .urgency-D { background-color: #6c757d; color: white; }
    .note {
      background-color: #fff3cd;
      border-left: 4px solid #ffc107;
      padding: 15px;
      margin: 20px 0;
      border-radius: 4px;
      font-size: 14px;
    }
  </style>
</head>
<body>
  <div class="header">
    <h1>🚀 Phase 10: 転職意欲・緊急度分析統合ダッシュボード</h1>
    <div class="subtitle">緊急度ランク（A-D）による求職者セグメンテーションと地域分析</div>
  </div>

  <div class="tabs">
    <button class="tab active" onclick="switchTab(0)">📊 緊急度分布</button>
    <button class="tab" onclick="switchTab(1)">👥 緊急度×年齢</button>
    <button class="tab" onclick="switchTab(2)">💼 緊急度×就業状態</button>
    <button class="tab" onclick="switchTab(3)">🔥 マトリックス</button>
    <button class="tab" onclick="switchTab(4)">🗺️ 市区町村別</button>
  </div>

  <div class="content">
    <!-- Tab 1: 緊急度分布 -->
    <div class="tab-content active" id="tab0">
      <div class="stats-summary" id="dist-stats"></div>

      <div class="note">
        <strong>📊 緊急度ランク説明:</strong>
        <ul style="margin: 10px 0; padding-left: 20px;">
          <li><strong>A: 高い</strong> - 緊急度スコア7以上（即座に対応すべき）</li>
          <li><strong>B: 中程度</strong> - 緊急度スコア5-7（優先的に対応）</li>
          <li><strong>C: やや低い</strong> - 緊急度スコア3-5（計画的に対応）</li>
          <li><strong>D: 低い</strong> - 緊急度スコア3未満（長期的に対応）</li>
        </ul>
      </div>

      <div class="chart-grid">
        <div class="chart-container">
          <h3>緊急度ランク別割合（円グラフ）</h3>
          <div id="pie_chart" class="chart"></div>
        </div>
        <div class="chart-container">
          <h3>緊急度ランク別人数（棒グラフ）</h3>
          <div id="bar_chart" class="chart"></div>
        </div>
      </div>

      <div class="table-container">
        <table id="dist-table">
          <thead>
            <tr>
              <th style="width: 30%;">緊急度ランク</th>
              <th style="width: 20%;">人数</th>
              <th style="width: 15%;">割合</th>
              <th style="width: 15%;">平均年齢</th>
              <th style="width: 20%;">平均緊急度スコア</th>
            </tr>
          </thead>
          <tbody id="dist-tbody"></tbody>
        </table>
      </div>
    </div>

    <!-- Tab 2: 緊急度×年齢 -->
    <div class="tab-content" id="tab1">
      <div class="stats-summary" id="age-stats"></div>
      <div class="chart-container">
        <h3>緊急度×年齢層グループ化縦棒グラフ</h3>
        <div id="age_column_chart" style="width: 100%; height: 500px;"></div>
      </div>
      <div class="table-container">
        <table id="age-table">
          <thead>
            <tr>
              <th style="width: 25%;">緊急度ランク</th>
              <th style="width: 20%;">年齢層</th>
              <th style="width: 15%;">人数</th>
              <th style="width: 15%;">平均年齢</th>
              <th style="width: 25%;">平均緊急度スコア</th>
            </tr>
          </thead>
          <tbody id="age-tbody"></tbody>
        </table>
      </div>
    </div>

    <!-- Tab 3: 緊急度×就業状態 -->
    <div class="tab-content" id="tab2">
      <div class="stats-summary" id="emp-stats"></div>
      <div class="chart-container">
        <h3>緊急度×就業状態グループ化縦棒グラフ</h3>
        <div id="emp_column_chart" style="width: 100%; height: 500px;"></div>
      </div>
      <div class="table-container">
        <table id="emp-table">
          <thead>
            <tr>
              <th style="width: 25%;">緊急度ランク</th>
              <th style="width: 20%;">就業状態</th>
              <th style="width: 15%;">人数</th>
              <th style="width: 15%;">平均年齢</th>
              <th style="width: 25%;">平均緊急度スコア</th>
            </tr>
          </thead>
          <tbody id="emp-tbody"></tbody>
        </table>
      </div>
    </div>

    <!-- Tab 4: マトリックス -->
    <div class="tab-content" id="tab3">
      <div class="stats-summary" id="matrix-stats"></div>
      <div class="chart-container">
        <h3>緊急度×年齢層ヒートマップ</h3>
        <div id="matrix-legend" style="display: flex; justify-content: center; margin-bottom: 15px; flex-wrap: wrap;"></div>
        <div style="overflow: auto; max-height: 600px; border: 1px solid #ddd; border-radius: 4px;">
          <table id="matrix-table"></table>
        </div>
      </div>
    </div>

    <!-- Tab 5: 市区町村別 -->
    <div class="tab-content" id="tab4">
      <div class="stats-summary" id="muni-stats"></div>
      <div class="chart-grid">
        <div class="chart-container">
          <h3>人数×緊急度スコア散布図</h3>
          <div id="scatter_chart" class="chart"></div>
        </div>
        <div class="chart-container">
          <h3>TOP20市区町村（人数順）</h3>
          <div id="muni_bar_chart" class="chart"></div>
        </div>
      </div>
      <div class="table-container">
        <table id="muni-table">
          <thead>
            <tr>
              <th style="width: 5%;">順位</th>
              <th style="width: 35%;">市区町村</th>
              <th style="width: 15%;">人数</th>
              <th style="width: 20%;">平均緊急度スコア</th>
              <th style="width: 25%;">緊急度ランク</th>
            </tr>
          </thead>
          <tbody id="muni-tbody"></tbody>
        </table>
      </div>
    </div>
  </div>

  <script type="text/javascript">
    // データ読み込み
    const urgencyDistData = ${urgencyDistJson};
    const urgencyAgeData = ${urgencyAgeJson};
    const urgencyEmpData = ${urgencyEmpJson};
    const urgencyMatrixData = ${urgencyMatrixJson};
    const urgencyMuniData = ${urgencyMuniJson};

    // 定義
    const urgencyOrder = ['A: 高い', 'B: 中程度', 'C: やや低い', 'D: 低い'];
    const ageGroupOrder = ['20代', '30代', '40代', '50代', '60代', '70歳以上'];
    const employmentOrder = ['在学中', '就業中', '離職中'];

    // ユーティリティ関数
    function getUrgencyRank(score) {
      if (score >= 7) return 'A: 高い';
      if (score >= 5) return 'B: 中程度';
      if (score >= 3) return 'C: やや低い';
      return 'D: 低い';
    }

    function getUrgencyBadgeClass(rank) {
      if (rank.startsWith('A')) return 'urgency-A';
      if (rank.startsWith('B')) return 'urgency-B';
      if (rank.startsWith('C')) return 'urgency-C';
      return 'urgency-D';
    }

    // タブ切り替え
    function switchTab(index) {
      document.querySelectorAll('.tab').forEach((tab, i) => {
        tab.classList.toggle('active', i === index);
      });
      document.querySelectorAll('.tab-content').forEach((content, i) => {
        content.classList.toggle('active', i === index);
      });

      // タブごとにチャート再描画
      if (index === 0) drawDistCharts();
      if (index === 1) drawAgeChart();
      if (index === 2) drawEmpChart();
      if (index === 3) drawMatrixChart();
      if (index === 4) drawMuniCharts();
    }

    // Google Charts読み込み
    google.charts.load('current', {'packages':['corechart']});
    google.charts.setOnLoadCallback(initialize);

    function initialize() {
      renderAllStats();
      drawDistCharts();
      renderDistTable();
      renderAgeTable();
      renderEmpTable();
      renderMuniTable();
    }

    // 統計サマリー表示
    function renderAllStats() {
      renderDistStats();
      renderAgeStats();
      renderEmpStats();
      renderMatrixStats();
      renderMuniStats();
    }

    function renderDistStats() {
      const container = document.getElementById('dist-stats');
      const totalCount = urgencyDistData.reduce((sum, row) => sum + row.count, 0);
      const highUrgencyCount = urgencyDistData
        .filter(d => d.urgencyRank.startsWith('A') || d.urgencyRank.startsWith('B'))
        .reduce((sum, d) => sum + d.count, 0);
      const avgAge = urgencyDistData.reduce((sum, row) => sum + (row.avgAge || 0) * row.count, 0) / totalCount;
      const avgScore = urgencyDistData.reduce((sum, row) => sum + (row.avgUrgencyScore || 0) * row.count, 0) / totalCount;

      const stats = [
        {label: '総人数', value: totalCount.toLocaleString(), unit: '名'},
        {label: '高緊急度（A+B）', value: \`\${highUrgencyCount.toLocaleString()} (\${(highUrgencyCount/totalCount*100).toFixed(1)}%)\`, unit: ''},
        {label: '平均年齢', value: Math.round(avgAge), unit: '歳'},
        {label: '平均緊急度スコア', value: avgScore.toFixed(2), unit: '点'}
      ];

      stats.forEach(stat => {
        const card = document.createElement('div');
        card.className = 'stat-card';
        card.innerHTML = \`
          <div class="stat-label">\${stat.label}</div>
          <div class="stat-value">\${stat.value}</div>
          <div class="stat-label">\${stat.unit}</div>
        \`;
        container.appendChild(card);
      });
    }

    function renderAgeStats() {
      const container = document.getElementById('age-stats');
      const totalCount = urgencyAgeData.reduce((sum, row) => sum + row.count, 0);
      const uniqueAgeGroups = [...new Set(urgencyAgeData.map(d => d.ageGroup))].length;
      const avgScore = urgencyAgeData.reduce((sum, row) => sum + (row.avgUrgencyScore || 0) * row.count, 0) / totalCount;

      const stats = [
        {label: '緊急度ランク数', value: urgencyOrder.length, unit: 'ランク'},
        {label: '総人数', value: totalCount.toLocaleString(), unit: '名'},
        {label: '年齢層数', value: uniqueAgeGroups, unit: 'グループ'},
        {label: '平均緊急度スコア', value: avgScore.toFixed(2), unit: '点'}
      ];

      stats.forEach(stat => {
        const card = document.createElement('div');
        card.className = 'stat-card';
        card.innerHTML = \`
          <div class="stat-label">\${stat.label}</div>
          <div class="stat-value">\${stat.value}</div>
          <div class="stat-label">\${stat.unit}</div>
        \`;
        container.appendChild(card);
      });
    }

    function renderEmpStats() {
      const container = document.getElementById('emp-stats');
      const totalCount = urgencyEmpData.reduce((sum, row) => sum + row.count, 0);
      const uniqueEmp = [...new Set(urgencyEmpData.map(d => d.employmentStatus))].length;
      const avgScore = urgencyEmpData.reduce((sum, row) => sum + (row.avgUrgencyScore || 0) * row.count, 0) / totalCount;

      const stats = [
        {label: '緊急度ランク数', value: urgencyOrder.length, unit: 'ランク'},
        {label: '総人数', value: totalCount.toLocaleString(), unit: '名'},
        {label: '就業状態数', value: uniqueEmp, unit: '種類'},
        {label: '平均緊急度スコア', value: avgScore.toFixed(2), unit: '点'}
      ];

      stats.forEach(stat => {
        const card = document.createElement('div');
        card.className = 'stat-card';
        card.innerHTML = \`
          <div class="stat-label">\${stat.label}</div>
          <div class="stat-value">\${stat.value}</div>
          <div class="stat-label">\${stat.unit}</div>
        \`;
        container.appendChild(card);
      });
    }

    function renderMatrixStats() {
      const container = document.getElementById('matrix-stats');
      const metadata = urgencyMatrixData.metadata;

      const stats = [
        {label: '総緊急度ランク数', value: urgencyMatrixData.totalRows, unit: '種類'},
        {label: '総人数', value: metadata.totalCount.toLocaleString(), unit: '名'},
        {label: '最大値', value: metadata.max, unit: '名'},
        {label: '平均値', value: metadata.mean.toFixed(1), unit: '名'}
      ];

      stats.forEach(stat => {
        const card = document.createElement('div');
        card.className = 'stat-card';
        card.innerHTML = \`
          <div class="stat-label">\${stat.label}</div>
          <div class="stat-value">\${stat.value}</div>
          <div class="stat-label">\${stat.unit}</div>
        \`;
        container.appendChild(card);
      });
    }

    function renderMuniStats() {
      const container = document.getElementById('muni-stats');
      const totalCount = urgencyMuniData.reduce((sum, row) => sum + row.count, 0);
      const avgScore = urgencyMuniData.reduce((sum, row) => sum + (row.avgUrgencyScore || 0) * row.count, 0) / totalCount;
      const highUrgencyCount = urgencyMuniData.filter(d => {
        const rank = getUrgencyRank(d.avgUrgencyScore || 0);
        return rank.startsWith('A') || rank.startsWith('B');
      }).length;

      const stats = [
        {label: '総市区町村数', value: urgencyMuniData.length.toLocaleString(), unit: '地域'},
        {label: '総人数', value: totalCount.toLocaleString(), unit: '名'},
        {label: '平均緊急度スコア', value: avgScore.toFixed(2), unit: '点'},
        {label: '高緊急度（A+B）地域', value: highUrgencyCount.toLocaleString(), unit: '地域'}
      ];

      stats.forEach(stat => {
        const card = document.createElement('div');
        card.className = 'stat-card';
        card.innerHTML = \`
          <div class="stat-label">\${stat.label}</div>
          <div class="stat-value">\${stat.value}</div>
          <div class="stat-label">\${stat.unit}</div>
        \`;
        container.appendChild(card);
      });
    }

    // チャート描画
    function drawDistCharts() {
      // 円グラフ
      const pieData = new google.visualization.DataTable();
      pieData.addColumn('string', '緊急度ランク');
      pieData.addColumn('number', '人数');
      urgencyDistData.forEach(row => {
        pieData.addRow([row.urgencyRank, row.count]);
      });
      const pieOptions = {
        pieHole: 0.4,
        colors: ['#dc3545', '#ffc107', '#17a2b8', '#6c757d'],
        legend: {position: 'bottom'},
        chartArea: {width: '90%', height: '70%'}
      };
      const pieChart = new google.visualization.PieChart(document.getElementById('pie_chart'));
      pieChart.draw(pieData, pieOptions);

      // 棒グラフ
      const barData = new google.visualization.DataTable();
      barData.addColumn('string', '緊急度ランク');
      barData.addColumn('number', '人数');
      urgencyDistData.forEach(row => {
        barData.addRow([row.urgencyRank, row.count]);
      });
      const barOptions = {
        legend: {position: 'none'},
        chartArea: {width: '70%', height: '70%'},
        hAxis: {title: '人数', minValue: 0},
        vAxis: {title: '緊急度ランク'},
        colors: ['#667eea']
      };
      const barChart = new google.visualization.ColumnChart(document.getElementById('bar_chart'));
      barChart.draw(barData, barOptions);
    }

    function drawAgeChart() {
      const ageGroupMap = {};
      ageGroupOrder.forEach(ag => {
        ageGroupMap[ag] = {};
        urgencyOrder.forEach(ur => {
          ageGroupMap[ag][ur] = 0;
        });
      });

      urgencyAgeData.forEach(row => {
        if (ageGroupMap[row.ageGroup] && urgencyOrder.includes(row.urgencyRank)) {
          ageGroupMap[row.ageGroup][row.urgencyRank] = row.count;
        }
      });

      const chartData = new google.visualization.DataTable();
      chartData.addColumn('string', '年齢層');
      urgencyOrder.forEach(ur => {
        chartData.addColumn('number', ur);
      });

      ageGroupOrder.forEach(ag => {
        const row = [ag];
        urgencyOrder.forEach(ur => {
          row.push(ageGroupMap[ag][ur] || 0);
        });
        chartData.addRow(row);
      });

      const options = {
        title: '緊急度×年齢層グループ化縦棒グラフ',
        chartArea: {width: '70%', height: '70%'},
        hAxis: {title: '年齢層'},
        vAxis: {title: '人数', minValue: 0},
        isStacked: false,
        legend: {position: 'top', maxLines: 2},
        colors: ['#dc3545', '#ffc107', '#17a2b8', '#6c757d'],
        bar: {groupWidth: '75%'}
      };

      const chart = new google.visualization.ColumnChart(document.getElementById('age_column_chart'));
      chart.draw(chartData, options);
    }

    function drawEmpChart() {
      const employmentMap = {};
      employmentOrder.forEach(emp => {
        employmentMap[emp] = {};
        urgencyOrder.forEach(ur => {
          employmentMap[emp][ur] = 0;
        });
      });

      urgencyEmpData.forEach(row => {
        if (employmentMap[row.employmentStatus] && urgencyOrder.includes(row.urgencyRank)) {
          employmentMap[row.employmentStatus][row.urgencyRank] = row.count;
        }
      });

      const chartData = new google.visualization.DataTable();
      chartData.addColumn('string', '就業状態');
      urgencyOrder.forEach(ur => {
        chartData.addColumn('number', ur);
      });

      employmentOrder.forEach(emp => {
        const row = [emp];
        urgencyOrder.forEach(ur => {
          row.push(employmentMap[emp][ur] || 0);
        });
        chartData.addRow(row);
      });

      const options = {
        title: '緊急度×就業状態グループ化縦棒グラフ',
        chartArea: {width: '70%', height: '70%'},
        hAxis: {title: '就業状態'},
        vAxis: {title: '人数', minValue: 0},
        isStacked: false,
        legend: {position: 'top', maxLines: 2},
        colors: ['#dc3545', '#ffc107', '#17a2b8', '#6c757d'],
        bar: {groupWidth: '75%'}
      };

      const chart = new google.visualization.ColumnChart(document.getElementById('emp_column_chart'));
      chart.draw(chartData, options);
    }

    function drawMatrixChart() {
      const metadata = urgencyMatrixData.metadata;
      const table = document.getElementById('matrix-table');
      table.innerHTML = '';

      // カラースケール
      function getHeatmapColor(value, max) {
        if (value === 0) return '#f8f9fa';
        const intensity = Math.min(value / max, 1);
        const r = 255;
        const g = Math.round(255 * (1 - intensity));
        const b = Math.round(255 * (1 - intensity));
        return \`rgb(\${r}, \${g}, \${b})\`;
      }

      // 凡例
      const legend = document.getElementById('matrix-legend');
      legend.innerHTML = '';
      const legendSteps = [
        { label: '0名', value: 0 },
        { label: \`\${Math.round(metadata.max * 0.5)}名\`, value: metadata.max * 0.5 },
        { label: \`\${metadata.max}名\`, value: metadata.max }
      ];
      legendSteps.forEach(step => {
        const item = document.createElement('div');
        item.style.cssText = 'margin: 5px 10px; display: flex; align-items: center;';
        const box = document.createElement('div');
        box.style.cssText = \`width: 30px; height: 20px; margin-right: 5px; border: 1px solid #ddd; background-color: \${getHeatmapColor(step.value, metadata.max)};\`;
        item.appendChild(box);
        item.appendChild(document.createTextNode(step.label));
        legend.appendChild(item);
      });

      // ヘッダー
      const thead = document.createElement('thead');
      const headerRow = document.createElement('tr');
      urgencyMatrixData.headers.forEach((header, index) => {
        const th = document.createElement('th');
        th.textContent = header;
        if (index === 0) th.style.cssText = 'min-width: 150px; text-align: left; position: sticky; left: 0; z-index: 11; background-color: #1a73e8;';
        else th.style.cssText = 'text-align: center;';
        headerRow.appendChild(th);
      });
      thead.appendChild(headerRow);
      table.appendChild(thead);

      // データ行
      const tbody = document.createElement('tbody');
      urgencyMatrixData.rows.forEach(row => {
        const tr = document.createElement('tr');
        row.forEach((cell, colIndex) => {
          const td = document.createElement('td');
          if (colIndex === 0) {
            td.textContent = cell;
            td.style.cssText = 'font-weight: bold; position: sticky; left: 0; background-color: #f8f9fa; z-index: 5; border-right: 2px solid #1a73e8;';
          } else {
            const value = Number(cell) || 0;
            td.textContent = value > 0 ? value : '－';
            td.style.cssText = \`text-align: center; background-color: \${getHeatmapColor(value, metadata.max)};\`;
            if (value > metadata.max * 0.6) {
              td.style.color = 'white';
              td.style.fontWeight = 'bold';
            }
          }
          tr.appendChild(td);
        });
        tbody.appendChild(tr);
      });
      table.appendChild(tbody);
    }

    function drawMuniCharts() {
      // 散布図
      const scatterData = new google.visualization.DataTable();
      scatterData.addColumn('number', '人数');
      scatterData.addColumn('number', '平均緊急度スコア');
      scatterData.addColumn({type: 'string', role: 'tooltip'});
      urgencyMuniData.forEach(row => {
        const tooltip = \`\${row.municipality}\\n人数: \${row.count}名\\n緊急度: \${row.avgUrgencyScore ? row.avgUrgencyScore.toFixed(2) : 'N/A'}点\`;
        scatterData.addRow([row.count, row.avgUrgencyScore || 0, tooltip]);
      });
      const scatterOptions = {
        hAxis: {title: '人数', minValue: 0},
        vAxis: {title: '平均緊急度スコア', minValue: 0, maxValue: 10},
        legend: 'none',
        pointSize: 5,
        colors: ['#667eea'],
        chartArea: {width: '75%', height: '70%'}
      };
      const scatterChart = new google.visualization.ScatterChart(document.getElementById('scatter_chart'));
      scatterChart.draw(scatterData, scatterOptions);

      // TOP20棒グラフ
      const sortedData = [...urgencyMuniData].sort((a, b) => b.count - a.count).slice(0, 20);
      const muniBarData = new google.visualization.DataTable();
      muniBarData.addColumn('string', '市区町村');
      muniBarData.addColumn('number', '人数');
      sortedData.forEach(row => {
        muniBarData.addRow([row.municipality, row.count]);
      });
      const muniBarOptions = {
        legend: {position: 'none'},
        chartArea: {width: '70%', height: '75%'},
        hAxis: {title: '人数', minValue: 0},
        colors: ['#4285F4']
      };
      const muniBarChart = new google.visualization.BarChart(document.getElementById('muni_bar_chart'));
      muniBarChart.draw(muniBarData, muniBarOptions);
    }

    // テーブル描画
    function renderDistTable() {
      const tbody = document.getElementById('dist-tbody');
      const totalCount = urgencyDistData.reduce((sum, row) => sum + row.count, 0);
      const sortedData = urgencyDistData.sort((a, b) => urgencyOrder.indexOf(a.urgencyRank) - urgencyOrder.indexOf(b.urgencyRank));

      sortedData.forEach(row => {
        const tr = document.createElement('tr');
        const badgeClass = getUrgencyBadgeClass(row.urgencyRank);
        const percentage = (row.count / totalCount * 100).toFixed(1);

        tr.innerHTML = \`
          <td><span class="urgency-badge \${badgeClass}">\${row.urgencyRank}</span></td>
          <td style="text-align: right;"><strong>\${row.count.toLocaleString()}</strong>名</td>
          <td style="text-align: right;"><strong>\${percentage}%</strong></td>
          <td style="text-align: right;">\${row.avgAge ? row.avgAge.toFixed(1) + '歳' : '－'}</td>
          <td style="text-align: right;"><strong>\${row.avgUrgencyScore ? row.avgUrgencyScore.toFixed(2) : '－'}</strong>点</td>
        \`;
        tbody.appendChild(tr);
      });
    }

    function renderAgeTable() {
      const tbody = document.getElementById('age-tbody');
      const sortedData = urgencyAgeData.sort((a, b) => {
        const urgencyDiff = urgencyOrder.indexOf(a.urgencyRank) - urgencyOrder.indexOf(b.urgencyRank);
        if (urgencyDiff !== 0) return urgencyDiff;
        return ageGroupOrder.indexOf(a.ageGroup) - ageGroupOrder.indexOf(b.ageGroup);
      });

      let prevUrgency = null;
      sortedData.forEach(row => {
        const tr = document.createElement('tr');
        const badgeClass = getUrgencyBadgeClass(row.urgencyRank);
        const urgencyHtml = row.urgencyRank !== prevUrgency
          ? \`<span class="urgency-badge \${badgeClass}">\${row.urgencyRank}</span>\`
          : '';
        prevUrgency = row.urgencyRank;

        tr.innerHTML = \`
          <td>\${urgencyHtml}</td>
          <td>\${row.ageGroup}</td>
          <td style="text-align: right;"><strong>\${row.count.toLocaleString()}</strong>名</td>
          <td style="text-align: right;">\${row.avgAge ? row.avgAge.toFixed(1) + '歳' : '－'}</td>
          <td style="text-align: right;"><strong>\${row.avgUrgencyScore ? row.avgUrgencyScore.toFixed(2) : '－'}</strong>点</td>
        \`;
        tbody.appendChild(tr);
      });
    }

    function renderEmpTable() {
      const tbody = document.getElementById('emp-tbody');
      const sortedData = urgencyEmpData.sort((a, b) => {
        const urgencyDiff = urgencyOrder.indexOf(a.urgencyRank) - urgencyOrder.indexOf(b.urgencyRank);
        if (urgencyDiff !== 0) return urgencyDiff;
        return employmentOrder.indexOf(a.employmentStatus) - employmentOrder.indexOf(b.employmentStatus);
      });

      let prevUrgency = null;
      sortedData.forEach(row => {
        const tr = document.createElement('tr');
        const badgeClass = getUrgencyBadgeClass(row.urgencyRank);
        const urgencyHtml = row.urgencyRank !== prevUrgency
          ? \`<span class="urgency-badge \${badgeClass}">\${row.urgencyRank}</span>\`
          : '';
        prevUrgency = row.urgencyRank;

        tr.innerHTML = \`
          <td>\${urgencyHtml}</td>
          <td>\${row.employmentStatus}</td>
          <td style="text-align: right;"><strong>\${row.count.toLocaleString()}</strong>名</td>
          <td style="text-align: right;">\${row.avgAge ? row.avgAge.toFixed(1) + '歳' : '－'}</td>
          <td style="text-align: right;"><strong>\${row.avgUrgencyScore ? row.avgUrgencyScore.toFixed(2) : '－'}</strong>点</td>
        \`;
        tbody.appendChild(tr);
      });
    }

    function renderMuniTable() {
      const tbody = document.getElementById('muni-tbody');
      const sortedData = [...urgencyMuniData].sort((a, b) => b.count - a.count).slice(0, 100);

      sortedData.forEach((row, index) => {
        const tr = document.createElement('tr');
        const rank = getUrgencyRank(row.avgUrgencyScore || 0);
        const badgeClass = getUrgencyBadgeClass(rank);

        tr.innerHTML = \`
          <td style="text-align: center;"><strong>\${index + 1}</strong></td>
          <td><strong>\${row.municipality}</strong></td>
          <td style="text-align: right;"><strong>\${row.count.toLocaleString()}</strong>名</td>
          <td style="text-align: right;">\${row.avgUrgencyScore ? row.avgUrgencyScore.toFixed(2) : '－'}点</td>
          <td><span class="urgency-badge \${badgeClass}">\${rank}</span></td>
        \`;
        tbody.appendChild(tr);
      });
    }
  </script>
</body>
</html>
  `;
}
