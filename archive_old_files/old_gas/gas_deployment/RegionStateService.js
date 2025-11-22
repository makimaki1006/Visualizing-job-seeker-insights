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
  MAP_METRICS: ['Phase1_MapMetrics', 'MapMetrics', 'Phase1_AggDesired', 'AggDesired']
};

const REGION_COLUMN_LABELS = {
  PREFECTURE: [
    '都道府県', '都道府県名', 'prefecture', 'Prefecture', 'PREFECTURE',
    'desired_prefecture', 'residence_prefecture', 'residence_pref',  // 🚀 追加: 実際のシートで使用されているカラム名
    'origin_pref', 'destination_pref', 'pref'  // 🚀 追加: FlowEdges、略称
  ],
  MUNICIPALITY: [
    '市区町村', '市区町村名', '自治体', 'municipality', 'Municipality', 'MUNICIPALITY',
    'desired_municipality', 'residence_municipality', 'residence_muni',  // 🚀 追加: 実際のシートで使用されているカラム名
    'origin_muni', 'destination_muni', 'muni', 'city'  // 🚀 追加: FlowEdges、略称
  ],
  KEY: ['キー', '地域キー', 'location_key', 'key', 'Key', 'KEY']
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
  Logger.log('========================================');
  Logger.log('[getAvailablePrefectures] 開始（MapComplete_Complete_All_FIXEDシートから取得）');
  Logger.log('========================================');

  const cache = CacheService.getScriptCache();
  const cached = cache.get(REGION_OPTION_CACHE.PREFECTURES);
  if (cached) {
    const cachedResult = JSON.parse(cached);
    Logger.log('[getAvailablePrefectures] 🔵 キャッシュから取得: ' + cachedResult.length + ' 件');
    Logger.log('[getAvailablePrefectures] キャッシュ内容: ' + JSON.stringify(cachedResult.slice(0, 10)));
    Logger.log('========================================');
    return cachedResult;
  }

  Logger.log('[getAvailablePrefectures] 🟢 キャッシュなし - MapComplete_Complete_All_FIXEDシートから都道府県抽出開始');

  // 統合CSV（MapComplete_Complete_All_FIXED）から都道府県リストを抽出
  const sheetName = 'MapComplete_Complete_All_FIXED';
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName(sheetName);

  if (!sheet) {
    Logger.log('[getAvailablePrefectures] ❌ シートが見つかりません: ' + sheetName);
    Logger.log('========================================');
    return [];
  }

  Logger.log('[getAvailablePrefectures] ✅ シート発見: ' + sheetName);

  const dataRange = sheet.getDataRange();
  const values = dataRange.getValues();
  Logger.log('[getAvailablePrefectures] データ行数: ' + values.length + '行');

  if (values.length === 0) {
    Logger.log('[getAvailablePrefectures] ❌ シートにデータがありません');
    Logger.log('========================================');
    return [];
  }

  const header = values[0];
  const prefIndex = header.indexOf('prefecture');

  if (prefIndex === -1) {
    Logger.log('[getAvailablePrefectures] ❌ prefecture列が見つかりません');
    Logger.log('========================================');
    return [];
  }

  // prefecture列からユニークな都道府県リストを抽出
  const prefectures = [];
  for (let i = 1; i < values.length; i++) {
    const row = values[i];
    const prefecture = row[prefIndex];
    if (prefecture) {
      const normalized = normalizeRegionValue(prefecture);
      if (normalized && prefectures.indexOf(normalized) === -1) {
        prefectures.push(normalized);
      }
    }
  }

  prefectures.sort();

  Logger.log('[getAvailablePrefectures] 抽出された都道府県数: ' + prefectures.length);
  Logger.log('[getAvailablePrefectures] 都道府県リスト: ' + JSON.stringify(prefectures));
  Logger.log('[getAvailablePrefectures] キャッシュに保存（TTL: ' + REGION_OPTION_CACHE.TTL_SECONDS + '秒）');

  cache.put(REGION_OPTION_CACHE.PREFECTURES, JSON.stringify(prefectures), REGION_OPTION_CACHE.TTL_SECONDS);

  Logger.log('========================================');
  return prefectures;
}

/**
 * 指定都道府県の市区町村リストを取得する。
 * @param {string} prefecture 都道府県名
 * @return {string[]} 市区町村リスト（昇順）
 */
