// ===== Phase7: SupplyDensityViz =====
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

// ===== Phase7: QualificationDistViz =====
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

// ===== Phase7: AgeGenderCrossViz =====
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

// ===== Phase7: MobilityScoreViz =====
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

// ===== Phase7: PersonaProfileViz =====
/**
 * Phase 7 ペルソナ詳細プロファイル可視化
 *
 * セグメント別の詳細特性を可視化します。
 */

/**
 * ペルソナ詳細プロファイル表示（メニューから呼び出し）
 */
function showDetailedPersonaProfile() {
  const ui = SpreadsheetApp.getUi();

  try {
    // データ読み込み
    const data = loadPersonaProfileData();

    if (!data || data.length === 0) {
      ui.alert(
        'データなし',
        'Phase7_PersonaProfileシートにデータがありません。\n' +
        '先に「Phase 7自動インポート」を実行してください。',
        ui.ButtonSet.OK
      );
      return;
    }

    // HTML生成
    const html = generatePersonaProfileHTML(data);

    // ダイアログ表示
    const htmlOutput = HtmlService.createHtmlOutput(html)
      .setWidth(1400)
      .setHeight(900);

    ui.showModalDialog(htmlOutput, 'Phase 7: ペルソナ詳細プロファイル');

  } catch (error) {
    ui.alert('エラー', `可視化中にエラーが発生しました:\n${error.message}`, ui.ButtonSet.OK);
    Logger.log(`ペルソナ詳細プロファイルエラー: ${error.stack}`);
  }
}


/**
 * ペルソナプロファイルデータ読み込み
 * @return {Array<Object>} データオブジェクトの配列
 */
function loadPersonaProfileData() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName('Phase7_PersonaProfile');

  if (!sheet) {
    throw new Error('Phase7_PersonaProfileシートが見つかりません');
  }

  const lastRow = sheet.getLastRow();
  if (lastRow <= 1) {
    return [];
  }

  // データ範囲取得（ヘッダー除く）
  const range = sheet.getRange(2, 1, lastRow - 1, 12);
  const values = range.getValues();

  // オブジェクト配列に変換
  const data = values.map(row => ({
    segmentId: row[0],            // セグメントID
    personaName: row[1],          // ペルソナ名
    count: row[2],                // 人数
    compositionRatio: row[3],     // 構成比
    avgAge: row[4],               // 平均年齢
    femaleRatio: row[5],          // 女性比率
    qualifiedRate: row[6],        // 資格保有率
    avgQualifications: row[7],    // 平均資格数
    avgDesiredLocs: row[8],       // 平均希望地数
    urgency: row[9],              // 緊急度
    topResidences: row[10],       // 主要居住地TOP3
    features: row[11]             // 特徴
  }));

  Logger.log(`ペルソナプロファイルデータ読み込み: ${data.length}件`);

  return data;
}


/**
 * ペルソナプロファイルHTML生成
 * @param {Array<Object>} data - データ配列
 * @return {string} HTML文字列
 */
