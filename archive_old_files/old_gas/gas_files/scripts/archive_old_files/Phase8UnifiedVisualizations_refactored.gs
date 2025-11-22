/**
 * Phase 8 統合可視化ファイル
 *
 * このファイルには以下の可視化機能がすべて含まれています:
 * 1. キャリア分布（TOP100）
 * 2. キャリア×年齢クロス分析
 * 3. キャリア×年齢マトリックス（ヒートマップ）
 * 4. 卒業年分布（1957-2030）
 * 5. Phase 8統合ダッシュボード
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
// 1. キャリア分布（TOP100）
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

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


// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 2. キャリア×年齢クロス分析
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

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


// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 3. キャリア×年齢マトリックス（ヒートマップ）
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

/**
 * キャリア×年齢マトリックス表示（メニューから呼び出し）
 */
function showCareerAgeMatrix() {
  const ui = SpreadsheetApp.getUi();

  try {
    // データ読み込み
    const data = loadCareerAgeMatrixData();

    if (!data || data.rows.length === 0) {
      ui.alert(
        'データなし',
        'P8_CareerAgeMatrixシートにデータがありません。\n' +
        '先に「Python結果CSVを取り込み」を実行してください。',
        ui.ButtonSet.OK
      );
      return;
    }

    // HTML生成
    const html = generateCareerAgeMatrixHTML(data);

    // ダイアログ表示
    const htmlOutput = HtmlService.createHtmlOutput(html)
      .setWidth(1400)
      .setHeight(900);

    ui.showModalDialog(htmlOutput, 'Phase 8: キャリア×年齢層マトリックス');

  } catch (error) {
    ui.alert('エラー', `可視化中にエラーが発生しました:\n${error.message}`, ui.ButtonSet.OK);
    Logger.log(`キャリア×年齢マトリックスエラー: ${error.stack}`);
  }
}


/**
 * キャリア×年齢マトリックスデータ読み込み
 * @return {Object} データオブジェクト
 */
