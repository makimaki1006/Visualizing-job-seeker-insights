/**
 * Phase 1-6 統合可視化ファイル
 *
 * このファイルには以下の可視化機能がすべて含まれています:
 * 1. 地図可視化（バブル・ヒートマップ）
 * 2. 統計分析・ペルソナ可視化
 * 3. 自治体間フロー分析
 * 4. ペルソナマップデータ可視化
 * 5. マトリックスヒートマップ
 * 6. 統合ダッシュボード（Phase 1-6）
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
// 1. 地図可視化（バブル・ヒートマップ）
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

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


// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 2. 統計分析・ペルソナ可視化
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

/**
 * カイ二乗検定結果の表示
 */
function showChiSquareTests() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName('ChiSquareTests');

  if (!sheet) {
    SpreadsheetApp.getUi().alert(
      'エラー',
      'ChiSquareTestsシートが見つかりません。\n' +
      'Phase 2データをインポートしてください。',
      SpreadsheetApp.getUi().ButtonSet.OK
    );
    return;
  }

  const data = sheet.getDataRange().getValues();

  if (data.length <= 1) {
    SpreadsheetApp.getUi().alert(
      '情報',
      'カイ二乗検定のデータがありません。',
      SpreadsheetApp.getUi().ButtonSet.OK
    );
    return;
  }

  // HTMLレポート生成
  let html = `
    <style>
    /* 共通スタイル */
    body {
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      margin: 20px;
      background-color: #f5f5f5;
    }
    h1 {
      color: #1a73e8;
      border-bottom: 3px solid #1a73e8;
      padding-bottom: 10px;
    }
    h2 {
      color: #333;
      margin-top: 20px;
    }
    .container {
      background-color: white;
      padding: 20px;
      border-radius: 8px;
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
      margin-bottom: 20px;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      margin-top: 10px;
    }
    th, td {
      padding: 12px;
      text-align: left;
      border-bottom: 1px solid #ddd;
    }
    th {
      background-color: #1a73e8;
      color: white;
      font-weight: bold;
      position: sticky;
      top: 0;
      z-index: 10;
    }
    tr:hover {
      background-color: #f5f5f5;
    }
    .stat-card {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      padding: 20px;
      border-radius: 8px;
      text-align: center;
    }
    .stat-label {
      font-size: 12px;
      opacity: 0.9;
      margin-bottom: 5px;
    }
    .stat-value {
      font-size: 28px;
      font-weight: bold;
    }

    /* Phase固有スタイル */
      body { font-family: Arial, sans-serif; padding: 20px; }
      h2 { color: #1a73e8; border-bottom: 2px solid #1a73e8; padding-bottom: 10px; }
      .test-card {
        background: #f8f9fa;
        border-left: 4px solid #1a73e8;
        padding: 15px;
        margin: 15px 0;
        border-radius: 4px;
      }
      .metric { display: inline-block; margin: 10px 20px 10px 0; }
      .metric-label { font-weight: bold; color: #5f6368; }
      .metric-value { font-size: 1.2em; color: #202124; }
      .significant { color: #ea4335; font-weight: bold; }
      .not-significant { color: #34a853; }
      .interpretation {
        background: #e8f0fe;
        padding: 10px;
        border-radius: 4px;
        margin-top: 10px;
        font-style: italic;
      }
    </style>

    <h2>🔬 カイ二乗検定結果</h2>
  `;

  // ヘッダー行をスキップ
  for (let i = 1; i < data.length; i++) {
    const row = data[i];
    const pattern = row[0];
    const group1 = row[1];
    const group2 = row[2];
    const variable = row[3];
    const chiSquare = row[4];
    const pValue = row[5];
    const df = row[6];
    const effectSize = row[7];
    const significant = row[8];
    const sampleSize = row[9];
    const interpretation = row[10];

    const significantClass = significant ? 'significant' : 'not-significant';
    const significantText = significant ? '有意' : '有意でない';

    html += `
      <div class="test-card">
        <h3>${pattern}</h3>
        <div class="metric">
          <span class="metric-label">カイ二乗値:</span>
          <span class="metric-value">${chiSquare.toFixed(4)}</span>
        </div>
        <div class="metric">
          <span class="metric-label">p値:</span>
          <span class="metric-value ${significantClass}">${pValue.toFixed(4)}</span>
        </div>
        <div class="metric">
          <span class="metric-label">自由度:</span>
          <span class="metric-value">${df}</span>
        </div>
        <div class="metric">
          <span class="metric-label">効果量:</span>
          <span class="metric-value">${effectSize.toFixed(4)}</span>
        </div>
        <div class="metric">
          <span class="metric-label">サンプルサイズ:</span>
          <span class="metric-value">${sampleSize}</span>
        </div>
        <div class="metric">
          <span class="metric-label">有意性:</span>
          <span class="metric-value ${significantClass}">${significantText}</span>
        </div>
        <div class="interpretation">
          💡 解釈: ${interpretation}
        </div>
      </div>
    `;
  }

  const htmlOutput = HtmlService.createHtmlOutput(html)
    .setWidth(800)
    .setHeight(600);

  SpreadsheetApp.getUi().showModalDialog(htmlOutput, 'カイ二乗検定結果');
}

/**
 * ANOVA検定結果の表示
 */
function showANOVATests() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName('ANOVATests');

  if (!sheet) {
    SpreadsheetApp.getUi().alert(
      'エラー',
      'ANOVATestsシートが見つかりません。\n' +
      'Phase 2データをインポートしてください。',
      SpreadsheetApp.getUi().ButtonSet.OK
    );
    return;
  }

  const data = sheet.getDataRange().getValues();

  if (data.length <= 1) {
    SpreadsheetApp.getUi().alert(
      '情報',
      'ANOVA検定のデータがありません。',
      SpreadsheetApp.getUi().ButtonSet.OK
    );
    return;
  }

  // HTMLレポート生成
  let html = `
    <style>
      body { font-family: Arial, sans-serif; padding: 20px; }
      h2 { color: #1a73e8; border-bottom: 2px solid #1a73e8; padding-bottom: 10px; }
      .test-card {
        background: #f8f9fa;
        border-left: 4px solid #34a853;
        padding: 15px;
        margin: 15px 0;
        border-radius: 4px;
      }
      .metric { display: inline-block; margin: 10px 20px 10px 0; }
      .metric-label { font-weight: bold; color: #5f6368; }
      .metric-value { font-size: 1.2em; color: #202124; }
      .significant { color: #ea4335; font-weight: bold; }
      .not-significant { color: #34a853; }
      .interpretation {
        background: #e8f0fe;
        padding: 10px;
        border-radius: 4px;
        margin-top: 10px;
        font-style: italic;
      }
    </style>

    <h2>📊 ANOVA検定結果</h2>
  `;

  // ヘッダー行をスキップ
  for (let i = 1; i < data.length; i++) {
    const row = data[i];
    const pattern = row[0];
    const dependentVar = row[1];
    const independentVar = row[2];
    const fStatistic = row[3];
    const pValue = row[4];
    const dfBetween = row[5];
    const dfWithin = row[6];
    const effectSize = row[7];
    const significant = row[8];
    const interpretation = row[9];

    const significantClass = significant ? 'significant' : 'not-significant';
    const significantText = significant ? '有意' : '有意でない';

    html += `
      <div class="test-card">
        <h3>${pattern}</h3>
        <div class="metric">
          <span class="metric-label">F統計量:</span>
          <span class="metric-value">${fStatistic.toFixed(4)}</span>
        </div>
        <div class="metric">
          <span class="metric-label">p値:</span>
          <span class="metric-value ${significantClass}">${pValue.toFixed(4)}</span>
        </div>
        <div class="metric">
          <span class="metric-label">群間自由度:</span>
          <span class="metric-value">${dfBetween}</span>
        </div>
        <div class="metric">
          <span class="metric-label">群内自由度:</span>
          <span class="metric-value">${dfWithin}</span>
        </div>
        <div class="metric">
          <span class="metric-label">効果量:</span>
          <span class="metric-value">${effectSize.toFixed(4)}</span>
        </div>
        <div class="metric">
          <span class="metric-label">有意性:</span>
          <span class="metric-value ${significantClass}">${significantText}</span>
        </div>
        <div class="interpretation">
          💡 解釈: ${interpretation}
        </div>
      </div>
    `;
  }

  const htmlOutput = HtmlService.createHtmlOutput(html)
    .setWidth(800)
    .setHeight(600);

  SpreadsheetApp.getUi().showModalDialog(htmlOutput, 'ANOVA検定結果');
}

/**
 * ペルソナサマリーの表示
 */
function showPersonaSummary() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName('PersonaSummary');

  if (!sheet) {
    SpreadsheetApp.getUi().alert(
      'エラー',
      'PersonaSummaryシートが見つかりません。\n' +
      'Phase 3データをインポートしてください。',
      SpreadsheetApp.getUi().ButtonSet.OK
    );
    return;
  }

  const data = sheet.getDataRange().getValues();

  if (data.length <= 1) {
    SpreadsheetApp.getUi().alert(
      '情報',
      'ペルソナサマリーのデータがありません。',
      SpreadsheetApp.getUi().ButtonSet.OK
    );
    return;
  }

  // HTMLレポート生成
  let html = `
    <style>
      body { font-family: Arial, sans-serif; padding: 20px; }
      h2 { color: #1a73e8; border-bottom: 2px solid #1a73e8; padding-bottom: 10px; }
      .persona-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        margin: 15px 0;
        border-radius: 8px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
      }
      .persona-name { font-size: 1.5em; font-weight: bold; margin-bottom: 10px; }
      .persona-stats {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 10px;
        margin-top: 15px;
      }
      .stat-item {
        background: rgba(255,255,255,0.2);
        padding: 10px;
        border-radius: 4px;
      }
      .stat-label { font-size: 0.9em; opacity: 0.9; }
      .stat-value { font-size: 1.3em; font-weight: bold; margin-top: 5px; }
    </style>

    <h2>👥 ペルソナサマリー</h2>
  `;

  // ヘッダー行をスキップ
  for (let i = 1; i < data.length; i++) {
    const row = data[i];
    const segmentId = row[0];
    const segmentName = row[1];
    const count = row[2];
    const percentage = row[3];
    const avgAge = row[4];
    const femaleRatio = row[5];
    const avgQualifications = row[6];
    const avgDesiredLocations = row[7];

    html += `
      <div class="persona-card">
        <div class="persona-name">🎭 ${segmentName}</div>
        <div class="persona-stats">
          <div class="stat-item">
            <div class="stat-label">人数</div>
            <div class="stat-value">${count}人 (${percentage.toFixed(1)}%)</div>
          </div>
          <div class="stat-item">
            <div class="stat-label">平均年齢</div>
            <div class="stat-value">${avgAge.toFixed(1)}歳</div>
          </div>
          <div class="stat-item">
            <div class="stat-label">女性比率</div>
            <div class="stat-value">${(femaleRatio * 100).toFixed(1)}%</div>
          </div>
          <div class="stat-item">
            <div class="stat-label">平均資格数</div>
            <div class="stat-value">${avgQualifications.toFixed(1)}個</div>
          </div>
          <div class="stat-item">
            <div class="stat-label">平均希望勤務地数</div>
            <div class="stat-value">${avgDesiredLocations.toFixed(1)}箇所</div>
          </div>
        </div>
      </div>
    `;
  }

  const htmlOutput = HtmlService.createHtmlOutput(html)
    .setWidth(800)
    .setHeight(600);

  SpreadsheetApp.getUi().showModalDialog(htmlOutput, 'ペルソナサマリー');
}

/**
 * ペルソナ詳細の表示
 */
