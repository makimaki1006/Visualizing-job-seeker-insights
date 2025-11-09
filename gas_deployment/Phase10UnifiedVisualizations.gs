/**
 * Phase 10 統合可視化ファイル
 *
 * このファイルには以下の可視化機能がすべて含まれています:
 * 1. 緊急度分布（A-Dランク）
 * 2. 緊急度×年齢クロス分析
 * 3. 緊急度×就業状態クロス分析
 * 4. 緊急度×年齢マトリックス（ヒートマップ）
 * 5. 市区町村別緊急度分布
 * 6. Phase 10統合ダッシュボード
 */

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 共通ユーティリティ関数
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

/**
 * データ読み込み共通エラーハンドリング
 * @param {string} sheetName - シート名
 * @param {number} columnCount - カラム数
 * @return {Array<Array>} データ配列
 */
function loadSheetData_(sheetName, columnCount) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName(sheetName);

  if (!sheet) {
    throw new Error(`${sheetName}シートが見つかりません`);
  }

  const lastRow = sheet.getLastRow();
  if (lastRow <= 1) {
    return [];
  }

  const range = sheet.getRange(2, 1, lastRow - 1, columnCount);
  return range.getValues();
}

/**
 * データなしアラート表示
 * @param {string} sheetName - シート名
 * @param {string} phaseName - Phase名
 */
function showNoDataAlert_(sheetName, phaseName) {
  const ui = SpreadsheetApp.getUi();
  ui.alert(
    'データなし',
    `${sheetName}シートにデータがありません。\n` +
    `先に「${phaseName}データ取り込み」を実行してください。`,
    ui.ButtonSet.OK
  );
}

/**
 * エラーアラート表示
 * @param {Error} error - エラーオブジェクト
 * @param {string} context - エラーコンテキスト
 */
function showErrorAlert_(error, context) {
  const ui = SpreadsheetApp.getUi();
  ui.alert('エラー', `${context}中にエラーが発生しました:\n${error.message}`, ui.ButtonSet.OK);
  Logger.log(`${context}エラー: ${error.stack}`);
}

/**
 * HTMLダイアログ表示
 * @param {string} html - HTML文字列
 * @param {string} title - ダイアログタイトル
 * @param {number} width - 幅（デフォルト: 1400）
 * @param {number} height - 高さ（デフォルト: 900）
 */
function showHtmlDialog_(html, title, width = 1400, height = 900) {
  const htmlOutput = HtmlService.createHtmlOutput(html)
    .setWidth(width)
    .setHeight(height);
  SpreadsheetApp.getUi().showModalDialog(htmlOutput, title);
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 1. 緊急度分布（A-Dランク）
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

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
        'Phase10_UrgencyDistシートにデータがありません。\n' +
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
  const sheet = findSheetByNames(ss, generateSheetNameCandidates('UrgencyDist', 10));

  if (!sheet) {
    throw new Error('UrgencyDistシートが見つかりません');
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
    /* 共通スタイル */
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
    h2 {
      color: #333;
      margin-top: 20px;
    }
    .container {
      background-color: white;
      padding: 20px;
      border-radius: 8px;
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
      margin-bottom: 20px;
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
      position: sticky;
      top: 0;
      z-index: 10;
    }
    tr:hover {
      background-color: #f5f5f5;
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

    /* Phase固有スタイル */
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

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 2. 緊急度×年齢クロス分析
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

/**
 * 緊急度×年齢クロス分析表示（メニューから呼び出し）
 */
function showUrgencyAgeCross() {
  const ui = SpreadsheetApp.getUi();

  try {
    // データ読み込み
    const data = loadUrgencyAgeCrossData();

    if (!data || data.length === 0) {
      ui.alert(
        'データなし',
        'Phase10_UrgencyAgeシートにデータがありません。\n' +
        '先に「Python結果CSVを取り込み」を実行してください。',
        ui.ButtonSet.OK
      );
      return;
    }

    // HTML生成
    const html = generateUrgencyAgeCrossHTML(data);

    // ダイアログ表示
    const htmlOutput = HtmlService.createHtmlOutput(html)
      .setWidth(1400)
      .setHeight(900);

    ui.showModalDialog(htmlOutput, 'Phase 10: 緊急度×年齢層クロス分析');

  } catch (error) {
    ui.alert('エラー', `可視化中にエラーが発生しました:\n${error.message}`, ui.ButtonSet.OK);
    Logger.log(`緊急度×年齢クロス分析エラー: ${error.stack}`);
  }
}

/**
 * 緊急度×年齢クロスデータ読み込み
 * @return {Array<Object>} データオブジェクトの配列
 */
function loadUrgencyAgeCrossData() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = findSheetByNames(ss, generateSheetNameCandidates('UrgencyAge', 10));

  if (!sheet) {
    throw new Error('UrgencyAgeシートが見つかりません');
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
      ageGroup: String(row[1]),
      count: Number(row[2]),
      avgAge: row[3] ? Number(row[3]) : null,
      avgUrgencyScore: row[4] ? Number(row[4]) : null
    }));

  Logger.log(`緊急度×年齢クロスデータ読み込み: ${data.length}件`);

  return data;
}

/**
 * 緊急度×年齢クロスHTML生成
 * @param {Array<Object>} data - データ配列
 * @return {string} HTML文字列
 */
