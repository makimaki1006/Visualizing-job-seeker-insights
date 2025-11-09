/**
 * 地図表示機能（新システム版）
 *
 * Phase 1のMapMetricsデータを使用してバブルマップを表示
 *
 * 作成日: 2025-10-27
 */

/**
 * バブルマップ表示（ダイアログ）
 */
function showBubbleMap() {
  const html = HtmlService.createHtmlOutputFromFile('BubbleMap')
    .setWidth(1400)
    .setHeight(800);

  SpreadsheetApp.getUi().showModalDialog(html, '🗺️ 希望勤務地バブルマップ');
}

/**
 * ヒートマップ表示（ダイアログ）
 */
function showHeatMap() {
  const html = HtmlService.createHtmlOutputFromFile('HeatMap')
    .setWidth(1400)
    .setHeight(800);

  SpreadsheetApp.getUi().showModalDialog(html, '📍 希望勤務地ヒートマップ');
}

/**
 * MapMetricsデータを取得
 */
function getMapMetricsData() {
  try {
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    const sheet = findSheetByNames_(ss, ['Phase1_MapMetrics', 'MapMetrics', 'Phase1_AggDesired', 'AggDesired']);

    if (!sheet) {
      throw new Error('MapMetricsシートが見つかりません。Phase 1のデータをアップロードしてください。');
    }

    const data = sheet.getDataRange().getValues();

    if (data.length < 2) {
      throw new Error('MapMetricsシートにデータがありません。');
    }

    const headers = data[0];
    const rows = data.slice(1);

    Logger.log('[getMapMetricsData] ヘッダー: ' + JSON.stringify(headers.slice(0, 10)));

    // ヘッダーのインデックスを取得（ColumnUtils.gs の findColumnIndexByLogicalName を使用）
    const prefectureIndex = findColumnIndexByLogicalName(headers, 'prefecture');
    const keyIndex = findColumnIndexByLogicalName(headers, 'location_key');
    const countIndex = findColumnIndexByLogicalName(headers, 'count');
    const latIndex = findColumnIndexByLogicalName(headers, 'latitude');
    const lngIndex = findColumnIndexByLogicalName(headers, 'longitude');

    Logger.log('[getMapMetricsData] インデックス: pref=' + prefectureIndex + ', key=' + keyIndex + ', count=' + countIndex + ', lat=' + latIndex + ', lng=' + lngIndex);

    // データをオブジェクト配列に変換（safeGetColumn で安全に取得）
    const result = rows.map(row => ({
      prefecture: safeGetColumn(row, prefectureIndex, ''),
      key: safeGetColumn(row, keyIndex, ''),
      count: Number(safeGetColumn(row, countIndex, 0)) || 0,
      lat: Number(safeGetColumn(row, latIndex, 0)) || 0,
      lng: Number(safeGetColumn(row, lngIndex, 0)) || 0
    })).filter(item => item.lat !== 0 && item.lng !== 0 && item.count > 0);

    Logger.log(`MapMetricsデータ取得: ${result.length}件`);

    return result;

  } catch (error) {
    Logger.log('MapMetricsデータ取得エラー: ' + error.message);
    throw error;
  }
}

/**
 * Applicantsデータを取得（統計情報用）
 */