function showPersonaDetails() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName('PersonaDetails');

  if (!sheet) {
    SpreadsheetApp.getUi().alert(
      'エラー',
      'PersonaDetailsシートが見つかりません。\n' +
      'Phase 3データをインポートしてください。',
      SpreadsheetApp.getUi().ButtonSet.OK
    );
    return;
  }

  const data = sheet.getDataRange().getValues();

  if (data.length <= 1) {
    SpreadsheetApp.getUi().alert(
      '情報',
      'ペルソナ詳細のデータがありません。',
      SpreadsheetApp.getUi().ButtonSet.OK
    );
    return;
  }

  // データをペルソナごとにグループ化
  const personaMap = {};

  for (let i = 1; i < data.length; i++) {
    const row = data[i];
    const segmentId = row[0];
    const segmentName = row[1];
    const detailType = row[2];
    const detailKey = row[3];
    const detailValue = row[4];

    if (!personaMap[segmentId]) {
      personaMap[segmentId] = {
        name: segmentName,
        details: []
      };
    }

    personaMap[segmentId].details.push({
      type: detailType,
      key: detailKey,
      value: detailValue
    });
  }

  // HTMLレポート生成
  let html = `
    <style>
      body { font-family: Arial, sans-serif; padding: 20px; }
      h2 { color: #1a73e8; border-bottom: 2px solid #1a73e8; padding-bottom: 10px; }
      .persona-section {
        background: #f8f9fa;
        padding: 20px;
        margin: 15px 0;
        border-radius: 8px;
        border-left: 4px solid #fbbc04;
      }
      .persona-name { font-size: 1.3em; font-weight: bold; color: #202124; margin-bottom: 15px; }
      .detail-table {
        width: 100%;
        border-collapse: collapse;
        margin-top: 10px;
      }
      .detail-table th {
        background: #e8eaed;
        padding: 10px;
        text-align: left;
        font-weight: bold;
        border-bottom: 2px solid #dadce0;
      }
      .detail-table td {
        padding: 8px 10px;
        border-bottom: 1px solid #e8eaed;
      }
      .detail-type { color: #5f6368; font-size: 0.9em; }
    </style>

    <h2>📋 ペルソナ詳細</h2>
  `;

  // ペルソナごとに表示
  Object.keys(personaMap).sort().forEach(segmentId => {
    const persona = personaMap[segmentId];

    html += `
      <div class="persona-section">
        <div class="persona-name">🎭 ${persona.name}</div>
        <table class="detail-table">
          <thead>
            <tr>
              <th>特徴タイプ</th>
              <th>項目</th>
              <th>値</th>
            </tr>
          </thead>
          <tbody>
    `;

    persona.details.forEach(detail => {
      html += `
        <tr>
          <td class="detail-type">${detail.type}</td>
          <td>${detail.key}</td>
          <td><strong>${detail.value}</strong></td>
        </tr>
      `;
    });

    html += `
          </tbody>
        </table>
      </div>
    `;
  });

  const htmlOutput = HtmlService.createHtmlOutput(html)
    .setWidth(900)
    .setHeight(700);

  SpreadsheetApp.getUi().showModalDialog(htmlOutput, 'ペルソナ詳細');
}


// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 3. 自治体間フロー分析
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

/**
 * MunicipalityFlowネットワーク図表示
 */
function showMunicipalityFlowNetworkVisualization() {
  const ui = SpreadsheetApp.getUi();

  try {
    // データ読み込み
    const flowData = loadMunicipalityFlowData();

    if (!flowData.edges || flowData.edges.length === 0) {
      ui.alert(
        'データなし',
        'MunicipalityFlowEdgesシートにデータがありません。\n' +
        '先に「Phase 6データ取り込み」を実行してください。',
        ui.ButtonSet.OK
      );
      return;
    }

    // HTML生成
    const html = generateMunicipalityFlowNetworkHTML(flowData);

    // 全画面表示
    const htmlOutput = HtmlService.createHtmlOutput(html)
      .setWidth(1600)
      .setHeight(950);

    ui.showModalDialog(htmlOutput, 'Phase 6: 自治体間フローネットワーク図（6,862エッジ）');

  } catch (error) {
    ui.alert('エラー', `ネットワーク図可視化中にエラーが発生しました:\n\n${error.message}`, ui.ButtonSet.OK);
    Logger.log(`MunicipalityFlowNetwork可視化エラー: ${error.stack}`);
  }
}

/**
 * MunicipalityFlowデータ読み込み
 *
 * エッジとノードの両方を読み込み、ネットワークデータを構築
 */
function loadMunicipalityFlowData() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();

  // エッジデータ読み込み
  const edgesSheet = ss.getSheetByName('Phase6_MunicipalityFlowEdges');
  if (!edgesSheet) {
    throw new Error('Phase6_MunicipalityFlowEdgesシートが見つかりません');
  }

  const edgesLastRow = edgesSheet.getLastRow();
  if (edgesLastRow <= 1) {
    return { edges: [], nodes: [] };
  }

  // エッジデータ取得（Source, Target, Flow_Count）
  const edgesData = edgesSheet.getRange(2, 1, edgesLastRow - 1, 3).getValues();

  const edges = edgesData.map((row, idx) => ({
    id: idx,
    source: row[0],
    target: row[1],
    flow: parseInt(row[2]) || 0
  }));

  // ノードデータ読み込み（存在する場合）
  const nodesSheet = ss.getSheetByName('Phase6_MunicipalityFlowNodes');
  let nodes = [];

  if (nodesSheet) {
    const nodesLastRow = nodesSheet.getLastRow();
    if (nodesLastRow > 1) {
      // ノードデータ取得（Municipality, TotalInflow, TotalOutflow, NetFlow, FlowCount, Centrality, Prefecture）
      const nodesData = nodesSheet.getRange(2, 1, nodesLastRow - 1, 7).getValues();

      nodes = nodesData.map(row => ({
        id: row[0],
        totalInflow: parseInt(row[1]) || 0,
        totalOutflow: parseInt(row[2]) || 0,
        netFlow: parseInt(row[3]) || 0,
        flowCount: parseInt(row[4]) || 0,
        centrality: parseFloat(row[5]) || 0,
        prefecture: row[6]
      }));
    }
  }

  // ノードデータがない場合、エッジから自動生成
  if (nodes.length === 0) {
    const municipalitySet = new Set();
    edges.forEach(edge => {
      municipalitySet.add(edge.source);
      municipalitySet.add(edge.target);
    });

    nodes = Array.from(municipalitySet).map(municipality => ({
      id: municipality,
      totalInflow: 0,
      totalOutflow: 0,
      netFlow: 0,
      flowCount: 0,
      centrality: 0,
      prefecture: extractPrefecture(municipality)
    }));

    // フロー統計計算
    edges.forEach(edge => {
      const sourceNode = nodes.find(n => n.id === edge.source);
      const targetNode = nodes.find(n => n.id === edge.target);

      if (sourceNode) {
        sourceNode.totalOutflow += edge.flow;
        sourceNode.flowCount++;
      }

      if (targetNode) {
        targetNode.totalInflow += edge.flow;
      }
    });

    // NetFlow計算
    nodes.forEach(node => {
      node.netFlow = node.totalInflow - node.totalOutflow;
    });
  }

  return { edges, nodes };
}

/**
 * 市区町村名から都道府県を抽出
 *
 * @param {string} municipality - 市区町村名（例: "京都府京都市伏見区"）
 * @return {string} 都道府県名（例: "京都府"）
 */
function extractPrefecture(municipality) {
  const match = municipality.match(/^(.{2,3}[都道府県])/);
  return match ? match[1] : '不明';
}

/**
 * MunicipalityFlowネットワーク図HTML生成
 *
 * D3.jsを使用した力学モデルネットワーク図
 */
