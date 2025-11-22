/**
 * Phase 10 緊急度分布可視化
 *
 * 転職意欲・緊急度（A-D）の分布を可視化します。
 */

/**
 * 緊急度分布表示（メニューから呼び出し）
 */
function showUrgencyDistribution() {
  const ui = SpreadsheetApp.getUi();

  try {
    // データ読み込み
    const data = loadUrgencyDistData();

    if (!data || data.length === 0) {
      ui.alert(
        'データなし',
        'P10_UrgencyDistシートにデータがありません。\n' +
        '先に「Python結果CSVを取り込み」を実行してください。',
        ui.ButtonSet.OK
      );
      return;
    }

    // HTML生成
    const html = generateUrgencyDistHTML(data);

    // ダイアログ表示
    const htmlOutput = HtmlService.createHtmlOutput(html)
      .setWidth(1400)
      .setHeight(900);

    ui.showModalDialog(htmlOutput, 'Phase 10: 転職意欲・緊急度分布分析');

  } catch (error) {
    ui.alert('エラー', `可視化中にエラーが発生しました:\n${error.message}`, ui.ButtonSet.OK);
    Logger.log(`緊急度分布エラー: ${error.stack}`);
  }
}


/**
 * 緊急度分布データ読み込み
 * @return {Array<Object>} データオブジェクトの配列
 */
function loadUrgencyDistData() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName('P10_UrgencyDist');

  if (!sheet) {
    throw new Error('P10_UrgencyDistシートが見つかりません');
  }

  const lastRow = sheet.getLastRow();
  if (lastRow <= 1) {
    return [];
  }

  // データ範囲取得（ヘッダー除く）
  const range = sheet.getRange(2, 1, lastRow - 1, 4);
  const values = range.getValues();

  // オブジェクト配列に変換
  const data = values
    .filter(row => row[0] && row[1] > 0)
    .map(row => ({
      urgencyRank: String(row[0]),
      count: Number(row[1]),
      avgAge: row[2] ? Number(row[2]) : null,
      avgUrgencyScore: row[3] ? Number(row[3]) : null
    }));

  Logger.log(`緊急度分布データ読み込み: ${data.length}件`);

  return data;
}


/**
 * 緊急度分布HTML生成
 * @param {Array<Object>} data - データ配列
 * @return {string} HTML文字列
 */
