// ===== Phase7: DataImporter =====
/**
 * Phase 7データインポート機能
 *
 * Phase 7の7つのCSVファイルをGoogleスプレッドシートにインポートします:
 * 1. SupplyDensityMap.csv - 人材供給密度マップ
 * 2. QualificationDistribution.csv - 資格別人材分布
 * 3. AgeGenderCrossAnalysis.csv - 年齢層×性別クロス分析
 * 4. MobilityScore.csv - 移動許容度スコアリング
 * 5. DetailedPersonaProfile.csv - ペルソナ詳細プロファイル
 * 6. PersonaMobilityCross.csv - ペルソナ×移動許容度クロス分析（GAS改良機能）
 * 7. PersonaMapData.csv - ペルソナ地図データ（座標付き）（GAS改良機能）
 */

/**
 * Phase 7データ一括インポート（メニューから呼び出し）
 */
function importPhase7Data() {
  const ui = SpreadsheetApp.getUi();

  // 確認ダイアログ
  const response = ui.alert(
    'Phase 7データインポート',
    'Phase 7の7つのCSVファイルをインポートしますか？\n\n' +
    '以下のシートが作成/更新されます：\n' +
    '1. Phase7_SupplyDensity\n' +
    '2. Phase7_QualificationDist\n' +
    '3. Phase7_AgeGenderCross\n' +
    '4. Phase7_MobilityScore\n' +
    '5. Phase7_PersonaProfile\n' +
    '6. Phase7_PersonaMobilityCross（GAS改良機能）\n' +
    '7. Phase7_PersonaMapData（GAS改良機能）',
    ui.ButtonSet.YES_NO
  );

  if (response !== ui.Button.YES) {
    ui.alert('キャンセルされました');
    return;
  }

  // インポート実行
  try {
    const results = importAllPhase7Files();

    // 結果表示
    let message = 'Phase 7データインポート完了！\n\n';
    results.forEach(result => {
      if (result.success) {
        message += `✓ ${result.fileName}: ${result.rows}行 × ${result.cols}列\n`;
      } else {
        message += `✗ ${result.fileName}: ${result.error}\n`;
      }
    });

    ui.alert('インポート結果', message, ui.ButtonSet.OK);

  } catch (error) {
    ui.alert('エラー', `インポート中にエラーが発生しました:\n${error.message}`, ui.ButtonSet.OK);
    Logger.log(`Phase 7インポートエラー: ${error.stack}`);
  }
}


/**
 * Phase 7全ファイルインポート（内部関数）
 * @return {Array<Object>} インポート結果の配列
 */
function importAllPhase7Files() {
  const files = [
    {
      fileName: 'SupplyDensityMap.csv',
      sheetName: 'Phase7_SupplyDensity',
      description: '人材供給密度マップ'
    },
    {
      fileName: 'QualificationDistribution.csv',
      sheetName: 'Phase7_QualificationDist',
      description: '資格別人材分布'
    },
    {
      fileName: 'AgeGenderCrossAnalysis.csv',
      sheetName: 'Phase7_AgeGenderCross',
      description: '年齢層×性別クロス分析'
    },
    {
      fileName: 'MobilityScore.csv',
      sheetName: 'Phase7_MobilityScore',
      description: '移動許容度スコアリング'
    },
    {
      fileName: 'DetailedPersonaProfile.csv',
      sheetName: 'Phase7_PersonaProfile',
      description: 'ペルソナ詳細プロファイル'
    },
    {
      fileName: 'PersonaMobilityCross.csv',
      sheetName: 'Phase7_PersonaMobilityCross',
      description: 'ペルソナ×移動許容度クロス分析'
    },
    {
      fileName: 'PersonaMapData.csv',
      sheetName: 'Phase7_PersonaMapData',
      description: 'ペルソナ地図データ（座標付き）'
    }
  ];

  const results = [];

  files.forEach(fileInfo => {
    try {
      const result = importPhase7File(fileInfo.fileName, fileInfo.sheetName);
      results.push({
        fileName: fileInfo.fileName,
        sheetName: fileInfo.sheetName,
        description: fileInfo.description,
        success: true,
        rows: result.rows,
        cols: result.cols
      });
      Logger.log(`✓ ${fileInfo.fileName}インポート成功: ${result.rows}行`);
    } catch (error) {
      results.push({
        fileName: fileInfo.fileName,
        sheetName: fileInfo.sheetName,
        description: fileInfo.description,
        success: false,
        error: error.message
      });
      Logger.log(`✗ ${fileInfo.fileName}インポート失敗: ${error.message}`);
    }
  });

  return results;
}


/**
 * 個別Phase 7ファイルインポート
 * @param {string} fileName - CSVファイル名
 * @param {string} sheetName - インポート先シート名
 * @return {Object} インポート結果
 */
function importPhase7File(fileName, sheetName) {
  // 注意: この関数は実際のファイルパスに基づいて実装する必要があります
  // ここではダミー実装を提供します

  // 実装方法1: Google DriveからCSVファイルを読み込む
  // 実装方法2: ユーザーにファイルアップロードを求める
  // 実装方法3: 直接データ配列を受け取る

  // 以下はダミーデータでの実装例
  throw new Error(`${fileName}のインポート機能は未実装です。ファイルパスを設定してください。`);
}


/**
 * CSVデータをシートにインポート（汎用関数）
 * @param {Array<Array>} data - CSV形式の2次元配列
 * @param {string} sheetName - インポート先シート名
 * @return {Object} インポート結果
 */