function generateMunicipalityFlowNetworkHTML(flowData) {
  const edgesJson = JSON.stringify(flowData.edges);
  const nodesJson = JSON.stringify(flowData.nodes);

  return `
<!DOCTYPE html>
<html>
<head>
  <base target="_top">
  <meta charset="UTF-8">
  <title>自治体間フローネットワーク図</title>
  <script src="https://d3js.org/d3.v7.min.js"></script>
  <style>
    * {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }

    body {
      font-family: 'Segoe UI', Arial, sans-serif;
      background-color: #f5f7fa;
    }

    .header {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      padding: 20px 30px;
      box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }

    .header h1 {
      font-size: 24px;
      font-weight: 600;
      margin-bottom: 8px;
    }

    .header p {
      font-size: 14px;
      opacity: 0.9;
    }

    .controls {
      background: white;
      padding: 15px 30px;
      box-shadow: 0 2px 5px rgba(0,0,0,0.05);
      display: flex;
      align-items: center;
      gap: 20px;
      flex-wrap: wrap;
    }

    .control-group {
      display: flex;
      align-items: center;
      gap: 10px;
    }

    .control-group label {
      font-size: 14px;
      font-weight: 500;
      color: #4a5568;
    }

    .control-group select,
    .control-group input[type="number"] {
      padding: 8px 12px;
      border: 1px solid #cbd5e0;
      border-radius: 6px;
      font-size: 14px;
      min-width: 120px;
    }

    .control-group button {
      padding: 8px 16px;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      border: none;
      border-radius: 6px;
      font-size: 14px;
      font-weight: 500;
      cursor: pointer;
      transition: transform 0.2s;
    }

    .control-group button:hover {
      transform: translateY(-1px);
    }

    .main-content {
      display: flex;
      height: calc(100vh - 140px);
    }

    .network-container {
      flex: 1;
      background: white;
      margin: 15px;
      border-radius: 8px;
      box-shadow: 0 2px 10px rgba(0,0,0,0.05);
      overflow: hidden;
      position: relative;
    }

    #network-svg {
      width: 100%;
      height: 100%;
    }

    .sidebar {
      width: 320px;
      background: white;
      margin: 15px 15px 15px 0;
      border-radius: 8px;
      box-shadow: 0 2px 10px rgba(0,0,0,0.05);
      padding: 20px;
      overflow-y: auto;
    }

    .sidebar h3 {
      font-size: 18px;
      font-weight: 600;
      color: #2d3748;
      margin-bottom: 15px;
      padding-bottom: 10px;
      border-bottom: 2px solid #e2e8f0;
    }

    .stat-item {
      display: flex;
      justify-content: space-between;
      padding: 10px 0;
      border-bottom: 1px solid #f1f5f9;
    }

    .stat-item:last-child {
      border-bottom: none;
    }

    .stat-label {
      font-size: 14px;
      color: #64748b;
    }

    .stat-value {
      font-size: 14px;
      font-weight: 600;
      color: #1e293b;
    }

    .node-detail {
      background: #f8fafc;
      padding: 15px;
      border-radius: 6px;
      margin-top: 15px;
    }

    .node-detail h4 {
      font-size: 16px;
      font-weight: 600;
      color: #667eea;
      margin-bottom: 10px;
    }

    .node-detail p {
      font-size: 13px;
      color: #475569;
      margin: 5px 0;
    }

    /* D3.js ネットワーク図スタイル */
    .link {
      stroke: #94a3b8;
      stroke-opacity: 0.6;
      fill: none;
    }

    .link-arrow {
      fill: #94a3b8;
      opacity: 0.6;
    }

    .node circle {
      cursor: pointer;
      stroke: white;
      stroke-width: 2px;
    }

    .node text {
      font-size: 11px;
      pointer-events: none;
      text-anchor: middle;
      dominant-baseline: central;
      fill: #334155;
      font-weight: 500;
    }

    .node:hover circle {
      stroke: #667eea;
      stroke-width: 3px;
    }

    .tooltip {
      position: absolute;
      background: rgba(0, 0, 0, 0.85);
      color: white;
      padding: 10px 15px;
      border-radius: 6px;
      font-size: 13px;
      pointer-events: none;
      z-index: 1000;
      display: none;
      max-width: 250px;
      line-height: 1.5;
    }

    .legend {
      position: absolute;
      top: 20px;
      right: 20px;
      background: white;
      padding: 15px;
      border-radius: 8px;
      box-shadow: 0 2px 10px rgba(0,0,0,0.1);
      font-size: 12px;
    }

    .legend h4 {
      font-size: 14px;
      font-weight: 600;
      margin-bottom: 10px;
      color: #2d3748;
    }

    .legend-item {
      display: flex;
      align-items: center;
      gap: 8px;
      margin: 8px 0;
    }

    .legend-color {
      width: 16px;
      height: 16px;
      border-radius: 50%;
    }
  </style>
</head>
<body>
  <div class="header">
    <h1>自治体間フローネットワーク図</h1>
    <p>Phase 6: ${flowData.edges.length.toLocaleString()}エッジ × ${flowData.nodes.length.toLocaleString()}ノード | 人材フロー可視化</p>
  </div>

  <div class="controls">
    <div class="control-group">
      <label>表示エッジ数:</label>
      <select id="edge-limit" onchange="updateVisualization()">
        <option value="50">TOP 50</option>
        <option value="100" selected>TOP 100</option>
        <option value="200">TOP 200</option>
        <option value="500">TOP 500</option>
        <option value="1000">TOP 1000</option>
        <option value="all">全表示</option>
      </select>
    </div>

    <div class="control-group">
      <label>最小フロー人数:</label>
      <input type="number" id="min-flow" value="50" min="1" max="1000" onchange="updateVisualization()">
    </div>

    <div class="control-group">
      <button onclick="resetZoom()">ズームリセット</button>
    </div>

    <div class="control-group">
      <button onclick="exportData()">データ出力</button>
    </div>
  </div>

  <div class="main-content">
    <div class="network-container">
      <svg id="network-svg"></svg>
      <div class="tooltip" id="tooltip"></div>

      <div class="legend">
        <h4>凡例</h4>
        <div class="legend-item">
          <div class="legend-color" style="background: #667eea;"></div>
          <span>ノード（自治体）</span>
        </div>
        <div class="legend-item">
          <div style="width: 16px; height: 2px; background: #94a3b8;"></div>
          <span>フロー（太さ=人数）</span>
        </div>
        <p style="margin-top: 10px; color: #64748b; font-size: 11px;">
          ノードサイズ = 総フロー量<br>
          ドラッグで移動可能<br>
          ホバーで詳細表示
        </p>
      </div>
    </div>

    <div class="sidebar">
      <h3>統計サマリー</h3>
      <div class="stat-item">
        <span class="stat-label">総自治体数</span>
        <span class="stat-value" id="total-nodes">${flowData.nodes.length.toLocaleString()}</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">総フロー数</span>
        <span class="stat-value" id="total-edges">${flowData.edges.length.toLocaleString()}</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">表示中ノード</span>
        <span class="stat-value" id="visible-nodes">-</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">表示中エッジ</span>
        <span class="stat-value" id="visible-edges">-</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">総フロー人数</span>
        <span class="stat-value" id="total-flow">-</span>
      </div>

      <div id="node-detail-container"></div>
    </div>
  </div>

  <script>
    // グローバルデータ
    const allEdges = ${edgesJson};
    const allNodes = ${nodesJson};

    let svg, g, simulation;
    let currentNodes = [];
    let currentEdges = [];

    // 初期化
    function init() {
      // SVG設定
      const container = document.querySelector('.network-container');
      svg = d3.select('#network-svg');

      // ズーム設定
      const zoom = d3.zoom()
        .scaleExtent([0.1, 4])
        .on('zoom', (event) => {
          g.attr('transform', event.transform);
        });

      svg.call(zoom);

      // グループ作成
      g = svg.append('g');

      // 初回可視化
      updateVisualization();
    }

    // 可視化更新
    function updateVisualization() {
      const edgeLimitValue = document.getElementById('edge-limit').value;
      const minFlow = parseInt(document.getElementById('min-flow').value) || 1;

      // エッジフィルタリング
      let filteredEdges = allEdges.filter(e => e.flow >= minFlow);

      // TOP N選択
      if (edgeLimitValue !== 'all') {
        const limit = parseInt(edgeLimitValue);
        filteredEdges = filteredEdges
          .sort((a, b) => b.flow - a.flow)
          .slice(0, limit);
      } else {
        filteredEdges = filteredEdges.sort((a, b) => b.flow - a.flow);
      }

      // フィルタリングされたエッジに含まれるノードのみ抽出
      const nodeSet = new Set();
      filteredEdges.forEach(edge => {
        nodeSet.add(edge.source);
        nodeSet.add(edge.target);
      });

      const filteredNodes = allNodes.filter(node => nodeSet.has(node.id));

      // データ更新
      currentNodes = filteredNodes;
      currentEdges = filteredEdges;

      // 統計更新
      updateStatistics();

      // グラフ描画
      drawNetwork();
    }

    // ネットワーク描画
    function drawNetwork() {
      // 既存要素削除
      g.selectAll('*').remove();

      // シミュレーション初期化
      const width = document.querySelector('.network-container').clientWidth;
      const height = document.querySelector('.network-container').clientHeight;

      simulation = d3.forceSimulation(currentNodes)
        .force('link', d3.forceLink(currentEdges).id(d => d.id).distance(100))
        .force('charge', d3.forceManyBody().strength(-300))
        .force('center', d3.forceCenter(width / 2, height / 2))
        .force('collision', d3.forceCollide().radius(d => getNodeRadius(d) + 5));

      // エッジ描画
      const link = g.append('g')
        .selectAll('line')
        .data(currentEdges)
        .join('line')
        .attr('class', 'link')
        .attr('stroke-width', d => Math.sqrt(d.flow) * 0.5);

      // ノード描画
      const node = g.append('g')
        .selectAll('g')
        .data(currentNodes)
        .join('g')
        .attr('class', 'node')
        .call(d3.drag()
          .on('start', dragStarted)
          .on('drag', dragged)
          .on('end', dragEnded));

      node.append('circle')
        .attr('r', d => getNodeRadius(d))
        .attr('fill', d => getNodeColor(d))
        .on('mouseover', showNodeTooltip)
        .on('mouseout', hideTooltip)
        .on('click', showNodeDetail);

      node.append('text')
        .text(d => d.id.split(/[都道府県]/)[1] || d.id)
        .attr('dy', d => getNodeRadius(d) + 15);

      // シミュレーション更新
      simulation.on('tick', () => {
        link
          .attr('x1', d => d.source.x)
          .attr('y1', d => d.source.y)
          .attr('x2', d => d.target.x)
          .attr('y2', d => d.target.y);

        node.attr('transform', d => \`translate(\${d.x},\${d.y})\`);
      });
    }

    // ノード半径計算
    function getNodeRadius(node) {
      const totalFlow = node.totalInflow + node.totalOutflow;
      return Math.sqrt(totalFlow) * 0.3 + 5;
    }

    // ノード色計算
    function getNodeColor(node) {
      // NetFlowに基づく色分け
      if (node.netFlow > 100) return '#10b981'; // 流入超過（緑）
      if (node.netFlow < -100) return '#ef4444'; // 流出超過（赤）
      return '#667eea'; // ニュートラル（紫）
    }

    // ツールチップ表示
    function showNodeTooltip(event, d) {
      const tooltip = document.getElementById('tooltip');
      tooltip.style.display = 'block';
      tooltip.style.left = (event.pageX + 10) + 'px';
      tooltip.style.top = (event.pageY - 10) + 'px';
      tooltip.innerHTML = \`
        <strong>\${d.id}</strong><br>
        総流入: \${d.totalInflow.toLocaleString()}名<br>
        総流出: \${d.totalOutflow.toLocaleString()}名<br>
        純フロー: \${d.netFlow > 0 ? '+' : ''}\${d.netFlow.toLocaleString()}名
      \`;
    }

    // ツールチップ非表示
    function hideTooltip() {
      document.getElementById('tooltip').style.display = 'none';
    }

    // ノード詳細表示
    function showNodeDetail(event, d) {
      const container = document.getElementById('node-detail-container');
      container.innerHTML = \`
        <div class="node-detail">
          <h4>\${d.id}</h4>
          <p><strong>都道府県:</strong> \${d.prefecture}</p>
          <p><strong>総流入:</strong> \${d.totalInflow.toLocaleString()}名</p>
          <p><strong>総流出:</strong> \${d.totalOutflow.toLocaleString()}名</p>
          <p><strong>純フロー:</strong> \${d.netFlow > 0 ? '+' : ''}\${d.netFlow.toLocaleString()}名</p>
          <p><strong>フロー数:</strong> \${d.flowCount}件</p>
          <p style="margin-top: 10px; color: \${d.netFlow > 0 ? '#10b981' : '#ef4444'};">
            \${d.netFlow > 0 ? '流入超過地域' : d.netFlow < 0 ? '流出超過地域' : 'バランス地域'}
          </p>
        </div>
      \`;
    }

    // ドラッグイベント
    function dragStarted(event, d) {
      if (!event.active) simulation.alphaTarget(0.3).restart();
      d.fx = d.x;
      d.fy = d.y;
    }

    function dragged(event, d) {
      d.fx = event.x;
      d.fy = event.y;
    }

    function dragEnded(event, d) {
      if (!event.active) simulation.alphaTarget(0);
      d.fx = null;
      d.fy = null;
    }

    // 統計更新
    function updateStatistics() {
      document.getElementById('visible-nodes').textContent = currentNodes.length.toLocaleString();
      document.getElementById('visible-edges').textContent = currentEdges.length.toLocaleString();

      const totalFlow = currentEdges.reduce((sum, e) => sum + e.flow, 0);
      document.getElementById('total-flow').textContent = totalFlow.toLocaleString() + '名';
    }

    // ズームリセット
    function resetZoom() {
      svg.transition().duration(750).call(
        d3.zoom().transform,
        d3.zoomIdentity
      );
    }

    // データ出力
    function exportData() {
      let csv = 'Source,Target,Flow\\n';
      currentEdges.forEach(edge => {
        csv += \`\${edge.source.id || edge.source},\${edge.target.id || edge.target},\${edge.flow}\\n\`;
      });

      const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
      const link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      link.download = \`MunicipalityFlow_\${new Date().toISOString().split('T')[0]}.csv\`;
      link.click();
    }

    // 初期化実行
    window.onload = init;

    // リサイズ対応
    window.addEventListener('resize', () => {
      if (simulation) {
        const width = document.querySelector('.network-container').clientWidth;
        const height = document.querySelector('.network-container').clientHeight;
        simulation.force('center', d3.forceCenter(width / 2, height / 2));
        simulation.alpha(0.3).restart();
      }
    });
  </script>
</body>
</html>
  `;
}


// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 4. ペルソナマップデータ可視化
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

/**
 * PersonaMapData地図可視化（メインエントリーポイント）
 */
function showPersonaMapVisualization() {
  const ui = SpreadsheetApp.getUi();

  try {
    // Step 1: データ読み込み
    const mapData = loadPersonaMapData();

    if (!mapData || mapData.length === 0) {
      ui.alert(
        'データなし',
        'Phase7_PersonaMapDataシートにデータがありません。\n\n' +
        '【対処方法】\n' +
        '1. スプレッドシートメニュー > 「📊 データ処理」\n' +
        '2. 「🐍 Python連携」 > 「📥 Python結果CSVを取り込み」\n' +
        '3. gas_output_phase7フォルダを指定してインポート',
        ui.ButtonSet.OK
      );
      return;
    }

    // Step 2: HTML生成（セキュアAPIキー取得）
    const html = generatePersonaMapHTML(mapData);

    // Step 3: 全画面モーダルダイアログ表示
    const htmlOutput = HtmlService.createHtmlOutput(html)
      .setWidth(1400)
      .setHeight(900);

    ui.showModalDialog(htmlOutput, 'ペルソナ地図可視化（792地点）');

  } catch (error) {
    ui.alert(
      'エラー',
      `地図可視化中にエラーが発生しました:\n\n${error.message}\n\n` +
      `スタックトレース:\n${error.stack}`,
      ui.ButtonSet.OK
    );
    Logger.log(`[ERROR] PersonaMap可視化エラー: ${error.stack}`);
  }
}

/**
 * PersonaMapData読み込み
 *
 * @return {Array<Object>} 地図データ配列（792要素）
 * @throws {Error} シートが見つからない場合
 */