function loadCareerAgeMatrixData() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName('P8_CareerAgeMatrix');

  if (!sheet) {
    throw new Error('P8_CareerAgeMatrixシートが見つかりません');
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

  // 各行の合計を計算してソート
  const rowsWithTotal = values.map(row => ({
    data: row,
    total: row.slice(1).reduce((sum, val) => sum + (Number(val) || 0), 0)
  }));

  // 合計の降順でソート、TOP100を抽出
  rowsWithTotal.sort((a, b) => b.total - a.total);
  const top100Rows = rowsWithTotal.slice(0, 100).map(item => item.data);

  // メタデータ計算
  const metadata = calculateMatrixMetadata(top100Rows);

  Logger.log(`キャリア×年齢マトリックスデータ読み込み: ${top100Rows.length}件（TOP100）`);

  return {
    headers,
    rows: top100Rows,
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
 * キャリア×年齢マトリックスHTML生成
 * @param {Object} data - データオブジェクト
 * @return {string} HTML文字列
 */
function generateCareerAgeMatrixHTML(data) {
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
      max-width: 300px;
      overflow: hidden;
      text-overflow: ellipsis;
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
  <h1>🔥 Phase 8: キャリア×年齢層マトリックス</h1>

  <div class="container">
    <h2>統計サマリー</h2>
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-label">総キャリア数</div>
        <div class="stat-value">${totalRows.toLocaleString()}</div>
        <div class="stat-label">種類</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">総人数（TOP100）</div>
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
    <h2>ヒートマップ（TOP100キャリア）</h2>
    <div class="note">
      <strong>📊 表示説明:</strong> 全${totalRows.toLocaleString()}種類のキャリアのうち、人数が多い上位100種類を抽出し、年齢層別の分布をヒートマップで表示しています。色が濃いほど人数が多いことを示します。
    </div>

    <div class="legend" id="legend"></div>

    <div class="heatmap-container">
      <table id="heatmap-table"></table>
    </div>
  </div>

  <script type="text/javascript">
    const data = ${dataJson};
    const metadata = ${JSON.stringify(metadata)};

    // カラースケール生成（青系グラデーション）
    function getHeatmapColor(value, max) {
      if (value === 0) return '#f8f9fa';  // 空セル

      const intensity = Math.min(value / max, 1);
      const r = Math.round(255 * (1 - intensity));
      const g = Math.round(255 * (1 - intensity * 0.5));
      const b = 255;

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
          th.style.minWidth = '300px';
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
            // キャリア名（行ヘッダー）
            td.className = 'row-header';
            td.textContent = cell;
            td.title = cell;  // ツールチップで全文表示
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
// 4. 卒業年分布（1957-2030）
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

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


// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 5. Phase 8統合ダッシュボード
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

/**
 * Phase 8統合ダッシュボード表示（メニューから呼び出し）
 */
function showPhase8CompleteDashboard() {
  const ui = SpreadsheetApp.getUi();

  try {
    // 全データ読み込み
    const dashboardData = loadAllPhase8Data();

    // データ存在確認
    const dataCount = Object.values(dashboardData).filter(d => d && (d.length > 0 || d.rows)).length;

    if (dataCount === 0) {
      ui.alert(
        'データなし',
        'Phase 8のデータがインポートされていません。\n\n' +
        '「Python結果CSVを取り込み」を先に実行してください。',
        ui.ButtonSet.OK
      );
      return;
    }

    // HTML生成
    const html = generatePhase8DashboardHTML(dashboardData);

    // 全画面ダイアログ表示
    const htmlOutput = HtmlService.createHtmlOutput(html)
      .setWidth(1600)
      .setHeight(1000);

    ui.showModalDialog(htmlOutput, 'Phase 8: キャリア・学歴分析 完全統合ダッシュボード');

  } catch (error) {
    ui.alert('エラー', `ダッシュボード生成中にエラーが発生しました:\n${error.message}`, ui.ButtonSet.OK);
    Logger.log(`Phase 8ダッシュボードエラー: ${error.stack}`);
  }
}


/**
 * 全Phase 8データ読み込み
 * @return {Object} 全データを含むオブジェクト
 */
function loadAllPhase8Data() {
  const data = {
    careerDist: [],
    careerAgeCross: [],
    careerAgeMatrix: null,
    graduationYear: []
  };

  try {
    data.careerDist = loadCareerDistData();
  } catch (e) {
    Logger.log(`キャリア分布データ読み込みエラー: ${e.message}`);
  }

  try {
    data.careerAgeCross = loadCareerAgeCrossData();
  } catch (e) {
    Logger.log(`キャリア×年齢クロスデータ読み込みエラー: ${e.message}`);
  }

  try {
    data.careerAgeMatrix = loadCareerAgeMatrixData();
  } catch (e) {
    Logger.log(`キャリア×年齢マトリックスデータ読み込みエラー: ${e.message}`);
  }

  try {
    data.graduationYear = loadGraduationYearData();
  } catch (e) {
    Logger.log(`卒業年分布データ読み込みエラー: ${e.message}`);
  }

  return data;
}


/**
 * Phase 8統合ダッシュボードHTML生成
 * @param {Object} dashboardData - 全データ
 * @return {string} HTML文字列
 */
function generatePhase8DashboardHTML(dashboardData) {
  // 各データをJSON文字列化
  const careerDistJson = JSON.stringify(dashboardData.careerDist.slice(0, 100));
  const careerAgeCrossJson = JSON.stringify(dashboardData.careerAgeCross.slice(0, 200));
  const careerAgeMatrixJson = JSON.stringify(dashboardData.careerAgeMatrix || {headers: [], rows: []});
  const graduationYearJson = JSON.stringify(dashboardData.graduationYear);

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
      background-color: #f5f5f5;
    }
    .dashboard-header {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      padding: 20px;
      text-align: center;
      box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    .dashboard-header h1 {
      font-size: 28px;
      margin-bottom: 10px;
    }
    .dashboard-header p {
      font-size: 14px;
      opacity: 0.9;
    }
    .tab-container {
      background-color: white;
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .tabs {
      display: flex;
      border-bottom: 2px solid #e0e0e0;
      overflow-x: auto;
    }
    .tab {
      padding: 15px 30px;
      cursor: pointer;
      border: none;
      background: none;
      font-size: 16px;
      color: #666;
      transition: all 0.3s;
      white-space: nowrap;
    }
    .tab:hover {
      background-color: #f5f5f5;
    }
    .tab.active {
      color: #667eea;
      border-bottom: 3px solid #667eea;
      font-weight: bold;
    }
    .tab-content {
      display: none;
      padding: 20px;
      animation: fadeIn 0.3s;
    }
    .tab-content.active {
      display: block;
    }
    @keyframes fadeIn {
      from { opacity: 0; }
      to { opacity: 1; }
    }
    .stats-summary {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 15px;
      margin-bottom: 20px;
    }
    .stat-card {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      padding: 20px;
      border-radius: 8px;
      text-align: center;
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
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
    .chart-container {
      background-color: white;
      padding: 20px;
      border-radius: 8px;
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
      margin-bottom: 20px;
    }
    .chart-title {
      font-size: 18px;
      font-weight: bold;
      color: #333;
      margin-bottom: 15px;
      padding-bottom: 10px;
      border-bottom: 2px solid #667eea;
    }
    .charts-row {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 20px;
      margin-bottom: 20px;
    }
    #career_dist_chart,
    #career_age_chart,
    #matrix_heatmap,
    #grad_year_line,
    #grad_year_area {
      width: 100%;
      height: 500px;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      font-size: 13px;
    }
    th {
      background-color: #667eea;
      color: white;
      padding: 12px;
      text-align: left;
      position: sticky;
      top: 0;
      z-index: 10;
    }
    td {
      padding: 10px;
      border-bottom: 1px solid #e0e0e0;
    }
    tr:hover {
      background-color: #f5f5f5;
    }
    .table-container {
      max-height: 400px;
      overflow-y: auto;
      border: 1px solid #e0e0e0;
      border-radius: 4px;
    }
    .note {
      background-color: #fff3cd;
      border-left: 4px solid #ffc107;
      padding: 15px;
      margin-bottom: 15px;
      border-radius: 4px;
    }
  </style>
</head>
<body>
  <div class="dashboard-header">
    <h1>💼🎓 Phase 8: キャリア・学歴分析 完全統合ダッシュボード</h1>
    <p>キャリア分布、キャリア×年齢クロス分析、マトリックス、卒業年分布の4つの分析を統合表示</p>
  </div>

  <div class="tab-container">
    <div class="tabs">
      <button class="tab active" onclick="switchTab(0)">💼 キャリア分布</button>
      <button class="tab" onclick="switchTab(1)">📊 キャリア×年齢クロス</button>
      <button class="tab" onclick="switchTab(2)">🔥 マトリックスヒートマップ</button>
      <button class="tab" onclick="switchTab(3)">🎓 卒業年分布</button>
    </div>

    <!-- Tab 1: キャリア分布 -->
    <div class="tab-content active" id="tab-0">
      <div class="note">
        <strong>💼 キャリア分布:</strong> 求職者のキャリア（職歴）の種類別人数を表示します。上位100種類を表示しています。
      </div>
      <div class="stats-summary" id="career-dist-stats"></div>
      <div class="chart-container">
        <div class="chart-title">キャリア別人数（TOP100）</div>
        <div id="career_dist_chart"></div>
      </div>
    </div>

    <!-- Tab 2: キャリア×年齢クロス -->
    <div class="tab-content" id="tab-1">
      <div class="note">
        <strong>📊 キャリア×年齢クロス:</strong> キャリアと年齢層のクロス集計を表示します。TOP30キャリアを年齢層別に色分けして表示しています。
      </div>
      <div class="stats-summary" id="career-age-stats"></div>
      <div class="chart-container">
        <div class="chart-title">キャリア×年齢層グループ化グラフ（TOP30）</div>
        <div id="career_age_chart"></div>
      </div>
    </div>

    <!-- Tab 3: マトリックスヒートマップ -->
    <div class="tab-content" id="tab-2">
      <div class="note">
        <strong>🔥 マトリックスヒートマップ:</strong> キャリア×年齢層のマトリックスをヒートマップで表示します。色が濃いほど人数が多いことを示します。TOP100キャリアを表示しています。
      </div>
      <div class="stats-summary" id="matrix-stats"></div>
      <div class="chart-container">
        <div class="chart-title">キャリア×年齢層ヒートマップ（TOP100）</div>
        <div id="matrix_heatmap"></div>
      </div>
    </div>

    <!-- Tab 4: 卒業年分布 -->
    <div class="tab-content" id="tab-3">
      <div class="note">
        <strong>🎓 卒業年分布:</strong> 求職者の卒業年（1957-2030）の分布をタイムラインで表示します。
      </div>
      <div class="stats-summary" id="grad-year-stats"></div>
      <div class="charts-row">
        <div class="chart-container">
          <div class="chart-title">卒業年別人数（ラインチャート）</div>
          <div id="grad_year_line"></div>
        </div>
        <div class="chart-container">
          <div class="chart-title">卒業年別人数（エリアチャート）</div>
          <div id="grad_year_area"></div>
        </div>
      </div>
    </div>
  </div>

  <script type="text/javascript">
    const careerDistData = ${careerDistJson};
    const careerAgeCrossData = ${careerAgeCrossJson};
    const careerAgeMatrixData = ${careerAgeMatrixJson};
    const graduationYearData = ${graduationYearJson};

    // Google Charts読み込み
    google.charts.load('current', {'packages':['corechart', 'table']});
    google.charts.setOnLoadCallback(initDashboard);

    // タブ切り替え
    function switchTab(index) {
      const tabs = document.querySelectorAll('.tab');
      const contents = document.querySelectorAll('.tab-content');

      tabs.forEach((tab, i) => {
        tab.classList.toggle('active', i === index);
      });

      contents.forEach((content, i) => {
        content.classList.toggle('active', i === index);
      });
    }

    function initDashboard() {
      renderCareerDistStats();
      renderCareerAgeStats();
      renderMatrixStats();
      renderGradYearStats();

      drawCareerDistChart();
      drawCareerAgeChart();
      drawMatrixHeatmap();
      drawGradYearCharts();
    }

    // Tab 1: キャリア分布統計
    function renderCareerDistStats() {
      const container = document.getElementById('career-dist-stats');
      const totalTypes = careerDistData.length;
      const totalCount = careerDistData.reduce((sum, d) => sum + d.count, 0);
      const avgCount = totalCount / totalTypes;

      const stats = [
        {label: 'キャリア種類数', value: totalTypes.toLocaleString(), unit: '種類'},
        {label: '総人数', value: totalCount.toLocaleString(), unit: '名'},
        {label: '平均人数/種類', value: Math.round(avgCount).toLocaleString(), unit: '名'}
      ];

      renderStats(container, stats);
    }

    function drawCareerDistChart() {
      const chartData = new google.visualization.DataTable();
      chartData.addColumn('string', 'キャリア');
      chartData.addColumn('number', '人数');

      careerDistData.slice(0, 30).forEach(row => {
        const label = row.career.length > 30 ? row.career.substring(0, 30) + '...' : row.career;
        chartData.addRow([label, row.count]);
      });

      const options = {
        chartArea: {width: '60%', height: '85%'},
        hAxis: { title: '人数', minValue: 0 },
        vAxis: { title: 'キャリア', textStyle: {fontSize: 11} },
        colors: ['#667eea'],
        legend: {position: 'none'}
      };

      new google.visualization.BarChart(
        document.getElementById('career_dist_chart')
      ).draw(chartData, options);
    }

    // Tab 2: キャリア×年齢クロス統計
    function renderCareerAgeStats() {
      const container = document.getElementById('career-age-stats');
      const uniqueCareers = [...new Set(careerAgeCrossData.map(d => d.career))].length;
      const totalCount = careerAgeCrossData.reduce((sum, d) => sum + d.count, 0);
      const uniqueAgeGroups = [...new Set(careerAgeCrossData.map(d => d.ageGroup))].length;

      const stats = [
        {label: 'キャリア数', value: uniqueCareers, unit: '種類'},
        {label: '総人数', value: totalCount.toLocaleString(), unit: '名'},
        {label: '年齢層数', value: uniqueAgeGroups, unit: 'グループ'}
      ];

      renderStats(container, stats);
    }

    function drawCareerAgeChart() {
      const ageGroupOrder = ['20代', '30代', '40代', '50代', '60代', '70歳以上'];

      // TOP20キャリアを抽出してピボット
      const careerTotals = {};
      careerAgeCrossData.forEach(row => {
        if (!careerTotals[row.career]) careerTotals[row.career] = 0;
        careerTotals[row.career] += row.count;
      });

      const top20Careers = Object.entries(careerTotals)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 20)
        .map(e => e[0]);

      const careerMap = {};
      careerAgeCrossData.filter(d => top20Careers.includes(d.career)).forEach(row => {
        if (!careerMap[row.career]) {
          careerMap[row.career] = {};
          ageGroupOrder.forEach(ag => { careerMap[row.career][ag] = 0; });
        }
        careerMap[row.career][row.ageGroup] = row.count;
      });

      const sortedCareers = Object.entries(careerMap)
        .map(([career, ageData]) => ({
          career,
          total: Object.values(ageData).reduce((sum, v) => sum + v, 0),
          ageData
        }))
        .sort((a, b) => b.total - a.total);

      const chartData = new google.visualization.DataTable();
      chartData.addColumn('string', 'キャリア');
      ageGroupOrder.forEach(ag => chartData.addColumn('number', ag));

      sortedCareers.forEach(item => {
        const label = item.career.length > 25 ? item.career.substring(0, 25) + '...' : item.career;
        const row = [label];
        ageGroupOrder.forEach(ag => row.push(item.ageData[ag] || 0));
        chartData.addRow(row);
      });

      const options = {
        chartArea: {width: '50%', height: '85%'},
        hAxis: { title: '人数', minValue: 0 },
        vAxis: { title: 'キャリア', textStyle: {fontSize: 10} },
        isStacked: false,
        legend: {position: 'top'},
        colors: ['#4285F4', '#AA46BE', '#F4B400', '#DB4437', '#0F9D58', '#00ACC1']
      };

      new google.visualization.BarChart(
        document.getElementById('career_age_chart')
      ).draw(chartData, options);
    }

    // Tab 3: マトリックス統計
    function renderMatrixStats() {
      const container = document.getElementById('matrix-stats');
      const metadata = careerAgeMatrixData.metadata || {};

      const stats = [
        {label: 'キャリア数', value: (careerAgeMatrixData.rows || []).length, unit: '種類'},
        {label: '総人数', value: (metadata.totalCount || 0).toLocaleString(), unit: '名'},
        {label: '最大値', value: metadata.max || 0, unit: '名'}
      ];

      renderStats(container, stats);
    }

    function drawMatrixHeatmap() {
      const container = document.getElementById('matrix_heatmap');
      if (!careerAgeMatrixData.rows || careerAgeMatrixData.rows.length === 0) {
        container.innerHTML = '<p style="text-align: center; padding: 50px; color: #666;">マトリックスデータがありません</p>';
        return;
      }

      // 簡易ヒートマップ表示（TOP20）
      const top20Rows = careerAgeMatrixData.rows.slice(0, 20);
      const max = careerAgeMatrixData.metadata.max || 1;

      let html = '<table style="width: 100%; font-size: 12px;"><thead><tr>';
      careerAgeMatrixData.headers.forEach((h, i) => {
        html += \`<th style="background: #667eea; color: white; padding: 10px; \${i === 0 ? 'text-align: left;' : 'text-align: center;'}">\${h}</th>\`;
      });
      html += '</tr></thead><tbody>';

      top20Rows.forEach(row => {
        html += '<tr>';
        row.forEach((cell, i) => {
          if (i === 0) {
            const label = String(cell).length > 30 ? String(cell).substring(0, 30) + '...' : cell;
            html += \`<td style="padding: 8px; font-weight: bold;">\${label}</td>\`;
          } else {
            const val = Number(cell) || 0;
            const intensity = Math.min(val / max, 1);
            const r = Math.round(255 * (1 - intensity));
            const g = Math.round(255 * (1 - intensity * 0.5));
            const bgColor = val > 0 ? \`rgb(\${r}, \${g}, 255)\` : '#f8f9fa';
            const textColor = val > max * 0.6 ? 'white' : 'black';
            html += \`<td style="padding: 8px; text-align: center; background: \${bgColor}; color: \${textColor};">\${val > 0 ? val : '－'}</td>\`;
          }
        });
        html += '</tr>';
      });

      html += '</tbody></table>';
      container.innerHTML = html;
    }

    // Tab 4: 卒業年統計
    function renderGradYearStats() {
      const container = document.getElementById('grad-year-stats');
      const totalYears = graduationYearData.length;
      const totalCount = graduationYearData.reduce((sum, d) => sum + d.count, 0);
      const minYear = Math.min(...graduationYearData.map(d => d.graduationYear));
      const maxYear = Math.max(...graduationYearData.map(d => d.graduationYear));

      const stats = [
        {label: '卒業年範囲', value: \`\${minYear}-\${maxYear}\`, unit: ''},
        {label: '総人数', value: totalCount.toLocaleString(), unit: '名'},
        {label: '年数', value: totalYears, unit: '年分'}
      ];

      renderStats(container, stats);
    }

    function drawGradYearCharts() {
      // ラインチャート
      const lineData = new google.visualization.DataTable();
      lineData.addColumn('string', '卒業年');
      lineData.addColumn('number', '人数');
      graduationYearData.forEach(d => lineData.addRow([d.graduationYear.toString(), d.count]));

      new google.visualization.LineChart(
        document.getElementById('grad_year_line')
      ).draw(lineData, {
        curveType: 'function',
        legend: {position: 'none'},
        chartArea: {width: '80%', height: '70%'},
        hAxis: { slantedText: true, slantedTextAngle: 45 },
        vAxis: { title: '人数', minValue: 0 },
        colors: ['#667eea']
      });

      // エリアチャート
      const areaData = new google.visualization.DataTable();
      areaData.addColumn('string', '卒業年');
      areaData.addColumn('number', '人数');
      graduationYearData.forEach(d => areaData.addRow([d.graduationYear.toString(), d.count]));

      new google.visualization.AreaChart(
        document.getElementById('grad_year_area')
      ).draw(areaData, {
        legend: {position: 'none'},
        chartArea: {width: '80%', height: '70%'},
        hAxis: { slantedText: true, slantedTextAngle: 45 },
        vAxis: { title: '人数', minValue: 0 },
        colors: ['#34A853']
      });
    }

    // 共通統計表示関数
    function renderStats(container, stats) {
      container.innerHTML = '';
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
  </script>
</body>
</html>
  `;
}


