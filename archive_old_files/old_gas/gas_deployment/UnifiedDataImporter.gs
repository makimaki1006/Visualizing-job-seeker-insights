/**
 * 統合データインポーター
 *
 * このファイルには以下のデータインポート機能がすべて含まれています:
 * 1. Phase 7データインポート（高度分析データ）
 * 2. Phase 8データインポート（キャリア・学歴データ）
 * 3. Phase 10データインポート（転職意欲・緊急度データ）
 */

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 1. Phase 7データインポート
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

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


// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 2. Phase 8データインポート
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

// ===== Phase 8データロード関数 =====

function loadPhase8EducationDistribution() {
  /**
   * キャリア（学歴）分布データを読み込む【v2.3: career列使用】
   * @return {Array} - [{education_level, 人数, 割合}, ...]
   */
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getSheetByName('P8_CareerDist');  // 🔄 v2.3: P8_EducationDist → P8_CareerDist

  if (!sheet) {
    throw new Error('P8_CareerDistシートが見つかりません。先にデータをインポートしてください。');
  }

  var data = sheet.getDataRange().getValues();
  var headers = data[0];
  var rows = data.slice(1);

  return rows.map(function(row) {
    return {
      education_level: row[0],
      count: row[1],
      percentage: row[2]
    };
  });
}

function loadPhase8EducationAgeCross() {
  /**
   * キャリア（学歴）×年齢クロス集計データを読み込む（ロング形式）【v2.3: career列使用】
   * @return {Array} - [{education_level, 年齢層, カウント, サンプルサイズ区分, 信頼性レベル, 警告フラグ, 警告メッセージ}, ...]
   */
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getSheetByName('P8_CareerAgeCross');  // 🔄 v2.3: P8_EduAgeCross → P8_CareerAgeCross

  if (!sheet) {
    throw new Error('P8_CareerAgeCrossシートが見つかりません。');
  }

  var data = sheet.getDataRange().getValues();
  var headers = data[0];
  var rows = data.slice(1);

  return rows.map(function(row) {
    return {
      education_level: row[0],
      age_group: row[1],
      count: row[2],
      cell_quality: row[3] || 'SUFFICIENT',
      warning_flag: row[4] || 'なし',
      warning_message: row[5] || 'なし'
    };
  });
}

function loadPhase8EducationAgeMatrix() {
  /**
   * キャリア（学歴）×年齢マトリックスデータを読み込む【v2.3: career列使用】
   * @return {Object} - {headers: [...], rows: [[...], ...]}
   */
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getSheetByName('P8_CareerAgeMatrix');  // 🔄 v2.3: P8_EduAgeMatrix → P8_CareerAgeMatrix

  if (!sheet) {
    return null;  // Matrixは必須でない
  }

  var data = sheet.getDataRange().getValues();

  return {
    headers: data[0],
    rows: data.slice(1)
  };
}

function loadPhase8GraduationYearDistribution() {
  /**
   * 卒業年度分布データを読み込む
   * @return {Array} - [{graduation_year, 人数}, ...]
   */
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getSheetByName('P8_GradYearDist');

  if (!sheet) {
    return [];  // 卒業年はオプション
  }

  var data = sheet.getDataRange().getValues();
  var headers = data[0];
  var rows = data.slice(1);

  return rows.map(function(row) {
    return {
      graduation_year: row[0],
      count: row[1]
    };
  });
}

function loadPhase8QualityReport() {
  /**
   * Phase 8品質レポートを読み込む
   * @return {Object} - {score, status, columns: [...]}
   */
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getSheetByName('P8_QualityInfer');

  if (!sheet) {
    return {score: 0, status: 'NO_DATA', columns: []};
  }

  var data = sheet.getDataRange().getValues();
  var headers = data[0];
  var rows = data.slice(1);

  var columns = rows.map(function(row) {
    return {
      column_name: row[0],
      valid_count: row[1],
      unique_values: row[2],
      min_group_size: row[3],
      reliability_level: row[4],
      warning: row[5]
    };
  });

  // 総合スコア計算（簡易版）
  var reliableCount = columns.filter(function(c) {
    return c.reliability_level === 'HIGH' || c.reliability_level === 'MEDIUM';
  }).length;

  var score = columns.length > 0 ? (reliableCount / columns.length) * 100 : 0;
  var status = score >= 80 ? 'EXCELLENT' : score >= 60 ? 'GOOD' : score >= 40 ? 'ACCEPTABLE' : 'POOR';

  return {
    score: score,
    status: status,
    columns: columns
  };
}

// ===== Phase 8可視化関数 =====

function showPhase8EducationDistribution() {
  /**
   * 学歴分布グラフを表示
   */
  try {
    var data = loadPhase8EducationDistribution();

    if (data.length === 0) {
      SpreadsheetApp.getUi().alert('データがありません');
      return;
    }

    var html = generatePhase8EducationDistributionHTML(data);

    SpreadsheetApp.getUi().showModalDialog(
      html,
      'Phase 8: 学歴分布分析'
    );

  } catch (e) {
    SpreadsheetApp.getUi().alert('エラー: ' + e.toString());
  }
}

