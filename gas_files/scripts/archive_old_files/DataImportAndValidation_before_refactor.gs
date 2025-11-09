/**
 * データインポート・検証統合ファイル
 *
 * このファイルには以下のインポート・検証機能がすべて含まれています:
 * 1. Python結果CSVインポート
 * 2. 汎用Phaseアップローダー
 * 3. データ検証機能（7種類）
 */

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 1. Python結果CSVインポート
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

// ===== Python結果の一括インポート =====
function batchImportPythonResults() {
  try {
    var ss = SpreadsheetApp.getActiveSpreadsheet();
    var ssId = ss.getId();
    var ssFile = DriveApp.getFileById(ssId);
    var parents = ssFile.getParents();
    
    if (!parents.hasNext()) {
      throw new Error('スプレッドシートの親フォルダが見つかりません');
    }
    
    var folder = parents.next();
    console.log('検索フォルダ: ' + folder.getName());
    
    var importCount = 0;
    var errors = [];
    
    // 必要なファイルのリスト（37ファイル対応）
    var requiredFiles = [
      // Phase 1: 基本データ（必須）
      {name: 'MapMetrics.csv', sheetName: 'MapMetrics', required: true, phase: 1, subfolder: 'phase1'},
      {name: 'Applicants.csv', sheetName: 'Applicants', required: true, phase: 1, subfolder: 'phase1'},
      {name: 'DesiredWork.csv', sheetName: 'DesiredWork', required: true, phase: 1, subfolder: 'phase1'},
      {name: 'AggDesired.csv', sheetName: 'AggDesired', required: true, phase: 1, subfolder: 'phase1'},
      {name: 'QualityReport.csv', sheetName: 'P1_QualityReport', required: false, phase: 1, subfolder: 'phase1'},
      {name: 'QualityReport_Descriptive.csv', sheetName: 'P1_QualityDesc', required: false, phase: 1, subfolder: 'phase1'},

      // Phase 2: 統計的検定結果
      {name: 'ChiSquareTests.csv', sheetName: 'ChiSquareTests', required: false, phase: 2, subfolder: 'phase2'},
      {name: 'ANOVATests.csv', sheetName: 'ANOVATests', required: false, phase: 2, subfolder: 'phase2'},
      {name: 'QualityReport_Inferential.csv', sheetName: 'P2_QualityInfer', required: false, phase: 2, subfolder: 'phase2'},

      // Phase 3: ペルソナ分析結果
      {name: 'PersonaSummary.csv', sheetName: 'PersonaSummary', required: false, phase: 3, subfolder: 'phase3'},
      {name: 'PersonaDetails.csv', sheetName: 'PersonaDetails', required: false, phase: 3, subfolder: 'phase3'},
      {name: 'QualityReport_Inferential.csv', sheetName: 'P3_QualityInfer', required: false, phase: 3, subfolder: 'phase3'},

      // Phase 6: フロー・近接分析
      {name: 'MunicipalityFlowEdges.csv', sheetName: 'FlowEdges', required: false, phase: 6, subfolder: 'phase6'},
      {name: 'MunicipalityFlowNodes.csv', sheetName: 'FlowNodes', required: false, phase: 6, subfolder: 'phase6'},
      {name: 'ProximityAnalysis.csv', sheetName: 'ProximityAnalysis', required: false, phase: 6, subfolder: 'phase6'},
      {name: 'QualityReport_Inferential.csv', sheetName: 'P6_QualityInfer', required: false, phase: 6, subfolder: 'phase6'},

      // Phase 7: 高度分析
      {name: 'SupplyDensityMap.csv', sheetName: 'P7_SupplyDensity', required: false, phase: 7, subfolder: 'phase7'},
      {name: 'QualificationDistribution.csv', sheetName: 'P7_Qualification', required: false, phase: 7, subfolder: 'phase7'},
      {name: 'AgeGenderCrossAnalysis.csv', sheetName: 'P7_AgeGenderCross', required: false, phase: 7, subfolder: 'phase7'},
      {name: 'MobilityScore.csv', sheetName: 'P7_MobilityScore', required: false, phase: 7, subfolder: 'phase7'},
      {name: 'DetailedPersonaProfile.csv', sheetName: 'P7_PersonaProfile', required: false, phase: 7, subfolder: 'phase7'},
      {name: 'QualityReport_Inferential.csv', sheetName: 'P7_QualityInfer', required: false, phase: 7, subfolder: 'phase7'},

      // Phase 8: キャリア・学歴分析【v2.3: career列使用版】
      {name: 'CareerDistribution.csv', sheetName: 'P8_CareerDist', required: false, phase: 8, subfolder: 'phase8'},  // 🔄 v2.3
      {name: 'CareerAgeCross.csv', sheetName: 'P8_CareerAgeCross', required: false, phase: 8, subfolder: 'phase8'},  // 🔄 v2.3
      {name: 'CareerAgeCross_Matrix.csv', sheetName: 'P8_CareerAgeMatrix', required: false, phase: 8, subfolder: 'phase8'},  // 🔄 v2.3
      {name: 'GraduationYearDistribution.csv', sheetName: 'P8_GradYearDist', required: false, phase: 8, subfolder: 'phase8'},
      {name: 'QualityReport.csv', sheetName: 'P8_QualityReport', required: false, phase: 8, subfolder: 'phase8'},
      {name: 'QualityReport_Inferential.csv', sheetName: 'P8_QualityInfer', required: false, phase: 8, subfolder: 'phase8'},

      // Phase 10: 転職意欲・緊急度分析
      {name: 'UrgencyDistribution.csv', sheetName: 'P10_UrgencyDist', required: false, phase: 10, subfolder: 'phase10'},
      {name: 'UrgencyAgeCross.csv', sheetName: 'P10_UrgencyAge', required: false, phase: 10, subfolder: 'phase10'},
      {name: 'UrgencyAgeCross_Matrix.csv', sheetName: 'P10_UrgencyAgeMatrix', required: false, phase: 10, subfolder: 'phase10'},
      {name: 'UrgencyEmploymentCross.csv', sheetName: 'P10_UrgencyEmp', required: false, phase: 10, subfolder: 'phase10'},
      {name: 'UrgencyEmploymentCross_Matrix.csv', sheetName: 'P10_UrgencyEmpMatrix', required: false, phase: 10, subfolder: 'phase10'},
      {name: 'UrgencyByMunicipality.csv', sheetName: 'P10_UrgencyByMuni', required: false, phase: 10, subfolder: 'phase10'},
      {name: 'UrgencyAgeCross_ByMunicipality.csv', sheetName: 'P10_UrgencyAgeByMuni', required: false, phase: 10, subfolder: 'phase10'},
      {name: 'UrgencyEmploymentCross_ByMunicipality.csv', sheetName: 'P10_UrgencyEmpByMuni', required: false, phase: 10, subfolder: 'phase10'},
      {name: 'QualityReport.csv', sheetName: 'P10_QualityReport', required: false, phase: 10, subfolder: 'phase10'},
      {name: 'QualityReport_Inferential.csv', sheetName: 'P10_QualityInfer', required: false, phase: 10, subfolder: 'phase10'},

      // Root統合品質レポート
      {name: 'OverallQualityReport.csv', sheetName: 'OverallQuality', required: false, phase: 0, subfolder: ''},
      {name: 'OverallQualityReport_Inferential.csv', sheetName: 'OverallQualityInfer', required: false, phase: 0, subfolder: ''}
    ];
    
    // output_v2フォルダを探す
    var output_v2_folder = findFolderByName(folder, 'output_v2');
    if (!output_v2_folder) {
      throw new Error('output_v2フォルダが見つかりません。data/output_v2/ を確認してください。');
    }

    console.log('output_v2フォルダ発見: ' + output_v2_folder.getName());

    // 各ファイルを処理
    requiredFiles.forEach(function(fileInfo) {
      try {
        var file = null;

        // サブフォルダ指定がある場合はそこから探す
        if (fileInfo.subfolder) {
          var subFolder = output_v2_folder.getFoldersByName(fileInfo.subfolder);
          if (subFolder.hasNext()) {
            var targetFolder = subFolder.next();
            var files = targetFolder.getFilesByName(fileInfo.name);
            if (files.hasNext()) {
              file = files.next();
            }
          }
        } else {
          // ルート直下から探す
          var files = output_v2_folder.getFilesByName(fileInfo.name);
          if (files.hasNext()) {
            file = files.next();
          }
        }

        if (!file) {
          if (fileInfo.required) {
            errors.push(fileInfo.name + ' が見つかりません (Phase ' + fileInfo.phase + ')');
          }
          return;
        }

        console.log('処理中: ' + fileInfo.name + ' (Phase ' + fileInfo.phase + ')');
        
        if (fileInfo.name.endsWith('.json')) {
          // JSONファイルの処理
          processJSONFile(file, ss);
        } else {
          // CSVファイルの処理
          processCSVFile(file, ss, fileInfo.sheetName);
        }
        
        importCount++;
        
      } catch (e) {
        errors.push(fileInfo.name + ': ' + e.toString());
      }
    });
    
    // 処理後のデータ整合性チェック（拡張版）
    var validationResults = validateImportedDataEnhanced(ss);

    // 検証結果をログ出力
    Logger.log('データ検証結果: ' + JSON.stringify(validationResults.summary));

    // エラーがある場合は警告を追加
    if (!validationResults.overall) {
      errors.push('⚠️ データ検証で' + validationResults.summary.totalErrors + '件のエラーが検出されました');
    }
    
    if (errors.length > 0) {
      return {
        success: false,
        message: 'インポートに一部エラーがありました:\n' + errors.join('\n')
      };
    }
    
    return {
      success: true,
      message: '✅ ' + importCount + '個のファイルを正常にインポートしました。\n地図表示メニューから可視化できます。'
    };
    
  } catch (e) {
    console.error('バッチインポートエラー:', e);
    return {
      success: false,
      message: 'エラー: ' + e.toString()
    };
  }
}

