/**
 * Phase 7 人材供給密度マップ可視化
 *
 * 地域ごとの求職者密度・資格保有率・緊急度を総合評価し、
 * バブルチャートとランク別テーブルで可視化します。
 */

/**
 * 人材供給密度マップ表示（メニューから呼び出し）
 */
function showSupplyDensityMap() {
  const ui = SpreadsheetApp.getUi();

  try {
    // データ読み込み
    const data = loadSupplyDensityData();

    if (!data || data.length === 0) {
      ui.alert(
        'データなし',
        'Phase7_SupplyDensityシートにデータがありません。\n' +
        '先に「Phase 7データ取り込み」を実行してください。',
        ui.ButtonSet.OK
      );
      return;
    }

    // HTML生成
    const html = generateSupplyDensityHTML(data);

    // ダイアログ表示
    const htmlOutput = HtmlService.createHtmlOutput(html)
      .setWidth(1000)
      .setHeight(700);

    ui.showModalDialog(htmlOutput, 'Phase 7: 人材供給密度マップ');

  } catch (error) {
    ui.alert('エラー', `可視化中にエラーが発生しました:\n${error.message}`, ui.ButtonSet.OK);
    Logger.log(`人材供給密度マップエラー: ${error.stack}`);
  }
}


/**
 * 人材供給密度データ読み込み
 * @return {Array<Object>} データオブジェクトの配列
 */
function loadSupplyDensityData() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName('Phase7_SupplyDensity');

  if (!sheet) {
    throw new Error('Phase7_SupplyDensityシートが見つかりません');
  }

  const lastRow = sheet.getLastRow();
  if (lastRow <= 1) {
    return [];
  }

  // データ範囲取得（ヘッダー除く）
  const range = sheet.getRange(2, 1, lastRow - 1, 7);
  const values = range.getValues();

  // オブジェクト配列に変換
  const data = values.map(row => ({
    municipality: row[0],      // 市区町村
    applicantCount: row[1],    // 求職者数
    qualifiedRate: row[2],     // 資格保有率
    avgAge: row[3],            // 平均年齢
    urgencyRate: row[4],       // 緊急度
    compositeScore: row[5],    // 総合スコア
    rank: row[6]               // ランク
  }));

  Logger.log(`人材供給密度データ読み込み: ${data.length}件`);

  return data;
}


/**
 * 人材供給密度マップHTML生成
 * @param {Array<Object>} data - データ配列
 * @return {string} HTML文字列
 */
