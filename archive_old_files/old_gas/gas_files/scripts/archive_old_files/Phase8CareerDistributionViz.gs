/**
 * Phase 8 キャリア分布可視化
 *
 * キャリア（職歴）の分布を可視化します。
 */

/**
 * キャリア分布表示（メニューから呼び出し）
 */
function showCareerDistribution() {
  const ui = SpreadsheetApp.getUi();

  try {
    // データ読み込み
    const data = loadCareerDistData();

    if (!data || data.length === 0) {
      ui.alert(
        'データなし',
        'P8_CareerDistシートにデータがありません。\n' +
        '先に「Python結果CSVを取り込み」を実行してください。',
        ui.ButtonSet.OK
      );
      return;
    }

    // HTML生成
    const html = generateCareerDistHTML(data);

    // ダイアログ表示
    const htmlOutput = HtmlService.createHtmlOutput(html)
      .setWidth(1200)
      .setHeight(800);

    ui.showModalDialog(htmlOutput, 'Phase 8: キャリア分布分析');

  } catch (error) {
    ui.alert('エラー', `可視化中にエラーが発生しました:\n${error.message}`, ui.ButtonSet.OK);
    Logger.log(`キャリア分布エラー: ${error.stack}`);
  }
}


/**
 * キャリア分布データ読み込み
 * @return {Array<Object>} データオブジェクトの配列
 */
function loadCareerDistData() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName('P8_CareerDist');

  if (!sheet) {
    throw new Error('P8_CareerDistシートが見つかりません');
  }

  const lastRow = sheet.getLastRow();
  if (lastRow <= 1) {
    return [];
  }

  // データ範囲取得（ヘッダー除く）
  const range = sheet.getRange(2, 1, lastRow - 1, 2);
  const values = range.getValues();

  // オブジェクト配列に変換
  const data = values
    .filter(row => row[0] && row[1] > 0)  // 空行とゼロ件を除外
    .map(row => ({
      career: String(row[0]),  // キャリア
      count: Number(row[1])    // 件数
    }));

  Logger.log(`キャリア分布データ読み込み: ${data.length}件`);

  return data;
}


/**
 * キャリア分布HTML生成
 * @param {Array<Object>} data - データ配列
 * @return {string} HTML文字列
 */
function generateCareerDistHTML(data) {
  // データをJSON文字列化（上位100件のみ）
  const top100Data = data
    .sort((a, b) => b.count - a.count)
    .slice(0, 100);
  const dataJson = JSON.stringify(top100Data);

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
      height: 600px;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      margin-top: 10px;
      font-size: 14px;
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
    .rank-badge {
      display: inline-block;
      width: 30px;
      height: 30px;
      background-color: #ffd700;
      color: #333;
      border-radius: 50%;
      text-align: center;
      line-height: 30px;
      font-weight: bold;
      margin-right: 10px;
    }
    .note {
      background-color: #fff3cd;
      border-left: 4px solid #ffc107;
      padding: 15px;
      margin-top: 10px;
      border-radius: 4px;
    }
  </style>
</head>
<body>
  <h1>💼 Phase 8: キャリア分布分析</h1>

  <div class="container">
    <h2>統計サマリー</h2>
    <div class="stats-summary" id="stats-summary"></div>
  </div>

  <div class="container">
    <h2>キャリア別人数（TOP100横棒グラフ）</h2>
    <div class="note">
      <strong>📊 表示説明:</strong> 全${data.length.toLocaleString()}種類のキャリアのうち、人数が多い上位100種類を表示しています。
    </div>
    <div id="bar_chart"></div>
  </div>

  <div class="container">
    <h2>キャリア別詳細データ（TOP100）</h2>
    <div class="table-container">
      <table id="data-table">
        <thead>
          <tr>
            <th style="width: 80px;">順位</th>
            <th>キャリア（職歴）</th>
            <th style="width: 120px;">人数</th>
          </tr>
        </thead>
        <tbody id="table-body"></tbody>
      </table>
    </div>
  </div>

  <script type="text/javascript">
    const data = ${dataJson};
    const totalCareerTypes = ${data.length};

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

      // 総キャリア種類数
      const totalTypes = totalCareerTypes;

      // 総人数
      const totalCount = data.reduce((sum, row) => sum + row.count, 0);

      // 平均人数
      const avgCount = totalCount / totalTypes;

      const stats = [
        {label: 'キャリア種類数', value: totalTypes.toLocaleString(), unit: '種類'},
        {label: '総人数', value: totalCount.toLocaleString(), unit: '名'},
        {label: '平均人数/種類', value: Math.round(avgCount).toLocaleString(), unit: '名'}
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
      chartData.addColumn('string', 'キャリア');
      chartData.addColumn('number', '人数');

      // データを人数降順でソート（既にソート済み）
      data.forEach(row => {
        // キャリア名が長い場合は省略
        const careerLabel = row.career.length > 40
          ? row.career.substring(0, 40) + '...'
          : row.career;
        chartData.addRow([careerLabel, row.count]);
      });

      const options = {
        title: 'キャリア別人数（TOP100）',
        chartArea: {width: '50%', height: '85%'},
        hAxis: {
          title: '人数',
          minValue: 0
        },
        vAxis: {
          title: 'キャリア',
          textStyle: {fontSize: 10}
        },
        colors: ['#4285F4'],
        legend: {position: 'none'},
        height: 600
      };

      const chart = new google.visualization.BarChart(
        document.getElementById('bar_chart')
      );

      chart.draw(chartData, options);
    }

    // データテーブル表示
    function renderDataTable() {
      const tbody = document.getElementById('table-body');

      data.forEach((row, index) => {
        const tr = document.createElement('tr');

        // 順位バッジ
        const rankHtml = index < 3
          ? \`<span class="rank-badge">\${index + 1}</span>\`
          : \`<span style="font-weight: bold;">\${index + 1}</span>\`;

        tr.innerHTML = \`
          <td style="text-align: center;">\${rankHtml}</td>
          <td><strong>\${row.career}</strong></td>
          <td style="text-align: right;"><strong>\${row.count.toLocaleString()}</strong>名</td>
        \`;
        tbody.appendChild(tr);
      });
    }
  </script>
</body>
</html>
  `;
}