// ===== CSVファイル処理 =====
function processCSVFile(file, ss, sheetName) {
  // CSVコンテンツを取得
  var content = file.getBlob().getDataAsString('UTF-8');
  
  // BOMを除去
  if (content.charCodeAt(0) === 0xFEFF) {
    content = content.substring(1);
  }
  
  // CSVパース
  var data = Utilities.parseCsv(content);
  
  if (data.length === 0) {
    throw new Error('空のCSVファイル');
  }
  
  // シート作成または取得
  var sheet = ss.getSheetByName(sheetName);
  if (sheet) {
    // 既存シートをクリア
    sheet.clear();
  } else {
    // 新規シート作成
    sheet = ss.insertSheet(sheetName);
  }
  
  // データ書き込み
  sheet.getRange(1, 1, data.length, data[0].length).setValues(data);
  
  // ヘッダー書式設定（1行目がヘッダーと仮定）
  sheet.getRange(1, 1, 1, data[0].length)
    .setBackground('#4285f4')
    .setFontColor('#ffffff')
    .setFontWeight('bold');
  
  // 列幅自動調整
  for (var i = 1; i <= data[0].length; i++) {
    sheet.autoResizeColumn(i);
  }
  
  console.log(sheetName + ': ' + (data.length - 1) + '行をインポート');
}

