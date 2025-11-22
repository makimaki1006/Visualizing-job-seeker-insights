/**
 * データ管理ユーティリティ関数
 *
 * データ確認、統計サマリー、データクリア、デバッグログ、カラム分析機能を提供します。
 *
 * 作成日: 2025-10-30
 * バージョン: 1.0（Phase接頭辞対応版）
 */

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// データ確認機能
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

/**
 * マップデータの存在確認と基本統計を表示
 */
function checkMapData() {
  const ui = SpreadsheetApp.getUi();
  const ss = SpreadsheetApp.getActiveSpreadsheet();

  // Phase 1のマップ関連シート確認
  const sheetConfigs = [
    { name: 'Phase1_MapMetrics', label: '地図メトリクス' },
    { name: 'Phase1_Applicants', label: '申請者基本情報' },
    { name: 'Phase1_DesiredWork', label: '希望勤務地詳細' },
    { name: 'Phase1_AggDesired', label: '集計データ' }
  ];

  let message = 'マップデータ確認:\n\n';
  let allPresent = true;
  let totalRecords = 0;

  sheetConfigs.forEach(config => {
    const sheet = ss.getSheetByName(config.name);

    if (!sheet) {
      message += `✗ ${config.label} (${config.name}): シートなし\n`;
      allPresent = false;
    } else {
      const rows = sheet.getLastRow() - 1; // ヘッダー除く
      const cols = sheet.getLastColumn();
      message += `✓ ${config.label} (${config.name}):\n`;
      message += `  データ行数: ${rows.toLocaleString()}行\n`;
      message += `  カラム数: ${cols}列\n\n`;
      totalRecords += rows;
    }
  });

  if (allPresent) {
    message += `\n合計レコード数: ${totalRecords.toLocaleString()}件\n`;
    message += '\n✅ 全てのマップデータが正常に存在しています。';
  } else {
    message += '\n⚠️ 一部のシートが見つかりません。\nデータインポートを実行してください。';
  }

  ui.alert('マップデータ確認', message, ui.ButtonSet.OK);
}


// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 統計サマリー機能
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

/**
 * 全Phase統計サマリーを表示
 */
function showStatsSummary() {
  const ui = SpreadsheetApp.getUi();
  const ss = SpreadsheetApp.getActiveSpreadsheet();

  const phaseConfigs = [
    {
      phase: 'Phase 1: 基礎集計',
      sheets: [
        'Phase1_MapMetrics',
        'Phase1_Applicants',
        'Phase1_DesiredWork',
        'Phase1_AggDesired'
      ]
    },
    {
      phase: 'Phase 2: 統計分析',
      sheets: [
        'Phase2_ChiSquare',
        'Phase2_ANOVA'
      ]
    },
    {
      phase: 'Phase 3: ペルソナ分析',
      sheets: [
        'Phase3_PersonaSummary',
        'Phase3_PersonaDetails',
        'Phase3_PersonaSummaryByMunicipality'
      ]
    },
    {
      phase: 'Phase 6: フロー分析',
      sheets: [
        'Phase6_FlowEdges',
        'Phase6_FlowNodes',
        'Phase6_Proximity'
      ]
    },
    {
      phase: 'Phase 7: 高度分析',
      sheets: [
        'Phase7_SupplyDensity',
        'Phase7_QualificationDist',
        'Phase7_AgeGenderCross',
        'Phase7_MobilityScore',
        'Phase7_PersonaProfile',
        'Phase7_PersonaMapData',
        'Phase7_PersonaMobilityCross'
      ]
    },
    {
      phase: 'Phase 8: キャリア・学歴分析',
      sheets: [
        'Phase8_EducationDist',
        'Phase8_EduAgeCross',
        'Phase8_EduAgeMatrix',
        'Phase8_GradYearDist',
        'Phase8_CareerDistribution',
        'Phase8_CareerAgeCross',
        'Phase8_CareerAgeMatrix'
      ]
    },
    {
      phase: 'Phase 10: 転職意欲・緊急度分析',
      sheets: [
        'Phase10_UrgDist',
        'Phase10_UrgAge',
        'Phase10_UrgAge_Matrix',
        'Phase10_UrgEmp',
        'Phase10_UrgEmp_Matrix'
      ]
    }
  ];

  let html = '<style>' +
    'body { font-family: Arial, sans-serif; padding: 20px; background: #f5f5f5; }' +
    'h2 { color: #1976d2; }' +
    '.phase-section { background: white; padding: 15px; margin: 15px 0; border-radius: 8px; border-left: 4px solid #1976d2; }' +
    '.phase-title { font-size: 16px; font-weight: bold; color: #333; margin-bottom: 10px; }' +
    '.sheet-item { padding: 5px 10px; margin: 5px 0; background: #f9f9f9; border-radius: 4px; }' +
    '.present { color: #2e7d32; }' +
    '.absent { color: #c62828; }' +
    '.stats { font-size: 12px; color: #666; margin-left: 10px; }' +
    '.summary { background: #e3f2fd; padding: 15px; border-radius: 8px; margin: 20px 0; }' +
    '</style>';

  html += '<h2>📊 全Phase統計サマリー</h2>';

  let totalSheets = 0;
  let presentSheets = 0;
  let totalRecords = 0;

  phaseConfigs.forEach(phaseConfig => {
    html += `<div class="phase-section">`;
    html += `<div class="phase-title">${phaseConfig.phase}</div>`;

    let phasePresent = 0;
    let phaseTotal = 0;

    phaseConfig.sheets.forEach(sheetName => {
      const sheet = ss.getSheetByName(sheetName);
      totalSheets++;

      if (sheet) {
        const rows = sheet.getLastRow() - 1;
        const cols = sheet.getLastColumn();
        html += `<div class="sheet-item">`;
        html += `<span class="present">✓</span> ${sheetName}`;
        html += `<span class="stats">${rows.toLocaleString()}行 × ${cols}列</span>`;
        html += `</div>`;
        presentSheets++;
        phasePresent++;
        totalRecords += rows;
      } else {
        html += `<div class="sheet-item">`;
        html += `<span class="absent">✗</span> ${sheetName} (シートなし)`;
        html += `</div>`;
      }

      phaseTotal++;
    });

    html += `<div style="margin-top: 10px; font-size: 12px; color: #666;">`;
    html += `ステータス: ${phasePresent}/${phaseTotal}シート存在`;
    html += `</div>`;

    html += `</div>`;
  });

  // サマリー
  html += `<div class="summary">`;
  html += `<strong>全体サマリー:</strong><br>`;
  html += `総シート数: ${presentSheets}/${totalSheets} (${(presentSheets / totalSheets * 100).toFixed(1)}%)<br>`;
  html += `総レコード数: ${totalRecords.toLocaleString()}件`;
  html += `</div>`;

  const htmlOutput = HtmlService.createHtmlOutput(html)
    .setWidth(800)
    .setHeight(700);

  ui.showModalDialog(htmlOutput, '📊 統計サマリー');
}


// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 全データクリア機能
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

/**
 * 全データクリア（Phase 7以外）
 */
function clearAllData() {
  const ui = SpreadsheetApp.getUi();

  const response = ui.alert(
    '全データクリア',
    '本当に全データをクリアしますか？\n\n※現在、Phase 7以外の全シートが対象です。',
    ui.ButtonSet.YES_NO
  );

  if (response !== ui.Button.YES) {
    ui.alert('キャンセルされました');
    return;
  }

  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheetNames = [
    'Phase1_MapMetrics', 'Phase1_Applicants', 'Phase1_DesiredWork', 'Phase1_AggDesired',
    'Phase2_ChiSquare', 'Phase2_ANOVA',
    'Phase3_PersonaSummary', 'Phase3_PersonaDetails', 'Phase3_PersonaSummaryByMunicipality',
    'Phase6_FlowEdges', 'Phase6_FlowNodes', 'Phase6_Proximity',
    'Phase7_SupplyDensity', 'Phase7_QualificationDist', 'Phase7_AgeGenderCross', 'Phase7_MobilityScore',
    'Phase7_PersonaProfile', 'Phase7_PersonaMapData', 'Phase7_PersonaMobilityCross',
    'Phase8_EducationDist', 'Phase8_EduAgeCross', 'Phase8_EduAgeMatrix', 'Phase8_GradYearDist',
    'Phase8_CareerDistribution', 'Phase8_CareerAgeCross', 'Phase8_CareerAgeMatrix',
    'Phase10_UrgencyDist', 'Phase10_UrgencyAge', 'Phase10_UrgencyAge_Matrix',
    'Phase10_UrgencyEmployment', 'Phase10_UrgencyEmployment_Matrix',
    'Phase10_UrgencyByMunicipality', 'Phase10_UrgencyAge_ByMunicipality', 'Phase10_UrgencyEmployment_ByMunicipality'
  ];

  let deletedCount = 0;
  sheetNames.forEach(function(name) {
    const sheet = ss.getSheetByName(name);
    if (sheet) {
      sheet.clear();
      deletedCount++;
    }
  });

  ui.alert('完了', deletedCount + '個のシートをクリアしました。', ui.ButtonSet.OK);
}


// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// デバッグログ機能
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

/**
 * デバッグログを表示
 */
