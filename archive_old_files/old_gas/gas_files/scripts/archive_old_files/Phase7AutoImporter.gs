/**
 * Phase 7 自動CSVインポート機能（Google Drive連携）
 *
 * Google DriveからPhase 7のCSVファイルを自動検出してインポートします。
 *
 * 使用方法:
 * 1. PythonでCSV生成後、Google Driveの特定フォルダにアップロード
 * 2. GASメニューから「Phase 7自動インポート」を実行
 * 3. 自動的に5つのCSVを検出してシートに取り込み
 */

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
      sheetName: 'Phase7_QualificationDist',
      description: '資格別人材分布'
    },
    {
      fileName: 'AgeGenderCrossAnalysis.csv',
      sheetName: 'Phase7_AgeGenderCross',
      description: '年齢層×性別クロス分析'
    },
    {
      fileName: 'MobilityScore.csv',
      sheetName: 'Phase7_MobilityScore',
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