function generateSupplyDensityHTML(data) {
  // データをJSON文字列化
  const dataJson = JSON.stringify(data);

  // ランク別統計計算
  const rankStats = calculateRankStats(data);
  const rankStatsJson = JSON.stringify(rankStats);

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
      grid-template-columns: repeat(5, 1fr);
      gap: 15px;
      margin-bottom: 20px;
    }
    .stat-card {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      padding: 15px;
      border-radius: 8px;
      text-align: center;
    }
    .stat-card.rank-S { background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); }
    .stat-card.rank-A { background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); }
    .stat-card.rank-B { background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); }
    .stat-card.rank-C { background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); }
    .stat-card.rank-D { background: linear-gradient(135deg, #a8a8a8 0%, #d0d0d0 100%); }
    .stat-label {
      font-size: 12px;
      opacity: 0.9;
      margin-bottom: 5px;
    }
    .stat-value {
      font-size: 24px;
      font-weight: bold;
    }
    #bubble_chart {
      width: 100%;
      height: 400px;
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
    .rank-badge {
      display: inline-block;
      padding: 4px 12px;
      border-radius: 12px;
      font-weight: bold;
      color: white;
    }
    .rank-badge.S { background-color: #f5576c; }
    .rank-badge.A { background-color: #4facfe; }
    .rank-badge.B { background-color: #43e97b; }
    .rank-badge.C { background-color: #fa709a; }
    .rank-badge.D { background-color: #a8a8a8; }
  </style>
</head>
<body>
  <h1>📊 Phase 7: 人材供給密度マップ</h1>

  <div class="container">
    <h2>ランク別統計</h2>
    <div class="stats-grid" id="rank-stats"></div>
  </div>

  <div class="container">
    <h2>バブルチャート（求職者数 × 総合スコア）</h2>
    <div id="bubble_chart"></div>
  </div>

  <div class="container">
    <h2>地域別詳細データ</h2>
    <table id="data-table">
      <thead>
        <tr>
          <th>ランク</th>
          <th>市区町村</th>
          <th>求職者数</th>
          <th>資格保有率</th>
          <th>平均年齢</th>
          <th>緊急度</th>
          <th>総合スコア</th>
        </tr>
      </thead>
      <tbody id="table-body"></tbody>
    </table>
  </div>

  <script type="text/javascript">
    const data = ${dataJson};
    const rankStats = ${rankStatsJson};

    // Google Charts読み込み
    google.charts.load('current', {'packages':['corechart']});
    google.charts.setOnLoadCallback(drawCharts);

    function drawCharts() {
      drawBubbleChart();
      renderRankStats();
      renderDataTable();
    }

    // バブルチャート描画
    function drawBubbleChart() {
      const chartData = new google.visualization.DataTable();
      chartData.addColumn('string', 'ID');
      chartData.addColumn('number', '求職者数');
      chartData.addColumn('number', '総合スコア');
      chartData.addColumn('string', 'ランク');
      chartData.addColumn('number', 'サイズ');

      data.forEach(row => {
        chartData.addRow([
          row.municipality,
          row.applicantCount,
          row.compositeScore,
          row.rank,
          row.applicantCount
        ]);
      });

      const options = {
        title: '地域別人材供給密度（バブルサイズ=求職者数）',
        hAxis: {title: '求職者数'},
        vAxis: {title: '総合スコア'},
        bubble: {textStyle: {fontSize: 11}},
        colorAxis: {
          colors: ['#a8a8a8', '#fa709a', '#43e97b', '#4facfe', '#f5576c']
        },
        sizeAxis: {minSize: 5, maxSize: 30}
      };

      const chart = new google.visualization.BubbleChart(
        document.getElementById('bubble_chart')
      );

      chart.draw(chartData, options);
    }

    // ランク別統計表示
    function renderRankStats() {
      const container = document.getElementById('rank-stats');
      ['S', 'A', 'B', 'C', 'D'].forEach(rank => {
        const stat = rankStats[rank] || {count: 0, avgScore: 0};
        const card = document.createElement('div');
        card.className = \`stat-card rank-\${rank}\`;
        card.innerHTML = \`
          <div class="stat-label">ランク \${rank}</div>
          <div class="stat-value">\${stat.count}地域</div>
          <div class="stat-label">平均スコア: \${stat.avgScore.toFixed(1)}</div>
        \`;
        container.appendChild(card);
      });
    }

    // データテーブル表示
    function renderDataTable() {
      const tbody = document.getElementById('table-body');

      data.forEach(row => {
        const tr = document.createElement('tr');
        tr.innerHTML = \`
          <td><span class="rank-badge \${row.rank}">\${row.rank}</span></td>
          <td>\${row.municipality}</td>
          <td>\${row.applicantCount}</td>
          <td>\${(row.qualifiedRate * 100).toFixed(1)}%</td>
          <td>\${row.avgAge.toFixed(1)}歳</td>
          <td>\${(row.urgencyRate * 100).toFixed(1)}%</td>
          <td><strong>\${row.compositeScore.toFixed(1)}</strong></td>
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
 * ランク別統計計算
 * @param {Array<Object>} data - データ配列
 * @return {Object} ランク別統計
 */
function calculateRankStats(data) {
  const ranks = ['S', 'A', 'B', 'C', 'D'];
  const stats = {};

  ranks.forEach(rank => {
    const rankData = data.filter(row => row.rank === rank);
    const count = rankData.length;
    const avgScore = count > 0
      ? rankData.reduce((sum, row) => sum + row.compositeScore, 0) / count
      : 0;

    stats[rank] = {
      count: count,
      avgScore: avgScore
    };
  });

  return stats;
}


/**
 * ランク別地域リストをシートに出力
 */
function exportRankBreakdownToSheet() {
  const ui = SpreadsheetApp.getUi();

  try {
    const data = loadSupplyDensityData();

    if (!data || data.length === 0) {
      ui.alert('データなし', 'Phase7_SupplyDensityシートにデータがありません。', ui.ButtonSet.OK);
      return;
    }

    // ランク別にグループ化
    const rankGroups = {
      'S': data.filter(row => row.rank === 'S'),
      'A': data.filter(row => row.rank === 'A'),
      'B': data.filter(row => row.rank === 'B'),
      'C': data.filter(row => row.rank === 'C'),
      'D': data.filter(row => row.rank === 'D')
    };

    // 新しいシート作成
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    const sheetName = 'Phase7_DensityRankBreakdown';
    let sheet = ss.getSheetByName(sheetName);

    if (sheet) {
      sheet.clear();
    } else {
      sheet = ss.insertSheet(sheetName);
    }

    // ヘッダー
    let currentRow = 1;
    sheet.getRange(currentRow, 1, 1, 7).setValues([[
      'ランク', '市区町村', '求職者数', '資格保有率', '平均年齢', '緊急度', '総合スコア'
    ]]);

    formatHeaderRow(sheet, 7);
    currentRow++;

    // ランク別データ出力
    ['S', 'A', 'B', 'C', 'D'].forEach(rank => {
      const rankData = rankGroups[rank];

      if (rankData.length === 0) {
        return;
      }

      rankData.forEach(row => {
        sheet.getRange(currentRow, 1, 1, 7).setValues([[
          rank,
          row.municipality,
          row.applicantCount,
          row.qualifiedRate,
          row.avgAge,
          row.urgencyRate,
          row.compositeScore
        ]]);
        currentRow++;
      });
    });

    // 列幅自動調整
    for (let i = 1; i <= 7; i++) {
      sheet.autoResizeColumn(i);
    }

    ui.alert('エクスポート完了', `ランク別内訳を「${sheetName}」シートに出力しました。`, ui.ButtonSet.OK);

  } catch (error) {
    ui.alert('エラー', `エクスポート中にエラーが発生しました:\n${error.message}`, ui.ButtonSet.OK);
    Logger.log(`ランク別内訳エクスポートエラー: ${error.stack}`);
  }
}
