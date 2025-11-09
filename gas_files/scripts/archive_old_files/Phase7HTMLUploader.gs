/**
 * Phase 7 HTMLアップローダー
 *
 * HTMLフォームからのCSVアップロードを処理します。
 */

/**
 * アップロードUIを表示
 */
function showPhase7UploadDialog() {
  const html = HtmlService.createHtmlOutputFromFile('Phase7Upload')
    .setWidth(950)
    .setHeight(700);

  SpreadsheetApp.getUi().showModalDialog(html, 'Phase 7: CSVファイルアップロード');
}

/**
 * Phase 7 CSVをシートにインポート
 * @param {string} sheetName - シート名
 * @param {Array<Array<string>>} csvData - CSV データ（2次元配列）
 * @return {Object} 結果オブジェクト
 */
function importPhase7CSV(sheetName, csvData) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();

  try {
    // シート存在確認
    let sheet = ss.getSheetByName(sheetName);

    // 存在しない場合は新規作成
    if (!sheet) {
      sheet = ss.insertSheet(sheetName);
      Logger.log(`新規シート作成: ${sheetName}`);
    } else {
      // 既存シートの場合はクリア
      sheet.clear();
      Logger.log(`既存シートクリア: ${sheetName}`);
    }

    // データが空の場合
    if (!csvData || csvData.length === 0) {
      throw new Error('CSVデータが空です');
    }

    // データをシートに書き込み
    const numRows = csvData.length;
    const numCols = csvData[0].length;

    sheet.getRange(1, 1, numRows, numCols).setValues(csvData);

    // ヘッダー行の書式設定
    const headerRange = sheet.getRange(1, 1, 1, numCols);
    headerRange.setBackground('#1a73e8')
               .setFontColor('white')
               .setFontWeight('bold')
               .setHorizontalAlignment('center');

    // 列幅の自動調整
    for (let col = 1; col <= numCols; col++) {
      sheet.autoResizeColumn(col);
    }

    // 固定行（ヘッダー）
    sheet.setFrozenRows(1);

    Logger.log(`インポート完了: ${sheetName} (${numRows}行 × ${numCols}列)`);

    return {
      success: true,
      sheetName: sheetName,
      rows: numRows,
      columns: numCols,
      message: `${sheetName}: ${numRows}行のデータをインポートしました`
    };

  } catch (error) {
    Logger.log(`インポートエラー: ${sheetName} - ${error.message}`);

    return {
      success: false,
      sheetName: sheetName,
      error: error.message
    };
  }
}

/**
 * 複数のPhase 7 CSVを一括インポート
 * @param {Object} filesData - ファイルデータのオブジェクト
 * @return {Object} 結果サマリー
 */
function importMultiplePhase7CSVs(filesData) {
  const results = {
    success: [],
    failed: [],
    totalFiles: 0,
    successCount: 0,
    failedCount: 0
  };

  const fileList = [
    { key: 'supply', sheetName: 'Phase7_SupplyDensity' },
    { key: 'qualification', sheetName: 'Phase7_QualificationDist' },
    { key: 'agegender', sheetName: 'Phase7_AgeGenderCross' },
    { key: 'mobility', sheetName: 'Phase7_MobilityScore' },
    { key: 'persona', sheetName: 'Phase7_PersonaProfile' }
  ];

  results.totalFiles = fileList.length;

  fileList.forEach(fileInfo => {
    if (filesData[fileInfo.key]) {
      const result = importPhase7CSV(fileInfo.sheetName, filesData[fileInfo.key]);

      if (result.success) {
        results.success.push(result);
        results.successCount++;
      } else {
        results.failed.push(result);
        results.failedCount++;
      }
    }
  });

  return results;
}

/**
 * Phase 7データの検証
 * @return {Object} 検証結果
 */
function validatePhase7Upload() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();

  const expectedSheets = [
    { name: 'Phase7_SupplyDensity', minRows: 10, minCols: 7 },
    { name: 'Phase7_QualificationDist', minRows: 5, minCols: 4 },
    { name: 'Phase7_AgeGenderCross', minRows: 10, minCols: 6 },
    { name: 'Phase7_MobilityScore', minRows: 100, minCols: 7 },
    { name: 'Phase7_PersonaProfile', minRows: 3, minCols: 12 }
  ];

  const validation = {
    allValid: true,
    sheets: []
  };

  expectedSheets.forEach(expected => {
    const sheet = ss.getSheetByName(expected.name);

    if (!sheet) {
      validation.allValid = false;
      validation.sheets.push({
        name: expected.name,
        exists: false,
        valid: false,
        message: 'シートが見つかりません'
      });
      return;
    }

    const lastRow = sheet.getLastRow();
    const lastCol = sheet.getLastColumn();

    const valid = (lastRow >= expected.minRows && lastCol >= expected.minCols);

    validation.sheets.push({
      name: expected.name,
      exists: true,
      valid: valid,
      rows: lastRow,
      cols: lastCol,
      message: valid ? 'OK' : `データ不足（行:${lastRow}/${expected.minRows}, 列:${lastCol}/${expected.minCols}）`
    });

    if (!valid) {
      validation.allValid = false;
    }
  });

  return validation;
}

/**
 * Phase 7アップロードサマリーを表示
 */
function showPhase7UploadSummary() {
  const validation = validatePhase7Upload();
  const ui = SpreadsheetApp.getUi();

  let message = '【Phase 7アップロード状況】\n\n';

  validation.sheets.forEach(sheet => {
    const icon = sheet.valid ? '✅' : '❌';
    message += `${icon} ${sheet.name}\n`;
    message += `   ${sheet.message}\n`;
    if (sheet.exists) {
      message += `   データ: ${sheet.rows}行 × ${sheet.cols}列\n`;
    }
    message += '\n';
  });

  if (validation.allValid) {
    message += '\nすべてのシートが正常にアップロードされています！\n';
    message += '可視化機能を使用できます。';
  } else {
    message += '\n⚠️ 一部のシートでデータ不足またはシート未作成\n';
    message += 'HTMLアップローダーで再度アップロードしてください。';
  }

  ui.alert('Phase 7アップロード状況', message, ui.ButtonSet.OK);
}