function generatePhase8EducationDistributionHTML(data) {
  /**
   * 学歴分布グラフHTML生成
   */

  // Google Charts用データ配列
  var chartData = [['学歴', '人数', '割合']];
  data.forEach(function(row) {
    chartData.push([
      row.education_level,
      row.count,
      row.percentage
    ]);
  });

  var html = HtmlService.createHtmlOutput();
  html.append('<script type="text/javascript" src="https://www.gstatic.com/charts/loader.js"></script>');
  html.append('<style>');
  html.append('body { font-family: Arial, sans-serif; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }');
  html.append('.container { background: white; border-radius: 12px; padding: 20px; box-shadow: 0 10px 40px rgba(0,0,0,0.1); }');
  html.append('h2 { color: #667eea; margin-top: 0; display: flex; align-items: center; }');
  html.append('h2 .icon { font-size: 32px; margin-right: 10px; }');
  html.append('.chart-container { margin: 20px 0; }');
  html.append('.stats-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin: 20px 0; }');
  html.append('.stat-card { background: #f8f9fa; border-radius: 8px; padding: 15px; text-align: center; }');
  html.append('.stat-value { font-size: 28px; font-weight: bold; color: #667eea; }');
  html.append('.stat-label { font-size: 12px; color: #666; margin-top: 5px; }');
  html.append('table { width: 100%; border-collapse: collapse; margin-top: 20px; }');
  html.append('th { background: #667eea; color: white; padding: 12px; text-align: left; }');
  html.append('td { padding: 10px; border-bottom: 1px solid #eee; }');
  html.append('tr:hover { background: #f8f9fa; }');
  html.append('</style>');

  html.append('<div class="container">');
  html.append('<h2><span class="icon">🎓</span>Phase 8: 学歴分布分析</h2>');

  // KPIカード
  var totalCount = data.reduce(function(sum, row) { return sum + row.count; }, 0);
  var maxEducation = data.reduce(function(max, row) {
    return row.count > max.count ? row : max;
  }, {education_level: '-', count: 0});

  html.append('<div class="stats-grid">');
  html.append('<div class="stat-card"><div class="stat-value">' + totalCount + '</div><div class="stat-label">総求職者数</div></div>');
  html.append('<div class="stat-card"><div class="stat-value">' + data.length + '</div><div class="stat-label">学歴区分数</div></div>');
  html.append('<div class="stat-card"><div class="stat-value">' + maxEducation.education_level + '</div><div class="stat-label">最多学歴</div></div>');
  html.append('</div>');

  // 棒グラフ
  html.append('<div class="chart-container" id="bar_chart" style="height: 400px;"></div>');

  // 円グラフ
  html.append('<div class="chart-container" id="pie_chart" style="height: 400px;"></div>');

  // 詳細テーブル
  html.append('<h3>詳細データ</h3>');
  html.append('<table>');
  html.append('<tr><th>学歴</th><th>人数</th><th>割合 (%)</th></tr>');
  data.forEach(function(row) {
    html.append('<tr>');
    html.append('<td>' + row.education_level + '</td>');
    html.append('<td>' + row.count.toLocaleString() + '名</td>');
    html.append('<td>' + (parseFloat(row.percentage) || 0).toFixed(2) + '%</td>');
    html.append('</tr>');
  });
  html.append('</table>');

  html.append('</div>');

  // Google Charts スクリプト
  html.append('<script>');
  html.append('google.charts.load("current", {packages:["corechart"]});');
  html.append('google.charts.setOnLoadCallback(drawCharts);');
  html.append('function drawCharts() {');

  // 棒グラフ
  html.append('var barData = google.visualization.arrayToDataTable(' + JSON.stringify(chartData) + ');');
  html.append('var barOptions = {');
  html.append('  title: "学歴別求職者数",');
  html.append('  titleTextStyle: {fontSize: 18, bold: true, color: "#667eea"},');
  html.append('  chartArea: {width: "70%", height: "70%"},');
  html.append('  hAxis: {title: "人数", titleTextStyle: {color: "#667eea"}},');
  html.append('  vAxis: {title: "学歴"},');
  html.append('  colors: ["#667eea"],');
  html.append('  legend: {position: "none"}');
  html.append('};');
  html.append('var barChart = new google.visualization.BarChart(document.getElementById("bar_chart"));');
  html.append('barChart.draw(barData, barOptions);');

  // 円グラフ
  html.append('var pieData = google.visualization.arrayToDataTable(' + JSON.stringify(chartData) + ');');
  html.append('var pieOptions = {');
  html.append('  title: "学歴分布割合",');
  html.append('  titleTextStyle: {fontSize: 18, bold: true, color: "#667eea"},');
  html.append('  chartArea: {width: "90%", height: "70%"},');
  html.append('  colors: ["#667eea", "#764ba2", "#f093fb", "#4facfe", "#00f2fe"],');
  html.append('  pieHole: 0.4,');
  html.append('  legend: {position: "right"}');
  html.append('};');
  html.append('var pieChart = new google.visualization.PieChart(document.getElementById("pie_chart"));');
  html.append('pieChart.draw(pieData, pieOptions);');

  html.append('}');
  html.append('</script>');

  html.setWidth(1000);
  html.setHeight(700);

  return html;
}

function showPhase8EducationAgeHeatmap() {
  /**
   * 学歴×年齢ヒートマップを表示
   */
  try {
    var matrixData = loadPhase8EducationAgeMatrix();

    if (!matrixData) {
      SpreadsheetApp.getUi().alert('Matrixデータがありません');
      return;
    }

    var html = generatePhase8HeatmapHTML(matrixData);

    SpreadsheetApp.getUi().showModalDialog(
      html,
      'Phase 8: 学歴×年齢ヒートマップ'
    );

  } catch (e) {
    SpreadsheetApp.getUi().alert('エラー: ' + e.toString());
  }
}

