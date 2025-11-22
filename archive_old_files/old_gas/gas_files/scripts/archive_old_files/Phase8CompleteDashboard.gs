/**
 * Phase 8 統合ダッシュボード
 *
 * Phase 8の全4機能を1つの画面で切り替えて表示する統合ダッシュボードです。
 */

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
