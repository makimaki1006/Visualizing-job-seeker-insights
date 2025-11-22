/**
 * Phase 7 統合ダッシュボード
 *
 * Phase 7の全5機能を1つの画面で切り替えて表示する統合ダッシュボードです。
 */

/**
 * Phase 7統合ダッシュボード表示（メニューから呼び出し）
 */
function showPhase7CompleteDashboard() {
  const ui = SpreadsheetApp.getUi();

  try {
    // 全データ読み込み
    const dashboardData = loadAllPhase7Data();

    // データ存在確認
    const dataCount = Object.values(dashboardData).filter(d => d && d.length > 0).length;

    if (dataCount === 0) {
      ui.alert(
        'データなし',
        'Phase 7のデータがインポートされていません。\n\n' +
        '「Phase 7クイックインポート」を先に実行してください。',
        ui.ButtonSet.OK
      );
      return;
    }

    // HTML生成
    const html = generateCompleteDashboardHTML(dashboardData);

    // 全画面ダイアログ表示
    const htmlOutput = HtmlService.createHtmlOutput(html)
      .setWidth(1600)
      .setHeight(1000);

    ui.showModalDialog(htmlOutput, 'Phase 7: 完全統合ダッシュボード');

  } catch (error) {
    ui.alert('エラー', `ダッシュボード生成中にエラーが発生しました:\n${error.message}`, ui.ButtonSet.OK);
    Logger.log(`Phase 7ダッシュボードエラー: ${error.stack}`);
  }
}


/**
 * 全Phase 7データ読み込み
 * @return {Object} 全データを含むオブジェクト
 */
function loadAllPhase7Data() {
  const data = {
    supplyDensity: [],
    qualificationDist: [],
    ageGenderCross: [],
    mobilityScore: [],
    personaProfile: []
  };

  try {
    data.supplyDensity = loadSupplyDensityData();
  } catch (e) {
    Logger.log(`人材供給密度データ読み込みエラー: ${e.message}`);
  }

  try {
    data.qualificationDist = loadQualificationDistData();
  } catch (e) {
    Logger.log(`資格別人材分布データ読み込みエラー: ${e.message}`);
  }

  try {
    data.ageGenderCross = loadAgeGenderCrossData();
  } catch (e) {
    Logger.log(`年齢層×性別クロスデータ読み込みエラー: ${e.message}`);
  }

  try {
    data.mobilityScore = loadMobilityScoreData();
  } catch (e) {
    Logger.log(`移動許容度データ読み込みエラー: ${e.message}`);
  }

  try {
    data.personaProfile = loadPersonaProfileData();
  } catch (e) {
    Logger.log(`ペルソナプロファイルデータ読み込みエラー: ${e.message}`);
  }

  return data;
}


/**
 * 統合ダッシュボードHTML生成
 * @param {Object} dashboardData - 全データ
 * @return {string} HTML文字列
 */