function showDebugLog() {
  const ui = SpreadsheetApp.getUi();
  const log = Logger.getLog();

  const html = HtmlService.createHtmlOutput(`
    <style>
      body { font-family: 'Courier New', monospace; padding: 20px; background: #1e1e1e; color: #d4d4d4; }
      h3 { color: #569cd6; }
      pre {
        background: #252526;
        padding: 15px;
        border-radius: 5px;
        overflow-x: auto;
        white-space: pre-wrap;
        word-wrap: break-word;
        font-size: 12px;
        line-height: 1.5;
      }
      .empty { color: #858585; font-style: italic; }
      .timestamp { color: #4ec9b0; }
      .error { color: #f48771; }
      .success { color: #4ec9b0; }
    </style>
    <h3>🐛 デバッグログ</h3>
    <pre>${log || '<span class="empty">ログがありません</span>'}</pre>
  `)
  .setWidth(900)
  .setHeight(700);

  ui.showModalDialog(html, '🐛 デバッグログ');
}


// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// カラム分析機能
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

/**
 * DesiredWorkシートのカラム構造を分析
 */
function analyzeDesiredColumns() {
  const ui = SpreadsheetApp.getUi();
  const ss = SpreadsheetApp.getActiveSpreadsheet();

  // DesiredWorkシート分析
  const sheet = ss.getSheetByName('Phase1_DesiredWork');

  if (!sheet) {
    ui.alert(
      'シートなし',
      'Phase1_DesiredWorkシートが見つかりません。\nデータインポートを実行してください。',
      ui.ButtonSet.OK
    );
    return;
  }

  const lastRow = sheet.getLastRow();
  const lastCol = sheet.getLastColumn();

  if (lastRow <= 1) {
    ui.alert(
      'データなし',
      'Phase1_DesiredWorkシートにデータがありません。',
      ui.ButtonSet.OK
    );
    return;
  }

  // ヘッダー取得
  const headers = sheet.getRange(1, 1, 1, lastCol).getValues()[0];

  // サンプルデータ取得（最初の5行）
  const sampleSize = Math.min(5, lastRow - 1);
  const sampleData = sheet.getRange(2, 1, sampleSize, lastCol).getValues();

  // ユニーク値カウント（最大100行サンプリング）
  const analysisSize = Math.min(100, lastRow - 1);
  const analysisData = sheet.getRange(2, 1, analysisSize, lastCol).getValues();

  let html = '<style>' +
    'body { font-family: Arial, sans-serif; padding: 20px; background: #f5f5f5; }' +
    'h3 { color: #1976d2; }' +
    'table { width: 100%; border-collapse: collapse; background: white; margin: 15px 0; }' +
    'th { background: #1976d2; color: white; padding: 12px; text-align: left; }' +
    'td { padding: 10px; border-bottom: 1px solid #ddd; }' +
    'tr:hover { background: #f5f5f5; }' +
    '.summary { background: #e3f2fd; padding: 15px; border-radius: 8px; margin: 15px 0; }' +
    '.code { font-family: monospace; background: #f5f5f5; padding: 2px 6px; border-radius: 3px; }' +
    '</style>';

  html += '<h3>📋 DesiredWork カラム分析</h3>';

  html += '<div class="summary">';
  html += `<strong>基本情報:</strong><br>`;
  html += `総行数: ${(lastRow - 1).toLocaleString()}行（ヘッダー除く）<br>`;
  html += `カラム数: ${lastCol}列<br>`;
  html += `分析対象: ${analysisSize}行（サンプリング）`;
  html += '</div>';

  // カラム詳細テーブル
  html += '<h4>カラム詳細</h4>';
  html += '<table>';
  html += '<tr><th>No.</th><th>カラム名</th><th>ユニーク値数</th><th>サンプル値</th></tr>';

  headers.forEach((header, index) => {
    // ユニーク値カウント
    const uniqueValues = new Set();
    analysisData.forEach(row => {
      const value = row[index];
      if (value !== '' && value !== null && value !== undefined) {
        uniqueValues.add(String(value));
      }
    });

    // サンプル値（最大3件）
    const sampleValues = Array.from(uniqueValues).slice(0, 3);

    html += '<tr>';
    html += `<td>${index + 1}</td>`;
    html += `<td><span class="code">${header || '(空)'}</span></td>`;
    html += `<td>${uniqueValues.size}件</td>`;
    html += `<td>${sampleValues.join(', ') || '(データなし)'}</td>`;
    html += '</tr>';
  });

  html += '</table>';

  const htmlOutput = HtmlService.createHtmlOutput(html)
    .setWidth(900)
    .setHeight(700);

  ui.showModalDialog(htmlOutput, '📋 カラム分析');
}