function generatePhase8HeatmapHTML(matrixData) {
  /**
   * ヒートマップHTML生成
   */

  var html = HtmlService.createHtmlOutput();
  html.append('<script type="text/javascript" src="https://www.gstatic.com/charts/loader.js"></script>');
  html.append('<style>');
  html.append('body { font-family: Arial, sans-serif; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }');
  html.append('.container { background: white; border-radius: 12px; padding: 20px; box-shadow: 0 10px 40px rgba(0,0,0,0.1); }');
  html.append('h2 { color: #667eea; margin-top: 0; }');
  html.append('.heatmap-container { margin: 20px 0; height: 500px; }');
  html.append('</style>');

  html.append('<div class="container">');
  html.append('<h2>🔥 Phase 8: 学歴×年齢ヒートマップ</h2>');
  html.append('<p>各セルの色が濃いほど求職者数が多いことを示します。</p>');
  html.append('<div class="heatmap-container" id="heatmap_chart"></div>');
  html.append('</div>');

  // Google Charts データ準備
  var chartData = [matrixData.headers];
  matrixData.rows.forEach(function(row) {
    chartData.push(row);
  });

  html.append('<script>');
  html.append('google.charts.load("current", {packages:["table"]});');
  html.append('google.charts.setOnLoadCallback(drawHeatmap);');
  html.append('function drawHeatmap() {');
  html.append('var data = google.visualization.arrayToDataTable(' + JSON.stringify(chartData) + ');');
  html.append('var table = new google.visualization.Table(document.getElementById("heatmap_chart"));');
  html.append('var options = {');
  html.append('  showRowNumber: false,');
  html.append('  width: "100%",');
  html.append('  height: "100%",');
  html.append('  allowHtml: true');
  html.append('};');
  html.append('table.draw(data, options);');

  // カラーフォーマット適用
  html.append('var formatter = new google.visualization.ColorFormat();');
  html.append('formatter.addGradientRange(0, 100, "#white", "#667eea", "#764ba2");');
  for (var i = 1; i < matrixData.headers.length; i++) {
    html.append('formatter.format(data, ' + i + ');');
  }
  html.append('table.draw(data, options);');

  html.append('}');
  html.append('</script>');

  html.setWidth(1000);
  html.setHeight(700);

  return html;
}

function showPhase8Dashboard() {
  /**
   * Phase 8統合ダッシュボード
   */
  try {
    var educationDist = loadPhase8EducationDistribution();
    var qualityReport = loadPhase8QualityReport();

    var html = generatePhase8DashboardHTML(educationDist, qualityReport);

    SpreadsheetApp.getUi().showModalDialog(
      html,
      'Phase 8: 学歴分析統合ダッシュボード'
    );

  } catch (e) {
    SpreadsheetApp.getUi().alert('エラー: ' + e.toString());
  }
}

