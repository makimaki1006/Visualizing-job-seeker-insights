/**
 * Phase 8 卒業年分布可視化
 *
 * 卒業年（1957-2030）の分布をタイムライン表示します。
 */

/**
 * 卒業年分布表示（メニューから呼び出し）
 */
function showGraduationYearDistribution() {
  const ui = SpreadsheetApp.getUi();

  try {
    // データ読み込み
    const data = loadGraduationYearData();

    if (!data || data.length === 0) {
      ui.alert(
        'データなし',
        'P8_GradYearDistシートにデータがありません。\n' +
        '先に「Python結果CSVを取り込み」を実行してください。',
        ui.ButtonSet.OK
      );
      return;
    }

    // HTML生成
    const html = generateGraduationYearHTML(data);

    // ダイアログ表示
    const htmlOutput = HtmlService.createHtmlOutput(html)
      .setWidth(1400)
      .setHeight(900);

    ui.showModalDialog(htmlOutput, 'Phase 8: 卒業年分布分析');

  } catch (error) {
    ui.alert('エラー', `可視化中にエラーが発生しました:\n${error.message}`, ui.ButtonSet.OK);
    Logger.log(`卒業年分布エラー: ${error.stack}`);
  }
}


/**
 * 卒業年データ読み込み
 * @return {Array<Object>} データオブジェクトの配列
 */
function loadGraduationYearData() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName('P8_GradYearDist');

  if (!sheet) {
    throw new Error('P8_GradYearDistシートが見つかりません');
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
      graduationYear: Number(row[0]),
      count: Number(row[1]),
      avgAge: row[2] ? Number(row[2]) : null
    }))
    .sort((a, b) => a.graduationYear - b.graduationYear);  // 年順にソート

  Logger.log(`卒業年分布データ読み込み: ${data.length}件`);

  return data;
}


/**
 * 卒業年分布HTML生成
 * @param {Array<Object>} data - データ配列
 * @return {string} HTML文字列
 */