function loadPersonaMapData() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName('Phase7_PersonaMapData');

  if (!sheet) {
    throw new Error(
      'Phase7_PersonaMapDataシートが見つかりません。\n' +
      'Pythonスクリプト実行後、「Phase 7データ取り込み」を実行してください。'
    );
  }

  const lastRow = sheet.getLastRow();
  Logger.log(`[INFO] PersonaMapData行数: ${lastRow - 1}行（ヘッダー除く）`);

  if (lastRow <= 1) {
    Logger.log('[WARNING] PersonaMapData: データが0行です');
    return [];
  }

  // 9列すべて取得: 市区町村, 緯度, 経度, ペルソナID, ペルソナ名, 求職者数, 平均年齢, 女性比率, 資格保有率
  const data = sheet.getRange(2, 1, lastRow - 1, 9).getValues();

  // データ変換 & 座標検証
  const validData = [];
  let invalidCount = 0;

  data.forEach((row, index) => {
    const lat = parseFloat(row[1]);
    const lng = parseFloat(row[2]);

    // 座標検証
    if (isNaN(lat) || isNaN(lng) || lat === 0 || lng === 0) {
      Logger.log(`[WARNING] 行${index + 2}: 無効な座標 (lat=${row[1]}, lng=${row[2]})`);
      invalidCount++;
      return;  // スキップ
    }

    validData.push({
      municipality: row[0],
      lat: lat,
      lng: lng,
      personaId: parseInt(row[3]),
      personaName: row[4],
      applicantCount: parseInt(row[5]),
      avgAge: parseFloat(row[6]),
      femaleRatio: parseFloat(row[7]),
      qualificationRate: parseFloat(row[8])
    });
  });

  if (invalidCount > 0) {
    Logger.log(`[INFO] スキップされた無効データ: ${invalidCount}件`);
  }

  Logger.log(`[OK] 有効なPersonaMapDataロード完了: ${validData.length}地点`);

  return validData;
}

/**
 * 地図HTML生成（セキュア実装）
 *
 * @param {Array<Object>} mapData - 地図データ
 * @return {string} HTML文字列
 */
function generatePersonaMapHTML(mapData) {
  const mapDataJson = JSON.stringify(mapData);

  // ペルソナ別色定義（10色 + グレー）
  const personaColors = {
    '-1': '#808080',  // セグメント-1: グレー
    '0': '#4285F4',   // セグメント0: 青
    '1': '#34A853',   // セグメント1: 緑
    '2': '#FBBC04',   // セグメント2: 黄
    '3': '#EA4335',   // セグメント3: 赤
    '4': '#9C27B0',   // セグメント4: 紫
    '5': '#FF6D00',   // セグメント5: オレンジ
    '6': '#00BCD4',   // セグメント6: シアン
    '7': '#8BC34A',   // セグメント7: ライムグリーン
    '8': '#E91E63',   // セグメント8: ピンク
    '9': '#795548'    // セグメント9: ブラウン
  };

  const personaColorsJson = JSON.stringify(personaColors);

  // 🔒 セキュアAPIキー取得（GoogleMapsAPIConfig.gs使用）
  const apiKeyScript = generateGoogleMapsScriptTag(['visualization']);

  return `
<!DOCTYPE html>
<html>
<head>
  <base target="_top">
  ${apiKeyScript}
  <script src="https://unpkg.com/@googlemaps/markerclusterer/dist/index.min.js"></script>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: 'Segoe UI', Arial, sans-serif; }

    #map { height: 100vh; width: 100%; }

    .controls {
      position: absolute;
      top: 20px;
      left: 20px;
      background: white;
      padding: 20px;
      border-radius: 12px;
      box-shadow: 0 4px 12px rgba(0,0,0,0.2);
      max-width: 350px;
      z-index: 1000;
      max-height: 80vh;
      overflow-y: auto;
    }

    .controls h3 {
      margin-bottom: 15px;
      color: #1a73e8;
      font-size: 18px;
      display: flex;
      align-items: center;
    }

    .controls h3::before {
      content: '🔍';
      margin-right: 8px;
    }

    .persona-filter {
      margin-bottom: 10px;
    }

    .persona-filter label {
      display: flex;
      align-items: center;
      padding: 8px 0;
      cursor: pointer;
      transition: background 0.2s;
      border-radius: 4px;
      padding-left: 5px;
    }

    .persona-filter label:hover {
      background: #f5f5f5;
    }

    .persona-filter input[type="checkbox"] {
      margin-right: 10px;
      cursor: pointer;
    }

    .color-box {
      width: 20px;
      height: 20px;
      display: inline-block;
      margin-right: 10px;
      border-radius: 4px;
      border: 2px solid #ddd;
    }

    .stats {
      margin-top: 20px;
      padding-top: 15px;
      border-top: 2px solid #e0e0e0;
    }

    .stats p {
      margin: 5px 0;
      font-size: 14px;
      color: #555;
    }

    .stats strong {
      color: #1a73e8;
      font-weight: 600;
    }

    .info-window {
      max-width: 300px;
      font-family: 'Segoe UI', Arial, sans-serif;
    }

    .info-window h4 {
      margin-bottom: 12px;
      color: #1a73e8;
      font-size: 16px;
      border-bottom: 2px solid #1a73e8;
      padding-bottom: 5px;
    }

    .info-window p {
      margin: 8px 0;
      font-size: 14px;
      line-height: 1.5;
    }

    .info-window .metric {
      display: flex;
      justify-content: space-between;
      padding: 4px 0;
    }

    .info-window .metric-label {
      color: #666;
    }

    .info-window .metric-value {
      font-weight: 600;
      color: #333;
    }
  </style>
</head>
<body>
  <div id="map"></div>

  <div class="controls">
    <h3>フィルター</h3>
    <div id="persona-filters"></div>
    <div class="stats">
      <p><strong>表示中:</strong> <span id="visible-count">0</span> / <span id="total-count">0</span> 地点</p>
      <p><strong>総求職者:</strong> <span id="total-applicants">0</span> 名</p>
    </div>
  </div>

  <script>
    const mapData = ${mapDataJson};
    const personaColors = ${personaColorsJson};

    let map;
    let markers = [];
    let markerClusterer;

    /**
     * Google Maps初期化
     */
    function initMap() {
      console.log('[INFO] Google Maps初期化開始');
      console.log('[INFO] データ地点数:', mapData.length);

      // 地図中心計算（全マーカーの平均座標）
      const avgLat = mapData.reduce((sum, d) => sum + d.lat, 0) / mapData.length;
      const avgLng = mapData.reduce((sum, d) => sum + d.lng, 0) / mapData.length;

      const center = { lat: avgLat, lng: avgLng };

      console.log('[INFO] 地図中心:', center);

      // 地図作成
      map = new google.maps.Map(document.getElementById('map'), {
        zoom: 9,
        center: center,
        mapTypeId: 'roadmap',
        mapTypeControl: true,
        streetViewControl: true,
        fullscreenControl: true
      });

      // フィルターUI作成
      createPersonaFilters();

      // マーカー作成
      createMarkers();

      // クラスタリング適用
      applyMarkerClustering();

      // 統計表示
      updateStats();

      console.log('[OK] Google Maps初期化完了');
    }

    /**
     * ペルソナフィルターUI作成
     */
    function createPersonaFilters() {
      const container = document.getElementById('persona-filters');

      // ユニークなペルソナIDを取得
      const personaIds = [...new Set(mapData.map(d => d.personaId))].sort((a, b) => a - b);

      console.log('[INFO] ユニークペルソナ数:', personaIds.length);

      personaIds.forEach(personaId => {
        const color = personaColors[personaId.toString()] || '#808080';
        const personaName = mapData.find(d => d.personaId === personaId).personaName;
        const count = mapData.filter(d => d.personaId === personaId).length;

        const label = document.createElement('label');
        label.className = 'persona-filter';
        label.innerHTML = \`
          <input type="checkbox" checked data-persona-id="\${personaId}">
          <span class="color-box" style="background-color: \${color};"></span>
          \${personaName} (\${count})
        \`;

        const checkbox = label.querySelector('input');
        checkbox.addEventListener('change', () => filterMarkers());

        container.appendChild(label);
      });

      console.log('[OK] フィルターUI作成完了');
    }

    /**
     * マーカー作成
     */
    function createMarkers() {
      console.log('[INFO] マーカー作成開始');

      mapData.forEach((data, index) => {
        const color = personaColors[data.personaId.toString()] || '#808080';

        // カスタムマーカーアイコン
        const icon = {
          path: google.maps.SymbolPath.CIRCLE,
          scale: 8,
          fillColor: color,
          fillOpacity: 0.85,
          strokeColor: 'white',
          strokeWeight: 2
        };

        const marker = new google.maps.Marker({
          position: { lat: data.lat, lng: data.lng },
          icon: icon,
          title: \`\${data.municipality} - \${data.personaName}\`,
          personaId: data.personaId
        });

        // 情報ウィンドウ
        const infoWindow = new google.maps.InfoWindow({
          content: generateInfoWindowContent(data)
        });

        marker.addListener('click', () => {
          // 他の情報ウィンドウを閉じる
          markers.forEach(m => {
            if (m.infoWindow) {
              m.infoWindow.close();
            }
          });

          infoWindow.open(map, marker);
        });

        marker.infoWindow = infoWindow;
        markers.push(marker);

        if ((index + 1) % 100 === 0) {
          console.log(\`[PROGRESS] マーカー作成: \${index + 1} / \${mapData.length}\`);
        }
      });

      console.log(\`[OK] マーカー作成完了: \${markers.length}個\`);
    }

    /**
     * 情報ウィンドウ内容生成
     *
     * @param {Object} data - ペルソナデータ
     * @return {string} HTML文字列
     */
    function generateInfoWindowContent(data) {
      const femaleRatioPercent = (data.femaleRatio * 100).toFixed(1);
      const qualificationRatePercent = (data.qualificationRate * 100).toFixed(1);

      return \`
        <div class="info-window">
          <h4>\${data.municipality}</h4>
          <div class="metric">
            <span class="metric-label">ペルソナ:</span>
            <span class="metric-value">\${data.personaName}</span>
          </div>
          <div class="metric">
            <span class="metric-label">求職者数:</span>
            <span class="metric-value">\${data.applicantCount}名</span>
          </div>
          <div class="metric">
            <span class="metric-label">平均年齢:</span>
            <span class="metric-value">\${data.avgAge}歳</span>
          </div>
          <div class="metric">
            <span class="metric-label">女性比率:</span>
            <span class="metric-value">\${femaleRatioPercent}%</span>
          </div>
          <div class="metric">
            <span class="metric-label">資格保有率:</span>
            <span class="metric-value">\${qualificationRatePercent}%</span>
          </div>
        </div>
      \`;
    }

    /**
     * クラスタリング適用
     */
    function applyMarkerClustering() {
      console.log('[INFO] クラスタリング適用開始');

      if (markerClusterer) {
        markerClusterer.clearMarkers();
      }

      const visibleMarkers = markers.filter(m => {
        const checkbox = document.querySelector(\`input[data-persona-id="\${m.personaId}"]\`);
        return checkbox && checkbox.checked;
      });

      console.log(\`[INFO] 表示マーカー数: \${visibleMarkers.length}\`);

      markerClusterer = new markerClusterer.MarkerClusterer({
        map,
        markers: visibleMarkers,
        algorithm: new markerClusterer.GridAlgorithm({ gridSize: 60 })
      });

      console.log('[OK] クラスタリング適用完了');
    }

    /**
     * フィルター適用
     */
    function filterMarkers() {
      console.log('[INFO] フィルター適用');
      applyMarkerClustering();
      updateStats();
    }

    /**
     * 統計更新
     */
    function updateStats() {
      const visibleMarkers = markers.filter(m => {
        const checkbox = document.querySelector(\`input[data-persona-id="\${m.personaId}"]\`);
        return checkbox && checkbox.checked;
      });

      const visibleCount = visibleMarkers.length;

      // 総求職者数計算
      const visibleDataPoints = mapData.filter(d => {
        const checkbox = document.querySelector(\`input[data-persona-id="\${d.personaId}"]\`);
        return checkbox && checkbox.checked;
      });

      const totalApplicants = visibleDataPoints.reduce((sum, d) => sum + d.applicantCount, 0);

      document.getElementById('visible-count').textContent = visibleCount;
      document.getElementById('total-count').textContent = markers.length;
      document.getElementById('total-applicants').textContent = totalApplicants.toLocaleString();

      console.log(\`[STATS] 表示: \${visibleCount} / \${markers.length}, 総求職者: \${totalApplicants}名\`);
    }

    /**
     * エラーハンドリング
     */
    window.onerror = function(message, source, lineno, colno, error) {
      console.error('[ERROR] JavaScript エラー:', message);
      console.error('[ERROR] ファイル:', source);
      console.error('[ERROR] 行番号:', lineno);
      alert('地図の初期化中にエラーが発生しました:\\n' + message);
      return false;
    };

    /**
     * 初期化実行（Google Maps API読み込み後）
     */
    window.onload = function() {
      if (typeof google === 'undefined' || !google.maps) {
        console.error('[ERROR] Google Maps APIの読み込みに失敗しました');
        alert(
          'Google Maps APIの読み込みに失敗しました。\\n\\n' +
          '【対処方法】\\n' +
          '1. インターネット接続を確認\\n' +
          '2. Google Maps APIキーが正しく設定されているか確認\\n' +
          '3. Google Cloud ConsoleでMaps JavaScript APIが有効化されているか確認'
        );
        return;
      }

      if (typeof markerClusterer === 'undefined') {
        console.error('[ERROR] MarkerClustererの読み込みに失敗しました');
        alert('MarkerClustererライブラリの読み込みに失敗しました。');
        return;
      }

      try {
        initMap();
      } catch (error) {
        console.error('[ERROR] 初期化エラー:', error);
        alert('地図の初期化中にエラーが発生しました:\\n' + error.message);
      }
    };
  </script>
</body>
</html>
  `;
}


// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 5. マトリックスヒートマップ
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

// ===== 汎用Matrix読み込み関数 =====

function loadMatrixData(sheetName) {
  /**
   * 指定されたシートからMatrix形式データを読み込む
   *
   * @param {string} sheetName - シート名
   * @return {Object} - {headers: [...], rows: [[...], ...], metadata: {...}}
   */
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getSheetByName(sheetName);

  if (!sheet) {
    throw new Error(sheetName + ' シートが見つかりません');
  }

  var data = sheet.getDataRange().getValues();

  if (data.length < 2) {
    throw new Error('データが不足しています');
  }

  // ヘッダー行とデータ行を分離
  var headers = data[0];
  var rows = data.slice(1);

  // メタデータ抽出
  var metadata = extractMatrixMetadata(headers, rows);

  return {
    headers: headers,
    rows: rows,
    metadata: metadata
  };
}

function extractMatrixMetadata(headers, rows) {
  /**
   * Matrixデータからメタデータを抽出
   *
   * @param {Array} headers - ヘッダー行
   * @param {Array} rows - データ行
   * @return {Object} - メタデータ
   */

  // 数値セルの統計
  var values = [];
  rows.forEach(function(row) {
    row.slice(1).forEach(function(cell) {
      var num = parseFloat(cell);
      if (!isNaN(num) && num > 0) {
        values.push(num);
      }
    });
  });

  values.sort(function(a, b) { return a - b; });

  var sum = values.reduce(function(acc, v) { return acc + v; }, 0);
  var mean = values.length > 0 ? sum / values.length : 0;
  var median = values.length > 0 ? values[Math.floor(values.length / 2)] : 0;
  var min = values.length > 0 ? values[0] : 0;
  var max = values.length > 0 ? values[values.length - 1] : 0;

  return {
    totalCells: rows.length * (headers.length - 1),
    valueCells: values.length,
    emptyCells: (rows.length * (headers.length - 1)) - values.length,
    sum: sum,
    mean: mean,
    median: median,
    min: min,
    max: max
  };
}

// ===== ヒートマップ可視化関数 =====

function showMatrixHeatmap(sheetName, title, colorScheme) {
  /**
   * Matrix形式ヒートマップを表示
   *
   * @param {string} sheetName - シート名
   * @param {string} title - タイトル
   * @param {string} colorScheme - カラースキーム ('blue', 'red', 'green', 'purple')
   */
  try {
    var matrixData = loadMatrixData(sheetName);

    var html = generateMatrixHeatmapHTML(
      matrixData,
      title,
      colorScheme || 'blue'
    );

    SpreadsheetApp.getUi().showModalDialog(
      html,
      title
    );

  } catch (e) {
    SpreadsheetApp.getUi().alert('エラー: ' + e.toString());
  }
}

function generateMatrixHeatmapHTML(matrixData, title, colorScheme) {
  /**
   * ヒートマップHTML生成
   *
   * @param {Object} matrixData - Matrix形式データ
   * @param {string} title - タイトル
   * @param {string} colorScheme - カラースキーム
   * @return {HtmlOutput} - HTML出力
   */

  var colors = getColorScheme(colorScheme);

  var html = HtmlService.createHtmlOutput();
  html.append('<style>');
  html.append('body { font-family: Arial, sans-serif; padding: 20px; background: ' + colors.background + '; }');
  html.append('.container { background: white; border-radius: 12px; padding: 20px; box-shadow: 0 10px 40px rgba(0,0,0,0.1); }');
  html.append('h2 { color: ' + colors.primary + '; margin-top: 0; display: flex; align-items: center; }');
  html.append('h2 .icon { font-size: 32px; margin-right: 10px; }');
  html.append('.stats-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin: 20px 0; }');
  html.append('.stat-card { background: #f8f9fa; border-radius: 8px; padding: 15px; text-align: center; }');
  html.append('.stat-value { font-size: 24px; font-weight: bold; color: ' + colors.primary + '; }');
  html.append('.stat-label { font-size: 12px; color: #666; margin-top: 5px; }');
  html.append('.heatmap-container { margin: 20px 0; overflow: auto; max-height: 500px; }');
  html.append('table { width: 100%; border-collapse: collapse; }');
  html.append('th { background: ' + colors.primary + '; color: white; padding: 12px; text-align: center; position: sticky; top: 0; z-index: 10; }');
  html.append('td { padding: 10px; text-align: center; border: 1px solid #e0e0e0; font-size: 13px; }');
  html.append('.row-header { background: ' + colors.secondary + '; color: white; font-weight: bold; position: sticky; left: 0; z-index: 5; }');
  html.append('.legend { display: flex; align-items: center; justify-content: center; margin: 20px 0; }');
  html.append('.legend-item { margin: 0 10px; display: flex; align-items: center; }');
  html.append('.legend-box { width: 30px; height: 20px; margin-right: 5px; border: 1px solid #ddd; }');
  html.append('</style>');

  html.append('<div class="container">');
  html.append('<h2><span class="icon">🔥</span>' + title + '</h2>');

  // 統計サマリー
  var meta = matrixData.metadata;
  html.append('<div class="stats-grid">');
  html.append('<div class="stat-card"><div class="stat-value">' + meta.max.toFixed(0) + '</div><div class="stat-label">最大値</div></div>');
  html.append('<div class="stat-card"><div class="stat-value">' + meta.mean.toFixed(1) + '</div><div class="stat-label">平均値</div></div>');
  html.append('<div class="stat-card"><div class="stat-value">' + meta.median.toFixed(1) + '</div><div class="stat-label">中央値</div></div>');
  html.append('<div class="stat-card"><div class="stat-value">' + meta.valueCells + '</div><div class="stat-label">有効セル数</div></div>');
  html.append('</div>');

  // カラーレジェンド
  html.append('<div class="legend">');
  html.append('<div class="legend-item"><div class="legend-box" style="background: #ffffff;"></div><span>0</span></div>');
  html.append('<div class="legend-item"><div class="legend-box" style="background: ' + colors.gradient[0] + ';"></div><span>低</span></div>');
  html.append('<div class="legend-item"><div class="legend-box" style="background: ' + colors.gradient[1] + ';"></div><span>中</span></div>');
  html.append('<div class="legend-item"><div class="legend-box" style="background: ' + colors.gradient[2] + ';"></div><span>高</span></div>');
  html.append('</div>');

  // ヒートマップテーブル
  html.append('<div class="heatmap-container">');
  html.append('<table>');

  // ヘッダー行
  html.append('<tr>');
  matrixData.headers.forEach(function(header) {
    html.append('<th>' + header + '</th>');
  });
  html.append('</tr>');

  // データ行（色付け）
  var maxValue = meta.max;
  matrixData.rows.forEach(function(row) {
    html.append('<tr>');
    row.forEach(function(cell, index) {
      if (index === 0) {
        // 行ラベル
        html.append('<td class="row-header">' + cell + '</td>');
      } else {
        // データセル
        var value = parseFloat(cell) || 0;
        var intensity = maxValue > 0 ? value / maxValue : 0;
        var bgColor = getCellColor(intensity, colors.gradient);

        html.append('<td style="background: ' + bgColor + '; color: ' + (intensity > 0.6 ? 'white' : 'black') + ';">');
        html.append(value > 0 ? value.toFixed(0) : '-');
        html.append('</td>');
      }
    });
    html.append('</tr>');
  });

  html.append('</table>');
  html.append('</div>');

  // 注釈
  html.append('<p style="font-size: 12px; color: #666; margin-top: 20px;">');
  html.append('※ セルの色が濃いほど数値が大きいことを示します。');
  html.append('</p>');

  html.append('</div>');

  html.setWidth(1200);
  html.setHeight(800);

  return html;
}

// ===== ヘルパー関数 =====

function getColorScheme(scheme) {
  /**
   * カラースキームを取得
   *
   * @param {string} scheme - スキーム名
   * @return {Object} - カラー設定
   */
  var schemes = {
    'blue': {
      primary: '#667eea',
      secondary: '#764ba2',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      gradient: ['#e3f2fd', '#667eea', '#4a5bbf']
    },
    'red': {
      primary: '#f5576c',
      secondary: '#f093fb',
      background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
      gradient: ['#ffebee', '#f5576c', '#c62828']
    },
    'green': {
      primary: '#10b981',
      secondary: '#34d399',
      background: 'linear-gradient(135deg, #10b981 0%, #34d399 100%)',
      gradient: ['#d1fae5', '#10b981', '#047857']
    },
    'purple': {
      primary: '#8b5cf6',
      secondary: '#a78bfa',
      background: 'linear-gradient(135deg, #8b5cf6 0%, #a78bfa 100%)',
      gradient: ['#ede9fe', '#8b5cf6', '#6d28d9']
    }
  };

  return schemes[scheme] || schemes['blue'];
}

function getCellColor(intensity, gradientColors) {
  /**
   * セルの色を計算
   *
   * @param {number} intensity - 強度（0-1）
   * @param {Array} gradientColors - グラデーションカラー配列
   * @return {string} - RGB色
   */
  if (intensity === 0) {
    return '#ffffff';
  }

  if (intensity < 0.33) {
    return gradientColors[0];
  } else if (intensity < 0.67) {
    return gradientColors[1];
  } else {
    return gradientColors[2];
  }
}

// ===== 便利関数（各Phaseから呼び出し可能） =====

function showPhase8EducationAgeMatrixHeatmap() {
  /**
   * Phase 8: 学歴×年齢Matrixヒートマップ
   */
  showMatrixHeatmap('P8_EduAgeMatrix', 'Phase 8: 学歴×年齢ヒートマップ', 'blue');
}

function showPhase10UrgencyAgeMatrixHeatmap() {
  /**
   * Phase 10: 緊急度×年齢Matrixヒートマップ
   */
  showMatrixHeatmap('P10_UrgencyAgeMatrix', 'Phase 10: 緊急度×年齢ヒートマップ', 'red');
}

function showPhase10UrgencyEmploymentMatrixHeatmap() {
  /**
   * Phase 10: 緊急度×就業状態Matrixヒートマップ
   */
  showMatrixHeatmap('P10_UrgencyEmpMatrix', 'Phase 10: 緊急度×就業状態ヒートマップ', 'red');
}

// ===== 汎用Matrix比較機能 =====

function compareMatrices(sheetName1, sheetName2, title) {
  /**
   * 2つのMatrixを比較表示
   *
   * @param {string} sheetName1 - 1つ目のシート名
   * @param {string} sheetName2 - 2つ目のシート名
   * @param {string} title - タイトル
   */
  try {
    var matrix1 = loadMatrixData(sheetName1);
    var matrix2 = loadMatrixData(sheetName2);

    var html = generateMatrixComparisonHTML(matrix1, matrix2, title);

    SpreadsheetApp.getUi().showModalDialog(
      html,
      title
    );

  } catch (e) {
    SpreadsheetApp.getUi().alert('エラー: ' + e.toString());
  }
}

