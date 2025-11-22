// === 設定値 ===
var SPREADSHEET_ID = "1w7Mbo1eKiooLlt090Nj9nQQktE7m29qNPX1RcS5x7nw"; // スプレッドシートID
var SOURCE_SHEET_NAME = "SourceData";
var FILTERED_SHEET_NAME = "FilteredData";
var EXTRACTED_SHEET_NAME = "ExtractedData";
var ANALYSIS_SHEET_NAME = "SalaryAnalysis";

/**
 * スプレッドシートを開いたときにカスタムメニューを追加する
 */
function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu("カスタム地図")
    .addItem("地図を表示", "showMap")
    .addItem("給与統計を作成", "analyzeSalaryData")
    .addToUi();
}

/**
 * ★ 修正点: ダイアログのタイトルを消し、その分高さを増やす
 */
function showMap() {
  var html = HtmlService.createTemplateFromFile("Map")
    .evaluate()
    .setWidth(1800)
    .setHeight(840); // タイトルバーの高さ分（約40px）を上乗せ
  SpreadsheetApp.getUi().showModelessDialog(html, " "); // タイトルを空にする
}

/**
 * Webアプリのエントリーポイント
 */
function doGet(e) {
  var output;
  if (e.parameter.mode && e.parameter.mode === 'popup') {
    output = HtmlService.createHtmlOutputFromFile('MapPopup');
  } else {
    output = HtmlService.createHtmlOutputFromFile('Map');
  }

  // iframe埋め込みを許可（X-Frame-Optionsを設定）
  output.setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);

  return output;
}

/**
 * 生データシートから全データを取得し、マーカー情報として返す
 */
function getMarkersFromSheet() {
  var ss = SpreadsheetApp.openById(SPREADSHEET_ID); // WebアプリではIDで開く
  var sheet = ss.getSheetByName(SOURCE_SHEET_NAME);
  if (!sheet) throw new Error("シート '" + SOURCE_SHEET_NAME + "' が見つかりません。");
  var values = sheet.getDataRange().getValues();
  var markers = [];
  
  var headers = values[0];
  var indexEmployment = headers.indexOf("給与_雇用形態");
  var indexSalary = headers.indexOf("給与_区分");
  var indexLower = headers.indexOf("給与_下限");
  var indexUpper = headers.indexOf("給与_上限");
  
  for (var i = 1; i < values.length; i++) {
    var row = values[i];
    var lng = row[26];
    var lat = row[27];
    if (lat !== "" && lng !== "" && !isNaN(lat) && !isNaN(lng)) {
      var infoArr = [];
      for (var j = 0; j < row.length; j++) {
        var headerName = headers[j] || ("Col" + (j + 1));
        infoArr.push(headerName + ": " + row[j]);
      }
      var info = infoArr.join("<br/>");
      var marker = {
        lat: parseFloat(lat),
        lng: parseFloat(lng),
        info: info
      };
      if (indexEmployment !== -1) marker.employmentType = row[indexEmployment];
      if (indexSalary !== -1) marker.salaryCategory = row[indexSalary];
      if (indexLower !== -1) marker.salaryLower = parseFloat(row[indexLower]);
      if (indexUpper !== -1) marker.salaryUpper = parseFloat(row[indexUpper]);
      markers.push(marker);
    }
  }
  return markers;
}

/**
 * 市町村からジオコーディングで中心座標を取得
 */
function getMunicipalityCoordinates(prefecture, municipality) {
  var query = prefecture + " " + municipality;
  var response = Maps.newGeocoder().geocode(query);
  if (response.status === 'OK' && response.results.length > 0) {
    var location = response.results[0].geometry.location;
    return { lat: location.lat, lng: location.lng };
  } else {
    throw new Error("ジオコーディングに失敗しました: " + query);
  }
}

/**
 * 2点間の距離（km）を計算
 */
function haversineDistance(lat1, lng1, lat2, lng2) {
  var R = 6371;
  var dLat = toRadians(lat2 - lat1);
  var dLng = toRadians(lng2 - lng1);
  var a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
        Math.cos(toRadians(lat1)) * Math.cos(toRadians(lat2)) *
        Math.sin(dLng / 2) * Math.sin(dLng / 2);
  var c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c;
}

/**
 * 度をラジアンに変換
 */
function toRadians(deg) {
  return deg * Math.PI / 180;
}

/**
 * 指定条件に基づいてマーカーを抽出
 */
