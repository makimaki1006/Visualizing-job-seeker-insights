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
