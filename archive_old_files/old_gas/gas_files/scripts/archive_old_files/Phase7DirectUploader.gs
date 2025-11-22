/**
 * Phase 7 直接アップロード機能（完全自動版）
 *
 * ローカルのCSVファイルを直接アップロードしてインポートします。
 * Google Drive不要、ワンクリックで全ファイルをアップロード可能。
 *
 * Phase 7で生成される全7ファイルに対応:
 * 1. SupplyDensityMap.csv
 * 2. QualificationDistribution.csv
 * 3. AgeGenderCrossAnalysis.csv
 * 4. MobilityScore.csv
 * 5. DetailedPersonaProfile.csv
 * 6. PersonaMapData.csv
 * 7. PersonaMobilityCross.csv
 *
 * 作成日: 2025-10-27
 * Phase 2対応版
 */

/**
 * Phase 7一括アップロード（メニューから呼び出し）
 */
function showPhase7BatchUploadDialog() {
  const html = HtmlService.createHtmlOutputFromFile('Phase7Upload')
    .setWidth(950)
    .setHeight(700);

  SpreadsheetApp.getUi().showModalDialog(html, 'Phase 7データ一括アップロード（全7ファイル）');
}

/**
 * アップロードされたCSVファイルを処理
 * @param {Object} fileData - ファイルデータ
 * @return {Object} 処理結果
 */
function processPhase7Upload(fileData) {
  try {
    // ファイル名からシート名を決定
    const sheetMapping = {
      'SupplyDensityMap.csv': 'Phase7_SupplyDensity',
      'QualificationDistribution.csv': 'Phase7_QualificationDist',
      'AgeGenderCrossAnalysis.csv': 'Phase7_AgeGenderCross',
      'MobilityScore.csv': 'Phase7_MobilityScore',
      'DetailedPersonaProfile.csv': 'Phase7_PersonaProfile',
      'PersonaMapData.csv': 'PersonaMapData',
      'PersonaMobilityCross.csv': 'PersonaMobilityCross'
    };

    const sheetName = sheetMapping[fileData.name];

    if (!sheetName) {
      return {
        success: false,
        fileName: fileData.name,
        error: '未対応のファイル名です'
      };
    }

    // CSVデータをパース
    const csvContent = Utilities.newBlob(
      Utilities.base64Decode(fileData.data),
      'text/csv',
      fileData.name
    ).getDataAsString('UTF-8');

    // BOM除去
    const cleanedContent = csvContent.replace(/^\uFEFF/, '');

    // CSV解析
    const data = Utilities.parseCsv(cleanedContent);

    if (!data || data.length === 0) {
      return {
        success: false,
        fileName: fileData.name,
        error: 'CSVファイルが空です'
      };
    }

    // シートにインポート
    const result = importCSVDataToSheet(data, sheetName);

    return {
      success: true,
      fileName: fileData.name,
      sheetName: sheetName,
      rows: result.rows,
      cols: result.cols
    };

  } catch (error) {
    Logger.log(`アップロード処理エラー: ${error.message}`);
    return {
      success: false,
      fileName: fileData.name || '不明',
      error: error.message
    };
  }
}

/**
 * CSVデータをシートにインポート（共通関数）
 * @param {Array<Array>} data - CSVデータ（2次元配列）
 * @param {string} sheetName - シート名
 * @return {Object} インポート結果
 */
function importCSVDataToSheet(data, sheetName) {
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
  const rows = data.length;
  const cols = data[0].length;

  sheet.getRange(1, 1, rows, cols).setValues(data);

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

  Logger.log(`データ書き込み完了: ${rows}行 × ${cols}列`);

  return {
    rows: rows,
    cols: cols
  };
}

/**
 * Phase 7 CSV直接インポート（HTML UIから呼び出し）
 * @param {string} sheetName - シート名
 * @param {Array<Array>} csvData - CSVデータ（2次元配列）
 */
function importPhase7CSV(sheetName, csvData) {
  try {
    const result = importCSVDataToSheet(csvData, sheetName);
    Logger.log(`CSV直接インポート完了: ${sheetName} (${result.rows}行 × ${result.cols}列)`);
    return {
      success: true,
      sheetName: sheetName,
      rows: result.rows,
      cols: result.cols
    };
  } catch (error) {
    Logger.log(`CSV直接インポートエラー: ${error.message}`);
    throw error;
  }
}

/**
 * Phase 7アップロード状況確認
 */
function showPhase7UploadSummary() {
  const ui = SpreadsheetApp.getUi();
  const ss = SpreadsheetApp.getActiveSpreadsheet();

  const expectedSheets = [
    { name: 'Phase7_SupplyDensity', file: 'SupplyDensityMap.csv' },
    { name: 'Phase7_QualificationDist', file: 'QualificationDistribution.csv' },
    { name: 'Phase7_AgeGenderCross', file: 'AgeGenderCrossAnalysis.csv' },
    { name: 'Phase7_MobilityScore', file: 'MobilityScore.csv' },
    { name: 'Phase7_PersonaProfile', file: 'DetailedPersonaProfile.csv' },
    { name: 'PersonaMapData', file: 'PersonaMapData.csv' },
    { name: 'PersonaMobilityCross', file: 'PersonaMobilityCross.csv' }
  ];

  let message = 'Phase 7データアップロード状況:\n\n';
  let uploadedCount = 0;

  expectedSheets.forEach(sheetInfo => {
    const sheet = ss.getSheetByName(sheetInfo.name);
    if (sheet) {
      const rows = sheet.getLastRow();
      const cols = sheet.getLastColumn();
      message += `✓ ${sheetInfo.file}: ${rows}行 × ${cols}列\n`;
      uploadedCount++;
    } else {
      message += `✗ ${sheetInfo.file}: 未アップロード\n`;
    }
  });

  message += `\n完了: ${uploadedCount}/7ファイル`;

  if (uploadedCount === 7) {
    message += '\n\n全ファイルのアップロードが完了しています！';
  } else {
    message += '\n\n未アップロードのファイルがあります。\n「Phase 7データ一括アップロード」から追加してください。';
  }

  ui.alert('Phase 7アップロード状況', message, ui.ButtonSet.OK);
}
