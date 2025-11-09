/**
 * オプションC: 完全統合 - 品質フラグ可視化
 *
 * 目的:
 * - AggDesired.csvのサンプルサイズ区分に基づく色分け
 * - クロス集計のセル品質に基づく色分け
 * - プルダウンでの警告メッセージ表示
 *
 * バージョン: 1.0
 * 作成日: 2025-10-28
 */

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