function generateUrgencyDistHTML(data) {
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
    #pie_chart,
    #bar_chart {
      width: 100%;
      height: 450px;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      margin-top: 10px;
      font-size: 14px;
    }
    th, td {
      padding: 12px;
      text-align: left;
      border-bottom: 1px solid #ddd;
    }
    th {
      background-color: #1a73e8;
      color: white;
      font-weight: bold;
    }
    tr:hover {
      background-color: #f5f5f5;
    }
    .urgency-badge {
      display: inline-block;
      padding: 6px 12px;
      border-radius: 20px;
      font-weight: bold;
      font-size: 14px;
    }
    .urgency-A { background-color: #dc3545; color: white; }
    .urgency-B { background-color: #ffc107; color: #333; }
    .urgency-C { background-color: #17a2b8; color: white; }
    .urgency-D { background-color: #6c757d; color: white; }
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
  <h1>🚀 Phase 10: 転職意欲・緊急度分布分析</h1>

  <div class="container">
    <h2>統計サマリー</h2>
    <div class="stats-summary" id="stats-summary"></div>
  </div>

  <div class="note">
    <strong>📊 緊急度ランク説明:</strong>
    <ul style="margin: 10px 0; padding-left: 20px;">
      <li><strong>A: 高い</strong> - 緊急度スコア7以上（即座に対応すべき）</li>
      <li><strong>B: 中程度</strong> - 緊急度スコア5-7（優先的に対応）</li>
      <li><strong>C: やや低い</strong> - 緊急度スコア3-5（計画的に対応）</li>
      <li><strong>D: 低い</strong> - 緊急度スコア3未満（長期的に対応）</li>
    </ul>
  </div>

  <div class="charts-row">
    <div class="chart-container">
      <h3>緊急度ランク別割合（円グラフ）</h3>
      <div id="pie_chart"></div>
    </div>
    <div class="chart-container">
      <h3>緊急度ランク別人数（棒グラフ）</h3>
      <div id="bar_chart"></div>
    </div>
  </div>

  <div class="container">
    <h2>緊急度ランク別詳細データ</h2>
    <table id="data-table">
      <thead>
        <tr>
          <th style="width: 30%;">緊急度ランク</th>
          <th style="width: 20%;">人数</th>
          <th style="width: 15%;">割合</th>
          <th style="width: 15%;">平均年齢</th>
          <th style="width: 20%;">平均緊急度スコア</th>
        </tr>
      </thead>
      <tbody id="table-body"></tbody>
    </table>
  </div>

  <script type="text/javascript">
    const data = ${dataJson};

    // 緊急度順序定義
    const urgencyOrder = ['A: 高い', 'B: 中程度', 'C: やや低い', 'D: 低い'];

    // Google Charts読み込み
    google.charts.load('current', {'packages':['corechart']});
    google.charts.setOnLoadCallback(drawCharts);

    function drawCharts() {
      renderStatsSummary();
      drawPieChart();
      drawBarChart();
      renderDataTable();
    }

    // 統計サマリー表示
    function renderStatsSummary() {
      const container = document.getElementById('stats-summary');

      // 総人数
      const totalCount = data.reduce((sum, row) => sum + row.count, 0);

      // 高緊急度（A+B）の人数と割合
      const highUrgencyCount = data
        .filter(d => d.urgencyRank.startsWith('A') || d.urgencyRank.startsWith('B'))
        .reduce((sum, d) => sum + d.count, 0);
      const highUrgencyRate = (highUrgencyCount / totalCount * 100).toFixed(1);

      // 平均年齢
      const avgAge = data.reduce((sum, row) => sum + (row.avgAge || 0) * row.count, 0) / totalCount;

      // 平均緊急度スコア
      const avgScore = data.reduce((sum, row) => sum + (row.avgUrgencyScore || 0) * row.count, 0) / totalCount;

      const stats = [
        {label: '総人数', value: totalCount.toLocaleString(), unit: '名'},
        {label: '高緊急度（A+B）', value: \`\${highUrgencyCount.toLocaleString()} (\${highUrgencyRate}%)\`, unit: ''},
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

    // 円グラフ描画
    function drawPieChart() {
      const chartData = new google.visualization.DataTable();
      chartData.addColumn('string', '緊急度ランク');
      chartData.addColumn('number', '人数');

      // 緊急度順にソート
      const sortedData = data.sort((a, b) =>
        urgencyOrder.indexOf(a.urgencyRank) - urgencyOrder.indexOf(b.urgencyRank)
      );

      sortedData.forEach(row => {
        chartData.addRow([row.urgencyRank, row.count]);
      });

      const options = {
        title: '緊急度ランク別割合',
        pieHole: 0.4,
        colors: ['#dc3545', '#ffc107', '#17a2b8', '#6c757d'],
        legend: {position: 'bottom'},
        chartArea: {width: '90%', height: '70%'}
      };

      const chart = new google.visualization.PieChart(
        document.getElementById('pie_chart')
      );

      chart.draw(chartData, options);
    }

    // 棒グラフ描画
    function drawBarChart() {
      const chartData = new google.visualization.DataTable();
      chartData.addColumn('string', '緊急度ランク');
      chartData.addColumn('number', '人数');

      // 緊急度順にソート
      const sortedData = data.sort((a, b) =>
        urgencyOrder.indexOf(a.urgencyRank) - urgencyOrder.indexOf(b.urgencyRank)
      );

      sortedData.forEach(row => {
        chartData.addRow([row.urgencyRank, row.count]);
      });

      const options = {
        title: '緊急度ランク別人数',
        legend: {position: 'none'},
        chartArea: {width: '70%', height: '70%'},
        hAxis: {
          title: '人数',
          minValue: 0
        },
        vAxis: {
          title: '緊急度ランク'
        },
        colors: ['#667eea']
      };

      const chart = new google.visualization.ColumnChart(
        document.getElementById('bar_chart')
      );

      chart.draw(chartData, options);
    }

    // データテーブル表示
    function renderDataTable() {
      const tbody = document.getElementById('table-body');

      // 総人数計算
      const totalCount = data.reduce((sum, row) => sum + row.count, 0);

      // 緊急度順にソート
      const sortedData = data.sort((a, b) =>
        urgencyOrder.indexOf(a.urgencyRank) - urgencyOrder.indexOf(b.urgencyRank)
      );

      sortedData.forEach(row => {
        const tr = document.createElement('tr');

        // 緊急度バッジのクラス決定
        const badgeClass = row.urgencyRank.startsWith('A') ? 'urgency-A' :
                           row.urgencyRank.startsWith('B') ? 'urgency-B' :
                           row.urgencyRank.startsWith('C') ? 'urgency-C' : 'urgency-D';

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
  </script>
</body>
</html>
  `;
}
