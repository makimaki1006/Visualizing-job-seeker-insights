/**
 * Matrix形式CSV汎用ヒートマップビューアー
 * Phase 8, 10のMatrix形式CSVをヒートマップで可視化
 */

// ===== 汎用Matrix読み込み関数 =====

function loadMatrixData(sheetName) {
  /**
   * 指定されたシートからMatrix形式データを読み込む
   *
   * @param {string} sheetName - シート名
   * @return {Object} - {headers: [...], rows: [[...], ...], metadata: {...}}
   */
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getSheetByName(sheetName);

  if (!sheet) {
    throw new Error(sheetName + ' シートが見つかりません');
  }

  var data = sheet.getDataRange().getValues();

  if (data.length < 2) {
    throw new Error('データが不足しています');
  }

  // ヘッダー行とデータ行を分離
  var headers = data[0];
  var rows = data.slice(1);

  // メタデータ抽出
  var metadata = extractMatrixMetadata(headers, rows);

  return {
    headers: headers,
    rows: rows,
    metadata: metadata
  };
}

function extractMatrixMetadata(headers, rows) {
  /**
   * Matrixデータからメタデータを抽出
   *
   * @param {Array} headers - ヘッダー行
   * @param {Array} rows - データ行
   * @return {Object} - メタデータ
   */

  // 数値セルの統計
  var values = [];
  rows.forEach(function(row) {
    row.slice(1).forEach(function(cell) {
      var num = parseFloat(cell);
      if (!isNaN(num) && num > 0) {
        values.push(num);
      }
    });
  });

  values.sort(function(a, b) { return a - b; });

  var sum = values.reduce(function(acc, v) { return acc + v; }, 0);
  var mean = values.length > 0 ? sum / values.length : 0;
  var median = values.length > 0 ? values[Math.floor(values.length / 2)] : 0;
  var min = values.length > 0 ? values[0] : 0;
  var max = values.length > 0 ? values[values.length - 1] : 0;

  return {
    totalCells: rows.length * (headers.length - 1),
    valueCells: values.length,
    emptyCells: (rows.length * (headers.length - 1)) - values.length,
    sum: sum,
    mean: mean,
    median: median,
    min: min,
    max: max
  };
}

// ===== ヒートマップ可視化関数 =====

function showMatrixHeatmap(sheetName, title, colorScheme) {
  /**
   * Matrix形式ヒートマップを表示
   *
   * @param {string} sheetName - シート名
   * @param {string} title - タイトル
   * @param {string} colorScheme - カラースキーム ('blue', 'red', 'green', 'purple')
   */
  try {
    var matrixData = loadMatrixData(sheetName);

    var html = generateMatrixHeatmapHTML(
      matrixData,
      title,
      colorScheme || 'blue'
    );

    SpreadsheetApp.getUi().showModalDialog(
      html,
      title
    );

  } catch (e) {
    SpreadsheetApp.getUi().alert('エラー: ' + e.toString());
  }
}

