/**
 * Phase 7 資格別人材分布可視化
 *
 * 資格カテゴリごとの地域分布を可視化します。
 */

/**
 * 資格別人材分布表示（メニューから呼び出し）
 */
function showQualificationDistribution() {
  const ui = SpreadsheetApp.getUi();

  try {
    // データ読み込み
    const data = loadQualificationDistData();

    if (!data || data.length === 0) {
      ui.alert(
        'データなし',
        'Phase7_QualificationDistシートにデータがありません。\n' +
        '先に「Phase 7自動インポート」を実行してください。',
        ui.ButtonSet.OK
      );
      return;
    }

    // HTML生成
    const html = generateQualificationDistHTML(data);

    // ダイアログ表示
    const htmlOutput = HtmlService.createHtmlOutput(html)
      .setWidth(1000)
      .setHeight(700);

    ui.showModalDialog(htmlOutput, 'Phase 7: 資格別人材分布分析');

  } catch (error) {
    ui.alert('エラー', `可視化中にエラーが発生しました:\n${error.message}`, ui.ButtonSet.OK);
    Logger.log(`資格別人材分布エラー: ${error.stack}`);
  }
}


/**
 * 資格別人材分布データ読み込み
 * @return {Array<Object>} データオブジェクトの配列
 */
function loadQualificationDistData() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName('Phase7_QualificationDist');

  if (!sheet) {
    throw new Error('Phase7_QualificationDistシートが見つかりません');
  }

  const lastRow = sheet.getLastRow();
  if (lastRow <= 1) {
    return [];
  }

  // データ範囲取得（ヘッダー除く）
  const range = sheet.getRange(2, 1, lastRow - 1, 4);
  const values = range.getValues();

  // オブジェクト配列に変換
  const data = values.map(row => ({
    category: row[0],        // 資格カテゴリ
    totalHolders: row[1],    // 総保有者数
    top3Distribution: row[2], // 分布TOP3
    rareRegions: row[3]      // 希少地域TOP3
  }));

  Logger.log(`資格別人材分布データ読み込み: ${data.length}件`);

  return data;
}


/**
 * 資格別人材分布HTML生成
 * @param {Array<Object>} data - データ配列
 * @return {string} HTML文字列
 */
function generateQualificationDistHTML(data) {
  // データをJSON文字列化
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
      grid-template-columns: repeat(3, 1fr);
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
      font-size: 32px;
      font-weight: bold;
    }
    #bar_chart {
      width: 100%;
      height: 500px;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      margin-top: 10px;
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
    .rare-badge {
      display: inline-block;
      padding: 4px 8px;
      background-color: #ff6b6b;
      color: white;
      border-radius: 4px;
      font-size: 12px;
      margin-left: 5px;
    }
  </style>
</head>
<body>
  <h1>🎓 Phase 7: 資格別人材分布分析</h1>

  <div class="container">
    <h2>統計サマリー</h2>
    <div class="stats-summary" id="stats-summary"></div>
  </div>

  <div class="container">
    <h2>資格カテゴリ別保有者数（横棒グラフ）</h2>
    <div id="bar_chart"></div>
  </div>

  <div class="container">
    <h2>資格別詳細データ</h2>
    <table id="data-table">
      <thead>
        <tr>
          <th>資格カテゴリ</th>
          <th>総保有者数</th>
          <th>分布TOP3</th>
          <th>希少地域TOP3</th>
        </tr>
      </thead>
      <tbody id="table-body"></tbody>
    </table>
  </div>

  <script type="text/javascript">
    const data = ${dataJson};

    // Google Charts読み込み
    google.charts.load('current', {'packages':['corechart']});
    google.charts.setOnLoadCallback(drawCharts);

    function drawCharts() {
      renderStatsSummary();
      drawBarChart();
      renderDataTable();
    }

    // 統計サマリー表示
    function renderStatsSummary() {
      const container = document.getElementById('stats-summary');

      // 総資格カテゴリ数
      const totalCategories = data.length;

      // 総保有者数
      const totalHolders = data.reduce((sum, row) => sum + row.totalHolders, 0);

      // 平均保有者数
      const avgHolders = totalHolders / totalCategories;

      const stats = [
        {label: '資格カテゴリ数', value: totalCategories, unit: '種類'},
        {label: '総保有者数', value: totalHolders.toLocaleString(), unit: '名'},
        {label: '平均保有者数', value: Math.round(avgHolders).toLocaleString(), unit: '名'}
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

    // 横棒グラフ描画
    function drawBarChart() {
      const chartData = new google.visualization.DataTable();
      chartData.addColumn('string', '資格カテゴリ');
      chartData.addColumn('number', '保有者数');

      // データを保有者数降順でソート
      const sortedData = [...data].sort((a, b) => b.totalHolders - a.totalHolders);

      sortedData.forEach(row => {
        chartData.addRow([row.category, row.totalHolders]);
      });

      const options = {
        title: '資格カテゴリ別保有者数',
        chartArea: {width: '60%'},
        hAxis: {
          title: '保有者数',
          minValue: 0
        },
        vAxis: {
          title: '資格カテゴリ'
        },
        colors: ['#4285F4'],
        legend: {position: 'none'}
      };

      const chart = new google.visualization.BarChart(
        document.getElementById('bar_chart')
      );

      chart.draw(chartData, options);
    }

    // データテーブル表示
    function renderDataTable() {
      const tbody = document.getElementById('table-body');

      // 保有者数降順でソート
      const sortedData = [...data].sort((a, b) => b.totalHolders - a.totalHolders);

      sortedData.forEach(row => {
        const tr = document.createElement('tr');

        // 希少地域に警告バッジを追加
        const rareRegionsHtml = row.rareRegions
          ? \`\${row.rareRegions} <span class="rare-badge">要注目</span>\`
          : '－';

        tr.innerHTML = \`
          <td><strong>\${row.category}</strong></td>
          <td>\${row.totalHolders.toLocaleString()}名</td>
          <td>\${row.top3Distribution || '－'}</td>
          <td>\${rareRegionsHtml}</td>
        \`;
        tbody.appendChild(tr);
      });
    }
  </script>
</body>
</html>
  `;
}
