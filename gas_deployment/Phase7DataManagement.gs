/**
 * Phase 7データ管理統合ファイル
 *
 * Phase 7関連の全関数を統合し、Phase接頭辞付きシート名に対応しました。
 *
 * 含まれる機能：
 * - Google Drive連携インポート
 * - 一括アップロード
 * - データ検証
 * - データサマリー
 * - クイックスタート
 * - フォルダ管理
 * - データクリア
 *
 * 作成日: 2025-10-30
 * バージョン: 1.0（Phase接頭辞対応版）
 */

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// Google Drive連携インポート機能
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

/**
 * Phase 7自動インポート（メニューから呼び出し）
 */
function autoImportPhase7Data() {
  const ui = SpreadsheetApp.getUi();

  // Google Driveフォルダ選択ダイアログ
  const response = ui.alert(
    'Phase 7自動インポート',
    'Google DriveからPhase 7のCSVファイルを自動検出してインポートします。\n\n' +
    '前提条件:\n' +
    '1. gas_output_phase7フォルダがGoogle Driveにアップロード済み\n' +
    '2. フォルダ内に5つのCSVファイルが存在\n\n' +
    '実行しますか？',
    ui.ButtonSet.YES_NO
  );

  if (response !== ui.Button.YES) {
    ui.alert('キャンセルされました');
    return;
  }

  try {
    // Google Driveからフォルダを検索
    const folderName = 'gas_output_phase7';
    const folder = findFolderByName(folderName);

    if (!folder) {
      ui.alert(
        'フォルダが見つかりません',
        `Google Driveに「${folderName}」フォルダが見つかりません。\n\n` +
        '以下の手順でフォルダをアップロードしてください:\n' +
        '1. Pythonで run_complete.py を実行\n' +
        '2. 生成された gas_output_phase7 フォルダをGoogle Driveにアップロード\n' +
        '3. 再度このメニューを実行',
        ui.ButtonSet.OK
      );
      return;
    }

    // 5つのCSVファイルを自動インポート
    const results = autoImportAllPhase7Files(folder);

    // 結果表示
    let message = 'Phase 7自動インポート完了！\n\n';
    let successCount = 0;
    let failCount = 0;

    results.forEach(result => {
      if (result.success) {
        message += `✓ ${result.fileName}: ${result.rows}行 × ${result.cols}列\n`;
        successCount++;
      } else {
        message += `✗ ${result.fileName}: ${result.error}\n`;
        failCount++;
      }
    });

    message += `\n成功: ${successCount}件 / 失敗: ${failCount}件`;

    ui.alert('インポート結果', message, ui.ButtonSet.OK);

    // 成功した場合はデータ検証も実行
    if (successCount > 0) {
      Utilities.sleep(1000);
      validatePhase7Data();
    }

  } catch (error) {
    ui.alert('エラー', `自動インポート中にエラーが発生しました:\n${error.message}`, ui.ButtonSet.OK);
    Logger.log(`Phase 7自動インポートエラー: ${error.stack}`);
  }
}


/**
 * Google Driveフォルダ検索
 * @param {string} folderName - フォルダ名
 * @return {Folder} Google Driveフォルダオブジェクト
 */
function findFolderByName(folderName) {
  const folders = DriveApp.getFoldersByName(folderName);

  if (folders.hasNext()) {
    const folder = folders.next();
    Logger.log(`フォルダ検出: ${folderName} (ID: ${folder.getId()})`);
    return folder;
  }

  return null;
}


/**
 * Phase 7全ファイル自動インポート
 * @param {Folder} folder - Google Driveフォルダ
 * @return {Array<Object>} インポート結果の配列
 */
function autoImportAllPhase7Files(folder) {
  const fileConfigs = [
    {
      fileName: 'SupplyDensityMap.csv',
      sheetName: 'Phase7_SupplyDensity',
      description: '人材供給密度マップ'
    },
    {
      fileName: 'QualificationDistribution.csv',
      sheetName: 'Phase7_QualDist',
      description: '資格別人材分布'
    },
    {
      fileName: 'AgeGenderCrossAnalysis.csv',
      sheetName: 'Phase7_AgeGender',
      description: '年齢層×性別クロス分析'
    },
    {
      fileName: 'MobilityScore.csv',
      sheetName: 'Phase7_Mobility',
      description: '移動許容度スコアリング'
    },
    {
      fileName: 'DetailedPersonaProfile.csv',
      sheetName: 'Phase7_PersonaProfile',
      description: 'ペルソナ詳細プロファイル'
    }
  ];

  const results = [];

  fileConfigs.forEach(config => {
    try {
      // フォルダ内からCSVファイルを検索
      const file = findFileInFolder(folder, config.fileName);

      if (!file) {
        results.push({
          fileName: config.fileName,
          sheetName: config.sheetName,
          description: config.description,
          success: false,
          error: 'ファイルが見つかりません'
        });
        return;
      }

      // CSVファイルを読み込んでインポート
      const result = importCSVFileToSheet(file, config.sheetName);

      results.push({
        fileName: config.fileName,
        sheetName: config.sheetName,
        description: config.description,
        success: true,
        rows: result.rows,
        cols: result.cols
      });

      Logger.log(`✓ ${config.fileName}インポート成功: ${result.rows}行`);

    } catch (error) {
      results.push({
        fileName: config.fileName,
        sheetName: config.sheetName,
        description: config.description,
        success: false,
        error: error.message
      });
      Logger.log(`✗ ${config.fileName}インポート失敗: ${error.message}`);
    }
  });

  return results;
}