function generatePhase8DashboardHTML(educationDist, qualityReport) {
  /**
   * Phase 8統合ダッシュボードHTML生成
   */

  var html = HtmlService.createHtmlOutput();
  html.append('<script type="text/javascript" src="https://www.gstatic.com/charts/loader.js"></script>');
  html.append('<style>');
  html.append('body { font-family: Arial, sans-serif; margin: 0; padding: 0; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }');
  html.append('.container { padding: 20px; }');
  html.append('.tabs { display: flex; background: white; border-radius: 12px 12px 0 0; overflow: hidden; }');
  html.append('.tab { padding: 15px 25px; cursor: pointer; background: #f8f9fa; border: none; font-size: 14px; font-weight: 600; transition: all 0.3s; }');
  html.append('.tab:hover { background: #e9ecef; }');
  html.append('.tab.active { background: white; color: #667eea; border-bottom: 3px solid #667eea; }');
  html.append('.tab-content { display: none; background: white; border-radius: 0 0 12px 12px; padding: 30px; min-height: 500px; }');
  html.append('.tab-content.active { display: block; }');
  html.append('h2 { color: #667eea; margin-top: 0; }');
  html.append('.chart-container { margin: 20px 0; height: 400px; }');
  html.append('.quality-badge { display: inline-block; padding: 5px 15px; border-radius: 20px; font-size: 12px; font-weight: bold; }');
  html.append('.quality-excellent { background: #10b981; color: white; }');
  html.append('.quality-good { background: #3b82f6; color: white; }');
  html.append('.quality-acceptable { background: #f59e0b; color: white; }');
  html.append('.quality-poor { background: #ef4444; color: white; }');
  html.append('</style>');

  html.append('<div class="container">');
  html.append('<div class="tabs">');
  html.append('<button class="tab active" data-tab="overview" onclick="showTab(\'overview\')">📋 概要</button>');
  html.append('<button class="tab" data-tab="education" onclick="showTab(\'education\')">🎓 学歴分布</button>');
  html.append('<button class="tab" data-tab="heatmap" onclick="showTab(\'heatmap\')">🔥 ヒートマップ</button>');
  html.append('<button class="tab" data-tab="quality" onclick="showTab(\'quality\')">✅ 品質レポート</button>');
  html.append('</div>');

  // 概要タブ
  html.append('<div id="overview" class="tab-content active">');
  html.append('<h2>📋 Phase 8: キャリア・学歴分析概要</h2>');
  html.append('<p>品質スコア: <span class="quality-badge quality-' + qualityReport.status.toLowerCase() + '">' + qualityReport.score.toFixed(1) + '/100点 (' + qualityReport.status + ')</span></p>');
  html.append('<p>総求職者数: ' + educationDist.reduce(function(sum, r) { return sum + r.count; }, 0).toLocaleString() + '名</p>');
  html.append('<p>学歴区分数: ' + educationDist.length + '種類</p>');
  html.append('<h3>分析内容</h3>');
  html.append('<ul>');
  html.append('<li>🎓 学歴分布: 各学歴レベルの求職者数と割合</li>');
  html.append('<li>🔥 学歴×年齢ヒートマップ: 学歴と年齢層のクロス分析</li>');
  html.append('<li>📅 卒業年度分布: 卒業年度別の求職者数</li>');
  html.append('</ul>');
  html.append('</div>');

  // 学歴分布タブ
  html.append('<div id="education" class="tab-content">');
  html.append('<h2>🎓 学歴分布</h2>');
  html.append('<div class="chart-container" id="education_chart"></div>');
  html.append('</div>');

  // ヒートマップタブ
  html.append('<div id="heatmap" class="tab-content">');
  html.append('<h2>🔥 キャリア（学歴）×年齢ヒートマップ</h2>');
  html.append('<p>Matrixデータが必要です。P8_CareerAgeMatrixシートを確認してください。</p>');  // 🔄 v2.3
  html.append('</div>');

  // 品質レポートタブ
  html.append('<div id="quality" class="tab-content">');
  html.append('<h2>✅ データ品質レポート</h2>');
  html.append('<p>品質スコア: <span class="quality-badge quality-' + qualityReport.status.toLowerCase() + '">' + qualityReport.score.toFixed(1) + '/100点</span></p>');
  html.append('<table style="width: 100%; border-collapse: collapse;">');
  html.append('<tr style="background: #667eea; color: white;"><th style="padding: 10px;">カラム名</th><th>有効データ数</th><th>信頼性レベル</th><th>警告</th></tr>');
  qualityReport.columns.forEach(function(col) {
    html.append('<tr style="border-bottom: 1px solid #eee;">');
    html.append('<td style="padding: 10px;">' + col.column_name + '</td>');
    html.append('<td>' + col.valid_count + '</td>');
    html.append('<td>' + col.reliability_level + '</td>');
    html.append('<td>' + col.warning + '</td>');
    html.append('</tr>');
  });
  html.append('</table>');
  html.append('</div>');

  html.append('</div>');

  // タブ切り替えスクリプト
  html.append('<script>');
  html.append('function showTab(tabName) {');
  html.append('  var tabs = document.querySelectorAll(".tab");');
  html.append('  var contents = document.querySelectorAll(".tab-content");');
  html.append('  tabs.forEach(function(t) { t.classList.remove("active"); });');
  html.append('  contents.forEach(function(c) { c.classList.remove("active"); });');
  html.append('  document.querySelectorAll(".tab").forEach(function(t) {');
  html.append('    if (t.getAttribute("data-tab") === tabName) {');
  html.append('      t.classList.add("active");');
  html.append('    }');
  html.append('  });');
  html.append('  document.getElementById(tabName).classList.add("active");');
  html.append('  if (tabName === "education" && !window.educationChartDrawn) {');
  html.append('    drawEducationChart();');
  html.append('    window.educationChartDrawn = true;');
  html.append('  }');
  html.append('}');

  // Google Charts
  var chartData = [['学歴', '人数']];
  educationDist.forEach(function(row) {
    chartData.push([row.education_level, row.count]);
  });

  html.append('google.charts.load("current", {packages:["corechart"]});');
  html.append('function drawEducationChart() {');
  html.append('var data = google.visualization.arrayToDataTable(' + JSON.stringify(chartData) + ');');
  html.append('var options = {');
  html.append('  title: "学歴別求職者数",');
  html.append('  titleTextStyle: {fontSize: 18, bold: true, color: "#667eea"},');
  html.append('  chartArea: {width: "70%", height: "70%"},');
  html.append('  colors: ["#667eea"],');
  html.append('  legend: {position: "none"}');
  html.append('};');
  html.append('var chart = new google.visualization.ColumnChart(document.getElementById("education_chart"));');
  html.append('chart.draw(data, options);');
  html.append('}');
  html.append('</script>');

  html.setWidth(1200);
  html.setHeight(800);

  return html;
}


// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 3. Phase 10データインポート
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

// ===== Phase 10データロード関数 =====

function loadPhase10UrgencyDistribution() {
  /**
   * Phase10 data loader (reuses shared logic)
   * @return {Array<Object>}
   */
  return loadUrgencyDistData();
}

function loadPhase10UrgencyAgeCross() {
  /**
   * Phase10 age cross loader (reuses shared logic)
   * @return {Array<Object>}
   */
  return loadUrgencyAgeCrossData();
}

function loadPhase10UrgencyAgeMatrix() {
  /**
   * Phase10 age matrix loader (reuses shared logic)
   * @return {Object|null}
   */
  return loadUrgencyAgeMatrixData();
}

function loadPhase10UrgencyEmploymentCross() {
  /**
   * Phase10 employment cross loader (reuses shared logic)
   * @return {Array<Object>}
   */
  return loadUrgencyEmploymentCrossData();
}

