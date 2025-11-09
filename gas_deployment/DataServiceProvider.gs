/**
 * データサービスプロバイダー統合ファイル
 *
 * このファイルには以下のデータサービス機能がすべて含まれています:
 * 1. 地図データプロバイダー
 * 2. Google Maps API設定
 * 3. 地域状態サービス
 */

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 共通ユーティリティ関数
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

/**
 * データ読み込み共通エラーハンドリング
 * @param {string} sheetName - シート名
 * @param {number} columnCount - カラム数
 * @return {Array<Array>} データ配列
 */
function loadSheetData_(sheetName, columnCount) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName(sheetName);

  if (!sheet) {
    throw new Error(`${sheetName}シートが見つかりません`);
  }

  const lastRow = sheet.getLastRow();
  if (lastRow <= 1) {
    return [];
  }

  const range = sheet.getRange(2, 1, lastRow - 1, columnCount);
  return range.getValues();
}

/**
 * データなしアラート表示
 * @param {string} sheetName - シート名
 * @param {string} phaseName - Phase名
 */
function showNoDataAlert_(sheetName, phaseName) {
  const ui = SpreadsheetApp.getUi();
  ui.alert(
    'データなし',
    `${sheetName}シートにデータがありません。\n` +
    `先に「${phaseName}データ取り込み」を実行してください。`,
    ui.ButtonSet.OK
  );
}

/**
 * エラーアラート表示
 * @param {Error} error - エラーオブジェクト
 * @param {string} context - エラーコンテキスト
 */
function showErrorAlert_(error, context) {
  const ui = SpreadsheetApp.getUi();
  ui.alert('エラー', `${context}中にエラーが発生しました:\n${error.message}`, ui.ButtonSet.OK);
  Logger.log(`${context}エラー: ${error.stack}`);
}

/**
 * HTMLダイアログ表示
 * @param {string} html - HTML文字列
 * @param {string} title - ダイアログタイトル
 * @param {number} width - 幅（デフォルト: 1400）
 * @param {number} height - 高さ（デフォルト: 900）
 */
function showHtmlDialog_(html, title, width = 1400, height = 900) {
  const htmlOutput = HtmlService.createHtmlOutput(html)
    .setWidth(width)
    .setHeight(height);
  SpreadsheetApp.getUi().showModalDialog(htmlOutput, title);
}



// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 1. 地図データプロバイダー
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

/**
 * 全可視化データを取得
 * map_GAS_complete.htmlで使用
 */
