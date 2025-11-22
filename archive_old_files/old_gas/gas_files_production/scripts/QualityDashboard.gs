/**
 * データ品質ダッシュボード
 * 全Phaseの品質レポートを統合表示
 */

// ===== 品質データロード関数 =====

function loadAllQualityReports() {
  /**
   * 全Phaseの品質レポートを読み込む
   *
   * @return {Object} - {overall: {...}, phases: [{phase, score, status, columns}, ...]}
   */

  var ss = SpreadsheetApp.getActiveSpreadsheet();

  var qualityReports = {
    overall: null,
    phases: []
  };

  // 統合品質レポート
  var overallSheet = ss.getSheetByName('OverallQualityInfer');
  if (overallSheet) {
    qualityReports.overall = loadQualityReportFromSheet(overallSheet, 'Overall');
  }

  // Phase別品質レポート
  var phaseSheets = [
    {name: 'P1_QualityReport', phase: 1, label: 'Phase 1: 基礎集計（観察的記述）'},
    {name: 'P1_QualityDesc', phase: 1, label: 'Phase 1: 基礎集計（詳細）'},
    {name: 'P2_QualityInfer', phase: 2, label: 'Phase 2: 統計分析'},
    {name: 'P3_QualityInfer', phase: 3, label: 'Phase 3: ペルソナ分析'},
    {name: 'P6_QualityInfer', phase: 6, label: 'Phase 6: フロー分析'},
    {name: 'P7_QualityInfer', phase: 7, label: 'Phase 7: 高度分析'},
    {name: 'P8_QualityReport', phase: 8, label: 'Phase 8: 学歴分析（観察的記述）'},
    {name: 'P8_QualityInfer', phase: 8, label: 'Phase 8: 学歴分析（推論的考察）'},
    {name: 'P10_QualityReport', phase: 10, label: 'Phase 10: 緊急度分析（観察的記述）'},
    {name: 'P10_QualityInfer', phase: 10, label: 'Phase 10: 緊急度分析（推論的考察）'}
  ];

  phaseSheets.forEach(function(phaseInfo) {
    var sheet = ss.getSheetByName(phaseInfo.name);
    if (sheet) {
      var report = loadQualityReportFromSheet(sheet, phaseInfo.label);
      report.phase = phaseInfo.phase;
      qualityReports.phases.push(report);
    }
  });

  return qualityReports;
}

function loadQualityReportFromSheet(sheet, label) {
  /**
   * シートから品質レポートを読み込む
   *
   * @param {Sheet} sheet - シート
   * @param {string} label - ラベル
   * @return {Object} - 品質レポート
   */

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
      warning: row[5] || 'なし'
    };
  });

  // 総合スコア計算
  var reliableCount = columns.filter(function(c) {
    return c.reliability_level === 'HIGH' || c.reliability_level === 'MEDIUM' || c.reliability_level === 'DESCRIPTIVE';
  }).length;

  var score = columns.length > 0 ? (reliableCount / columns.length) * 100 : 0;
  var status = score >= 80 ? 'EXCELLENT' : score >= 60 ? 'GOOD' : score >= 40 ? 'ACCEPTABLE' : 'POOR';

  return {
    label: label,
    score: score,
    status: status,
    total_columns: columns.length,
    reliable_columns: reliableCount,
    columns: columns
  };
}

// ===== 品質ダッシュボード表示 =====

function showQualityDashboard() {
  /**
   * 品質ダッシュボードを表示
   */
  try {
    var qualityData = loadAllQualityReports();

    var html = generateQualityDashboardHTML(qualityData);

    SpreadsheetApp.getUi().showModalDialog(
      html,
      '📊 データ品質ダッシュボード'
    );

  } catch (e) {
    SpreadsheetApp.getUi().alert('エラー: ' + e.toString());
  }
}