function getFilteredMarkers(prefecture, municipality, radius, employmentType, salaryCategory) {
  try {
    var cache = CacheService.getUserCache();
    cache.put("progress", JSON.stringify({ percentage: 0, stage: "開始" }), 600);
    
    var center = getMunicipalityCoordinates(prefecture, municipality);
    cache.put("progress", JSON.stringify({ percentage: 20, stage: "ジオコーディング完了" }), 600);
    
    var allMarkers = getMarkersFromSheet();
    cache.put("progress", JSON.stringify({ percentage: 30, stage: "全データ取得完了" }), 600);
    
    var filtered = [];
    var total = allMarkers.length;
    var lastProgress = 30;
    for (var i = 0; i < total; i++) {
      var marker = allMarkers[i];
      var distance = haversineDistance(center.lat, center.lng, marker.lat, marker.lng);
      if (distance <= radius) {
        if (employmentType !== "全て選択" && marker.employmentType !== employmentType) continue;
        if (salaryCategory !== "どちらも" && marker.salaryCategory !== salaryCategory) continue;
        filtered.push(marker);
      }
      var progressPercent = 30 + Math.floor(((i + 1) / total) * 40);
      if ((progressPercent - lastProgress) >= 10 || i === total - 1) {
        cache.put("progress", JSON.stringify({ percentage: progressPercent, stage: "フィルタ処理中" }), 600);
        lastProgress = progressPercent;
      }
    }
    
    var ss = SpreadsheetApp.openById(SPREADSHEET_ID);
    var filteredSheet = ss.getSheetByName(FILTERED_SHEET_NAME) || ss.insertSheet(FILTERED_SHEET_NAME);
    filteredSheet.clearContents();
    var outputDetailed = [["Latitude", "Longitude", "Info"]];
    filtered.forEach(function(marker) { outputDetailed.push([marker.lat, marker.lng, marker.info]); });
    if(outputDetailed.length > 1) filteredSheet.getRange(1, 1, outputDetailed.length, outputDetailed[0].length).setValues(outputDetailed);
      
    var extractedSheet = ss.getSheetByName(EXTRACTED_SHEET_NAME) || ss.insertSheet(EXTRACTED_SHEET_NAME);
    extractedSheet.clearContents();
    var outputSimple = [["Latitude", "Longitude", "給与_下限", "給与_上限"]];
    filtered.forEach(function(marker) { outputSimple.push([marker.lat, marker.lng, marker.salaryLower, marker.salaryUpper]); });
    if(outputSimple.length > 1) extractedSheet.getRange(1, 1, outputSimple.length, outputSimple[0].length).setValues(outputSimple);
      
    SpreadsheetApp.flush();
    cache.put("progress", JSON.stringify({ percentage: 90, stage: "シート転記完了" }), 600);
    
    cache.put("progress", JSON.stringify({ percentage: 100, stage: "完了" }), 600);
    return JSON.parse(JSON.stringify(filtered));
    
  } catch (e) {
    Logger.log("getFilteredMarkers() エラー: " + e.toString());
    return { error: true, message: "処理中にエラーが発生しました: " + e.message };
  }
}

/**
 * クライアント側から進捗状況を取得
 */
function getProgress() {
  var cache = CacheService.getUserCache();
  var progressStr = cache.get("progress");
  return progressStr ? JSON.parse(progressStr) : { percentage: 0, stage: "未開始" };
}

/**
 * 給与データの統計を生成
 */
function analyzeSalaryData() {
  var ss = SpreadsheetApp.openById(SPREADSHEET_ID);
  var sheet = ss.getSheetByName(EXTRACTED_SHEET_NAME);
  if (!sheet) return;
  var data = sheet.getDataRange().getValues();
  if (data.length < 2) return;
  var headers = data[0];
  var idxLower = headers.indexOf("給与_下限");
  var idxUpper = headers.indexOf("給与_上限");
  if (idxLower == -1 || idxUpper == -1) throw new Error("給与_下限/上限のカラムが見つかりません。");

  var lowerValues = [], upperValues = [];
  for (var i = 1; i < data.length; i++) {
    var lower = parseFloat(data[i][idxLower]);
    var upper = parseFloat(data[i][idxUpper]);
    if (!isNaN(lower)) lowerValues.push(lower);
    if (!isNaN(upper)) upperValues.push(upper);
  }
  var statsLower = computeStats(lowerValues);
  var statsUpper = computeStats(upperValues);

  var analysisSheet = ss.getSheetByName(ANALYSIS_SHEET_NAME) || ss.insertSheet(ANALYSIS_SHEET_NAME);
  analysisSheet.clear();
  
  var statsData = [
    ["区分", "平均", "中央値", "最頻値"],
    ["給与下限", statsLower.average, statsLower.median, statsLower.mode],
    ["給与上限", statsUpper.average, statsUpper.median, statsUpper.mode]
  ];
  analysisSheet.getRange(1, 1, statsData.length, statsData[0].length).setValues(statsData);

  // 以下、グラフ生成など（省略）
}

/**
 * Helper: 統計計算
 */
function computeStats(values) {
  if (values.length === 0) return { average: 0, median: 0, mode: 0 };
  var sorted = values.slice().sort(function(a, b) { return a - b; });
  var sum = values.reduce(function(a, b) { return a + b; }, 0);
  var average = sum / values.length;
  var mid = Math.floor(sorted.length / 2);
  var median = sorted.length % 2 === 0 ? (sorted[mid - 1] + sorted[mid]) / 2 : sorted[mid];
  var freq = {}, maxFreq = 0, mode = sorted[0];
  sorted.forEach(function(v) {
    freq[v] = (freq[v] || 0) + 1;
    if (freq[v] > maxFreq) { maxFreq = freq[v]; mode = v; }
  });
  return { average: average, median: median, mode: mode };
}