/**
 * Phase 8 キャリア×年齢層クロス分析可視化
 *
 * キャリアと年齢層のクロス集計を可視化します。
 */

/**
 * キャリア×年齢クロス分析表示（メニューから呼び出し）
 */
function showCareerAgeCross() {
  const ui = SpreadsheetApp.getUi();

  try {
    // データ読み込み
    const data = loadCareerAgeCrossData();

    if (!data || data.length === 0) {
      ui.alert(
        'データなし',
        'P8_CareerAgeCrossシートにデータがありません。\n' +
        '先に「Python結果CSVを取り込み」を実行してください。',
        ui.ButtonSet.OK
      );
      return;
    }

    // HTML生成
    const html = generateCareerAgeCrossHTML(data);

    // ダイアログ表示
    const htmlOutput = HtmlService.createHtmlOutput(html)
      .setWidth(1400)
      .setHeight(900);

    ui.showModalDialog(htmlOutput, 'Phase 8: キャリア×年齢層クロス分析');

  } catch (error) {
    ui.alert('エラー', `可視化中にエラーが発生しました:\n${error.message}`, ui.ButtonSet.OK);
    Logger.log(`キャリア×年齢クロス分析エラー: ${error.stack}`);
  }
}


/**
 * キャリア×年齢クロスデータ読み込み
 * @return {Array<Object>} データオブジェクトの配列
 */
function loadCareerAgeCrossData() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName('P8_CareerAgeCross');

  if (!sheet) {
    throw new Error('P8_CareerAgeCrossシートが見つかりません');
  }

  const lastRow = sheet.getLastRow();
  if (lastRow <= 1) {
    return [];
  }

  // データ範囲取得（ヘッダー除く）
  const range = sheet.getRange(2, 1, lastRow - 1, 5);
  const values = range.getValues();

  // オブジェクト配列に変換
  const data = values
    .filter(row => row[0] && row[1] && row[2] > 0)
    .map(row => ({
      career: String(row[0]),
      ageGroup: String(row[1]),
      count: Number(row[2]),
      avgAge: row[3] ? Number(row[3]) : null,
      avgQualifications: row[4] ? Number(row[4]) : null
    }));

  Logger.log(`キャリア×年齢クロスデータ読み込み: ${data.length}件`);

  return data;
}


/**
 * キャリア×年齢クロスHTML生成
 * @param {Array<Object>} data - データ配列
 * @return {string} HTML文字列
 */