/**
 * フォルダ内のファイル検索
 * @param {Folder} folder - Google Driveフォルダ
 * @param {string} fileName - ファイル名
 * @return {File} Google Driveファイルオブジェクト
 */
function findFileInFolder(folder, fileName) {
  const files = folder.getFilesByName(fileName);

  if (files.hasNext()) {
    const file = files.next();
    Logger.log(`ファイル検出: ${fileName} (ID: ${file.getId()})`);
    return file;
  }

  return null;
}


/**
 * CSVファイルをシートにインポート
 * @param {File} file - Google DriveのCSVファイル
 * @param {string} sheetName - インポート先シート名
 * @return {Object} インポート結果
 */
function importCSVFileToSheet(file, sheetName) {
  // CSVファイル読み込み
  const csvContent = file.getBlob().getDataAsString('UTF-8');

  // BOM除去（UTF-8 BOM対応）
  const cleanedContent = csvContent.replace(/^\uFEFF/, '');

  // CSV解析
  const data = Utilities.parseCsv(cleanedContent);

  if (!data || data.length === 0) {
    throw new Error('CSVファイルが空です');
  }

  // シートにインポート
  return importCSVDataToSheet(data, sheetName);
}


/**
 * CSVデータをシートにインポート（汎用関数）
 * @param {Array<Array>} data - CSV形式の2次元配列
 * @param {string} sheetName - インポート先シート名
 * @return {Object} インポート結果
 */
function importCSVDataToSheet(data, sheetName) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let sheet = ss.getSheetByName(sheetName);

  // シートが存在しない場合は新規作成
  if (!sheet) {
    sheet = ss.insertSheet(sheetName);
    Logger.log(`新規シート作成: ${sheetName}`);
  } else {
    // 既存シートの場合はクリア
    sheet.clear();
    Logger.log(`既存シートクリア: ${sheetName}`);
  }

  // データが空の場合
  if (!data || data.length === 0) {
    throw new Error('インポートするデータが空です');
  }

  // データをシートに書き込み
  const rows = data.length;
  const cols = data[0].length;

  sheet.getRange(1, 1, rows, cols).setValues(data);

  // ヘッダー行のフォーマット
  formatHeaderRow(sheet, cols);

  // 列幅自動調整
  for (let i = 1; i <= cols; i++) {
    sheet.autoResizeColumn(i);
  }

  Logger.log(`データ書き込み完了: ${rows}行 × ${cols}列`);

  return {
    rows: rows,
    cols: cols,
    sheetName: sheetName
  };
}


/**
 * ヘッダー行のフォーマット
 * @param {Sheet} sheet - 対象シート
 * @param {number} cols - 列数
 */
function formatHeaderRow(sheet, cols) {
  const headerRange = sheet.getRange(1, 1, 1, cols);

  headerRange
    .setBackground('#4285F4')
    .setFontColor('#FFFFFF')
    .setFontWeight('bold')
    .setHorizontalAlignment('center');

  // 固定表示
  sheet.setFrozenRows(1);
}


// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// Google Drive管理機能
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

/**
 * Google Driveフォルダパス表示（デバッグ用）
 */
function showGoogleDriveFolderInfo() {
  const ui = SpreadsheetApp.getUi();

  const folderName = 'gas_output_phase7';
  const folder = findFolderByName(folderName);

  if (!folder) {
    ui.alert(
      'フォルダが見つかりません',
      `Google Driveに「${folderName}」フォルダが見つかりません。`,
      ui.ButtonSet.OK
    );
    return;
  }

  // フォルダ内のファイル一覧
  const files = folder.getFiles();
  let fileList = '';
  let fileCount = 0;

  while (files.hasNext()) {
    const file = files.next();
    fileList += `  - ${file.getName()} (${file.getSize()} bytes)\n`;
    fileCount++;
  }

  const message = `フォルダ情報:\n\n` +
    `フォルダ名: ${folder.getName()}\n` +
    `フォルダID: ${folder.getId()}\n` +
    `ファイル数: ${fileCount}件\n\n` +
    `ファイル一覧:\n${fileList}`;

  ui.alert('Google Driveフォルダ情報', message, ui.ButtonSet.OK);
}