function getMunicipalitiesForPrefecture(prefecture) {
  Logger.log('========================================');
  Logger.log('[getMunicipalitiesForPrefecture] 開始（MapComplete_Complete_*シートから取得）');
  Logger.log('[getMunicipalitiesForPrefecture] 入力: prefecture = "' + prefecture + '"');
  Logger.log('========================================');

  const prefValue = normalizeRegionValue(prefecture);
  if (!prefValue) {
    Logger.log('[getMunicipalitiesForPrefecture] ❌ 都道府県が無効です');
    Logger.log('========================================');
    return [];
  }

  Logger.log('[getMunicipalitiesForPrefecture] 正規化後: prefecture = "' + prefValue + '"');

  const cacheKey = REGION_OPTION_CACHE.MUNICIPALITY_PREFIX + prefValue;
  const cache = CacheService.getScriptCache();
  const cached = cache.get(cacheKey);
  if (cached) {
    const cachedResult = JSON.parse(cached);
    Logger.log('[getMunicipalitiesForPrefecture] 🔵 キャッシュから取得: ' + cachedResult.length + ' 件');
    Logger.log('[getMunicipalitiesForPrefecture] キャッシュ内容（最初の10件）: ' + JSON.stringify(cachedResult.slice(0, 10)));
    Logger.log('========================================');
    return cachedResult;
  }

  Logger.log('[getMunicipalitiesForPrefecture] 🟢 キャッシュなし - シートからデータ読み込み開始');

  // 統合CSV（MapComplete_Complete_All_FIXED）から指定都道府県の市区町村リストを取得
  const sheetName = 'MapComplete_Complete_All_FIXED';
  Logger.log('[getMunicipalitiesForPrefecture] 対象シート名: "' + sheetName + '"');

  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName(sheetName);

  if (!sheet) {
    Logger.log('[getMunicipalitiesForPrefecture] ❌ シートが見つかりません: ' + sheetName);
    Logger.log('========================================');
    return [];
  }

  Logger.log('[getMunicipalitiesForPrefecture] ✅ シート発見: ' + sheetName);

  const dataRange = sheet.getDataRange();
  const values = dataRange.getValues();
  Logger.log('[getMunicipalitiesForPrefecture] データ行数: ' + values.length + '行');

  if (values.length === 0) {
    Logger.log('[getMunicipalitiesForPrefecture] ❌ シートにデータがありません');
    Logger.log('========================================');
    return [];
  }

  const header = values[0];
  Logger.log('[getMunicipalitiesForPrefecture] ヘッダー: ' + JSON.stringify(header.slice(0, 10)));

  const rowTypeIndex = header.indexOf('row_type');
  const prefIndex = header.indexOf('prefecture');
  const muniIndex = header.indexOf('municipality');
  Logger.log('[getMunicipalitiesForPrefecture] カラムインデックス: rowTypeIndex=' + rowTypeIndex + ', prefIndex=' + prefIndex + ', muniIndex=' + muniIndex);

  if (rowTypeIndex === -1 || muniIndex === -1) {
    Logger.log('[getMunicipalitiesForPrefecture] ❌ 必要なカラムが見つかりません');
    Logger.log('========================================');
    return [];
  }

  // SUMMARY行かつ指定都道府県から市区町村リストを抽出
  const municipalities = [];
  let summaryCount = 0;

  for (let i = 1; i < values.length; i++) {
    const row = values[i];
    const rowType = row[rowTypeIndex];
    const rowPrefecture = row[prefIndex];
    const municipality = row[muniIndex];

    // SUMMARY行かつ指定都道府県のみを対象にする
    if (rowType === 'SUMMARY' && rowPrefecture === prefValue && municipality) {
      summaryCount++;
      const normalized = normalizeRegionValue(municipality);
      if (normalized && municipalities.indexOf(normalized) === -1) {
        municipalities.push(normalized);
        if (municipalities.length <= 5) {
          Logger.log('[getMunicipalitiesForPrefecture]   SUMMARY行' + summaryCount + ': prefecture="' + rowPrefecture + '", municipality = "' + municipality + '" → 正規化: "' + normalized + '"');
        }
      }
    }
  }

  municipalities.sort();

  Logger.log('[getMunicipalitiesForPrefecture] SUMMARY行総数: ' + summaryCount + '件');
  Logger.log('[getMunicipalitiesForPrefecture] 抽出された市区町村数: ' + municipalities.length + '件');
  Logger.log('[getMunicipalitiesForPrefecture] 市区町村リスト（全件）: ' + JSON.stringify(municipalities));
  Logger.log('[getMunicipalitiesForPrefecture] キャッシュに保存（TTL: ' + REGION_OPTION_CACHE.TTL_SECONDS + '秒）');

  cache.put(cacheKey, JSON.stringify(municipalities), REGION_OPTION_CACHE.TTL_SECONDS);

  Logger.log('========================================');
  return municipalities;
}

