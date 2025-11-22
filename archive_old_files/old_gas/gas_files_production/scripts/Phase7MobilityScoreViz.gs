/**
 * Phase 7 移動許容度スコアリング可視化
 *
 * 求職者ごとの移動許容度を定量化し、
 * ヒストグラム、円グラフ、散布図で可視化します。
 */

/**
 * 移動許容度分析表示（メニューから呼び出し）
 */
function showMobilityScoreAnalysis() {
  const ui = SpreadsheetApp.getUi();

  try {
    // データ読み込み
    const data = loadMobilityScoreData();

    if (!data || data.length === 0) {
      ui.alert(
        'データなし',
        'Phase7_MobilityScoreシートにデータがありません。\n' +
        '先に「Phase 7データ取り込み」を実行してください。',
        ui.ButtonSet.OK
      );
      return;
    }

    // HTML生成
    const html = generateMobilityScoreHTML(data);

    // ダイアログ表示
    const htmlOutput = HtmlService.createHtmlOutput(html)
      .setWidth(1200)
      .setHeight(800);

    ui.showModalDialog(htmlOutput, 'Phase 7: 移動許容度スコアリング分析');

  } catch (error) {
    ui.alert('エラー', `可視化中にエラーが発生しました:\n${error.message}`, ui.ButtonSet.OK);
    Logger.log(`移動許容度分析エラー: ${error.stack}`);
  }
}


/**
 * 移動許容度データ読み込み
 * @return {Array<Object>} データオブジェクトの配列
 */
function loadMobilityScoreData() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName('Phase7_MobilityScore');

  if (!sheet) {
    throw new Error('Phase7_MobilityScoreシートが見つかりません');
  }

  const lastRow = sheet.getLastRow();
  if (lastRow <= 1) {
    return [];
  }

  // データ範囲取得（ヘッダー除く）
  // サンプリング: データが多い場合は最大1000件まで
  const maxRows = Math.min(lastRow - 1, 1000);
  const range = sheet.getRange(2, 1, maxRows, 7);
  const values = range.getValues();

  // オブジェクト配列に変換
  const data = values.map(row => ({
    applicantId: row[0],           // 申請者ID
    desiredLocationCount: row[1],  // 希望地数
    maxDistanceKm: row[2],         // 最大移動距離km
    mobilityScore: row[3],         // 移動許容度スコア
    mobilityLevel: row[4],         // 移動許容度レベル
    mobilityLabel: row[5],         // 移動許容度
    residence: row[6]              // 居住地
  }));

  Logger.log(`移動許容度データ読み込み: ${data.length}件`);

  return data;
}


/**
 * 移動許容度分析HTML生成
 * @param {Array<Object>} data - データ配列
 * @return {string} HTML文字列
 */
