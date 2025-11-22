/**
 * Phase 10 市区町村別緊急度分布可視化
 *
 * 市区町村ごとの緊急度スコアと人数を可視化します。
 */

/**
 * 市区町村別緊急度マップ表示（メニューから呼び出し）
 */
function showUrgencyByMunicipality() {
  const ui = SpreadsheetApp.getUi();

  try {
    // データ読み込み
    const data = loadUrgencyByMunicipalityData();

    if (!data || data.length === 0) {
      ui.alert(
        'データなし',
        'P10_UrgencyByMuniシートにデータがありません。\n' +
        '先に「Python結果CSVを取り込み」を実行してください。',
        ui.ButtonSet.OK
      );
      return;
    }

    // HTML生成
    const html = generateUrgencyByMunicipalityHTML(data);

    // ダイアログ表示
    const htmlOutput = HtmlService.createHtmlOutput(html)
      .setWidth(1400)
      .setHeight(900);

    ui.showModalDialog(htmlOutput, 'Phase 10: 市区町村別緊急度分布');

  } catch (error) {
    ui.alert('エラー', `可視化中にエラーが発生しました:\n${error.message}`, ui.ButtonSet.OK);
    Logger.log(`市区町村別緊急度マップエラー: ${error.stack}`);
  }
}


/**
 * 市区町村別緊急度データ読み込み
 * @return {Array<Object>} データオブジェクトの配列
 */
function loadUrgencyByMunicipalityData() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName('P10_UrgencyByMuni');

  if (!sheet) {
    throw new Error('P10_UrgencyByMuniシートが見つかりません');
  }

  const lastRow = sheet.getLastRow();
  if (lastRow <= 1) {
    return [];
  }

  // データ範囲取得（ヘッダー除く）
  const range = sheet.getRange(2, 1, lastRow - 1, 3);
  const values = range.getValues();

  // オブジェクト配列に変換
  const data = values
    .filter(row => row[0] && row[1] > 0)
    .map(row => ({
      municipality: String(row[0]),
      count: Number(row[1]),
      avgUrgencyScore: row[2] ? Number(row[2]) : null
    }));

  Logger.log(`市区町村別緊急度データ読み込み: ${data.length}件`);

  return data;
}


/**
 * 緊急度ランク判定
 * @param {number} score - 緊急度スコア
 * @return {string} ランク（A-D）
 */
function getUrgencyRank(score) {
  if (score >= 7) return 'A';
  if (score >= 5) return 'B';
  if (score >= 3) return 'C';
  return 'D';
}


/**
 * 市区町村別緊急度HTML生成
 * @param {Array<Object>} data - データ配列
 * @return {string} HTML文字列
 */
