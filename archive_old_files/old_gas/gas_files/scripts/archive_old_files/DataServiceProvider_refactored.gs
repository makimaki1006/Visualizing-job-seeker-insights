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

const REGION_STATE_KEYS = {
  PREFECTURE: 'regionalDashboard.prefecture',
  MUNICIPALITY: 'regionalDashboard.municipality'
};

const REGION_OPTION_CACHE = {
  PREFECTURES: 'regionalDashboard.prefList:v1',
  MUNICIPALITY_PREFIX: 'regionalDashboard.muniList:v1:',
  TTL_SECONDS: 300
};

const REGION_SOURCE_SHEETS = {
  MAP_METRICS: 'MapMetrics'
};

const REGION_COLUMN_LABELS = {
  PREFECTURE: ['都道府県', '都道府県名'],
  MUNICIPALITY: ['市区町村', '市区町村名', '自治体'],
  KEY: ['キー', '地域キー']
};

/**
 * 選択済み地域を保存する。
 * @param {string} prefecture 都道府県名
 * @param {string} municipality 市区町村名
 * @return {{prefecture: string|null, municipality: string|null}}
 */
function saveSelectedRegion(prefecture, municipality) {
  const userProps = PropertiesService.getUserProperties();
  const prefValue = normalizeRegionValue(prefecture);
  const muniValue = normalizeRegionValue(municipality);

  if (prefValue) {
    userProps.setProperty(REGION_STATE_KEYS.PREFECTURE, prefValue);
  } else {
    userProps.deleteProperty(REGION_STATE_KEYS.PREFECTURE);
  }

  if (muniValue) {
    userProps.setProperty(REGION_STATE_KEYS.MUNICIPALITY, muniValue);
  } else {
    userProps.deleteProperty(REGION_STATE_KEYS.MUNICIPALITY);
  }

  return {
    prefecture: prefValue,
    municipality: muniValue
  };
}

/**
 * 保存済み地域を読み込む。未保存の場合はMapMetricsから先頭候補を採用する。
 * @return {{prefecture: string|null, municipality: string|null, key: string|null}}
 */
function loadSelectedRegion() {
  const userProps = PropertiesService.getUserProperties();
  let prefecture = userProps.getProperty(REGION_STATE_KEYS.PREFECTURE);
  let municipality = userProps.getProperty(REGION_STATE_KEYS.MUNICIPALITY);

  if (!prefecture) {
    const defaults = getAvailablePrefectures();
    prefecture = defaults.length ? defaults[0] : null;
  }

  if (prefecture && municipality) {
    const municipalities = getMunicipalitiesForPrefecture(prefecture);
    if (!municipalities.includes(municipality)) {
      municipality = municipalities.length ? municipalities[0] : null;
    }
  } else if (prefecture && !municipality) {
    const municipalities = getMunicipalitiesForPrefecture(prefecture);
    municipality = municipalities.length ? municipalities[0] : null;
  }

  return {
    prefecture: prefecture,
    municipality: municipality,
    key: buildRegionKey(prefecture, municipality)
  };
}

/**
 * 地域選択をクリアする。
 */
function clearSelectedRegion() {
  const userProps = PropertiesService.getUserProperties();
  userProps.deleteProperty(REGION_STATE_KEYS.PREFECTURE);
  userProps.deleteProperty(REGION_STATE_KEYS.MUNICIPALITY);
}

/**
 * 利用可能な都道府県を取得する。
 * @return {string[]} 都道府県名リスト（昇順）
 */
function getAvailablePrefectures() {
  const cache = CacheService.getScriptCache();
  const cached = cache.get(REGION_OPTION_CACHE.PREFECTURES);
  if (cached) {
    return JSON.parse(cached);
  }

  const rows = readSheetRows(REGION_SOURCE_SHEETS.MAP_METRICS);
  if (!rows.length) {
    return [];
  }

  const prefectureIndex = findColumnIndex(rows[0], REGION_COLUMN_LABELS.PREFECTURE);
  if (prefectureIndex === -1) {
    return [];
  }

  const prefectures = Array.from(
    new Set(
      rows.slice(1)
        .map(row => normalizeRegionValue(row[prefectureIndex]))
        .filter(Boolean)
    )
  ).sort();

  cache.put(REGION_OPTION_CACHE.PREFECTURES, JSON.stringify(prefectures), REGION_OPTION_CACHE.TTL_SECONDS);
  return prefectures;
}

