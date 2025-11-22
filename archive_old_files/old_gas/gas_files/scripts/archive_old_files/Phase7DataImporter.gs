/**
 * Phase 7データインポート機能
 *
 * Phase 7の7つのCSVファイルをGoogleスプレッドシートにインポートします:
 * 1. SupplyDensityMap.csv - 人材供給密度マップ
 * 2. QualificationDistribution.csv - 資格別人材分布
 * 3. AgeGenderCrossAnalysis.csv - 年齢層×性別クロス分析
 * 4. MobilityScore.csv - 移動許容度スコアリング
 * 5. DetailedPersonaProfile.csv - ペルソナ詳細プロファイル
 * 6. PersonaMobilityCross.csv - ペルソナ×移動許容度クロス分析（GAS改良機能）
 * 7. PersonaMapData.csv - ペルソナ地図データ（座標付き）（GAS改良機能）
 */

/**
 * Phase 7データ一括インポート（メニューから呼び出し）
 */
function importPhase7Data() {
  const ui = SpreadsheetApp.getUi();

  // 確認ダイアログ
  const response = ui.alert(
    'Phase 7データインポート',
    'Phase 7の7つのCSVファイルをインポートしますか？\n\n' +
    '以下のシートが作成/更新されます：\n' +
    '1. Phase7_SupplyDensity\n' +
    '2. Phase7_QualificationDist\n' +
    '3. Phase7_AgeGenderCross\n' +
    '4. Phase7_MobilityScore\n' +
    '5. Phase7_PersonaProfile\n' +
    '6. Phase7_PersonaMobilityCross（GAS改良機能）\n' +
    '7. Phase7_PersonaMapData（GAS改良機能）',
    ui.ButtonSet.YES_NO
  );

  if (response !== ui.Button.YES) {
    ui.alert('キャンセルされました');
    return;
  }

  // インポート実行
  try {
    const results = importAllPhase7Files();

    // 結果表示
    let message = 'Phase 7データインポート完了！\n\n';
    results.forEach(result => {
      if (result.success) {
        message += `✓ ${result.fileName}: ${result.rows}行 × ${result.cols}列\n`;
      } else {
        message += `✗ ${result.fileName}: ${result.error}\n`;
      }
    });

    ui.alert('インポート結果', message, ui.ButtonSet.OK);

  } catch (error) {
    ui.alert('エラー', `インポート中にエラーが発生しました:\n${error.message}`, ui.ButtonSet.OK);
    Logger.log(`Phase 7インポートエラー: ${error.stack}`);
  }
}


/**
 * Phase 7全ファイルインポート（内部関数）
 * @return {Array<Object>} インポート結果の配列
 */
function importAllPhase7Files() {
  const files = [
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
    },
    {
      fileName: 'PersonaMobilityCross.csv',
      sheetName: 'Phase7_PersonaMobilityCross',
      description: 'ペルソナ×移動許容度クロス分析'
    },
    {
      fileName: 'PersonaMapData.csv',
      sheetName: 'Phase7_PersonaMapData',
      description: 'ペルソナ地図データ（座標付き）'
    }
  ];

  const results = [];

  files.forEach(fileInfo => {
    try {
      const result = importPhase7File(fileInfo.fileName, fileInfo.sheetName);
      results.push({
        fileName: fileInfo.fileName,
        sheetName: fileInfo.sheetName,
        description: fileInfo.description,
        success: true,
        rows: result.rows,
        cols: result.cols
      });
      Logger.log(`✓ ${fileInfo.fileName}インポート成功: ${result.rows}行`);
    } catch (error) {
      results.push({
        fileName: fileInfo.fileName,
        sheetName: fileInfo.sheetName,
        description: fileInfo.description,
        success: false,
        error: error.message
      });
      Logger.log(`✗ ${fileInfo.fileName}インポート失敗: ${error.message}`);
    }
  });

  return results;
}


/**
 * 個別Phase 7ファイルインポート
 * @param {string} fileName - CSVファイル名
 * @param {string} sheetName - インポート先シート名
 * @return {Object} インポート結果
 */
function importPhase7File(fileName, sheetName) {
  // 注意: この関数は実際のファイルパスに基づいて実装する必要があります
  // ここではダミー実装を提供します

  // 実装方法1: Google DriveからCSVファイルを読み込む
  // 実装方法2: ユーザーにファイルアップロードを求める
  // 実装方法3: 直接データ配列を受け取る

  // 以下はダミーデータでの実装例
  throw new Error(`${fileName}のインポート機能は未実装です。ファイルパスを設定してください。`);
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
      sheetName: 'Phase7_QualificationDist',
      requiredColumns: ['資格カテゴリ', '総保有者数', '分布TOP3', '希少地域TOP3']
    },
    {
      sheetName: 'Phase7_AgeGenderCross',
      requiredColumns: ['市区町村', '総求職者数', '支配的セグメント', '若年女性比率', '中年女性比率', 'ダイバーシティスコア']
    },
    {
      sheetName: 'Phase7_MobilityScore',
      requiredColumns: ['申請者ID', '希望地数', '最大移動距離km', '移動許容度スコア', '移動許容度レベル', '移動許容度', '居住地']
    },
    {
      sheetName: 'Phase7_PersonaProfile',
      requiredColumns: ['セグメントID', 'ペルソナ名', '人数', '構成比', '平均年齢', '女性比率', '資格保有率', '平均資格数', '平均希望地数', '緊急度', '主要居住地TOP3', '特徴']
    },
    {
      sheetName: 'Phase7_PersonaMobilityCross',
      requiredColumns: ['ペルソナID', 'ペルソナ名', 'A', 'B', 'C', 'D', '合計', 'A比率', 'B比率', 'C比率', 'D比率']
    },
    {
      sheetName: 'Phase7_PersonaMapData',
      requiredColumns: ['市区町村', '緯度', '経度', 'ペルソナID', 'ペルソナ名', '求職者数', '平均年齢', '女性比率', '資格保有率']
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


/**
 * Phase 7データサマリー表示
 */
function showPhase7DataSummary() {
  const ui = SpreadsheetApp.getUi();
  const ss = SpreadsheetApp.getActiveSpreadsheet();

  const sheets = [
    'Phase7_SupplyDensity',
    'Phase7_QualificationDist',
    'Phase7_AgeGenderCross',
    'Phase7_MobilityScore',
    'Phase7_PersonaProfile',
    'Phase7_PersonaMobilityCross',
    'Phase7_PersonaMapData'
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
