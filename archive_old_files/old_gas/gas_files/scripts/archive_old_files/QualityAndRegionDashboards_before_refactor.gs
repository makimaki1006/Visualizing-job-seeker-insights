/**
 * 品質・地域ダッシュボード統合ファイル
 *
 * このファイルには以下のダッシュボード機能がすべて含まれています:
 * 1. 品質ダッシュボード
 * 2. 品質フラグ可視化
 * 3. 地域別ダッシュボード
 */

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 1. 品質ダッシュボード
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

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
    {name: 'P1_QualityDesc', phase: 1, label: 'Phase 1: 基礎集計'},
    {name: 'P2_QualityInfer', phase: 2, label: 'Phase 2: 統計分析'},
    {name: 'P3_QualityInfer', phase: 3, label: 'Phase 3: ペルソナ分析'},
    {name: 'P6_QualityInfer', phase: 6, label: 'Phase 6: フロー分析'},
    {name: 'P7_QualityInfer', phase: 7, label: 'Phase 7: 高度分析'},
    {name: 'P8_QualityInfer', phase: 8, label: 'Phase 8: 学歴分析'},
    {name: 'P10_QualityInfer', phase: 10, label: 'Phase 10: 緊急度分析'}
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


// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 2. 品質フラグ可視化
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

// ========================================
// 1. サンプルサイズ区分による色分け
// ========================================

/**
 * サンプルサイズ区分から色を取得
 *
 * @param {string} sampleSizeCategory - サンプルサイズ区分（VERY_SMALL/SMALL/MEDIUM/LARGE）
 * @return {string} 16進数カラーコード
 */
function getMarkerColor(sampleSizeCategory) {
  const colorMap = {
    'VERY_SMALL': '#ff0000',  // 赤色（1-9件）
    'SMALL': '#ff9900',       // オレンジ色（10-29件）
    'MEDIUM': '#ffcc00',      // 黄色（30-99件）
    'LARGE': '#00cc00'        // 緑色（100件以上）
  };
  return colorMap[sampleSizeCategory] || '#cccccc';  // デフォルトは灰色
}

/**
 * サンプルサイズ区分から日本語ラベルを取得
 *
 * @param {string} sampleSizeCategory - サンプルサイズ区分
 * @return {string} 日本語ラベル
 */
function getSampleSizeLabel(sampleSizeCategory) {
  const labelMap = {
    'VERY_SMALL': '極小',
    'SMALL': '小',
    'MEDIUM': '中',
    'LARGE': '大'
  };
  return labelMap[sampleSizeCategory] || '不明';
}

/**
 * AggDesired.csvデータから地図マーカー用データを生成
 *
 * @param {Array<Object>} aggDesiredData - AggDesired.csvのデータ
 * @return {Array<Object>} マーカーデータ配列
 */
function createMarkersWithQualityFlags(aggDesiredData) {
  return aggDesiredData.map(function(row) {
    const count = parseInt(row['カウント']) || 0;
    const sampleSizeCategory = row['サンプルサイズ区分'] || 'VERY_SMALL';
    const warningMessage = row['警告メッセージ'] || 'なし';

    // 警告がある場合はタイトルに追加
    const title = warningMessage !== 'なし（観察的記述）' && warningMessage !== 'なし'
      ? row['希望勤務地_市区町村'] + ' (' + count + '件・' + warningMessage + ')'
      : row['希望勤務地_市区町村'] + ' (' + count + '件)';

    return {
      key: row['キー'],
      prefecture: row['希望勤務地_都道府県'],
      municipality: row['希望勤務地_市区町村'],
      count: count,
      sampleSizeCategory: sampleSizeCategory,
      color: getMarkerColor(sampleSizeCategory),
      title: title,
      warningMessage: warningMessage
    };
  });
}

/**
 * プルダウン用オプションを生成（品質フラグ付き）
 *
 * @param {Array<Object>} aggDesiredData - AggDesired.csvのデータ
 * @return {Array<Object>} プルダウンオプション配列
 */
function createDropdownOptionsWithQualityFlags(aggDesiredData) {
  return aggDesiredData.map(function(row) {
    const count = parseInt(row['カウント']) || 0;
    const sampleSizeCategory = row['サンプルサイズ区分'] || 'VERY_SMALL';
    const warningMessage = row['警告メッセージ'] || 'なし';

    // 警告がある場合は表示テキストに追加
    let displayText = row['希望勤務地_市区町村'] + ' (' + count + '件';

    if (warningMessage !== 'なし（観察的記述）' && warningMessage !== 'なし') {
      displayText += '・' + warningMessage;
    }

    displayText += ')';

    return {
      value: row['キー'],
      display: displayText,
      color: getMarkerColor(sampleSizeCategory),
      sampleSizeLabel: getSampleSizeLabel(sampleSizeCategory),
      warningMessage: warningMessage
    };
  });
}

// ========================================
// 2. クロス集計セル品質による色分け
// ========================================

/**
 * セル品質から背景色を取得
 *
 * @param {string} cellQuality - セル品質（INSUFFICIENT/MARGINAL/SUFFICIENT）
 * @return {string} 16進数カラーコード
 */