function generateMatrixHeatmapHTML(matrixData, title, colorScheme) {
  /**
   * ヒートマップHTML生成
   *
   * @param {Object} matrixData - Matrix形式データ
   * @param {string} title - タイトル
   * @param {string} colorScheme - カラースキーム
   * @return {HtmlOutput} - HTML出力
   */

  var colors = getColorScheme(colorScheme);

  var html = HtmlService.createHtmlOutput();
  html.append('<style>');
  html.append('body { font-family: Arial, sans-serif; padding: 20px; background: ' + colors.background + '; }');
  html.append('.container { background: white; border-radius: 12px; padding: 20px; box-shadow: 0 10px 40px rgba(0,0,0,0.1); }');
  html.append('h2 { color: ' + colors.primary + '; margin-top: 0; display: flex; align-items: center; }');
  html.append('h2 .icon { font-size: 32px; margin-right: 10px; }');
  html.append('.stats-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin: 20px 0; }');
  html.append('.stat-card { background: #f8f9fa; border-radius: 8px; padding: 15px; text-align: center; }');
  html.append('.stat-value { font-size: 24px; font-weight: bold; color: ' + colors.primary + '; }');
  html.append('.stat-label { font-size: 12px; color: #666; margin-top: 5px; }');
  html.append('.heatmap-container { margin: 20px 0; overflow: auto; max-height: 500px; }');
  html.append('table { width: 100%; border-collapse: collapse; }');
  html.append('th { background: ' + colors.primary + '; color: white; padding: 12px; text-align: center; position: sticky; top: 0; z-index: 10; }');
  html.append('td { padding: 10px; text-align: center; border: 1px solid #e0e0e0; font-size: 13px; }');
  html.append('.row-header { background: ' + colors.secondary + '; color: white; font-weight: bold; position: sticky; left: 0; z-index: 5; }');
  html.append('.legend { display: flex; align-items: center; justify-content: center; margin: 20px 0; }');
  html.append('.legend-item { margin: 0 10px; display: flex; align-items: center; }');
  html.append('.legend-box { width: 30px; height: 20px; margin-right: 5px; border: 1px solid #ddd; }');
  html.append('</style>');

  html.append('<div class="container">');
  html.append('<h2><span class="icon">🔥</span>' + title + '</h2>');

  // 統計サマリー
  var meta = matrixData.metadata;
  html.append('<div class="stats-grid">');
  html.append('<div class="stat-card"><div class="stat-value">' + meta.max.toFixed(0) + '</div><div class="stat-label">最大値</div></div>');
  html.append('<div class="stat-card"><div class="stat-value">' + meta.mean.toFixed(1) + '</div><div class="stat-label">平均値</div></div>');
  html.append('<div class="stat-card"><div class="stat-value">' + meta.median.toFixed(1) + '</div><div class="stat-label">中央値</div></div>');
  html.append('<div class="stat-card"><div class="stat-value">' + meta.valueCells + '</div><div class="stat-label">有効セル数</div></div>');
  html.append('</div>');

  // カラーレジェンド
  html.append('<div class="legend">');
  html.append('<div class="legend-item"><div class="legend-box" style="background: #ffffff;"></div><span>0</span></div>');
  html.append('<div class="legend-item"><div class="legend-box" style="background: ' + colors.gradient[0] + ';"></div><span>低</span></div>');
  html.append('<div class="legend-item"><div class="legend-box" style="background: ' + colors.gradient[1] + ';"></div><span>中</span></div>');
  html.append('<div class="legend-item"><div class="legend-box" style="background: ' + colors.gradient[2] + ';"></div><span>高</span></div>');
  html.append('</div>');

  // ヒートマップテーブル
  html.append('<div class="heatmap-container">');
  html.append('<table>');

  // ヘッダー行
  html.append('<tr>');
  matrixData.headers.forEach(function(header) {
    html.append('<th>' + header + '</th>');
  });
  html.append('</tr>');

  // データ行（色付け）
  var maxValue = meta.max;
  matrixData.rows.forEach(function(row) {
    html.append('<tr>');
    row.forEach(function(cell, index) {
      if (index === 0) {
        // 行ラベル
        html.append('<td class="row-header">' + cell + '</td>');
      } else {
        // データセル
        var value = parseFloat(cell) || 0;
        var intensity = maxValue > 0 ? value / maxValue : 0;
        var bgColor = getCellColor(intensity, colors.gradient);

        html.append('<td style="background: ' + bgColor + '; color: ' + (intensity > 0.6 ? 'white' : 'black') + ';">');
        html.append(value > 0 ? value.toFixed(0) : '-');
        html.append('</td>');
      }
    });
    html.append('</tr>');
  });

  html.append('</table>');
  html.append('</div>');

  // 注釈
  html.append('<p style="font-size: 12px; color: #666; margin-top: 20px;">');
  html.append('※ セルの色が濃いほど数値が大きいことを示します。');
  html.append('</p>');

  html.append('</div>');

  html.setWidth(1200);
  html.setHeight(800);

  return html;
}

// ===== ヘルパー関数 =====

function getColorScheme(scheme) {
  /**
   * カラースキームを取得
   *
   * @param {string} scheme - スキーム名
   * @return {Object} - カラー設定
   */
  var schemes = {
    'blue': {
      primary: '#667eea',
      secondary: '#764ba2',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      gradient: ['#e3f2fd', '#667eea', '#4a5bbf']
    },
    'red': {
      primary: '#f5576c',
      secondary: '#f093fb',
      background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
      gradient: ['#ffebee', '#f5576c', '#c62828']
    },
    'green': {
      primary: '#10b981',
      secondary: '#34d399',
      background: 'linear-gradient(135deg, #10b981 0%, #34d399 100%)',
      gradient: ['#d1fae5', '#10b981', '#047857']
    },
    'purple': {
      primary: '#8b5cf6',
      secondary: '#a78bfa',
      background: 'linear-gradient(135deg, #8b5cf6 0%, #a78bfa 100%)',
      gradient: ['#ede9fe', '#8b5cf6', '#6d28d9']
    }
  };

  return schemes[scheme] || schemes['blue'];
}