function generateQualityDashboardHTML(qualityData) {
  /**
   * 品質ダッシュボードHTML生成
   *
   * @param {Object} qualityData - 品質データ
   * @return {HtmlOutput} - HTML出力
   */

  var html = HtmlService.createHtmlOutput();
  html.append('<script type="text/javascript" src="https://www.gstatic.com/charts/loader.js"></script>');
  html.append('<style>');
  html.append('body { font-family: Arial, sans-serif; margin: 0; padding: 0; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }');
  html.append('.container { padding: 20px; }');
  html.append('.header { background: white; border-radius: 12px; padding: 30px; margin-bottom: 20px; box-shadow: 0 10px 40px rgba(0,0,0,0.1); }');
  html.append('h1 { color: #667eea; margin: 0; display: flex; align-items: center; }');
  html.append('h1 .icon { font-size: 40px; margin-right: 15px; }');
  html.append('.stats-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-top: 20px; }');
  html.append('.stat-card { background: #f8f9fa; border-radius: 8px; padding: 20px; text-align: center; }');
  html.append('.stat-value { font-size: 32px; font-weight: bold; color: #667eea; }');
  html.append('.stat-label { font-size: 13px; color: #666; margin-top: 8px; }');
  html.append('.phase-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; }');
  html.append('.phase-card { background: white; border-radius: 12px; padding: 20px; box-shadow: 0 5px 20px rgba(0,0,0,0.1); }');
  html.append('.phase-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; }');
  html.append('.phase-title { font-size: 18px; font-weight: bold; color: #333; }');
  html.append('.quality-badge { display: inline-block; padding: 5px 15px; border-radius: 20px; font-size: 12px; font-weight: bold; }');
  html.append('.quality-excellent { background: #10b981; color: white; }');
  html.append('.quality-good { background: #3b82f6; color: white; }');
  html.append('.quality-acceptable { background: #f59e0b; color: white; }');
  html.append('.quality-poor { background: #ef4444; color: white; }');
  html.append('.quality-no-data { background: #6b7280; color: white; }');
  html.append('.progress-bar { width: 100%; height: 8px; background: #e5e7eb; border-radius: 4px; overflow: hidden; margin: 10px 0; }');
  html.append('.progress-fill { height: 100%; background: #667eea; transition: width 0.3s; }');
  html.append('.column-table { width: 100%; border-collapse: collapse; margin-top: 15px; font-size: 12px; }');
  html.append('.column-table th { background: #f8f9fa; padding: 8px; text-align: left; border-bottom: 2px solid #ddd; }');
  html.append('.column-table td { padding: 6px 8px; border-bottom: 1px solid #eee; }');
  html.append('.reliability-high { color: #10b981; font-weight: bold; }');
  html.append('.reliability-medium { color: #3b82f6; font-weight: bold; }');
  html.append('.reliability-low { color: #f59e0b; font-weight: bold; }');
  html.append('.reliability-critical { color: #ef4444; font-weight: bold; }');
  html.append('.reliability-descriptive { color: #6b7280; font-weight: bold; }');
  html.append('.chart-container { margin: 20px 0; height: 300px; }');
  html.append('</style>');

  html.append('<div class="container">');

  // ヘッダー
  html.append('<div class="header">');
  html.append('<h1><span class="icon">📊</span>データ品質ダッシュボード</h1>');

  // 統合統計
  var totalPhases = qualityData.phases.length;
  var excellentPhases = qualityData.phases.filter(function(p) { return p.status === 'EXCELLENT'; }).length;
  var avgScore = qualityData.phases.length > 0
    ? qualityData.phases.reduce(function(sum, p) { return sum + p.score; }, 0) / qualityData.phases.length
    : 0;
  var totalColumns = qualityData.phases.reduce(function(sum, p) { return sum + p.total_columns; }, 0);

  html.append('<div class="stats-grid">');
  html.append('<div class="stat-card"><div class="stat-value">' + totalPhases + '</div><div class="stat-label">分析Phase数</div></div>');
  html.append('<div class="stat-card"><div class="stat-value">' + avgScore.toFixed(1) + '</div><div class="stat-label">平均品質スコア</div></div>');
  html.append('<div class="stat-card"><div class="stat-value">' + excellentPhases + '</div><div class="stat-label">EXCELLENT Phase</div></div>');
  html.append('<div class="stat-card"><div class="stat-value">' + totalColumns + '</div><div class="stat-label">総カラム数</div></div>');
  html.append('</div>');

  // 品質スコアチャート
  html.append('<div class="chart-container" id="score_chart"></div>');

  html.append('</div>');

  // Phase別品質カード
  html.append('<div class="phase-grid">');

  qualityData.phases.forEach(function(phase) {
    html.append('<div class="phase-card">');
    html.append('<div class="phase-header">');
    html.append('<div class="phase-title">' + phase.label + '</div>');
    html.append('<span class="quality-badge quality-' + phase.status.toLowerCase() + '">' + phase.score.toFixed(1) + '/100 (' + phase.status + ')</span>');
    html.append('</div>');

    // プログレスバー
    html.append('<div class="progress-bar">');
    html.append('<div class="progress-fill" style="width: ' + phase.score + '%;"></div>');
    html.append('</div>');

    // 統計
    html.append('<p style="font-size: 13px; color: #666; margin: 10px 0;">');
    html.append('信頼できるカラム: ' + phase.reliable_columns + '/' + phase.total_columns + ' (' + (phase.total_columns > 0 ? ((phase.reliable_columns / phase.total_columns) * 100).toFixed(1) : 0) + '%)');
    html.append('</p>');

    // カラム詳細（最初の5件のみ表示）
    if (phase.columns.length > 0) {
      html.append('<table class="column-table">');
      html.append('<tr><th>カラム名</th><th>信頼性</th><th>警告</th></tr>');

      var displayColumns = phase.columns.slice(0, 5);
      displayColumns.forEach(function(col) {
        var reliabilityClass = 'reliability-' + col.reliability_level.toLowerCase();
        html.append('<tr>');
        html.append('<td>' + col.column_name + '</td>');
        html.append('<td class="' + reliabilityClass + '">' + col.reliability_level + '</td>');
        html.append('<td style="font-size: 11px;">' + (col.warning.length > 30 ? col.warning.substring(0, 30) + '...' : col.warning) + '</td>');
        html.append('</tr>');
      });

      if (phase.columns.length > 5) {
        html.append('<tr><td colspan="3" style="text-align: center; color: #999; font-size: 11px;">他 ' + (phase.columns.length - 5) + ' カラム...</td></tr>');
      }

      html.append('</table>');
    }

    html.append('</div>');
  });

  html.append('</div>');

  html.append('</div>');

  // Google Charts スクリプト
  html.append('<script>');
  html.append('google.charts.load("current", {packages:["corechart"]});');
  html.append('google.charts.setOnLoadCallback(drawScoreChart);');
  html.append('function drawScoreChart() {');

  // Phase別スコアグラフ用データ
  var chartData = [['Phase', 'スコア', {role: 'style'}]];
  qualityData.phases.forEach(function(phase) {
    var color = phase.score >= 80 ? '#10b981' : phase.score >= 60 ? '#3b82f6' : phase.score >= 40 ? '#f59e0b' : '#ef4444';
    chartData.push(['Phase ' + phase.phase, phase.score, color]);
  });

  html.append('var data = google.visualization.arrayToDataTable(' + JSON.stringify(chartData) + ');');
  html.append('var options = {');
  html.append('  title: "Phase別品質スコア",');
  html.append('  titleTextStyle: {fontSize: 16, bold: true, color: "#667eea"},');
  html.append('  chartArea: {width: "75%", height: "70%"},');
  html.append('  hAxis: {title: "品質スコア", minValue: 0, maxValue: 100},');
  html.append('  vAxis: {title: "Phase"},');
  html.append('  legend: {position: "none"},');
  html.append('  bar: {groupWidth: "70%"}');
  html.append('};');
  html.append('var chart = new google.visualization.BarChart(document.getElementById("score_chart"));');
  html.append('chart.draw(data, options);');

  html.append('}');
  html.append('</script>');

  html.setWidth(1400);
  html.setHeight(900);

  return html;
}