function getCellBackgroundColor(cellQuality) {
  const colorMap = {
    'INSUFFICIENT': '#ffcccc',  // 薄い赤（0-4件）
    'MARGINAL': '#ffffcc',      // 薄い黄色（5-29件）
    'SUFFICIENT': '#ccffcc'     // 薄い緑（30件以上）
  };
  return colorMap[cellQuality] || '#ffffff';  // デフォルトは白
}

/**
 * セル品質から日本語ラベルを取得
 *
 * @param {string} cellQuality - セル品質
 * @return {string} 日本語ラベル
 */
function getCellQualityLabel(cellQuality) {
  const labelMap = {
    'INSUFFICIENT': '不足',
    'MARGINAL': '限界',
    'SUFFICIENT': '十分'
  };
  return labelMap[cellQuality] || '不明';
}

/**
 * 警告フラグから警告アイコンを取得
 *
 * @param {string} warningFlag - 警告フラグ（なし/要注意/使用不可）
 * @return {string} 警告アイコン（絵文字）
 */
function getWarningIcon(warningFlag) {
  const iconMap = {
    'なし': '',
    '要注意': '⚠️',
    '使用不可': '🚫'
  };
  return iconMap[warningFlag] || '';
}

/**
 * クロス集計データをHTMLテーブルに変換（品質フラグ付き）
 *
 * @param {Array<Object>} crossTabData - クロス集計データ
 * @param {string} col1Name - 列1の名前
 * @param {string} col2Name - 列2の名前
 * @return {string} HTMLテーブル文字列
 */
function renderCrossTabTableWithQualityFlags(crossTabData, col1Name, col2Name) {
  if (!crossTabData || crossTabData.length === 0) {
    return '<p>データがありません</p>';
  }

  // ヘッダー行
  let html = '<table border="1" cellpadding="5" cellspacing="0" style="border-collapse: collapse; width: 100%;">';
  html += '<thead>';
  html += '<tr style="background-color: #f0f0f0;">';
  html += '<th>' + col1Name + '</th>';
  html += '<th>' + col2Name + '</th>';
  html += '<th>件数</th>';
  html += '<th>品質</th>';
  html += '<th>警告</th>';
  html += '</tr>';
  html += '</thead>';
  html += '<tbody>';

  // データ行
  crossTabData.forEach(function(row) {
    const count = parseInt(row['カウント']) || 0;
    const cellQuality = row['セル品質'] || 'SUFFICIENT';
    const warningFlag = row['警告フラグ'] || 'なし';
    const warningMessage = row['警告メッセージ'] || 'なし';

    const bgColor = getCellBackgroundColor(cellQuality);
    const qualityLabel = getCellQualityLabel(cellQuality);
    const warningIcon = getWarningIcon(warningFlag);

    html += '<tr>';
    html += '<td>' + row[col1Name] + '</td>';
    html += '<td>' + row[col2Name] + '</td>';
    html += '<td style="background-color: ' + bgColor + '; text-align: right;">';
    html += count + ' ' + warningIcon;
    html += '</td>';
    html += '<td style="background-color: ' + bgColor + ';">' + qualityLabel + '</td>';
    html += '<td>' + warningMessage + '</td>';
    html += '</tr>';
  });

  html += '</tbody>';
  html += '</table>';

  return html;
}

/**
 * クロス集計データをGoogle Charts用DataTableに変換（色情報付き）
 *
 * @param {Array<Object>} crossTabData - クロス集計データ
 * @param {string} col1Name - 列1の名前
 * @param {string} col2Name - 列2の名前
 * @return {Object} Google Charts DataTable形式のオブジェクト
 */
function convertCrossTabToDataTableWithQuality(crossTabData, col1Name, col2Name) {
  if (!crossTabData || crossTabData.length === 0) {
    return {
      cols: [
        {id: col1Name, label: col1Name, type: 'string'},
        {id: col2Name, label: col2Name, type: 'string'},
        {id: 'count', label: '件数', type: 'number'}
      ],
      rows: []
    };
  }

  // DataTable構造を作成
  const dataTable = {
    cols: [
      {id: col1Name, label: col1Name, type: 'string'},
      {id: col2Name, label: col2Name, type: 'string'},
      {id: 'count', label: '件数', type: 'number'},
      {id: 'quality', label: '品質', type: 'string', role: 'annotation'}
    ],
    rows: []
  };

  // データ行を追加
  crossTabData.forEach(function(row) {
    const count = parseInt(row['カウント']) || 0;
    const cellQuality = row['セル品質'] || 'SUFFICIENT';
    const warningFlag = row['警告フラグ'] || 'なし';

    const qualityLabel = getCellQualityLabel(cellQuality);
    const warningIcon = getWarningIcon(warningFlag);

    dataTable.rows.push({
      c: [
        {v: row[col1Name]},
        {v: row[col2Name]},
        {v: count},
        {v: qualityLabel + ' ' + warningIcon}
      ]
    });
  });

  return dataTable;
}

// ========================================
// 3. 品質フラグ統計サマリー
// ========================================

