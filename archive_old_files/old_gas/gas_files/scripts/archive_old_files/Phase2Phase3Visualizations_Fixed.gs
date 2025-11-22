/**
 * Phase 2/3 可視化関数 - 修正版
 * 統計分析とペルソナ分析の結果を表示
 *
 * 作成日: 2025-10-27
 * 修正日: 2025-10-28 - データなしの場合のメッセージ改善
 */

/**
 * カイ二乗検定結果の表示
 *
 * 【修正内容】
 * - データなしの場合の詳細メッセージ追加
 * - デバッグログ追加
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
  Logger.log(`ChiSquareTests データ行数: ${data.length}`);

  if (data.length <= 1) {
    // 【修正】より詳細なメッセージ
    SpreadsheetApp.getUi().alert(
      '情報',
      'カイ二乗検定のデータがありません。\n\n' +
      '【確認事項】\n' +
      '1. ChiSquareTests.csvがヘッダー行のみになっていませんか？\n' +
      '2. Pythonスクリプト実行時にエラーが出ていませんか？\n' +
      '3. データに「性別」「年齢層」「希望勤務地数」が含まれていますか？\n\n' +
      '【対応方法】\n' +
      '- run_complete_v2.pyを再実行してください\n' +
      '- 実行ログで「[2/4] カイ二乗検定実施中...」を確認してください\n' +
      '- ChiSquareTests.csvに2行以上あることを確認してください',
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
    <p style="color: #5f6368;">データ件数: ${data.length - 1}件</p>
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
          <span class="metric-value">${Number(chiSquare).toFixed(4)}</span>
        </div>
        <div class="metric">
          <span class="metric-label">p値:</span>
          <span class="metric-value ${significantClass}">${Number(pValue).toFixed(4)}</span>
        </div>
        <div class="metric">
          <span class="metric-label">自由度:</span>
          <span class="metric-value">${df}</span>
        </div>
        <div class="metric">
          <span class="metric-label">効果量:</span>
          <span class="metric-value">${Number(effectSize).toFixed(4)}</span>
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
          ${interpretation}
        </div>
      </div>
    `;
  }

  const output = HtmlService.createHtmlOutput(html)
    .setWidth(900)
    .setHeight(700);

  SpreadsheetApp.getUi().showModalDialog(output, '🔬 カイ二乗検定結果');
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
  Logger.log(`ANOVATests データ行数: ${data.length}`);

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
    <p style="color: #5f6368;">データ件数: ${data.length - 1}件</p>
  `;

  // ヘッダー行をスキップ
  for (let i = 1; i < data.length; i++) {
    const row = data[i];
    const pattern = row[0];
    const group = row[1];
    const variable = row[2];
    const fStatistic = row[3];
    const pValue = row[4];
    const dfBetween = row[5];
    const dfWithin = row[6];
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
          <span class="metric-label">F統計量:</span>
          <span class="metric-value">${Number(fStatistic).toFixed(4)}</span>
        </div>
        <div class="metric">
          <span class="metric-label">p値:</span>
          <span class="metric-value ${significantClass}">${Number(pValue).toFixed(6)}</span>
        </div>
        <div class="metric">
          <span class="metric-label">自由度（群間/群内）:</span>
          <span class="metric-value">${dfBetween} / ${dfWithin}</span>
        </div>
        <div class="metric">
          <span class="metric-label">効果量:</span>
          <span class="metric-value">${Number(effectSize).toFixed(4)}</span>
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
          ${interpretation}
        </div>
      </div>
    `;
  }

  const output = HtmlService.createHtmlOutput(html)
    .setWidth(900)
    .setHeight(700);

  SpreadsheetApp.getUi().showModalDialog(output, '📊 ANOVA検定結果');
}