// ===== JSONファイル処理 =====
function processJSONFile(file, ss) {
  var content = file.getBlob().getDataAsString('UTF-8');
  var data = JSON.parse(content);
  
  // スクリプトプロパティに保存
  var scriptProperties = PropertiesService.getScriptProperties();
  scriptProperties.setProperty('pythonAnalysisData', content);
  
  // キャッシュにも保存
  var cache = CacheService.getScriptCache();
  cache.put('pythonAnalysisData', content, 21600);
  
  // メタデータシート作成
  var metaSheet = ss.getSheetByName('_PythonMetadata') || ss.insertSheet('_PythonMetadata');
  metaSheet.clear();
  
  var metaData = [
    ['項目', '値'],
    ['処理日時', data.metadata.processed_at || ''],
    ['総申請者数', data.metadata.total_applicants || 0],
    ['地点数', data.metadata.total_locations || 0],
    ['データ品質スコア', JSON.stringify(data.metadata.data_quality_score || {})]
  ];
  
  // インサイト情報も追加
  if (data.insights && data.insights.length > 0) {
    metaData.push(['', '']);
    metaData.push(['インサイト', '']);
    data.insights.forEach(function(insight, idx) {
      metaData.push([
        (idx + 1) + '. ' + insight.finding,
        insight.recommendation
      ]);
    });
  }
  
  metaSheet.getRange(1, 1, metaData.length, 2).setValues(metaData);
  metaSheet.getRange(1, 1, 1, 2)
    .setBackground('#4285f4')
    .setFontColor('#ffffff')
    .setFontWeight('bold');
  
  console.log('JSONメタデータを保存');
}

// ===== データ整合性チェック =====
function validateImportedData(ss) {
  var validation = {
    hasMapMetrics: false,
    hasApplicants: false,
    hasDesiredWork: false,
    hasAggDesired: false,
    mapMetricsCount: 0,
    applicantsCount: 0,
    desiredWorkCount: 0
  };
  
  // MapMetrics チェック
  var mapSheet = ss.getSheetByName('MapMetrics');
  if (mapSheet && mapSheet.getLastRow() > 1) {
    validation.hasMapMetrics = true;
    validation.mapMetricsCount = mapSheet.getLastRow() - 1;
    
    // 座標データの存在確認
    var sample = mapSheet.getRange(2, 5, 1, 2).getValues()[0];
    if (!sample[0] || !sample[1]) {
      console.warn('警告: MapMetricsに座標データがありません');
    }
  }
  
  // Applicants チェック
  var appSheet = ss.getSheetByName('Applicants');
  if (appSheet && appSheet.getLastRow() > 1) {
    validation.hasApplicants = true;
    validation.applicantsCount = appSheet.getLastRow() - 1;
  }
  
  // DesiredWork チェック
  var dwSheet = ss.getSheetByName('DesiredWork');
  if (dwSheet && dwSheet.getLastRow() > 1) {
    validation.hasDesiredWork = true;
    validation.desiredWorkCount = dwSheet.getLastRow() - 1;
  }
  
  // AggDesired チェック
  var aggSheet = ss.getSheetByName('AggDesired');
  if (aggSheet && aggSheet.getLastRow() > 1) {
    validation.hasAggDesired = true;
  }
  
  // 検証結果をログ
  console.log('データ検証結果:', validation);
  
  // 問題がある場合は警告
  if (!validation.hasMapMetrics) {
    throw new Error('MapMetricsデータが不足しています');
  }
  
  return validation;
}

// ===== Pythonレポート表示 =====
function showPythonReport() {
  var scriptProperties = PropertiesService.getScriptProperties();
  var jsonData = scriptProperties.getProperty('pythonAnalysisData');
  
  if (!jsonData) {
    SpreadsheetApp.getUi().alert('Python分析データがありません。先にインポートしてください。');
    return;
  }
  
  var data = JSON.parse(jsonData);
  
  var html = HtmlService.createHtmlOutput(`
    <style>
      body { font-family: Arial, sans-serif; padding: 20px; }
      h2 { color: #4285f4; }
      .stat-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; margin: 20px 0; }
      .stat-card { padding: 15px; background: #f5f5f5; border-radius: 8px; }
      .stat-value { font-size: 24px; font-weight: bold; color: #4285f4; }
      .stat-label { font-size: 12px; color: #666; margin-top: 5px; }
      .insight { margin: 10px 0; padding: 10px; background: #e3f2fd; border-radius: 4px; }
      .button { background: #4285f4; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
    </style>
    
    <h2>📊 Python分析レポート</h2>
    
    <div class="stat-grid">
      <div class="stat-card">
        <div class="stat-value">${data.metadata.total_applicants || 0}</div>
        <div class="stat-label">総申請者数</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">${data.metadata.total_locations || 0}</div>
        <div class="stat-label">地点数</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">${data.demographics ? data.demographics.average_age.toFixed(1) : '-'}</div>
        <div class="stat-label">平均年齢</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">${data.cluster_info ? data.cluster_info.n_clusters : '-'}</div>
        <div class="stat-label">クラスタ数</div>
      </div>
    </div>
    
    <h3>💡 インサイト</h3>
    ${data.insights ? data.insights.map(i => 
      `<div class="insight">
        <strong>${i.finding}</strong><br>
        ${i.detail}<br>
        <em>提案: ${i.recommendation}</em>
      </div>`
    ).join('') : '<p>インサイトがありません</p>'}
    
    <div style="text-align: center; margin-top: 30px;">
      <button class="button" onclick="google.script.host.close()">閉じる</button>
    </div>
  `)
  .setWidth(600)
  .setHeight(600);
  
  SpreadsheetApp.getUi().showModalDialog(html, 'Python分析レポート');
}

// ===== フォルダ検索ヘルパー関数 =====
function findFolderByName(parentFolder, folderName) {
  /**
   * 親フォルダ内を再帰的に検索して指定名のフォルダを探す
   *
   * @param {Folder} parentFolder - 検索開始フォルダ
   * @param {string} folderName - 検索するフォルダ名
   * @return {Folder|null} - 見つかったフォルダ、またはnull
   */

  // 直下を検索
  var folders = parentFolder.getFoldersByName(folderName);
  if (folders.hasNext()) {
    return folders.next();
  }

  // サブフォルダを再帰的に検索（最大深度3）
  var allFolders = parentFolder.getFolders();
  while (allFolders.hasNext()) {
    var subFolder = allFolders.next();
    var found = subFolder.getFoldersByName(folderName);
    if (found.hasNext()) {
      return found.next();
    }
  }

  return null;
}