/**
 * Phase 7フォルダ作成支援（初回セットアップ）
 */
function createPhase7FolderInDrive() {
  const ui = SpreadsheetApp.getUi();

  const response = ui.alert(
    'Phase 7フォルダ作成',
    'Google Driveに「gas_output_phase7」フォルダを作成しますか？\n\n' +
    '作成後、Pythonで生成したCSVファイルをこのフォルダにアップロードしてください。',
    ui.ButtonSet.YES_NO
  );

  if (response !== ui.Button.YES) {
    ui.alert('キャンセルされました');
    return;
  }

  try {
    // フォルダ作成
    const folder = DriveApp.createFolder('gas_output_phase7');

    ui.alert(
      'フォルダ作成完了',
      `Google Driveに「gas_output_phase7」フォルダを作成しました。\n\n` +
      `フォルダID: ${folder.getId()}\n` +
      `フォルダURL: ${folder.getUrl()}\n\n` +
      `次のステップ:\n` +
      `1. Pythonで run_complete.py を実行\n` +
      `2. 生成された5つのCSVファイルをこのフォルダにアップロード\n` +
      `3. 「Phase 7自動インポート」を実行`,
      ui.ButtonSet.OK
    );

    // フォルダURLをクリップボードにコピー（ブラウザで開く）
    const htmlOutput = HtmlService.createHtmlOutput(`
      <p>フォルダが作成されました。</p>
      <p><a href="${folder.getUrl()}" target="_blank">フォルダを開く</a></p>
      <script>
        window.open('${folder.getUrl()}', '_blank');
        google.script.host.close();
      </script>
    `);

    ui.showModalDialog(htmlOutput, 'フォルダを開く');

  } catch (error) {
    ui.alert('エラー', `フォルダ作成中にエラーが発生しました:\n${error.message}`, ui.ButtonSet.OK);
    Logger.log(`Phase 7フォルダ作成エラー: ${error.stack}`);
  }
}


/**
 * 最新のPhase 7データを自動検出してインポート（ワンクリック版）
 */
function quickImportLatestPhase7Data() {
  const ui = SpreadsheetApp.getUi();

  try {
    // フォルダ検索
    const folder = findFolderByName('gas_output_phase7');

    if (!folder) {
      // フォルダがない場合は作成を提案
      const response = ui.alert(
        'フォルダが見つかりません',
        'Google Driveに「gas_output_phase7」フォルダが見つかりません。\n\n' +
        '今すぐ作成しますか？',
        ui.ButtonSet.YES_NO
      );

      if (response === ui.Button.YES) {
        createPhase7FolderInDrive();
      }
      return;
    }

    // 自動インポート実行
    ui.alert(
      'Phase 7クイックインポート',
      'Phase 7データを自動検出してインポートします。\n\n' +
      '処理中...',
      ui.ButtonSet.OK
    );

    const results = autoImportAllPhase7Files(folder);

    // 結果表示
    const successCount = results.filter(r => r.success).length;
    const totalCount = results.length;

    if (successCount === totalCount) {
      ui.alert(
        '成功！',
        `Phase 7データのインポートが完了しました！\n\n` +
        `${successCount}/${totalCount}ファイルをインポートしました。\n\n` +
        `次のステップ:\n` +
        `メニューから「Phase 7高度分析」の各機能を使用してください。`,
        ui.ButtonSet.OK
      );
    } else {
      let message = `${successCount}/${totalCount}ファイルをインポートしました。\n\n`;
      results.forEach(r => {
        if (!r.success) {
          message += `✗ ${r.fileName}: ${r.error}\n`;
        }
      });
      ui.alert('一部失敗', message, ui.ButtonSet.OK);
    }

  } catch (error) {
    ui.alert('エラー', `クイックインポート中にエラーが発生しました:\n${error.message}`, ui.ButtonSet.OK);
    Logger.log(`Phase 7クイックインポートエラー: ${error.stack}`);
  }
}


// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 一括アップロード機能
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

/**
 * Phase 7一括アップロード（メニューから呼び出し）
 */