// ===== 品質レポート比較機能 =====

function comparePhaseQuality(phase1, phase2) {
  /**
   * 2つのPhaseの品質を比較
   *
   * @param {number} phase1 - Phase番号1
   * @param {number} phase2 - Phase番号2
   */
  try {
    var qualityData = loadAllQualityReports();

    var p1 = qualityData.phases.find(function(p) { return p.phase === phase1; });
    var p2 = qualityData.phases.find(function(p) { return p.phase === phase2; });

    if (!p1 || !p2) {
      SpreadsheetApp.getUi().alert('指定されたPhaseの品質レポートが見つかりません');
      return;
    }

    var html = generatePhaseComparisonHTML(p1, p2);

    SpreadsheetApp.getUi().showModalDialog(
      html,
      'Phase品質比較: Phase ' + phase1 + ' vs Phase ' + phase2
    );

  } catch (e) {
    SpreadsheetApp.getUi().alert('エラー: ' + e.toString());
  }
}

function generatePhaseComparisonHTML(p1, p2) {
  /**
   * Phase比較HTML生成
   */

  var html = HtmlService.createHtmlOutput();
  html.append('<style>');
  html.append('body { font-family: Arial, sans-serif; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }');
  html.append('.container { background: white; border-radius: 12px; padding: 20px; }');
  html.append('h2 { color: #667eea; }');
  html.append('.comparison-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }');
  html.append('.phase-panel { border: 1px solid #ddd; border-radius: 8px; padding: 20px; }');
  html.append('.quality-badge { display: inline-block; padding: 5px 15px; border-radius: 20px; font-size: 12px; font-weight: bold; }');
  html.append('.quality-excellent { background: #10b981; color: white; }');
  html.append('.quality-good { background: #3b82f6; color: white; }');
  html.append('.quality-acceptable { background: #f59e0b; color: white; }');
  html.append('.quality-poor { background: #ef4444; color: white; }');
  html.append('</style>');

  html.append('<div class="container">');
  html.append('<h2>Phase品質比較</h2>');
  html.append('<div class="comparison-grid">');

  // Phase 1
  html.append('<div class="phase-panel">');
  html.append('<h3>' + p1.label + '</h3>');
  html.append('<p>スコア: <span class="quality-badge quality-' + p1.status.toLowerCase() + '">' + p1.score.toFixed(1) + '/100</span></p>');
  html.append('<p>信頼できるカラム: ' + p1.reliable_columns + '/' + p1.total_columns + '</p>');
  html.append('</div>');

  // Phase 2
  html.append('<div class="phase-panel">');
  html.append('<h3>' + p2.label + '</h3>');
  html.append('<p>スコア: <span class="quality-badge quality-' + p2.status.toLowerCase() + '">' + p2.score.toFixed(1) + '/100</span></p>');
  html.append('<p>信頼できるカラム: ' + p2.reliable_columns + '/' + p2.total_columns + '</p>');
  html.append('</div>');

  html.append('</div>');
  html.append('</div>');

  html.setWidth(1000);
  html.setHeight(600);

  return html;
}