function loadPhase10QualityReport() {
  /**
   * Phase 10品質レポートを読み込む
   * @return {Object} - {score, status, columns: [...]}
   */
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getSheetByName('P10_QualityInfer');

  if (!sheet) {
    return {score: 0, status: 'NO_DATA', columns: []};
  }

  var data = sheet.getDataRange().getValues();
  var headers = data[0];
  var rows = data.slice(1);

  var columns = rows.map(function(row) {
    return {
      column_name: row[0],
      valid_count: row[1],
      unique_values: row[2],
      min_group_size: row[3],
      reliability_level: row[4],
      warning: row[5]
    };
  });

  // 総合スコア計算
  var reliableCount = columns.filter(function(c) {
    return c.reliability_level === 'HIGH' || c.reliability_level === 'MEDIUM';
  }).length;

  var score = columns.length > 0 ? (reliableCount / columns.length) * 100 : 0;
  var status = score >= 80 ? 'EXCELLENT' : score >= 60 ? 'GOOD' : score >= 40 ? 'ACCEPTABLE' : 'POOR';

  return {
    score: score,
    status: status,
    columns: columns
  };
}

// ===== Phase 10可視化関数 =====

function showPhase10UrgencyDistribution() {
  /**
   * 緊急度分布グラフを表示
   */
  try {
    var data = loadPhase10UrgencyDistribution();

    if (data.length === 0) {
      SpreadsheetApp.getUi().alert('データがありません');
      return;
    }

    var html = generatePhase10UrgencyDistributionHTML(data);

    SpreadsheetApp.getUi().showModalDialog(
      html,
      'Phase 10: 緊急度分布分析'
    );

  } catch (e) {
    SpreadsheetApp.getUi().alert('エラー: ' + e.toString());
  }
}

function generatePhase10UrgencyDistributionHTML(data) {
  /**
   * Builds urgency distribution dialog using shared visualization template.
   */
  var htmlString = generateUrgencyDistHTML(data);
  return HtmlService.createHtmlOutput(htmlString)
    .setWidth(1400)
    .setHeight(900);
}

function showPhase10UrgencyAgeHeatmap() {
  /**
   * 緊急度×年齢ヒートマップを表示
   */
  try {
    var matrixData = loadPhase10UrgencyAgeMatrix();

    if (!matrixData) {
      SpreadsheetApp.getUi().alert('Matrixデータがありません');
      return;
    }

    var html = generatePhase10HeatmapHTML(matrixData, '緊急度×年齢ヒートマップ');

    SpreadsheetApp.getUi().showModalDialog(
      html,
      'Phase 10: 緊急度×年齢ヒートマップ'
    );

  } catch (e) {
    SpreadsheetApp.getUi().alert('エラー: ' + e.toString());
  }
}


// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 複数Phase一括インポート（Upload_Enhanced.html用）
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

/**
 * 複数PhaseのCSVファイルを一括インポート
 * @param {Object} fileDataMap - Phase別ファイルデータマップ
 * @return {Object} インポート結果
 */
