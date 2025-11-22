/**
 * Phase 10 緊急度×就業状態クロス分析可視化
 *
 * 緊急度ランクと就業状態のクロス集計を可視化します。
 */

/**
 * 緊急度×就業状態クロス分析表示（メニューから呼び出し）
 */
function showUrgencyEmploymentCross() {
  const ui = SpreadsheetApp.getUi();

  try {
    // データ読み込み
    const data = loadUrgencyEmploymentCrossData();

    if (!data || data.length === 0) {
      ui.alert(
        'データなし',
        'P10_UrgencyEmpシートにデータがありません。\n' +
        '先に「Python結果CSVを取り込み」を実行してください。',
        ui.ButtonSet.OK
      );
      return;
    }

    // HTML生成
    const html = generateUrgencyEmploymentCrossHTML(data);

    // ダイアログ表示
    const htmlOutput = HtmlService.createHtmlOutput(html)
      .setWidth(1400)
      .setHeight(900);

    ui.showModalDialog(htmlOutput, 'Phase 10: 緊急度×就業状態クロス分析');

  } catch (error) {
    ui.alert('エラー', `可視化中にエラーが発生しました:\n${error.message}`, ui.ButtonSet.OK);
    Logger.log(`緊急度×就業状態クロス分析エラー: ${error.stack}`);
  }
}


/**
 * 緊急度×就業状態クロスデータ読み込み
 * @return {Array<Object>} データオブジェクトの配列
 */
function loadUrgencyEmploymentCrossData() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName('P10_UrgencyEmp');

  if (!sheet) {
    throw new Error('P10_UrgencyEmpシートが見つかりません');
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
      urgencyRank: String(row[0]),
      employmentStatus: String(row[1]),
      count: Number(row[2]),
      avgAge: row[3] ? Number(row[3]) : null,
      avgUrgencyScore: row[4] ? Number(row[4]) : null
    }));

  Logger.log(`緊急度×就業状態クロスデータ読み込み: ${data.length}件`);

  return data;
}


/**
 * 緊急度×就業状態クロスHTML生成
 * @param {Array<Object>} data - データ配列
 * @return {string} HTML文字列
 */