// ===== 単一CSVファイルの直接インポート =====
function importSinglePythonCSV(fileName) {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var ssFile = DriveApp.getFileById(ss.getId());
  var folder = ssFile.getParents().next();

  var files = folder.getFilesByName(fileName);
  if (!files.hasNext()) {
    throw new Error(fileName + ' が見つかりません');
  }

  var file = files.next();

  // ファイル名からシート名を決定
  var sheetNameMap = {
    'MapMetrics.csv': 'MapMetrics',
    'Applicants.csv': 'Applicants',
    'DesiredWork.csv': 'DesiredWork',
    'AggDesired.csv': 'AggDesired',
    'processed_data.csv': 'ProcessedData'
  };

  var sheetName = sheetNameMap[fileName] || fileName.replace('.csv', '');

  processCSVFile(file, ss, sheetName);

  return {
    success: true,
    message: fileName + ' をインポートしました'
  };
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 2. 汎用Phaseアップローダー
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

/**
 * Phase別ファイル定義
 */
const PHASE_CONFIGS = {
  'phase1': {
    name: 'Phase 1: 基礎集計',
    icon: '📍',
    files: [
      { name: 'MapMetrics.csv', sheetName: 'MapMetrics', label: '地図メトリクス' },
      { name: 'Applicants.csv', sheetName: 'Applicants', label: '応募者情報' },
      { name: 'DesiredWork.csv', sheetName: 'DesiredWork', label: '希望勤務地' },
      { name: 'AggDesired.csv', sheetName: 'AggDesired', label: '集計データ' }
    ]
  },
  'phase2': {
    name: 'Phase 2: 統計分析',
    icon: '📊',
    files: [
      { name: 'ChiSquareTests.csv', sheetName: 'ChiSquareTests', label: 'カイ二乗検定' },
      { name: 'ANOVATests.csv', sheetName: 'ANOVATests', label: 'ANOVA検定' }
    ]
  },
  'phase3': {
    name: 'Phase 3: ペルソナ分析',
    icon: '👥',
    files: [
      { name: 'PersonaSummary.csv', sheetName: 'PersonaSummary', label: 'ペルソナサマリー' },
      { name: 'PersonaDetails.csv', sheetName: 'PersonaDetails', label: 'ペルソナ詳細' }
    ]
  },
  'phase6': {
    name: 'Phase 6: フロー分析',
    icon: '🌊',
    files: [
      { name: 'MunicipalityFlowEdges.csv', sheetName: 'MunicipalityFlowEdges', label: 'フローエッジ' },
      { name: 'MunicipalityFlowNodes.csv', sheetName: 'MunicipalityFlowNodes', label: 'フローノード' },
      { name: 'ProximityAnalysis.csv', sheetName: 'ProximityAnalysis', label: '移動パターン分析' }
    ]
  },
  'phase7': {
    name: 'Phase 7: 高度分析',
    icon: '📈',
    files: [
      { name: 'SupplyDensityMap.csv', sheetName: 'Phase7_SupplyDensity', label: '人材供給密度' },
      { name: 'QualificationDistribution.csv', sheetName: 'Phase7_QualificationDist', label: '資格分布' },
      { name: 'AgeGenderCrossAnalysis.csv', sheetName: 'Phase7_AgeGenderCross', label: '年齢×性別' },
      { name: 'MobilityScore.csv', sheetName: 'Phase7_MobilityScore', label: '移動許容度' },
      { name: 'DetailedPersonaProfile.csv', sheetName: 'Phase7_PersonaProfile', label: 'ペルソナ詳細' },
      { name: 'PersonaMapData.csv', sheetName: 'Phase7_PersonaMapData', label: 'ペルソナ地図' },
      { name: 'PersonaMobilityCross.csv', sheetName: 'Phase7_PersonaMobilityCross', label: 'ペルソナ×移動' }
    ]
  }
};

/**
 * Phase別アップロードダイアログを表示
 * @param {string} phaseId - Phase ID (phase1, phase2, phase3, phase6, phase7)
 */
function showPhaseUploadDialog(phaseId) {
  const config = PHASE_CONFIGS[phaseId];

  if (!config) {
    SpreadsheetApp.getUi().alert('エラー', `無効なPhase ID: ${phaseId}`, SpreadsheetApp.getUi().ButtonSet.OK);
    return;
  }

  const html = HtmlService.createTemplateFromFile('PhaseUpload');
  html.phaseId = phaseId;
  html.phaseName = config.name;
  html.phaseIcon = config.icon;
  html.files = JSON.stringify(config.files);

  const output = html.evaluate()
    .setWidth(1000)
    .setHeight(700);

  SpreadsheetApp.getUi().showModalDialog(output, `${config.icon} ${config.name} - データアップロード`);
}

/**
 * Phase別設定を取得（HTML側から呼び出し）
 * @param {string} phaseId - Phase ID
 * @return {Object} Phase設定
 */
function getPhaseConfig(phaseId) {
  return PHASE_CONFIGS[phaseId];
}

/**
 * CSVファイルをシートにインポート（HTML UIから呼び出し）
 * @param {string} sheetName - シート名
 * @param {Array<Array>} csvData - CSVデータ（2次元配列）
 * @return {Object} インポート結果
 */
function importCSVToSheet(sheetName, csvData) {
  try {
    const ss = SpreadsheetApp.getActiveSpreadsheet();

    // 既存シートを削除（存在する場合）
    let sheet = ss.getSheetByName(sheetName);
    if (sheet) {
      ss.deleteSheet(sheet);
      Logger.log(`既存シート削除: ${sheetName}`);
    }

    // 新規シート作成
    sheet = ss.insertSheet(sheetName);
    Logger.log(`新規シート作成: ${sheetName}`);

    // データを書き込み
    const rows = csvData.length;
    const cols = csvData[0].length;

    sheet.getRange(1, 1, rows, cols).setValues(csvData);

    // ヘッダー行を太字にフォーマット
    sheet.getRange(1, 1, 1, cols)
      .setFontWeight('bold')
      .setBackground('#f3f3f3');

    // 列幅を自動調整
    for (let i = 1; i <= cols; i++) {
      sheet.autoResizeColumn(i);
    }

    // シートを先頭に移動
    ss.setActiveSheet(sheet);
    ss.moveActiveSheet(1);

    Logger.log(`CSV直接インポート完了: ${sheetName} (${rows}行 × ${cols}列)`);

    return {
      success: true,
      sheetName: sheetName,
      rows: rows,
      cols: cols
    };

  } catch (error) {
    Logger.log(`CSV直接インポートエラー: ${error.message}`);
    throw error;
  }
}

/**
 * Phase別アップロード状況確認
 * @param {string} phaseId - Phase ID
 */
function showPhaseUploadStatus(phaseId) {
  const ui = SpreadsheetApp.getUi();
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const config = PHASE_CONFIGS[phaseId];

  if (!config) {
    ui.alert('エラー', `無効なPhase ID: ${phaseId}`, ui.ButtonSet.OK);
    return;
  }

  let message = `${config.icon} ${config.name} - アップロード状況:\n\n`;
  let uploadedCount = 0;

  config.files.forEach(fileInfo => {
    const sheet = ss.getSheetByName(fileInfo.sheetName);
    if (sheet) {
      const rows = sheet.getLastRow();
      const cols = sheet.getLastColumn();
      message += `✓ ${fileInfo.label}: ${rows}行 × ${cols}列\n`;
      uploadedCount++;
    } else {
      message += `✗ ${fileInfo.label}: 未アップロード\n`;
    }
  });

  message += `\n完了: ${uploadedCount}/${config.files.length}ファイル`;

  if (uploadedCount === config.files.length) {
    message += '\n\n全ファイルのアップロードが完了しています！';
  } else {
    message += `\n\n未アップロードのファイルがあります。\n「${config.icon} ${config.name} - データアップロード」から追加してください。`;
  }

  ui.alert(`${config.name} アップロード状況`, message, ui.ButtonSet.OK);
}

/**
 * 全Phaseアップロード状況確認
 */
function showAllPhasesUploadStatus() {
  const ui = SpreadsheetApp.getUi();
  const ss = SpreadsheetApp.getActiveSpreadsheet();

  let message = '全Phaseアップロード状況:\n\n';
  let totalFiles = 0;
  let totalUploaded = 0;

  Object.keys(PHASE_CONFIGS).forEach(phaseId => {
    const config = PHASE_CONFIGS[phaseId];
    let phaseUploaded = 0;

    config.files.forEach(fileInfo => {
      const sheet = ss.getSheetByName(fileInfo.sheetName);
      if (sheet) {
        phaseUploaded++;
      }
      totalFiles++;
    });

    totalUploaded += phaseUploaded;
    const status = phaseUploaded === config.files.length ? '✅' : '⚠️';
    message += `${status} ${config.icon} ${config.name}: ${phaseUploaded}/${config.files.length}\n`;
  });

  message += `\n合計: ${totalUploaded}/${totalFiles}ファイル`;

  if (totalUploaded === totalFiles) {
    message += '\n\n🎉 全Phaseのアップロードが完了しています！';
  } else {
    message += '\n\n未完了のPhaseがあります。各Phaseのアップロード機能をご利用ください。';
  }

  ui.alert('全Phaseアップロード状況', message, ui.ButtonSet.OK);
}


// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 3. データ検証機能（7種類）
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

// ===== 期待カラム数定義 =====
var EXPECTED_COLUMNS = {
  'MapMetrics': 6,        // 都道府県, 市区町村, キー, カウント, 緯度, 経度
  'Applicants': 21,       // processed_data_complete.csvの全カラム
  'DesiredWork': 4,       // 希望勤務地関連
  'AggDesired': 4,        // 集計データ
  'ChiSquareTests': 11,   // カイ二乗検定結果
  'ANOVATests': 12,       // ANOVA検定結果
  'PersonaSummary': 10,   // ペルソナサマリー
  'PersonaDetails': 5,    // ペルソナ詳細
  'FlowEdges': 3,         // フローエッジ
  'FlowNodes': 5,         // フローノード
  'ProximityAnalysis': 4  // 近接性分析（最小カラム数）
};

// ===== データ型定義 =====
var COLUMN_TYPES = {
  'MapMetrics': {
    1: 'string',   // 都道府県
    2: 'string',   // 市区町村
    3: 'string',   // キー
    4: 'number',   // カウント
    5: 'number',   // 緯度
    6: 'number'    // 経度
  },
  'AggDesired': {
    1: 'string',   // 都道府県
    2: 'string',   // 市区町村
    3: 'string',   // キー
    4: 'number'    // カウント
  },
  'FlowEdges': {
    1: 'string',   // Source
    2: 'string',   // Target
    3: 'number'    // Count
  }
};

// ===== 1. データ型検証 =====
function validateDataTypes(sheet, sheetName) {
  var errors = [];

  if (!COLUMN_TYPES[sheetName]) {
    // データ型定義がないシートはスキップ
    return { valid: true, errors: [] };
  }

  var columnTypes = COLUMN_TYPES[sheetName];
  var lastRow = sheet.getLastRow();

  if (lastRow <= 1) {
    return { valid: true, errors: [] };
  }

  var data = sheet.getRange(2, 1, lastRow - 1, sheet.getLastColumn()).getValues();

  for (var i = 0; i < data.length; i++) {
    for (var col in columnTypes) {
      var colIndex = parseInt(col) - 1;
      var expectedType = columnTypes[col];
      var value = data[i][colIndex];

      // 空セルはスキップ
      if (value === '' || value === null || value === undefined) {
        continue;
      }

      if (expectedType === 'number') {
        if (typeof value !== 'number' || isNaN(value)) {
          errors.push(`行${i + 2}, 列${col}: 数値が期待されますが "${value}" が検出されました`);

          // エラー数が多すぎる場合は途中で打ち切り
          if (errors.length >= 10) {
            errors.push(`... 他にも${data.length - i - 1}行の検証が残っています`);
            break;
          }
        }
      } else if (expectedType === 'string') {
        if (typeof value !== 'string') {
          // 数値などが入っている場合は文字列に変換可能なのでwarning扱い
          Logger.log(`[WARNING] 行${i + 2}, 列${col}: 文字列が期待されますが ${typeof value} 型です`);
        }
      }
    }

    if (errors.length >= 10) break;
  }

  return {
    valid: errors.length === 0,
    errors: errors
  };
}

// ===== 2. 座標範囲検証 =====
function validateCoordinates(sheet) {
  var errors = [];
  var lastRow = sheet.getLastRow();

  if (lastRow <= 1) {
    return { valid: true, errors: [] };
  }

  // 緯度: 列5, 経度: 列6
  var data = sheet.getRange(2, 5, lastRow - 1, 2).getValues();

  for (var i = 0; i < data.length; i++) {
    var lat = data[i][0];
    var lng = data[i][1];

    // 空セルはスキップ
    if (lat === '' || lng === '') {
      continue;
    }

    // 日本の座標範囲: 緯度 20-46, 経度 122-154
    if (lat < 20 || lat > 46) {
      errors.push(`行${i + 2}: 緯度が範囲外です (${lat}度)`);
    }

    if (lng < 122 || lng > 154) {
      errors.push(`行${i + 2}: 経度が範囲外です (${lng}度)`);
    }

    // エラー数制限
    if (errors.length >= 10) {
      errors.push('... 他にも座標エラーがある可能性があります');
      break;
    }
  }

  return {
    valid: errors.length === 0,
    errors: errors,
    warnings: errors.length > 0 ? ['一部の座標が日本国外を指しています'] : []
  };
}

// ===== 3. カラム数検証 =====
function validateColumnCount(sheet, sheetName) {
  var expected = EXPECTED_COLUMNS[sheetName];

  if (!expected) {
    // 定義がないシートはスキップ
    return { valid: true, errors: [] };
  }

  var actual = sheet.getLastColumn();

  if (sheetName === 'ProximityAnalysis') {
    // ProximityAnalysisは動的カラムなので最小値のみチェック
    if (actual < expected) {
      return {
        valid: false,
        errors: [`${sheetName}: 最低${expected}列必要ですが${actual}列しかありません`]
      };
    }
    return { valid: true, errors: [] };
  }

  if (actual !== expected) {
    return {
      valid: false,
      errors: [`${sheetName}: 期待${expected}列ですが実際は${actual}列です`]
    };
  }

  return { valid: true, errors: [] };
}

// ===== 4. 重複キー検出 =====
function detectDuplicateKeys(sheet, keyColumn, sheetName) {
  var lastRow = sheet.getLastRow();

  if (lastRow <= 1) {
    return { valid: true, duplicates: [] };
  }

  var data = sheet.getRange(2, keyColumn, lastRow - 1, 1).getValues();
  var keys = {};
  var duplicates = [];

  for (var i = 0; i < data.length; i++) {
    var key = data[i][0];

    if (key === '' || key === null) {
      continue;
    }

    if (keys[key]) {
      duplicates.push({
        key: key,
        firstRow: keys[key],
        duplicateRow: i + 2
      });
    } else {
      keys[key] = i + 2;
    }

    // 重複が多すぎる場合は途中で打ち切り
    if (duplicates.length >= 20) {
      break;
    }
  }

  return {
    valid: duplicates.length === 0,
    duplicates: duplicates,
    totalUnique: Object.keys(keys).length,
    totalRows: data.length
  };
}

// ===== 5. 集計値整合性チェック =====
function validateAggregation(ss) {
  var errors = [];
  var warnings = [];

  var mapMetrics = ss.getSheetByName('MapMetrics');
  var aggDesired = ss.getSheetByName('AggDesired');

  if (!mapMetrics || !aggDesired) {
    return {
      valid: true,
      errors: [],
      warnings: ['MapMetricsまたはAggDesiredが存在しないため集計値チェックをスキップ']
    };
  }

  // MapMetricsの総カウント
  var mapData = mapMetrics.getRange(2, 4, mapMetrics.getLastRow() - 1, 1).getValues();
  var mapTotal = 0;
  for (var i = 0; i < mapData.length; i++) {
    mapTotal += Number(mapData[i][0]) || 0;
  }

  // AggDesiredの総カウント
  var aggData = aggDesired.getRange(2, 4, aggDesired.getLastRow() - 1, 1).getValues();
  var aggTotal = 0;
  for (var i = 0; i < aggData.length; i++) {
    aggTotal += Number(aggData[i][0]) || 0;
  }

  // 許容誤差5%
  var tolerance = Math.max(mapTotal, aggTotal) * 0.05;
  var diff = Math.abs(mapTotal - aggTotal);

  if (diff > tolerance) {
    errors.push(
      `集計値の不一致が検出されました: ` +
      `MapMetrics合計=${mapTotal}, AggDesired合計=${aggTotal}, ` +
      `差分=${diff} (許容誤差: ${tolerance.toFixed(0)})`
    );
  } else if (diff > 0) {
    warnings.push(
      `集計値にわずかな差があります（許容範囲内）: ` +
      `MapMetrics=${mapTotal}, AggDesired=${aggTotal}, 差分=${diff}`
    );
  }

  return {
    valid: errors.length === 0,
    errors: errors,
    warnings: warnings,
    mapTotal: mapTotal,
    aggTotal: aggTotal,
    difference: diff
  };
}

// ===== 6. 外部キー整合性チェック =====
function validateForeignKeys(ss) {
  var errors = [];
  var warnings = [];

  var applicants = ss.getSheetByName('Applicants');
  var mapMetrics = ss.getSheetByName('MapMetrics');

  if (!applicants || !mapMetrics) {
    return {
      valid: true,
      errors: [],
      warnings: ['ApplicantsまたはMapMetricsが存在しないため外部キーチェックをスキップ']
    };
  }

  // MapMetricsの地点リスト作成
  var locations = {};
  var mapData = mapMetrics.getRange(2, 3, mapMetrics.getLastRow() - 1, 1).getValues();

  for (var i = 0; i < mapData.length; i++) {
    var location = String(mapData[i][0]);
    if (location) {
      locations[location] = true;
    }
  }

  Logger.log(`MapMetrics地点数: ${Object.keys(locations).length}`);

  // Applicantsの希望勤務地をチェック（サンプリング: 最初の100件）
  var sampleSize = Math.min(100, applicants.getLastRow() - 1);

  if (sampleSize > 0) {
    // desired_locationsカラムを探す（カラム11付近）
    var headers = applicants.getRange(1, 1, 1, applicants.getLastColumn()).getValues()[0];
    var desiredLocCol = -1;

    for (var i = 0; i < headers.length; i++) {
      if (headers[i] === 'desired_locations' || headers[i] === 'primary_desired_location') {
        desiredLocCol = i + 1;
        break;
      }
    }

    if (desiredLocCol > 0) {
      var appData = applicants.getRange(2, desiredLocCol, sampleSize, 1).getValues();
      var missingCount = 0;

      for (var i = 0; i < appData.length; i++) {
        var desiredLoc = String(appData[i][0]);

        if (desiredLoc && desiredLoc !== '' && !locations[desiredLoc]) {
          missingCount++;

          if (errors.length < 5) {
            errors.push(`行${i + 2}: 希望勤務地 "${desiredLoc}" がMapMetricsに存在しません`);
          }
        }
      }

      if (missingCount > 5) {
        warnings.push(`合計${missingCount}件の希望勤務地がMapMetricsに存在しません（サンプル${sampleSize}件中）`);
      }
    } else {
      warnings.push('Applicantsシートにdesired_locationsカラムが見つかりません');
    }
  }

  return {
    valid: errors.length === 0,
    errors: errors,
    warnings: warnings
  };
}

// ===== 7. 区レベル粒度確認 =====
function validateWardLevelGranularity(sheet) {
  var warnings = [];
  var stats = {
    totalRecords: 0,
    cityOnly: 0,
    wardLevel: 0,
    prefectureOnly: 0
  };

  var lastRow = sheet.getLastRow();
  if (lastRow <= 1) {
    return { valid: true, stats: stats, warnings: [] };
  }

  // キー列（列3）をチェック
  var data = sheet.getRange(2, 3, lastRow - 1, 1).getValues();
  stats.totalRecords = data.length;

  for (var i = 0; i < data.length; i++) {
    var key = String(data[i][0]);

    if (!key) continue;

    // 区レベル検出: 「〇〇市〇〇区」
    if (key.match(/市.+区$/)) {
      stats.wardLevel++;
    }
    // 市のみ: 「〇〇市」（その後に区がない）
    else if (key.match(/市$/) && !key.match(/市.+区$/)) {
      stats.cityOnly++;
    }
    // 都道府県のみ
    else if (key.match(/^.+[都道府県]$/)) {
      stats.prefectureOnly++;
    }
  }

  // 混在チェック: 同一都市で区レベルと市レベルが混在している場合
  var cityKeys = {};
  for (var i = 0; i < data.length; i++) {
    var key = String(data[i][0]);

    var cityMatch = key.match(/(.+市)/);
    if (cityMatch) {
      var city = cityMatch[1];

      if (!cityKeys[city]) {
        cityKeys[city] = { hasWard: false, hasCity: false };
      }

      if (key.match(/市.+区$/)) {
        cityKeys[city].hasWard = true;
      } else if (key === city || key === cityMatch[0]) {
        cityKeys[city].hasCity = true;
      }
    }
  }

  // 混在している都市を検出
  var mixedCities = [];
  for (var city in cityKeys) {
    if (cityKeys[city].hasWard && cityKeys[city].hasCity) {
      mixedCities.push(city);
    }
  }

  if (mixedCities.length > 0) {
    warnings.push(
      `区レベルと市レベルが混在している都市: ${mixedCities.slice(0, 5).join(', ')}` +
      (mixedCities.length > 5 ? ` 他${mixedCities.length - 5}都市` : '')
    );
  }

  return {
    valid: true,  // これは警告のみでエラーではない
    stats: stats,
    warnings: warnings,
    mixedCities: mixedCities
  };
}

// ===== 8. 拡張版validateImportedData =====
function validateImportedDataEnhanced(ss) {
  var results = {
    overall: true,
    timestamp: new Date(),
    checks: {}
  };

  var allErrors = [];
  var allWarnings = [];

  // MapMetrics検証
  var mapSheet = ss.getSheetByName('MapMetrics');
  if (mapSheet && mapSheet.getLastRow() > 1) {
    Logger.log('MapMetrics検証開始...');

    // カラム数チェック
    var colCheck = validateColumnCount(mapSheet, 'MapMetrics');
    results.checks.mapMetricsColumns = colCheck;
    if (!colCheck.valid) {
      allErrors = allErrors.concat(colCheck.errors);
      results.overall = false;
    }

    // データ型チェック
    var typeCheck = validateDataTypes(mapSheet, 'MapMetrics');
    results.checks.mapMetricsTypes = typeCheck;
    if (!typeCheck.valid) {
      allErrors = allErrors.concat(typeCheck.errors);
      results.overall = false;
    }

    // 座標範囲チェック
    var coordCheck = validateCoordinates(mapSheet);
    results.checks.mapMetricsCoordinates = coordCheck;
    if (!coordCheck.valid) {
      allErrors = allErrors.concat(coordCheck.errors);
      results.overall = false;
    }
    if (coordCheck.warnings) {
      allWarnings = allWarnings.concat(coordCheck.warnings);
    }

    // 重複キーチェック
    var dupCheck = detectDuplicateKeys(mapSheet, 3, 'MapMetrics');
    results.checks.mapMetricsDuplicates = dupCheck;
    if (!dupCheck.valid) {
      allWarnings.push(`MapMetricsに${dupCheck.duplicates.length}件の重複キーがあります`);
    }

    // 区レベル粒度チェック
    var wardCheck = validateWardLevelGranularity(mapSheet);
    results.checks.mapMetricsWardLevel = wardCheck;
    if (wardCheck.warnings.length > 0) {
      allWarnings = allWarnings.concat(wardCheck.warnings);
    }

    Logger.log('MapMetrics検証完了');
  }

  // AggDesired検証
  var aggSheet = ss.getSheetByName('AggDesired');
  if (aggSheet && aggSheet.getLastRow() > 1) {
    Logger.log('AggDesired検証開始...');

    var aggColCheck = validateColumnCount(aggSheet, 'AggDesired');
    results.checks.aggDesiredColumns = aggColCheck;
    if (!aggColCheck.valid) {
      allErrors = allErrors.concat(aggColCheck.errors);
      results.overall = false;
    }

    var aggTypeCheck = validateDataTypes(aggSheet, 'AggDesired');
    results.checks.aggDesiredTypes = aggTypeCheck;
    if (!aggTypeCheck.valid) {
      allErrors = allErrors.concat(aggTypeCheck.errors);
      results.overall = false;
    }

    Logger.log('AggDesired検証完了');
  }

  // 集計値整合性チェック
  Logger.log('集計値整合性チェック開始...');
  var aggCheck = validateAggregation(ss);
  results.checks.aggregation = aggCheck;
  if (!aggCheck.valid) {
    allErrors = allErrors.concat(aggCheck.errors);
    results.overall = false;
  }
  if (aggCheck.warnings) {
    allWarnings = allWarnings.concat(aggCheck.warnings);
  }
  Logger.log('集計値整合性チェック完了');

  // 外部キー整合性チェック
  Logger.log('外部キー整合性チェック開始...');
  var fkCheck = validateForeignKeys(ss);
  results.checks.foreignKeys = fkCheck;
  if (!fkCheck.valid) {
    allErrors = allErrors.concat(fkCheck.errors);
    results.overall = false;
  }
  if (fkCheck.warnings) {
    allWarnings = allWarnings.concat(fkCheck.warnings);
  }
  Logger.log('外部キー整合性チェック完了');

  // サマリー
  results.summary = {
    totalErrors: allErrors.length,
    totalWarnings: allWarnings.length,
    errors: allErrors,
    warnings: allWarnings
  };

  return results;
}

// ===== 検証レポート表示 =====
function showValidationReport() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var results = validateImportedDataEnhanced(ss);

  var html = '<style>' +
    'body { font-family: Arial, sans-serif; padding: 20px; background: #f5f5f5; }' +
    'h2 { color: #1976d2; }' +
    '.summary { background: #e3f2fd; padding: 15px; border-radius: 8px; margin: 20px 0; }' +
    '.success { background: #c8e6c9; color: #2e7d32; padding: 15px; border-radius: 8px; }' +
    '.error { background: #ffcdd2; color: #c62828; padding: 15px; border-radius: 8px; margin: 10px 0; }' +
    '.warning { background: #fff3e0; color: #f57c00; padding: 15px; border-radius: 8px; margin: 10px 0; }' +
    '.check-item { background: white; padding: 15px; margin: 10px 0; border-radius: 4px; }' +
    '.check-title { font-weight: bold; color: #333; margin-bottom: 10px; }' +
    'ul { margin: 5px 0; padding-left: 20px; }' +
    '</style>';

  html += '<h2>🔍 データ検証レポート</h2>';

  html += '<div class="summary">' +
    '<strong>検証実施日時:</strong> ' + results.timestamp.toLocaleString('ja-JP') + '<br>' +
    '<strong>総合判定:</strong> ' + (results.overall ? '✅ 合格' : '❌ 不合格') + '<br>' +
    '<strong>エラー数:</strong> ' + results.summary.totalErrors + '<br>' +
    '<strong>警告数:</strong> ' + results.summary.totalWarnings +
    '</div>';

  if (results.overall && results.summary.totalWarnings === 0) {
    html += '<div class="success">🎉 すべての検証項目をクリアしました！データ品質: 100/100</div>';
  }

  if (results.summary.totalErrors > 0) {
    html += '<div class="error">' +
      '<strong>❌ エラー（修正必須）:</strong><ul>';
    results.summary.errors.forEach(function(err) {
      html += '<li>' + err + '</li>';
    });
    html += '</ul></div>';
  }

  if (results.summary.totalWarnings > 0) {
    html += '<div class="warning">' +
      '<strong>⚠️ 警告（確認推奨）:</strong><ul>';
    results.summary.warnings.forEach(function(warn) {
      html += '<li>' + warn + '</li>';
    });
    html += '</ul></div>';
  }

  // 詳細チェック結果
  html += '<h3>詳細チェック結果</h3>';

  for (var checkName in results.checks) {
    var check = results.checks[checkName];
    var icon = check.valid ? '✅' : '❌';

    html += '<div class="check-item">' +
      '<div class="check-title">' + icon + ' ' + checkName + '</div>';

    if (check.stats) {
      html += '<div>統計: ' + JSON.stringify(check.stats) + '</div>';
    }

    if (check.totalUnique !== undefined) {
      html += '<div>ユニークキー数: ' + check.totalUnique + ' / 総行数: ' + check.totalRows + '</div>';
    }

    if (check.mapTotal !== undefined) {
      html += '<div>MapMetrics合計: ' + check.mapTotal + ', AggDesired合計: ' + check.aggTotal + '</div>';
    }

    html += '</div>';
  }

  var htmlOutput = HtmlService.createHtmlOutput(html)
    .setWidth(900)
    .setHeight(700);

  SpreadsheetApp.getUi().showModalDialog(htmlOutput, 'データ検証レポート');
}