function importMultiplePhaseCSVs(fileDataMap) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const results = {
    totalFiles: 0,
    successCount: 0,
    errorCount: 0,
    details: []
  };

  // Phase別シート名マッピング
  const SHEET_NAME_MAP = {
    // Phase 1
    'Phase1_MapMetrics.csv': 'Phase1_MapMetrics',
    'MapMetrics.csv': 'Phase1_MapMetrics',
    'Phase1_Applicants.csv': 'Phase1_Applicants',
    'Applicants.csv': 'Phase1_Applicants',
    'Phase1_DesiredWork.csv': 'Phase1_DesiredWork',
    'DesiredWork.csv': 'Phase1_DesiredWork',
    'Phase1_AggDesired.csv': 'Phase1_AggDesired',
    'AggDesired.csv': 'Phase1_AggDesired',
    'P1_QualityReport.csv': 'Phase1_QualityReport',
    'QualityReport.csv': 'Phase1_QualityReport',
    'P1_QualityReport_Descriptive.csv': 'Phase1_QualityReport_Descriptive',
    'QualityReport_Descriptive.csv': 'Phase1_QualityReport_Descriptive',
    'P1_QualityDesc.csv': 'Phase1_QualityReport_Descriptive',

    // Phase 2
    'Phase2_ChiSquare.csv': 'Phase2_ChiSquare',
    'ChiSquareTests.csv': 'Phase2_ChiSquare',
    'Phase2_ANOVA.csv': 'Phase2_ANOVA',
    'ANOVATests.csv': 'Phase2_ANOVA',
    'P2_QualityReport_Inferential.csv': 'Phase2_QualityReport_Inferential',
    'QualityReport_Inferential.csv': 'Phase2_QualityReport_Inferential',

    // Phase 3
    'Phase3_PersonaSummary.csv': 'Phase3_PersonaSummary',
    'PersonaSummary.csv': 'Phase3_PersonaSummary',
    'Phase3_PersonaDetails.csv': 'Phase3_PersonaDetails',
    'PersonaDetails.csv': 'Phase3_PersonaDetails',
    'Phase3_PersonaByMunicipality.csv': 'Phase3_PersonaByMunicipality',
    'PersonaSummaryByMunicipality.csv': 'Phase3_PersonaByMunicipality',
    'P3_QualityReport_Inferential.csv': 'Phase3_QualityReport_Inferential',

    // Phase 6
    'Phase6_FlowEdges.csv': 'Phase6_FlowEdges',
    'MunicipalityFlowEdges.csv': 'Phase6_FlowEdges',
    'Phase6_MunicipalityFlowEdges.csv': 'Phase6_FlowEdges',
    'Phase6_FlowNodes.csv': 'Phase6_FlowNodes',
    'MunicipalityFlowNodes.csv': 'Phase6_FlowNodes',
    'Phase6_MunicipalityFlowNodes.csv': 'Phase6_FlowNodes',
    'Phase6_Proximity.csv': 'Phase6_Proximity',
    'ProximityAnalysis.csv': 'Phase6_Proximity',
    'Phase6_ProximityAnalysis.csv': 'Phase6_Proximity',
    'Phase6_AggregatedFlowEdges.csv': 'Phase6_AggregatedFlowEdges',
    'AggregatedFlowEdges.csv': 'Phase6_AggregatedFlowEdges',
    'P6_QualityReport_Inferential.csv': 'Phase6_QualityReport_Inferential',

    // Phase 7
    'Phase7_SupplyDensity.csv': 'Phase7_SupplyDensity',
    'SupplyDensityMap.csv': 'Phase7_SupplyDensity',
    'Phase7_SupplyDensityMap.csv': 'Phase7_SupplyDensity',
    'Phase7_QualificationDist.csv': 'Phase7_QualificationDist',
    'QualificationDistribution.csv': 'Phase7_QualificationDist',
    'Phase7_QualificationDistribution.csv': 'Phase7_QualificationDist',
    'Phase7_AgeGenderCross.csv': 'Phase7_AgeGenderCross',
    'AgeGenderCrossAnalysis.csv': 'Phase7_AgeGenderCross',
    'Phase7_AgeGenderCrossAnalysis.csv': 'Phase7_AgeGenderCross',
    'Phase7_MobilityScore.csv': 'Phase7_MobilityScore',
    'MobilityScore.csv': 'Phase7_MobilityScore',
    'Phase7_PersonaProfile.csv': 'Phase7_PersonaProfile',
    'DetailedPersonaProfile.csv': 'Phase7_PersonaProfile',
    'Phase7_DetailedPersonaProfile.csv': 'Phase7_PersonaProfile',
    'Phase7_PersonaMapData.csv': 'Phase7_PersonaMapData',
    'PersonaMapData.csv': 'Phase7_PersonaMapData',
    'Phase7_PersonaMobilityCross.csv': 'Phase7_PersonaMobilityCross',
    'PersonaMobilityCross.csv': 'Phase7_PersonaMobilityCross',
    'P7_QualityReport_Inferential.csv': 'Phase7_QualityReport_Inferential',

    // Phase 8
    'Phase8_EducationDist.csv': 'Phase8_EducationDist',
    'EducationDistribution.csv': 'Phase8_EducationDist',
    'Phase8_EduAgeCross.csv': 'Phase8_EduAgeCross',
    'EducationAgeCross.csv': 'Phase8_EduAgeCross',
    'Phase8_EduAgeMatrix.csv': 'Phase8_EduAgeMatrix',
    'EducationAgeCross_Matrix.csv': 'Phase8_EduAgeMatrix',
    'Phase8_GradYearDist.csv': 'Phase8_GradYearDist',
    'GraduationYearDistribution.csv': 'Phase8_GradYearDist',
    'Phase8_GraduationYearDistribution.csv': 'Phase8_GradYearDist',
    'Phase8_CareerDistribution.csv': 'Phase8_CareerDistribution',
    'CareerDistribution.csv': 'Phase8_CareerDistribution',
    'Phase8_CareerAgeCross.csv': 'Phase8_CareerAgeCross',
    'CareerAgeCross.csv': 'Phase8_CareerAgeCross',
    'Phase8_CareerAgeMatrix.csv': 'Phase8_CareerAgeMatrix',
    'CareerAgeCross_Matrix.csv': 'Phase8_CareerAgeMatrix',
    'P8_QualityReport.csv': 'Phase8_QualityReport',
    'P8_QualityReport_Inferential.csv': 'Phase8_QualityReport_Inferential',

    // Phase 10
    'Phase10_UrgencyDist.csv': 'Phase10_UrgencyDist',
    'UrgencyDistribution.csv': 'Phase10_UrgencyDist',
    'Phase10_UrgencyDistribution.csv': 'Phase10_UrgencyDist',
    'Phase10_UrgencyAge.csv': 'Phase10_UrgencyAge',
    'UrgencyAgeCross.csv': 'Phase10_UrgencyAge',
    'Phase10_UrgencyAgeCross.csv': 'Phase10_UrgencyAge',
    'Phase10_UrgencyAge_Matrix.csv': 'Phase10_UrgencyAge_Matrix',
    'UrgencyAgeCross_Matrix.csv': 'Phase10_UrgencyAge_Matrix',
    'Phase10_UrgencyAgeCross_Matrix.csv': 'Phase10_UrgencyAge_Matrix',
    'Phase10_UrgencyEmployment.csv': 'Phase10_UrgencyEmployment',
    'UrgencyEmploymentCross.csv': 'Phase10_UrgencyEmployment',
    'Phase10_UrgencyEmploymentCross.csv': 'Phase10_UrgencyEmployment',
    'Phase10_UrgencyEmployment_Matrix.csv': 'Phase10_UrgencyEmployment_Matrix',
    'UrgencyEmploymentCross_Matrix.csv': 'Phase10_UrgencyEmployment_Matrix',
    'Phase10_UrgencyEmploymentCross_Matrix.csv': 'Phase10_UrgencyEmployment_Matrix',
    'Phase10_UrgencyByMunicipality.csv': 'Phase10_UrgencyByMunicipality',
    'UrgencyByMunicipality.csv': 'Phase10_UrgencyByMunicipality',
    'Phase10_UrgencyAge_ByMunicipality.csv': 'Phase10_UrgencyAge_ByMunicipality',
    'UrgencyAgeCross_ByMunicipality.csv': 'Phase10_UrgencyAge_ByMunicipality',
    'Phase10_UrgencyAgeCross_ByMunicipality.csv': 'Phase10_UrgencyAge_ByMunicipality',
    'Phase10_UrgencyEmployment_ByMunicipality.csv': 'Phase10_UrgencyEmployment_ByMunicipality',
    'UrgencyEmploymentCross_ByMunicipality.csv': 'Phase10_UrgencyEmployment_ByMunicipality',
    'Phase10_UrgencyEmploymentCross_ByMunicipality.csv': 'Phase10_UrgencyEmployment_ByMunicipality',
    'P10_QualityReport.csv': 'Phase10_QualityReport',
    'P10_QualityReport_Inferential.csv': 'Phase10_QualityReport_Inferential',

    // Phase 1 - Additional Master Files
    'Phase1_EmploymentStatusMaster.csv': 'Phase1_EmploymentStatusMaster',
    'Phase1_PersonaByMunicipality_WithResidence.csv': 'Phase1_PersonaByMunicipality_WithResidence',
    'Phase1_PrefectureMaster.csv': 'Phase1_PrefectureMaster',
    'Phase1_QualificationDistributionByMunicipality.csv': 'Phase1_QualificationDistributionByMunicipality',
    'Phase1_QualificationMaster.csv': 'Phase1_QualificationMaster',

    // Phase 2 - Additional Naming Variants
    'Phase2_ChiSquareTests.csv': 'Phase2_ChiSquare',
    'Phase2_ANOVATests.csv': 'Phase2_ANOVA',

    // Phase 3 - Additional Municipality Data
    'Phase3_PersonaSummaryByMunicipality.csv': 'Phase3_PersonaSummaryByMunicipality',

    // Phase 8 - Additional Naming Variants
    'Phase8_CareerAgeCross_Matrix.csv': 'Phase8_CareerAgeMatrix',

    // Phase 10 - Additional Naming Variants
    'Phase10_UrgencyAgeCross.csv': 'Phase10_UrgencyAge',
    'Phase10_UrgencyEmploymentCross.csv': 'Phase10_UrgencyEmployment',

    // Phase 12 - Supply/Demand Gap Analysis
    'Phase12_SupplyDemandGap.csv': 'Phase12_SupplyDemandGap',
    'SupplyDemandGap.csv': 'Phase12_SupplyDemandGap',
    'P12_QualityReport.csv': 'Phase12_QualityReport',
    'P12_QualityReport_Descriptive.csv': 'Phase12_QualityReport_Descriptive',

    // Phase 13 - Rarity Score Analysis
    'Phase13_RarityScore.csv': 'Phase13_RarityScore',
    'RarityScore.csv': 'Phase13_RarityScore',
    'P13_QualityReport.csv': 'Phase13_QualityReport',
    'P13_QualityReport_Descriptive.csv': 'Phase13_QualityReport_Descriptive',

    // Phase 14 - Competition Profile Analysis
    'Phase14_CompetitionProfile.csv': 'Phase14_CompetitionProfile',
    'CompetitionProfile.csv': 'Phase14_CompetitionProfile',
    'P14_QualityReport.csv': 'Phase14_QualityReport',
    'P14_QualityReport_Descriptive.csv': 'Phase14_QualityReport_Descriptive'
  };



  try {
    // Phase別に処理
    for (const phase in fileDataMap) {
      const phaseFiles = fileDataMap[phase];

      Logger.log(`Processing ${phase}: ${Object.keys(phaseFiles).length} files`);

      // 各ファイルをインポート
      for (const fileName in phaseFiles) {
        results.totalFiles++;

        const fileData = phaseFiles[fileName];

        // シート名判定（MapComplete統合CSV対応）
        let sheetName;
        if (/^MapComplete_Complete_.+\.csv$/i.test(fileName)) {
          // MapComplete統合CSV: ファイル名から.csvを除去してシート名にする
          sheetName = fileName.replace('.csv', '');
        } else {
          // 通常のPhase CSV: SHEET_NAME_MAPから取得
          sheetName = SHEET_NAME_MAP[fileName];
        }

        if (!sheetName) {
          results.errorCount++;
          results.details.push({
            fileName: fileName,
            phase: phase,
            success: false,
            error: 'シート名マッピングが見つかりません'
          });
          Logger.log(`Warning: No sheet mapping for ${fileName}`);
          continue;
        }

        try {
          // CSVをパース
          const csvData = parseCSV(fileData.content);

          if (!csvData || csvData.length === 0) {
            throw new Error('CSVデータが空です');
          }

          // シートを作成または取得
          let sheet = ss.getSheetByName(sheetName);
          if (!sheet) {
            sheet = ss.insertSheet(sheetName);
          } else {
            sheet.clear();
          }

          // データをシートに書き込み
          const numRows = csvData.length;
          const numCols = csvData[0].length;

          sheet.getRange(1, 1, numRows, numCols).setValues(csvData);

          // ヘッダー行を太字にする
          if (numRows > 0) {
            sheet.getRange(1, 1, 1, numCols).setFontWeight('bold');
          }

          results.successCount++;
          results.details.push({
            fileName: fileName,
            phase: phase,
            sheetName: sheetName,
            success: true,
            rows: numRows,
            cols: numCols
          });

          Logger.log(`✓ ${fileName} → ${sheetName}: ${numRows} rows × ${numCols} cols`);

        } catch (error) {
          results.errorCount++;
          results.details.push({
            fileName: fileName,
            phase: phase,
            sheetName: sheetName,
            success: false,
            error: error.message
          });
          Logger.log(`✗ ${fileName} import failed: ${error.message}`);
        }
      }
    }

    Logger.log(`Import complete: ${results.successCount}/${results.totalFiles} files succeeded`);
    return results;

  } catch (error) {
    Logger.log(`Import error: ${error.message}`);
    throw new Error('インポート中にエラーが発生しました: ' + error.message);
  }
}