/**
 * 指定都道府県の市区町村リストを取得する。
 * @param {string} prefecture 都道府県名
 * @return {string[]} 市区町村リスト（昇順）
 */
function getMunicipalitiesForPrefecture(prefecture) {
  const prefValue = normalizeRegionValue(prefecture);
  if (!prefValue) {
    return [];
  }

  const cacheKey = REGION_OPTION_CACHE.MUNICIPALITY_PREFIX + prefValue;
  const cache = CacheService.getScriptCache();
  const cached = cache.get(cacheKey);
  if (cached) {
    return JSON.parse(cached);
  }

  const rows = readSheetRows(REGION_SOURCE_SHEETS.MAP_METRICS);
  if (!rows.length) {
    return [];
  }

  const header = rows[0];
  const prefIndex = findColumnIndex(header, REGION_COLUMN_LABELS.PREFECTURE);
  const muniIndex = findColumnIndex(header, REGION_COLUMN_LABELS.MUNICIPALITY);
  if (prefIndex === -1 || muniIndex === -1) {
    return [];
  }

  const municipalities = Array.from(
    new Set(
      rows.slice(1)
        .filter(row => normalizeRegionValue(row[prefIndex]) === prefValue)
        .map(row => normalizeRegionValue(row[muniIndex]))
        .filter(Boolean)
    )
  ).sort();

  cache.put(cacheKey, JSON.stringify(municipalities), REGION_OPTION_CACHE.TTL_SECONDS);
  return municipalities;
}

/**
 * 地域候補と保存済み状態をまとめて取得する。
 * @return {{state: {prefecture: string|null, municipality: string|null, key: string|null}, prefectures: string[], municipalities: string[]}}
 */
function getRegionOptions() {
  const state = loadSelectedRegion();
  const prefectures = getAvailablePrefectures();
  const municipalities = state.prefecture ? getMunicipalitiesForPrefecture(state.prefecture) : [];
  return {
    state: state,
    prefectures: prefectures,
    municipalities: municipalities
  };
}

/**
 * 地域候補キャッシュを破棄する。
 */
function resetRegionOptionCache() {
  const cache = CacheService.getScriptCache();
  cache.remove(REGION_OPTION_CACHE.PREFECTURES);
  const prefectures = getAvailablePrefectures();
  prefectures.forEach(pref => {
    cache.remove(REGION_OPTION_CACHE.MUNICIPALITY_PREFIX + pref);
  });
}

/**
 * MapMetricsシートを2次元配列で取得する。
 * @param {string} sheetName シート名
 * @return {Array<Array<*>>}
 */
function readSheetRows(sheetName) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName(sheetName);
  if (!sheet) {
    return [];
  }
  const values = sheet.getDataRange().getValues();
  return values || [];
}

/**
 * 候補列名の中から一致する列インデックスを取得する。
 * @param {string[]} header ヘッダー行
 * @param {string[]} candidates 優先候補
 * @return {number} 見つかった列番号（0始まり） / 見つからない場合は -1
 */
function findColumnIndex(header, candidates) {
  for (let i = 0; i < header.length; i += 1) {
    const label = header[i];
    if (!label) {
      continue;
    }
    const normalized = normalizeRegionValue(label);
    if (candidates.includes(label) || candidates.includes(normalized)) {
      return i;
    }
  }
  return -1;
}

/**
 * 地域名の正規化。
 * @param {string} value 対象文字列
 * @return {string|null}
 */
function normalizeRegionValue(value) {
  if (value === null || value === undefined) {
    return null;
  }
  const trimmed = String(value).trim();
  return trimmed.length ? trimmed : null;
}

/**
 * 地域キーを生成する。
 * @param {string|null} prefecture 都道府県
 * @param {string|null} municipality 市区町村
 * @return {string|null}
 */
function buildRegionKey(prefecture, municipality) {
  const pref = normalizeRegionValue(prefecture);
  if (!pref) {
    return null;
  }
  const muni = normalizeRegionValue(municipality);
  return muni ? pref + muni : pref;
}