function showPhase7BatchUploadDialog() {
  const html = HtmlService.createHtmlOutputFromFile('Phase7Upload')
    .setWidth(950)
    .setHeight(700);

  SpreadsheetApp.getUi().showModalDialog(html, 'Phase 7データ一括アップロード（全7ファイル）');
}


// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// データ検証機能
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

/**
 * Phase 7データ検証
 * 各シートのデータ整合性を検証します
 */
function validatePhase7Data() {
  const ui = SpreadsheetApp.getUi();
  const ss = SpreadsheetApp.getActiveSpreadsheet();

  const validations = [
    {
      sheetName: 'Phase7_SupplyDensity',
      requiredColumns: ['市区町村', '求職者数', '資格保有率', '平均年齢', '緊急度', '総合スコア', 'ランク']
    },
    {
      sheetName: 'Phase7_QualDist',
      requiredColumns: ['資格カテゴリ', '総保有者数', '分布TOP3', '希少地域TOP3']
    },
    {
      sheetName: 'Phase7_AgeGender',
      requiredColumns: ['市区町村', '総求職者数', '支配的セグメント', '若年女性比率', '中年女性比率', 'ダイバーシティスコア']
    },
    {
      sheetName: 'Phase7_Mobility',
      requiredColumns: ['申請者ID', '希望地数', '最大移動距離km', '移動許容度スコア', '移動許容度レベル', '移動許容度', '居住地']
    },
    {
      sheetName: 'Phase7_PersonaProfile',
      requiredColumns: ['セグメントID', 'ペルソナ名', '人数', '構成比', '平均年齢', '女性比率', '資格保有率', '平均資格数', '平均希望地数', '緊急度', '主要居住地TOP3', '特徴']
    }
  ];

  let message = 'Phase 7データ検証結果:\n\n';
  let allValid = true;

  validations.forEach(validation => {
    const sheet = ss.getSheetByName(validation.sheetName);

    if (!sheet) {
      message += `✗ ${validation.sheetName}: シートが見つかりません\n`;
      allValid = false;
      return;
    }

    // データ件数確認
    const lastRow = sheet.getLastRow();
    if (lastRow <= 1) {
      message += `✗ ${validation.sheetName}: データがありません\n`;
      allValid = false;
      return;
    }

    // カラム名確認
    const headers = sheet.getRange(1, 1, 1, validation.requiredColumns.length).getValues()[0];
    const missingColumns = validation.requiredColumns.filter(col => !headers.includes(col));

    if (missingColumns.length > 0) {
      message += `✗ ${validation.sheetName}: 必須カラムが不足 - ${missingColumns.join(', ')}\n`;
      allValid = false;
      return;
    }

    message += `✓ ${validation.sheetName}: OK (${lastRow - 1}行)\n`;
  });

  if (allValid) {
    message += '\n全てのPhase 7データが正常です！';
  } else {
    message += '\nエラーがあります。Phase 7データを再インポートしてください。';
  }

  ui.alert('データ検証結果', message, ui.ButtonSet.OK);
}


// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// データサマリー機能
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

/**
 * Phase 7データサマリー表示
 */
function showPhase7DataSummary() {
  const ui = SpreadsheetApp.getUi();
  const ss = SpreadsheetApp.getActiveSpreadsheet();

  const sheets = [
    'Phase7_SupplyDensity',
    'Phase7_QualDist',
    'Phase7_AgeGender',
    'Phase7_Mobility',
    'Phase7_PersonaProfile'
  ];

  let message = 'Phase 7データサマリー:\n\n';

  sheets.forEach(sheetName => {
    const sheet = ss.getSheetByName(sheetName);

    if (!sheet) {
      message += `${sheetName}: データなし\n`;
      return;
    }

    const lastRow = sheet.getLastRow();
    const lastCol = sheet.getLastColumn();

    message += `${sheetName}:\n`;
    message += `  データ行数: ${lastRow - 1}行\n`;
    message += `  カラム数: ${lastCol}列\n\n`;
  });

  ui.alert('Phase 7データサマリー', message, ui.ButtonSet.OK);
}


/**
 * Phase 7アップロード状況確認
 */
