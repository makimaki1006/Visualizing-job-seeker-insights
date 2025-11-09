// ===== Phase10: DataImporter =====
/**
 * Phase 10: 転職意欲・緊急度分析データインポーター
 * 7ファイルのインポートと可視化機能
 */

// ===== Phase 10データロード関数 =====

function loadPhase10UrgencyDistribution() {
  /**
   * 緊急度分布データを読み込む
   * @return {Array} - [{urgency_score, 緊急度, 人数, 割合}, ...]
   */
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getSheetByName('P10_UrgencyDist');

  if (!sheet) {
    throw new Error('P10_UrgencyDistシートが見つかりません。先にデータをインポートしてください。');
  }

  var data = sheet.getDataRange().getValues();
  var headers = data[0];
  var rows = data.slice(1);

  return rows.map(function(row) {
    return {
      urgency_score: row[0],
      urgency_label: row[1],
      count: row[2],
      percentage: row[3]
    };
  });
}

function loadPhase10UrgencyAgeCross() {
  /**
   * 緊急度×年齢クロス集計データを読み込む
   * @return {Array} - [{年齢層, urgency_score, カウント, セル品質, 警告フラグ, 警告メッセージ}, ...]
   */
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getSheetByName('P10_UrgencyAge');

  if (!sheet) {
    throw new Error('P10_UrgencyAgeシートが見つかりません。');
  }

  var data = sheet.getDataRange().getValues();
  var headers = data[0];
  var rows = data.slice(1);

  return rows.map(function(row) {
    return {
      age_group: row[0],
      urgency_score: row[1],
      count: row[2],
      cell_quality: row[3] || 'SUFFICIENT',
      warning_flag: row[4] || 'なし',
      warning_message: row[5] || 'なし'
    };
  });
}

function loadPhase10UrgencyAgeMatrix() {
  /**
   * 緊急度×年齢マトリックスデータを読み込む
   * @return {Object} - {headers: [...], rows: [[...], ...]}
   */
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getSheetByName('P10_UrgencyAgeMatrix');

  if (!sheet) {
    return null;
  }

  var data = sheet.getDataRange().getValues();

  return {
    headers: data[0],
    rows: data.slice(1)
  };
}

function loadPhase10UrgencyEmploymentCross() {
  /**
   * 緊急度×就業状態クロス集計データを読み込む
   * @return {Array} - [{employment_status, urgency_score, カウント, セル品質, 警告フラグ, 警告メッセージ}, ...]
   */
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getSheetByName('P10_UrgencyEmp');

  if (!sheet) {
    return [];
  }

  var data = sheet.getDataRange().getValues();
  var headers = data[0];
  var rows = data.slice(1);

  return rows.map(function(row) {
    return {
      employment_status: row[0],
      urgency_score: row[1],
      count: row[2],
      cell_quality: row[3] || 'SUFFICIENT',
      warning_flag: row[4] || 'なし',
      warning_message: row[5] || 'なし'
    };
  });
}