function getCellColor(intensity, gradientColors) {
  /**
   * セルの色を計算
   *
   * @param {number} intensity - 強度（0-1）
   * @param {Array} gradientColors - グラデーションカラー配列
   * @return {string} - RGB色
   */
  if (intensity === 0) {
    return '#ffffff';
  }

  if (intensity < 0.33) {
    return gradientColors[0];
  } else if (intensity < 0.67) {
    return gradientColors[1];
  } else {
    return gradientColors[2];
  }
}

// ===== 便利関数（各Phaseから呼び出し可能） =====

function showPhase8EducationAgeMatrixHeatmap() {
  /**
   * Phase 8: 学歴×年齢Matrixヒートマップ
   */
  showMatrixHeatmap('P8_EduAgeMatrix', 'Phase 8: 学歴×年齢ヒートマップ', 'blue');
}

function showPhase10UrgencyAgeMatrixHeatmap() {
  /**
   * Phase 10: 緊急度×年齢Matrixヒートマップ
   */
  showMatrixHeatmap('P10_UrgencyAgeMatrix', 'Phase 10: 緊急度×年齢ヒートマップ', 'red');
}

function showPhase10UrgencyEmploymentMatrixHeatmap() {
  /**
   * Phase 10: 緊急度×就業状態Matrixヒートマップ
   */
  showMatrixHeatmap('P10_UrgencyEmpMatrix', 'Phase 10: 緊急度×就業状態ヒートマップ', 'red');
}

// ===== 汎用Matrix比較機能 =====

function compareMatrices(sheetName1, sheetName2, title) {
  /**
   * 2つのMatrixを比較表示
   *
   * @param {string} sheetName1 - 1つ目のシート名
   * @param {string} sheetName2 - 2つ目のシート名
   * @param {string} title - タイトル
   */
  try {
    var matrix1 = loadMatrixData(sheetName1);
    var matrix2 = loadMatrixData(sheetName2);

    var html = generateMatrixComparisonHTML(matrix1, matrix2, title);

    SpreadsheetApp.getUi().showModalDialog(
      html,
      title
    );

  } catch (e) {
    SpreadsheetApp.getUi().alert('エラー: ' + e.toString());
  }
}

function generateMatrixComparisonHTML(matrix1, matrix2, title) {
  /**
   * Matrix比較HTML生成
   */

  var html = HtmlService.createHtmlOutput();
  html.append('<style>');
  html.append('body { font-family: Arial, sans-serif; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }');
  html.append('.container { background: white; border-radius: 12px; padding: 20px; }');
  html.append('h2 { color: #667eea; }');
  html.append('.comparison-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }');
  html.append('.matrix-panel { border: 1px solid #ddd; border-radius: 8px; padding: 15px; }');
  html.append('table { width: 100%; border-collapse: collapse; font-size: 12px; }');
  html.append('th, td { padding: 8px; text-align: center; border: 1px solid #ddd; }');
  html.append('th { background: #667eea; color: white; }');
  html.append('</style>');

  html.append('<div class="container">');
  html.append('<h2>' + title + '</h2>');
  html.append('<div class="comparison-grid">');

  // Matrix 1
  html.append('<div class="matrix-panel">');
  html.append('<h3>Matrix 1</h3>');
  html.append('<p>最大値: ' + matrix1.metadata.max.toFixed(0) + ' / 平均値: ' + matrix1.metadata.mean.toFixed(1) + '</p>');
  html.append('</div>');

  // Matrix 2
  html.append('<div class="matrix-panel">');
  html.append('<h3>Matrix 2</h3>');
  html.append('<p>最大値: ' + matrix2.metadata.max.toFixed(0) + ' / 平均値: ' + matrix2.metadata.mean.toFixed(1) + '</p>');
  html.append('</div>');

  html.append('</div>');
  html.append('</div>');

  html.setWidth(1200);
  html.setHeight(800);

  return html;
}