function generateCompleteDashboardHTML(dashboardData) {
  // 各データをJSON文字列化
  const supplyDensityJson = JSON.stringify(dashboardData.supplyDensity || []);
  const qualificationDistJson = JSON.stringify(dashboardData.qualificationDist || []);
  const ageGenderCrossJson = JSON.stringify(dashboardData.ageGenderCross || []);
  const mobilityScoreJson = JSON.stringify(dashboardData.mobilityScore || []);
  const personaProfileJson = JSON.stringify(dashboardData.personaProfile || []);

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
      min-height: 100vh;
    }
    .dashboard-header {
      background: rgba(255,255,255,0.95);
      padding: 20px 40px;
      box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }
    .dashboard-header h1 {
      color: #1a73e8;
      font-size: 32px;
      margin-bottom: 10px;
    }
    .dashboard-header p {
      color: #666;
      font-size: 14px;
    }
    .tab-container {
      background: white;
      margin: 20px;
      border-radius: 12px;
      box-shadow: 0 4px 20px rgba(0,0,0,0.15);
      overflow: hidden;
    }
    .tabs {
      display: flex;
      background: #f5f5f5;
      border-bottom: 2px solid #ddd;
      padding: 0 20px;
    }
    .tab {
      padding: 15px 30px;
      cursor: pointer;
      border: none;
      background: transparent;
      font-size: 16px;
      font-weight: 500;
      color: #666;
      transition: all 0.3s;
      border-bottom: 3px solid transparent;
    }
    .tab:hover {
      background: rgba(26, 115, 232, 0.1);
      color: #1a73e8;
    }
    .tab.active {
      color: #1a73e8;
      border-bottom-color: #1a73e8;
      background: white;
    }
    .tab-content {
      display: none;
      padding: 30px;
      min-height: 700px;
    }
    .tab-content.active {
      display: block;
      animation: fadeIn 0.3s;
    }
    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(10px); }
      to { opacity: 1; transform: translateY(0); }
    }
    .kpi-grid {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 20px;
      margin-bottom: 30px;
    }
    .kpi-card {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      padding: 25px;
      border-radius: 12px;
      box-shadow: 0 4px 6px rgba(0,0,0,0.1);
      text-align: center;
    }
    .kpi-card.card-1 { background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); }
    .kpi-card.card-2 { background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); }
    .kpi-card.card-3 { background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); }
    .kpi-card.card-4 { background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); }
    .kpi-label {
      font-size: 14px;
      opacity: 0.9;
      margin-bottom: 10px;
    }
    .kpi-value {
      font-size: 36px;
      font-weight: bold;
    }
    .kpi-unit {
      font-size: 14px;
      opacity: 0.9;
      margin-top: 5px;
    }
    .chart-container {
      background: white;
      padding: 20px;
      border-radius: 8px;
      margin-bottom: 20px;
      box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .chart-container h2 {
      color: #333;
      margin-bottom: 15px;
      font-size: 20px;
    }
    .chart {
      width: 100%;
      height: 400px;
    }
  </style>
</head>
<body>
  <div class="dashboard-header">
    <h1>📊 Phase 7: 完全統合ダッシュボード</h1>
    <p>Python分析エンジンによる高度分析結果を、美しいUIで可視化</p>
  </div>

  <div class="tab-container">
    <div class="tabs">
      <button class="tab active" onclick="switchTab(0)">📋 概要</button>
      <button class="tab" onclick="switchTab(1)">🗺️ 人材供給密度</button>
      <button class="tab" onclick="switchTab(2)">🎓 資格分布</button>
      <button class="tab" onclick="switchTab(3)">👥 年齢×性別</button>
      <button class="tab" onclick="switchTab(4)">🚗 移動許容度</button>
      <button class="tab" onclick="switchTab(5)">📊 ペルソナ</button>
    </div>

    <!-- タブ0: 概要 -->
    <div class="tab-content active" id="tab-0">
      <h2>Phase 7データサマリー</h2>
      <div class="kpi-grid" id="overview-kpis"></div>

      <div class="chart-container">
        <h2>データ可用性</h2>
        <div id="overview_availability_chart" class="chart"></div>
      </div>
    </div>

    <!-- タブ1: 人材供給密度 -->
    <div class="tab-content" id="tab-1">
      <h2>人材供給密度マップ</h2>
      <div id="supply_density_chart" class="chart"></div>
    </div>

    <!-- タブ2: 資格分布 -->
    <div class="tab-content" id="tab-2">
      <h2>資格別人材分布</h2>
      <div id="qualification_dist_chart" class="chart"></div>
    </div>

    <!-- タブ3: 年齢×性別 -->
    <div class="tab-content" id="tab-3">
      <h2>年齢層×性別クロス分析</h2>
      <div id="age_gender_cross_chart" class="chart"></div>
    </div>

    <!-- タブ4: 移動許容度 -->
    <div class="tab-content" id="tab-4">
      <h2>移動許容度スコアリング</h2>
      <div id="mobility_score_chart" class="chart"></div>
    </div>

    <!-- タブ5: ペルソナ -->
    <div class="tab-content" id="tab-5">
      <h2>ペルソナ詳細プロファイル</h2>
      <div id="persona_profile_chart" class="chart"></div>
    </div>
  </div>

  <script type="text/javascript">
    // データ読み込み
    const supplyDensityData = ${supplyDensityJson};
    const qualificationDistData = ${qualificationDistJson};
    const ageGenderCrossData = ${ageGenderCrossJson};
    const mobilityScoreData = ${mobilityScoreJson};
    const personaProfileData = ${personaProfileJson};

    // Google Charts読み込み
    google.charts.load('current', {'packages':['corechart']});
    google.charts.setOnLoadCallback(initDashboard);

    function initDashboard() {
      renderOverviewKPIs();
      drawOverviewAvailabilityChart();
      // 他のチャートは必要に応じて遅延読み込み
    }

    // タブ切り替え
    function switchTab(tabIndex) {
      // 全タブを非アクティブ化
      document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
      document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));

      // 選択されたタブをアクティブ化
      document.querySelectorAll('.tab')[tabIndex].classList.add('active');
      document.getElementById(\`tab-\${tabIndex}\`).classList.add('active');

      // タブ別にチャート描画
      switch(tabIndex) {
        case 1:
          if (supplyDensityData.length > 0) drawSupplyDensityChart();
          break;
        case 2:
          if (qualificationDistData.length > 0) drawQualificationDistChart();
          break;
        case 3:
          if (ageGenderCrossData.length > 0) drawAgeGenderCrossChart();
          break;
        case 4:
          if (mobilityScoreData.length > 0) drawMobilityScoreChart();
          break;
        case 5:
          if (personaProfileData.length > 0) drawPersonaProfileChart();
          break;
      }
    }

    // 概要KPI表示
    function renderOverviewKPIs() {
      const container = document.getElementById('overview-kpis');

      const kpis = [
        {
          label: '人材供給密度',
          value: supplyDensityData.length,
          unit: '地域',
          cardClass: 'card-1'
        },
        {
          label: '資格カテゴリ',
          value: qualificationDistData.length,
          unit: '種類',
          cardClass: 'card-2'
        },
        {
          label: '分析地域',
          value: ageGenderCrossData.length,
          unit: '地域',
          cardClass: 'card-3'
        },
        {
          label: '求職者',
          value: mobilityScoreData.length.toLocaleString(),
          unit: '名',
          cardClass: 'card-4'
        }
      ];

      kpis.forEach(kpi => {
        const card = document.createElement('div');
        card.className = \`kpi-card \${kpi.cardClass}\`;
        card.innerHTML = \`
          <div class="kpi-label">\${kpi.label}</div>
          <div class="kpi-value">\${kpi.value}</div>
          <div class="kpi-unit">\${kpi.unit}</div>
        \`;
        container.appendChild(card);
      });
    }

    // データ可用性チャート
    function drawOverviewAvailabilityChart() {
      const chartData = new google.visualization.DataTable();
      chartData.addColumn('string', 'データセット');
      chartData.addColumn('number', 'レコード数');

      chartData.addRow(['人材供給密度', supplyDensityData.length]);
      chartData.addRow(['資格別人材分布', qualificationDistData.length]);
      chartData.addRow(['年齢層×性別', ageGenderCrossData.length]);
      chartData.addRow(['移動許容度', mobilityScoreData.length]);
      chartData.addRow(['ペルソナ', personaProfileData.length]);

      const options = {
        title: 'Phase 7データセット別レコード数',
        colors: ['#4285F4'],
        legend: {position: 'none'}
      };

      const chart = new google.visualization.ColumnChart(
        document.getElementById('overview_availability_chart')
      );

      chart.draw(chartData, options);
    }

    // 以下、各チャート描画関数（簡略版）
    function drawSupplyDensityChart() {
      const chartData = new google.visualization.DataTable();
      chartData.addColumn('string', '市区町村');
      chartData.addColumn('number', '総合スコア');

      const top10 = [...supplyDensityData]
        .sort((a, b) => b.compositeScore - a.compositeScore)
        .slice(0, 10);

      top10.forEach(row => {
        chartData.addRow([row.municipality, row.compositeScore]);
      });

      const options = {
        title: '人材供給密度TOP10',
        colors: ['#4285F4']
      };

      const chart = new google.visualization.BarChart(
        document.getElementById('supply_density_chart')
      );

      chart.draw(chartData, options);
    }

    function drawQualificationDistChart() {
      const chartData = new google.visualization.DataTable();
      chartData.addColumn('string', '資格カテゴリ');
      chartData.addColumn('number', '保有者数');

      qualificationDistData.forEach(row => {
        chartData.addRow([row.category, row.totalHolders]);
      });

      const options = {
        title: '資格カテゴリ別保有者数',
        colors: ['#34A853']
      };

      const chart = new google.visualization.BarChart(
        document.getElementById('qualification_dist_chart')
      );

      chart.draw(chartData, options);
    }

    function drawAgeGenderCrossChart() {
      const chartData = new google.visualization.DataTable();
      chartData.addColumn('string', '市区町村');
      chartData.addColumn('number', 'ダイバーシティスコア');

      ageGenderCrossData.forEach(row => {
        chartData.addRow([row.municipality, row.diversityScore]);
      });

      const options = {
        title: 'ダイバーシティスコア',
        colors: ['#FBBC04']
      };

      const chart = new google.visualization.ColumnChart(
        document.getElementById('age_gender_cross_chart')
      );

      chart.draw(chartData, options);
    }

    function drawMobilityScoreChart() {
      const chartData = new google.visualization.DataTable();
      chartData.addColumn('string', 'レベル');
      chartData.addColumn('number', '人数');

      const levels = ['A', 'B', 'C', 'D'];
      const levelCounts = {};

      levels.forEach(level => {
        levelCounts[level] = mobilityScoreData.filter(r => r.mobilityLevel === level).length;
      });

      chartData.addRow(['広域移動OK', levelCounts['A'] || 0]);
      chartData.addRow(['中距離OK', levelCounts['B'] || 0]);
      chartData.addRow(['近距離のみ', levelCounts['C'] || 0]);
      chartData.addRow(['地元限定', levelCounts['D'] || 0]);

      const options = {
        title: '移動許容度レベル別人数',
        pieHole: 0.4,
        colors: ['#4facfe', '#43e97b', '#fa709a', '#a8a8a8']
      };

      const chart = new google.visualization.PieChart(
        document.getElementById('mobility_score_chart')
      );

      chart.draw(chartData, options);
    }

    function drawPersonaProfileChart() {
      const chartData = new google.visualization.DataTable();
      chartData.addColumn('string', 'ペルソナ');
      chartData.addColumn('number', '人数');

      personaProfileData.forEach(row => {
        chartData.addRow([row.personaName, row.count]);
      });

      const options = {
        title: 'ペルソナ別人数分布',
        pieHole: 0.4,
        colors: ['#667eea', '#4facfe', '#43e97b', '#fa709a', '#f093fb']
      };

      const chart = new google.visualization.PieChart(
        document.getElementById('persona_profile_chart')
      );

      chart.draw(chartData, options);
    }
  </script>
</body>
</html>
  `;
}