function generateGraduationYearHTML(data) {
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
    #line_chart {
      width: 100%;
      height: 450px;
    }
    #area_chart {
      width: 100%;
      height: 450px;
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
      max-height: 400px;
      overflow-y: auto;
    }
    .decade-badge {
      display: inline-block;
      padding: 4px 8px;
      border-radius: 4px;
      font-size: 11px;
      font-weight: bold;
      margin-left: 10px;
    }
    .decade-1950 { background-color: #e3f2fd; color: #1976d2; }
    .decade-1960 { background-color: #f3e5f5; color: #7b1fa2; }
    .decade-1970 { background-color: #fff3e0; color: #e65100; }
    .decade-1980 { background-color: #fce4ec; color: #c2185b; }
    .decade-1990 { background-color: #f1f8e9; color: #558b2f; }
    .decade-2000 { background-color: #e0f2f1; color: #00695c; }
    .decade-2010 { background-color: #fff9c4; color: #f57f17; }
    .decade-2020 { background-color: #ffebee; color: #c62828; }
  </style>
</head>
<body>
  <h1>🎓 Phase 8: 卒業年分布分析（1957-2030）</h1>

  <div class="container">
    <h2>統計サマリー</h2>
    <div class="stats-summary" id="stats-summary"></div>
  </div>

  <div class="charts-row">
    <div class="chart-container">
      <h3>卒業年別人数（ラインチャート）</h3>
      <div id="line_chart"></div>
    </div>
    <div class="chart-container">
      <h3>卒業年別人数（エリアチャート）</h3>
      <div id="area_chart"></div>
    </div>
  </div>

  <div class="container">
    <h2>卒業年別詳細データ</h2>
    <div class="table-container">
      <table id="data-table">
        <thead>
          <tr>
            <th style="width: 25%;">卒業年</th>
            <th style="width: 20%;">人数</th>
            <th style="width: 20%;">平均年齢</th>
            <th style="width: 35%;">年代</th>
          </tr>
        </thead>
        <tbody id="table-body"></tbody>
      </table>
    </div>
  </div>

  <script type="text/javascript">
    const data = ${dataJson};

    // Google Charts読み込み
    google.charts.load('current', {'packages':['corechart']});
    google.charts.setOnLoadCallback(drawCharts);

    function drawCharts() {
      renderStatsSummary();
      drawLineChart();
      drawAreaChart();
      renderDataTable();
    }

    // 統計サマリー表示
    function renderStatsSummary() {
      const container = document.getElementById('stats-summary');

      // 総卒業年数
      const totalYears = data.length;

      // 総人数
      const totalCount = data.reduce((sum, row) => sum + row.count, 0);

      // 最多卒業年
      const maxCountRow = data.reduce((max, row) => row.count > max.count ? row : max);

      // 最新卒業年
      const latestYear = Math.max(...data.map(d => d.graduationYear));

      const stats = [
        {label: '卒業年範囲', value: \`\${data[0].graduationYear}-\${data[data.length - 1].graduationYear}\`, unit: ''},
        {label: '総人数', value: totalCount.toLocaleString(), unit: '名'},
        {label: '最多卒業年', value: maxCountRow.graduationYear, unit: \`(\${maxCountRow.count}名)\`},
        {label: '最新卒業年', value: latestYear, unit: '年'}
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

    // ラインチャート描画
    function drawLineChart() {
      const chartData = new google.visualization.DataTable();
      chartData.addColumn('string', '卒業年');
      chartData.addColumn('number', '人数');

      data.forEach(row => {
        chartData.addRow([row.graduationYear.toString(), row.count]);
      });

      const options = {
        title: '卒業年別人数トレンド',
        curveType: 'function',
        legend: { position: 'bottom' },
        chartArea: {width: '80%', height: '70%'},
        hAxis: {
          title: '卒業年',
          slantedText: true,
          slantedTextAngle: 45
        },
        vAxis: {
          title: '人数',
          minValue: 0
        },
        colors: ['#4285F4'],
        pointSize: 4
      };

      const chart = new google.visualization.LineChart(
        document.getElementById('line_chart')
      );

      chart.draw(chartData, options);
    }

    // エリアチャート描画
    function drawAreaChart() {
      const chartData = new google.visualization.DataTable();
      chartData.addColumn('string', '卒業年');
      chartData.addColumn('number', '人数');

      data.forEach(row => {
        chartData.addRow([row.graduationYear.toString(), row.count]);
      });

      const options = {
        title: '卒業年別人数累積ビュー',
        legend: { position: 'bottom' },
        chartArea: {width: '80%', height: '70%'},
        hAxis: {
          title: '卒業年',
          slantedText: true,
          slantedTextAngle: 45
        },
        vAxis: {
          title: '人数',
          minValue: 0
        },
        colors: ['#34A853'],
        isStacked: false
      };

      const chart = new google.visualization.AreaChart(
        document.getElementById('area_chart')
      );

      chart.draw(chartData, options);
    }

    // データテーブル表示
    function renderDataTable() {
      const tbody = document.getElementById('table-body');

      // 人数降順でソート（表示用）
      const sortedData = [...data].sort((a, b) => b.count - a.count);

      sortedData.forEach(row => {
        const tr = document.createElement('tr');

        // 年代判定
        const decade = Math.floor(row.graduationYear / 10) * 10;
        const decadeClass = \`decade-\${decade}\`;
        const decadeLabel = \`\${decade}年代\`;

        tr.innerHTML = \`
          <td><strong>\${row.graduationYear}年</strong></td>
          <td style="text-align: right;"><strong>\${row.count.toLocaleString()}</strong>名</td>
          <td style="text-align: right;">\${row.avgAge ? row.avgAge.toFixed(1) + '歳' : '－'}</td>
          <td><span class="decade-badge \${decadeClass}">\${decadeLabel}</span></td>
        \`;
        tbody.appendChild(tr);
      });
    }
  </script>
</body>
</html>
  `;
}