function generateMatrixComparisonHTML(matrix1, matrix2, title) {
  /**
   * Matrix比較HTML生成
   */

  var html = HtmlService.createHtmlOutput();
  html.append('<style>');
  html.append('body { font-family: Arial, sans-serif; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }');
  html.append('.container { background: white; border-radius: 12px; padding: 20px; }');
  html.append('h2 { color: #667eea; }');
  html.append('.comparison-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }');
  html.append('.matrix-panel { border: 1px solid #ddd; border-radius: 8px; padding: 15px; }');
  html.append('table { width: 100%; border-collapse: collapse; font-size: 12px; }');
  html.append('th, td { padding: 8px; text-align: center; border: 1px solid #ddd; }');
  html.append('th { background: #667eea; color: white; }');
  html.append('</style>');

  html.append('<div class="container">');
  html.append('<h2>' + title + '</h2>');
  html.append('<div class="comparison-grid">');

  // Matrix 1
  html.append('<div class="matrix-panel">');
  html.append('<h3>Matrix 1</h3>');
  html.append('<p>最大値: ' + matrix1.metadata.max.toFixed(0) + ' / 平均値: ' + matrix1.metadata.mean.toFixed(1) + '</p>');
  html.append('</div>');

  // Matrix 2
  html.append('<div class="matrix-panel">');
  html.append('<h3>Matrix 2</h3>');
  html.append('<p>最大値: ' + matrix2.metadata.max.toFixed(0) + ' / 平均値: ' + matrix2.metadata.mean.toFixed(1) + '</p>');
  html.append('</div>');

  html.append('</div>');
  html.append('</div>');

  html.setWidth(1200);
  html.setHeight(800);

  return html;
}


// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 6. 統合ダッシュボード（Phase 1-6）
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

/**
 * 完全統合ダッシュボード表示（メニューから呼び出し）
 */
function showCompleteIntegratedDashboard() {
  const ui = SpreadsheetApp.getUi();

  try {
    // 全データ読み込み
    const dashboardData = loadCompleteIntegratedData();

    // データ存在確認
    const totalRecords = calculateTotalRecords(dashboardData);

    if (totalRecords === 0) {
      ui.alert(
        'データなし',
        'データがインポートされていません。\n\n' +
        '「Phase 7クイックインポート」を先に実行してください。',
        ui.ButtonSet.OK
      );
      return;
    }

    // HTML生成
    const html = generateCompleteIntegratedDashboardHTML(dashboardData);

    // 全画面ダイアログ表示
    const htmlOutput = HtmlService.createHtmlOutput(html)
      .setWidth(1700)
      .setHeight(1000);

    ui.showModalDialog(htmlOutput, '📊 完全統合ダッシュボード - Phase 1+6+7+Network Analysis');

  } catch (error) {
    ui.alert('エラー', `ダッシュボード生成中にエラーが発生しました:\n${error.message}`, ui.ButtonSet.OK);
    Logger.log(`完全統合ダッシュボードエラー: ${error.stack}`);
  }
}


/**
 * 完全統合データ読み込み
 * @return {Object} 全データを含むオブジェクト
 */
function loadCompleteIntegratedData() {
  const data = {
    // Phase 1: 基礎集計
    mapMetrics: [],
    applicants: [],
    desiredWork: [],
    aggDesired: [],

    // Phase 6: フロー分析
    municipalityFlowEdges: [],
    municipalityFlowNodes: [],
    proximityAnalysis: [],

    // Phase 7: 高度分析
    supplyDensity: [],
    qualificationDist: [],
    ageGenderCross: [],
    mobilityScore: [],
    personaProfile: [],

    // ネットワーク分析
    networkMetrics: {},
    centralityRanking: []
  };

  // Phase 1データ読み込み
  try {
    const ss = SpreadsheetApp.getActiveSpreadsheet();

    const mapMetricsSheet = ss.getSheetByName('MapMetrics');
    if (mapMetricsSheet) {
      data.mapMetrics = getSheetData(mapMetricsSheet);
    }

    const applicantsSheet = ss.getSheetByName('Applicants');
    if (applicantsSheet) {
      data.applicants = getSheetData(applicantsSheet);
    }

    const desiredWorkSheet = ss.getSheetByName('DesiredWork');
    if (desiredWorkSheet) {
      data.desiredWork = getSheetData(desiredWorkSheet);
    }

    const aggDesiredSheet = ss.getSheetByName('AggDesired');
    if (aggDesiredSheet) {
      data.aggDesired = getSheetData(aggDesiredSheet);
    }
  } catch (e) {
    Logger.log(`Phase 1データ読み込みエラー: ${e.message}`);
  }

  // Phase 6データ読み込み
  try {
    data.municipalityFlowEdges = loadMunicipalityFlowData().edges || [];
    data.municipalityFlowNodes = loadMunicipalityFlowData().nodes || [];
  } catch (e) {
    Logger.log(`Phase 6データ読み込みエラー: ${e.message}`);
  }

  // Phase 7データ読み込み
  try {
    data.supplyDensity = loadSupplyDensityData();
  } catch (e) {
    Logger.log(`Phase 7 SupplyDensityデータ読み込みエラー: ${e.message}`);
  }

  try {
    data.qualificationDist = loadQualificationDistData();
  } catch (e) {
    Logger.log(`Phase 7 QualificationDistデータ読み込みエラー: ${e.message}`);
  }

  try {
    data.ageGenderCross = loadAgeGenderCrossData();
  } catch (e) {
    Logger.log(`Phase 7 AgeGenderCrossデータ読み込みエラー: ${e.message}`);
  }

  try {
    data.mobilityScore = loadMobilityScoreData();
  } catch (e) {
    Logger.log(`Phase 7 MobilityScoreデータ読み込みエラー: ${e.message}`);
  }

  try {
    data.personaProfile = loadPersonaProfileData();
  } catch (e) {
    Logger.log(`Phase 7 PersonaProfileデータ読み込みエラー: ${e.message}`);
  }

  // ネットワーク分析データ読み込み（JSON/CSV）
  try {
    // NetworkMetrics.jsonは手動でパースが必要な場合があるため、
    // 簡易的にCentralityRankingから統計を計算
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    const centralitySheet = ss.getSheetByName('CentralityRanking');

    if (centralitySheet) {
      data.centralityRanking = getSheetData(centralitySheet);

      // ネットワーク統計を計算
      if (data.centralityRanking.length > 0) {
        data.networkMetrics = {
          nodes: data.municipalityFlowNodes.length || 804,
          edges: data.municipalityFlowEdges.length || 6861,
          hubMunicipalities: data.centralityRanking.length
        };
      }
    }
  } catch (e) {
    Logger.log(`ネットワーク分析データ読み込みエラー: ${e.message}`);
  }

  return data;
}


/**
 * シートからデータ配列を取得
 * @param {Sheet} sheet - Googleスプレッドシートのシート
 * @return {Array} データ配列
 */
function getSheetData(sheet) {
  const range = sheet.getDataRange();
  const values = range.getValues();

  if (values.length === 0) return [];

  const headers = values[0];
  const dataRows = values.slice(1);

  return dataRows.map(row => {
    const obj = {};
    headers.forEach((header, index) => {
      obj[header] = row[index];
    });
    return obj;
  });
}


/**
 * 総レコード数計算
 * @param {Object} data - データオブジェクト
 * @return {number} 総レコード数
 */
function calculateTotalRecords(data) {
  let total = 0;

  for (let key in data) {
    if (Array.isArray(data[key])) {
      total += data[key].length;
    } else if (typeof data[key] === 'object' && data[key] !== null) {
      total += Object.keys(data[key]).length;
    }
  }

  return total;
}


/**
 * 完全統合ダッシュボードHTML生成
 * @param {Object} dashboardData - 全データ
 * @return {string} HTML文字列
 */