/**
 * CSV文字列をパース
 * @param {string} csvText - CSV文字列
 * @return {Array<Array>} 2次元配列
 */
function parseCSV(csvText) {
  if (!csvText || typeof csvText !== 'string') {
    throw new Error('Invalid CSV text');
  }

  const lines = csvText.split(/\r?\n/);
  const result = [];

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim();

    if (line.length === 0) {
      continue; // 空行をスキップ
    }

    // CSVパース（簡易版 - カンマ区切り）
    // ダブルクォート内のカンマを考慮
    const row = parseCSVLine(line);
    result.push(row);
  }

  return result;
}


/**
 * CSV行をパース（ダブルクォート対応）
 * @param {string} line - CSV行
 * @return {Array} パースされた配列
 */
function parseCSVLine(line) {
  const result = [];
  let current = '';
  let inQuotes = false;

  for (let i = 0; i < line.length; i++) {
    const char = line[i];

    if (char === '"') {
      if (inQuotes && line[i + 1] === '"') {
        // エスケープされたダブルクォート
        current += '"';
        i++; // 次の文字をスキップ
      } else {
        // クォートの開始/終了
        inQuotes = !inQuotes;
      }
    } else if (char === ',' && !inQuotes) {
      // フィールド区切り
      result.push(current.trim());
      current = '';
    } else {
      current += char;
    }
  }

  // 最後のフィールド
  result.push(current.trim());

  return result;
}