function generateUrgencyAgeCrossHTML(data) {
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
    .age-badge {
      display: inline-block;
      padding: 4px 8px;
      border-radius: 4px;
      font-size: 11px;
      font-weight: bold;
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
  <h1>🚀📊 Phase 10: 緊急度×年齢層クロス分析</h1>

  <div class="container">
    <h2>統計サマリー</h2>
    <div class="stats-summary" id="stats-summary"></div>
  </div>

  <div class="container">
    <h2>緊急度×年齢層グループ化縦棒グラフ</h2>
    <div id="grouped_column_chart"></div>
  </div>

  <div class="container">
    <h2>緊急度×年齢層詳細データ</h2>
    <div class="table-container">
      <table id="data-table">
        <thead>
          <tr>
            <th style="width: 25%;">緊急度ランク</th>
            <th style="width: 20%;">年齢層</th>
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

    // 緊急度・年齢層順序定義
    const urgencyOrder = ['A: 高い', 'B: 中程度', 'C: やや低い', 'D: 低い'];
    const ageGroupOrder = ['20代', '30代', '40代', '50代', '60代', '70歳以上'];

    // Google Charts読み込み
    google.charts.load('current', {'packages':['corechart']});
    google.charts.setOnLoadCallback(drawCharts);

        // 統計サマリー表示
    function renderStatsSummary() {
      const container = document.getElementById('stats-summary');

      // 緊急度ランク数
      const uniqueUrgency = [...new Set(data.map(d => d.urgencyRank))].length;

      // 総人数
      const totalCount = data.reduce((sum, row) => sum + row.count, 0);

      // 年齢層数
      const uniqueAgeGroups = [...new Set(data.map(d => d.ageGroup))].length;

      // 平均緊急度スコア
      const avgScore = data.reduce((sum, row) => sum + (row.avgUrgencyScore || 0) * row.count, 0) / totalCount;

      const stats = [
        {label: '緊急度ランク数', value: uniqueUrgency, unit: 'ランク'},
        {label: '総人数', value: totalCount.toLocaleString(), unit: '名'},
        {label: '年齢層数', value: uniqueAgeGroups, unit: 'グループ'},
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
      // データを年齢層別にピボット
      const ageGroupMap = {};
      ageGroupOrder.forEach(ag => {
        ageGroupMap[ag] = {};
        urgencyOrder.forEach(ur => {
          ageGroupMap[ag][ur] = 0;
        });
      });

      data.forEach(row => {
        if (ageGroupMap[row.ageGroup] && urgencyOrder.includes(row.urgencyRank)) {
          ageGroupMap[row.ageGroup][row.urgencyRank] = row.count;
        }
      });

      // Google Charts用データテーブル作成
      const chartData = new google.visualization.DataTable();
      chartData.addColumn('string', '年齢層');
      urgencyOrder.forEach(ur => {
        chartData.addColumn('number', ur);
      });

      ageGroupOrder.forEach(ag => {
        const row = [ag];
        urgencyOrder.forEach(ur => {
          row.push(ageGroupMap[ag][ur] || 0);
        });
        chartData.addRow(row);
      });

      const options = {
        title: '緊急度×年齢層グループ化縦棒グラフ',
        chartArea: {width: '70%', height: '70%'},
        hAxis: {
          title: '年齢層'
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

      // 緊急度→年齢層の順にソート
      const sortedData = data.sort((a, b) => {
        const urgencyDiff = urgencyOrder.indexOf(a.urgencyRank) - urgencyOrder.indexOf(b.urgencyRank);
        if (urgencyDiff !== 0) return urgencyDiff;
        return ageGroupOrder.indexOf(a.ageGroup) - ageGroupOrder.indexOf(b.ageGroup);
      });

      let prevUrgency = null;

      sortedData.forEach(row => {
        const tr = document.createElement('tr');

        // 緊急度バッジのクラス決定
        const urgencyBadgeClass = row.urgencyRank.startsWith('A') ? 'urgency-A' :
                                   row.urgencyRank.startsWith('B') ? 'urgency-B' :
                                   row.urgencyRank.startsWith('C') ? 'urgency-C' : 'urgency-D';

        // 年齢層バッジのクラス決定
        const ageBadgeClass = row.ageGroup.includes('20') ? 'age-20' :
                              row.ageGroup.includes('30') ? 'age-30' :
                              row.ageGroup.includes('40') ? 'age-40' :
                              row.ageGroup.includes('50') ? 'age-50' :
                              row.ageGroup.includes('60') ? 'age-60' : 'age-70';

        // 同じ緊急度が続く場合は空欄に
        const urgencyHtml = row.urgencyRank !== prevUrgency
          ? \`<span class="urgency-badge \${urgencyBadgeClass}">\${row.urgencyRank}</span>\`
          : '';

        prevUrgency = row.urgencyRank;

        tr.innerHTML = \`
          <td>\${urgencyHtml}</td>
          <td><span class="age-badge \${ageBadgeClass}">\${row.ageGroup}</span></td>
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

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 3. 緊急度×就業状態クロス分析
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

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
        'Phase10_UrgencyEmploymentシートにデータがありません。\n' +
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
  const sheet = findSheetByNames(ss, generateSheetNameCandidates('UrgencyEmployment', 10));

  if (!sheet) {
    throw new Error('UrgencyEmploymentシートが見つかりません');
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

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 4. 緊急度×年齢マトリックス（ヒートマップ）
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

/**
 * 緊急度×年齢マトリックス表示（メニューから呼び出し）
 */
function showUrgencyAgeMatrix() {
  const ui = SpreadsheetApp.getUi();

  try {
    // データ読み込み
    const data = loadUrgencyAgeMatrixData();

    if (!data || data.rows.length === 0) {
      ui.alert(
        'データなし',
        'Phase10_UrgencyAge_Matrixシートにデータがありません。\n' +
        '先に「Python結果CSVを取り込み」を実行してください。',
        ui.ButtonSet.OK
      );
      return;
    }

    // HTML生成
    const html = generateUrgencyAgeMatrixHTML(data);

    // ダイアログ表示
    const htmlOutput = HtmlService.createHtmlOutput(html)
      .setWidth(1400)
      .setHeight(900);

    ui.showModalDialog(htmlOutput, 'Phase 10: 緊急度×年齢層マトリックス');

  } catch (error) {
    ui.alert('エラー', `可視化中にエラーが発生しました:\n${error.message}`, ui.ButtonSet.OK);
    Logger.log(`緊急度×年齢マトリックスエラー: ${error.stack}`);
  }
}

/**
 * 緊急度×年齢マトリックスデータ読み込み
 * @return {Object} データオブジェクト
 */
function loadUrgencyAgeMatrixData() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = findSheetByNames(ss, ['Phase10_UrgencyAge_Matrix', 'UrgencyAge_Matrix', 'Phase10_UrgencyAgeMatrix', 'UrgencyAgeMatrix']);

  if (!sheet) {
    throw new Error('UrgencyAge_Matrixシートが見つかりません');
  }

  const lastRow = sheet.getLastRow();
  if (lastRow <= 1) {
    return { headers: [], rows: [], metadata: {} };
  }

  // ヘッダー行取得
  const headers = sheet.getRange(1, 1, 1, 7).getValues()[0];

  // データ範囲取得（ヘッダー除く）
  const range = sheet.getRange(2, 1, lastRow - 1, 7);
  const values = range.getValues();

  // メタデータ計算
  const metadata = calculateMatrixMetadata(values);

  Logger.log(`緊急度×年齢マトリックスデータ読み込み: ${values.length}件`);

  return {
    headers,
    rows: values,
    metadata,
    totalRows: lastRow - 1
  };
}

/**
 * マトリックスメタデータ計算
 * @param {Array} rows - データ行
 * @return {Object} メタデータ
 */
function calculateMatrixMetadata(rows) {
  const values = [];
  let totalCount = 0;

  rows.forEach(row => {
    row.slice(1).forEach(cell => {
      const num = Number(cell) || 0;
      if (num > 0) {
        values.push(num);
        totalCount += num;
      }
    });
  });

  values.sort((a, b) => a - b);

  return {
    totalCells: rows.length * 6,  // 6列（年齢層）
    valueCells: values.length,
    emptyCells: (rows.length * 6) - values.length,
    totalCount,
    min: values.length > 0 ? values[0] : 0,
    max: values.length > 0 ? values[values.length - 1] : 0,
    mean: values.length > 0 ? values.reduce((sum, v) => sum + v, 0) / values.length : 0,
    median: values.length > 0 ? values[Math.floor(values.length / 2)] : 0
  };
}

/**
 * 緊急度×年齢マトリックスHTML生成
 * @param {Object} data - データオブジェクト
 * @return {string} HTML文字列
 */
function generateUrgencyAgeMatrixHTML(data) {
  const { headers, rows, metadata, totalRows } = data;
  const dataJson = JSON.stringify({ headers, rows });

  return `
<!DOCTYPE html>
<html>
<head>
  <base target="_top">
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
    .stat-label {
      font-size: 12px;
      opacity: 0.9;
      margin-bottom: 5px;
    }
    .stat-value {
      font-size: 28px;
      font-weight: bold;
    }
    .heatmap-container {
      overflow: auto;
      max-height: 600px;
      border: 1px solid #ddd;
      border-radius: 4px;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      font-size: 13px;
    }
    th {
      background-color: #1a73e8;
      color: white;
      padding: 12px;
      text-align: center;
      position: sticky;
      top: 0;
      z-index: 10;
      font-weight: bold;
    }
    td {
      padding: 10px;
      text-align: center;
      border: 1px solid #e0e0e0;
    }
    .row-header {
      background-color: #f8f9fa;
      font-weight: bold;
      text-align: left;
      position: sticky;
      left: 0;
      z-index: 5;
      border-right: 2px solid #1a73e8;
      max-width: 150px;
      white-space: nowrap;
    }
    .legend {
      display: flex;
      align-items: center;
      justify-content: center;
      margin: 20px 0;
      flex-wrap: wrap;
    }
    .legend-item {
      margin: 5px 10px;
      display: flex;
      align-items: center;
    }
    .legend-box {
      width: 30px;
      height: 20px;
      margin-right: 5px;
      border: 1px solid #ddd;
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
  <h1>🔥 Phase 10: 緊急度×年齢層マトリックス</h1>

  <div class="container">
    <h2>統計サマリー</h2>
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-label">総緊急度ランク数</div>
        <div class="stat-value">${totalRows.toLocaleString()}</div>
        <div class="stat-label">種類</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">総人数</div>
        <div class="stat-value">${metadata.totalCount.toLocaleString()}</div>
        <div class="stat-label">名</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">最大値</div>
        <div class="stat-value">${metadata.max}</div>
        <div class="stat-label">名</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">平均値</div>
        <div class="stat-value">${metadata.mean.toFixed(1)}</div>
        <div class="stat-label">名</div>
      </div>
    </div>
  </div>

  <div class="container">
    <h2>ヒートマップ（緊急度×年齢層）</h2>
    <div class="note">
      <strong>📊 表示説明:</strong> 緊急度ランク（A-D）と年齢層（20代-70歳以上）の分布をヒートマップで表示しています。色が濃いほど人数が多いことを示します。
      <ul style="margin: 10px 0; padding-left: 20px;">
        <li><strong>A: 高い</strong> - 緊急度スコア7以上（即座に対応すべき）</li>
        <li><strong>B: 中程度</strong> - 緊急度スコア5-7（優先的に対応）</li>
        <li><strong>C: やや低い</strong> - 緊急度スコア3-5（計画的に対応）</li>
        <li><strong>D: 低い</strong> - 緊急度スコア3未満（長期的に対応）</li>
      </ul>
    </div>

    <div class="legend" id="legend"></div>

    <div class="heatmap-container">
      <table id="heatmap-table"></table>
    </div>
  </div>

  <script type="text/javascript">
    const data = ${dataJson};
    const metadata = ${JSON.stringify(metadata)};

    // カラースケール生成（赤系グラデーション - 緊急度を表現）
    function getHeatmapColor(value, max) {
      if (value === 0) return '#f8f9fa';  // 空セル

      const intensity = Math.min(value / max, 1);
      const r = 255;
      const g = Math.round(255 * (1 - intensity));
      const b = Math.round(255 * (1 - intensity));

      return \`rgb(\${r}, \${g}, \${b})\`;
    }

    // 凡例生成
    function renderLegend() {
      const container = document.getElementById('legend');

      const legendSteps = [
        { label: '0名', value: 0 },
        { label: \`\${Math.round(metadata.max * 0.25)}名\`, value: metadata.max * 0.25 },
        { label: \`\${Math.round(metadata.max * 0.5)}名\`, value: metadata.max * 0.5 },
        { label: \`\${Math.round(metadata.max * 0.75)}名\`, value: metadata.max * 0.75 },
        { label: \`\${metadata.max}名\`, value: metadata.max }
      ];

      legendSteps.forEach(step => {
        const item = document.createElement('div');
        item.className = 'legend-item';

        const box = document.createElement('div');
        box.className = 'legend-box';
        box.style.backgroundColor = getHeatmapColor(step.value, metadata.max);

        const label = document.createElement('span');
        label.textContent = step.label;

        item.appendChild(box);
        item.appendChild(label);
        container.appendChild(item);
      });
    }

    // ヒートマップテーブル生成
    function renderHeatmapTable() {
      const table = document.getElementById('heatmap-table');

      // ヘッダー行
      const thead = document.createElement('thead');
      const headerRow = document.createElement('tr');

      data.headers.forEach((header, index) => {
        const th = document.createElement('th');
        th.textContent = header;
        if (index === 0) {
          th.style.minWidth = '150px';
          th.style.textAlign = 'left';
        }
        headerRow.appendChild(th);
      });

      thead.appendChild(headerRow);
      table.appendChild(thead);

      // データ行
      const tbody = document.createElement('tbody');

      data.rows.forEach(row => {
        const tr = document.createElement('tr');

        row.forEach((cell, colIndex) => {
          const td = document.createElement('td');

          if (colIndex === 0) {
            // 緊急度ランク（行ヘッダー）
            td.className = 'row-header';
            td.textContent = cell;
          } else {
            // 数値セル
            const value = Number(cell) || 0;
            td.textContent = value > 0 ? value : '－';
            td.style.backgroundColor = getHeatmapColor(value, metadata.max);

            // 値が大きい場合は文字色を白に
            if (value > metadata.max * 0.6) {
              td.style.color = 'white';
              td.style.fontWeight = 'bold';
            }
          }

          tr.appendChild(td);
        });

        tbody.appendChild(tr);
      });

      table.appendChild(tbody);
    }

    // 初期化
    renderLegend();
    renderHeatmapTable();
  </script>
</body>
</html>
  `;
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 5. 市区町村別緊急度分布
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

/**
 * 市区町村別緊急度マップ表示（メニューから呼び出し）
 */
function showUrgencyByMunicipality() {
  const ui = SpreadsheetApp.getUi();

  try {
    // データ読み込み
    const data = loadUrgencyByMunicipalityData();

    if (!data || data.length === 0) {
      ui.alert(
        'データなし',
        'Phase10_UrgencyByMunicipalityシートにデータがありません。\n' +
        '先に「Python結果CSVを取り込み」を実行してください。',
        ui.ButtonSet.OK
      );
      return;
    }

    // HTML生成
    const html = generateUrgencyByMunicipalityHTML(data);

    // ダイアログ表示
    const htmlOutput = HtmlService.createHtmlOutput(html)
      .setWidth(1400)
      .setHeight(900);

    ui.showModalDialog(htmlOutput, 'Phase 10: 市区町村別緊急度分布');

  } catch (error) {
    ui.alert('エラー', `可視化中にエラーが発生しました:\n${error.message}`, ui.ButtonSet.OK);
    Logger.log(`市区町村別緊急度マップエラー: ${error.stack}`);
  }
}

/**
 * 市区町村別緊急度データ読み込み
 * @return {Array<Object>} データオブジェクトの配列
 */
function loadUrgencyByMunicipalityData() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = findSheetByNames(ss, generateSheetNameCandidates('UrgencyByMunicipality', 10));

  if (!sheet) {
    throw new Error('UrgencyByMunicipalityシートが見つかりません');
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
      municipality: String(row[0]),
      count: Number(row[1]),
      avgUrgencyScore: row[2] ? Number(row[2]) : null
    }));

  Logger.log(`市区町村別緊急度データ読み込み: ${data.length}件`);

  return data;
}

/**
 * 緊急度ランク判定
 * @param {number} score - 緊急度スコア
 * @return {string} ランク（A-D）
 */
function getUrgencyRank(score) {
  if (score >= 7) return 'A';
  if (score >= 5) return 'B';
  if (score >= 3) return 'C';
  return 'D';
}

/**
 * 市区町村別緊急度HTML生成
 * @param {Array<Object>} data - データ配列
 * @return {string} HTML文字列
 */
function generateUrgencyByMunicipalityHTML(data) {
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
    #scatter_chart {
      width: 100%;
      height: 500px;
    }
    #bar_chart {
      width: 100%;
      height: 500px;
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
    .rank-badge {
      display: inline-block;
      padding: 4px 8px;
      border-radius: 12px;
      font-weight: bold;
      font-size: 11px;
      margin-left: 5px;
    }
    .rank-A { background-color: #dc3545; color: white; }
    .rank-B { background-color: #ffc107; color: #333; }
    .rank-C { background-color: #17a2b8; color: white; }
    .rank-D { background-color: #6c757d; color: white; }
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
  <h1>🗺️ Phase 10: 市区町村別緊急度分布分析</h1>

  <div class="container">
    <h2>統計サマリー</h2>
    <div class="stats-summary" id="stats-summary"></div>
  </div>

  <div class="note">
    <strong>📊 緊急度ランク説明:</strong>
    <ul style="margin: 10px 0; padding-left: 20px;">
      <li><strong>A: 高い</strong> - 平均緊急度スコア7以上（即座に対応すべき地域）</li>
      <li><strong>B: 中程度</strong> - 平均緊急度スコア5-7（優先的に対応）</li>
      <li><strong>C: やや低い</strong> - 平均緊急度スコア3-5（計画的に対応）</li>
      <li><strong>D: 低い</strong> - 平均緊急度スコア3未満（長期的に対応）</li>
    </ul>
  </div>

  <div class="charts-row">
    <div class="chart-container">
      <h3>人数×緊急度スコア散布図</h3>
      <div id="scatter_chart"></div>
    </div>
    <div class="chart-container">
      <h3>TOP20市区町村（人数順）</h3>
      <div id="bar_chart"></div>
    </div>
  </div>

  <div class="container">
    <h2>市区町村別詳細データ（TOP100）</h2>
    <div class="table-container">
      <table id="data-table">
        <thead>
          <tr>
            <th style="width: 5%;">順位</th>
            <th style="width: 35%;">市区町村</th>
            <th style="width: 15%;">人数</th>
            <th style="width: 20%;">平均緊急度スコア</th>
            <th style="width: 25%;">緊急度ランク</th>
          </tr>
        </thead>
        <tbody id="table-body"></tbody>
      </table>
    </div>
  </div>

  <script type="text/javascript">
    const data = ${dataJson};

    // 緊急度ランク判定
    function getUrgencyRank(score) {
      if (score >= 7) return 'A: 高い';
      if (score >= 5) return 'B: 中程度';
      if (score >= 3) return 'C: やや低い';
      return 'D: 低い';
    }

    // Google Charts読み込み
    google.charts.load('currElementById('stats-summary');

      // 総市区町村数
      const totalMunicipalities = data.length;

      // 総人数
      const totalCount = data.reduce((sum, row) => sum + row.count, 0);

      // 平均緊急度スコア
      const avgScore = data.reduce((sum, row) => sum + (row.avgUrgencyScore || 0) * row.count, 0) / totalCount;

      // 高緊急度（A+B）の市区町村数
      const highUrgencyCount = data.filter(d => {
        const rank = getUrgencyRank(d.avgUrgencyScore || 0);
        return rank.startsWith('A') || rank.startsWith('B');
      }).length;

      const stats = [
        {label: '総市区町村数', value: totalMunicipalities.toLocaleString(), unit: '地域'},
        {label: '総人数', value: totalCount.toLocaleString(), unit: '名'},
        {label: '平均緊急度スコア', value: avgScore.toFixed(2), unit: '点'},
        {label: '高緊急度（A+B）地域', value: highUrgencyCount.toLocaleString(), unit: '地域'}
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

    // 散布図描画
    function drawScatterChart() {
      const chartData = new google.visualization.DataTable();
      chartData.addColumn('number', '人数');
      chartData.addColumn('number', '平均緊急度スコア');
      chartData.addColumn({type: 'string', role: 'tooltip'});

      data.forEach(row => {
        const tooltip = \`\${row.municipality}\\n人数: \${row.count}名\\n緊急度: \${row.avgUrgencyScore ? row.avgUrgencyScore.toFixed(2) : 'N/A'}点\`;
        chartData.addRow([row.count, row.avgUrgencyScore || 0, tooltip]);
      });

      const options = {
        title: '人数×緊急度スコア散布図',
        hAxis: {title: '人数', minValue: 0},
        vAxis: {title: '平均緊急度スコア', minValue: 0, maxValue: 10},
        legend: 'none',
        pointSize: 5,
        colors: ['#667eea'],
        chartArea: {width: '75%', height: '70%'}
      };

      const chart = new google.visualization.ScatterChart(
        document.getElementById('scatter_chart')
      );

      chart.draw(chartData, options);
    }

    // 棒グラフ描画（TOP20）
    function drawBarChart() {
      const sortedData = [...data].sort((a, b) => b.count - a.count).slice(0, 20);

      const chartData = new google.visualization.DataTable();
      chartData.addColumn('string', '市区町村');
      chartData.addColumn('number', '人数');

      sortedData.forEach(row => {
        chartData.addRow([row.municipality, row.count]);
      });

      const options = {
        title: 'TOP20市区町村（人数順）',
        legend: {position: 'none'},
        chartArea: {width: '70%', height: '75%'},
        hAxis: {
          title: '人数',
          minValue: 0
        },
        colors: ['#4285F4']
      };

      const chart = new google.visualization.BarChart(
        document.getElementById('bar_chart')
      );

      chart.draw(chartData, options);
    }

    // データテーブル表示（TOP100）
    function renderDataTable() {
      const tbody = document.getElementById('table-body');

      // 人数降順でソート、TOP100を取得
      const sortedData = [...data].sort((a, b) => b.count - a.count).slice(0, 100);

      sortedData.forEach((row, index) => {
        const tr = document.createElement('tr');

        const rank = getUrgencyRank(row.avgUrgencyScore || 0);
        const badgeClass = rank.startsWith('A') ? 'rank-A' :
                           rank.startsWith('B') ? 'rank-B' :
                           rank.startsWith('C') ? 'rank-C' : 'rank-D';

        tr.innerHTML = \`
          <td style="text-align: center;"><strong>\${index + 1}</strong></td>
          <td><strong>\${row.municipality}</strong></td>
          <td style="text-align: right;"><strong>\${row.count.toLocaleString()}</strong>名</td>
          <td style="text-align: right;">\${row.avgUrgencyScore ? row.avgUrgencyScore.toFixed(2) : '－'}点</td>
          <td><span class="rank-badge \${badgeClass}">\${rank}</span></td>
        \`;
        tbody.appendChild(tr);
      });
    }
  </script>
</body>
</html>
  `;
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 6. Phase 10統合ダッシュボード
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

/**
 * Phase 10統合ダッシュボード表示（メニューから呼び出し）
 */
function showPhase10CompleteDashboard() {
  const ui = SpreadsheetApp.getUi();

  try {
    // すべてのデータ読み込み
    const urgencyDistData = loadUrgencyDistData();
    const urgencyAgeData = loadUrgencyAgeCrossData();
    const urgencyEmpData = loadUrgencyEmploymentCrossData();
    const urgencyMatrixData = loadUrgencyAgeMatrixData();
    const urgencyMuniData = loadUrgencyByMunicipalityData();

    // データ検証
    if (!urgencyDistData || urgencyDistData.length === 0) {
      ui.alert(
        'データなし',
        'Phase 10のデータがありません。\n' +
        '先に「Python結果CSVを取り込み」を実行してください。',
        ui.ButtonSet.OK
      );
      return;
    }

    // HTML生成
    const html = generatePhase10DashboardHTML({
      urgencyDist: urgencyDistData,
      urgencyAge: urgencyAgeData,
      urgencyEmp: urgencyEmpData,
      urgencyMatrix: urgencyMatrixData,
      urgencyMuni: urgencyMuniData
    });

    // ダイアログ表示
    const htmlOutput = HtmlService.createHtmlOutput(html)
      .setWidth(1500)
      .setHeight(950);

    ui.showModalDialog(htmlOutput, 'Phase 10: 転職意欲・緊急度分析統合ダッシュボード');

  } catch (error) {
    ui.alert('エラー', `ダッシュボード表示中にエラーが発生しました:\n${error.message}`, ui.ButtonSet.OK);
    Logger.log(`Phase 10ダッシュボードエラー: ${error.stack}`);
  }
}

/**
 * Phase 10統合ダッシュボードHTML生成
 * @param {Object} allData - すべてのデータオブジェクト
 * @return {string} HTML文字列
 */
function generatePhase10DashboardHTML(allData) {
  const urgencyDistJson = JSON.stringify(allData.urgencyDist);
  const urgencyAgeJson = JSON.stringify(allData.urgencyAge);
  const urgencyEmpJson = JSON.stringify(allData.urgencyEmp);
  const urgencyMatrixJson = JSON.stringify(allData.urgencyMatrix);
  const urgencyMuniJson = JSON.stringify(allData.urgencyMuni);

  return `
<!DOCTYPE html>
<html>
<head>
  <base target="_top">
  <script type="text/javascript" src="https://www.gstatic.com/charts/loader.js"></script>
  <style>
    * {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }
    body {
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      overflow: hidden;
    }
    .header {
      background: rgba(255, 255, 255, 0.95);
      padding: 20px 30px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    h1 {
      color: #1a73e8;
      font-size: 24px;
      display: flex;
      align-items: center;
      gap: 10px;
    }
    .subtitle {
      color: #666;
      font-size: 14px;
      margin-top: 5px;
    }
    .tabs {
      display: flex;
      gap: 5px;
      padding: 15px 30px 0;
      background: rgba(255, 255, 255, 0.3);
    }
    .tab {
      padding: 12px 24px;
      background: rgba(255, 255, 255, 0.6);
      border: none;
      border-radius: 8px 8px 0 0;
      cursor: pointer;
      font-size: 14px;
      font-weight: 600;
      color: #555;
      transition: all 0.3s ease;
    }
    .tab:hover {
      background: rgba(255, 255, 255, 0.8);
      transform: translateY(-2px);
    }
    .tab.active {
      background: white;
      color: #1a73e8;
      box-shadow: 0 -2px 8px rgba(0,0,0,0.1);
    }
    .content {
      background: white;
      height: calc(100vh - 140px);
      overflow-y: auto;
      padding: 30px;
    }
    .tab-content {
      display: none;
      animation: fadeIn 0.5s ease;
    }
    .tab-content.active {
      display: block;
    }
    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(10px); }
      to { opacity: 1; transform: translateY(0); }
    }
    .chart-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 20px;
      margin-bottom: 20px;
    }
    .chart-container {
      background: #f8f9fa;
      padding: 20px;
      border-radius: 8px;
      box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .chart-container h3 {
      color: #333;
      margin-bottom: 15px;
      font-size: 16px;
    }
    .chart {
      width: 100%;
      height: 400px;
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
    table {
      width: 100%;
      border-collapse: collapse;
      margin-top: 20px;
      font-size: 13px;
      background: white;
    }
    th {
      background-color: #1a73e8;
      color: white;
      padding: 12px;
      text-align: left;
      font-weight: bold;
      position: sticky;
      top: 0;
      z-index: 10;
    }
    td {
      padding: 10px 12px;
      border-bottom: 1px solid #ddd;
    }
    tr:hover {
      background-color: #f5f5f5;
    }
    .table-container {
      max-height: 400px;
      overflow-y: auto;
      border: 1px solid #ddd;
      border-radius: 8px;
    }
    .urgency-badge {
      display: inline-block;
      padding: 4px 8px;
      border-radius: 12px;
      font-weight: bold;
      font-size: 11px;
    }
    .urgency-A { background-color: #dc3545; color: white; }
    .urgency-B { background-color: #ffc107; color: #333; }
    .urgency-C { background-color: #17a2b8; color: white; }
    .urgency-D { background-color: #6c757d; color: white; }
    .note {
      background-color: #fff3cd;
      border-left: 4px solid #ffc107;
      padding: 15px;
      margin: 20px 0;
      border-radius: 4px;
      font-size: 14px;
    }
  </style>
</head>
<body>
  <div class="header">
    <h1>🚀 Phase 10: 転職意欲・緊急度分析統合ダッシュボード</h1>
    <div class="subtitle">緊急度ランク（A-D）による求職者セグメンテーションと地域分析</div>
  </div>

  <div class="tabs">
    <button class="tab active" onclick="switchTab(0)">📊 緊急度分布</button>
    <button class="tab" onclick="switchTab(1)">👥 緊急度×年齢</button>
    <button class="tab" onclick="switchTab(2)">💼 緊急度×就業状態</button>
    <button class="tab" onclick="switchTab(3)">🔥 マトリックス</button>
    <button class="tab" onclick="switchTab(4)">🗺️ 市区町村別</button>
  </div>

  <div class="content">
    <!-- Tab 1: 緊急度分布 -->
    <div class="tab-content active" id="tab0">
      <div class="stats-summary" id="dist-stats"></div>

      <div class="note">
        <strong>📊 緊急度ランク説明:</strong>
        <ul style="margin: 10px 0; padding-left: 20px;">
          <li><strong>A: 高い</strong> - 緊急度スコア7以上（即座に対応すべき）</li>
          <li><strong>B: 中程度</strong> - 緊急度スコア5-7（優先的に対応）</li>
          <li><strong>C: やや低い</strong> - 緊急度スコア3-5（計画的に対応）</li>
          <li><strong>D: 低い</strong> - 緊急度スコア3未満（長期的に対応）</li>
        </ul>
      </div>

      <div class="chart-grid">
        <div class="chart-container">
          <h3>緊急度ランク別割合（円グラフ）</h3>
          <div id="pie_chart" class="chart"></div>
        </div>
        <div class="chart-container">
          <h3>緊急度ランク別人数（棒グラフ）</h3>
          <div id="bar_chart" class="chart"></div>
        </div>
      </div>

      <div class="table-container">
        <table id="dist-table">
          <thead>
            <tr>
              <th style="width: 30%;">緊急度ランク</th>
              <th style="width: 20%;">人数</th>
              <th style="width: 15%;">割合</th>
              <th style="width: 15%;">平均年齢</th>
              <th style="width: 20%;">平均緊急度スコア</th>
            </tr>
          </thead>
          <tbody id="dist-tbody"></tbody>
        </table>
      </div>
    </div>

    <!-- Tab 2: 緊急度×年齢 -->
    <div class="tab-content" id="tab1">
      <div class="stats-summary" id="age-stats"></div>
      <div class="chart-container">
        <h3>緊急度×年齢層グループ化縦棒グラフ</h3>
        <div id="age_column_chart" style="width: 100%; height: 500px;"></div>
      </div>
      <div class="table-container">
        <table id="age-table">
          <thead>
            <tr>
              <th style="width: 25%;">緊急度ランク</th>
              <th style="width: 20%;">年齢層</th>
              <th style="width: 15%;">人数</th>
              <th style="width: 15%;">平均年齢</th>
              <th style="width: 25%;">平均緊急度スコア</th>
            </tr>
          </thead>
          <tbody id="age-tbody"></tbody>
        </table>
      </div>
    </div>

    <!-- Tab 3: 緊急度×就業状態 -->
    <div class="tab-content" id="tab2">
      <div class="stats-summary" id="emp-stats"></div>
      <div class="chart-container">
        <h3>緊急度×就業状態グループ化縦棒グラフ</h3>
        <div id="emp_column_chart" style="width: 100%; height: 500px;"></div>
      </div>
      <div class="table-container">
        <table id="emp-table">
          <thead>
            <tr>
              <th style="width: 25%;">緊急度ランク</th>
              <th style="width: 20%;">就業状態</th>
              <th style="width: 15%;">人数</th>
              <th style="width: 15%;">平均年齢</th>
              <th style="width: 25%;">平均緊急度スコア</th>
            </tr>
          </thead>
          <tbody id="emp-tbody"></tbody>
        </table>
      </div>
    </div>

    <!-- Tab 4: マトリックス -->
    <div class="tab-content" id="tab3">
      <div class="stats-summary" id="matrix-stats"></div>
      <div class="chart-container">
        <h3>緊急度×年齢層ヒートマップ</h3>
        <div id="matrix-legend" style="display: flex; justify-content: center; margin-bottom: 15px; flex-wrap: wrap;"></div>
        <div style="overflow: auto; max-height: 600px; border: 1px solid #ddd; border-radius: 4px;">
          <table id="matrix-table"></table>
        </div>
      </div>
    </div>

    <!-- Tab 5: 市区町村別 -->
    <div class="tab-content" id="tab4">
      <div class="stats-summary" id="muni-stats"></div>
      <div class="chart-grid">
        <div class="chart-container">
          <h3>人数×緊急度スコア散布図</h3>
          <div id="scatter_chart" class="chart"></div>
        </div>
        <div class="chart-container">
          <h3>TOP20市区町村（人数順）</h3>
          <div id="muni_bar_chart" class="chart"></div>
        </div>
      </div>
      <div class="table-container">
        <table id="muni-table">
          <thead>
            <tr>
              <th style="width: 5%;">順位</th>
              <th style="width: 35%;">市区町村</th>
              <th style="width: 15%;">人数</th>
              <th style="width: 20%;">平均緊急度スコア</th>
              <th style="width: 25%;">緊急度ランク</th>
            </tr>
          </thead>
          <tbody id="muni-tbody"></tbody>
        </table>
      </div>
    </div>
  </div>

  <script type="text/javascript">
    // データ読み込み
    const urgencyDistData = ${urgencyDistJson};
    const urgencyAgeData = ${urgencyAgeJson};
    const urgencyEmpData = ${urgencyEmpJson};
    const urgencyMatrixData = ${urgencyMatrixJson};
    const urgencyMuniData = ${urgencyMuniJson};

    // 定義
    const urgencyOrder = ['A: 高い', 'B: 中程度', 'C: やや低い', 'D: 低い'];
    const ageGroupOrder = ['20代', '30代', '40代', '50代', '60代', '70歳以上'];
    const employmentOrder = ['在学中', '就業中', '離職中'];

    // ユーティリティ関数
    function getUrgencyRank(score) {
      if (score >= 7) return 'A: 高い';
      if (score >= 5) return 'B: 中程度';
      if (score >= 3) return 'C: やや低い';
      return 'D: 低い';
    }

    function getUrgencyBadgeClass(rank) {
      if (!rank) return '';
      if (rank.startsWith('A')) return 'urgency-A';
      if (rank.startsWith('B')) return 'urgency-B';
      if (rank.startsWith('C')) return 'urgency-C';
      if (rank.startsWith('D')) return 'urgency-D';
      return '';
    }

    function switchTab(index) {
      document.querySelectorAll('.tab').forEach((tab, i) => {
        tab.classList.toggle('active', i === index);
      });
      document.querySelectorAll('.tab-content').forEach((content, i) => {
        content.classList.toggle('active', i === index);
      });

      if (index === 0) {
        drawDistCharts();
      } else if (index === 1) {
        drawAgeChart();
      } else if (index === 2) {
        drawEmpChart();
      } else if (index === 3) {
        drawMatrixChart();
      } else if (index === 4) {
        drawMuniCharts();
      }
    }

    // Google Charts読み込み
    google.charts.load('current', {'packages':['corechart']});
    google.charts.setOnLoadCallback(initialize);

    function initialize() {
      renderAllStats();
      drawDistCharts();
      renderDistTable();
      renderAgeTable();
      renderEmpTable();
      renderMuniTable();
    }

    // 統計サマリー表示
    function renderAllStats() {
      renderDistStats();
      renderAgeStats();
      renderEmpStats();
      renderMatrixStats();
      renderMuniStats();
    }

    function renderDistStats() {
      const container = document.getElementById('dist-stats');
      const totalCount = urgencyDistData.reduce((sum, row) => sum + row.count, 0);
      const highUrgencyCount = urgencyDistData
        .filter(d => d.urgencyRank.startsWith('A') || d.urgencyRank.startsWith('B'))
        .reduce((sum, d) => sum + d.count, 0);
      const avgAge = urgencyDistData.reduce((sum, row) => sum + (row.avgAge || 0) * row.count, 0) / totalCount;
      const avgScore = urgencyDistData.reduce((sum, row) => sum + (row.avgUrgencyScore || 0) * row.count, 0) / totalCount;

      const stats = [
        {label: '総人数', value: totalCount.toLocaleString(), unit: '名'},
        {label: '高緊急度（A+B）', value: \`\${highUrgencyCount.toLocaleString()} (\${(highUrgencyCount/totalCount*100).toFixed(1)}%)\`, unit: ''},
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

    function renderAgeStats() {
      const container = document.getElementById('age-stats');
      const totalCount = urgencyAgeData.reduce((sum, row) => sum + row.count, 0);
      const uniqueAgeGroups = [...new Set(urgencyAgeData.map(d => d.ageGroup))].length;
      const avgScore = urgencyAgeData.reduce((sum, row) => sum + (row.avgUrgencyScore || 0) * row.count, 0) / totalCount;

      const stats = [
        {label: '緊急度ランク数', value: urgencyOrder.length, unit: 'ランク'},
        {label: '総人数', value: totalCount.toLocaleString(), unit: '名'},
        {label: '年齢層数', value: uniqueAgeGroups, unit: 'グループ'},
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

    function renderEmpStats() {
      const container = document.getElementById('emp-stats');
      const totalCount = urgencyEmpData.reduce((sum, row) => sum + row.count, 0);
      const uniqueEmp = [...new Set(urgencyEmpData.map(d => d.employmentStatus))].length;
      const avgScore = urgencyEmpData.reduce((sum, row) => sum + (row.avgUrgencyScore || 0) * row.count, 0) / totalCount;

      const stats = [
        {label: '緊急度ランク数', value: urgencyOrder.length, unit: 'ランク'},
        {label: '総人数', value: totalCount.toLocaleString(), unit: '名'},
        {label: '就業状態数', value: uniqueEmp, unit: '種類'},
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

    function renderMatrixStats() {
      const container = document.getElementById('matrix-stats');
      const metadata = urgencyMatrixData.metadata;

      const stats = [
        {label: '総緊急度ランク数', value: urgencyMatrixData.totalRows, unit: '種類'},
        {label: '総人数', value: metadata.totalCount.toLocaleString(), unit: '名'},
        {label: '最大値', value: metadata.max, unit: '名'},
        {label: '平均値', value: metadata.mean.toFixed(1), unit: '名'}
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

    function renderMuniStats() {
      const container = document.getElementById('muni-stats');
      const totalCount = urgencyMuniData.reduce((sum, row) => sum + row.count, 0);
      const avgScore = urgencyMuniData.reduce((sum, row) => sum + (row.avgUrgencyScore || 0) * row.count, 0) / totalCount;
      const highUrgencyCount = urgencyMuniData.filter(d => {
        const rank = getUrgencyRank(d.avgUrgencyScore || 0);
        return rank.startsWith('A') || rank.startsWith('B');
      }).length;

      const stats = [
        {label: '総市区町村数', value: urgencyMuniData.length.toLocaleString(), unit: '地域'},
        {label: '総人数', value: totalCount.toLocaleString(), unit: '名'},
        {label: '平均緊急度スコア', value: avgScore.toFixed(2), unit: '点'},
        {label: '高緊急度（A+B）地域', value: highUrgencyCount.toLocaleString(), unit: '地域'}
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

    // チャート描画
    function drawDistCharts() {
      // 円グラフ
      const pieData = new google.visualization.DataTable();
      pieData.addColumn('string', '緊急度ランク');
      pieData.addColumn('number', '人数');
      urgencyDistData.forEach(row => {
        pieData.addRow([row.urgencyRank, row.count]);
      });
      const pieOptions = {
        pieHole: 0.4,
        colors: ['#dc3545', '#ffc107', '#17a2b8', '#6c757d'],
        legend: {position: 'bottom'},
        chartArea: {width: '90%', height: '70%'}
      };
      const pieChart = new google.visualization.PieChart(document.getElementById('pie_chart'));
      pieChart.draw(pieData, pieOptions);

      // 棒グラフ
      const barData = new google.visualization.DataTable();
      barData.addColumn('string', '緊急度ランク');
      barData.addColumn('number', '人数');
      urgencyDistData.forEach(row => {
        barData.addRow([row.urgencyRank, row.count]);
      });
      const barOptions = {
        legend: {position: 'none'},
        chartArea: {width: '70%', height: '70%'},
        hAxis: {title: '人数', minValue: 0},
        vAxis: {title: '緊急度ランク'},
        colors: ['#667eea']
      };
      const barChart = new google.visualization.ColumnChart(document.getElementById('bar_chart'));
      barChart.draw(barData, barOptions);
    }

    function drawAgeChart() {
      const ageGroupMap = {};
      ageGroupOrder.forEach(ag => {
        ageGroupMap[ag] = {};
        urgencyOrder.forEach(ur => {
          ageGroupMap[ag][ur] = 0;
        });
      });

      urgencyAgeData.forEach(row => {
        if (ageGroupMap[row.ageGroup] && urgencyOrder.includes(row.urgencyRank)) {
          ageGroupMap[row.ageGroup][row.urgencyRank] = row.count;
        }
      });

      const chartData = new google.visualization.DataTable();
      chartData.addColumn('string', '年齢層');
      urgencyOrder.forEach(ur => {
        chartData.addColumn('number', ur);
      });

      ageGroupOrder.forEach(ag => {
        const row = [ag];
        urgencyOrder.forEach(ur => {
          row.push(ageGroupMap[ag][ur] || 0);
        });
        chartData.addRow(row);
      });

      const options = {
        title: '緊急度×年齢層グループ化縦棒グラフ',
        chartArea: {width: '70%', height: '70%'},
        hAxis: {title: '年齢層'},
        vAxis: {title: '人数', minValue: 0},
        isStacked: false,
        legend: {position: 'top', maxLines: 2},
        colors: ['#dc3545', '#ffc107', '#17a2b8', '#6c757d'],
        bar: {groupWidth: '75%'}
      };

      const chart = new google.visualization.ColumnChart(document.getElementById('age_column_chart'));
      chart.draw(chartData, options);
    }

    function drawEmpChart() {
      const employmentMap = {};
      employmentOrder.forEach(emp => {
        employmentMap[emp] = {};
        urgencyOrder.forEach(ur => {
          employmentMap[emp][ur] = 0;
        });
      });

      urgencyEmpData.forEach(row => {
        if (employmentMap[row.employmentStatus] && urgencyOrder.includes(row.urgencyRank)) {
          employmentMap[row.employmentStatus][row.urgencyRank] = row.count;
        }
      });

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
        hAxis: {title: '就業状態'},
        vAxis: {title: '人数', minValue: 0},
        isStacked: false,
        legend: {position: 'top', maxLines: 2},
        colors: ['#dc3545', '#ffc107', '#17a2b8', '#6c757d'],
        bar: {groupWidth: '75%'}
      };

      const chart = new google.visualization.ColumnChart(document.getElementById('emp_column_chart'));
      chart.draw(chartData, options);
    }

    function drawMatrixChart() {
      const metadata = urgencyMatrixData.metadata;
      const table = document.getElementById('matrix-table');
      table.innerHTML = '';

      // カラースケール
      function getHeatmapColor(value, max) {
        if (value === 0) return '#f8f9fa';
        const intensity = Math.min(value / max, 1);
        const r = 255;
        const g = Math.round(255 * (1 - intensity));
        const b = Math.round(255 * (1 - intensity));
        return \`rgb(\${r}, \${g}, \${b})\`;
      }

      // 凡例
      const legend = document.getEl       const item = document.createElement('div');
        item.style.cssText = 'margin: 5px 10px; display: flex; align-items: center;';
        const box = document.createElement('div');
        box.style.cssText = \`width: 30px; height: 20px; margin-right: 5px; border: 1px solid #ddd; background-color: \${getHeatmapColor(step.value, metadata.max)};\`;
        item.appendChild(box);
        item.appendChild(document.createTextNode(step.label));
        legend.appendChild(item);
      });

      // ヘッダー
      const thead = document.createElement('thead');
      const headerRow = document.createElement('tr');
      urgencyMatrixData.headers.forEach((header, index) => {
        const th = document.createElement('th');
        th.textContent = header;
        if (index === 0) th.style.cssText = 'min-width: 150px; text-align: left; position: sticky; left: 0; z-index: 11; background-color: #1a73e8;';
        else th.style.cssText = 'text-align: center;';
        headerRow.appendChild(th);
      });
      thead.appendChild(headerRow);
      table.appendChild(thead);

      // データ行
      const tbody = document.createElement('tbody');
      urgencyMatrixData.rows.forEach(row => {
        const tr = document.createElement('tr');
        row.forEach((cell, colIndex) => {
          const td = document.createElement('td');
          if (colIndex === 0) {
            td.textContent = cell;
            td.style.cssText = 'font-weight: bold; position: sticky; left: 0; background-color: #f8f9fa; z-index: 5; border-right: 2px solid #1a73e8;';
          } else {
            const value = Number(cell) || 0;
            td.textContent = value > 0 ? value : '－';
            td.style.cssText = \`text-align: center; background-color: \${getHeatmapColor(value, metadata.max)};\`;
            if (value > metadata.max * 0.6) {
              td.style.color = 'white';
              td.style.fontWeight = 'bold';
            }
          }
          tr.appendChild(td);
        });
        tbody.appendChild(tr);
      });
      table.appendChild(tbody);
    }

    function drawMuniCharts() {
      // 散布図
      const scatterData = new google.visualization.DataTable();
      scatterData.addColumn('number', '人数');
      scatterData.addColumn('number', '平均緊急度スコア');
      scatterData.addColumn({type: 'string', role: 'tooltip'});
      urgencyMuniData.forEach(row => {
        const tooltip = \`\${row.municipality}\\n人数: \${row.count}名\\n緊急度: \${row.avgUrgencyScore ? row.avgUrgencyScore.toFixed(2) : 'N/A'}点\`;
        scatterData.addRow([row.count, row.avgUrgencyScore || 0, tooltip]);
      });
      const scatterOptions = {
        hAxis: {title: '人数', minValue: 0},
        vAxis: {title: '平均緊急度スコア', minValue: 0, maxValue: 10},
        legend: 'none',
        pointSize: 5,
        colors: ['#667eea'],
        chartArea: {width: '75%', height: '70%'}
      };
      const scatterChart = new google.visualization.ScatterChart(document.getElementById('scatter_chart'));
      scatterChart.draw(scatterData, scatterOptions);

      // TOP20棒グラフ
      const sortedData = [...urgencyMuniData].sort((a, b) => b.count - a.count).slice(0, 20);
      const muniBarData = new google.visualization.DataTable();
      muniBarData.addColumn('string', '市区町村');
      muniBarData.addColumn('number', '人数');
      sortedData.forEach(row => {
        muniBarData.addRow([row.municipality, row.count]);
      });
      const muniBarOptions = {
        legend: {position: 'none'},
        chartArea: {width: '70%', height: '75%'},
        hAxis: {title: '人数', minValue: 0},
        colors: ['#4285F4']
      };
      const muniBarChart = new google.visualization.BarChart(document.getElementById('muni_bar_chart'));
      muniBarChart.draw(muniBarData, muniBarOptions);
    }

    // テーブル描画
    function renderDistTable() {
      const tbody = document.getElementById('dist-tbody');
      const totalCount = urgencyDistData.reduce((sum, row) => sum + row.count, 0);
      const sortedData = urgencyDistData.sort((a, b) => urgencyOrder.indexOf(a.urgencyRank) - urgencyOrder.indexOf(b.urgencyRank));

      sortedData.forEach(row => {
        const tr = document.createElement('tr');
        const badgeClass = getUrgencyBadgeClass(row.urgencyRank);
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

    function renderAgeTable() {
      const tbody = document.getElementById('age-tbody');
      const sortedData = urgencyAgeData.sort((a, b) => {
        const urgencyDiff = urgencyOrder.indexOf(a.urgencyRank) - urgencyOrder.indexOf(b.urgencyRank);
        if (urgencyDiff !== 0) return urgencyDiff;
        return ageGroupOrder.indexOf(a.ageGroup) - ageGroupOrder.indexOf(b.ageGroup);
      });

      let prevUrgency = null;
      sortedData.forEach(row => {
        const tr = document.createElement('tr');
        const badgeClass = getUrgencyBadgeClass(row.urgencyRank);
        const urgencyHtml = row.urgencyRank !== prevUrgency
          ? \`<span class="urgency-badge \${badgeClass}">\${row.urgencyRank}</span>\`
          : '';
        prevUrgency = row.urgencyRank;

        tr.innerHTML = \`
          <td>\${urgencyHtml}</td>
          <td>\${row.ageGroup}</td>
          <td style="text-align: right;"><strong>\${row.count.toLocaleString()}</strong>名</td>
          <td style="text-align: right;">\${row.avgAge ? row.avgAge.toFixed(1) + '歳' : '－'}</td>
          <td style="text-align: right;"><strong>\${row.avgUrgencyScore ? row.avgUrgencyScore.toFixed(2) : '－'}</strong>点</td>
        \`;
        tbody.appendChild(tr);
      });
    }

    function renderEmpTable() {
      const tbody = document.getElementById('emp-tbody');
      const sortedData = urgencyEmpData.sort((a, b) => {
        const urgencyDiff = urgencyOrder.indexOf(a.urgencyRank) - urgencyOrder.indexOf(b.urgencyRank);
        if (urgencyDiff !== 0) return urgencyDiff;
        return employmentOrder.indexOf(a.employmentStatus) - employmentOrder.indexOf(b.employmentStatus);
      });

      let prevUrgency = null;
      sortedData.forEach(row => {
        const tr = document.createElement('tr');
        const badgeClass = getUrgencyBadgeClass(row.urgencyRank);
        const urgencyHtml = row.urgencyRank !== prevUrgency
          ? \`<span class="urgency-badge \${badgeClass}">\${row.urgencyRank}</span>\`
          : '';
        prevUrgency = row.urgencyRank;

        tr.innerHTML = \`
          <td>\${urgencyHtml}</td>
          <td>\${row.employmentStatus}</td>
          <td style="text-align: right;"><strong>\${row.count.toLocaleString()}</strong>名</td>
          <td style="text-align: right;">\${row.avgAge ? row.avgAge.toFixed(1) + '歳' : '－'}</td>
          <td style="text-align: right;"><strong>\${row.avgUrgencyScore ? row.avgUrgencyScore.toFixed(2) : '－'}</strong>点</td>
        \`;
        tbody.appendChild(tr);
      });
    }

    function renderMuniTable() {
      const tbody = document.getElementById('muni-tbody');
      const sortedData = [...urgencyMuniData].sort((a, b) => b.count - a.count).slice(0, 100);

      sortedData.forEach((row, index) => {
        const tr = document.createElement('tr');
        const rank = getUrgencyRank(row.avgUrgencyScore || 0);
        const badgeClass = getUrgencyBadgeClass(rank);

        tr.innerHTML = \`
          <td style="text-align: center;"><strong>\${index + 1}</strong></td>
          <td><strong>\${row.municipality}</strong></td>
          <td style="text-align: right;"><strong>\${row.count.toLocaleString()}</strong>名</td>
          <td style="text-align: right;">\${row.avgUrgencyScore ? row.avgUrgencyScore.toFixed(2) : '－'}点</td>
          <td><span class="urgency-badge \${badgeClass}">\${rank}</span></td>
        \`;
        tbody.appendChild(tr);
      });
    }
  </script>
</body>
</html>
  `;
}