function generatePersonaProfileHTML(data) {
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
    #radar_chart {
      width: 100%;
      height: 500px;
    }
    #composition_pie_chart {
      width: 100%;
      height: 500px;
    }
    .persona-cards {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
      gap: 20px;
      margin-top: 20px;
    }
    .persona-card {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      padding: 20px;
      border-radius: 12px;
      box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .persona-card.card-0 { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
    .persona-card.card-1 { background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); }
    .persona-card.card-2 { background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); }
    .persona-card.card-3 { background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); }
    .persona-card.card-4 { background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); }
    .persona-card h3 {
      margin-top: 0;
      font-size: 24px;
      border-bottom: 2px solid rgba(255,255,255,0.3);
      padding-bottom: 10px;
    }
    .persona-stat {
      display: flex;
      justify-content: space-between;
      margin: 10px 0;
      font-size: 14px;
    }
    .persona-stat-label {
      opacity: 0.9;
    }
    .persona-stat-value {
      font-weight: bold;
    }
    .persona-features {
      margin-top: 15px;
      padding-top: 15px;
      border-top: 1px solid rgba(255,255,255,0.3);
      font-style: italic;
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
      font-size: 13px;
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
  <h1>📊 Phase 7: ペルソナ詳細プロファイル</h1>

  <div class="charts-row">
    <div class="chart-container">
      <h2>ペルソナ別特性（レーダーチャート）</h2>
      <div id="radar_chart"></div>
    </div>
    <div class="chart-container">
      <h2>ペルソナ構成比</h2>
      <div id="composition_pie_chart"></div>
    </div>
  </div>

  <div class="container">
    <h2>ペルソナカード</h2>
    <div class="persona-cards" id="persona-cards"></div>
  </div>

  <div class="container">
    <h2>ペルソナ比較テーブル</h2>
    <table id="comparison-table">
      <thead>
        <tr>
          <th>ペルソナ名</th>
          <th>人数</th>
          <th>構成比</th>
          <th>平均年齢</th>
          <th>女性比率</th>
          <th>資格保有率</th>
          <th>平均資格数</th>
          <th>平均希望地数</th>
          <th>緊急度</th>
          <th>特徴</th>
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
      drawRadarChart();
      drawCompositionPieChart();
      renderPersonaCards();
      renderComparisonTable();
    }

    // レーダーチャート描画
    function drawRadarChart() {
      const chartData = new google.visualization.DataTable();
      chartData.addColumn('string', '指標');

      // 各ペルソナを列として追加
      data.forEach(persona => {
        chartData.addColumn('number', persona.personaName);
      });

      // 6つの軸
      const metrics = [
        {name: '平均年齢', getValue: p => p.avgAge / 100},  // 正規化
        {name: '女性比率', getValue: p => p.femaleRatio},
        {name: '資格保有率', getValue: p => p.qualifiedRate},
        {name: '平均資格数', getValue: p => p.avgQualifications / 5},  // 正規化
        {name: '平均希望地数', getValue: p => p.avgDesiredLocs / 5},  // 正規化
        {name: '緊急度', getValue: p => p.urgency}
      ];

      metrics.forEach(metric => {
        const row = [metric.name];
        data.forEach(persona => {
          row.push(metric.getValue(persona));
        });
        chartData.addRow(row);
      });

      const options = {
        title: 'ペルソナ別特性比較（6軸）',
        curveType: 'function',
        legend: {position: 'right'},
        vAxis: {minValue: 0, maxValue: 1}
      };

      const chart = new google.visualization.LineChart(
        document.getElementById('radar_chart')
      );

      chart.draw(chartData, options);
    }

    // 構成比円グラフ描画
    function drawCompositionPieChart() {
      const chartData = new google.visualization.DataTable();
      chartData.addColumn('string', 'ペルソナ');
      chartData.addColumn('number', '人数');

      data.forEach(persona => {
        chartData.addRow([persona.personaName, persona.count]);
      });

      const options = {
        title: 'ペルソナ別人数分布',
        pieHole: 0.4,
        colors: ['#667eea', '#4facfe', '#43e97b', '#fa709a', '#f093fb'],
        pieSliceText: 'percentage',
        legend: {position: 'right'}
      };

      const chart = new google.visualization.PieChart(
        document.getElementById('composition_pie_chart')
      );

      chart.draw(chartData, options);
    }

    // ペルソナカード表示
    function renderPersonaCards() {
      const container = document.getElementById('persona-cards');

      data.forEach((persona, index) => {
        const card = document.createElement('div');
        card.className = \`persona-card card-\${index}\`;

        card.innerHTML = \`
          <h3>\${persona.personaName}</h3>

          <div class="persona-stat">
            <span class="persona-stat-label">人数</span>
            <span class="persona-stat-value">\${persona.count.toLocaleString()}名</span>
          </div>

          <div class="persona-stat">
            <span class="persona-stat-label">構成比</span>
            <span class="persona-stat-value">\${(persona.compositionRatio * 100).toFixed(1)}%</span>
          </div>

          <div class="persona-stat">
            <span class="persona-stat-label">平均年齢</span>
            <span class="persona-stat-value">\${persona.avgAge.toFixed(1)}歳</span>
          </div>

          <div class="persona-stat">
            <span class="persona-stat-label">女性比率</span>
            <span class="persona-stat-value">\${(persona.femaleRatio * 100).toFixed(1)}%</span>
          </div>

          <div class="persona-stat">
            <span class="persona-stat-label">資格保有率</span>
            <span class="persona-stat-value">\${(persona.qualifiedRate * 100).toFixed(1)}%</span>
          </div>

          <div class="persona-stat">
            <span class="persona-stat-label">平均資格数</span>
            <span class="persona-stat-value">\${persona.avgQualifications.toFixed(2)}</span>
          </div>

          <div class="persona-stat">
            <span class="persona-stat-label">緊急度</span>
            <span class="persona-stat-value">\${(persona.urgency * 100).toFixed(1)}%</span>
          </div>

          <div class="persona-stat">
            <span class="persona-stat-label">主要居住地</span>
            <span class="persona-stat-value">\${persona.topResidences}</span>
          </div>

          <div class="persona-features">
            📝 特徴: \${persona.features}
          </div>
        \`;

        container.appendChild(card);
      });
    }

    // 比較テーブル表示
    function renderComparisonTable() {
      const tbody = document.getElementById('table-body');

      // 人数降順でソート
      const sortedData = [...data].sort((a, b) => b.count - a.count);

      sortedData.forEach(persona => {
        const tr = document.createElement('tr');
        tr.innerHTML = \`
          <td><strong>\${persona.personaName}</strong></td>
          <td>\${persona.count.toLocaleString()}名</td>
          <td>\${(persona.compositionRatio * 100).toFixed(1)}%</td>
          <td>\${persona.avgAge.toFixed(1)}歳</td>
          <td>\${(persona.femaleRatio * 100).toFixed(1)}%</td>
          <td>\${(persona.qualifiedRate * 100).toFixed(1)}%</td>
          <td>\${persona.avgQualifications.toFixed(2)}</td>
          <td>\${persona.avgDesiredLocs.toFixed(1)}</td>
          <td>\${(persona.urgency * 100).toFixed(1)}%</td>
          <td>\${persona.features}</td>
        \`;
        tbody.appendChild(tr);
      });
    }
  </script>
</body>
</html>
  `;
}
