/**
 * 地域選択状態と候補リストを管理するサービス。
 * ユーザープロパティに選択済みの都道府県／市区町村を保存し、
 * MapMetricsシートから地域候補を動的に取得する。
 */

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
