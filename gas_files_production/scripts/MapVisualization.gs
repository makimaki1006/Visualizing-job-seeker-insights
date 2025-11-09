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
    const sheet = ss.getSheetByName('MapMetrics');

    if (!sheet) {
      throw new Error('MapMetricsシートが見つかりません。Phase 1のデータをアップロードしてください。');
    }

    const data = sheet.getDataRange().getValues();

    if (data.length < 2) {
      throw new Error('MapMetricsシートにデータがありません。');
    }

    const headers = data[0];
    const rows = data.slice(1);

    // ヘッダーのインデックスを取得
    const prefectureIndex = headers.indexOf('都道府県');
    const keyIndex = headers.indexOf('キー');
    const countIndex = headers.indexOf('人数');
    const latIndex = headers.indexOf('緯度');
    const lngIndex = headers.indexOf('経度');

    // データをオブジェクト配列に変換
    const result = rows.map(row => ({
      prefecture: row[prefectureIndex] || '',
      key: row[keyIndex] || '',
      count: Number(row[countIndex]) || 0,
      lat: Number(row[latIndex]) || 0,
      lng: Number(row[lngIndex]) || 0
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
    const sheet = ss.getSheetByName('Applicants');

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

    // ヘッダーのインデックスを取得
    const genderIndex = headers.indexOf('性別');
    const ageIndex = headers.indexOf('年齢');
    const ageGroupIndex = headers.indexOf('年齢層');

    const stats = {
      total: rows.length,
      byGender: {},
      byAge: {},
      avgAge: 0
    };

    let totalAge = 0;
    let validAgeCount = 0;

    rows.forEach(row => {
      // 性別集計
      const gender = row[genderIndex];
      if (gender) {
        stats.byGender[gender] = (stats.byGender[gender] || 0) + 1;
      }

      // 年齢層集計
      const ageGroup = row[ageGroupIndex];
      if (ageGroup) {
        stats.byAge[ageGroup] = (stats.byAge[ageGroup] || 0) + 1;
      }

      // 平均年齢計算
      const age = Number(row[ageIndex]);
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
    const sheet = ss.getSheetByName('DesiredWork');

    if (!sheet) {
      return [];
    }

    const data = sheet.getDataRange().getValues();

    if (data.length < 2) {
      return [];
    }

    const headers = data[0];
    const rows = data.slice(1);

    // ヘッダーのインデックスを取得
    const prefectureIndex = headers.indexOf('希望都道府県');

    // 都道府県別に集計
    const countByPrefecture = {};

    rows.forEach(row => {
      const prefecture = row[prefectureIndex];
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