function generateUrgencyEmploymentCrossHTML(data) {
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
    #grouped_column_chart {
      width: 100%;
      height: 600px;
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
    .urgency-badge {
      display: inline-block;
      padding: 4px 8px;
      border-radius: 12px;
      font-weight: bold;
      font-size: 11px;
      margin-right: 5px;
    }
    .urgency-A { background-color: #dc3545; color: white; }
    .urgency-B { background-color: #ffc107; color: #333; }
    .urgency-C { background-color: #17a2b8; color: white; }
    .urgency-D { background-color: #6c757d; color: white; }
    .employment-badge {
      display: inline-block;
      padding: 4px 8px;
      border-radius: 4px;
      font-size: 11px;
      font-weight: bold;
    }
    .employment-在学中 { background-color: #e3f2fd; color: #1976d2; }
    .employment-就業中 { background-color: #f1f8e9; color: #558b2f; }
    .employment-離職中 { background-color: #fce4ec; color: #c2185b; }
  </style>
</head>
<body>
  <h1>🚀💼 Phase 10: 緊急度×就業状態クロス分析</h1>

  <div class="container">
    <h2>統計サマリー</h2>
    <div class="stats-summary" id="stats-summary"></div>
  </div>

  <div class="container">
    <h2>緊急度×就業状態グループ化縦棒グラフ</h2>
    <div id="grouped_column_chart"></div>
  </div>

  <div class="container">
    <h2>緊急度×就業状態詳細データ</h2>
    <div class="table-container">
      <table id="data-table">
        <thead>
          <tr>
            <th style="width: 25%;">緊急度ランク</th>
            <th style="width: 20%;">就業状態</th>
            <th style="width: 15%;">人数</th>
            <th style="width: 15%;">平均年齢</th>
            <th style="width: 25%;">平均緊急度スコア</th>
          </tr>
        </thead>
        <tbody id="table-body"></tbody>
      </table>
    </div>
  </div>

  <script type="text/javascript">
    const data = ${dataJson};

    // 緊急度・就業状態順序定義
    const urgencyOrder = ['A: 高い', 'B: 中程度', 'C: やや低い', 'D: 低い'];
    const employmentOrder = ['在学中', '就業中', '離職中'];

    // Google Charts読み込み
    google.charts.load('current', {'packages':['corechart']});
    google.charts.setOnLoadCallback(drawCharts);

    function drawCharts() {
      renderStatsSummary();
      drawGroupedColumnChart();
      renderDataTable();
    }

    // 統計サマリー表示
    function renderStatsSummary() {
      const container = document.getElementById('stats-summary');

      // 緊急度ランク数
      const uniqueUrgency = [...new Set(data.map(d => d.urgencyRank))].length;

      // 総人数
      const totalCount = data.reduce((sum, row) => sum + row.count, 0);

      // 就業状態数
      const uniqueEmployment = [...new Set(data.map(d => d.employmentStatus))].length;

      // 平均緊急度スコア
      const avgScore = data.reduce((sum, row) => sum + (row.avgUrgencyScore || 0) * row.count, 0) / totalCount;

      const stats = [
        {label: '緊急度ランク数', value: uniqueUrgency, unit: 'ランク'},
        {label: '総人数', value: totalCount.toLocaleString(), unit: '名'},
        {label: '就業状態数', value: uniqueEmployment, unit: '種類'},
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

    // グループ化縦棒グラフ描画
    function drawGroupedColumnChart() {
      // データを就業状態別にピボット
      const employmentMap = {};
      employmentOrder.forEach(emp => {
        employmentMap[emp] = {};
        urgencyOrder.forEach(ur => {
          employmentMap[emp][ur] = 0;
        });
      });

      data.forEach(row => {
        if (employmentMap[row.employmentStatus] && urgencyOrder.includes(row.urgencyRank)) {
          employmentMap[row.employmentStatus][row.urgencyRank] = row.count;
        }
      });

      // Google Charts用データテーブル作成
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
        hAxis: {
          title: '就業状態'
        },
        vAxis: {
          title: '人数',
          minValue: 0
        },
        isStacked: false,
        legend: {position: 'top', maxLines: 2},
        colors: ['#dc3545', '#ffc107', '#17a2b8', '#6c757d'],
        bar: {groupWidth: '75%'}
      };

      const chart = new google.visualization.ColumnChart(
        document.getElementById('grouped_column_chart')
      );

      chart.draw(chartData, options);
    }

    // データテーブル表示
    function renderDataTable() {
      const tbody = document.getElementById('table-body');

      // 緊急度→就業状態の順にソート
      const sortedData = data.sort((a, b) => {
        const urgencyDiff = urgencyOrder.indexOf(a.urgencyRank) - urgencyOrder.indexOf(b.urgencyRank);
        if (urgencyDiff !== 0) return urgencyDiff;
        return employmentOrder.indexOf(a.employmentStatus) - employmentOrder.indexOf(b.employmentStatus);
      });

      let prevUrgency = null;

      sortedData.forEach(row => {
        const tr = document.createElement('tr');

        // 緊急度バッジのクラス決定
        const urgencyBadgeClass = row.urgencyRank.startsWith('A') ? 'urgency-A' :
                                   row.urgencyRank.startsWith('B') ? 'urgency-B' :
                                   row.urgencyRank.startsWith('C') ? 'urgency-C' : 'urgency-D';

        // 就業状態バッジのクラス決定
        const empBadgeClass = 'employment-' + row.employmentStatus;

        // 同じ緊急度が続く場合は空欄に
        const urgencyHtml = row.urgencyRank !== prevUrgency
          ? \`<span class="urgency-badge \${urgencyBadgeClass}">\${row.urgencyRank}</span>\`
          : '';

        prevUrgency = row.urgencyRank;

        tr.innerHTML = \`
          <td>\${urgencyHtml}</td>
          <td><span class="employment-badge \${empBadgeClass}">\${row.employmentStatus}</span></td>
          <td style="text-align: right;"><strong>\${row.count.toLocaleString()}</strong>名</td>
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