function generatePhase10HeatmapHTML(matrixData, title) {
  /**
   * ヒートマップHTML生成
   */

  var html = HtmlService.createHtmlOutput();
  html.append('<script type="text/javascript" src="https://www.gstatic.com/charts/loader.js"></script>');
  html.append('<style>');
  html.append('body { font-family: Arial, sans-serif; padding: 20px; background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); }');
  html.append('.container { background: white; border-radius: 12px; padding: 20px; box-shadow: 0 10px 40px rgba(0,0,0,0.1); }');
  html.append('h2 { color: #f5576c; margin-top: 0; }');
  html.append('.heatmap-container { margin: 20px 0; height: 500px; overflow: auto; }');
  html.append('table { width: 100%; border-collapse: collapse; }');
  html.append('th, td { padding: 10px; text-align: center; border: 1px solid #ddd; }');
  html.append('th { background: #f5576c; color: white; }');
  html.append('</style>');

  html.append('<div class="container">');
  html.append('<h2>🔥 ' + title + '</h2>');
  html.append('<p>各セルの数値が大きいほど該当する求職者数が多いことを示します。</p>');
  html.append('<div class="heatmap-container">');
  html.append('<table>');

  // ヘッダー行
  html.append('<tr>');
  matrixData.headers.forEach(function(header) {
    html.append('<th>' + header + '</th>');
  });
  html.append('</tr>');

  // データ行
  matrixData.rows.forEach(function(row) {
    html.append('<tr>');
    row.forEach(function(cell, index) {
      if (index === 0) {
        // 行ラベル
        html.append('<th>' + cell + '</th>');
      } else {
        // データセル
        var value = parseFloat(cell) || 0;
        var bgColor = value > 0 ? 'rgba(245, 87, 108, ' + Math.min(value / 100, 1) + ')' : '#fff';
        html.append('<td style="background: ' + bgColor + ';">' + cell + '</td>');
      }
    });
    html.append('</tr>');
  });

  html.append('</table>');
  html.append('</div>');
  html.append('</div>');

  html.setWidth(1000);
  html.setHeight(700);

  return html;
}

function showPhase10Dashboard() {
  try {
    var urgencyDist = loadUrgencyDistData();
    var urgencyAge = loadUrgencyAgeCrossData();
    var urgencyEmp = loadUrgencyEmploymentCrossData();
    var urgencyMatrix = loadUrgencyAgeMatrixData();
    var urgencyMuni = loadUrgencyByMunicipalityData();

    if (!urgencyDist || urgencyDist.length === 0) {
      SpreadsheetApp.getUi().alert('緊急度データが見つかりません。先に「Python結果CSVを取り込み」を実行してください。');
      return;
    }

    var htmlString = generatePhase10DashboardHTML({
      urgencyDist: urgencyDist,
      urgencyAge: urgencyAge,
      urgencyEmp: urgencyEmp,
      urgencyMatrix: urgencyMatrix,
      urgencyMuni: urgencyMuni
    });

    var htmlOutput = HtmlService.createHtmlOutput(htmlString)
      .setWidth(1500)
      .setHeight(950);

    SpreadsheetApp.getUi().showModalDialog(
      htmlOutput,
      'Phase 10: 転職意欲・緊急度ダッシュボード'
    );

  } catch (e) {
    SpreadsheetApp.getUi().alert('エラー: ' + e.toString());
  }
}