function getApplicantsStats() {
  try {
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    const sheet = findSheetByNames_(ss, ['Phase1_Applicants', 'Applicants']);

    if (!sheet) {
      return {
        total: 0,
        byGender: {},
        byAge: {},
        avgAge: 0
      };
    }

    const data = sheet.getDataRange().getValues();

    if (data.length < 2) {
      return {
        total: 0,
        byGender: {},
        byAge: {},
        avgAge: 0
      };
    }

    const headers = data[0];
    const rows = data.slice(1);

    // ヘッダーのインデックスを取得（ColumnUtils.gs の findColumnIndexByLogicalName を使用）
    const genderIndex = findColumnIndexByLogicalName(headers, 'gender');
    const ageIndex = findColumnIndexByLogicalName(headers, 'age');
    const ageGroupIndex = findColumnIndexByLogicalName(headers, 'age_group');

    const stats = {
      total: rows.length,
      byGender: {},
      byAge: {},
      avgAge: 0
    };

    let totalAge = 0;
    let validAgeCount = 0;

    rows.forEach(row => {
      // 性別集計（safeGetColumn で安全に取得）
      const gender = safeGetColumn(row, genderIndex, null);
      if (gender) {
        stats.byGender[gender] = (stats.byGender[gender] || 0) + 1;
      }

      // 年齢層集計
      const ageGroup = safeGetColumn(row, ageGroupIndex, null);
      if (ageGroup) {
        stats.byAge[ageGroup] = (stats.byAge[ageGroup] || 0) + 1;
      }

      // 平均年齢計算
      const age = Number(safeGetColumn(row, ageIndex, 0));
      if (age > 0) {
        totalAge += age;
        validAgeCount++;
      }
    });

    if (validAgeCount > 0) {
      stats.avgAge = Math.round(totalAge / validAgeCount * 10) / 10;
    }

    Logger.log(`Applicants統計: 総数=${stats.total}, 平均年齢=${stats.avgAge}`);

    return stats;

  } catch (error) {
    Logger.log('Applicants統計取得エラー: ' + error.message);
    return {
      total: 0,
      byGender: {},
      byAge: {},
      avgAge: 0
    };
  }
}

/**
 * DesiredWorkデータを取得（TOP10都道府県用）
 */
function getDesiredWorkTop10() {
  try {
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    const sheet = findSheetByNames_(ss, ['Phase1_DesiredWork', 'DesiredWork']);

    if (!sheet) {
      return [];
    }

    const data = sheet.getDataRange().getValues();

    if (data.length < 2) {
      return [];
    }

    const headers = data[0];
    const rows = data.slice(1);

    // ヘッダーのインデックスを取得（ColumnUtils.gs の findColumnIndexByLogicalName を使用）
    const prefectureIndex = findColumnIndexByLogicalName(headers, 'desired_prefecture');

    // 都道府県別に集計
    const countByPrefecture = {};

    rows.forEach(row => {
      const prefecture = safeGetColumn(row, prefectureIndex, null);
      if (prefecture) {
        countByPrefecture[prefecture] = (countByPrefecture[prefecture] || 0) + 1;
      }
    });

    // 配列に変換してソート
    const sorted = Object.entries(countByPrefecture)
      .map(([prefecture, count]) => ({ prefecture, count }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 10);

    Logger.log(`希望勤務地TOP10: ${sorted.length}件`);

    return sorted;

  } catch (error) {
    Logger.log('DesiredWorkデータ取得エラー: ' + error.message);
    return [];
  }
}

/**
 * 複数のシート名候補から最初に見つかったシートを返す
 * @param {Spreadsheet} spreadsheet - スプレッドシートオブジェクト
 * @param {string[]} sheetNames - シート名候補の配列
 * @return {Sheet|null} - 見つかったシート、またはnull
 */
function findSheetByNames_(spreadsheet, sheetNames) {
  Logger.log('[findSheetByNames_] シート名候補: ' + JSON.stringify(sheetNames));

  for (let i = 0; i < sheetNames.length; i += 1) {
    const sheetName = sheetNames[i];
    Logger.log('[findSheetByNames_] 試行 ' + (i + 1) + '/' + sheetNames.length + ': ' + sheetName);

    const sheet = spreadsheet.getSheetByName(sheetName);
    if (sheet) {
      Logger.log('[findSheetByNames_] 成功 - シート "' + sheetName + '" を使用します');
      return sheet;
    }
  }

  Logger.log('[findSheetByNames_] 警告 - 有効なシートが見つかりませんでした');
  return null;
}
