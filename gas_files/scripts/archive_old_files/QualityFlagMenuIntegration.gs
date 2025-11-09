/**
 * オプションC: 完全統合 - メニュー統合
 *
 * 目的:
 * - 品質フラグ可視化機能をGASメニューに統合
 * - デモUIの表示機能
 *
 * バージョン: 1.0
 * 作成日: 2025-10-28
 */

/**
 * カスタムメニューを作成
 */
function onOpen() {
  const ui = SpreadsheetApp.getUi();

  ui.createMenu('📊 品質フラグ可視化')
    .addItem('🎨 デモUIを表示', 'showQualityFlagDemoUI')
    .addSeparator()
    .addItem('📈 Phase 1 品質フラグ確認', 'showPhase1QualityFlags')
    .addItem('📊 Phase 8 品質フラグ確認', 'showPhase8QualityFlags')
    .addItem('📉 Phase 10 品質フラグ確認', 'showPhase10QualityFlags')
    .addSeparator()
    .addItem('🧪 品質フラグ機能テスト', 'testQualityFlagVisualization')
    .addToUi();
}

/**
 * 品質フラグデモUIを表示
 */
function showQualityFlagDemoUI() {
  const html = HtmlService.createHtmlOutputFromFile('QualityFlagDemoUI')
    .setWidth(1000)
    .setHeight(800)
    .setTitle('品質フラグ可視化デモ');

  SpreadsheetApp.getUi().showModelessDialog(html, '品質フラグ可視化デモ');
}

/**
 * Phase 1 品質フラグを確認
 */
function showPhase1QualityFlags() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName('AggDesired');

  if (!sheet) {
    SpreadsheetApp.getUi().alert('エラー', 'AggDesiredシートが見つかりません', SpreadsheetApp.getUi().ButtonSet.OK);
    return;
  }

  // データ読み込み
  const data = sheet.getDataRange().getValues();
  const headers = data[0];
  const rows = data.slice(1);

  // 品質フラグカラムのインデックスを取得
  const sampleSizeCategoryIndex = headers.indexOf('サンプルサイズ区分');
  const reliabilityLevelIndex = headers.indexOf('信頼性レベル');
  const warningMessageIndex = headers.indexOf('警告メッセージ');

  if (sampleSizeCategoryIndex === -1) {
    SpreadsheetApp.getUi().alert('エラー', '品質フラグカラムが見つかりません。\nPythonスクリプトで品質フラグ付きCSVを生成してください。', SpreadsheetApp.getUi().ButtonSet.OK);
    return;
  }

  // 品質統計を集計
  const stats = {
    total: rows.length,
    byCategory: {
      'VERY_SMALL': 0,
      'SMALL': 0,
      'MEDIUM': 0,
      'LARGE': 0
    },
    withWarnings: 0
  };

  rows.forEach(function(row) {
    const category = row[sampleSizeCategoryIndex] || 'VERY_SMALL';
    const warningMessage = row[warningMessageIndex] || 'なし';

    if (stats.byCategory[category] !== undefined) {
      stats.byCategory[category]++;
    }

    if (warningMessage !== 'なし（観察的記述）' && warningMessage !== 'なし') {
      stats.withWarnings++;
    }
  });

  // 結果を表示
  let message = '=== Phase 1 品質フラグ統計 ===\n\n';
  message += '総件数: ' + stats.total + '件\n\n';
  message += 'サンプルサイズ区分:\n';
  message += '  LARGE (100件以上): ' + stats.byCategory['LARGE'] + '件\n';
  message += '  MEDIUM (30-99件): ' + stats.byCategory['MEDIUM'] + '件\n';
  message += '  SMALL (10-29件): ' + stats.byCategory['SMALL'] + '件\n';
  message += '  VERY_SMALL (1-9件): ' + stats.byCategory['VERY_SMALL'] + '件\n\n';
  message += '警告あり: ' + stats.withWarnings + '件\n';

  SpreadsheetApp.getUi().alert('Phase 1 品質フラグ統計', message, SpreadsheetApp.getUi().ButtonSet.OK);
}

/**
 * Phase 8 品質フラグを確認
 */