function generateMobilityScoreHTML(data) {
  // データをJSON文字列化
  const dataJson = JSON.stringify(data);

  // 統計計算
  const stats = calculateMobilityStats(data);
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
    .stats-grid {
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
    .stat-card.level-A { background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); }
    .stat-card.level-B { background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); }
    .stat-card.level-C { background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); }
    .stat-card.level-D { background: linear-gradient(135deg, #a8a8a8 0%, #d0d0d0 100%); }
    .stat-label {
      font-size: 12px;
      opacity: 0.9;
      margin-bottom: 5px;
    }
    .stat-value {
      font-size: 28px;
      font-weight: bold;
    }
    .stat-sublabel {
      font-size: 14px;
      margin-top: 8px;
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
    #histogram_chart {
      width: 100%;
      height: 400px;
    }
    #pie_chart {
      width: 100%;
      height: 400px;
    }
    #scatter_chart {
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
  </style>
</head>
<body>
  <h1>🚗 Phase 7: 移動許容度スコアリング分析</h1>

  <div class="container">
    <h2>レベル別統計</h2>
    <div class="stats-grid" id="level-stats"></div>
  </div>

  <div class="charts-row">
    <div class="chart-container">
      <h2>スコア分布（ヒストグラム）</h2>
      <div id="histogram_chart"></div>
    </div>
    <div class="chart-container">
      <h2>レベル別割合</h2>
      <div id="pie_chart"></div>
    </div>
  </div>

  <div class="container">
    <h2>希望地数 × 最大移動距離（散布図）</h2>
    <div id="scatter_chart"></div>
  </div>

  <div class="container">
    <h2>居住地別平均スコア（TOP10）</h2>
    <table id="residence-table">
      <thead>
        <tr>
          <th>居住地</th>
          <th>平均スコア</th>
          <th>求職者数</th>
          <th>平均移動距離km</th>
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
      renderLevelStats();
      drawHistogram();
      drawPieChart();
      drawScatterChart();
      renderResidenceTable();
    }

    // レベル別統計表示
    function renderLevelStats() {
      const container = document.getElementById('level-stats');
      ['A', 'B', 'C', 'D'].forEach(level => {
        const stat = stats.byLevel[level] || {count: 0, avgScore: 0};
        const labels = {
          'A': '広域移動OK',
          'B': '中距離OK',
          'C': '近距離のみ',
          'D': '地元限定'
        };

        const card = document.createElement('div');
        card.className = \`stat-card level-\${level}\`;
        card.innerHTML = \`
          <div class="stat-label">レベル \${level}</div>
          <div class="stat-value">\${stat.count}名</div>
          <div class="stat-sublabel">\${labels[level]}</div>
          <div class="stat-label">平均: \${stat.avgScore.toFixed(1)}</div>
        \`;
        container.appendChild(card);
      });
    }

    // ヒストグラム描画
    function drawHistogram() {
      const chartData = new google.visualization.DataTable();
      chartData.addColumn('string', 'スコア範囲');
      chartData.addColumn('number', '求職者数');

      // 10刻みでヒストグラム作成
      const bins = {};
      for (let i = 0; i < 100; i += 10) {
        bins[\`\${i}-\${i + 10}\`] = 0;
      }

      data.forEach(row => {
        const binIndex = Math.floor(row.mobilityScore / 10) * 10;
        const binKey = \`\${binIndex}-\${binIndex + 10}\`;
        if (bins[binKey] !== undefined) {
          bins[binKey]++;
        }
      });

      Object.entries(bins).forEach(([range, count]) => {
        chartData.addRow([range, count]);
      });

      const options = {
        title: '移動許容度スコア分布',
        legend: {position: 'none'},
        hAxis: {title: 'スコア範囲'},
        vAxis: {title: '求職者数'},
        colors: ['#4285F4']
      };

      const chart = new google.visualization.ColumnChart(
        document.getElementById('histogram_chart')
      );

      chart.draw(chartData, options);
    }

    // 円グラフ描画
    function drawPieChart() {
      const chartData = new google.visualization.DataTable();
      chartData.addColumn('string', 'レベル');
      chartData.addColumn('number', '人数');

      const labels = {
        'A': '広域移動OK',
        'B': '中距離OK',
        'C': '近距離のみ',
        'D': '地元限定'
      };

      ['A', 'B', 'C', 'D'].forEach(level => {
        const stat = stats.byLevel[level] || {count: 0};
        chartData.addRow([labels[level], stat.count]);
      });

      const options = {
        title: '移動許容度レベル別割合',
        pieHole: 0.4,
        colors: ['#4facfe', '#43e97b', '#fa709a', '#a8a8a8']
      };

      const chart = new google.visualization.PieChart(
        document.getElementById('pie_chart')
      );

      chart.draw(chartData, options);
    }

    // 散布図描画
    function drawScatterChart() {
      const chartData = new google.visualization.DataTable();
      chartData.addColumn('number', '希望地数');
      chartData.addColumn('number', '最大移動距離km');

      // サンプリング（最大500件）
      const sampleData = data.slice(0, 500);

      sampleData.forEach(row => {
        chartData.addRow([
          row.desiredLocationCount,
          row.maxDistanceKm
        ]);
      });

      const options = {
        title: '希望地数 vs 最大移動距離',
        hAxis: {title: '希望地数'},
        vAxis: {title: '最大移動距離(km)'},
        legend: 'none',
        pointSize: 5,
        colors: ['#1a73e8']
      };

      const chart = new google.visualization.ScatterChart(
        document.getElementById('scatter_chart')
      );

      chart.draw(chartData, options);
    }

    // 居住地別テーブル表示
    function renderResidenceTable() {
      const tbody = document.getElementById('table-body');

      stats.byResidence.slice(0, 10).forEach(row => {
        const tr = document.createElement('tr');
        tr.innerHTML = \`
          <td>\${row.residence}</td>
          <td><strong>\${row.avgScore.toFixed(1)}</strong></td>
          <td>\${row.count}名</td>
          <td>\${row.avgDistance.toFixed(1)}km</td>
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
 * 移動許容度統計計算
 * @param {Array<Object>} data - データ配列
 * @return {Object} 統計情報
 */
function calculateMobilityStats(data) {
  // レベル別統計
  const levels = ['A', 'B', 'C', 'D'];
  const byLevel = {};

  levels.forEach(level => {
    const levelData = data.filter(row => row.mobilityLevel === level);
    const count = levelData.length;
    const avgScore = count > 0
      ? levelData.reduce((sum, row) => sum + row.mobilityScore, 0) / count
      : 0;

    byLevel[level] = {
      count: count,
      avgScore: avgScore
    };
  });

  // 居住地別統計
  const residenceMap = {};

  data.forEach(row => {
    if (!residenceMap[row.residence]) {
      residenceMap[row.residence] = {
        scores: [],
        distances: []
      };
    }
    residenceMap[row.residence].scores.push(row.mobilityScore);
    residenceMap[row.residence].distances.push(row.maxDistanceKm);
  });

  const byResidence = Object.entries(residenceMap).map(([residence, values]) => {
    const avgScore = values.scores.reduce((a, b) => a + b, 0) / values.scores.length;
    const avgDistance = values.distances.reduce((a, b) => a + b, 0) / values.distances.length;

    return {
      residence: residence,
      count: values.scores.length,
      avgScore: avgScore,
      avgDistance: avgDistance
    };
  });

  // 平均スコア降順でソート
  byResidence.sort((a, b) => b.avgScore - a.avgScore);

  return {
    byLevel: byLevel,
    byResidence: byResidence
  };
}
