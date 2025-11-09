/**
 * 汎用Phase別一括アップローダー
 *
 * 全Phase（Phase 1, 2, 3, 6, 7）のCSVファイルを
 * ブラウザから直接アップロードしてシートに反映します。
 *
 * 作成日: 2025-10-27
 * バージョン: 1.0
 */

/**
 * Phase別ファイル定義
 */
const PHASE_CONFIGS = {
  'phase1': {
    name: 'Phase 1: 基礎集計',
    icon: '📍',
    files: [
      { name: 'MapMetrics.csv', sheetName: 'MapMetrics', label: '地図メトリクス' },
      { name: 'Applicants.csv', sheetName: 'Applicants', label: '応募者情報' },
      { name: 'DesiredWork.csv', sheetName: 'DesiredWork', label: '希望勤務地' },
      { name: 'AggDesired.csv', sheetName: 'AggDesired', label: '集計データ' }
    ]
  },
  'phase2': {
    name: 'Phase 2: 統計分析',
    icon: '📊',
    files: [
      { name: 'ChiSquareTests.csv', sheetName: 'ChiSquareTests', label: 'カイ二乗検定' },
      { name: 'ANOVATests.csv', sheetName: 'ANOVATests', label: 'ANOVA検定' }
    ]
  },
  'phase3': {
    name: 'Phase 3: ペルソナ分析',
    icon: '👥',
    files: [
      { name: 'PersonaSummary.csv', sheetName: 'PersonaSummary', label: 'ペルソナサマリー' },
      { name: 'PersonaDetails.csv', sheetName: 'PersonaDetails', label: 'ペルソナ詳細' }
    ]
  },
  'phase6': {
    name: 'Phase 6: フロー分析',
    icon: '🌊',
    files: [
      { name: 'MunicipalityFlowEdges.csv', sheetName: 'MunicipalityFlowEdges', label: 'フローエッジ' },
      { name: 'MunicipalityFlowNodes.csv', sheetName: 'MunicipalityFlowNodes', label: 'フローノード' },
      { name: 'ProximityAnalysis.csv', sheetName: 'ProximityAnalysis', label: '移動パターン分析' }
    ]
  },
  'phase7': {
    name: 'Phase 7: 高度分析',
    icon: '📈',
    files: [
      { name: 'SupplyDensityMap.csv', sheetName: 'Phase7_SupplyDensity', label: '人材供給密度' },
      { name: 'QualificationDistribution.csv', sheetName: 'Phase7_QualificationDist', label: '資格分布' },
      { name: 'AgeGenderCrossAnalysis.csv', sheetName: 'Phase7_AgeGenderCross', label: '年齢×性別' },
      { name: 'MobilityScore.csv', sheetName: 'Phase7_MobilityScore', label: '移動許容度' },
      { name: 'DetailedPersonaProfile.csv', sheetName: 'Phase7_PersonaProfile', label: 'ペルソナ詳細' },
      { name: 'PersonaMapData.csv', sheetName: 'Phase7_PersonaMapData', label: 'ペルソナ地図' },
      { name: 'PersonaMobilityCross.csv', sheetName: 'Phase7_PersonaMobilityCross', label: 'ペルソナ×移動' }
    ]
  }
};

/**
 * Phase別アップロードダイアログを表示
 * @param {string} phaseId - Phase ID (phase1, phase2, phase3, phase6, phase7)
 */
function showPhaseUploadDialog(phaseId) {
  const config = PHASE_CONFIGS[phaseId];

  if (!config) {
    SpreadsheetApp.getUi().alert('エラー', `無効なPhase ID: ${phaseId}`, SpreadsheetApp.getUi().ButtonSet.OK);
    return;
  }

  const html = HtmlService.createTemplateFromFile('PhaseUpload');
  html.phaseId = phaseId;
  html.phaseName = config.name;
  html.phaseIcon = config.icon;
  html.files = JSON.stringify(config.files);

  const output = html.evaluate()
    .setWidth(1000)
    .setHeight(700);

  SpreadsheetApp.getUi().showModalDialog(output, `${config.icon} ${config.name} - データアップロード`);
}

/**
 * Phase別設定を取得（HTML側から呼び出し）
 * @param {string} phaseId - Phase ID
 * @return {Object} Phase設定
 */
function getPhaseConfig(phaseId) {
  return PHASE_CONFIGS[phaseId];
}

