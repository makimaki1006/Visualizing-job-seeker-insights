/**
 * MAP機能用データプロバイダー
 * Leaflet.js + OpenStreetMap用
 *
 * Google Maps API不要のGAS完結型
 */

/**
 * 全可視化データを取得
 * map_GAS_complete.htmlで使用
 */
function getAllVisualizationData() {
  try {
    const ss = SpreadsheetApp.getActiveSpreadsheet();

    // 4つのシートからデータ取得
    const mapMetrics = getSheetData(ss, 'MapMetrics');
    const applicants = getSheetData(ss, 'Applicants');
    const desiredWork = getSheetData(ss, 'DesiredWork');
    const aggDesired = getSheetData(ss, 'AggDesired');

    Logger.log(`データ取得成功: MapMetrics=${mapMetrics.length}, Applicants=${applicants.length}, DesiredWork=${desiredWork.length}, AggDesired=${aggDesired.length}`);

    return {
      mapMetrics: mapMetrics,
      applicants: applicants,
      desiredWork: desiredWork,
      aggDesired: aggDesired
    };

  } catch (error) {
    Logger.log('データ取得エラー: ' + error.message);
    throw new Error('データ取得に失敗しました: ' + error.message);
  }
}

/**
 * シートデータを取得してオブジェクト配列に変換
 */
function getSheetData(spreadsheet, sheetName) {
  const sheet = spreadsheet.getSheetByName(sheetName);

  if (!sheet) {
    Logger.log(`警告: ${sheetName}シートが見つかりません`);
    return [];
  }

  const data = sheet.getDataRange().getValues();

  if (data.length < 2) {
    Logger.log(`警告: ${sheetName}シートにデータがありません`);
    return [];
  }

  const headers = data[0];
  const rows = data.slice(1);

  // オブジェクト配列に変換
  const result = rows.map(row => {
    const obj = {};
    headers.forEach((header, index) => {
      obj[header] = row[index];
    });
    return obj;
  });

  return result;
}

/**
 * MAPダイアログ表示（Leaflet版）
 */
function showMapComplete() {
  const html = HtmlService.createHtmlOutputFromFile('MapComplete')
    .setWidth(1400)
    .setHeight(800);

  SpreadsheetApp.getUi().showModalDialog(html, '🗺️ 求職者データ分析マップ');
}
