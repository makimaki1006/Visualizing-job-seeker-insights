/**
 * Phase 2/3 可視化関数
 * 統計分析とペルソナ分析の結果を表示
 *
 * 作成日: 2025-10-27
 */

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