/**
 * CSVファイルをシートにインポート（HTML UIから呼び出し）
 * @param {string} sheetName - シート名
 * @param {Array<Array>} csvData - CSVデータ（2次元配列）
 * @return {Object} インポート結果
 */
function importCSVToSheet(sheetName, csvData) {
  try {
    const ss = SpreadsheetApp.getActiveSpreadsheet();

    // 既存シートを削除（存在する場合）
    let sheet = ss.getSheetByName(sheetName);
    if (sheet) {
      ss.deleteSheet(sheet);
      Logger.log(`既存シート削除: ${sheetName}`);
    }

    // 新規シート作成
    sheet = ss.insertSheet(sheetName);
    Logger.log(`新規シート作成: ${sheetName}`);

    // データを書き込み
    const rows = csvData.length;
    const cols = csvData[0].length;

    sheet.getRange(1, 1, rows, cols).setValues(csvData);

    // ヘッダー行を太字にフォーマット
    sheet.getRange(1, 1, 1, cols)
      .setFontWeight('bold')
      .setBackground('#f3f3f3');

    // 列幅を自動調整
    for (let i = 1; i <= cols; i++) {
      sheet.autoResizeColumn(i);
    }

    // シートを先頭に移動
    ss.setActiveSheet(sheet);
    ss.moveActiveSheet(1);

    Logger.log(`CSV直接インポート完了: ${sheetName} (${rows}行 × ${cols}列)`);

    return {
      success: true,
      sheetName: sheetName,
      rows: rows,
      cols: cols
    };

  } catch (error) {
    Logger.log(`CSV直接インポートエラー: ${error.message}`);
    throw error;
  }
}

/**
 * Phase別アップロード状況確認
 * @param {string} phaseId - Phase ID
 */
function showPhaseUploadStatus(phaseId) {
  const ui = SpreadsheetApp.getUi();
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const config = PHASE_CONFIGS[phaseId];

  if (!config) {
    ui.alert('エラー', `無効なPhase ID: ${phaseId}`, ui.ButtonSet.OK);
    return;
  }

  let message = `${config.icon} ${config.name} - アップロード状況:\n\n`;
  let uploadedCount = 0;

  config.files.forEach(fileInfo => {
    const sheet = ss.getSheetByName(fileInfo.sheetName);
    if (sheet) {
      const rows = sheet.getLastRow();
      const cols = sheet.getLastColumn();
      message += `✓ ${fileInfo.label}: ${rows}行 × ${cols}列\n`;
      uploadedCount++;
    } else {
      message += `✗ ${fileInfo.label}: 未アップロード\n`;
    }
  });

  message += `\n完了: ${uploadedCount}/${config.files.length}ファイル`;

  if (uploadedCount === config.files.length) {
    message += '\n\n全ファイルのアップロードが完了しています！';
  } else {
    message += `\n\n未アップロードのファイルがあります。\n「${config.icon} ${config.name} - データアップロード」から追加してください。`;
  }

  ui.alert(`${config.name} アップロード状況`, message, ui.ButtonSet.OK);
}

/**
 * 全Phaseアップロード状況確認
 */
function showAllPhasesUploadStatus() {
  const ui = SpreadsheetApp.getUi();
  const ss = SpreadsheetApp.getActiveSpreadsheet();

  let message = '全Phaseアップロード状況:\n\n';
  let totalFiles = 0;
  let totalUploaded = 0;

  Object.keys(PHASE_CONFIGS).forEach(phaseId => {
    const config = PHASE_CONFIGS[phaseId];
    let phaseUploaded = 0;

    config.files.forEach(fileInfo => {
      const sheet = ss.getSheetByName(fileInfo.sheetName);
      if (sheet) {
        phaseUploaded++;
      }
      totalFiles++;
    });

    totalUploaded += phaseUploaded;
    const status = phaseUploaded === config.files.length ? '✅' : '⚠️';
    message += `${status} ${config.icon} ${config.name}: ${phaseUploaded}/${config.files.length}\n`;
  });

  message += `\n合計: ${totalUploaded}/${totalFiles}ファイル`;

  if (totalUploaded === totalFiles) {
    message += '\n\n🎉 全Phaseのアップロードが完了しています！';
  } else {
    message += '\n\n未完了のPhaseがあります。各Phaseのアップロード機能をご利用ください。';
  }

  ui.alert('全Phaseアップロード状況', message, ui.ButtonSet.OK);
}
