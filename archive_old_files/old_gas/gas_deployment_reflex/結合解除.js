function unmergeSheet1() {
  // スプレッドシートのインスタンスを取得
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  // "SourceData" という名前のシートを取得
  var sheet = ss.getSheetByName("SourceData");
  if (!sheet) {
    Logger.log("シート1が見つかりません。");
    return;
  }
  
  // シートのデータ範囲内で結合されているセルの範囲を取得
  var dataRange = sheet.getDataRange();
  var mergedRanges = dataRange.getMergedRanges();
  
  // 各結合セルの範囲に対して結合を解除
  mergedRanges.forEach(function(range) {
    range.breakApart();
  });
}