/**
 * AggDesiredデータから品質統計サマリーを生成
 *
 * @param {Array<Object>} aggDesiredData - AggDesired.csvのデータ
 * @return {Object} 品質統計サマリー
 */
function generateQualitySummary(aggDesiredData) {
  const summary = {
    total: aggDesiredData.length,
    byCategory: {
      'VERY_SMALL': 0,
      'SMALL': 0,
      'MEDIUM': 0,
      'LARGE': 0
    },
    withWarnings: 0,
    averageCount: 0
  };

  let totalCount = 0;

  aggDesiredData.forEach(function(row) {
    const category = row['サンプルサイズ区分'] || 'VERY_SMALL';
    const warningMessage = row['警告メッセージ'] || 'なし';
    const count = parseInt(row['カウント']) || 0;

    summary.byCategory[category]++;
    totalCount += count;

    if (warningMessage !== 'なし（観察的記述）' && warningMessage !== 'なし') {
      summary.withWarnings++;
    }
  });

  summary.averageCount = Math.round(totalCount / summary.total);

  return summary;
}

/**
 * クロス集計データからセル品質統計サマリーを生成
 *
 * @param {Array<Object>} crossTabData - クロス集計データ
 * @return {Object} セル品質統計サマリー
 */
function generateCellQualitySummary(crossTabData) {
  const summary = {
    total: crossTabData.length,
    byQuality: {
      'INSUFFICIENT': 0,
      'MARGINAL': 0,
      'SUFFICIENT': 0
    },
    withWarnings: 0,
    averageCount: 0
  };

  let totalCount = 0;

  crossTabData.forEach(function(row) {
    const quality = row['セル品質'] || 'SUFFICIENT';
    const warningFlag = row['警告フラグ'] || 'なし';
    const count = parseInt(row['カウント']) || 0;

    summary.byQuality[quality]++;
    totalCount += count;

    if (warningFlag !== 'なし') {
      summary.withWarnings++;
    }
  });

  summary.averageCount = Math.round(totalCount / summary.total);

  return summary;
}

/**
 * 品質統計サマリーをHTML表示用に変換
 *
 * @param {Object} summary - 品質統計サマリー
 * @param {string} type - 'aggregation' または 'crosstab'
 * @return {string} HTML文字列
 */
function renderQualitySummaryHTML(summary, type) {
  let html = '<div style="background-color: #f9f9f9; padding: 10px; margin: 10px 0; border-left: 4px solid #4285f4;">';
  html += '<h4 style="margin: 0 0 10px 0;">品質サマリー</h4>';

  if (type === 'aggregation') {
    html += '<p><strong>総件数:</strong> ' + summary.total + '件</p>';
    html += '<p><strong>平均カウント:</strong> ' + summary.averageCount + '件</p>';
    html += '<p><strong>サンプルサイズ区分:</strong></p>';
    html += '<ul>';
    html += '<li><span style="color: #00cc00;">■</span> LARGE: ' + summary.byCategory['LARGE'] + '件</li>';
    html += '<li><span style="color: #ffcc00;">■</span> MEDIUM: ' + summary.byCategory['MEDIUM'] + '件</li>';
    html += '<li><span style="color: #ff9900;">■</span> SMALL: ' + summary.byCategory['SMALL'] + '件</li>';
    html += '<li><span style="color: #ff0000;">■</span> VERY_SMALL: ' + summary.byCategory['VERY_SMALL'] + '件</li>';
    html += '</ul>';
    html += '<p><strong>警告あり:</strong> ' + summary.withWarnings + '件</p>';
  } else if (type === 'crosstab') {
    html += '<p><strong>総セル数:</strong> ' + summary.total + '件</p>';
    html += '<p><strong>平均カウント:</strong> ' + summary.averageCount + '件</p>';
    html += '<p><strong>セル品質:</strong></p>';
    html += '<ul>';
    html += '<li><span style="color: #00cc00;">■</span> SUFFICIENT: ' + summary.byQuality['SUFFICIENT'] + '件</li>';
    html += '<li><span style="color: #ffcc00;">■</span> MARGINAL: ' + summary.byQuality['MARGINAL'] + '件</li>';
    html += '<li><span style="color: #ff0000;">■</span> INSUFFICIENT: ' + summary.byQuality['INSUFFICIENT'] + '件</li>';
    html += '</ul>';
    html += '<p><strong>警告あり:</strong> ' + summary.withWarnings + '件</p>';
  }

  html += '</div>';

  return html;
}

// ========================================
// 4. テスト関数
// ========================================

/**
 * 品質フラグ可視化機能のテスト
 */