function showPhase8QualityFlags() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName('EducationAgeCross');

  if (!sheet) {
    SpreadsheetApp.getUi().alert('エラー', 'EducationAgeCrossシートが見つかりません', SpreadsheetApp.getUi().ButtonSet.OK);
    return;
  }

  // データ読み込み
  const data = sheet.getDataRange().getValues();
  const headers = data[0];
  const rows = data.slice(1);

  // 品質フラグカラムのインデックスを取得
  const cellQualityIndex = headers.indexOf('セル品質');
  const warningFlagIndex = headers.indexOf('警告フラグ');

  if (cellQualityIndex === -1) {
    SpreadsheetApp.getUi().alert('エラー', '品質フラグカラムが見つかりません。\nPythonスクリプトで品質フラグ付きCSVを生成してください。', SpreadsheetApp.getUi().ButtonSet.OK);
    return;
  }

  // 品質統計を集計
  const stats = {
    total: rows.length,
    byQuality: {
      'INSUFFICIENT': 0,
      'MARGINAL': 0,
      'SUFFICIENT': 0
    },
    withWarnings: 0
  };

  rows.forEach(function(row) {
    const quality = row[cellQualityIndex] || 'SUFFICIENT';
    const warningFlag = row[warningFlagIndex] || 'なし';

    if (stats.byQuality[quality] !== undefined) {
      stats.byQuality[quality]++;
    }

    if (warningFlag !== 'なし') {
      stats.withWarnings++;
    }
  });

  // 結果を表示
  let message = '=== Phase 8 品質フラグ統計 ===\n\n';
  message += '総セル数: ' + stats.total + '件\n\n';
  message += 'セル品質:\n';
  message += '  SUFFICIENT (30件以上): ' + stats.byQuality['SUFFICIENT'] + '件\n';
  message += '  MARGINAL (5-29件): ' + stats.byQuality['MARGINAL'] + '件 ⚠️\n';
  message += '  INSUFFICIENT (0-4件): ' + stats.byQuality['INSUFFICIENT'] + '件 🚫\n\n';
  message += '警告あり: ' + stats.withWarnings + '件\n';

  SpreadsheetApp.getUi().alert('Phase 8 品質フラグ統計', message, SpreadsheetApp.getUi().ButtonSet.OK);
}

/**
 * Phase 10 品質フラグを確認
 */
function showPhase10QualityFlags() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();

  // UrgencyAgeCross と UrgencyEmploymentCross の両方をチェック
  const sheets = [
    { name: 'UrgencyAgeCross', displayName: '緊急度×年齢層' },
    { name: 'UrgencyEmploymentCross', displayName: '緊急度×就業状態' }
  ];

  let allStats = [];

  sheets.forEach(function(sheetInfo) {
    const sheet = ss.getSheetByName(sheetInfo.name);

    if (!sheet) {
      return;
    }

    // データ読み込み
    const data = sheet.getDataRange().getValues();
    const headers = data[0];
    const rows = data.slice(1);

    // 品質フラグカラムのインデックスを取得
    const cellQualityIndex = headers.indexOf('セル品質');
    const warningFlagIndex = headers.indexOf('警告フラグ');

    if (cellQualityIndex === -1) {
      return;
    }

    // 品質統計を集計
    const stats = {
      sheetName: sheetInfo.displayName,
      total: rows.length,
      byQuality: {
        'INSUFFICIENT': 0,
        'MARGINAL': 0,
        'SUFFICIENT': 0
      },
      withWarnings: 0
    };

    rows.forEach(function(row) {
      const quality = row[cellQualityIndex] || 'SUFFICIENT';
      const warningFlag = row[warningFlagIndex] || 'なし';

      if (stats.byQuality[quality] !== undefined) {
        stats.byQuality[quality]++;
      }

      if (warningFlag !== 'なし') {
        stats.withWarnings++;
      }
    });

    allStats.push(stats);
  });

  if (allStats.length === 0) {
    SpreadsheetApp.getUi().alert('エラー', 'Phase 10のシートが見つかりません', SpreadsheetApp.getUi().ButtonSet.OK);
    return;
  }

  // 結果を表示
  let message = '=== Phase 10 品質フラグ統計 ===\n\n';

  allStats.forEach(function(stats) {
    message += '【' + stats.sheetName + '】\n';
    message += '総セル数: ' + stats.total + '件\n';
    message += 'セル品質:\n';
    message += '  SUFFICIENT: ' + stats.byQuality['SUFFICIENT'] + '件\n';
    message += '  MARGINAL: ' + stats.byQuality['MARGINAL'] + '件 ⚠️\n';
    message += '  INSUFFICIENT: ' + stats.byQuality['INSUFFICIENT'] + '件 🚫\n';
    message += '警告あり: ' + stats.withWarnings + '件\n\n';
  });

  SpreadsheetApp.getUi().alert('Phase 10 品質フラグ統計', message, SpreadsheetApp.getUi().ButtonSet.OK);
}