function getAllVisualizationData() {
  try {
    const ss = SpreadsheetApp.getActiveSpreadsheet();

    // 4つのシートからデータ取得
    const mapMetrics = getSheetData(ss, 'Phase1_MapMetrics');
    const applicants = getSheetData(ss, 'Phase1_Applicants');
    const desiredWork = getSheetData(ss, 'Phase1_DesiredWork');
    const aggDesired = getSheetData(ss, 'Phase1_AggDesired');

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
  let htmlOutput;
  try {
    htmlOutput = HtmlService.createHtmlOutputFromFile('map_complete_prototype_Ver2')
      .setWidth(1400)
      .setHeight(860);
  } catch (error) {
    Logger.log('map_complete_prototype_Ver2 の読み込みに失敗。旧UIへフォールバックします: ' + error.message);
    htmlOutput = HtmlService.createHtmlOutputFromFile('MapComplete')
      .setWidth(1400)
      .setHeight(800);
  }

  SpreadsheetApp.getUi().showModalDialog(htmlOutput, '🗺️ 求職者データ分析マップ');
}

/**
 * 旧MapComplete UI（レガシー版）を直接起動する。
 * 新UIの動作確認が完了するまでの暫定フォールバック用。
 */
function showMapCompleteLegacy() {
  const htmlOutput = HtmlService.createHtmlOutputFromFile('MapComplete')
    .setWidth(1400)
    .setHeight(800);
  SpreadsheetApp.getUi().showModalDialog(htmlOutput, '🗺️ 求職者データ分析マップ（旧UI）');
}

/**
 * 地図表示（バブルマップ）
 */
function showMapBubble() {
  const html = HtmlService.createHtmlOutputFromFile('MapComplete')
    .setWidth(1400)
    .setHeight(800);

  SpreadsheetApp.getUi().showModalDialog(html, '🗺️ 地図表示（バブル）');
}

/**
 * 地図表示（ヒートマップ）
 */
function showMapHeatmap() {
  const html = HtmlService.createHtmlOutputFromFile('MapComplete')
    .setWidth(1400)
    .setHeight(800);

  SpreadsheetApp.getUi().showModalDialog(html, '📍 地図表示（ヒートマップ）');
}


// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 2. Google Maps API設定
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

/**
 * Google Maps APIキー取得（セキュア版・オプショナル対応）
 *
 * @param {boolean} throwError - APIキー未設定時にエラーをスローするか（デフォルト: false）
 * @return {string|null} Google Maps APIキー（未設定時はnull）
 */
function getGoogleMapsAPIKey(throwError = false) {
  const properties = PropertiesService.getScriptProperties();
  const apiKey = properties.getProperty('GOOGLE_MAPS_API_KEY');

  if (!apiKey) {
    if (throwError) {
      throw new Error(
        'Google Maps APIキーが設定されていません。\n\n' +
        '設定方法:\n' +
        '1. GASエディタ > プロジェクト設定（歯車アイコン）\n' +
        '2. 「スクリプトのプロパティ」セクション\n' +
        '3. 「スクリプト プロパティを追加」\n' +
        '4. プロパティ名: GOOGLE_MAPS_API_KEY\n' +
        '5. 値: あなたのGoogle Maps APIキー\n' +
        '6. 保存後、再度この機能を実行してください'
      );
    }

    // エラーをスローしない場合は警告をログに出力
    console.warn('⚠️ Google Maps APIキーが未設定です。一部の地図機能が制限される場合があります。');
    return null;
  }

  return apiKey;
}

/**
 * Google Maps APIキー設定（初回セットアップ用）
 *
 * 注意: この関数は初回セットアップ時に一度だけ実行してください
 * セキュリティ上、APIキーをコード内に直接書かないでください
 *
 * @param {string} apiKey - Google Maps APIキー
 */
function setGoogleMapsAPIKey(apiKey) {
  if (!apiKey || apiKey.trim() === '') {
    throw new Error('APIキーが空です');
  }

  if (apiKey === 'YOUR_API_KEY_HERE') {
    throw new Error('プレースホルダーのままです。実際のAPIキーを設定してください');
  }

  const properties = PropertiesService.getScriptProperties();
  properties.setProperty('GOOGLE_MAPS_API_KEY', apiKey);

  Logger.log('Google Maps APIキーを設定しました');
  Logger.log('セキュリティのため、この関数内のAPIキーは削除してください');
}

/**
 * Google Maps APIキー検証
 *
 * @return {boolean} APIキーが設定されている場合true
 */
function validateGoogleMapsAPIKey() {
  try {
    const apiKey = getGoogleMapsAPIKey();
    return apiKey && apiKey.length > 0 && apiKey !== 'YOUR_API_KEY_HERE';
  } catch (error) {
    return false;
  }
}

/**
 * Google Maps スクリプトタグ生成（セキュア版・オプショナル対応）
 *
 * @param {Array<string>} libraries - 読み込むライブラリ（例: ['visualization', 'geometry']）
 * @return {string} Google Maps スクリプトタグHTML（APIキー未設定時は警告コメント）
 */
function generateGoogleMapsScriptTag(libraries) {
  const apiKey = getGoogleMapsAPIKey(false); // エラーをスローしない

  if (!apiKey) {
    // APIキーが未設定の場合は警告コメントを返す
    return `<!-- ⚠️ Google Maps APIキーが未設定です。地図機能が制限されています。 -->`;
  }

  let scriptUrl = `https://maps.googleapis.com/maps/api/js?key=${apiKey}`;

  if (libraries && libraries.length > 0) {
    scriptUrl += `&libraries=${libraries.join(',')}`;
  }

  return `<script src="${scriptUrl}"></script>`;
}

/**
 * APIキー設定状況確認（デバッグ用）
 */
function checkAPIKeyStatus() {
  const ui = SpreadsheetApp.getUi();

  try {
    const apiKey = getGoogleMapsAPIKey();
    const maskedKey = apiKey.substring(0, 10) + '...' + apiKey.substring(apiKey.length - 4);

    ui.alert(
      'APIキー設定確認',
      `✅ Google Maps APIキーが設定されています\n\n` +
      `マスク済みキー: ${maskedKey}\n` +
      `キー長: ${apiKey.length}文字\n\n` +
      `セキュリティのため、完全なキーは表示されません。`,
      ui.ButtonSet.OK
    );
  } catch (error) {
    ui.alert(
      'APIキー未設定',
      `❌ Google Maps APIキーが設定されていません\n\n` +
      error.message,
      ui.ButtonSet.OK
    );
  }
}

/**
 * APIキーリセット（管理者用）
 *
 * 注意: この操作は取り消せません
 */
function resetGoogleMapsAPIKey() {
  const ui = SpreadsheetApp.getUi();

  const response = ui.alert(
    'APIキーリセット',
    '本当にGoogle Maps APIキーをリセットしますか？\n\n' +
    'この操作は取り消せません。',
    ui.ButtonSet.YES_NO
  );

  if (response === ui.Button.YES) {
    const properties = PropertiesService.getScriptProperties();
    properties.deleteProperty('GOOGLE_MAPS_API_KEY');

    ui.alert(
      'リセット完了',
      'Google Maps APIキーをリセットしました。\n\n' +
      '再度setGoogleMapsAPIKey()関数を使用して設定してください。',
      ui.ButtonSet.OK
    );

    Logger.log('Google Maps APIキーをリセットしました');
  }
}


// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 3. 地域状態サービス
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
//
// 注: 地域状態サービスの関数と定数は RegionStateService.gs に移動しました。
// 以下の関数を使用してください:
// - saveSelectedRegion(prefecture, municipality)
// - loadSelectedRegion()
// - listPrefectureOptions()
// - listMunicipalityOptions(prefecture)
//