function showPhase7UploadSummary() {
  const ui = SpreadsheetApp.getUi();
  const ss = SpreadsheetApp.getActiveSpreadsheet();

  const expectedSheets = [
    { name: 'Phase7_SupplyDensity', file: 'SupplyDensityMap.csv' },
    { name: 'Phase7_QualDist', file: 'QualificationDistribution.csv' },
    { name: 'Phase7_AgeGender', file: 'AgeGenderCrossAnalysis.csv' },
    { name: 'Phase7_Mobility', file: 'MobilityScore.csv' },
    { name: 'Phase7_PersonaProfile', file: 'DetailedPersonaProfile.csv' }
  ];

  let message = 'Phase 7データアップロード状況:\n\n';
  let uploadedCount = 0;

  expectedSheets.forEach(sheetInfo => {
    const sheet = ss.getSheetByName(sheetInfo.name);
    if (sheet) {
      const rows = sheet.getLastRow();
      const cols = sheet.getLastColumn();
      message += `✓ ${sheetInfo.file}: ${rows}行 × ${cols}列\n`;
      uploadedCount++;
    } else {
      message += `✗ ${sheetInfo.file}: 未アップロード\n`;
    }
  });

  message += `\n完了: ${uploadedCount}/5ファイル`;

  if (uploadedCount === 5) {
    message += '\n\n全ファイルのアップロードが完了しています！';
  } else {
    message += '\n\n未アップロードのファイルがあります。\n「Phase 7データ一括アップロード」から追加してください。';
  }

  ui.alert('Phase 7アップロード状況', message, ui.ButtonSet.OK);
}


// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// クイックスタートガイド
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

/**
 * Phase 7クイックスタートガイド表示
 */
function showPhase7QuickStart() {
  const ui = SpreadsheetApp.getUi();

  const html = HtmlService.createHtmlOutput(`
    <style>
      body { font-family: Arial, sans-serif; padding: 20px; line-height: 1.6; }
      h3 { color: #667eea; }
      .step { background: #f0f0f0; padding: 15px; margin: 10px 0; border-radius: 8px; border-left: 4px solid #667eea; }
      .step-number { font-weight: bold; color: #667eea; }
      code { background: #e0e0e0; padding: 2px 6px; border-radius: 3px; }
    </style>

    <h3>📈 Phase 7 クイックスタート</h3>

    <div class="step">
      <div class="step-number">ステップ 1: Pythonでデータ生成</div>
      <p>ローカル環境で <code>python run_complete.py</code> を実行</p>
      <p>→ <code>data/output_v2/phase7/</code> に6個のCSVファイルが生成されます</p>
    </div>

    <div class="step">
      <div class="step-number">ステップ 2: GASにアップロード</div>
      <p>GASメニュー: <strong>データ処理 → 📥 データインポート → ⚡ CSVファイルを個別アップロード</strong></p>
      <p>Phase 7の6ファイルをアップロードしてください</p>
    </div>

    <div class="step">
      <div class="step-number">ステップ 3: 可視化</div>
      <p>GASメニュー: <strong>データ処理 → 📈 Phase 7: 高度分析 → 🎯 Phase 7統合ダッシュボード</strong></p>
      <p>または個別分析メニューから各種分析を表示</p>
    </div>

    <div class="step">
      <div class="step-number">必要なファイル（6個）</div>
      <ul>
        <li>SupplyDensityMap.csv</li>
        <li>QualificationDistribution.csv</li>
        <li>AgeGenderCrossAnalysis.csv</li>
        <li>MobilityScore.csv</li>
        <li>DetailedPersonaProfile.csv</li>
        <li>QualityReport_Inferential.csv</li>
      </ul>
    </div>

    <p style="margin-top: 20px; padding: 10px; background: #fff3cd; border-radius: 5px;">
      <strong>注意:</strong> Google Drive連携機能は実装準備中のため、
      現在は「⚡ CSVファイルを個別アップロード」のみ利用可能です。
    </p>
  `)
  .setWidth(600)
  .setHeight(600);

  ui.showModalDialog(html, '❓ Phase 7クイックスタート');
}


// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// データクリア機能
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

/**
 * Phase 7全データクリア（デバッグ用）
 */
function clearAllPhase7Data() {
  const ui = SpreadsheetApp.getUi();

  const response = ui.alert(
    'Phase 7データクリア',
    '全てのPhase 7シートを削除しますか？\n' +
    'この操作は取り消せません。',
    ui.ButtonSet.YES_NO
  );

  if (response !== ui.Button.YES) {
    ui.alert('キャンセルされました');
    return;
  }

  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const phase7Sheets = [
    'Phase7_SupplyDensity',
    'Phase7_QualDist',
    'Phase7_AgeGender',
    'Phase7_Mobility',
    'Phase7_PersonaProfile'
  ];

  let deletedCount = 0;

  phase7Sheets.forEach(sheetName => {
    const sheet = ss.getSheetByName(sheetName);
    if (sheet) {
      ss.deleteSheet(sheet);
      deletedCount++;
      Logger.log(`削除: ${sheetName}`);
    }
  });

  ui.alert(
    'クリア完了',
    `${deletedCount}個のPhase 7シートを削除しました。`,
    ui.ButtonSet.OK
  );
}