function testQualityFlagVisualization() {
  Logger.log('===== 品質フラグ可視化機能テスト開始 =====');

  // テストデータ（AggDesired.csv形式）
  const testAggDesiredData = [
    {
      '希望勤務地_都道府県': '京都府',
      '希望勤務地_市区町村': '京都市',
      'キー': '京都府京都市',
      'カウント': '450',
      'サンプルサイズ区分': 'LARGE',
      '信頼性レベル': 'DESCRIPTIVE',
      '警告メッセージ': 'なし（観察的記述）'
    },
    {
      '希望勤務地_都道府県': '京都府',
      '希望勤務地_市区町村': '○○村',
      'キー': '京都府○○村',
      'カウント': '1',
      'サンプルサイズ区分': 'VERY_SMALL',
      '信頼性レベル': 'DESCRIPTIVE',
      '警告メッセージ': 'なし（観察的記述）'
    }
  ];

  // テストデータ（クロス集計形式）
  const testCrossTabData = [
    {
      'education_level': '高校',
      '年齢層': '20代',
      'カウント': '45',
      'セル品質': 'SUFFICIENT',
      '警告フラグ': 'なし',
      '警告メッセージ': 'なし'
    },
    {
      'education_level': '高校',
      '年齢層': '30代',
      'カウント': '12',
      'セル品質': 'MARGINAL',
      '警告フラグ': '要注意',
      '警告メッセージ': 'セル数不足（n=12 < 30）'
    },
    {
      'education_level': '専門',
      '年齢層': '40代',
      'カウント': '3',
      'セル品質': 'INSUFFICIENT',
      '警告フラグ': '使用不可',
      '警告メッセージ': 'セル数不足（n=3 < 5）'
    }
  ];

  // テスト1: マーカー色取得
  Logger.log('テスト1: マーカー色取得');
  Logger.log('LARGE: ' + getMarkerColor('LARGE')); // #00cc00
  Logger.log('VERY_SMALL: ' + getMarkerColor('VERY_SMALL')); // #ff0000

  // テスト2: マーカーデータ生成
  Logger.log('テスト2: マーカーデータ生成');
  const markers = createMarkersWithQualityFlags(testAggDesiredData);
  Logger.log(JSON.stringify(markers, null, 2));

  // テスト3: プルダウンオプション生成
  Logger.log('テスト3: プルダウンオプション生成');
  const options = createDropdownOptionsWithQualityFlags(testAggDesiredData);
  Logger.log(JSON.stringify(options, null, 2));

  // テスト4: クロス集計HTMLテーブル生成
  Logger.log('テスト4: クロス集計HTMLテーブル生成');
  const tableHTML = renderCrossTabTableWithQualityFlags(testCrossTabData, 'education_level', '年齢層');
  Logger.log(tableHTML);

  // テスト5: 品質統計サマリー生成
  Logger.log('テスト5: 品質統計サマリー生成');
  const summary = generateQualitySummary(testAggDesiredData);
  Logger.log(JSON.stringify(summary, null, 2));

  const cellSummary = generateCellQualitySummary(testCrossTabData);
  Logger.log(JSON.stringify(cellSummary, null, 2));

  Logger.log('===== 品質フラグ可視化機能テスト完了 =====');
}


// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 3. 地域別ダッシュボード
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

const REGION_DASHBOARD_SHEETS = {
  phase1: {
    mapMetrics: ['MapMetrics'],
    aggDesired: ['AggDesired'],
    quality: ['P1_QualityReport', 'QualityReport']
  },
  phase2: {
    chiSquare: ['ChiSquareTests'],
    anova: ['ANOVATests'],
    quality: ['P2_QualityReport_Inferential', 'QualityReport_Inferential']
  },
  phase3: {
    summary: ['PersonaSummary'],
    details: ['PersonaDetails'],
    quality: ['P3_QualityReport_Inferential', 'QualityReport_Inferential']
  },
  phase7: {
    supply: ['SupplyDensityMap'],
    qualification: ['QualificationDistribution'],
    ageGender: ['AgeGenderCrossAnalysis'],
    mobility: ['MobilityScore'],
    personaProfile: ['DetailedPersonaProfile'],
    quality: ['P7_QualityReport_Inferential', 'QualityReport_Inferential']
  },
  phase8: {
    education: ['EducationDistribution'],
    educationCross: ['EducationAgeCross', 'EducationAgeCross_Matrix'],
    graduation: ['GraduationYearDistribution'],
    quality: ['P8_QualityReport', 'QualityReport', 'P8_QualityReport_Inferential']
  },
  phase10: {
    urgency: ['UrgencyDistribution_ByMunicipality', 'UrgencyDistribution'],
    ageCross: ['UrgencyAgeCross_ByMunicipality', 'UrgencyAgeCross'],
    employmentCross: ['UrgencyEmploymentCross_ByMunicipality', 'UrgencyEmploymentCross'],
    desiredWorkCross: ['UrgencyDesiredWorkCross'],
    quality: ['P10_QualityReport', 'QualityReport', 'P10_QualityReport_Inferential']
  }
};

const REGION_DASHBOARD_COLUMN_ALIASES = {
  都道府県: 'prefecture',
  市区町村: 'municipality',
  自治体: 'municipality',
  '希望勤務地_都道府県': 'prefecture',
  '希望勤務地_市区町村': 'municipality',
  地域キー: 'regionKey',
  キー: 'regionKey',
  lat: 'latitude',
  lng: 'longitude',
  緯度: 'latitude',
  経度: 'longitude',
  カウント: 'count',
  件数: 'count',
  '希望求職者': 'count',
  '応募者数': 'count',
  '希望者数': 'count',
  比率: 'ratio',
  割合: 'ratio',
  スコア: 'score',
  スコアリング: 'score',
  緊急度: 'urgencyLevel',
  urgency_score: 'urgencyScore',
  segment_id: 'segmentId',
  segment_name: 'segmentName',
  avg_age: 'avgAge',
  avg_desired_locations: 'avgDesiredLocations',
  avg_qualifications: 'avgQualifications',
  average_desired_locations: 'avgDesiredLocations',
  average_qualifications: 'avgQualifications',
  female_ratio: 'femaleRatio',
  ratio: 'percentage',
  percentage: 'percentage'
};

