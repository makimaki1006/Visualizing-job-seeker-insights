/**
 * Phase 8: キャリア・学歴分析データインポーター
 * 6ファイルのインポートと可視化機能
 *
 * 【v2.3更新】career列使用版
 * - ファイル名: Education* → Career*
 * - シート名: P8_EducationDist → P8_CareerDist
 */

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
   * Phase 8品質レポートを読み込む（観察的記述 + 推論的考察）
   * @return {Object} - {descriptive: {...}, inferential: {...}}
   */
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var result = {
    descriptive: null,
    inferential: null
  };

  // P8_QualityReport（観察的記述）
  var descriptiveSheet = ss.getSheetByName('P8_QualityReport');
  if (descriptiveSheet) {
    result.descriptive = loadQualityReportFromSheet(descriptiveSheet);
  }

  // P8_QualityInfer（推論的考察）
  var inferentialSheet = ss.getSheetByName('P8_QualityInfer');
  if (inferentialSheet) {
    result.inferential = loadQualityReportFromSheet(inferentialSheet);
  }

  return result;
}

function loadQualityReportFromSheet(sheet) {
  /**
   * シートから品質レポートを読み込む共通関数
   * @param {Sheet} sheet - 品質レポートシート
   * @return {Object} - {score, status, columns: [...]}
   */
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
    html.append('<td>' + row.percentage.toFixed(2) + '%</td>');
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
