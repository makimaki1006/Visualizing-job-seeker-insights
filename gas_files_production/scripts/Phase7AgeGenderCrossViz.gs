/**
 * Phase 7 年齢層×性別クロス分析可視化
 *
 * 地域ごとの年齢層・性別構成を可視化します。
 */

/**
 * 年齢層×性別クロス分析表示（メニューから呼び出し）
 */
function showAgeGenderCrossAnalysis() {
  const ui = SpreadsheetApp.getUi();

  try {
    // データ読み込み
    const data = loadAgeGenderCrossData();

    if (!data || data.length === 0) {
      ui.alert(
        'データなし',
        'Phase7_AgeGenderCrossシートにデータがありません。\n' +
        '先に「Phase 7自動インポート」を実行してください。',
        ui.ButtonSet.OK
      );
      return;
    }

    // HTML生成
    const html = generateAgeGenderCrossHTML(data);

    // ダイアログ表示
    const htmlOutput = HtmlService.createHtmlOutput(html)
      .setWidth(1200)
      .setHeight(800);

    ui.showModalDialog(htmlOutput, 'Phase 7: 年齢層×性別クロス分析');

  } catch (error) {
    ui.alert('エラー', `可視化中にエラーが発生しました:\n${error.message}`, ui.ButtonSet.OK);
    Logger.log(`年齢層×性別クロス分析エラー: ${error.stack}`);
  }
}


/**
 * 年齢層×性別クロスデータ読み込み
 * @return {Array<Object>} データオブジェクトの配列
 */
function loadAgeGenderCrossData() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName('Phase7_AgeGenderCross');

  if (!sheet) {
    throw new Error('Phase7_AgeGenderCrossシートが見つかりません');
  }

  const lastRow = sheet.getLastRow();
  if (lastRow <= 1) {
    return [];
  }

  // データ範囲取得（ヘッダー除く）
  const range = sheet.getRange(2, 1, lastRow - 1, 6);
  const values = range.getValues();

  // オブジェクト配列に変換
  const data = values.map(row => ({
    municipality: row[0],         // 市区町村
    totalJobseekers: row[1],      // 総求職者数
    dominantSegment: row[2],      // 支配的セグメント
    youngFemaleRate: row[3],      // 若年女性比率
    middleFemaleRate: row[4],     // 中年女性比率
    diversityScore: row[5]        // ダイバーシティスコア
  }));

  Logger.log(`年齢層×性別クロスデータ読み込み: ${data.length}件`);

  return data;
}


/**
 * 年齢層×性別クロスHTML生成
 * @param {Array<Object>} data - データ配列
 * @return {string} HTML文字列
 */