const REGION_FILTER_MAPPINGS = {
  mapMetrics: { prefecture: ['prefecture', '都道府県'], municipality: ['municipality', '市区町村'], regionKey: ['regionKey', 'キー'] },
  aggDesired: { prefecture: ['prefecture', '希望勤務地_都道府県'], municipality: ['municipality', '希望勤務地_市区町村'], regionKey: ['regionKey', 'キー'] },
  genericPrefecture: { prefecture: ['prefecture', '都道府県'] },
  municipalityOnly: { municipality: ['municipality', '市区町村'] }
};

const REGION_VALUE_COLUMNS = {
  applicantCount: ['count', 'カウント', '希望求職者', '応募者数', '希望者数']
};

/**
 * Phase1 指標を取得。
 */
function fetchPhase1Metrics(prefecture, municipality) {
  const ctx = resolveRegionContext(prefecture, municipality);
  const warnings = [];

  const mapMetrics = filterByRegion(
    readFirstAvailableSheet(REGION_DASHBOARD_SHEETS.phase1.mapMetrics),
    ctx,
    REGION_FILTER_MAPPINGS.mapMetrics,
    warnings,
    'MapMetrics'
  );

  const aggDesired = filterByRegion(
    readFirstAvailableSheet(REGION_DASHBOARD_SHEETS.phase1.aggDesired),
    ctx,
    REGION_FILTER_MAPPINGS.aggDesired,
    warnings,
    'AggDesired'
  );

  const quality = readFirstAvailableSheet(REGION_DASHBOARD_SHEETS.phase1.quality);

  const applicantTotal = sumNumericValues(mapMetrics, REGION_VALUE_COLUMNS.applicantCount);

  return {
    region: ctx,
    summary: {
      applicantCount: applicantTotal,
      mapRecords: mapMetrics.length,
      aggDesiredRecords: aggDesired.length
    },
    tables: {
      mapMetrics: mapMetrics,
      aggDesired: aggDesired,
      quality: filterByRegionIfPossible(quality, ctx, REGION_FILTER_MAPPINGS.mapMetrics)
    },
    warnings: warnings
  };
}

/**
 * Phase2 (統計検定) データを取得。
 */
function fetchPhase2Stats(prefecture, municipality) {
  const ctx = resolveRegionContext(prefecture, municipality);
  const warnings = [];

  const chiSquare = readFirstAvailableSheet(REGION_DASHBOARD_SHEETS.phase2.chiSquare);
  const anova = readFirstAvailableSheet(REGION_DASHBOARD_SHEETS.phase2.anova);
  const quality = readFirstAvailableSheet(REGION_DASHBOARD_SHEETS.phase2.quality);

  if (chiSquare.length) {
    warnings.push('ChiSquareTestsは地域列を持たないため、選択地域の結果を直接抽出できません。');
  }
  if (anova.length) {
    warnings.push('ANOVATestsは地域列を持たないため、選択地域の結果を直接抽出できません。');
  }

  return {
    region: ctx,
    summary: {
      chiSquareTests: chiSquare.length,
      anovaTests: anova.length
    },
    tables: {
      chiSquare: chiSquare,
      anova: anova,
      quality: quality
    },
    warnings: warnings
  };
}

/**
 * Phase3 (ペルソナ分析) データを取得。
 * @param {string} prefecture
 * @param {string} municipality
 * @param {{segmentId: number|string}} filters
 */
function fetchPhase3Persona(prefecture, municipality, filters) {
  const ctx = resolveRegionContext(prefecture, municipality);
  const warnings = [];

  const rawSummary = readFirstAvailableSheet(REGION_DASHBOARD_SHEETS.phase3.summary);
  const summary = augmentPersonaDifficulty(rawSummary);
  const details = readFirstAvailableSheet(REGION_DASHBOARD_SHEETS.phase3.details);
  const quality = readFirstAvailableSheet(REGION_DASHBOARD_SHEETS.phase3.quality);

  const filteredSummary = applyPersonaFilters(summary, filters);
  const filteredDetails = applyPersonaFilters(details, filters);

  if (summary.length) {
    warnings.push('PersonaSummary は地域列を持たないため、地域別フィルタリングは未対応です。');
  }

  const difficultyStats = calculateDifficultySummary(filteredSummary);

  return {
    region: ctx,
    summary: {
      personaSegments: filteredSummary.length,
      averageDifficultyScore: difficultyStats.averageScore,
      topDifficultyLevel: difficultyStats.topLevel
    },
    tables: {
      personaSummary: filteredSummary,
      personaDetails: filteredDetails,
      quality: quality
    },
    warnings: warnings
  };
}

/**
 * Phase7 (高度分析) データを取得。
 */
