/**
 * 地図表示機能（新システム版）- 修正版
 *
 * Phase 1のMapMetricsデータを使用してバブルマップを表示
 *
 * 作成日: 2025-10-27
 * 修正日: 2025-10-28 - カラム名の互換性対応
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
 *
 * 【修正内容】
 * - '人数'と'希望者数'の両方に対応（旧形式・新形式互換）
 * - データ検証を強化
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

    Logger.log('MapMetrics ヘッダー: ' + headers.join(', '));

    // ヘッダーのインデックスを取得
    const prefectureIndex = headers.indexOf('都道府県');
    const keyIndex = headers.indexOf('キー');

    // 【修正】'人数'と'希望者数'の両方に対応
    let countIndex = headers.indexOf('希望者数');
    if (countIndex === -1) {
      countIndex = headers.indexOf('人数');
    }

    const latIndex = headers.indexOf('緯度');
    const lngIndex = headers.indexOf('経度');

    // デバッグログ
    Logger.log(`インデックス検出: prefecture=${prefectureIndex}, key=${keyIndex}, count=${countIndex}, lat=${latIndex}, lng=${lngIndex}`);

    // インデックス検証
    if (countIndex === -1) {
      throw new Error('カラム「希望者数」または「人数」が見つかりません。ヘッダー: ' + headers.join(', '));
    }
    if (latIndex === -1 || lngIndex === -1) {
      throw new Error('カラム「緯度」「経度」が見つかりません。ヘッダー: ' + headers.join(', '));
    }

    // データをオブジェクト配列に変換
    const result = rows.map((row, index) => {
      const item = {
        prefecture: row[prefectureIndex] || '',
        key: row[keyIndex] || '',
        count: Number(row[countIndex]) || 0,
        lat: Number(row[latIndex]) || 0,
        lng: Number(row[lngIndex]) || 0
      };

      // 最初の3件をログ出力（デバッグ用）
      if (index < 3) {
        Logger.log(`データ例${index + 1}: count=${item.count}, lat=${item.lat}, lng=${item.lng}`);
      }

      return item;
    }).filter(item => {
      // データ検証を強化
      const isValid = item.lat !== 0 && item.lng !== 0 && item.count > 0;
      if (!isValid && item.key) {
        Logger.log(`除外データ: ${item.key} (count=${item.count}, lat=${item.lat}, lng=${item.lng})`);
      }
      return isValid;
    });

    Logger.log(`MapMetricsデータ取得: ${result.length}件（全${rows.length}件中）`);

    if (result.length === 0) {
      throw new Error('有効なデータがありません。緯度・経度・人数がすべて0以外のデータが必要です。');
    }

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
