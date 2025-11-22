/**
 * SourceDataシートの構造とサンプルデータをエクスポート
 */
function exportSourceDataStructure() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getSheetByName("SourceData");

  if (!sheet) {
    Logger.log("SourceDataシートが見つかりません");
    return;
  }

  // ヘッダー行取得
  var headers = sheet.getRange(1, 1, 1, sheet.getLastColumn()).getValues()[0];

  // 最初の10行のデータ取得
  var lastRow = Math.min(sheet.getLastRow(), 11); // ヘッダー + 10行
  var sampleData = sheet.getRange(1, 1, lastRow, sheet.getLastColumn()).getValues();

  // 結果をJSON形式でログ出力
  var result = {
    totalRows: sheet.getLastRow() - 1, // ヘッダーを除く
    totalColumns: sheet.getLastColumn(),
    headers: headers,
    sampleData: sampleData.slice(0, 4) // ヘッダー + 3行
  };

  Logger.log(JSON.stringify(result, null, 2));

  // 新しいシートに出力
  var outputSheet = ss.getSheetByName("DataStructure") || ss.insertSheet("DataStructure");
  outputSheet.clear();

  // カラム情報
  outputSheet.getRange(1, 1).setValue("カラムインデックス");
  outputSheet.getRange(1, 2).setValue("カラム名");
  outputSheet.getRange(1, 3).setValue("サンプルデータ1");
  outputSheet.getRange(1, 4).setValue("サンプルデータ2");
  outputSheet.getRange(1, 5).setValue("サンプルデータ3");

  for (var i = 0; i < headers.length; i++) {
    outputSheet.getRange(i + 2, 1).setValue(i);
    outputSheet.getRange(i + 2, 2).setValue(headers[i]);
    if (sampleData.length > 1) outputSheet.getRange(i + 2, 3).setValue(sampleData[1][i]);
    if (sampleData.length > 2) outputSheet.getRange(i + 2, 4).setValue(sampleData[2][i]);
    if (sampleData.length > 3) outputSheet.getRange(i + 2, 5).setValue(sampleData[3][i]);
  }

  SpreadsheetApp.getUi().alert("データ構造を「DataStructure」シートに出力しました");
}

/**
 * 先頭100行をCSV形式でエクスポート
 */
function exportFirst100RowsAsCSV() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getSheetByName("SourceData");

  if (!sheet) {
    Logger.log("SourceDataシートが見つかりません");
    return;
  }

  var lastRow = Math.min(sheet.getLastRow(), 101); // ヘッダー + 100行
  var data = sheet.getRange(1, 1, lastRow, sheet.getLastColumn()).getValues();

  // CSV形式に変換
  var csv = data.map(function(row) {
    return row.map(function(cell) {
      // セル内の改行・カンマ・ダブルクォートをエスケープ
      var cellStr = String(cell);
      if (cellStr.indexOf(',') !== -1 || cellStr.indexOf('"') !== -1 || cellStr.indexOf('\n') !== -1) {
        cellStr = '"' + cellStr.replace(/"/g, '""') + '"';
      }
      return cellStr;
    }).join(',');
  }).join('\n');

  // 新しいシートに出力（後でダウンロード）
  var csvSheet = ss.getSheetByName("CSV_Export") || ss.insertSheet("CSV_Export");
  csvSheet.clear();
  csvSheet.getRange(1, 1).setValue(csv);

  SpreadsheetApp.getUi().alert("CSV形式を「CSV_Export」シートに出力しました\nA1セルの内容をコピーしてテキストファイルに保存してください");
}

/**
 * メニューに追加
 */
function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu("データエクスポート")
    .addItem("データ構造を確認", "exportSourceDataStructure")
    .addItem("先頭100行をCSVエクスポート", "exportFirst100RowsAsCSV")
    .addToUi();
}