function fetchPhase7Supply(prefecture, municipality) {
  const ctx = resolveRegionContext(prefecture, municipality);
  const warnings = [];

  const supply = filterByRegion(
    readFirstAvailableSheet(REGION_DASHBOARD_SHEETS.phase7.supply),
    ctx,
    REGION_FILTER_MAPPINGS.municipalityOnly,
    warnings,
    'SupplyDensityMap'
  );
  const qualification = filterByRegion(
    readFirstAvailableSheet(REGION_DASHBOARD_SHEETS.phase7.qualification),
    ctx,
    REGION_FILTER_MAPPINGS.municipalityOnly,
    warnings,
    'QualificationDistribution'
  );
  const ageGender = filterByRegion(
    readFirstAvailableSheet(REGION_DASHBOARD_SHEETS.phase7.ageGender),
    ctx,
    REGION_FILTER_MAPPINGS.municipalityOnly,
    warnings,
    'AgeGenderCrossAnalysis'
  );
  const mobility = filterByRegion(
    readFirstAvailableSheet(REGION_DASHBOARD_SHEETS.phase7.mobility),
    ctx,
    REGION_FILTER_MAPPINGS.municipalityOnly,
    warnings,
    'MobilityScore'
  );
  const personaProfile = filterByRegion(
    readFirstAvailableSheet(REGION_DASHBOARD_SHEETS.phase7.personaProfile),
    ctx,
    REGION_FILTER_MAPPINGS.municipalityOnly,
    warnings,
    'DetailedPersonaProfile'
  );
  const quality = readFirstAvailableSheet(REGION_DASHBOARD_SHEETS.phase7.quality);

  return {
    region: ctx,
    summary: {
      supplyRecords: supply.length,
      qualificationRecords: qualification.length,
      mobilityRecords: mobility.length
    },
    tables: {
      supplyDensity: supply,
      qualificationDistribution: qualification,
      ageGenderCross: ageGender,
      mobilityScore: mobility,
      personaProfile: personaProfile,
      quality: filterByRegionIfPossible(quality, ctx, REGION_FILTER_MAPPINGS.municipalityOnly)
    },
    warnings: warnings
  };
}

/**
 * Phase8 (学歴・キャリア) データを取得。
 */
function fetchPhase8Education(prefecture, municipality) {
  const ctx = resolveRegionContext(prefecture, municipality);
  const warnings = [];

  const education = readFirstAvailableSheet(REGION_DASHBOARD_SHEETS.phase8.education);
  const educationCross = readFirstAvailableSheet(REGION_DASHBOARD_SHEETS.phase8.educationCross);
  const graduation = readFirstAvailableSheet(REGION_DASHBOARD_SHEETS.phase8.graduation);
  const quality = readFirstAvailableSheet(REGION_DASHBOARD_SHEETS.phase8.quality);

  if (education.length) {
    warnings.push('EducationDistribution は地域列を持たないため、地域別フィルタリングは未対応です。');
  }

  return {
    region: ctx,
    summary: {
      educationBuckets: education.length,
      graduationBuckets: graduation.length
    },
    tables: {
      educationDistribution: education,
      educationCross: educationCross,
      graduationDistribution: graduation,
      quality: quality
    },
    warnings: warnings
  };
}

/**
 * Phase10 (転職意欲) データを取得。
 */
function fetchPhase10Urgency(prefecture, municipality) {
  const ctx = resolveRegionContext(prefecture, municipality);
  const warnings = [];

  const urgency = filterByRegion(
    readFirstAvailableSheet(REGION_DASHBOARD_SHEETS.phase10.urgency),
    ctx,
    REGION_FILTER_MAPPINGS.municipalityOnly,
    warnings,
    'UrgencyDistribution'
  );
  const ageCross = filterByRegion(
    readFirstAvailableSheet(REGION_DASHBOARD_SHEETS.phase10.ageCross),
    ctx,
    REGION_FILTER_MAPPINGS.municipalityOnly,
    warnings,
    'UrgencyAgeCross'
  );
  const employmentCross = filterByRegion(
    readFirstAvailableSheet(REGION_DASHBOARD_SHEETS.phase10.employmentCross),
    ctx,
    REGION_FILTER_MAPPINGS.municipalityOnly,
    warnings,
    'UrgencyEmploymentCross'
  );
  const desiredWorkCross = filterByRegion(
    readFirstAvailableSheet(REGION_DASHBOARD_SHEETS.phase10.desiredWorkCross),
    ctx,
    REGION_FILTER_MAPPINGS.municipalityOnly,
    warnings,
    'UrgencyDesiredWorkCross'
  );
  const quality = readFirstAvailableSheet(REGION_DASHBOARD_SHEETS.phase10.quality);

  return {
    region: ctx,
    summary: {
      urgencyRecords: urgency.length,
      ageCrossRecords: ageCross.length,
      employmentCrossRecords: employmentCross.length
    },
    tables: {
      urgencyDistribution: urgency,
      ageCross: ageCross,
      employmentCross: employmentCross,
      desiredWorkCross: desiredWorkCross,
      quality: filterByRegionIfPossible(quality, ctx, REGION_FILTER_MAPPINGS.municipalityOnly)
    },
    warnings: warnings
  };
}