function generateCareerAgeCrossHTML(data) {
  // キャリア別に合計件数を計算してTOP30を抽出
  const careerTotals = {};
  data.forEach(row => {
    if (!careerTotals[row.career]) {
      careerTotals[row.career] = 0;
    }
    careerTotals[row.career] += row.count;
  });

  const top30Careers = Object.entries(careerTotals)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 30)
    .map(entry => entry[0]);

  // TOP30キャリアのデータのみ抽出
  const top30Data = data.filter(row => top30Careers.includes(row.career));

  const dataJson = JSON.stringify(top30Data);
  const totalCount = data.length;

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
    #grouped_bar_chart {
      width: 100%;
      height: 700px;
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
    .note {
      background-color: #fff3cd;
      border-left: 4px solid #ffc107;
      padding: 15px;
      margin-top: 10px;
      border-radius: 4px;
    }
    .age-badge {
      display: inline-block;
      padding: 4px 8px;
      border-radius: 4px;
      font-size: 11px;
      font-weight: bold;
      margin-right: 5px;
    }
    .age-20 { background-color: #e3f2fd; color: #1976d2; }
    .age-30 { background-color: #f3e5f5; color: #7b1fa2; }
    .age-40 { background-color: #fff3e0; color: #e65100; }
    .age-50 { background-color: #fce4ec; color: #c2185b; }
    .age-60 { background-color: #f1f8e9; color: #558b2f; }
    .age-70 { background-color: #e0f2f1; color: #00695c; }
  </style>
</head>
<body>
  <h1>💼📊 Phase 8: キャリア×年齢層クロス分析</h1>

  <div class="container">
    <h2>統計サマリー</h2>
    <div class="stats-summary" id="stats-summary"></div>
  </div>

  <div class="container">
    <h2>キャリア×年齢層グループ化グラフ（TOP30）</h2>
    <div class="note">
      <strong>📊 表示説明:</strong> 全${totalCount.toLocaleString()}件のデータから、人数が多い上位30キャリアを抽出し、年齢層別に色分けして表示しています。
    </div>
    <div id="grouped_bar_chart"></div>
  </div>

  <div class="container">
    <h2>キャリア×年齢層詳細データ（TOP30）</h2>
    <div class="table-container">
      <table id="data-table">
        <thead>
          <tr>
            <th style="width: 40%;">キャリア</th>
            <th style="width: 15%;">年齢層</th>
            <th style="width: 12%;">人数</th>
            <th style="width: 12%;">平均年齢</th>
            <th style="width: 12%;">平均資格数</th>
          </tr>
        </thead>
        <tbody id="table-body"></tbody>
      </table>
    </div>
  </div>

  <script type="text/javascript">
    const data = ${dataJson};
    const totalDataCount = ${totalCount};

    // 年齢層の順序定義
    const ageGroupOrder = ['20代', '30代', '40代', '50代', '60代', '70歳以上'];

    // Google Charts読み込み
    google.charts.load('current', {'packages':['corechart']});
    google.charts.setOnLoadCallback(drawCharts);

    function drawCharts() {
      renderStatsSummary();
      drawGroupedBarChart();
      renderDataTable();
    }

    // 統計サマリー表示
    function renderStatsSummary() {
      const container = document.getElementById('stats-summary');

      // キャリア種類数（TOP30）
      const uniqueCareers = [...new Set(data.map(d => d.career))].length;

      // 総人数（TOP30の合計）
      const totalCount = data.reduce((sum, row) => sum + row.count, 0);

      // 年齢層数
      const uniqueAgeGroups = [...new Set(data.map(d => d.ageGroup))].length;

      // 平均年齢
      const avgAge = data.reduce((sum, row) => sum + (row.avgAge || 0) * row.count, 0) / totalCount;

      const stats = [
        {label: 'TOP30キャリア数', value: uniqueCareers, unit: '種類'},
        {label: '総人数（TOP30）', value: totalCount.toLocaleString(), unit: '名'},
        {label: '年齢層数', value: uniqueAgeGroups, unit: 'グループ'},
        {label: '平均年齢', value: Math.round(avgAge), unit: '歳'}
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

    // グループ化横棒グラフ描画
    function drawGroupedBarChart() {
      // データをキャリア別にピボット
      const careerMap = {};
      data.forEach(row => {
        if (!careerMap[row.career]) {
          careerMap[row.career] = {};
          ageGroupOrder.forEach(ag => {
            careerMap[row.career][ag] = 0;
          });
        }
        careerMap[row.career][row.ageGroup] = row.count;
      });

      // キャリア別合計でソート
      const sortedCareers = Object.entries(careerMap)
        .map(([career, ageData]) => ({
          career,
          total: Object.values(ageData).reduce((sum, val) => sum + val, 0),
          ageData
        }))
        .sort((a, b) => b.total - a.total);

      // Google Charts用データテーブル作成
      const chartData = new google.visualization.DataTable();
      chartData.addColumn('string', 'キャリア');
      ageGroupOrder.forEach(ag => {
        chartData.addColumn('number', ag);
      });

      sortedCareers.forEach(item => {
        const careerLabel = item.career.length > 35
          ? item.career.substring(0, 35) + '...'
          : item.career;
        const row = [careerLabel];
        ageGroupOrder.forEach(ag => {
          row.push(item.ageData[ag] || 0);
        });
        chartData.addRow(row);
      });

      const options = {
        title: 'キャリア×年齢層グループ化横棒グラフ（TOP30）',
        chartArea: {width: '50%', height: '85%'},
        hAxis: {
          title: '人数',
          minValue: 0
        },
        vAxis: {
          title: 'キャリア',
          textStyle: {fontSize: 10}
        },
        isStacked: false,
        legend: {position: 'top', maxLines: 2},
        colors: ['#4285F4', '#AA46BE', '#F4B400', '#DB4437', '#0F9D58', '#00ACC1'],
        height: 700
      };

      const chart = new google.visualization.BarChart(
        document.getElementById('grouped_bar_chart')
      );

      chart.draw(chartData, options);
    }

    // データテーブル表示
    function renderDataTable() {
      const tbody = document.getElementById('table-body');

      // キャリア別にグループ化してソート
      const careerGroups = {};
      data.forEach(row => {
        if (!careerGroups[row.career]) {
          careerGroups[row.career] = [];
        }
        careerGroups[row.career].push(row);
      });

      // キャリア別合計でソート
      const sortedCareerEntries = Object.entries(careerGroups)
        .map(([career, rows]) => ({
          career,
          total: rows.reduce((sum, r) => sum + r.count, 0),
          rows
        }))
        .sort((a, b) => b.total - a.total);

      sortedCareerEntries.forEach(careerEntry => {
        // 年齢層順にソート
        const sortedRows = careerEntry.rows.sort((a, b) => {
          return ageGroupOrder.indexOf(a.ageGroup) - ageGroupOrder.indexOf(b.ageGroup);
        });

        sortedRows.forEach((row, index) => {
          const tr = document.createElement('tr');

          // 年齢層バッジのクラス決定
          const ageBadgeClass = row.ageGroup.includes('20') ? 'age-20' :
                                 row.ageGroup.includes('30') ? 'age-30' :
                                 row.ageGroup.includes('40') ? 'age-40' :
                                 row.ageGroup.includes('50') ? 'age-50' :
                                 row.ageGroup.includes('60') ? 'age-60' : 'age-70';

          tr.innerHTML = \`
            <td>\${index === 0 ? '<strong>' + row.career + '</strong>' : ''}</td>
            <td><span class="age-badge \${ageBadgeClass}">\${row.ageGroup}</span></td>
            <td style="text-align: right;"><strong>\${row.count.toLocaleString()}</strong>名</td>
            <td style="text-align: right;">\${row.avgAge ? row.avgAge.toFixed(1) + '歳' : '－'}</td>
            <td style="text-align: right;">\${row.avgQualifications !== null ? row.avgQualifications.toFixed(1) + '個' : '－'}</td>
          \`;
          tbody.appendChild(tr);
        });
      });
    }
  </script>
</body>
</html>
  `;
}