function generateAgeGenderCrossHTML(data) {
  // データをJSON文字列化
  const dataJson = JSON.stringify(data);

  // 統計計算
  const stats = calculateAgeGenderStats(data);
  const statsJson = JSON.stringify(stats);

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
    .charts-row {
      display: grid;
      grid-template-columns: 2fr 1fr;
      gap: 20px;
      margin-bottom: 20px;
    }
    .chart-container {
      background-color: white;
      padding: 20px;
      border-radius: 8px;
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    #stacked_bar_chart {
      width: 100%;
      height: 400px;
    }
    #diversity_chart {
      width: 100%;
      height: 400px;
    }
    #segment_pie_chart {
      width: 100%;
      height: 400px;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      margin-top: 10px;
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
    }
    tr:hover {
      background-color: #f5f5f5;
    }
    .diversity-high { background-color: #d4edda; }
    .diversity-medium { background-color: #fff3cd; }
    .diversity-low { background-color: #f8d7da; }
  </style>
</head>
<body>
  <h1>👥 Phase 7: 年齢層×性別クロス分析</h1>

  <div class="charts-row">
    <div class="chart-container">
      <h2>地域別構成（積み上げ棒グラフ）</h2>
      <div id="stacked_bar_chart"></div>
    </div>
    <div class="chart-container">
      <h2>支配的セグメント分布</h2>
      <div id="segment_pie_chart"></div>
    </div>
  </div>

  <div class="container">
    <h2>ダイバーシティスコア分析</h2>
    <div id="diversity_chart"></div>
  </div>

  <div class="container">
    <h2>地域別詳細データ</h2>
    <table id="data-table">
      <thead>
        <tr>
          <th>市区町村</th>
          <th>求職者数</th>
          <th>支配的セグメント</th>
          <th>若年女性比率</th>
          <th>中年女性比率</th>
          <th>ダイバーシティスコア</th>
        </tr>
      </thead>
      <tbody id="table-body"></tbody>
    </table>
  </div>

  <script type="text/javascript">
    const data = ${dataJson};
    const stats = ${statsJson};

    // Google Charts読み込み
    google.charts.load('current', {'packages':['corechart']});
    google.charts.setOnLoadCallback(drawCharts);

    function drawCharts() {
      drawStackedBarChart();
      drawSegmentPieChart();
      drawDiversityChart();
      renderDataTable();
    }

    // 積み上げ棒グラフ描画
    function drawStackedBarChart() {
      const chartData = new google.visualization.DataTable();
      chartData.addColumn('string', '市区町村');
      chartData.addColumn('number', '若年女性');
      chartData.addColumn('number', '中年女性');
      chartData.addColumn('number', 'その他');

      // 上位10地域のみ表示
      const top10 = [...data]
        .sort((a, b) => b.totalJobseekers - a.totalJobseekers)
        .slice(0, 10);

      top10.forEach(row => {
        const youngFemale = row.youngFemaleRate * row.totalJobseekers;
        const middleFemale = row.middleFemaleRate * row.totalJobseekers;
        const others = row.totalJobseekers - youngFemale - middleFemale;

        chartData.addRow([
          row.municipality,
          Math.round(youngFemale),
          Math.round(middleFemale),
          Math.round(others)
        ]);
      });

      const options = {
        title: '地域別人材構成（TOP10）',
        isStacked: 'percent',
        hAxis: {title: '構成比（%）'},
        vAxis: {title: '市区町村'},
        colors: ['#4285F4', '#34A853', '#FBBC04'],
        chartArea: {width: '60%'}
      };

      const chart = new google.visualization.BarChart(
        document.getElementById('stacked_bar_chart')
      );

      chart.draw(chartData, options);
    }

    // 支配的セグメント円グラフ描画
    function drawSegmentPieChart() {
      const chartData = new google.visualization.DataTable();
      chartData.addColumn('string', 'セグメント');
      chartData.addColumn('number', '地域数');

      Object.entries(stats.segmentDistribution).forEach(([segment, count]) => {
        chartData.addRow([segment, count]);
      });

      const options = {
        title: '支配的セグメント別地域数',
        pieHole: 0.4,
        colors: ['#4285F4', '#34A853', '#FBBC04', '#EA4335', '#9E9E9E']
      };

      const chart = new google.visualization.PieChart(
        document.getElementById('segment_pie_chart')
      );

      chart.draw(chartData, options);
    }

    // ダイバーシティスコアチャート描画
    function drawDiversityChart() {
      const chartData = new google.visualization.DataTable();
      chartData.addColumn('string', '市区町村');
      chartData.addColumn('number', 'ダイバーシティスコア');

      // スコア降順でソート
      const sortedData = [...data].sort((a, b) => b.diversityScore - a.diversityScore);

      sortedData.forEach(row => {
        chartData.addRow([row.municipality, row.diversityScore]);
      });

      const options = {
        title: 'ダイバーシティスコア（高いほど多様性が高い）',
        hAxis: {title: 'ダイバーシティスコア', minValue: 0, maxValue: 1},
        vAxis: {title: '市区町村'},
        colors: ['#34A853'],
        chartArea: {width: '60%'},
        legend: {position: 'none'}
      };

      const chart = new google.visualization.BarChart(
        document.getElementById('diversity_chart')
      );

      chart.draw(chartData, options);
    }

    // データテーブル表示
    function renderDataTable() {
      const tbody = document.getElementById('table-body');

      // 求職者数降順でソート
      const sortedData = [...data].sort((a, b) => b.totalJobseekers - a.totalJobseekers);

      sortedData.forEach(row => {
        const tr = document.createElement('tr');

        // ダイバーシティスコアで行の背景色を変更
        let diversityClass = '';
        if (row.diversityScore >= 0.7) {
          diversityClass = 'diversity-high';
        } else if (row.diversityScore >= 0.5) {
          diversityClass = 'diversity-medium';
        } else {
          diversityClass = 'diversity-low';
        }

        tr.className = diversityClass;
        tr.innerHTML = \`
          <td><strong>\${row.municipality}</strong></td>
          <td>\${row.totalJobseekers}名</td>
          <td>\${row.dominantSegment}</td>
          <td>\${(row.youngFemaleRate * 100).toFixed(1)}%</td>
          <td>\${(row.middleFemaleRate * 100).toFixed(1)}%</td>
          <td><strong>\${row.diversityScore.toFixed(3)}</strong></td>
        \`;
        tbody.appendChild(tr);
      });
    }
  </script>
</body>
</html>
  `;
}


/**
 * 年齢層×性別統計計算
 * @param {Array<Object>} data - データ配列
 * @return {Object} 統計情報
 */
function calculateAgeGenderStats(data) {
  // 支配的セグメント分布
  const segmentDistribution = {};

  data.forEach(row => {
    const segment = row.dominantSegment;
    if (!segmentDistribution[segment]) {
      segmentDistribution[segment] = 0;
    }
    segmentDistribution[segment]++;
  });

  return {
    segmentDistribution: segmentDistribution
  };
}