/**
 * 地域コンテキストを解決する。
 */
function resolveRegionContext(prefecture, municipality) {
  const normalizedPref = normalizeRegionValue(prefecture);
  const normalizedMuni = normalizeRegionValue(municipality);

  if (normalizedPref) {
    const municipalities = getMunicipalitiesForPrefecture(normalizedPref);
    const resolvedMuni = normalizedMuni && municipalities.includes(normalizedMuni)
      ? normalizedMuni
      : (municipalities.length ? municipalities[0] : null);
    return {
      prefecture: normalizedPref,
      municipality: resolvedMuni,
      key: buildRegionKey(normalizedPref, resolvedMuni)
    };
  }

  return loadSelectedRegion();
}

/**
 * 最初に見つかったシートを読み込む。
 * @param {string[]} candidates
 * @return {Array<Object>}
 */
function readFirstAvailableSheet(candidates) {
  for (let i = 0; i < candidates.length; i += 1) {
    const sheetName = candidates[i];
    const rows = readSheetAsObjects(sheetName);
    if (rows.length) {
      return rows;
    }
  }
  return [];
}

/**
 * シートをオブジェクト配列に変換する。
 * @param {string} sheetName
 * @return {Array<Object>}
 */
function readSheetAsObjects(sheetName) {
  const rows = readSheetRows(sheetName);
  if (!rows.length) {
    return [];
  }

  const header = rows[0].map(value => (value !== null && value !== undefined ? String(value).trim() : ''));
  const records = [];

  for (let i = 1; i < rows.length; i += 1) {
    const row = rows[i];
    const record = {};
    const normalized = {};

    for (let col = 0; col < header.length; col += 1) {
      const sourceKey = header[col] || 'column_' + col;
      const value = row[col];
      record[sourceKey] = value;

      if (sourceKey) {
        normalized[sourceKey] = value;
      }

      const alias = REGION_DASHBOARD_COLUMN_ALIASES[sourceKey];
      if (alias) {
        normalized[alias] = value;
      }
    }

    record.__normalized = normalized;
    records.push(record);
  }

  return records;
}

/**
 * 指定したキー候補から値を取得する。
 * @param {Object} record
 * @param {string[]} candidates
 * @return {*}
 */
function extractValue(record, candidates) {
  if (!record) {
    return null;
  }

  for (let i = 0; i < candidates.length; i += 1) {
    const key = candidates[i];
    if (key === undefined || key === null) {
      continue;
    }
    if (record.hasOwnProperty(key)) {
      return record[key];
    }
    const normalized = record.__normalized || {};
    if (normalized.hasOwnProperty(key)) {
      return normalized[key];
    }
  }

  return null;
}

/**
 * レコードを地域でフィルタリングする。
 */
function filterByRegion(records, ctx, mapping, warnings, datasetLabel) {
  if (!records.length) {
    if (warnings && datasetLabel) {
      warnings.push(datasetLabel + ' シートが見つかりません。');
    }
    return [];
  }

  const filtered = records.filter(record => {
    if (ctx.prefecture && mapping.prefecture) {
      const pref = normalizeRegionValue(extractValue(record, mapping.prefecture));
      if (pref && pref !== ctx.prefecture) {
        return false;
      }
      if (!pref && mapping.prefecture.length) {
        return true;
      }
    }

    if (ctx.municipality && mapping.municipality) {
      const muni = normalizeRegionValue(extractValue(record, mapping.municipality));
      if (muni && muni !== ctx.municipality) {
        return false;
      }
      if (!muni && mapping.municipality.length) {
        return true;
      }
    }

    if (ctx.key && mapping.regionKey) {
      const keyValue = normalizeRegionValue(extractValue(record, mapping.regionKey));
      if (keyValue && keyValue !== ctx.key) {
        return false;
      }
    }

    return true;
  });

  if (!filtered.length && warnings && datasetLabel) {
    warnings.push(datasetLabel + ' で指定地域のデータが見つかりませんでした。');
  }

  return filtered;
}

/**
 * 可能なら地域フィルタを適用する。
 */
function filterByRegionIfPossible(records, ctx, mapping) {
  if (!records.length || !mapping) {
    return records;
  }
  const filtered = filterByRegion(records, ctx, mapping);
  return filtered.length ? filtered : records;
}

/**
 * 数値列を合計する。
 */
function sumNumericValues(records, candidates) {
  let total = 0;
  records.forEach(record => {
    const value = extractValue(record, candidates);
    const numeric = typeof value === 'number' ? value : parseFloat(String(value).replace(/,/g, ''));
    if (!isNaN(numeric)) {
      total += numeric;
    }
  });
  return total;
}

/**
 * ペルソナフィルタを適用する。
 */