function importCSVDataToSheet(data, sheetName) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let sheet = ss.getSheetByName(sheetName);

  // シートが存在しない場合は新規作成
  if (!sheet) {
    sheet = ss.insertSheet(sheetName);
    Logger.log(`新規シート作成: ${sheetName}`);
  } else {
    // 既存シートの場合はクリア
    sheet.clear();
    Logger.log(`既存シートクリア: ${sheetName}`);
  }

  // データが空の場合
  if (!data || data.length === 0) {
    throw new Error('インポートするデータが空です');
  }

  // データをシートに書き込み
  const rows = data.length;
  const cols = data[0].length;

  sheet.getRange(1, 1, rows, cols).setValues(data);

  // ヘッダー行のフォーマット
  formatHeaderRow(sheet, cols);

  // 列幅自動調整
  for (let i = 1; i <= cols; i++) {
    sheet.autoResizeColumn(i);
  }

  Logger.log(`データ書き込み完了: ${rows}行 × ${cols}列`);

  return {
    rows: rows,
    cols: cols,
    sheetName: sheetName
  };
}


/**
 * ヘッダー行のフォーマット
 * @param {Sheet} sheet - 対象シート
 * @param {number} cols - 列数
 */
function formatHeaderRow(sheet, cols) {
  const headerRange = sheet.getRange(1, 1, 1, cols);

  headerRange
    .setBackground('#4285F4')
    .setFontColor('#FFFFFF')
    .setFontWeight('bold')
    .setHorizontalAlignment('center');

  // 固定表示
  sheet.setFrozenRows(1);
}


/**
 * Phase 7データ検証
 * 各シートのデータ整合性を検証します
 */
function validatePhase7Data() {
  const ui = SpreadsheetApp.getUi();
  const ss = SpreadsheetApp.getActiveSpreadsheet();

  const validations = [
    {
      sheetName: 'Phase7_SupplyDensity',
      requiredColumns: ['市区町村', '求職者数', '資格保有率', '平均年齢', '緊急度', '総合スコア', 'ランク']
    },
    {
      sheetName: 'Phase7_QualificationDist',
      requiredColumns: ['資格カテゴリ', '総保有者数', '分布TOP3', '希少地域TOP3']
    },
    {
      sheetName: 'Phase7_AgeGenderCross',
      requiredColumns: ['市区町村', '総求職者数', '支配的セグメント', '若年女性比率', '中年女性比率', 'ダイバーシティスコア']
    },
    {
      sheetName: 'Phase7_MobilityScore',
      requiredColumns: ['申請者ID', '希望地数', '最大移動距離km', '移動許容度スコア', '移動許容度レベル', '移動許容度', '居住地']
    },
    {
      sheetName: 'Phase7_PersonaProfile',
      requiredColumns: ['セグメントID', 'ペルソナ名', '人数', '構成比', '平均年齢', '女性比率', '資格保有率', '平均資格数', '平均希望地数', '緊急度', '主要居住地TOP3', '特徴']
    },
    {
      sheetName: 'Phase7_PersonaMobilityCross',
      requiredColumns: ['ペルソナID', 'ペルソナ名', 'A', 'B', 'C', 'D', '合計', 'A比率', 'B比率', 'C比率', 'D比率']
    },
    {
      sheetName: 'Phase7_PersonaMapData',
      requiredColumns: ['市区町村', '緯度', '経度', 'ペルソナID', 'ペルソナ名', '求職者数', '平均年齢', '女性比率', '資格保有率']
    }
  ];

  let message = 'Phase 7データ検証結果:\n\n';
  let allValid = true;

  validations.forEach(validation => {
    const sheet = ss.getSheetByName(validation.sheetName);

    if (!sheet) {
      message += `✗ ${validation.sheetName}: シートが見つかりません\n`;
      allValid = false;
      return;
    }

    // データ件数確認
    const lastRow = sheet.getLastRow();
    if (lastRow <= 1) {
      message += `✗ ${validation.sheetName}: データがありません\n`;
      allValid = false;
      return;
    }

    // カラム名確認
    const headers = sheet.getRange(1, 1, 1, validation.requiredColumns.length).getValues()[0];
    const missingColumns = validation.requiredColumns.filter(col => !headers.includes(col));

    if (missingColumns.length > 0) {
      message += `✗ ${validation.sheetName}: 必須カラムが不足 - ${missingColumns.join(', ')}\n`;
      allValid = false;
      return;
    }

    message += `✓ ${validation.sheetName}: OK (${lastRow - 1}行)\n`;
  });

  if (allValid) {
    message += '\n全てのPhase 7データが正常です！';
  } else {
    message += '\nエラーがあります。Phase 7データを再インポートしてください。';
  }

  ui.alert('データ検証結果', message, ui.ButtonSet.OK);
}


/**
 * Phase 7データサマリー表示
 */
function showPhase7DataSummary() {
  const ui = SpreadsheetApp.getUi();
  const ss = SpreadsheetApp.getActiveSpreadsheet();

  const sheets = [
    'Phase7_SupplyDensity',
    'Phase7_QualificationDist',
    'Phase7_AgeGenderCross',
    'Phase7_MobilityScore',
    'Phase7_PersonaProfile',
    'Phase7_PersonaMobilityCross',
    'Phase7_PersonaMapData'
  ];

  let message = 'Phase 7データサマリー:\n\n';

  sheets.forEach(sheetName => {
    const sheet = ss.getSheetByName(sheetName);

    if (!sheet) {
      message += `${sheetName}: データなし\n`;
      return;
    }

    const lastRow = sheet.getLastRow();
    const lastCol = sheet.getLastColumn();

    message += `${sheetName}:\n`;
    message += `  データ行数: ${lastRow - 1}行\n`;
    message += `  カラム数: ${lastCol}列\n\n`;
  });

  ui.alert('Phase 7データサマリー', message, ui.ButtonSet.OK);
}

// ===== Phase7: CompleteDashboard =====
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