/**
 * 地域候補と保存済み状態をまとめて取得する。
 * @return {{state: {prefecture: string|null, municipality: string|null, key: string|null}, prefectures: string[], municipalities: string[]}}
 */
function getRegionOptions() {
  Logger.log('========================================');
  Logger.log('[getRegionOptions] 地域オプション取得開始');
  Logger.log('========================================');

  const state = loadSelectedRegion();
  Logger.log('[getRegionOptions] 保存済み状態: prefecture="' + state.prefecture + '", municipality="' + state.municipality + '"');

  const prefectures = getAvailablePrefectures();
  Logger.log('[getRegionOptions] 都道府県リスト取得完了: ' + prefectures.length + '件');

  const municipalities = state.prefecture ? getMunicipalitiesForPrefecture(state.prefecture) : [];
  Logger.log('[getRegionOptions] 市区町村リスト取得完了: ' + municipalities.length + '件');

  const result = {
    state: state,
    prefectures: prefectures,
    municipalities: municipalities
  };

  Logger.log('========================================');
  Logger.log('[getRegionOptions] ✅ 地域オプション取得完了');
  Logger.log('========================================');

  return result;
}

/**
 * 地域候補キャッシュを破棄する。
 */
function resetRegionOptionCache() {
  Logger.log('========================================');
  Logger.log('[resetRegionOptionCache] キャッシュクリア開始');
  Logger.log('========================================');

  const cache = CacheService.getScriptCache();

  // 都道府県キャッシュをクリア
  cache.remove(REGION_OPTION_CACHE.PREFECTURES);
  Logger.log('[resetRegionOptionCache] 都道府県キャッシュをクリアしました');

  // 市区町村キャッシュをクリア
  const prefectures = getAvailablePrefectures();
  Logger.log('[resetRegionOptionCache] 市区町村キャッシュをクリア中... 対象: ' + prefectures.length + '都道府県');

  let clearedCount = 0;
  prefectures.forEach(function(pref) {
    const key = REGION_OPTION_CACHE.MUNICIPALITY_PREFIX + pref;
    cache.remove(key);
    clearedCount++;
    if (clearedCount <= 5) {
      Logger.log('[resetRegionOptionCache]   クリア' + clearedCount + ': ' + pref);
    }
  });

  Logger.log('[resetRegionOptionCache] 市区町村キャッシュをクリアしました: ' + clearedCount + '件');
  Logger.log('========================================');
  Logger.log('[resetRegionOptionCache] ✅ キャッシュクリア完了');
  Logger.log('========================================');
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// パフォーマンス最適化設定
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

/**
 * 最適化機能の有効/無効を制御するフラグ
 * true: TextFinder版の高速実装を使用
 * false: 従来の全行読み込み実装を使用（ロールバック用）
 *
 * ⚠️ 2025-11-05: スパースデータでのバッチ最適化失敗により一時無効化（1658バッチ/1748行 → 435秒、20倍悪化）
 * ✅ 2025-11-05: 都道府県別統合シート導入により再有効化
 *    - 統合シートは密なデータ（37-71行×57列）のため、TextFinderが有効に機能
 *    - 全国データ展開時（328,188行）に必須の最適化
 */
const ENABLE_TEXTFINDER_OPTIMIZATION = true;

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// シート行読み取り関数（旧実装 - バックアップ）
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

/**
 * MapMetricsシートを2次元配列で取得する（旧実装 - 全行読み込み）
 * @param {string|string[]} sheetName シート名または候補シート名の配列
 * @return {Array<Array<*>>}
 */
function readSheetRows_ORIGINAL(sheetName) {
  Logger.log('[readSheetRows_ORIGINAL] 開始 - sheetName: ' + JSON.stringify(sheetName));

  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const candidates = Array.isArray(sheetName) ? sheetName : [sheetName];

  for (let i = 0; i < candidates.length; i += 1) {
    const name = candidates[i];
    Logger.log('[readSheetRows_ORIGINAL] 試行 ' + (i + 1) + '/' + candidates.length + ': ' + name);

    const sheet = ss.getSheetByName(name);
    if (sheet) {
      const values = sheet.getDataRange().getValues();
      Logger.log('[readSheetRows_ORIGINAL] 成功 - シート "' + name + '" から ' + values.length + ' 行読み取り');
      return values || [];
    }
  }

  Logger.log('[readSheetRows_ORIGINAL] 警告 - 有効なシートが見つかりませんでした');
  return [];
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// シート行読み取り関数（新実装 - TextFinder最適化版）
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

/**
 * シート行を地域で絞り込んで取得する（高速版 - TextFinder使用）
 * @param {string|string[]} sheetName シート名または候補シート名の配列
 * @param {string} prefecture 都道府県名（省略可）
 * @param {string} municipality 市区町村名（省略可）
 * @return {Array<Array<*>>}
 */
function readSheetRows_OPTIMIZED(sheetName, prefecture, municipality) {
  const startTime = new Date();
  Logger.log('[readSheetRows_OPTIMIZED] 開始 - sheetName: ' + JSON.stringify(sheetName) +
             ', prefecture: ' + prefecture + ', municipality: ' + municipality);

  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const candidates = Array.isArray(sheetName) ? sheetName : [sheetName];

  for (let i = 0; i < candidates.length; i += 1) {
    const name = candidates[i];
    Logger.log('[readSheetRows_OPTIMIZED] 試行 ' + (i + 1) + '/' + candidates.length + ': ' + name);

    try {
      const sheet = ss.getSheetByName(name);
      if (!sheet) {
        continue;
      }

      const lastRow = sheet.getLastRow();
      const lastCol = sheet.getLastColumn();

      if (lastRow < 2) {
        Logger.log('[readSheetRows_OPTIMIZED] シート "' + name + '" にデータ行がありません');
        continue; // 🔧 修正: return → continue（次の候補を試す）
      }

    // ヘッダー行を取得
    const headers = sheet.getRange(1, 1, 1, lastCol).getValues()[0];
    Logger.log('[readSheetRows_OPTIMIZED] ヘッダー: ' + JSON.stringify(headers.slice(0, 5)) + '...');

    // 都道府県列のインデックスを検索
    const prefColIndex = findColumnIndex(headers, REGION_COLUMN_LABELS.PREFECTURE);

    if (prefColIndex === -1 || !prefecture) {
      // 都道府県列が見つからない、または prefecture が指定されていない場合は全行取得
      Logger.log('[readSheetRows_OPTIMIZED] 都道府県列なしまたは prefecture 未指定 → 全行取得にフォールバック');
      const allValues = sheet.getDataRange().getValues();
      Logger.log('[readSheetRows_OPTIMIZED] 全行取得完了: ' + allValues.length + ' 行');
      return allValues;
    }

    // TextFinderで都道府県を検索（高速）
    const prefCol = sheet.getRange(2, prefColIndex + 1, lastRow - 1, 1);
    const finder = prefCol.createTextFinder(prefecture)
      .matchEntireCell(true)
      .findAll();

    if (finder.length === 0) {
      Logger.log('[readSheetRows_OPTIMIZED] "' + prefecture + '" のデータが見つかりませんでした');
      return [headers]; // ヘッダーのみ返す
    }

    Logger.log('[readSheetRows_OPTIMIZED] TextFinder検索結果: ' + finder.length + ' 行見つかりました');

    // TextFinderの結果から行番号リストを取得
    let targetRowNums = [];
    for (let j = 0; j < finder.length; j += 1) {
      targetRowNums.push(finder[j].getRow());
    }

    // 🚀 最適化: municipality絞り込みがある場合、先に絞り込む
    if (municipality) {
      const muniColIndex = findColumnIndex(headers, REGION_COLUMN_LABELS.MUNICIPALITY);

      if (muniColIndex !== -1) {
        Logger.log('[readSheetRows_OPTIMIZED] 🚀 municipality絞り込み開始...');

        // 連続する行範囲を特定してバッチ取得
        targetRowNums.sort(function(a, b) { return a - b; });
        const ranges = buildBatchRanges_(targetRowNums);

        // 各範囲からmunicipality列を取得
        const matchingRowNums = [];
        const normalizedMuni = normalizeRegionValue(municipality);

        for (let i = 0; i < ranges.length; i += 1) {
          const range = ranges[i];
          const muniValues = sheet.getRange(range.start, muniColIndex + 1, range.count, 1).getValues();

          for (let j = 0; j < muniValues.length; j += 1) {
            const muniValue = normalizeRegionValue(muniValues[j][0]);
            if (muniValue === normalizedMuni) {
              matchingRowNums.push(range.start + j);
            }
          }
        }

        Logger.log('[readSheetRows_OPTIMIZED] municipality一致行数: ' + matchingRowNums.length + ' 行（' + finder.length + ' 行から絞り込み）');
        targetRowNums = matchingRowNums;
      }
    }

    // 🚀 最適化: 連続範囲に分割して一括取得
    if (targetRowNums.length === 0) {
      Logger.log('[readSheetRows_OPTIMIZED] 一致する行がありません');
      return [headers];
    }

    targetRowNums.sort(function(a, b) { return a - b; });
    const ranges = buildBatchRanges_(targetRowNums);
    Logger.log('[readSheetRows_OPTIMIZED] バッチ範囲数: ' + ranges.length + ' 個に分割');

    // 各範囲から全カラムを一括取得
    const result = [headers];
    for (let i = 0; i < ranges.length; i += 1) {
      const range = ranges[i];
      const batchData = sheet.getRange(range.start, 1, range.count, lastCol).getValues();
      for (let j = 0; j < batchData.length; j += 1) {
        result.push(batchData[j]);
      }
    }

    const elapsed = new Date() - startTime;
    Logger.log('[readSheetRows_OPTIMIZED] 成功: ' + (result.length - 1) + ' 行, ' + elapsed + 'ms (バッチ数: ' + ranges.length + ')');
    return result;

    } catch (error) {
      // 🔧 エラーハンドリング: このシートで失敗しても次の候補を試す
      Logger.log('[readSheetRows_OPTIMIZED] エラー: シート "' + name + '" の処理中にエラー発生: ' + error.message);
      Logger.log('[readSheetRows_OPTIMIZED] スタック: ' + error.stack);
      continue; // 次の候補を試す
    }
  }

  Logger.log('[readSheetRows_OPTIMIZED] 警告 - 有効なシートが見つかりませんでした');
  return [];
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// シート行読み取り関数（メイン - 切り替えロジック付き）
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

/**
 * MapMetricsシートを2次元配列で取得する。
 * prefecture/municipality が指定されている場合は、TextFinder で高速絞り込み。
 *
 * @param {string|string[]} sheetName シート名または候補シート名の配列
 * @param {string} prefecture 都道府県名（省略可）
 * @param {string} municipality 市区町村名（省略可）
 * @return {Array<Array<*>>}
 */
function readSheetRows(sheetName, prefecture, municipality) {
  // 最適化が有効 かつ prefecture が指定されている場合は新実装を使用
  if (ENABLE_TEXTFINDER_OPTIMIZATION && prefecture) {
    return readSheetRows_OPTIMIZED(sheetName, prefecture, municipality);
  }

  // それ以外は従来の実装を使用（後方互換性）
  return readSheetRows_ORIGINAL(sheetName);
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
 * 行番号リストを連続範囲に分割する（バッチ最適化用）。
 * @param {number[]} rowNums - ソート済みの行番号配列
 * @return {Array<{start: number, count: number}>} - 連続範囲の配列
 * @private
 *
 * 例: [5, 6, 7, 100, 101, 500, 501, 502]
 *  → [{start: 5, count: 3}, {start: 100, count: 2}, {start: 500, count: 3}]
 *
 * メモリ対策: 連続範囲が5000行を超える場合は分割
 */
function buildBatchRanges_(rowNums) {
  if (!rowNums || rowNums.length === 0) {
    return [];
  }

  const MAX_BATCH_SIZE = 5000; // 🔧 メモリ制限対策: 1回のgetRange()で取得する最大行数
  const ranges = [];
  let rangeStart = rowNums[0];
  let rangeCount = 1;

  for (let i = 1; i < rowNums.length; i += 1) {
    const currentRow = rowNums[i];
    const prevRow = rowNums[i - 1];

    // 連続している場合
    if (currentRow === prevRow + 1 && rangeCount < MAX_BATCH_SIZE) {
      rangeCount += 1;
    } else {
      // 連続が途切れた、またはバッチサイズ制限に達した場合、範囲を確定
      ranges.push({ start: rangeStart, count: rangeCount });
      rangeStart = currentRow;
      rangeCount = 1;
    }
  }

  // 最後の範囲を追加
  if (rangeCount > 0) {
    ranges.push({ start: rangeStart, count: rangeCount });
  }

  return ranges;
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