function applyPersonaFilters(records, filters) {
  if (!records.length || !filters) {
    return records;
  }
  const normalizedFilters = {};
  if (filters.segmentId !== undefined && filters.segmentId !== null && filters.segmentId !== '') {
    normalizedFilters.segmentId = String(filters.segmentId).trim();
  }
  if (filters.difficultyLevel !== undefined && filters.difficultyLevel !== null && filters.difficultyLevel !== '') {
    normalizedFilters.difficultyLevel = String(filters.difficultyLevel).trim();
  }
  if (!Object.keys(normalizedFilters).length) {
    return records;
  }

  return records.filter(record => {
    if (normalizedFilters.segmentId) {
      const value = extractValue(record, ['segment_id', 'segmentId']);
      if (value === undefined || value === null) {
        return false;
      }
      if (String(value).trim() !== normalizedFilters.segmentId) {
        return false;
      }
    }
    if (normalizedFilters.difficultyLevel) {
      const value = extractValue(record, ['difficulty_level', 'difficultyLevel']);
      if (!value || String(value).trim() !== normalizedFilters.difficultyLevel) {
        return false;
      }
    }
    return true;
  });
}

/**
 * PersonaSummaryに難易度情報を付与する。
 * @param {Array<Object>} records
 * @return {Array<Object>}
 */
function augmentPersonaDifficulty(records) {
  if (!records.length) {
    return records;
  }

  return records.map(record => {
    const normalized = record.__normalized || {};
    const difficulty = calculatePersonaDifficultyScore(record);
    const clone = Object.assign({}, record);
    clone.difficulty_score = difficulty.score;
    clone.difficulty_level = difficulty.level;
    clone.__normalized = Object.assign({}, normalized, {
      difficultyScore: difficulty.score,
      difficulty_level: difficulty.level,
      difficultyLevel: difficulty.level
    });
    return clone;
  });
}

/**
 * 難易度のサマリー統計量を算出する。
 * @param {Array<Object>} records
 * @return {{averageScore: number, topLevel: string}}
 */
function calculateDifficultySummary(records) {
  if (!records.length) {
    return {
      averageScore: 0,
      topLevel: 'データなし'
    };
  }

  let total = 0;
  let count = 0;
  let topScore = -1;
  let topLevel = 'データなし';

  records.forEach(record => {
    const score = extractNumeric(record, ['difficulty_score', 'difficultyScore']);
    const level = extractValue(record, ['difficulty_level', 'difficultyLevel']);
    if (score !== null) {
      total += score;
      count += 1;
      if (score > topScore) {
        topScore = score;
        topLevel = level || topLevel;
      }
    }
  });

  return {
    averageScore: count ? Math.round((total / count) * 10) / 10 : 0,
    topLevel: topLevel || 'データなし'
  };
}

/**
 * 難易度スコアとランクを算出する。
 * @param {Object} record
 * @return {{score: number, level: string}}
 */
function calculatePersonaDifficultyScore(record) {
  const params = {
    avgQualifications: extractNumeric(record, ['avg_qualifications', 'avgQualifications', '平均資格数'], 0),
    avgDesiredLocations: extractNumeric(record, ['avg_desired_locations', 'avgDesiredLocations', '平均希望勤務地数'], 0),
    femaleRatio: extractNumeric(record, ['female_ratio', 'femaleRatio', '女性比率'], 0),
    count: extractNumeric(record, ['count', '人数'], 0),
    percentage: extractNumeric(record, ['ratio', 'percentage', '比率'], 0) * 100,
    avgAge: extractNumeric(record, ['avg_age', 'avgAge', '平均年齢'], 0)
  };

  const score = calculateDifficultyScore(params);
  const level = getDifficultyLevel(score);
  return {
    score: score,
    level: level
  };
}

/**
 * 数値を抽出するユーティリティ。
 */
function extractNumeric(record, candidates, defaultValue) {
  const raw = extractValue(record, candidates);
  if (raw === undefined || raw === null || raw === '') {
    return defaultValue !== undefined ? defaultValue : null;
  }
  const numeric = typeof raw === 'number' ? raw : parseFloat(String(raw).replace(/,/g, ''));
  if (isNaN(numeric)) {
    return defaultValue !== undefined ? defaultValue : null;
  }
  return numeric;
}

/**
 * 難易度スコア計算（PersonaDifficultyChecker と同ロジック）。
 */
function calculateDifficultyScore(params) {
  const qualScore = Math.min((params.avgQualifications || 0) * 15, 40);
  const mobilityScore = Math.min((params.avgDesiredLocations || 0) * 8, 25);
  const sizeScore = Math.max(0, 20 - (params.percentage || 0) * 2);
  const ageScore = getAgeScore(params.avgAge || 0);
  const genderScore = Math.abs((params.femaleRatio || 0) - 0.5) * 10;
  const total = qualScore + mobilityScore + sizeScore + ageScore + genderScore;
  return Math.min(Math.round(total), 100);
}

function getAgeScore(avgAge) {
  if (avgAge < 25) return 5;
  if (avgAge < 35) return 3;
  if (avgAge < 50) return 4;
  if (avgAge < 60) return 7;
  return 10;
}

function getDifficultyLevel(score) {
  if (score >= 80) return 'S級（最難）';
  if (score >= 65) return 'A級（難）';
  if (score >= 50) return 'B級（やや難）';
  if (score >= 35) return 'C級（普通）';
  if (score >= 20) return 'D級（やや易）';
  return 'E級（易）';
}