/**
 * 品質フラグ付きデータを取得（汎用関数）
 *
 * @param {string} sheetName - シート名
 * @return {Array<Object>} データオブジェクト配列
 */
function getQualityFlagData(sheetName) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName(sheetName);

  if (!sheet) {
    throw new Error('シートが見つかりません: ' + sheetName);
  }

  const data = sheet.getDataRange().getValues();
  const headers = data[0];
  const rows = data.slice(1);

  return rows.map(function(row) {
    const obj = {};
    headers.forEach(function(header, index) {
      obj[header] = row[index];
    });
    return obj;
  });
}

/**
 * サンプルデータを生成（テスト用）
 */
function generateSampleQualityFlagData() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();

  // AggDesiredシートにサンプルデータを追加
  let sheet = ss.getSheetByName('AggDesired_Sample');
  if (!sheet) {
    sheet = ss.insertSheet('AggDesired_Sample');
  }

  const sampleAggDesiredData = [
    ['希望勤務地_都道府県', '希望勤務地_市区町村', 'キー', 'カウント', 'サンプルサイズ区分', '信頼性レベル', '警告メッセージ'],
    ['京都府', '京都市', '京都府京都市', 450, 'LARGE', 'DESCRIPTIVE', 'なし（観察的記述）'],
    ['京都府', '宇治市', '京都府宇治市', 85, 'MEDIUM', 'DESCRIPTIVE', 'なし（観察的記述）'],
    ['京都府', '亀岡市', '京都府亀岡市', 22, 'SMALL', 'DESCRIPTIVE', 'なし（観察的記述）'],
    ['京都府', '○○村', '京都府○○村', 1, 'VERY_SMALL', 'DESCRIPTIVE', 'なし（観察的記述）']
  ];

  sheet.clear();
  sheet.getRange(1, 1, sampleAggDesiredData.length, sampleAggDesiredData[0].length).setValues(sampleAggDesiredData);

  // EducationAgeCross_Sampleシートにサンプルデータを追加
  let crossSheet = ss.getSheetByName('CrossTab_Sample');
  if (!crossSheet) {
    crossSheet = ss.insertSheet('CrossTab_Sample');
  }

  const sampleCrossTabData = [
    ['education_level', '年齢層', 'カウント', 'セル品質', '警告フラグ', '警告メッセージ'],
    ['高校', '20代', 45, 'SUFFICIENT', 'なし', 'なし'],
    ['高校', '30代', 12, 'MARGINAL', '要注意', 'セル数不足（n=12 < 30）'],
    ['専門', '40代', 3, 'INSUFFICIENT', '使用不可', 'セル数不足（n=3 < 5）'],
    ['大学', '20代', 73, 'SUFFICIENT', 'なし', 'なし'],
    ['大学院', '20代', 2, 'INSUFFICIENT', '使用不可', 'セル数不足（n=2 < 5）']
  ];

  crossSheet.clear();
  crossSheet.getRange(1, 1, sampleCrossTabData.length, sampleCrossTabData[0].length).setValues(sampleCrossTabData);

  SpreadsheetApp.getUi().alert('サンプルデータ生成完了', 'AggDesired_Sample と CrossTab_Sample シートにサンプルデータを生成しました。', SpreadsheetApp.getUi().ButtonSet.OK);
}