function generateUrgencyByMunicipalityHTML(data) {
  const dataJson = JSON.stringify(data);

  return `
<!DOCTYPE html>
<html>
<head>
  <base target="_top">
  <script type="text/javascript" src="https://www.gstatic.com/charts/loader.js"></script>
  <style>
    body {
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      margin: 20px;
      background-color: #f5f5f5;
    }
    h1 {
      color: #1a73e8;
      border-bottom: 3px solid #1a73e8;
      padding-bottom: 10px;
    }
    .container {
      background-color: white;
      padding: 20px;
      border-radius: 8px;
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
      margin-bottom: 20px;
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
    .charts-row {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 20px;
      margin-bottom: 20px;
    }
    .chart-container {
      background-color: white;
      padding: 20px;
      border-radius: 8px;
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    #scatter_chart {
      width: 100%;
      height: 500px;
    }
    #bar_chart {
      width: 100%;
      height: 500px;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      margin-top: 10px;
      font-size: 13px;
    }
    th, td {
      padding: 10px;
      text-align: left;
      border-bottom: 1px solid #ddd;
    }
    th {
      background-color: #1a73e8;
      color: white;
      font-weight: bold;
      position: sticky;
      top: 0;
      z-index: 10;
    }
    tr:hover {
      background-color: #f5f5f5;
    }
    .table-container {
      max-height: 500px;
      overflow-y: auto;
    }
    .rank-badge {
      display: inline-block;
      padding: 4px 8px;
      border-radius: 12px;
      font-weight: bold;
      font-size: 11px;
      margin-left: 5px;
    }
    .rank-A { background-color: #dc3545; color: white; }
    .rank-B { background-color: #ffc107; color: #333; }
    .rank-C { background-color: #17a2b8; color: white; }
    .rank-D { background-color: #6c757d; color: white; }
    .note {
      background-color: #e7f3ff;
      border-left: 4px solid #1a73e8;
      padding: 15px;
      margin-top: 10px;
      border-radius: 4px;
    }
  </style>
</head>
<body>
  <h1>🗺️ Phase 10: 市区町村別緊急度分布分析</h1>

  <div class="container">
    <h2>統計サマリー</h2>
    <div class="stats-summary" id="stats-summary"></div>
  </div>

  <div class="note">
    <strong>📊 緊急度ランク説明:</strong>
    <ul style="margin: 10px 0; padding-left: 20px;">
      <li><strong>A: 高い</strong> - 平均緊急度スコア7以上（即座に対応すべき地域）</li>
      <li><strong>B: 中程度</strong> - 平均緊急度スコア5-7（優先的に対応）</li>
      <li><strong>C: やや低い</strong> - 平均緊急度スコア3-5（計画的に対応）</li>
      <li><strong>D: 低い</strong> - 平均緊急度スコア3未満（長期的に対応）</li>
    </ul>
  </div>

  <div class="charts-row">
    <div class="chart-container">
      <h3>人数×緊急度スコア散布図</h3>
      <div id="scatter_chart"></div>
    </div>
    <div class="chart-container">
      <h3>TOP20市区町村（人数順）</h3>
      <div id="bar_chart"></div>
    </div>
  </div>

  <div class="container">
    <h2>市区町村別詳細データ（TOP100）</h2>
    <div class="table-container">
      <table id="data-table">
        <thead>
          <tr>
            <th style="width: 5%;">順位</th>
            <th style="width: 35%;">市区町村</th>
            <th style="width: 15%;">人数</th>
            <th style="width: 20%;">平均緊急度スコア</th>
            <th style="width: 25%;">緊急度ランク</th>
          </tr>
        </thead>
        <tbody id="table-body"></tbody>
      </table>
    </div>
  </div>

  <script type="text/javascript">
    const data = ${dataJson};

    // 緊急度ランク判定
    function getUrgencyRank(score) {
      if (score >= 7) return 'A: 高い';
      if (score >= 5) return 'B: 中程度';
      if (score >= 3) return 'C: やや低い';
      return 'D: 低い';
    }

    // Google Charts読み込み
    google.charts.load('current', {'packages':['corechart']});
    google.charts.setOnLoadCallback(drawCharts);

    function drawCharts() {
      renderStatsSummary();
      drawScatterChart();
      drawBarChart();
      renderDataTable();
    }

    // 統計サマリー表示
    function renderStatsSummary() {
      const container = document.getElementById('stats-summary');

      // 総市区町村数
      const totalMunicipalities = data.length;

      // 総人数
      const totalCount = data.reduce((sum, row) => sum + row.count, 0);

      // 平均緊急度スコア
      const avgScore = data.reduce((sum, row) => sum + (row.avgUrgencyScore || 0) * row.count, 0) / totalCount;

      // 高緊急度（A+B）の市区町村数
      const highUrgencyCount = data.filter(d => {
        const rank = getUrgencyRank(d.avgUrgencyScore || 0);
        return rank.startsWith('A') || rank.startsWith('B');
      }).length;

      const stats = [
        {label: '総市区町村数', value: totalMunicipalities.toLocaleString(), unit: '地域'},
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

    // 散布図描画
    function drawScatterChart() {
      const chartData = new google.visualization.DataTable();
      chartData.addColumn('number', '人数');
      chartData.addColumn('number', '平均緊急度スコア');
      chartData.addColumn({type: 'string', role: 'tooltip'});

      data.forEach(row => {
        const tooltip = \`\${row.municipality}\\n人数: \${row.count}名\\n緊急度: \${row.avgUrgencyScore ? row.avgUrgencyScore.toFixed(2) : 'N/A'}点\`;
        chartData.addRow([row.count, row.avgUrgencyScore || 0, tooltip]);
      });

      const options = {
        title: '人数×緊急度スコア散布図',
        hAxis: {title: '人数', minValue: 0},
        vAxis: {title: '平均緊急度スコア', minValue: 0, maxValue: 10},
        legend: 'none',
        pointSize: 5,
        colors: ['#667eea'],
        chartArea: {width: '75%', height: '70%'}
      };

      const chart = new google.visualization.ScatterChart(
        document.getElementById('scatter_chart')
      );

      chart.draw(chartData, options);
    }

    // 棒グラフ描画（TOP20）
    function drawBarChart() {
      const sortedData = [...data].sort((a, b) => b.count - a.count).slice(0, 20);

      const chartData = new google.visualization.DataTable();
      chartData.addColumn('string', '市区町村');
      chartData.addColumn('number', '人数');

      sortedData.forEach(row => {
        chartData.addRow([row.municipality, row.count]);
      });

      const options = {
        title: 'TOP20市区町村（人数順）',
        legend: {position: 'none'},
        chartArea: {width: '70%', height: '75%'},
        hAxis: {
          title: '人数',
          minValue: 0
        },
        colors: ['#4285F4']
      };

      const chart = new google.visualization.BarChart(
        document.getElementById('bar_chart')
      );

      chart.draw(chartData, options);
    }

    // データテーブル表示（TOP100）
    function renderDataTable() {
      const tbody = document.getElementById('table-body');

      // 人数降順でソート、TOP100を取得
      const sortedData = [...data].sort((a, b) => b.count - a.count).slice(0, 100);

      sortedData.forEach((row, index) => {
        const tr = document.createElement('tr');

        const rank = getUrgencyRank(row.avgUrgencyScore || 0);
        const badgeClass = rank.startsWith('A') ? 'rank-A' :
                           rank.startsWith('B') ? 'rank-B' :
                           rank.startsWith('C') ? 'rank-C' : 'rank-D';

        tr.innerHTML = \`
          <td style="text-align: center;"><strong>\${index + 1}</strong></td>
          <td><strong>\${row.municipality}</strong></td>
          <td style="text-align: right;"><strong>\${row.count.toLocaleString()}</strong>名</td>
          <td style="text-align: right;">\${row.avgUrgencyScore ? row.avgUrgencyScore.toFixed(2) : '－'}点</td>
          <td><span class="rank-badge \${badgeClass}">\${rank}</span></td>
        \`;
        tbody.appendChild(tr);
      });
    }
  </script>
</body>
</html>
  `;
}