function loadPhase10QualityReport() {
  /**
   * Phase 10品質レポートを読み込む（観察的記述 + 推論的考察）
   * @return {Object} - {descriptive: {...}, inferential: {...}}
   */
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var result = {
    descriptive: null,
    inferential: null
  };

  // P10_QualityReport（観察的記述）
  var descriptiveSheet = ss.getSheetByName('P10_QualityReport');
  if (descriptiveSheet) {
    result.descriptive = loadQualityReportFromSheet(descriptiveSheet);
  }

  // P10_QualityInfer（推論的考察）
  var inferentialSheet = ss.getSheetByName('P10_QualityInfer');
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
   * 緊急度分布グラフHTML生成
   */

  // 緊急度降順ソート
  data.sort(function(a, b) {
    return b.urgency_score - a.urgency_score;
  });

  // Google Charts用データ配列
  var chartData = [['緊急度', '人数', '割合']];
  data.forEach(function(row) {
    chartData.push([
      row.urgency_label + ' (' + row.urgency_score + ')',
      row.count,
      row.percentage
    ]);
  });

  var html = HtmlService.createHtmlOutput();
  html.append('<script type="text/javascript" src="https://www.gstatic.com/charts/loader.js"></script>');
  html.append('<style>');
  html.append('body { font-family: Arial, sans-serif; padding: 20px; background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); }');
  html.append('.container { background: white; border-radius: 12px; padding: 20px; box-shadow: 0 10px 40px rgba(0,0,0,0.1); }');
  html.append('h2 { color: #f5576c; margin-top: 0; display: flex; align-items: center; }');
  html.append('h2 .icon { font-size: 32px; margin-right: 10px; }');
  html.append('.chart-container { margin: 20px 0; }');
  html.append('.stats-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin: 20px 0; }');
  html.append('.stat-card { background: #f8f9fa; border-radius: 8px; padding: 15px; text-align: center; }');
  html.append('.stat-value { font-size: 28px; font-weight: bold; color: #f5576c; }');
  html.append('.stat-label { font-size: 12px; color: #666; margin-top: 5px; }');
  html.append('table { width: 100%; border-collapse: collapse; margin-top: 20px; }');
  html.append('th { background: #f5576c; color: white; padding: 12px; text-align: left; }');
  html.append('td { padding: 10px; border-bottom: 1px solid #eee; }');
  html.append('tr:hover { background: #f8f9fa; }');
  html.append('.urgency-badge { display: inline-block; padding: 5px 12px; border-radius: 15px; font-size: 11px; font-weight: bold; color: white; }');
  html.append('.urgency-5 { background: #ef4444; }');
  html.append('.urgency-4 { background: #f59e0b; }');
  html.append('.urgency-3 { background: #10b981; }');
  html.append('.urgency-2 { background: #3b82f6; }');
  html.append('.urgency-1 { background: #6b7280; }');
  html.append('</style>');

  html.append('<div class="container">');
  html.append('<h2><span class="icon">🚀</span>Phase 10: 転職意欲・緊急度分析</h2>');

  // KPIカード
  var totalCount = data.reduce(function(sum, row) { return sum + row.count; }, 0);
  var highUrgency = data.filter(function(row) { return row.urgency_score >= 4; });
  var highUrgencyCount = highUrgency.reduce(function(sum, row) { return sum + row.count; }, 0);
  var highUrgencyRate = totalCount > 0 ? (highUrgencyCount / totalCount * 100) : 0;

  html.append('<div class="stats-grid">');
  html.append('<div class="stat-card"><div class="stat-value">' + totalCount.toLocaleString() + '</div><div class="stat-label">総求職者数</div></div>');
  html.append('<div class="stat-card"><div class="stat-value">' + highUrgencyCount.toLocaleString() + '</div><div class="stat-label">高緊急度（4以上）</div></div>');
  html.append('<div class="stat-card"><div class="stat-value">' + highUrgencyRate.toFixed(1) + '%</div><div class="stat-label">高緊急度率</div></div>');
  html.append('</div>');

  // 棒グラフ
  html.append('<div class="chart-container" id="bar_chart" style="height: 400px;"></div>');

  // 円グラフ
  html.append('<div class="chart-container" id="pie_chart" style="height: 400px;"></div>');

  // 詳細テーブル
  html.append('<h3>詳細データ</h3>');
  html.append('<table>');
  html.append('<tr><th>スコア</th><th>緊急度</th><th>人数</th><th>割合 (%)</th></tr>');
  data.forEach(function(row) {
    html.append('<tr>');
    html.append('<td><span class="urgency-badge urgency-' + row.urgency_score + '">' + row.urgency_score + '</span></td>');
    html.append('<td>' + row.urgency_label + '</td>');
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
  html.append('  title: "緊急度別求職者数",');
  html.append('  titleTextStyle: {fontSize: 18, bold: true, color: "#f5576c"},');
  html.append('  chartArea: {width: "70%", height: "70%"},');
  html.append('  hAxis: {title: "人数"},');
  html.append('  vAxis: {title: "緊急度"},');
  html.append('  colors: ["#f5576c"],');
  html.append('  legend: {position: "none"}');
  html.append('};');
  html.append('var barChart = new google.visualization.BarChart(document.getElementById("bar_chart"));');
  html.append('barChart.draw(barData, barOptions);');

  // 円グラフ
  html.append('var pieData = google.visualization.arrayToDataTable(' + JSON.stringify(chartData) + ');');
  html.append('var pieOptions = {');
  html.append('  title: "緊急度分布割合",');
  html.append('  titleTextStyle: {fontSize: 18, bold: true, color: "#f5576c"},');
  html.append('  chartArea: {width: "90%", height: "70%"},');
  html.append('  colors: ["#ef4444", "#f59e0b", "#10b981", "#3b82f6", "#6b7280"],');
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
  /**
   * Phase 10統合ダッシュボード
   */
  try {
    var urgencyDist = loadPhase10UrgencyDistribution();
    var urgencyAge = loadPhase10UrgencyAgeCross();
    var urgencyEmp = loadPhase10UrgencyEmploymentCross();
    var qualityReport = loadPhase10QualityReport();

    var html = generatePhase10DashboardHTML(urgencyDist, urgencyAge, urgencyEmp, qualityReport);

    SpreadsheetApp.getUi().showModalDialog(
      html,
      'Phase 10: 緊急度分析統合ダッシュボード'
    );

  } catch (e) {
    SpreadsheetApp.getUi().alert('エラー: ' + e.toString());
  }
}

function generatePhase10DashboardHTML(urgencyDist, urgencyAge, urgencyEmp, qualityReport) {
  /**
   * Phase 10統合ダッシュボードHTML生成
   */

  var html = HtmlService.createHtmlOutput();
  html.append('<script type="text/javascript" src="https://www.gstatic.com/charts/loader.js"></script>');
  html.append('<style>');
  html.append('body { font-family: Arial, sans-serif; margin: 0; padding: 0; background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); }');
  html.append('.container { padding: 20px; }');
  html.append('.tabs { display: flex; background: white; border-radius: 12px 12px 0 0; overflow: hidden; }');
  html.append('.tab { padding: 15px 25px; cursor: pointer; background: #f8f9fa; border: none; font-size: 14px; font-weight: 600; transition: all 0.3s; }');
  html.append('.tab:hover { background: #e9ecef; }');
  html.append('.tab.active { background: white; color: #f5576c; border-bottom: 3px solid #f5576c; }');
  html.append('.tab-content { display: none; background: white; border-radius: 0 0 12px 12px; padding: 30px; min-height: 500px; }');
  html.append('.tab-content.active { display: block; }');
  html.append('h2 { color: #f5576c; margin-top: 0; }');
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
  html.append('<button class="tab" data-tab="urgency" onclick="showTab(\'urgency\')">🚀 緊急度分布</button>');
  html.append('<button class="tab" data-tab="age_cross" onclick="showTab(\'age_cross\')">👥 年齢別</button>');
  html.append('<button class="tab" data-tab="emp_cross" onclick="showTab(\'emp_cross\')">💼 就業状態別</button>');
  html.append('<button class="tab" data-tab="quality" onclick="showTab(\'quality\')">✅ 品質レポート</button>');
  html.append('</div>');

  // 概要タブ
  var totalCount = urgencyDist.reduce(function(sum, r) { return sum + r.count; }, 0);
  var highUrgency = urgencyDist.filter(function(r) { return r.urgency_score >= 4; });
  var highUrgencyCount = highUrgency.reduce(function(sum, r) { return sum + r.count; }, 0);

  // 品質レポート表示用（推論的考察優先、なければ観察的記述）
  var displayQuality = qualityReport.inferential || qualityReport.descriptive || {score: 0, status: 'NO_DATA', columns: []};

  html.append('<div id="overview" class="tab-content active">');
  html.append('<h2>📋 Phase 10: 転職意欲・緊急度分析概要</h2>');
  html.append('<p>品質スコア: <span class="quality-badge quality-' + displayQuality.status.toLowerCase() + '">' + displayQuality.score.toFixed(1) + '/100点 (' + displayQuality.status + ')</span></p>');
  html.append('<p>総求職者数: ' + totalCount.toLocaleString() + '名</p>');
  html.append('<p>高緊急度（4以上）: ' + highUrgencyCount.toLocaleString() + '名 (' + (highUrgencyCount / totalCount * 100).toFixed(1) + '%)</p>');
  html.append('<h3>分析内容</h3>');
  html.append('<ul>');
  html.append('<li>🚀 緊急度分布: 各緊急度レベルの求職者数と割合</li>');
  html.append('<li>👥 緊急度×年齢クロス: 年齢層別の緊急度傾向</li>');
  html.append('<li>💼 緊急度×就業状態クロス: 就業状態別の緊急度傾向</li>');
  html.append('</ul>');
  html.append('</div>');

  // 緊急度分布タブ
  var urgencyChartData = [['緊急度', '人数']];
  urgencyDist.forEach(function(row) {
    urgencyChartData.push([row.urgency_label + ' (' + row.urgency_score + ')', row.count]);
  });

  html.append('<div id="urgency" class="tab-content">');
  html.append('<h2>🚀 緊急度分布</h2>');
  html.append('<div class="chart-container" id="urgency_chart"></div>');
  html.append('</div>');

  // 年齢別タブ
  html.append('<div id="age_cross" class="tab-content">');
  html.append('<h2>👥 緊急度×年齢クロス分析</h2>');
  html.append('<p>P10_UrgencyAgeMatrixシートから詳細なヒートマップを表示できます。</p>');
  html.append('</div>');

  // 就業状態別タブ
  html.append('<div id="emp_cross" class="tab-content">');
  html.append('<h2>💼 緊急度×就業状態クロス分析</h2>');
  html.append('<p>P10_UrgencyEmpMatrixシートから詳細なヒートマップを表示できます。</p>');
  html.append('</div>');

  // 品質レポートタブ
  html.append('<div id="quality" class="tab-content">');
  html.append('<h2>✅ データ品質レポート</h2>');

  // 推論的考察レポート
  if (qualityReport.inferential) {
    html.append('<h3>推論的考察用（Inferential）</h3>');
    html.append('<p>品質スコア: <span class="quality-badge quality-' + qualityReport.inferential.status.toLowerCase() + '">' + qualityReport.inferential.score.toFixed(1) + '/100点</span></p>');
    html.append('<table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">');
    html.append('<tr style="background: #f5576c; color: white;"><th style="padding: 10px;">カラム名</th><th>有効データ数</th><th>信頼性レベル</th><th>警告</th></tr>');
    qualityReport.inferential.columns.forEach(function(col) {
      html.append('<tr style="border-bottom: 1px solid #eee;">');
      html.append('<td style="padding: 10px;">' + col.column_name + '</td>');
      html.append('<td>' + col.valid_count + '</td>');
      html.append('<td>' + col.reliability_level + '</td>');
      html.append('<td>' + col.warning + '</td>');
      html.append('</tr>');
    });
    html.append('</table>');
  }

  // 観察的記述レポート
  if (qualityReport.descriptive) {
    html.append('<h3>観察的記述用（Descriptive）</h3>');
    html.append('<p>品質スコア: <span class="quality-badge quality-' + qualityReport.descriptive.status.toLowerCase() + '">' + qualityReport.descriptive.score.toFixed(1) + '/100点</span></p>');
    html.append('<table style="width: 100%; border-collapse: collapse;">');
    html.append('<tr style="background: #f5576c; color: white;"><th style="padding: 10px;">カラム名</th><th>有効データ数</th><th>信頼性レベル</th><th>警告</th></tr>');
    qualityReport.descriptive.columns.forEach(function(col) {
      html.append('<tr style="border-bottom: 1px solid #eee;">');
      html.append('<td style="padding: 10px;">' + col.column_name + '</td>');
      html.append('<td>' + col.valid_count + '</td>');
      html.append('<td>' + col.reliability_level + '</td>');
      html.append('<td>' + col.warning + '</td>');
      html.append('</tr>');
    });
    html.append('</table>');
  }

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
  html.append('  if (tabName === "urgency" && !window.urgencyChartDrawn) {');
  html.append('    drawUrgencyChart();');
  html.append('    window.urgencyChartDrawn = true;');
  html.append('  }');
  html.append('}');

  // Google Charts
  html.append('google.charts.load("current", {packages:["corechart"]});');
  html.append('function drawUrgencyChart() {');
  html.append('var data = google.visualization.arrayToDataTable(' + JSON.stringify(urgencyChartData) + ');');
  html.append('var options = {');
  html.append('  title: "緊急度別求職者数",');
  html.append('  titleTextStyle: {fontSize: 18, bold: true, color: "#f5576c"},');
  html.append('  chartArea: {width: "70%", height: "70%"},');
  html.append('  colors: ["#f5576c"],');
  html.append('  legend: {position: "none"}');
  html.append('};');
  html.append('var chart = new google.visualization.ColumnChart(document.getElementById("urgency_chart"));');
  html.append('chart.draw(data, options);');
  html.append('}');
  html.append('</script>');

  html.setWidth(1200);
  html.setHeight(800);

  return html;
}