function generateCompleteIntegratedDashboardHTML(dashboardData) {
  // 各データをJSON文字列化（安全なエスケープ）
  const mapMetricsJson = JSON.stringify(dashboardData.mapMetrics || []);
  const applicantsJson = JSON.stringify(dashboardData.applicants || []);
  const municipalityFlowEdgesJson = JSON.stringify(dashboardData.municipalityFlowEdges || []);
  const municipalityFlowNodesJson = JSON.stringify(dashboardData.municipalityFlowNodes || []);
  const supplyDensityJson = JSON.stringify(dashboardData.supplyDensity || []);
  const qualificationDistJson = JSON.stringify(dashboardData.qualificationDist || []);
  const ageGenderCrossJson = JSON.stringify(dashboardData.ageGenderCross || []);
  const mobilityScoreJson = JSON.stringify(dashboardData.mobilityScore || []);
  const personaProfileJson = JSON.stringify(dashboardData.personaProfile || []);
  const centralityRankingJson = JSON.stringify(dashboardData.centralityRanking || []);
  const networkMetricsJson = JSON.stringify(dashboardData.networkMetrics || {});

  return `
<!DOCTYPE html>
<html>
<head>
  <base target="_top">
  <meta charset="UTF-8">
  <script type="text/javascript" src="https://www.gstatic.com/charts/loader.js"></script>
  <script src="https://d3js.org/d3.v7.min.js"></script>
  <style>
    * {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }
    body {
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      min-height: 100vh;
      overflow-x: hidden;
    }
    .dashboard-header {
      background: rgba(255,255,255,0.95);
      padding: 25px 50px;
      box-shadow: 0 4px 15px rgba(0,0,0,0.15);
      border-bottom: 4px solid #1a73e8;
    }
    .dashboard-header h1 {
      color: #1a73e8;
      font-size: 36px;
      margin-bottom: 8px;
      font-weight: 700;
    }
    .dashboard-header p {
      color: #666;
      font-size: 16px;
    }
    .dashboard-header .version {
      display: inline-block;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      padding: 5px 15px;
      border-radius: 20px;
      font-size: 12px;
      font-weight: 600;
      margin-left: 15px;
      vertical-align: middle;
    }
    .tab-container {
      background: white;
      margin: 20px;
      border-radius: 16px;
      box-shadow: 0 8px 30px rgba(0,0,0,0.2);
      overflow: hidden;
    }
    .tabs {
      display: flex;
      flex-wrap: wrap;
      background: #f8f9fa;
      border-bottom: 3px solid #e0e0e0;
      padding: 5px 20px 0;
    }
    .tab {
      padding: 15px 25px;
      cursor: pointer;
      border: none;
      background: transparent;
      font-size: 15px;
      font-weight: 600;
      color: #666;
      transition: all 0.3s;
      border-bottom: 3px solid transparent;
      margin-bottom: -3px;
      border-radius: 8px 8px 0 0;
    }
    .tab:hover {
      background: rgba(26, 115, 232, 0.1);
      color: #1a73e8;
    }
    .tab.active {
      color: #1a73e8;
      border-bottom-color: #1a73e8;
      background: white;
      box-shadow: 0 -2px 5px rgba(0,0,0,0.05);
    }
    .tab-content {
      display: none;
      padding: 40px;
      min-height: 750px;
      animation: fadeIn 0.4s ease-in-out;
    }
    .tab-content.active {
      display: block;
    }
    @keyframes fadeIn {
      from {
        opacity: 0;
        transform: translateY(15px);
      }
      to {
        opacity: 1;
        transform: translateY(0);
      }
    }
    .kpi-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
      gap: 25px;
      margin-bottom: 35px;
    }
    .kpi-card {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      padding: 30px;
      border-radius: 16px;
      box-shadow: 0 8px 20px rgba(0,0,0,0.15);
      text-align: center;
      transition: transform 0.3s, box-shadow 0.3s;
    }
    .kpi-card:hover {
      transform: translateY(-5px);
      box-shadow: 0 12px 30px rgba(0,0,0,0.25);
    }
    .kpi-card.card-1 { background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); }
    .kpi-card.card-2 { background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); }
    .kpi-card.card-3 { background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); }
    .kpi-card.card-4 { background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); }
    .kpi-card.card-5 { background: linear-gradient(135deg, #30cfd0 0%, #330867 100%); }
    .kpi-card.card-6 { background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%); }
    .kpi-label {
      font-size: 15px;
      opacity: 0.95;
      margin-bottom: 12px;
      font-weight: 500;
      text-transform: uppercase;
      letter-spacing: 1px;
    }
    .kpi-value {
      font-size: 42px;
      font-weight: 700;
      margin: 10px 0;
      text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
    }
    .kpi-unit {
      font-size: 14px;
      opacity: 0.9;
      margin-top: 8px;
    }
    .chart-container {
      background: white;
      padding: 30px;
      border-radius: 12px;
      margin-bottom: 25px;
      box-shadow: 0 4px 12px rgba(0,0,0,0.08);
      border: 1px solid #e8e8e8;
    }
    .chart-container h2 {
      color: #333;
      margin-bottom: 20px;
      font-size: 22px;
      font-weight: 600;
      border-left: 4px solid #1a73e8;
      padding-left: 15px;
    }
    .chart {
      width: 100%;
      height: 450px;
    }
    .data-table {
      width: 100%;
      border-collapse: collapse;
      margin-top: 20px;
      font-size: 14px;
    }
    .data-table th {
      background: #f5f5f5;
      color: #333;
      padding: 12px;
      text-align: left;
      border-bottom: 2px solid #ddd;
      font-weight: 600;
    }
    .data-table td {
      padding: 10px 12px;
      border-bottom: 1px solid #eee;
    }
    .data-table tr:hover {
      background: #f9f9f9;
    }
    .badge {
      display: inline-block;
      padding: 4px 12px;
      border-radius: 12px;
      font-size: 12px;
      font-weight: 600;
      text-transform: uppercase;
    }
    .badge-success { background: #d4edda; color: #155724; }
    .badge-warning { background: #fff3cd; color: #856404; }
    .badge-danger { background: #f8d7da; color: #721c24; }
    .badge-info { background: #d1ecf1; color: #0c5460; }
    .section-title {
      font-size: 24px;
      font-weight: 700;
      color: #333;
      margin-bottom: 25px;
      padding-bottom: 12px;
      border-bottom: 3px solid #1a73e8;
    }
    .stats-summary {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 20px;
      margin-bottom: 30px;
    }
    .stats-item {
      background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
      padding: 20px;
      border-radius: 10px;
      text-align: center;
    }
    .stats-item-label {
      font-size: 14px;
      color: #666;
      margin-bottom: 8px;
    }
    .stats-item-value {
      font-size: 32px;
      font-weight: 700;
      color: #333;
    }
  </style>
</head>
<body>
  <div class="dashboard-header">
    <h1>📊 完全統合ダッシュボード <span class="version">Phase 1+6+7+Network v1.0</span></h1>
    <p>Python分析エンジン × Google Apps Script × D3.js による包括的データ可視化プラットフォーム</p>
  </div>

  <div class="tab-container">
    <div class="tabs">
      <button class="tab active" onclick="switchTab(0)">📊 統合概要</button>
      <button class="tab" onclick="switchTab(1)">📍 Phase 1: 基礎集計</button>
      <button class="tab" onclick="switchTab(2)">🌊 Phase 6: フロー分析</button>
      <button class="tab" onclick="switchTab(3)">🔗 ネットワーク中心性</button>
      <button class="tab" onclick="switchTab(4)">🗺️ Phase 7: 供給密度</button>
      <button class="tab" onclick="switchTab(5)">🎓 Phase 7: 資格分布</button>
      <button class="tab" onclick="switchTab(6)">👥 Phase 7: 年齢×性別</button>
      <button class="tab" onclick="switchTab(7)">🚗 Phase 7: 移動許容度</button>
      <button class="tab" onclick="switchTab(8)">📋 Phase 7: ペルソナ</button>
    </div>

    <!-- タブ0: 統合概要 -->
    <div class="tab-content active" id="tab-0">
      <h2 class="section-title">全Phase統合サマリー</h2>
      <div class="kpi-grid" id="overview-kpis"></div>

      <div class="chart-container">
        <h2>データセット別レコード数</h2>
        <div id="overview_availability_chart" class="chart"></div>
      </div>

      <div class="chart-container">
        <h2>Phase別データ可用性</h2>
        <div id="phase_availability_chart" class="chart"></div>
      </div>
    </div>

    <!-- タブ1: Phase 1基礎集計 -->
    <div class="tab-content" id="tab-1">
      <h2 class="section-title">Phase 1: 基礎集計データ</h2>

      <div class="stats-summary">
        <div class="stats-item">
          <div class="stats-item-label">MapMetrics</div>
          <div class="stats-item-value" id="mapmetrics-count">0</div>
        </div>
        <div class="stats-item">
          <div class="stats-item-label">Applicants</div>
          <div class="stats-item-value" id="applicants-count">0</div>
        </div>
        <div class="stats-item">
          <div class="stats-item-label">DesiredWork</div>
          <div class="stats-item-value" id="desiredwork-count">0</div>
        </div>
      </div>

      <div class="chart-container">
        <h2>希望勤務地TOP 20（MapMetrics）</h2>
        <div id="phase1_mapmetrics_chart" class="chart"></div>
      </div>
    </div>

    <!-- タブ2: Phase 6フロー分析 -->
    <div class="tab-content" id="tab-2">
      <h2 class="section-title">Phase 6: 自治体間フロー分析</h2>

      <div class="stats-summary">
        <div class="stats-item">
          <div class="stats-item-label">フローエッジ</div>
          <div class="stats-item-value" id="flow-edges-count">0</div>
        </div>
        <div class="stats-item">
          <div class="stats-item-label">フローノード</div>
          <div class="stats-item-value" id="flow-nodes-count">0</div>
        </div>
        <div class="stats-item">
          <div class="stats-item-label">ネットワーク密度</div>
          <div class="stats-item-value" id="network-density">0%</div>
        </div>
      </div>

      <div class="chart-container">
        <h2>TOP 20フローエッジ（Source → Target）</h2>
        <div id="phase6_flow_chart" class="chart"></div>
      </div>
    </div>

    <!-- タブ3: ネットワーク中心性分析 -->
    <div class="tab-content" id="tab-3">
      <h2 class="section-title">ネットワーク中心性分析（NetworkX）</h2>

      <div class="stats-summary">
        <div class="stats-item">
          <div class="stats-item-label">ノード数</div>
          <div class="stats-item-value" id="network-nodes">0</div>
        </div>
        <div class="stats-item">
          <div class="stats-item-label">エッジ数</div>
          <div class="stats-item-value" id="network-edges">0</div>
        </div>
        <div class="stats-item">
          <div class="stats-item-label">ハブ自治体</div>
          <div class="stats-item-value" id="hub-municipalities">0</div>
        </div>
      </div>

      <div class="chart-container">
        <h2>TOP 10ハブ自治体（複合中心性スコア）</h2>
        <div id="network_centrality_chart" class="chart"></div>
      </div>

      <div class="chart-container">
        <h2>中心性ランキング詳細（TOP 20）</h2>
        <table class="data-table" id="centrality-ranking-table">
          <thead>
            <tr>
              <th>順位</th>
              <th>自治体</th>
              <th>複合スコア</th>
              <th>PageRank</th>
              <th>媒介中心性</th>
              <th>純フロー</th>
            </tr>
          </thead>
          <tbody id="centrality-table-body"></tbody>
        </table>
      </div>
    </div>

    <!-- タブ4: Phase 7供給密度 -->
    <div class="tab-content" id="tab-4">
      <h2 class="section-title">Phase 7: 人材供給密度マップ</h2>
      <div class="chart-container">
        <h2>人材供給密度TOP 20</h2>
        <div id="supply_density_chart" class="chart"></div>
      </div>
    </div>

    <!-- タブ5: Phase 7資格分布 -->
    <div class="tab-content" id="tab-5">
      <h2 class="section-title">Phase 7: 資格別人材分布</h2>
      <div class="chart-container">
        <h2>資格カテゴリ別保有者数</h2>
        <div id="qualification_dist_chart" class="chart"></div>
      </div>
    </div>

    <!-- タブ6: Phase 7年齢×性別 -->
    <div class="tab-content" id="tab-6">
      <h2 class="section-title">Phase 7: 年齢層×性別クロス分析</h2>
      <div class="chart-container">
        <h2>ダイバーシティスコア（TOP 20）</h2>
        <div id="age_gender_cross_chart" class="chart"></div>
      </div>
    </div>

    <!-- タブ7: Phase 7移動許容度 -->
    <div class="tab-content" id="tab-7">
      <h2 class="section-title">Phase 7: 移動許容度スコアリング</h2>
      <div class="chart-container">
        <h2>移動許容度レベル別人数</h2>
        <div id="mobility_score_chart" class="chart"></div>
      </div>
    </div>

    <!-- タブ8: Phase 7ペルソナ -->
    <div class="tab-content" id="tab-8">
      <h2 class="section-title">Phase 7: ペルソナ詳細プロファイル</h2>
      <div class="chart-container">
        <h2>ペルソナ別人数分布</h2>
        <div id="persona_profile_chart" class="chart"></div>
      </div>
    </div>
  </div>

  <script type="text/javascript">
    // データ読み込み
    const mapMetricsData = ${mapMetricsJson};
    const applicantsData = ${applicantsJson};
    const municipalityFlowEdges = ${municipalityFlowEdgesJson};
    const municipalityFlowNodes = ${municipalityFlowNodesJson};
    const supplyDensityData = ${supplyDensityJson};
    const qualificationDistData = ${qualificationDistJson};
    const ageGenderCrossData = ${ageGenderCrossJson};
    const mobilityScoreData = ${mobilityScoreJson};
    const personaProfileData = ${personaProfileJson};
    const centralityRankingData = ${centralityRankingJson};
    const networkMetrics = ${networkMetricsJson};

    // Google Charts読み込み
    google.charts.load('current', {'packages':['corechart', 'bar', 'table']});
    google.charts.setOnLoadCallback(initDashboard);

    function initDashboard() {
      renderOverviewKPIs();
      drawOverviewAvailabilityChart();
      drawPhaseAvailabilityChart();
      updatePhaseStats();
    }

    // タブ切り替え
    function switchTab(tabIndex) {
      // 全タブを非アクティブ化
      document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
      document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));

      // 選択されたタブをアクティブ化
      document.querySelectorAll('.tab')[tabIndex].classList.add('active');
      document.getElementById(\`tab-\${tabIndex}\`).classList.add('active');

      // タブ別にチャート描画
      switch(tabIndex) {
        case 1:
          if (mapMetricsData.length > 0) drawPhase1MapMetricsChart();
          break;
        case 2:
          if (municipalityFlowEdges.length > 0) drawPhase6FlowChart();
          break;
        case 3:
          if (centralityRankingData.length > 0) {
            drawNetworkCentralityChart();
            renderCentralityRankingTable();
          }
          break;
        case 4:
          if (supplyDensityData.length > 0) drawSupplyDensityChart();
          break;
        case 5:
          if (qualificationDistData.length > 0) drawQualificationDistChart();
          break;
        case 6:
          if (ageGenderCrossData.length > 0) drawAgeGenderCrossChart();
          break;
        case 7:
          if (mobilityScoreData.length > 0) drawMobilityScoreChart();
          break;
        case 8:
          if (personaProfileData.length > 0) drawPersonaProfileChart();
          break;
      }
    }

    // 概要KPI表示
    function renderOverviewKPIs() {
      const container = document.getElementById('overview-kpis');

      const kpis = [
        {
          label: 'Phase 1データ',
          value: mapMetricsData.length + applicantsData.length,
          unit: 'レコード',
          cardClass: 'card-1'
        },
        {
          label: 'フローエッジ',
          value: municipalityFlowEdges.length.toLocaleString(),
          unit: 'エッジ',
          cardClass: 'card-2'
        },
        {
          label: 'ハブ自治体',
          value: centralityRankingData.length,
          unit: '都市',
          cardClass: 'card-3'
        },
        {
          label: 'Phase 7分析',
          value: supplyDensityData.length + qualificationDistData.length + ageGenderCrossData.length,
          unit: 'レコード',
          cardClass: 'card-4'
        },
        {
          label: '移動許容度',
          value: mobilityScoreData.length.toLocaleString(),
          unit: '名',
          cardClass: 'card-5'
        },
        {
          label: 'ペルソナ',
          value: personaProfileData.length,
          unit: 'タイプ',
          cardClass: 'card-6'
        }
      ];

      kpis.forEach(kpi => {
        const card = document.createElement('div');
        card.className = \`kpi-card \${kpi.cardClass}\`;
        card.innerHTML = \`
          <div class="kpi-label">\${kpi.label}</div>
          <div class="kpi-value">\${kpi.value}</div>
          <div class="kpi-unit">\${kpi.unit}</div>
        \`;
        container.appendChild(card);
      });
    }

    // Phase統計更新
    function updatePhaseStats() {
      document.getElementById('mapmetrics-count').textContent = mapMetricsData.length.toLocaleString();
      document.getElementById('applicants-count').textContent = applicantsData.length.toLocaleString();
      document.getElementById('desiredwork-count').textContent = mapMetricsData.length.toLocaleString();

      document.getElementById('flow-edges-count').textContent = municipalityFlowEdges.length.toLocaleString();
      document.getElementById('flow-nodes-count').textContent = municipalityFlowNodes.length.toLocaleString();

      if (municipalityFlowNodes.length > 0 && municipalityFlowEdges.length > 0) {
        const maxEdges = municipalityFlowNodes.length * (municipalityFlowNodes.length - 1);
        const density = ((municipalityFlowEdges.length / maxEdges) * 100).toFixed(2);
        document.getElementById('network-density').textContent = density + '%';
      }

      document.getElementById('network-nodes').textContent = (networkMetrics.nodes || 0).toLocaleString();
      document.getElementById('network-edges').textContent = (networkMetrics.edges || 0).toLocaleString();
      document.getElementById('hub-municipalities').textContent = (networkMetrics.hubMunicipalities || 0);
    }

    // データ可用性チャート
    function drawOverviewAvailabilityChart() {
      const chartData = new google.visualization.DataTable();
      chartData.addColumn('string', 'データセット');
      chartData.addColumn('number', 'レコード数');

      chartData.addRow(['MapMetrics', mapMetricsData.length]);
      chartData.addRow(['Applicants', applicantsData.length]);
      chartData.addRow(['FlowEdges', municipalityFlowEdges.length]);
      chartData.addRow(['FlowNodes', municipalityFlowNodes.length]);
      chartData.addRow(['SupplyDensity', supplyDensityData.length]);
      chartData.addRow(['Qualification', qualificationDistData.length]);
      chartData.addRow(['AgeGender', ageGenderCrossData.length]);
      chartData.addRow(['MobilityScore', mobilityScoreData.length]);
      chartData.addRow(['Persona', personaProfileData.length]);
      chartData.addRow(['Centrality', centralityRankingData.length]);

      const options = {
        title: 'データセット別レコード数（全10データセット）',
        colors: ['#1a73e8'],
        legend: {position: 'none'},
        hAxis: { title: 'レコード数' },
        vAxis: { title: 'データセット' },
        chartArea: {width: '70%', height: '75%'}
      };

      const chart = new google.visualization.BarChart(
        document.getElementById('overview_availability_chart')
      );

      chart.draw(chartData, options);
    }

    // Phase別可用性チャート
    function drawPhaseAvailabilityChart() {
      const chartData = new google.visualization.DataTable();
      chartData.addColumn('string', 'Phase');
      chartData.addColumn('number', 'レコード数');

      const phase1Records = mapMetricsData.length + applicantsData.length;
      const phase6Records = municipalityFlowEdges.length + municipalityFlowNodes.length;
      const phase7Records = supplyDensityData.length + qualificationDistData.length +
                           ageGenderCrossData.length + mobilityScoreData.length + personaProfileData.length;
      const networkRecords = centralityRankingData.length;

      chartData.addRow(['Phase 1: 基礎集計', phase1Records]);
      chartData.addRow(['Phase 6: フロー分析', phase6Records]);
      chartData.addRow(['Phase 7: 高度分析', phase7Records]);
      chartData.addRow(['Network: 中心性', networkRecords]);

      const options = {
        title: 'Phase別データ総量',
        colors: ['#4285F4', '#34A853', '#FBBC04', '#EA4335'],
        legend: {position: 'none'},
        chartArea: {width: '70%', height: '70%'}
      };

      const chart = new google.visualization.ColumnChart(
        document.getElementById('phase_availability_chart')
      );

      chart.draw(chartData, options);
    }

    // Phase 1: MapMetricsチャート
    function drawPhase1MapMetricsChart() {
      const chartData = new google.visualization.DataTable();
      chartData.addColumn('string', '市区町村');
      chartData.addColumn('number', '希望者数');

      const top20 = [...mapMetricsData]
        .sort((a, b) => (b.人数 || 0) - (a.人数 || 0))
        .slice(0, 20);

      top20.forEach(row => {
        chartData.addRow([row.市区町村名 || row.Municipality || 'N/A', row.人数 || row.Count || 0]);
      });

      const options = {
        title: '希望勤務地TOP 20',
        colors: ['#4285F4'],
        hAxis: { title: '希望者数' },
        chartArea: {width: '70%', height: '75%'}
      };

      const chart = new google.visualization.BarChart(
        document.getElementById('phase1_mapmetrics_chart')
      );

      chart.draw(chartData, options);
    }

    // Phase 6: フローチャート
    function drawPhase6FlowChart() {
      const chartData = new google.visualization.DataTable();
      chartData.addColumn('string', 'フロー');
      chartData.addColumn('number', 'カウント');

      const top20 = [...municipalityFlowEdges]
        .sort((a, b) => (b.Flow_Count || 0) - (a.Flow_Count || 0))
        .slice(0, 20);

      top20.forEach(row => {
        const label = \`\${row.Source_Municipality || 'N/A'} → \${row.Target_Municipality || 'N/A'}\`;
        chartData.addRow([label, row.Flow_Count || 0]);
      });

      const options = {
        title: 'TOP 20フローエッジ',
        colors: ['#34A853'],
        hAxis: { title: 'フローカウント' },
        chartArea: {width: '60%', height: '75%'}
      };

      const chart = new google.visualization.BarChart(
        document.getElementById('phase6_flow_chart')
      );

      chart.draw(chartData, options);
    }

    // ネットワーク中心性チャート
    function drawNetworkCentralityChart() {
      const chartData = new google.visualization.DataTable();
      chartData.addColumn('string', '自治体');
      chartData.addColumn('number', '複合スコア');

      const top10 = [...centralityRankingData]
        .sort((a, b) => (b.composite_score || 0) - (a.composite_score || 0))
        .slice(0, 10);

      top10.forEach(row => {
        chartData.addRow([row.municipality || 'N/A', row.composite_score || 0]);
      });

      const options = {
        title: 'ハブ自治体TOP 10（複合中心性スコア）',
        colors: ['#EA4335'],
        hAxis: { title: '複合スコア' },
        chartArea: {width: '70%', height: '75%'}
      };

      const chart = new google.visualization.BarChart(
        document.getElementById('network_centrality_chart')
      );

      chart.draw(chartData, options);
    }

    // 中心性ランキングテーブル
    function renderCentralityRankingTable() {
      const tbody = document.getElementById('centrality-table-body');
      tbody.innerHTML = '';

      centralityRankingData.slice(0, 20).forEach(row => {
        const tr = document.createElement('tr');
        tr.innerHTML = \`
          <td><span class="badge badge-info">#\${row.rank || '-'}</span></td>
          <td>\${row.municipality || 'N/A'}</td>
          <td>\${(row.composite_score || 0).toFixed(4)}</td>
          <td>\${(row.pagerank || 0).toFixed(4)}</td>
          <td>\${(row.betweenness_centrality || 0).toFixed(4)}</td>
          <td>\${(row.net_flow || 0).toLocaleString()}</td>
        \`;
        tbody.appendChild(tr);
      });
    }

    // Phase 7チャート描画関数（既存のものを再利用）
    function drawSupplyDensityChart() {
      const chartData = new google.visualization.DataTable();
      chartData.addColumn('string', '市区町村');
      chartData.addColumn('number', '総合スコア');

      const top20 = [...supplyDensityData]
        .sort((a, b) => (b.compositeScore || 0) - (a.compositeScore || 0))
        .slice(0, 20);

      top20.forEach(row => {
        chartData.addRow([row.municipality || 'N/A', row.compositeScore || 0]);
      });

      const options = {
        title: '人材供給密度TOP 20',
        colors: ['#4285F4'],
        hAxis: { title: '総合スコア' },
        chartArea: {width: '70%', height: '75%'}
      };

      const chart = new google.visualization.BarChart(
        document.getElementById('supply_density_chart')
      );

      chart.draw(chartData, options);
    }

    function drawQualificationDistChart() {
      const chartData = new google.visualization.DataTable();
      chartData.addColumn('string', '資格カテゴリ');
      chartData.addColumn('number', '保有者数');

      qualificationDistData.forEach(row => {
        chartData.addRow([row.category || 'N/A', row.totalHolders || 0]);
      });

      const options = {
        title: '資格カテゴリ別保有者数',
        colors: ['#34A853'],
        hAxis: { title: '保有者数' },
        chartArea: {width: '70%', height: '70%'}
      };

      const chart = new google.visualization.BarChart(
        document.getElementById('qualification_dist_chart')
      );

      chart.draw(chartData, options);
    }

    function drawAgeGenderCrossChart() {
      const chartData = new google.visualization.DataTable();
      chartData.addColumn('string', '市区町村');
      chartData.addColumn('number', 'ダイバーシティスコア');

      const top20 = [...ageGenderCrossData]
        .sort((a, b) => (b.diversityScore || 0) - (a.diversityScore || 0))
        .slice(0, 20);

      top20.forEach(row => {
        chartData.addRow([row.municipality || 'N/A', row.diversityScore || 0]);
      });

      const options = {
        title: 'ダイバーシティスコアTOP 20',
        colors: ['#FBBC04'],
        hAxis: { title: 'ダイバーシティスコア' },
        chartArea: {width: '70%', height: '75%'}
      };

      const chart = new google.visualization.BarChart(
        document.getElementById('age_gender_cross_chart')
      );

      chart.draw(chartData, options);
    }

    function drawMobilityScoreChart() {
      const chartData = new google.visualization.DataTable();
      chartData.addColumn('string', 'レベル');
      chartData.addColumn('number', '人数');

      const levels = ['A', 'B', 'C', 'D'];
      const levelCounts = {};

      levels.forEach(level => {
        levelCounts[level] = mobilityScoreData.filter(r => r.mobilityLevel === level).length;
      });

      chartData.addRow(['広域移動OK (A)', levelCounts['A'] || 0]);
      chartData.addRow(['中距離OK (B)', levelCounts['B'] || 0]);
      chartData.addRow(['近距離のみ (C)', levelCounts['C'] || 0]);
      chartData.addRow(['地元限定 (D)', levelCounts['D'] || 0]);

      const options = {
        title: '移動許容度レベル別人数',
        pieHole: 0.4,
        colors: ['#4facfe', '#43e97b', '#fa709a', '#a8a8a8']
      };

      const chart = new google.visualization.PieChart(
        document.getElementById('mobility_score_chart')
      );

      chart.draw(chartData, options);
    }

    function drawPersonaProfileChart() {
      const chartData = new google.visualization.DataTable();
      chartData.addColumn('string', 'ペルソナ');
      chartData.addColumn('number', '人数');

      personaProfileData.forEach(row => {
        chartData.addRow([row.personaName || 'N/A', row.count || 0]);
      });

      const options = {
        title: 'ペルソナ別人数分布',
        pieHole: 0.4,
        colors: ['#667eea', '#4facfe', '#43e97b', '#fa709a', '#f093fb', '#30cfd0']
      };

      const chart = new google.visualization.PieChart(
        document.getElementById('persona_profile_chart')
      );

      chart.draw(chartData, options);
    }
  </script>
</body>
</html>
  `;
}


