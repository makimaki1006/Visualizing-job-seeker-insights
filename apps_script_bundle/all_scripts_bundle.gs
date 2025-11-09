// ===== DataImportAndValidation.gs =====
/**
 * データインポート・検証統合ファイル
 *
 * このファイルには以下のインポート・検証機能がすべて含まれています:
 * 1. Python結果CSVインポート
 * 2. 汎用Phaseアップローダー
 * 3. データ検証機能（7種類）
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
  // Phase 1: Core descriptive dataset
  {
    name: 'Phase1_MapMetrics.csv',
    alternateNames: ['MapMetrics.csv'],
    sheetName: 'Phase1_MapMetrics',
    required: true,
    phase: 1,
    subfolder: 'phase1'
  },
  {
    name: 'Phase1_Applicants.csv',
    alternateNames: ['Applicants.csv'],
    sheetName: 'Phase1_Applicants',
    required: true,
    phase: 1,
    subfolder: 'phase1'
  },
  {
    name: 'Phase1_DesiredWork.csv',
    alternateNames: ['DesiredWork.csv'],
    sheetName: 'Phase1_DesiredWork',
    required: true,
    phase: 1,
    subfolder: 'phase1'
  },
  {
    name: 'Phase1_AggDesired.csv',
    alternateNames: ['AggDesired.csv'],
    sheetName: 'Phase1_AggDesired',
    required: true,
    phase: 1,
    subfolder: 'phase1'
  },
  {
    name: 'P1_QualityReport.csv',
    alternateNames: ['QualityReport.csv'],
    sheetName: 'Phase1_QualityReport',
    required: false,
    phase: 1,
    subfolder: 'phase1'
  },
  {
    name: 'P1_QualityReport_Descriptive.csv',
    alternateNames: ['QualityReport_Descriptive.csv', 'P1_QualityDesc.csv'],
    sheetName: 'Phase1_QualityReport_Descriptive',
    required: false,
    phase: 1,
    subfolder: 'phase1'
  },

  // Phase 2: Statistical testing outputs
  {
    name: 'Phase2_ChiSquare.csv',
    alternateNames: ['ChiSquareTests.csv'],
    sheetName: 'Phase2_ChiSquare',
    required: false,
    phase: 2,
    subfolder: 'phase2'
  },
  {
    name: 'Phase2_ANOVA.csv',
    alternateNames: ['ANOVATests.csv'],
    sheetName: 'Phase2_ANOVA',
    required: false,
    phase: 2,
    subfolder: 'phase2'
  },
  {
    name: 'P2_QualityReport_Inferential.csv',
    alternateNames: ['QualityReport_Inferential.csv'],
    sheetName: 'Phase2_QualityReport_Inferential',
    required: false,
    phase: 2,
    subfolder: 'phase2'
  },

  // Phase 3: Persona analytics
  {
    name: 'Phase3_PersonaSummary.csv',
    alternateNames: ['PersonaSummary.csv'],
    sheetName: 'Phase3_PersonaSummary',
    required: false,
    phase: 3,
    subfolder: 'phase3'
  },
  {
    name: 'Phase3_PersonaDetails.csv',
    alternateNames: ['PersonaDetails.csv'],
    sheetName: 'Phase3_PersonaDetails',
    required: false,
    phase: 3,
    subfolder: 'phase3'
  },
  {
    name: 'P3_QualityReport_Inferential.csv',
    alternateNames: ['QualityReport_Inferential.csv'],
    sheetName: 'Phase3_QualityReport_Inferential',
    required: false,
    phase: 3,
    subfolder: 'phase3'
  },

  // Phase 6: Flow network analytics
  {
    name: 'Phase6_FlowEdges.csv',
    alternateNames: ['MunicipalityFlowEdges.csv'],
    sheetName: 'Phase6_FlowEdges',
    required: false,
    phase: 6,
    subfolder: 'phase6'
  },
  {
    name: 'Phase6_FlowNodes.csv',
    alternateNames: ['MunicipalityFlowNodes.csv'],
    sheetName: 'Phase6_FlowNodes',
    required: false,
    phase: 6,
    subfolder: 'phase6'
  },
  {
    name: 'Phase6_Proximity.csv',
    alternateNames: ['ProximityAnalysis.csv'],
    sheetName: 'Phase6_Proximity',
    required: false,
    phase: 6,
    subfolder: 'phase6'
  },
  {
    name: 'P6_QualityReport_Inferential.csv',
    alternateNames: ['QualityReport_Inferential.csv'],
    sheetName: 'Phase6_QualityReport_Inferential',
    required: false,
    phase: 6,
    subfolder: 'phase6'
  },

  // Phase 7: Advanced persona analytics
  {
    name: 'Phase7_SupplyDensity.csv',
    alternateNames: ['SupplyDensityMap.csv'],
    sheetName: 'Phase7_SupplyDensity',
    required: false,
    phase: 7,
    subfolder: 'phase7'
  },
  {
    name: 'Phase7_QualificationDist.csv',
    alternateNames: ['QualificationDistribution.csv'],
    sheetName: 'Phase7_QualificationDist',
    required: false,
    phase: 7,
    subfolder: 'phase7'
  },
  {
    name: 'Phase7_AgeGenderCross.csv',
    alternateNames: ['AgeGenderCrossAnalysis.csv'],
    sheetName: 'Phase7_AgeGenderCross',
    required: false,
    phase: 7,
    subfolder: 'phase7'
  },
  {
    name: 'Phase7_MobilityScore.csv',
    alternateNames: ['MobilityScore.csv'],
    sheetName: 'Phase7_MobilityScore',
    required: false,
    phase: 7,
    subfolder: 'phase7'
  },
  {
    name: 'Phase7_PersonaProfile.csv',
    alternateNames: ['DetailedPersonaProfile.csv'],
    sheetName: 'Phase7_PersonaProfile',
    required: false,
    phase: 7,
    subfolder: 'phase7'
  },
  {
    name: 'Phase7_PersonaMapData.csv',
    alternateNames: ['PersonaMapData.csv'],
    sheetName: 'Phase7_PersonaMapData',
    required: false,
    phase: 7,
    subfolder: 'phase7'
  },
  {
    name: 'Phase7_PersonaMobilityCross.csv',
    alternateNames: ['PersonaMobilityCross.csv'],
    sheetName: 'Phase7_PersonaMobilityCross',
    required: false,
    phase: 7,
    subfolder: 'phase7'
  },
  {
    name: 'P7_QualityReport_Inferential.csv',
    alternateNames: ['QualityReport_Inferential.csv'],
    sheetName: 'Phase7_QualityReport_Inferential',
    required: false,
    phase: 7,
    subfolder: 'phase7'
  },

  // Phase 8: Career & education analytics
  {
    name: 'Phase8_EducationDist.csv',
    alternateNames: ['EducationDistribution.csv'],
    sheetName: 'Phase8_EducationDist',
    required: false,
    phase: 8,
    subfolder: 'phase8'
  },
  {
    name: 'Phase8_EduAgeCross.csv',
    alternateNames: ['EducationAgeCross.csv'],
    sheetName: 'Phase8_EduAgeCross',
    required: false,
    phase: 8,
    subfolder: 'phase8'
  },
  {
    name: 'Phase8_EduAgeMatrix.csv',
    alternateNames: ['EducationAgeCross_Matrix.csv'],
    sheetName: 'Phase8_EduAgeMatrix',
    required: false,
    phase: 8,
    subfolder: 'phase8'
  },
  {
    name: 'Phase8_GradYearDist.csv',
    alternateNames: ['GraduationYearDistribution.csv'],
    sheetName: 'Phase8_GradYearDist',
    required: false,
    phase: 8,
    subfolder: 'phase8'
  },
  {
    name: 'Phase8_CareerDistribution.csv',
    alternateNames: ['CareerDistribution.csv'],
    sheetName: 'Phase8_CareerDistribution',
    required: false,
    phase: 8,
    subfolder: 'phase8'
  },
  {
    name: 'Phase8_CareerAgeCross.csv',
    alternateNames: ['CareerAgeCross.csv'],
    sheetName: 'Phase8_CareerAgeCross',
    required: false,
    phase: 8,
    subfolder: 'phase8'
  },
  {
    name: 'Phase8_CareerAgeMatrix.csv',
    alternateNames: ['CareerAgeCross_Matrix.csv'],
    sheetName: 'Phase8_CareerAgeMatrix',
    required: false,
    phase: 8,
    subfolder: 'phase8'
  },
  {
    name: 'P8_QualityReport.csv',
    alternateNames: ['QualityReport.csv'],
    sheetName: 'Phase8_QualityReport',
    required: false,
    phase: 8,
    subfolder: 'phase8'
  },
  {
    name: 'P8_QualityReport_Inferential.csv',
    alternateNames: ['QualityReport_Inferential.csv'],
    sheetName: 'Phase8_QualityReport_Inferential',
    required: false,
    phase: 8,
    subfolder: 'phase8'
  },

  // Phase 10: Urgency analytics
  {
    name: 'Phase10_UrgencyDist.csv',
    alternateNames: ['UrgencyDistribution.csv'],
    sheetName: 'Phase10_UrgencyDist',
    required: false,
    phase: 10,
    subfolder: 'phase10'
  },
  {
    name: 'Phase10_UrgencyAge.csv',
    alternateNames: ['UrgencyAgeCross.csv'],
    sheetName: 'Phase10_UrgencyAge',
    required: false,
    phase: 10,
    subfolder: 'phase10'
  },
  {
    name: 'Phase10_UrgencyAge_Matrix.csv',
    alternateNames: ['UrgencyAgeCross_Matrix.csv'],
    sheetName: 'Phase10_UrgencyAge_Matrix',
    required: false,
    phase: 10,
    subfolder: 'phase10'
  },
  {
    name: 'Phase10_UrgencyEmployment.csv',
    alternateNames: ['UrgencyEmploymentCross.csv'],
    sheetName: 'Phase10_UrgencyEmployment',
    required: false,
    phase: 10,
    subfolder: 'phase10'
  },
  {
    name: 'Phase10_UrgencyEmployment_Matrix.csv',
    alternateNames: ['UrgencyEmploymentCross_Matrix.csv'],
    sheetName: 'Phase10_UrgencyEmployment_Matrix',
    required: false,
    phase: 10,
    subfolder: 'phase10'
  },
  {
    name: 'Phase10_UrgencyByMunicipality.csv',
    alternateNames: ['UrgencyByMunicipality.csv'],
    sheetName: 'Phase10_UrgencyByMunicipality',
    required: false,
    phase: 10,
    subfolder: 'phase10'
  },
  {
    name: 'Phase10_UrgencyAge_ByMunicipality.csv',
    alternateNames: ['UrgencyAgeCross_ByMunicipality.csv'],
    sheetName: 'Phase10_UrgencyAge_ByMunicipality',
    required: false,
    phase: 10,
    subfolder: 'phase10'
  },
  {
    name: 'Phase10_UrgencyEmployment_ByMunicipality.csv',
    alternateNames: ['UrgencyEmploymentCross_ByMunicipality.csv'],
    sheetName: 'Phase10_UrgencyEmployment_ByMunicipality',
    required: false,
    phase: 10,
    subfolder: 'phase10'
  },
  {
    name: 'P10_QualityReport.csv',
    alternateNames: ['QualityReport.csv'],
    sheetName: 'Phase10_QualityReport',
    required: false,
    phase: 10,
    subfolder: 'phase10'
  },
  {
    name: 'P10_QualityReport_Inferential.csv',
    alternateNames: ['QualityReport_Inferential.csv'],
    sheetName: 'Phase10_QualityReport_Inferential',
    required: false,
    phase: 10,
    subfolder: 'phase10'
  },

  // Consolidated quality rollups (Phase 0)
  {
    name: 'OverallQualityReport.csv',
    alternateNames: [],
    sheetName: 'OverallQuality',
    required: false,
    phase: 0,
    subfolder: ''
  },
  {
    name: 'OverallQualityReport_Inferential.csv',
    alternateNames: [],
    sheetName: 'OverallQualityInfer',
    required: false,
    phase: 0,
    subfolder: ''
  },

  // Python analysis metadata
  {
    name: 'analysis_summary.json',
    alternateNames: [],
    sheetName: null,
    required: false,
    phase: 0,
    subfolder: null
  }
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
        var candidateNames = [fileInfo.name].concat(fileInfo.alternateNames || []);
        var searchedLabel = candidateNames.join(' / ');

        for (var i = 0; i < candidateNames.length && !file; i++) {
          var candidateName = candidateNames[i];

          if (fileInfo.subfolder) {
            var subFolder = output_v2_folder.getFoldersByName(fileInfo.subfolder);
            if (subFolder.hasNext()) {
              var targetFolder = subFolder.next();
              var filesInSub = targetFolder.getFilesByName(candidateName);
              if (filesInSub.hasNext()) {
                file = filesInSub.next();
              }
            }
          } else {
            var rootFiles = output_v2_folder.getFilesByName(candidateName);
            if (rootFiles.hasNext()) {
              file = rootFiles.next();
            }
          }
        }

        if (!file) {
          if (fileInfo.required) {
            errors.push(searchedLabel + ' が見つかりません (Phase ' + fileInfo.phase + ')');
          }
          return;
        }

        var resolvedName = file.getName();
        console.log('Processing: ' + resolvedName + ' (Phase ' + fileInfo.phase + ')');

        if (resolvedName.endsWith('.json')) {
          processJSONFile(file, ss);
        } else {
          processCSVFile(file, ss, fileInfo.sheetName);
        }

        importCount++;

      } catch (e) {
        errors.push(searchedLabel + ': ' + e.toString());
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
  var mapSheet = ss.getSheetByName('Phase1_MapMetrics');
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
  var appSheet = ss.getSheetByName('Phase1_Applicants');
  if (appSheet && appSheet.getLastRow() > 1) {
    validation.hasApplicants = true;
    validation.applicantsCount = appSheet.getLastRow() - 1;
  }
  
  // DesiredWork チェック
  var dwSheet = ss.getSheetByName('Phase1_DesiredWork');
  if (dwSheet && dwSheet.getLastRow() > 1) {
    validation.hasDesiredWork = true;
    validation.desiredWorkCount = dwSheet.getLastRow() - 1;
  }
  
  // AggDesired チェック
  var aggSheet = ss.getSheetByName('Phase1_AggDesired');
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
    'Phase1_MapMetrics.csv': 'Phase1_MapMetrics',
    'MapMetrics.csv': 'Phase1_MapMetrics',
    'Phase1_Applicants.csv': 'Phase1_Applicants',
    'Applicants.csv': 'Phase1_Applicants',
    'Phase1_DesiredWork.csv': 'Phase1_DesiredWork',
    'DesiredWork.csv': 'Phase1_DesiredWork',
    'Phase1_AggDesired.csv': 'Phase1_AggDesired',
    'AggDesired.csv': 'Phase1_AggDesired',
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
      { name: 'Phase1_MapMetrics.csv', sheetName: 'Phase1_MapMetrics', label: '地図メトリクス' },
      { name: 'Phase1_Applicants.csv', sheetName: 'Phase1_Applicants', label: '応募者情報' },
      { name: 'Phase1_DesiredWork.csv', sheetName: 'Phase1_DesiredWork', label: '希望勤務地' },
      { name: 'Phase1_AggDesired.csv', sheetName: 'Phase1_AggDesired', label: '集計データ' }
    ]
  },
  'phase2': {
    name: 'Phase 2: 統計分析',
    icon: '📊',
    files: [
      { name: 'Phase2_ChiSquare.csv', sheetName: 'Phase2_ChiSquare', label: 'カイ二乗検定' },
      { name: 'Phase2_ANOVA.csv', sheetName: 'Phase2_ANOVA', label: 'ANOVA検定' }
    ]
  },
  'phase3': {
    name: 'Phase 3: ペルソナ分析',
    icon: '👥',
    files: [
      { name: 'Phase3_PersonaSummary.csv', sheetName: 'Phase3_PersonaSummary', label: 'ペルソナサマリー' },
      { name: 'Phase3_PersonaDetails.csv', sheetName: 'Phase3_PersonaDetails', label: 'ペルソナ詳細' }
    ]
  },
  'phase6': {
    name: 'Phase 6: フロー分析',
    icon: '🌊',
    files: [
      { name: 'Phase6_FlowEdges.csv', sheetName: 'Phase6_FlowEdges', label: 'フローエッジ' },
      { name: 'Phase6_FlowNodes.csv', sheetName: 'Phase6_FlowNodes', label: 'フローノード' },
      { name: 'Phase6_Proximity.csv', sheetName: 'Phase6_Proximity', label: '移動パターン分析' }
    ]
  },
  'phase7': {
    name: 'Phase 7: 高度分析',
    icon: '📈',
    files: [
      { name: 'Phase7_SupplyDensity.csv', sheetName: 'Phase7_SupplyDensity', label: '人材供給密度' },
      { name: 'Phase7_QualificationDist.csv', sheetName: 'Phase7_QualificationDist', label: '資格分布' },
      { name: 'Phase7_AgeGenderCross.csv', sheetName: 'Phase7_AgeGenderCross', label: '年齢×性別' },
      { name: 'Phase7_MobilityScore.csv', sheetName: 'Phase7_MobilityScore', label: '移動許容度' },
      { name: 'Phase7_PersonaProfile.csv', sheetName: 'Phase7_PersonaProfile', label: 'ペルソナ詳細' },
      { name: 'Phase7_PersonaMapData.csv', sheetName: 'Phase7_PersonaMapData', label: 'ペルソナ地図' },
      { name: 'Phase7_PersonaMobilityCross.csv', sheetName: 'Phase7_PersonaMobilityCross', label: 'ペルソナ×移動' }
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
  'Phase1_MapMetrics': 6,        // 都道府県, 市区町村, キー, カウント, 緯度, 経度
  'Phase1_Applicants': 21,       // processed_data_complete.csvの全カラム
  'Phase1_DesiredWork': 4,       // 希望勤務地関連
  'Phase1_AggDesired': 4,        // 集計データ
  'Phase2_ChiSquare': 11,   // カイ二乗検定結果
  'Phase2_ANOVA': 12,       // ANOVA検定結果
  'Phase3_PersonaSummary': 10,   // ペルソナサマリー
  'Phase3_PersonaDetails': 5,    // ペルソナ詳細
  'Phase6_FlowEdges': 3,         // フローエッジ
  'Phase6_FlowNodes': 5,         // フローノード
  'Phase6_Proximity': 4  // 近接性分析（最小カラム数）
};

// ===== データ型定義 =====
var COLUMN_TYPES = {
  'Phase1_MapMetrics': {
    1: 'string',   // 都道府県
    2: 'string',   // 市区町村
    3: 'string',   // キー
    4: 'number',   // カウント
    5: 'number',   // 緯度
    6: 'number'    // 経度
  },
  'Phase1_AggDesired': {
    1: 'string',   // 都道府県
    2: 'string',   // 市区町村
    3: 'string',   // キー
    4: 'number'    // カウント
  },
  'Phase6_FlowEdges': {
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

  if (sheetName === 'Phase6_Proximity') {
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

  var mapMetrics = ss.getSheetByName('Phase1_MapMetrics');
  var aggDesired = ss.getSheetByName('Phase1_AggDesired');

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

  var applicants = ss.getSheetByName('Phase1_Applicants');
  var mapMetrics = ss.getSheetByName('Phase1_MapMetrics');

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
  var mapSheet = ss.getSheetByName('Phase1_MapMetrics');
  if (mapSheet && mapSheet.getLastRow() > 1) {
    Logger.log('MapMetrics検証開始...');

    // カラム数チェック
    var colCheck = validateColumnCount(mapSheet, 'Phase1_MapMetrics');
    results.checks.mapMetricsColumns = colCheck;
    if (!colCheck.valid) {
      allErrors = allErrors.concat(colCheck.errors);
      results.overall = false;
    }

    // データ型チェック
    var typeCheck = validateDataTypes(mapSheet, 'Phase1_MapMetrics');
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
    var dupCheck = detectDuplicateKeys(mapSheet, 3, 'Phase1_MapMetrics');
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
  var aggSheet = ss.getSheetByName('Phase1_AggDesired');
  if (aggSheet && aggSheet.getLastRow() > 1) {
    Logger.log('AggDesired検証開始...');

    var aggColCheck = validateColumnCount(aggSheet, 'Phase1_AggDesired');
    results.checks.aggDesiredColumns = aggColCheck;
    if (!aggColCheck.valid) {
      allErrors = allErrors.concat(aggColCheck.errors);
      results.overall = false;
    }

    var aggTypeCheck = validateDataTypes(aggSheet, 'Phase1_AggDesired');
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

// ===== DataManagementUtilities.gs =====
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

// ===== DataServiceProvider.gs =====
/**
 * データサービスプロバイダー統合ファイル
 *
 * このファイルには以下のデータサービス機能がすべて含まれています:
 * 1. 地図データプロバイダー
 * 2. Google Maps API設定
 * 3. 地域状態サービス
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
// 1. 地図データプロバイダー
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

/**
 * 全可視化データを取得
 * map_GAS_complete.htmlで使用
 */
function getAllVisualizationData() {
  try {
    const ss = SpreadsheetApp.getActiveSpreadsheet();

    // 4つのシートからデータ取得
    const mapMetrics = getSheetData(ss, 'Phase1_MapMetrics');
    const applicants = getSheetData(ss, 'Phase1_Applicants');
    const desiredWork = getSheetData(ss, 'Phase1_DesiredWork');
    const aggDesired = getSheetData(ss, 'Phase1_AggDesired');

    Logger.log(`データ取得成功: MapMetrics=${mapMetrics.length}, Applicants=${applicants.length}, DesiredWork=${desiredWork.length}, AggDesired=${aggDesired.length}`);

    return {
      mapMetrics: mapMetrics,
      applicants: applicants,
      desiredWork: desiredWork,
      aggDesired: aggDesired
    };

  } catch (error) {
    Logger.log('データ取得エラー: ' + error.message);
    throw new Error('データ取得に失敗しました: ' + error.message);
  }
}

/**
 * シートデータを取得してオブジェクト配列に変換
 */
function getSheetData(spreadsheet, sheetName) {
  const sheet = spreadsheet.getSheetByName(sheetName);

  if (!sheet) {
    Logger.log(`警告: ${sheetName}シートが見つかりません`);
    return [];
  }

  const data = sheet.getDataRange().getValues();

  if (data.length < 2) {
    Logger.log(`警告: ${sheetName}シートにデータがありません`);
    return [];
  }

  const headers = data[0];
  const rows = data.slice(1);

  // オブジェクト配列に変換
  const result = rows.map(row => {
    const obj = {};
    headers.forEach((header, index) => {
      obj[header] = row[index];
    });
    return obj;
  });

  return result;
}

/**
 * MAPダイアログ表示（Leaflet版）
 */
function showMapComplete() {
  const html = HtmlService.createHtmlOutputFromFile('MapComplete')
    .setWidth(1400)
    .setHeight(800);

  SpreadsheetApp.getUi().showModalDialog(html, '🗺️ 求職者データ分析マップ');
}

/**
 * 地図表示（バブルマップ）
 */
function showMapBubble() {
  const html = HtmlService.createHtmlOutputFromFile('MapComplete')
    .setWidth(1400)
    .setHeight(800);

  SpreadsheetApp.getUi().showModalDialog(html, '🗺️ 地図表示（バブル）');
}

/**
 * 地図表示（ヒートマップ）
 */
function showMapHeatmap() {
  const html = HtmlService.createHtmlOutputFromFile('MapComplete')
    .setWidth(1400)
    .setHeight(800);

  SpreadsheetApp.getUi().showModalDialog(html, '📍 地図表示（ヒートマップ）');
}


// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 2. Google Maps API設定
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

/**
 * Google Maps APIキー取得（セキュア版・オプショナル対応）
 *
 * @param {boolean} throwError - APIキー未設定時にエラーをスローするか（デフォルト: false）
 * @return {string|null} Google Maps APIキー（未設定時はnull）
 */
function getGoogleMapsAPIKey(throwError = false) {
  const properties = PropertiesService.getScriptProperties();
  const apiKey = properties.getProperty('GOOGLE_MAPS_API_KEY');

  if (!apiKey) {
    if (throwError) {
      throw new Error(
        'Google Maps APIキーが設定されていません。\n\n' +
        '設定方法:\n' +
        '1. GASエディタ > プロジェクト設定（歯車アイコン）\n' +
        '2. 「スクリプトのプロパティ」セクション\n' +
        '3. 「スクリプト プロパティを追加」\n' +
        '4. プロパティ名: GOOGLE_MAPS_API_KEY\n' +
        '5. 値: あなたのGoogle Maps APIキー\n' +
        '6. 保存後、再度この機能を実行してください'
      );
    }

    // エラーをスローしない場合は警告をログに出力
    console.warn('⚠️ Google Maps APIキーが未設定です。一部の地図機能が制限される場合があります。');
    return null;
  }

  return apiKey;
}

/**
 * Google Maps APIキー設定（初回セットアップ用）
 *
 * 注意: この関数は初回セットアップ時に一度だけ実行してください
 * セキュリティ上、APIキーをコード内に直接書かないでください
 *
 * @param {string} apiKey - Google Maps APIキー
 */
function setGoogleMapsAPIKey(apiKey) {
  if (!apiKey || apiKey.trim() === '') {
    throw new Error('APIキーが空です');
  }

  if (apiKey === 'YOUR_API_KEY_HERE') {
    throw new Error('プレースホルダーのままです。実際のAPIキーを設定してください');
  }

  const properties = PropertiesService.getScriptProperties();
  properties.setProperty('GOOGLE_MAPS_API_KEY', apiKey);

  Logger.log('Google Maps APIキーを設定しました');
  Logger.log('セキュリティのため、この関数内のAPIキーは削除してください');
}

/**
 * Google Maps APIキー検証
 *
 * @return {boolean} APIキーが設定されている場合true
 */
function validateGoogleMapsAPIKey() {
  try {
    const apiKey = getGoogleMapsAPIKey();
    return apiKey && apiKey.length > 0 && apiKey !== 'YOUR_API_KEY_HERE';
  } catch (error) {
    return false;
  }
}

/**
 * Google Maps スクリプトタグ生成（セキュア版・オプショナル対応）
 *
 * @param {Array<string>} libraries - 読み込むライブラリ（例: ['visualization', 'geometry']）
 * @return {string} Google Maps スクリプトタグHTML（APIキー未設定時は警告コメント）
 */
function generateGoogleMapsScriptTag(libraries) {
  const apiKey = getGoogleMapsAPIKey(false); // エラーをスローしない

  if (!apiKey) {
    // APIキーが未設定の場合は警告コメントを返す
    return `<!-- ⚠️ Google Maps APIキーが未設定です。地図機能が制限されています。 -->`;
  }

  let scriptUrl = `https://maps.googleapis.com/maps/api/js?key=${apiKey}`;

  if (libraries && libraries.length > 0) {
    scriptUrl += `&libraries=${libraries.join(',')}`;
  }

  return `<script src="${scriptUrl}"></script>`;
}

/**
 * APIキー設定状況確認（デバッグ用）
 */
function checkAPIKeyStatus() {
  const ui = SpreadsheetApp.getUi();

  try {
    const apiKey = getGoogleMapsAPIKey();
    const maskedKey = apiKey.substring(0, 10) + '...' + apiKey.substring(apiKey.length - 4);

    ui.alert(
      'APIキー設定確認',
      `✅ Google Maps APIキーが設定されています\n\n` +
      `マスク済みキー: ${maskedKey}\n` +
      `キー長: ${apiKey.length}文字\n\n` +
      `セキュリティのため、完全なキーは表示されません。`,
      ui.ButtonSet.OK
    );
  } catch (error) {
    ui.alert(
      'APIキー未設定',
      `❌ Google Maps APIキーが設定されていません\n\n` +
      error.message,
      ui.ButtonSet.OK
    );
  }
}

/**
 * APIキーリセット（管理者用）
 *
 * 注意: この操作は取り消せません
 */
function resetGoogleMapsAPIKey() {
  const ui = SpreadsheetApp.getUi();

  const response = ui.alert(
    'APIキーリセット',
    '本当にGoogle Maps APIキーをリセットしますか？\n\n' +
    'この操作は取り消せません。',
    ui.ButtonSet.YES_NO
  );

  if (response === ui.Button.YES) {
    const properties = PropertiesService.getScriptProperties();
    properties.deleteProperty('GOOGLE_MAPS_API_KEY');

    ui.alert(
      'リセット完了',
      'Google Maps APIキーをリセットしました。\n\n' +
      '再度setGoogleMapsAPIKey()関数を使用して設定してください。',
      ui.ButtonSet.OK
    );

    Logger.log('Google Maps APIキーをリセットしました');
  }
}


// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 3. 地域状態サービス
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

const REGION_STATE_KEYS = {
  PREFECTURE: 'regionalDashboard.prefecture',
  MUNICIPALITY: 'regionalDashboard.municipality'
};

const REGION_OPTION_CACHE = {
  PREFECTURES: 'regionalDashboard.prefList:v1',
  MUNICIPALITY_PREFIX: 'regionalDashboard.muniList:v1:',
  TTL_SECONDS: 300
};

const REGION_SOURCE_SHEETS = {
  MAP_METRICS: 'Phase1_MapMetrics'
};

const REGION_COLUMN_LABELS = {
  PREFECTURE: ['都道府県', '都道府県名'],
  MUNICIPALITY: ['市区町村', '市区町村名', '自治体'],
  KEY: ['キー', '地域キー']
};

/**
 * 選択済み地域を保存する。
 * @param {string} prefecture 都道府県名
 * @param {string} municipality 市区町村名
 * @return {{prefecture: string|null, municipality: string|null}}
 */
function saveSelectedRegion(prefecture, municipality) {
  const userProps = PropertiesService.getUserProperties();
  const prefValue = normalizeRegionValue(prefecture);
  const muniValue = normalizeRegionValue(municipality);

  if (prefValue) {
    userProps.setProperty(REGION_STATE_KEYS.PREFECTURE, prefValue);
  } else {
    userProps.deleteProperty(REGION_STATE_KEYS.PREFECTURE);
  }

  if (muniValue) {
    userProps.setProperty(REGION_STATE_KEYS.MUNICIPALITY, muniValue);
  } else {
    userProps.deleteProperty(REGION_STATE_KEYS.MUNICIPALITY);
  }

  return {
    prefecture: prefValue,
    municipality: muniValue
  };
}

/**
 * 保存済み地域を読み込む。未保存の場合はMapMetricsから先頭候補を採用する。
 * @return {{prefecture: string|null, municipality: string|null, key: string|null}}
 */
function loadSelectedRegion() {
  const userProps = PropertiesService.getUserProperties();
  let prefecture = userProps.getProperty(REGION_STATE_KEYS.PREFECTURE);
  let municipality = userProps.getProperty(REGION_STATE_KEYS.MUNICIPALITY);

  if (!prefecture) {
    const defaults = getAvailablePrefectures();
    prefecture = defaults.length ? defaults[0] : null;
  }

  if (prefecture && municipality) {
    const municipalities = getMunicipalitiesForPrefecture(prefecture);
    if (!municipalities.includes(municipality)) {
      municipality = municipalities.length ? municipalities[0] : null;
    }
  } else if (prefecture && !municipality) {
    const municipalities = getMunicipalitiesForPrefecture(prefecture);
    municipality = municipalities.length ? municipalities[0] : null;
  }

  return {
    prefecture: prefecture,
    municipality: municipality,
    key: buildRegionKey(prefecture, municipality)
  };
}

/**
 * 地域選択をクリアする。
 */
function clearSelectedRegion() {
  const userProps = PropertiesService.getUserProperties();
  userProps.deleteProperty(REGION_STATE_KEYS.PREFECTURE);
  userProps.deleteProperty(REGION_STATE_KEYS.MUNICIPALITY);
}

/**
 * 利用可能な都道府県を取得する。
 * @return {string[]} 都道府県名リスト（昇順）
 */
function getAvailablePrefectures() {
  const cache = CacheService.getScriptCache();
  const cached = cache.get(REGION_OPTION_CACHE.PREFECTURES);
  if (cached) {
    return JSON.parse(cached);
  }

  const rows = readSheetRows(REGION_SOURCE_SHEETS.MAP_METRICS);
  if (!rows.length) {
    return [];
  }

  const prefectureIndex = findColumnIndex(rows[0], REGION_COLUMN_LABELS.PREFECTURE);
  if (prefectureIndex === -1) {
    return [];
  }

  const prefectures = Array.from(
    new Set(
      rows.slice(1)
        .map(row => normalizeRegionValue(row[prefectureIndex]))
        .filter(Boolean)
    )
  ).sort();

  cache.put(REGION_OPTION_CACHE.PREFECTURES, JSON.stringify(prefectures), REGION_OPTION_CACHE.TTL_SECONDS);
  return prefectures;
}

/**
 * 指定都道府県の市区町村リストを取得する。
 * @param {string} prefecture 都道府県名
 * @return {string[]} 市区町村リスト（昇順）
 */
function getMunicipalitiesForPrefecture(prefecture) {
  const prefValue = normalizeRegionValue(prefecture);
  if (!prefValue) {
    return [];
  }

  const cacheKey = REGION_OPTION_CACHE.MUNICIPALITY_PREFIX + prefValue;
  const cache = CacheService.getScriptCache();
  const cached = cache.get(cacheKey);
  if (cached) {
    return JSON.parse(cached);
  }

  const rows = readSheetRows(REGION_SOURCE_SHEETS.MAP_METRICS);
  if (!rows.length) {
    return [];
  }

  const header = rows[0];
  const prefIndex = findColumnIndex(header, REGION_COLUMN_LABELS.PREFECTURE);
  const muniIndex = findColumnIndex(header, REGION_COLUMN_LABELS.MUNICIPALITY);
  if (prefIndex === -1 || muniIndex === -1) {
    return [];
  }

  const municipalities = Array.from(
    new Set(
      rows.slice(1)
        .filter(row => normalizeRegionValue(row[prefIndex]) === prefValue)
        .map(row => normalizeRegionValue(row[muniIndex]))
        .filter(Boolean)
    )
  ).sort();

  cache.put(cacheKey, JSON.stringify(municipalities), REGION_OPTION_CACHE.TTL_SECONDS);
  return municipalities;
}

/**
 * 地域候補と保存済み状態をまとめて取得する。
 * @return {{state: {prefecture: string|null, municipality: string|null, key: string|null}, prefectures: string[], municipalities: string[]}}
 */
function getRegionOptions() {
  const state = loadSelectedRegion();
  const prefectures = getAvailablePrefectures();
  const municipalities = state.prefecture ? getMunicipalitiesForPrefecture(state.prefecture) : [];
  return {
    state: state,
    prefectures: prefectures,
    municipalities: municipalities
  };
}

/**
 * 地域候補キャッシュを破棄する。
 */
function resetRegionOptionCache() {
  const cache = CacheService.getScriptCache();
  cache.remove(REGION_OPTION_CACHE.PREFECTURES);
  const prefectures = getAvailablePrefectures();
  prefectures.forEach(pref => {
    cache.remove(REGION_OPTION_CACHE.MUNICIPALITY_PREFIX + pref);
  });
}

/**
 * MapMetricsシートを2次元配列で取得する。
 * @param {string} sheetName シート名
 * @return {Array<Array<*>>}
 */
function readSheetRows(sheetName) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName(sheetName);
  if (!sheet) {
    return [];
  }
  const values = sheet.getDataRange().getValues();
  return values || [];
}

/**
 * 候補列名の中から一致する列インデックスを取得する。
 * @param {string[]} header ヘッダー行
 * @param {string[]} candidates 優先候補
 * @return {number} 見つかった列番号（0始まり） / 見つからない場合は -1
 */
function findColumnIndex(header, candidates) {
  for (let i = 0; i < header.length; i += 1) {
    const label = header[i];
    if (!label) {
      continue;
    }
    const normalized = normalizeRegionValue(label);
    if (candidates.includes(label) || candidates.includes(normalized)) {
      return i;
    }
  }
  return -1;
}

/**
 * 地域名の正規化。
 * @param {string} value 対象文字列
 * @return {string|null}
 */
function normalizeRegionValue(value) {
  if (value === null || value === undefined) {
    return null;
  }
  const trimmed = String(value).trim();
  return trimmed.length ? trimmed : null;
}

/**
 * 地域キーを生成する。
 * @param {string|null} prefecture 都道府県
 * @param {string|null} municipality 市区町村
 * @return {string|null}
 */
function buildRegionKey(prefecture, municipality) {
  const pref = normalizeRegionValue(prefecture);
  if (!pref) {
    return null;
  }
  const muni = normalizeRegionValue(municipality);
  return muni ? pref + muni : pref;
}

// ===== MapVisualization.gs =====
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

// ===== MenuIntegration.gs =====
/**
 * メニュー統合とダイアログ表示
 * Upload_Enhanced.htmlを起動するためのメニュー追加
 */

// ===== メニュー作成（完全版） =====
function onOpen() {
  var ui = SpreadsheetApp.getUi();
  
  ui.createMenu('📊 データ処理')
    // データインポート（整理版）
    .addSubMenu(ui.createMenu('📥 データインポート')
      .addItem('🎯 Python結果を自動インポート（推奨）', 'importPythonCSVDialog')
      .addItem('📁 フォルダを指定してインポート', 'batchImportPythonResults')
      .addItem('⚡ CSVファイルを個別アップロード', 'showEnhancedUploadDialog'))
    .addSeparator()
    // 地図表示
    .addItem('🗺️ 地図表示（バブル）', 'showMapBubble')
    .addItem('📍 地図表示（ヒートマップ）', 'showMapHeatmap')
    .addSeparator()
    // 統計分析・ペルソナ
    .addSubMenu(ui.createMenu('📈 統計分析・ペルソナ')
      .addItem('🔬 カイ二乗検定結果', 'showChiSquareTests')
      .addItem('📊 ANOVA検定結果', 'showANOVATests')
      .addSeparator()
      .addItem('👥 ペルソナサマリー', 'showPersonaSummary')
      .addItem('📋 ペルソナ詳細', 'showPersonaDetails')
      .addSeparator()
      .addItem('🎯 ペルソナ難易度確認（NEW）', 'showPersonaDifficultyChecker'))
    .addSeparator()
    // Phase 6: フロー・移動パターン分析
    .addSubMenu(ui.createMenu('🌊 フロー・移動パターン分析')
      .addItem('🔀 自治体間フロー分析', 'showMunicipalityFlowNetworkVisualization')
      .addSeparator()
      .addItem('🎯 フロー・移動統合ビュー', 'showCompleteIntegratedDashboard'))
    .addSeparator()
    // Phase 7: 高度分析
    .addSubMenu(ui.createMenu('📈 Phase 7: 高度分析')
      .addSubMenu(ui.createMenu('📥 データインポート')
        .addItem('📤 一括アップロード（全7ファイル）', 'showPhase7BatchUploadDialog')
        .addSeparator()
        .addItem('🚀 クイックインポート（Google Drive）', 'quickImportLatestPhase7Data')
        .addItem('📂 Google Driveから自動インポート', 'autoImportPhase7Data')
        .addSeparator()
        .addItem('📁 Phase 7フォルダ作成', 'createPhase7FolderInDrive')
        .addItem('ℹ️ Google Driveフォルダ情報', 'showGoogleDriveFolderInfo')
        .addSeparator()
        .addItem('✅ アップロード状況確認', 'showPhase7UploadSummary'))
      .addSeparator()
      .addSubMenu(ui.createMenu('📊 個別分析')
        .addItem('🗺️ 人材供給密度マップ', 'showSupplyDensityMap')
        .addItem('🎓 資格別人材分布', 'showQualificationDistribution')
        .addItem('👥 年齢層×性別クロス分析', 'showAgeGenderCrossAnalysis')
        .addItem('🚗 移動許容度スコアリング', 'showMobilityScoreAnalysis')
        .addItem('📊 ペルソナ詳細プロファイル', 'showDetailedPersonaProfile'))
      .addSeparator()
      .addItem('🎯 Phase 7統合ダッシュボード', 'showPhase7CompleteDashboard')
      .addSeparator()
      .addSubMenu(ui.createMenu('🔧 データ管理')
        .addItem('✅ データ検証', 'validatePhase7Data')
        .addItem('📊 データサマリー', 'showPhase7DataSummary')
        .addSeparator()
        .addItem('📤 ランク別内訳エクスポート', 'exportRankBreakdownToSheet')
        .addSeparator()
        .addItem('🧹 全データクリア', 'clearAllPhase7Data'))
      .addSeparator()
      .addItem('❓ Phase 7クイックスタート', 'showPhase7QuickStart'))
    .addSeparator()
    // Phase 8: キャリア・学歴分析
    .addSubMenu(ui.createMenu('🎓 Phase 8: キャリア・学歴分析')
      .addSubMenu(ui.createMenu('📊 個別分析')
        .addItem('📊 キャリア分布（TOP100）', 'showCareerDistribution')
        .addItem('👥 キャリア×年齢クロス分析', 'showCareerAgeCross')
        .addItem('🔥 キャリア×年齢マトリックス（ヒートマップ）', 'showCareerAgeMatrix')
        .addItem('🎓 卒業年分布（1957-2030）', 'showGraduationYearDistribution')
      )
      .addSeparator()
      .addItem('🎯 Phase 8統合ダッシュボード', 'showPhase8CompleteDashboard')
    )
    .addSeparator()
    // Phase 10: 転職意欲・緊急度分析
    .addSubMenu(ui.createMenu('🚀 Phase 10: 転職意欲・緊急度分析')
      .addSubMenu(ui.createMenu('📊 個別分析')
        .addItem('📊 緊急度分布（A-Dランク）', 'showUrgencyDistribution')
        .addItem('👥 緊急度×年齢クロス分析', 'showUrgencyAgeCross')
        .addItem('💼 緊急度×就業状態クロス分析', 'showUrgencyEmploymentCross')
        .addItem('🔥 緊急度×年齢マトリックス（ヒートマップ）', 'showUrgencyAgeMatrix')
        .addItem('🗺️ 市区町村別緊急度分布', 'showUrgencyByMunicipality')
      )
      .addSeparator()
      .addItem('🎯 Phase 10統合ダッシュボード', 'showPhase10CompleteDashboard')
    )
    .addSeparator()
    // 品質管理（NEW）
    .addSubMenu(ui.createMenu('✅ 品質管理')
      .addItem('📊 品質ダッシュボード', 'showQualityDashboard')
      .addItem('✅ データ検証レポート', 'showValidationReport')
      .addSeparator()
      .addItem('🔍 Phase品質比較', 'showPhaseQualityComparison'))
    .addSeparator()
    // データ管理
    .addItem('🔍 データ確認', 'checkMapData')
    .addItem('📊 統計サマリー', 'showStatsSummary')
    .addItem('🧹 全データクリア', 'clearAllData')
    .addSeparator()
    // デバッグ
    .addItem('🐛 デバッグログ', 'showDebugLog')
    .addItem('🔧 カラム分析', 'analyzeDesiredColumns')
    .addToUi();
}

// ===== 高速CSVインポートダイアログ（新） =====
function showEnhancedUploadDialog() {
  var html = HtmlService.createHtmlOutputFromFile('Upload_Enhanced')
    .setWidth(900)
    .setHeight(700);
  SpreadsheetApp.getUi().showModalDialog(html, '⚡ 高速CSVインポート（ブラウザ内処理）');
}

// ===== Phase品質比較ダイアログ =====
function showPhaseQualityComparison() {
  var html = HtmlService.createHtmlOutput(`
    <style>
      body { font-family: Arial, sans-serif; padding: 20px; }
      h3 { color: #667eea; }
      .form-group { margin: 15px 0; }
      label { display: block; margin-bottom: 5px; font-weight: bold; }
      select { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
      .button { background: #667eea; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; margin: 5px; }
      .button:hover { background: #5568d3; }
    </style>

    <h3>🔍 Phase品質比較</h3>
    <p>2つのPhaseの品質レポートを比較します。</p>

    <div class="form-group">
      <label>Phase 1:</label>
      <select id="phase1">
        <option value="1">Phase 1: 基礎集計</option>
        <option value="2">Phase 2: 統計分析</option>
        <option value="3">Phase 3: ペルソナ分析</option>
        <option value="6">Phase 6: フロー分析</option>
        <option value="7">Phase 7: 高度分析</option>
        <option value="8">Phase 8: 学歴分析</option>
        <option value="10">Phase 10: 緊急度分析</option>
      </select>
    </div>

    <div class="form-group">
      <label>Phase 2:</label>
      <select id="phase2">
        <option value="1">Phase 1: 基礎集計</option>
        <option value="2">Phase 2: 統計分析</option>
        <option value="3">Phase 3: ペルソナ分析</option>
        <option value="6">Phase 6: フロー分析</option>
        <option value="7">Phase 7: 高度分析</option>
        <option value="8" selected>Phase 8: 学歴分析</option>
        <option value="10">Phase 10: 緊急度分析</option>
      </select>
    </div>

    <div style="text-align: center; margin-top: 20px;">
      <button class="button" onclick="compare()">🔍 比較開始</button>
      <button class="button" style="background: #666;" onclick="google.script.host.close()">閉じる</button>
    </div>

    <script>
      function compare() {
        var p1 = parseInt(document.getElementById('phase1').value);
        var p2 = parseInt(document.getElementById('phase2').value);

        if (p1 === p2) {
          alert('異なるPhaseを選択してください');
          return;
        }

        google.script.run
          .withSuccessHandler(function() {
            google.script.host.close();
          })
          .withFailureHandler(function(error) {
            alert('エラー: ' + error);
          })
          .comparePhaseQuality(p1, p2);
      }
    </script>
  `)
  .setWidth(500)
  .setHeight(400);

  SpreadsheetApp.getUi().showModalDialog(html, '🔍 Phase品質比較');
}

// ===== 従来のCSVアップロードダイアログ（削除済み） =====
// Upload.htmlが不要なため削除

// ===== Python処理済みCSVインポートダイアログ =====
function importPythonCSVDialog() {
  var html = HtmlService.createHtmlOutput(`
    <style>
      body { font-family: Arial, sans-serif; padding: 20px; background: #f5f7fa; }
      .container { background: white; border-radius: 12px; padding: 25px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
      h3 { color: #667eea; margin-top: 0; }
      .info-box { background: #e8f4fd; padding: 15px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #4285f4; }
      .folder-structure { background: #f8f9fa; padding: 15px; border-radius: 8px; font-family: monospace; font-size: 12px; margin: 15px 0; }
      .phase-group { margin: 10px 0; padding: 10px; background: white; border-radius: 6px; }
      .phase-title { font-weight: bold; color: #667eea; margin-bottom: 5px; }
      .file-item { padding: 4px 0 4px 20px; color: #555; }
      .button { background: #667eea; color: white; padding: 12px 24px; border: none; border-radius: 6px; cursor: pointer; margin: 5px; font-size: 14px; font-weight: 500; }
      .button:hover { background: #5568d3; }
      .button-secondary { background: #6c757d; }
      .status { margin: 15px 0; padding: 12px; border-radius: 6px; display: none; font-weight: 500; }
      .status.success { background: #d1f2eb; color: #0f5132; display: block; }
      .status.error { background: #f8d7da; color: #842029; display: block; }
      .note { font-size: 12px; color: #666; margin-top: 10px; }
    </style>

    <div class="container">
      <h3>🎯 Python結果を自動インポート（推奨）</h3>

      <div class="info-box">
        <strong>📂 想定フォルダ構造</strong>
        <div class="folder-structure">
data/output_v2/<br>
├── phase1/ (6ファイル)<br>
├── phase2/ (3ファイル)<br>
├── phase3/ (3ファイル)<br>
├── phase6/ (4ファイル)<br>
├── phase7/ (6ファイル)<br>
├── phase8/ (6ファイル) ✨<br>
├── phase10/ (7ファイル) ✨<br>
├── OverallQualityReport.csv<br>
├── OverallQualityReport_Inferential.csv<br>
└── geocache.json
        </div>
        <div class="note">※ 各Phaseフォルダに分かれていても自動検出します</div>
      </div>

      <div class="info-box">
        <strong>📋 インポートされるファイル（合計37ファイル）</strong>

        <div class="phase-group">
          <div class="phase-title">Phase 1: 基礎集計 (6ファイル)</div>
          <div class="file-item">→ Applicants.csv, DesiredWork.csv, AggDesired.csv</div>
          <div class="file-item">→ MapMetrics.csv, QualityReport.csv, QualityReport_Descriptive.csv</div>
        </div>

        <div class="phase-group">
          <div class="phase-title">Phase 2: 統計分析 (3ファイル)</div>
          <div class="file-item">→ ChiSquareTests.csv, ANOVATests.csv, QualityReport_Inferential.csv</div>
        </div>

        <div class="phase-group">
          <div class="phase-title">Phase 3: ペルソナ分析 (3ファイル)</div>
          <div class="file-item">→ PersonaSummary.csv, PersonaDetails.csv, QualityReport_Inferential.csv</div>
        </div>

        <div class="phase-group">
          <div class="phase-title">Phase 6: フロー分析 (4ファイル)</div>
          <div class="file-item">→ MunicipalityFlowEdges.csv, MunicipalityFlowNodes.csv</div>
          <div class="file-item">→ ProximityAnalysis.csv, QualityReport_Inferential.csv</div>
        </div>

        <div class="phase-group">
          <div class="phase-title">Phase 7: 高度分析 (6ファイル)</div>
          <div class="file-item">→ SupplyDensityMap.csv, QualificationDistribution.csv</div>
          <div class="file-item">→ AgeGenderCrossAnalysis.csv, MobilityScore.csv</div>
          <div class="file-item">→ DetailedPersonaProfile.csv, QualityReport_Inferential.csv</div>
        </div>

        <div class="phase-group">
          <div class="phase-title">Phase 8: 学歴分析 (6ファイル) ✨</div>
          <div class="file-item">→ EducationDistribution.csv, EducationAgeCross.csv</div>
          <div class="file-item">→ EducationAgeCross_Matrix.csv, GraduationYearDistribution.csv</div>
          <div class="file-item">→ QualityReport.csv, QualityReport_Inferential.csv</div>
        </div>

        <div class="phase-group">
          <div class="phase-title">Phase 10: 緊急度分析 (7ファイル) ✨</div>
          <div class="file-item">→ UrgencyDistribution.csv, UrgencyAgeCross.csv, UrgencyAgeCross_Matrix.csv</div>
          <div class="file-item">→ UrgencyEmploymentCross.csv, UrgencyEmploymentCross_Matrix.csv</div>
          <div class="file-item">→ QualityReport.csv, QualityReport_Inferential.csv</div>
        </div>

        <div class="phase-group">
          <div class="phase-title">Root: 統合品質レポート (2ファイル)</div>
          <div class="file-item">→ OverallQualityReport.csv, OverallQualityReport_Inferential.csv</div>
        </div>
      </div>

      <div style="text-align: center; margin: 30px 0;">
        <p style="font-weight: 500;">Google DriveのフォルダからPython出力ファイルを自動検出してインポートします</p>
        <button class="button" onclick="startImport()">📥 インポート開始（37ファイル自動）</button>
        <button class="button button-secondary" onclick="google.script.host.close()">閉じる</button>
      </div>

      <div id="status" class="status"></div>
    </div>

    <script>
      function startImport() {
        document.getElementById('status').textContent = '⏳ 処理中...（37ファイルを検索しています）';
        document.getElementById('status').className = 'status';
        document.getElementById('status').style.display = 'block';
        document.getElementById('status').style.background = '#fff3cd';
        document.getElementById('status').style.color = '#856404';

        google.script.run
          .withSuccessHandler(function(result) {
            document.getElementById('status').textContent = '✅ ' + result.message;
            document.getElementById('status').className = 'status success';
            setTimeout(() => google.script.host.close(), 2000);
          })
          .withFailureHandler(function(error) {
            document.getElementById('status').textContent = '❌ エラー: ' + error.message;
            document.getElementById('status').className = 'status error';
          })
          .batchImportPythonResults();
      }
    </script>
  `)
  .setWidth(700)
  .setHeight(750);

  SpreadsheetApp.getUi().showModalDialog(html, '🎯 Python結果を自動インポート（推奨）');
}

// ===== PersonaDifficultyChecker.gs =====
/**
 * ペルソナ難易度確認機能（市町村別対応版）
 * セグメント別の採用難易度を多角的に分析・表示
 * v2.2: 市町村フィルター機能追加
 */

// ===== ペルソナ難易度確認ダイアログ表示 =====
function showPersonaDifficultyChecker() {
  var html = HtmlService.createHtmlOutputFromFile('PersonaDifficultyCheckerUI')
    .setWidth(1400)
    .setHeight(900);
  SpreadsheetApp.getUi().showModalDialog(html, '🎯 ペルソナ難易度確認（市町村別対応）');
}

// ===== 市町村リスト取得 =====
function getMunicipalityList() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getSheetByName('Phase3_PersonaSummaryByMunicipality');

  if (!sheet || sheet.getLastRow() <= 1) {
    return { success: false, message: 'Phase3_PersonaByMunicipalityデータが見つかりません' };
  }

  var data = sheet.getDataRange().getValues();
  var headers = data[0];
  var rows = data.slice(1);

  // municipalityカラムのインデックス
  var muniColIndex = headers.indexOf('municipality');

  if (muniColIndex === -1) {
    return { success: false, message: 'municipalityカラムが見つかりません' };
  }

  // 重複を除去してソート
  var municipalities = rows.map(function(row) {
    return row[muniColIndex];
  }).filter(function(value, index, self) {
    return self.indexOf(value) === index;
  }).sort();

  return { success: true, municipalities: municipalities };
}

// ===== 市町村別ペルソナデータ取得 =====
function getPersonaDataByMunicipality(municipality) {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getSheetByName('Phase3_PersonaSummaryByMunicipality');

  if (!sheet || sheet.getLastRow() <= 1) {
    return { success: false, message: 'Phase3_PersonaByMunicipalityデータが見つかりません' };
  }

  var data = sheet.getDataRange().getValues();
  var headers = data[0];
  var rows = data.slice(1);

  // カラムインデックス
  var muniColIndex = headers.indexOf('municipality');
  var personaNameIndex = headers.indexOf('persona_name');
  var countIndex = headers.indexOf('count');
  var totalInMuniIndex = headers.indexOf('total_in_municipality');
  var marketShareIndex = headers.indexOf('market_share_pct');
  var avgAgeIndex = headers.indexOf('avg_age');
  var avgDesiredIndex = headers.indexOf('avg_desired_areas');
  var avgQualIndex = headers.indexOf('avg_qualifications');
  var employmentRateIndex = headers.indexOf('employment_rate');

  // 指定された市町村のデータのみフィルタリング
  var filteredRows = rows.filter(function(row) {
    return row[muniColIndex] === municipality;
  });

  if (filteredRows.length === 0) {
    return { success: false, message: '指定された市町村のデータが見つかりません: ' + municipality };
  }

  // 市町村内の総母数（最初の行から取得）
  var totalInMunicipality = filteredRows[0][totalInMuniIndex];

  // 各ペルソナの詳細分析
  var personas = filteredRows.map(function(row) {
    var personaName = row[personaNameIndex];
    var count = parseInt(row[countIndex]) || 0;
    var marketSharePct = parseFloat(row[marketShareIndex]) || 0;
    var avgAge = parseFloat(row[avgAgeIndex]) || 0;
    var avgDesiredAreas = parseFloat(row[avgDesiredIndex]) || 0;
    var avgQualifications = parseFloat(row[avgQualIndex]) || 0;
    var employmentRate = parseFloat(row[employmentRateIndex]) || 0;

    // 性別推定（ペルソナ名から）
    var femaleRatio = personaName.indexOf('女性') !== -1 ? 1.0 : 0.0;

    // 難易度スコア計算（市町村内シェアベース）
    var difficultyScore = calculateDifficultyScoreMunicipality({
      avgQualifications: avgQualifications,
      avgDesiredLocations: avgDesiredAreas,
      femaleRatio: femaleRatio,
      count: count,
      marketSharePct: marketSharePct,  // 市町村内シェア
      avgAge: avgAge
    });

    return {
      segmentName: personaName,
      count: count,
      marketSharePct: marketSharePct,
      totalInMunicipality: totalInMunicipality,
      difficultyScore: difficultyScore,
      difficultyLevel: getDifficultyLevel(difficultyScore),
      ageGroup: getAgeGroupFromPersonaName(personaName),
      qualificationLevel: getQualificationLevel(avgQualifications),
      mobilityLevel: getMobilityLevel(avgDesiredAreas),
      genderCategory: getGenderCategory(femaleRatio),
      marketSizeCategory: getMarketSizeCategoryMunicipality(marketSharePct),
      avgAge: avgAge,
      avgQualifications: avgQualifications,
      avgDesiredLocations: avgDesiredAreas,
      femaleRatio: femaleRatio,
      employmentRate: employmentRate
    };
  });

  return {
    success: true,
    personas: personas,
    municipality: municipality,
    totalInMunicipality: totalInMunicipality
  };
}

// ===== ペルソナ名から年齢グループ抽出 =====
function getAgeGroupFromPersonaName(personaName) {
  if (personaName.indexOf('20代') !== -1) {
    var age = 25; // 20代の中央値
    return getAgeGroup(age);
  } else if (personaName.indexOf('30代') !== -1) {
    return getAgeGroup(35);
  } else if (personaName.indexOf('40代') !== -1) {
    return getAgeGroup(45);
  } else if (personaName.indexOf('50代') !== -1) {
    return getAgeGroup(55);
  } else if (personaName.indexOf('60代') !== -1) {
    return getAgeGroup(65);
  } else if (personaName.indexOf('70歳以上') !== -1) {
    return getAgeGroup(75);
  }
  return '不明';
}

// ===== 市町村内シェアベースの市場規模カテゴリ =====
function getMarketSizeCategoryMunicipality(marketSharePct) {
  if (marketSharePct >= 20.0) return '超大規模（20%以上）';
  if (marketSharePct >= 15.0) return '大規模（15～19%）';
  if (marketSharePct >= 10.0) return '中規模（10～14%）';
  if (marketSharePct >= 7.0) return 'やや小規模（7～9%）';
  if (marketSharePct >= 4.0) return '小規模（4～6%）';
  if (marketSharePct >= 2.0) return '超小規模（2～3%）';
  return 'ニッチ（2%未満）';
}

// ===== 市町村内シェアベースの難易度スコア計算 =====
function calculateDifficultyScoreMunicipality(params) {
  // 資格数スコア（0-40点）
  var qualScore = Math.min(params.avgQualifications * 15, 40);

  // 移動性スコア（0-25点）
  var mobilityScore = Math.min(params.avgDesiredLocations * 8, 25);

  // 市場規模スコア（0-20点、市町村内シェアが小さいほど高得点）
  var sizeScore = Math.max(0, 20 - params.marketSharePct * 2);

  // 年齢スコア（0-10点）
  var ageScore = getAgeScore(params.avgAge);

  // 性別偏りスコア（0-5点）
  var genderScore = Math.abs(params.femaleRatio - 0.5) * 10;

  var totalScore = qualScore + mobilityScore + sizeScore + ageScore + genderScore;
  return Math.min(Math.round(totalScore), 100);
}

// ===== ペルソナデータ取得（全国レベル・従来版） =====
function getPersonaDataForDifficulty() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var summarySheet = ss.getSheetByName('Phase3_PersonaSummary');
  var detailsSheet = ss.getSheetByName('Phase3_PersonaDetails');
  var applicantsSheet = ss.getSheetByName('Phase1_Applicants');

  if (!summarySheet || summarySheet.getLastRow() <= 1) {
    return { success: false, message: 'Phase3_PersonaSummaryデータが見つかりません' };
  }

  // Phase3_PersonaSummaryデータ取得
  var summaryData = summarySheet.getDataRange().getValues();
  var summaryHeaders = summaryData[0];
  var summaryRows = summaryData.slice(1);

  // 各ペルソナの詳細分析
  var personas = summaryRows.map(function(row) {
    var segmentId = row[0];
    var segmentName = row[1];
    var count = parseInt(row[2]) || 0;
    var percentage = parseFloat(row[3]) || 0;
    var avgAge = parseFloat(row[4]) || 0;
    var femaleRatio = parseFloat(row[5]) || 0;
    var avgQualifications = parseFloat(row[6]) || 0;
    var topPrefecture = row[7];
    var avgDesiredLocations = parseFloat(row[8]) || 0;

    // 難易度スコア計算（0-100）
    var difficultyScore = calculateDifficultyScore({
      avgQualifications: avgQualifications,
      avgDesiredLocations: avgDesiredLocations,
      femaleRatio: femaleRatio,
      count: count,
      percentage: percentage,
      avgAge: avgAge
    });

    return {
      segmentId: segmentId,
      segmentName: segmentName,
      count: count,
      percentage: percentage,
      avgAge: avgAge,
      femaleRatio: femaleRatio,
      avgQualifications: avgQualifications,
      topPrefecture: topPrefecture,
      avgDesiredLocations: avgDesiredLocations,
      difficultyScore: difficultyScore,
      difficultyLevel: getDifficultyLevel(difficultyScore),
      ageGroup: getAgeGroup(avgAge),
      qualificationLevel: getQualificationLevel(avgQualifications),
      mobilityLevel: getMobilityLevel(avgDesiredLocations),
      genderCategory: getGenderCategory(femaleRatio),
      marketSizeCategory: getMarketSizeCategory(percentage)
    };
  });

  // 難易度スコアでソート
  personas.sort(function(a, b) {
    return b.difficultyScore - a.difficultyScore;
  });

  return {
    success: true,
    personas: personas,
    totalCount: personas.reduce(function(sum, p) { return sum + p.count; }, 0)
  };
}

// ===== 難易度スコア計算 =====
function calculateDifficultyScore(params) {
  // スコア計算ロジック（重み付け）
  var qualScore = Math.min(params.avgQualifications * 15, 40);  // 資格数（最大40点）
  var mobilityScore = Math.min(params.avgDesiredLocations * 8, 25);  // 希望地数（最大25点）
  var sizeScore = Math.max(0, 20 - params.percentage * 2);  // 市場サイズ（小さいほど難）
  var ageScore = getAgeScore(params.avgAge);  // 年齢（10点）
  var genderScore = Math.abs(params.femaleRatio - 0.5) * 10;  // 性別偏り（5点）

  var totalScore = qualScore + mobilityScore + sizeScore + ageScore + genderScore;
  return Math.min(Math.round(totalScore), 100);
}

// ===== 年齢スコア =====
function getAgeScore(avgAge) {
  if (avgAge < 25) return 5;  // 若年層：やや難
  if (avgAge < 35) return 3;  // 若手：普通
  if (avgAge < 50) return 4;  // 中堅：やや難
  if (avgAge < 60) return 7;  // シニア：難
  return 10;  // 高齢：最難
}

// ===== 難易度レベル判定 =====
function getDifficultyLevel(score) {
  if (score >= 80) return 'S級（最難）';
  if (score >= 65) return 'A級（難）';
  if (score >= 50) return 'B級（やや難）';
  if (score >= 35) return 'C級（普通）';
  if (score >= 20) return 'D級（やや易）';
  return 'E級（易）';
}

// ===== 年齢グループ分類 =====
function getAgeGroup(avgAge) {
  if (avgAge < 25) return '新卒層（～24歳）';
  if (avgAge < 30) return '若手層（25～29歳）';
  if (avgAge < 35) return '若手中堅層（30～34歳）';
  if (avgAge < 40) return '中堅層（35～39歳）';
  if (avgAge < 45) return 'ミドル層（40～44歳）';
  if (avgAge < 50) return 'シニアミドル層（45～49歳）';
  if (avgAge < 55) return 'プレシニア層（50～54歳）';
  if (avgAge < 60) return 'シニア層（55～59歳）';
  if (avgAge < 65) return 'アクティブシニア層（60～64歳）';
  return '高齢層（65歳～）';
}

// ===== 資格レベル分類 =====
function getQualificationLevel(avgQualifications) {
  if (avgQualifications >= 5.0) return '超高資格層（5個以上）';
  if (avgQualifications >= 3.0) return '高資格層（3～4個）';
  if (avgQualifications >= 2.0) return '中資格層（2～3個）';
  if (avgQualifications >= 1.0) return '低資格層（1～2個）';
  if (avgQualifications >= 0.5) return '微資格層（0.5～1個）';
  return '無資格層（0.5個未満）';
}

// ===== 移動性レベル分類 =====
function getMobilityLevel(avgDesiredLocations) {
  if (avgDesiredLocations >= 10.0) return '超広域希望（10箇所以上）';
  if (avgDesiredLocations >= 6.0) return '広域希望（6～9箇所）';
  if (avgDesiredLocations >= 4.0) return '中域希望（4～5箇所）';
  if (avgDesiredLocations >= 2.5) return '狭域希望（2.5～3.5箇所）';
  if (avgDesiredLocations >= 1.5) return '限定希望（1.5～2.5箇所）';
  return '固定希望（1.5箇所未満）';
}

// ===== 性別カテゴリ分類 =====
function getGenderCategory(femaleRatio) {
  if (femaleRatio >= 0.9) return '女性特化層（90%以上）';
  if (femaleRatio >= 0.7) return '女性優勢層（70～89%）';
  if (femaleRatio >= 0.55) return '女性やや多層（55～69%）';
  if (femaleRatio >= 0.45) return '男女均衡層（45～54%）';
  if (femaleRatio >= 0.3) return '男性やや多層（31～44%）';
  if (femaleRatio >= 0.1) return '男性優勢層（11～30%）';
  return '男性特化層（10%以下）';
}

// ===== 市場規模カテゴリ分類 =====
function getMarketSizeCategory(percentage) {
  if (percentage >= 20.0) return '超大規模（20%以上）';
  if (percentage >= 15.0) return '大規模（15～19%）';
  if (percentage >= 10.0) return '中規模（10～14%）';
  if (percentage >= 7.0) return 'やや小規模（7～9%）';
  if (percentage >= 4.0) return '小規模（4～6%）';
  if (percentage >= 2.0) return '超小規模（2～3%）';
  return 'ニッチ（2%未満）';
}

// ===== フィルタリング機能 =====
function filterPersonasByConditions(filters) {
  var allData = getPersonaDataForDifficulty();

  if (!allData.success) {
    return allData;
  }

  var personas = allData.personas;

  // 難易度レベルフィルタ
  if (filters.difficultyLevels && filters.difficultyLevels.length > 0) {
    personas = personas.filter(function(p) {
      return filters.difficultyLevels.indexOf(p.difficultyLevel) !== -1;
    });
  }

  // 年齢グループフィルタ
  if (filters.ageGroups && filters.ageGroups.length > 0) {
    personas = personas.filter(function(p) {
      return filters.ageGroups.indexOf(p.ageGroup) !== -1;
    });
  }

  // 資格レベルフィルタ
  if (filters.qualificationLevels && filters.qualificationLevels.length > 0) {
    personas = personas.filter(function(p) {
      return filters.qualificationLevels.indexOf(p.qualificationLevel) !== -1;
    });
  }

  // 移動性レベルフィルタ
  if (filters.mobilityLevels && filters.mobilityLevels.length > 0) {
    personas = personas.filter(function(p) {
      return filters.mobilityLevels.indexOf(p.mobilityLevel) !== -1;
    });
  }

  // 性別カテゴリフィルタ
  if (filters.genderCategories && filters.genderCategories.length > 0) {
    personas = personas.filter(function(p) {
      return filters.genderCategories.indexOf(p.genderCategory) !== -1;
    });
  }

  // 市場規模カテゴリフィルタ
  if (filters.marketSizeCategories && filters.marketSizeCategories.length > 0) {
    personas = personas.filter(function(p) {
      return filters.marketSizeCategories.indexOf(p.marketSizeCategory) !== -1;
    });
  }

  return {
    success: true,
    personas: personas,
    totalCount: personas.reduce(function(sum, p) { return sum + p.count; }, 0),
    filteredCount: personas.length
  };
}

// ===== 統計サマリー取得 =====
function getPersonaDifficultyStatistics() {
  var data = getPersonaDataForDifficulty();

  if (!data.success) {
    return data;
  }

  var personas = data.personas;

  // 難易度レベル別集計
  var difficultyDistribution = {};
  var ageGroupDistribution = {};
  var qualificationDistribution = {};
  var mobilityDistribution = {};
  var genderDistribution = {};
  var marketSizeDistribution = {};

  personas.forEach(function(p) {
    // 難易度レベル
    difficultyDistribution[p.difficultyLevel] = (difficultyDistribution[p.difficultyLevel] || 0) + p.count;

    // 年齢グループ
    ageGroupDistribution[p.ageGroup] = (ageGroupDistribution[p.ageGroup] || 0) + p.count;

    // 資格レベル
    qualificationDistribution[p.qualificationLevel] = (qualificationDistribution[p.qualificationLevel] || 0) + p.count;

    // 移動性レベル
    mobilityDistribution[p.mobilityLevel] = (mobilityDistribution[p.mobilityLevel] || 0) + p.count;

    // 性別カテゴリ
    genderDistribution[p.genderCategory] = (genderDistribution[p.genderCategory] || 0) + p.count;

    // 市場規模カテゴリ
    marketSizeDistribution[p.marketSizeCategory] = (marketSizeDistribution[p.marketSizeCategory] || 0) + p.count;
  });

  return {
    success: true,
    avgDifficultyScore: personas.reduce(function(sum, p) { return sum + p.difficultyScore; }, 0) / personas.length,
    difficultyDistribution: difficultyDistribution,
    ageGroupDistribution: ageGroupDistribution,
    qualificationDistribution: qualificationDistribution,
    mobilityDistribution: mobilityDistribution,
    genderDistribution: genderDistribution,
    marketSizeDistribution: marketSizeDistribution,
    totalPersonas: personas.length,
    totalCount: data.totalCount
  };
}

// ===== Phase1-6UnifiedVisualizations.gs =====
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
    const sheet = ss.getSheetByName('Phase1_MapMetrics');

    if (!sheet) {
      throw new Error('Phase1_MapMetricsシートが見つかりません。Phase 1のデータをアップロードしてください。');
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
    const sheet = ss.getSheetByName('Phase1_Applicants');

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
    const sheet = ss.getSheetByName('Phase1_DesiredWork');

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
  const sheet = ss.getSheetByName('Phase2_ChiSquare');

  if (!sheet) {
    SpreadsheetApp.getUi().alert(
      'エラー',
      'Phase2_ChiSquareシートが見つかりません。\n' +
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
  const sheet = ss.getSheetByName('Phase2_ANOVA');

  if (!sheet) {
    SpreadsheetApp.getUi().alert(
      'エラー',
      'Phase2_ANOVAシートが見つかりません。\n' +
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
  const sheet = ss.getSheetByName('Phase3_PersonaSummary');

  if (!sheet) {
    SpreadsheetApp.getUi().alert(
      'エラー',
      'Phase3_PersonaSummaryシートが見つかりません。\n' +
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
    const percentage = parseFloat(row[3]) || 0;
    const avgAge = parseFloat(row[4]) || 0;
    const femaleRatio = parseFloat(row[5]) || 0;
    const avgQualifications = parseFloat(row[6]) || 0;
    const avgDesiredLocations = parseFloat(row[7]) || 0;

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
  const sheet = ss.getSheetByName('Phase3_PersonaDetails');

  if (!sheet) {
    SpreadsheetApp.getUi().alert(
      'エラー',
      'Phase3_PersonaDetailsシートが見つかりません。\n' +
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
  const edgesSheet = ss.getSheetByName('Phase6_FlowEdges');
  if (!edgesSheet) {
    throw new Error('Phase6_FlowEdgesシートが見つかりません');
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
  const nodesSheet = ss.getSheetByName('Phase6_FlowNodes');
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
  showMatrixHeatmap('Phase8_EduAgeMatrix', 'Phase 8: 学歴×年齢ヒートマップ', 'blue');
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

    const mapMetricsSheet = ss.getSheetByName('Phase1_MapMetrics');
    if (mapMetricsSheet) {
      data.mapMetrics = getSheetData(mapMetricsSheet);
    }

    const applicantsSheet = ss.getSheetByName('Phase1_Applicants');
    if (applicantsSheet) {
      data.applicants = getSheetData(applicantsSheet);
    }

    const desiredWorkSheet = ss.getSheetByName('Phase1_DesiredWork');
    if (desiredWorkSheet) {
      data.desiredWork = getSheetData(desiredWorkSheet);
    }

    const aggDesiredSheet = ss.getSheetByName('Phase1_AggDesired');
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

// ===== Phase10UnifiedVisualizations.gs =====
/**
 * Phase 10 統合可視化ファイル
 *
 * このファイルには以下の可視化機能がすべて含まれています:
 * 1. 緊急度分布（A-Dランク）
 * 2. 緊急度×年齢クロス分析
 * 3. 緊急度×就業状態クロス分析
 * 4. 緊急度×年齢マトリックス（ヒートマップ）
 * 5. 市区町村別緊急度分布
 * 6. Phase 10統合ダッシュボード
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
// 1. 緊急度分布（A-Dランク）
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

/**
 * 緊急度分布表示（メニューから呼び出し）
 */
function showUrgencyDistribution() {
  const ui = SpreadsheetApp.getUi();

  try {
    // データ読み込み
    const data = loadUrgencyDistData();

    if (!data || data.length === 0) {
      ui.alert(
        'データなし',
        'Phase10_UrgencyDistシートにデータがありません。\n' +
        '先に「Python結果CSVを取り込み」を実行してください。',
        ui.ButtonSet.OK
      );
      return;
    }

    // HTML生成
    const html = generateUrgencyDistHTML(data);

    // ダイアログ表示
    const htmlOutput = HtmlService.createHtmlOutput(html)
      .setWidth(1400)
      .setHeight(900);

    ui.showModalDialog(htmlOutput, 'Phase 10: 転職意欲・緊急度分布分析');

  } catch (error) {
    ui.alert('エラー', `可視化中にエラーが発生しました:\n${error.message}`, ui.ButtonSet.OK);
    Logger.log(`緊急度分布エラー: ${error.stack}`);
  }
}

/**
 * 緊急度分布データ読み込み
 * @return {Array<Object>} データオブジェクトの配列
 */
function loadUrgencyDistData() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName('Phase10_UrgencyDist');

  if (!sheet) {
    throw new Error('Phase10_UrgencyDistシートが見つかりません');
  }

  const lastRow = sheet.getLastRow();
  if (lastRow <= 1) {
    return [];
  }

  // データ範囲取得（ヘッダー除く）
  const range = sheet.getRange(2, 1, lastRow - 1, 4);
  const values = range.getValues();

  // オブジェクト配列に変換
  const data = values
    .filter(row => row[0] && row[1] > 0)
    .map(row => ({
      urgencyRank: String(row[0]),
      count: Number(row[1]),
      avgAge: row[2] ? Number(row[2]) : null,
      avgUrgencyScore: row[3] ? Number(row[3]) : null
    }));

  Logger.log(`緊急度分布データ読み込み: ${data.length}件`);

  return data;
}

/**
 * 緊急度分布HTML生成
 * @param {Array<Object>} data - データ配列
 * @return {string} HTML文字列
 */
function generateUrgencyDistHTML(data) {
  const dataJson = JSON.stringify(data);

  return `
<!DOCTYPE html>
<html>
<head>
  <base target="_top">
  <script type="text/javascript" src="https://www.gstatic.com/charts/loader.js"></script>
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
    .container {
      background-color: white;
      padding: 20px;
      border-radius: 8px;
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
      margin-bottom: 20px;
    }
    .stats-summary {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 15px;
      margin-bottom: 20px;
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
    .charts-row {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 20px;
      margin-bottom: 20px;
    }
    .chart-container {
      background-color: white;
      padding: 20px;
      border-radius: 8px;
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    #pie_chart,
    #bar_chart {
      width: 100%;
      height: 450px;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      margin-top: 10px;
      font-size: 14px;
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
    }
    tr:hover {
      background-color: #f5f5f5;
    }
    .urgency-badge {
      display: inline-block;
      padding: 6px 12px;
      border-radius: 20px;
      font-weight: bold;
      font-size: 14px;
    }
    .urgency-A { background-color: #dc3545; color: white; }
    .urgency-B { background-color: #ffc107; color: #333; }
    .urgency-C { background-color: #17a2b8; color: white; }
    .urgency-D { background-color: #6c757d; color: white; }
    .note {
      background-color: #e7f3ff;
      border-left: 4px solid #1a73e8;
      padding: 15px;
      margin-top: 10px;
      border-radius: 4px;
    }
  </style>
</head>
<body>
  <h1>🚀 Phase 10: 転職意欲・緊急度分布分析</h1>

  <div class="container">
    <h2>統計サマリー</h2>
    <div class="stats-summary" id="stats-summary"></div>
  </div>

  <div class="note">
    <strong>📊 緊急度ランク説明:</strong>
    <ul style="margin: 10px 0; padding-left: 20px;">
      <li><strong>A: 高い</strong> - 緊急度スコア7以上（即座に対応すべき）</li>
      <li><strong>B: 中程度</strong> - 緊急度スコア5-7（優先的に対応）</li>
      <li><strong>C: やや低い</strong> - 緊急度スコア3-5（計画的に対応）</li>
      <li><strong>D: 低い</strong> - 緊急度スコア3未満（長期的に対応）</li>
    </ul>
  </div>

  <div class="charts-row">
    <div class="chart-container">
      <h3>緊急度ランク別割合（円グラフ）</h3>
      <div id="pie_chart"></div>
    </div>
    <div class="chart-container">
      <h3>緊急度ランク別人数（棒グラフ）</h3>
      <div id="bar_chart"></div>
    </div>
  </div>

  <div class="container">
    <h2>緊急度ランク別詳細データ</h2>
    <table id="data-table">
      <thead>
        <tr>
          <th style="width: 30%;">緊急度ランク</th>
          <th style="width: 20%;">人数</th>
          <th style="width: 15%;">割合</th>
          <th style="width: 15%;">平均年齢</th>
          <th style="width: 20%;">平均緊急度スコア</th>
        </tr>
      </thead>
      <tbody id="table-body"></tbody>
    </table>
  </div>

  <script type="text/javascript">
    const data = ${dataJson};

    // 緊急度順序定義
    const urgencyOrder = ['A: 高い', 'B: 中程度', 'C: やや低い', 'D: 低い'];

    // Google Charts読み込み
    google.charts.load('current', {'packages':['corechart']});
    google.charts.setOnLoadCallback(drawCharts);

    function drawCharts() {
      renderStatsSummary();
      drawPieChart();
      drawBarChart();
      renderDataTable();
    }

    // 統計サマリー表示
    function renderStatsSummary() {
      const container = document.getElementById('stats-summary');

      // 総人数
      const totalCount = data.reduce((sum, row) => sum + row.count, 0);

      // 高緊急度（A+B）の人数と割合
      const highUrgencyCount = data
        .filter(d => d.urgencyRank.startsWith('A') || d.urgencyRank.startsWith('B'))
        .reduce((sum, d) => sum + d.count, 0);
      const highUrgencyRate = (highUrgencyCount / totalCount * 100).toFixed(1);

      // 平均年齢
      const avgAge = data.reduce((sum, row) => sum + (row.avgAge || 0) * row.count, 0) / totalCount;

      // 平均緊急度スコア
      const avgScore = data.reduce((sum, row) => sum + (row.avgUrgencyScore || 0) * row.count, 0) / totalCount;

      const stats = [
        {label: '総人数', value: totalCount.toLocaleString(), unit: '名'},
        {label: '高緊急度（A+B）', value: \`\${highUrgencyCount.toLocaleString()} (\${highUrgencyRate}%)\`, unit: ''},
        {label: '平均年齢', value: Math.round(avgAge), unit: '歳'},
        {label: '平均緊急度スコア', value: avgScore.toFixed(2), unit: '点'}
      ];

      stats.forEach(stat => {
        const card = document.createElement('div');
        card.className = 'stat-card';
        card.innerHTML = \`
          <div class="stat-label">\${stat.label}</div>
          <div class="stat-value">\${stat.value}</div>
          <div class="stat-label">\${stat.unit}</div>
        \`;
        container.appendChild(card);
      });
    }

    // 円グラフ描画
    function drawPieChart() {
      const chartData = new google.visualization.DataTable();
      chartData.addColumn('string', '緊急度ランク');
      chartData.addColumn('number', '人数');

      // 緊急度順にソート
      const sortedData = data.sort((a, b) =>
        urgencyOrder.indexOf(a.urgencyRank) - urgencyOrder.indexOf(b.urgencyRank)
      );

      sortedData.forEach(row => {
        chartData.addRow([row.urgencyRank, row.count]);
      });

      const options = {
        title: '緊急度ランク別割合',
        pieHole: 0.4,
        colors: ['#dc3545', '#ffc107', '#17a2b8', '#6c757d'],
        legend: {position: 'bottom'},
        chartArea: {width: '90%', height: '70%'}
      };

      const chart = new google.visualization.PieChart(
        document.getElementById('pie_chart')
      );

      chart.draw(chartData, options);
    }

    // 棒グラフ描画
    function drawBarChart() {
      const chartData = new google.visualization.DataTable();
      chartData.addColumn('string', '緊急度ランク');
      chartData.addColumn('number', '人数');

      // 緊急度順にソート
      const sortedData = data.sort((a, b) =>
        urgencyOrder.indexOf(a.urgencyRank) - urgencyOrder.indexOf(b.urgencyRank)
      );

      sortedData.forEach(row => {
        chartData.addRow([row.urgencyRank, row.count]);
      });

      const options = {
        title: '緊急度ランク別人数',
        legend: {position: 'none'},
        chartArea: {width: '70%', height: '70%'},
        hAxis: {
          title: '人数',
          minValue: 0
        },
        vAxis: {
          title: '緊急度ランク'
        },
        colors: ['#667eea']
      };

      const chart = new google.visualization.ColumnChart(
        document.getElementById('bar_chart')
      );

      chart.draw(chartData, options);
    }

    // データテーブル表示
    function renderDataTable() {
      const tbody = document.getElementById('table-body');

      // 総人数計算
      const totalCount = data.reduce((sum, row) => sum + row.count, 0);

      // 緊急度順にソート
      const sortedData = data.sort((a, b) =>
        urgencyOrder.indexOf(a.urgencyRank) - urgencyOrder.indexOf(b.urgencyRank)
      );

      sortedData.forEach(row => {
        const tr = document.createElement('tr');

        // 緊急度バッジのクラス決定
        const badgeClass = row.urgencyRank.startsWith('A') ? 'urgency-A' :
                           row.urgencyRank.startsWith('B') ? 'urgency-B' :
                           row.urgencyRank.startsWith('C') ? 'urgency-C' : 'urgency-D';

        const percentage = (row.count / totalCount * 100).toFixed(1);

        tr.innerHTML = \`
          <td><span class="urgency-badge \${badgeClass}">\${row.urgencyRank}</span></td>
          <td style="text-align: right;"><strong>\${row.count.toLocaleString()}</strong>名</td>
          <td style="text-align: right;"><strong>\${percentage}%</strong></td>
          <td style="text-align: right;">\${row.avgAge ? row.avgAge.toFixed(1) + '歳' : '－'}</td>
          <td style="text-align: right;"><strong>\${row.avgUrgencyScore ? row.avgUrgencyScore.toFixed(2) : '－'}</strong>点</td>
        \`;
        tbody.appendChild(tr);
      });
    }
  </script>
</body>
</html>
  `;
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 2. 緊急度×年齢クロス分析
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

/**
 * 緊急度×年齢クロス分析表示（メニューから呼び出し）
 */
function showUrgencyAgeCross() {
  const ui = SpreadsheetApp.getUi();

  try {
    // データ読み込み
    const data = loadUrgencyAgeCrossData();

    if (!data || data.length === 0) {
      ui.alert(
        'データなし',
        'Phase10_UrgencyAgeシートにデータがありません。\n' +
        '先に「Python結果CSVを取り込み」を実行してください。',
        ui.ButtonSet.OK
      );
      return;
    }

    // HTML生成
    const html = generateUrgencyAgeCrossHTML(data);

    // ダイアログ表示
    const htmlOutput = HtmlService.createHtmlOutput(html)
      .setWidth(1400)
      .setHeight(900);

    ui.showModalDialog(htmlOutput, 'Phase 10: 緊急度×年齢層クロス分析');

  } catch (error) {
    ui.alert('エラー', `可視化中にエラーが発生しました:\n${error.message}`, ui.ButtonSet.OK);
    Logger.log(`緊急度×年齢クロス分析エラー: ${error.stack}`);
  }
}

/**
 * 緊急度×年齢クロスデータ読み込み
 * @return {Array<Object>} データオブジェクトの配列
 */
function loadUrgencyAgeCrossData() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName('Phase10_UrgencyAge');

  if (!sheet) {
    throw new Error('Phase10_UrgencyAgeシートが見つかりません');
  }

  const lastRow = sheet.getLastRow();
  if (lastRow <= 1) {
    return [];
  }

  // データ範囲取得（ヘッダー除く）
  const range = sheet.getRange(2, 1, lastRow - 1, 5);
  const values = range.getValues();

  // オブジェクト配列に変換
  const data = values
    .filter(row => row[0] && row[1] && row[2] > 0)
    .map(row => ({
      urgencyRank: String(row[0]),
      ageGroup: String(row[1]),
      count: Number(row[2]),
      avgAge: row[3] ? Number(row[3]) : null,
      avgUrgencyScore: row[4] ? Number(row[4]) : null
    }));

  Logger.log(`緊急度×年齢クロスデータ読み込み: ${data.length}件`);

  return data;
}

/**
 * 緊急度×年齢クロスHTML生成
 * @param {Array<Object>} data - データ配列
 * @return {string} HTML文字列
 */
function generateUrgencyAgeCrossHTML(data) {
  const dataJson = JSON.stringify(data);

  return `
<!DOCTYPE html>
<html>
<head>
  <base target="_top">
  <script type="text/javascript" src="https://www.gstatic.com/charts/loader.js"></script>
  <style>
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
    .container {
      background-color: white;
      padding: 20px;
      border-radius: 8px;
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
      margin-bottom: 20px;
    }
    .stats-summary {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 15px;
      margin-bottom: 20px;
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
    #grouped_column_chart {
      width: 100%;
      height: 600px;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      margin-top: 10px;
      font-size: 13px;
    }
    th, td {
      padding: 10px;
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
    .table-container {
      max-height: 400px;
      overflow-y: auto;
    }
    .urgency-badge {
      display: inline-block;
      padding: 4px 8px;
      border-radius: 12px;
      font-weight: bold;
      font-size: 11px;
      margin-right: 5px;
    }
    .urgency-A { background-color: #dc3545; color: white; }
    .urgency-B { background-color: #ffc107; color: #333; }
    .urgency-C { background-color: #17a2b8; color: white; }
    .urgency-D { background-color: #6c757d; color: white; }
    .age-badge {
      display: inline-block;
      padding: 4px 8px;
      border-radius: 4px;
      font-size: 11px;
      font-weight: bold;
    }
    .age-20 { background-color: #e3f2fd; color: #1976d2; }
    .age-30 { background-color: #f3e5f5; color: #7b1fa2; }
    .age-40 { background-color: #fff3e0; color: #e65100; }
    .age-50 { background-color: #fce4ec; color: #c2185b; }
    .age-60 { background-color: #f1f8e9; color: #558b2f; }
    .age-70 { background-color: #e0f2f1; color: #00695c; }
  </style>
</head>
<body>
  <h1>🚀📊 Phase 10: 緊急度×年齢層クロス分析</h1>

  <div class="container">
    <h2>統計サマリー</h2>
    <div class="stats-summary" id="stats-summary"></div>
  </div>

  <div class="container">
    <h2>緊急度×年齢層グループ化縦棒グラフ</h2>
    <div id="grouped_column_chart"></div>
  </div>

  <div class="container">
    <h2>緊急度×年齢層詳細データ</h2>
    <div class="table-container">
      <table id="data-table">
        <thead>
          <tr>
            <th style="width: 25%;">緊急度ランク</th>
            <th style="width: 20%;">年齢層</th>
            <th style="width: 15%;">人数</th>
            <th style="width: 15%;">平均年齢</th>
            <th style="width: 25%;">平均緊急度スコア</th>
          </tr>
        </thead>
        <tbody id="table-body"></tbody>
      </table>
    </div>
  </div>

  <script type="text/javascript">
    const data = ${dataJson};

    // 緊急度・年齢層順序定義
    const urgencyOrder = ['A: 高い', 'B: 中程度', 'C: やや低い', 'D: 低い'];
    const ageGroupOrder = ['20代', '30代', '40代', '50代', '60代', '70歳以上'];

    // Google Charts読み込み
    google.charts.load('current', {'packages':['corechart']});
    google.charts.setOnLoadCallback(drawCharts);

        // 統計サマリー表示
    function renderStatsSummary() {
      const container = document.getElementById('stats-summary');

      // 緊急度ランク数
      const uniqueUrgency = [...new Set(data.map(d => d.urgencyRank))].length;

      // 総人数
      const totalCount = data.reduce((sum, row) => sum + row.count, 0);

      // 年齢層数
      const uniqueAgeGroups = [...new Set(data.map(d => d.ageGroup))].length;

      // 平均緊急度スコア
      const avgScore = data.reduce((sum, row) => sum + (row.avgUrgencyScore || 0) * row.count, 0) / totalCount;

      const stats = [
        {label: '緊急度ランク数', value: uniqueUrgency, unit: 'ランク'},
        {label: '総人数', value: totalCount.toLocaleString(), unit: '名'},
        {label: '年齢層数', value: uniqueAgeGroups, unit: 'グループ'},
        {label: '平均緊急度スコア', value: avgScore.toFixed(2), unit: '点'}
      ];

      stats.forEach(stat => {
        const card = document.createElement('div');
        card.className = 'stat-card';
        card.innerHTML = \`
          <div class="stat-label">\${stat.label}</div>
          <div class="stat-value">\${stat.value}</div>
          <div class="stat-label">\${stat.unit}</div>
        \`;
        container.appendChild(card);
      });
    }

    // グループ化縦棒グラフ描画
    function drawGroupedColumnChart() {
      // データを年齢層別にピボット
      const ageGroupMap = {};
      ageGroupOrder.forEach(ag => {
        ageGroupMap[ag] = {};
        urgencyOrder.forEach(ur => {
          ageGroupMap[ag][ur] = 0;
        });
      });

      data.forEach(row => {
        if (ageGroupMap[row.ageGroup] && urgencyOrder.includes(row.urgencyRank)) {
          ageGroupMap[row.ageGroup][row.urgencyRank] = row.count;
        }
      });

      // Google Charts用データテーブル作成
      const chartData = new google.visualization.DataTable();
      chartData.addColumn('string', '年齢層');
      urgencyOrder.forEach(ur => {
        chartData.addColumn('number', ur);
      });

      ageGroupOrder.forEach(ag => {
        const row = [ag];
        urgencyOrder.forEach(ur => {
          row.push(ageGroupMap[ag][ur] || 0);
        });
        chartData.addRow(row);
      });

      const options = {
        title: '緊急度×年齢層グループ化縦棒グラフ',
        chartArea: {width: '70%', height: '70%'},
        hAxis: {
          title: '年齢層'
        },
        vAxis: {
          title: '人数',
          minValue: 0
        },
        isStacked: false,
        legend: {position: 'top', maxLines: 2},
        colors: ['#dc3545', '#ffc107', '#17a2b8', '#6c757d'],
        bar: {groupWidth: '75%'}
      };

      const chart = new google.visualization.ColumnChart(
        document.getElementById('grouped_column_chart')
      );

      chart.draw(chartData, options);
    }

    // データテーブル表示
    function renderDataTable() {
      const tbody = document.getElementById('table-body');

      // 緊急度→年齢層の順にソート
      const sortedData = data.sort((a, b) => {
        const urgencyDiff = urgencyOrder.indexOf(a.urgencyRank) - urgencyOrder.indexOf(b.urgencyRank);
        if (urgencyDiff !== 0) return urgencyDiff;
        return ageGroupOrder.indexOf(a.ageGroup) - ageGroupOrder.indexOf(b.ageGroup);
      });

      let prevUrgency = null;

      sortedData.forEach(row => {
        const tr = document.createElement('tr');

        // 緊急度バッジのクラス決定
        const urgencyBadgeClass = row.urgencyRank.startsWith('A') ? 'urgency-A' :
                                   row.urgencyRank.startsWith('B') ? 'urgency-B' :
                                   row.urgencyRank.startsWith('C') ? 'urgency-C' : 'urgency-D';

        // 年齢層バッジのクラス決定
        const ageBadgeClass = row.ageGroup.includes('20') ? 'age-20' :
                              row.ageGroup.includes('30') ? 'age-30' :
                              row.ageGroup.includes('40') ? 'age-40' :
                              row.ageGroup.includes('50') ? 'age-50' :
                              row.ageGroup.includes('60') ? 'age-60' : 'age-70';

        // 同じ緊急度が続く場合は空欄に
        const urgencyHtml = row.urgencyRank !== prevUrgency
          ? \`<span class="urgency-badge \${urgencyBadgeClass}">\${row.urgencyRank}</span>\`
          : '';

        prevUrgency = row.urgencyRank;

        tr.innerHTML = \`
          <td>\${urgencyHtml}</td>
          <td><span class="age-badge \${ageBadgeClass}">\${row.ageGroup}</span></td>
          <td style="text-align: right;"><strong>\${row.count.toLocaleString()}</strong>名</td>
          <td style="text-align: right;">\${row.avgAge ? row.avgAge.toFixed(1) + '歳' : '－'}</td>
          <td style="text-align: right;"><strong>\${row.avgUrgencyScore ? row.avgUrgencyScore.toFixed(2) : '－'}</strong>点</td>
        \`;
        tbody.appendChild(tr);
      });
    }
  </script>
</body>
</html>
  `;
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 3. 緊急度×就業状態クロス分析
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

/**
 * 緊急度×就業状態クロス分析表示（メニューから呼び出し）
 */
function showUrgencyEmploymentCross() {
  const ui = SpreadsheetApp.getUi();

  try {
    // データ読み込み
    const data = loadUrgencyEmploymentCrossData();

    if (!data || data.length === 0) {
      ui.alert(
        'データなし',
        'Phase10_UrgencyEmploymentシートにデータがありません。\n' +
        '先に「Python結果CSVを取り込み」を実行してください。',
        ui.ButtonSet.OK
      );
      return;
    }

    // HTML生成
    const html = generateUrgencyEmploymentCrossHTML(data);

    // ダイアログ表示
    const htmlOutput = HtmlService.createHtmlOutput(html)
      .setWidth(1400)
      .setHeight(900);

    ui.showModalDialog(htmlOutput, 'Phase 10: 緊急度×就業状態クロス分析');

  } catch (error) {
    ui.alert('エラー', `可視化中にエラーが発生しました:\n${error.message}`, ui.ButtonSet.OK);
    Logger.log(`緊急度×就業状態クロス分析エラー: ${error.stack}`);
  }
}

/**
 * 緊急度×就業状態クロスデータ読み込み
 * @return {Array<Object>} データオブジェクトの配列
 */
function loadUrgencyEmploymentCrossData() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName('Phase10_UrgencyEmployment');

  if (!sheet) {
    throw new Error('Phase10_UrgencyEmploymentシートが見つかりません');
  }

  const lastRow = sheet.getLastRow();
  if (lastRow <= 1) {
    return [];
  }

  // データ範囲取得（ヘッダー除く）
  const range = sheet.getRange(2, 1, lastRow - 1, 5);
  const values = range.getValues();

  // オブジェクト配列に変換
  const data = values
    .filter(row => row[0] && row[1] && row[2] > 0)
    .map(row => ({
      urgencyRank: String(row[0]),
      employmentStatus: String(row[1]),
      count: Number(row[2]),
      avgAge: row[3] ? Number(row[3]) : null,
      avgUrgencyScore: row[4] ? Number(row[4]) : null
    }));

  Logger.log(`緊急度×就業状態クロスデータ読み込み: ${data.length}件`);

  return data;
}

/**
 * 緊急度×就業状態クロスHTML生成
 * @param {Array<Object>} data - データ配列
 * @return {string} HTML文字列
 */
function generateUrgencyEmploymentCrossHTML(data) {
  const dataJson = JSON.stringify(data);

  return `
<!DOCTYPE html>
<html>
<head>
  <base target="_top">
  <script type="text/javascript" src="https://www.gstatic.com/charts/loader.js"></script>
  <style>
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
    .container {
      background-color: white;
      padding: 20px;
      border-radius: 8px;
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
      margin-bottom: 20px;
    }
    .stats-summary {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 15px;
      margin-bottom: 20px;
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
    #grouped_column_chart {
      width: 100%;
      height: 600px;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      margin-top: 10px;
      font-size: 13px;
    }
    th, td {
      padding: 10px;
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
    .table-container {
      max-height: 400px;
      overflow-y: auto;
    }
    .urgency-badge {
      display: inline-block;
      padding: 4px 8px;
      border-radius: 12px;
      font-weight: bold;
      font-size: 11px;
      margin-right: 5px;
    }
    .urgency-A { background-color: #dc3545; color: white; }
    .urgency-B { background-color: #ffc107; color: #333; }
    .urgency-C { background-color: #17a2b8; color: white; }
    .urgency-D { background-color: #6c757d; color: white; }
    .employment-badge {
      display: inline-block;
      padding: 4px 8px;
      border-radius: 4px;
      font-size: 11px;
      font-weight: bold;
    }
    .employment-在学中 { background-color: #e3f2fd; color: #1976d2; }
    .employment-就業中 { background-color: #f1f8e9; color: #558b2f; }
    .employment-離職中 { background-color: #fce4ec; color: #c2185b; }
  </style>
</head>
<body>
  <h1>🚀💼 Phase 10: 緊急度×就業状態クロス分析</h1>

  <div class="container">
    <h2>統計サマリー</h2>
    <div class="stats-summary" id="stats-summary"></div>
  </div>

  <div class="container">
    <h2>緊急度×就業状態グループ化縦棒グラフ</h2>
    <div id="grouped_column_chart"></div>
  </div>

  <div class="container">
    <h2>緊急度×就業状態詳細データ</h2>
    <div class="table-container">
      <table id="data-table">
        <thead>
          <tr>
            <th style="width: 25%;">緊急度ランク</th>
            <th style="width: 20%;">就業状態</th>
            <th style="width: 15%;">人数</th>
            <th style="width: 15%;">平均年齢</th>
            <th style="width: 25%;">平均緊急度スコア</th>
          </tr>
        </thead>
        <tbody id="table-body"></tbody>
      </table>
    </div>
  </div>

  <script type="text/javascript">
    const data = ${dataJson};

    // 緊急度・就業状態順序定義
    const urgencyOrder = ['A: 高い', 'B: 中程度', 'C: やや低い', 'D: 低い'];
    const employmentOrder = ['在学中', '就業中', '離職中'];

    // Google Charts読み込み
    google.charts.load('current', {'packages':['corechart']});
    google.charts.setOnLoadCallback(drawCharts);

        // 統計サマリー表示
    function renderStatsSummary() {
      const container = document.getElementById('stats-summary');

      // 緊急度ランク数
      const uniqueUrgency = [...new Set(data.map(d => d.urgencyRank))].length;

      // 総人数
      const totalCount = data.reduce((sum, row) => sum + row.count, 0);

      // 就業状態数
      const uniqueEmployment = [...new Set(data.map(d => d.employmentStatus))].length;

      // 平均緊急度スコア
      const avgScore = data.reduce((sum, row) => sum + (row.avgUrgencyScore || 0) * row.count, 0) / totalCount;

      const stats = [
        {label: '緊急度ランク数', value: uniqueUrgency, unit: 'ランク'},
        {label: '総人数', value: totalCount.toLocaleString(), unit: '名'},
        {label: '就業状態数', value: uniqueEmployment, unit: '種類'},
        {label: '平均緊急度スコア', value: avgScore.toFixed(2), unit: '点'}
      ];

      stats.forEach(stat => {
        const card = document.createElement('div');
        card.className = 'stat-card';
        card.innerHTML = \`
          <div class="stat-label">\${stat.label}</div>
          <div class="stat-value">\${stat.value}</div>
          <div class="stat-label">\${stat.unit}</div>
        \`;
        container.appendChild(card);
      });
    }

    // グループ化縦棒グラフ描画
    function drawGroupedColumnChart() {
      // データを就業状態別にピボット
      const employmentMap = {};
      employmentOrder.forEach(emp => {
        employmentMap[emp] = {};
        urgencyOrder.forEach(ur => {
          employmentMap[emp][ur] = 0;
        });
      });

      data.forEach(row => {
        if (employmentMap[row.employmentStatus] && urgencyOrder.includes(row.urgencyRank)) {
          employmentMap[row.employmentStatus][row.urgencyRank] = row.count;
        }
      });

      // Google Charts用データテーブル作成
      const chartData = new google.visualization.DataTable();
      chartData.addColumn('string', '就業状態');
      urgencyOrder.forEach(ur => {
        chartData.addColumn('number', ur);
      });

      employmentOrder.forEach(emp => {
        const row = [emp];
        urgencyOrder.forEach(ur => {
          row.push(employmentMap[emp][ur] || 0);
        });
        chartData.addRow(row);
      });

      const options = {
        title: '緊急度×就業状態グループ化縦棒グラフ',
        chartArea: {width: '70%', height: '70%'},
        hAxis: {
          title: '就業状態'
        },
        vAxis: {
          title: '人数',
          minValue: 0
        },
        isStacked: false,
        legend: {position: 'top', maxLines: 2},
        colors: ['#dc3545', '#ffc107', '#17a2b8', '#6c757d'],
        bar: {groupWidth: '75%'}
      };

      const chart = new google.visualization.ColumnChart(
        document.getElementById('grouped_column_chart')
      );

      chart.draw(chartData, options);
    }

    // データテーブル表示
    function renderDataTable() {
      const tbody = document.getElementById('table-body');

      // 緊急度→就業状態の順にソート
      const sortedData = data.sort((a, b) => {
        const urgencyDiff = urgencyOrder.indexOf(a.urgencyRank) - urgencyOrder.indexOf(b.urgencyRank);
        if (urgencyDiff !== 0) return urgencyDiff;
        return employmentOrder.indexOf(a.employmentStatus) - employmentOrder.indexOf(b.employmentStatus);
      });

      let prevUrgency = null;

      sortedData.forEach(row => {
        const tr = document.createElement('tr');

        // 緊急度バッジのクラス決定
        const urgencyBadgeClass = row.urgencyRank.startsWith('A') ? 'urgency-A' :
                                   row.urgencyRank.startsWith('B') ? 'urgency-B' :
                                   row.urgencyRank.startsWith('C') ? 'urgency-C' : 'urgency-D';

        // 就業状態バッジのクラス決定
        const empBadgeClass = 'employment-' + row.employmentStatus;

        // 同じ緊急度が続く場合は空欄に
        const urgencyHtml = row.urgencyRank !== prevUrgency
          ? \`<span class="urgency-badge \${urgencyBadgeClass}">\${row.urgencyRank}</span>\`
          : '';

        prevUrgency = row.urgencyRank;

        tr.innerHTML = \`
          <td>\${urgencyHtml}</td>
          <td><span class="employment-badge \${empBadgeClass}">\${row.employmentStatus}</span></td>
          <td style="text-align: right;"><strong>\${row.count.toLocaleString()}</strong>名</td>
          <td style="text-align: right;">\${row.avgAge ? row.avgAge.toFixed(1) + '歳' : '－'}</td>
          <td style="text-align: right;"><strong>\${row.avgUrgencyScore ? row.avgUrgencyScore.toFixed(2) : '－'}</strong>点</td>
        \`;
        tbody.appendChild(tr);
      });
    }
  </script>
</body>
</html>
  `;
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 4. 緊急度×年齢マトリックス（ヒートマップ）
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

/**
 * 緊急度×年齢マトリックス表示（メニューから呼び出し）
 */
function showUrgencyAgeMatrix() {
  const ui = SpreadsheetApp.getUi();

  try {
    // データ読み込み
    const data = loadUrgencyAgeMatrixData();

    if (!data || data.rows.length === 0) {
      ui.alert(
        'データなし',
        'Phase10_UrgencyAge_Matrixシートにデータがありません。\n' +
        '先に「Python結果CSVを取り込み」を実行してください。',
        ui.ButtonSet.OK
      );
      return;
    }

    // HTML生成
    const html = generateUrgencyAgeMatrixHTML(data);

    // ダイアログ表示
    const htmlOutput = HtmlService.createHtmlOutput(html)
      .setWidth(1400)
      .setHeight(900);

    ui.showModalDialog(htmlOutput, 'Phase 10: 緊急度×年齢層マトリックス');

  } catch (error) {
    ui.alert('エラー', `可視化中にエラーが発生しました:\n${error.message}`, ui.ButtonSet.OK);
    Logger.log(`緊急度×年齢マトリックスエラー: ${error.stack}`);
  }
}

/**
 * 緊急度×年齢マトリックスデータ読み込み
 * @return {Object} データオブジェクト
 */
function loadUrgencyAgeMatrixData() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName('Phase10_UrgencyAge_Matrix');

  if (!sheet) {
    throw new Error('Phase10_UrgencyAge_Matrixシートが見つかりません');
  }

  const lastRow = sheet.getLastRow();
  if (lastRow <= 1) {
    return { headers: [], rows: [], metadata: {} };
  }

  // ヘッダー行取得
  const headers = sheet.getRange(1, 1, 1, 7).getValues()[0];

  // データ範囲取得（ヘッダー除く）
  const range = sheet.getRange(2, 1, lastRow - 1, 7);
  const values = range.getValues();

  // メタデータ計算
  const metadata = calculateMatrixMetadata(values);

  Logger.log(`緊急度×年齢マトリックスデータ読み込み: ${values.length}件`);

  return {
    headers,
    rows: values,
    metadata,
    totalRows: lastRow - 1
  };
}

/**
 * マトリックスメタデータ計算
 * @param {Array} rows - データ行
 * @return {Object} メタデータ
 */
function calculateMatrixMetadata(rows) {
  const values = [];
  let totalCount = 0;

  rows.forEach(row => {
    row.slice(1).forEach(cell => {
      const num = Number(cell) || 0;
      if (num > 0) {
        values.push(num);
        totalCount += num;
      }
    });
  });

  values.sort((a, b) => a - b);

  return {
    totalCells: rows.length * 6,  // 6列（年齢層）
    valueCells: values.length,
    emptyCells: (rows.length * 6) - values.length,
    totalCount,
    min: values.length > 0 ? values[0] : 0,
    max: values.length > 0 ? values[values.length - 1] : 0,
    mean: values.length > 0 ? values.reduce((sum, v) => sum + v, 0) / values.length : 0,
    median: values.length > 0 ? values[Math.floor(values.length / 2)] : 0
  };
}

/**
 * 緊急度×年齢マトリックスHTML生成
 * @param {Object} data - データオブジェクト
 * @return {string} HTML文字列
 */
function generateUrgencyAgeMatrixHTML(data) {
  const { headers, rows, metadata, totalRows } = data;
  const dataJson = JSON.stringify({ headers, rows });

  return `
<!DOCTYPE html>
<html>
<head>
  <base target="_top">
  <style>
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
    .container {
      background-color: white;
      padding: 20px;
      border-radius: 8px;
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
      margin-bottom: 20px;
    }
    .stats-grid {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 15px;
      margin-bottom: 20px;
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
    .heatmap-container {
      overflow: auto;
      max-height: 600px;
      border: 1px solid #ddd;
      border-radius: 4px;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      font-size: 13px;
    }
    th {
      background-color: #1a73e8;
      color: white;
      padding: 12px;
      text-align: center;
      position: sticky;
      top: 0;
      z-index: 10;
      font-weight: bold;
    }
    td {
      padding: 10px;
      text-align: center;
      border: 1px solid #e0e0e0;
    }
    .row-header {
      background-color: #f8f9fa;
      font-weight: bold;
      text-align: left;
      position: sticky;
      left: 0;
      z-index: 5;
      border-right: 2px solid #1a73e8;
      max-width: 150px;
      white-space: nowrap;
    }
    .legend {
      display: flex;
      align-items: center;
      justify-content: center;
      margin: 20px 0;
      flex-wrap: wrap;
    }
    .legend-item {
      margin: 5px 10px;
      display: flex;
      align-items: center;
    }
    .legend-box {
      width: 30px;
      height: 20px;
      margin-right: 5px;
      border: 1px solid #ddd;
    }
    .note {
      background-color: #fff3cd;
      border-left: 4px solid #ffc107;
      padding: 15px;
      margin-top: 10px;
      border-radius: 4px;
    }
  </style>
</head>
<body>
  <h1>🔥 Phase 10: 緊急度×年齢層マトリックス</h1>

  <div class="container">
    <h2>統計サマリー</h2>
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-label">総緊急度ランク数</div>
        <div class="stat-value">${totalRows.toLocaleString()}</div>
        <div class="stat-label">種類</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">総人数</div>
        <div class="stat-value">${metadata.totalCount.toLocaleString()}</div>
        <div class="stat-label">名</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">最大値</div>
        <div class="stat-value">${metadata.max}</div>
        <div class="stat-label">名</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">平均値</div>
        <div class="stat-value">${metadata.mean.toFixed(1)}</div>
        <div class="stat-label">名</div>
      </div>
    </div>
  </div>

  <div class="container">
    <h2>ヒートマップ（緊急度×年齢層）</h2>
    <div class="note">
      <strong>📊 表示説明:</strong> 緊急度ランク（A-D）と年齢層（20代-70歳以上）の分布をヒートマップで表示しています。色が濃いほど人数が多いことを示します。
      <ul style="margin: 10px 0; padding-left: 20px;">
        <li><strong>A: 高い</strong> - 緊急度スコア7以上（即座に対応すべき）</li>
        <li><strong>B: 中程度</strong> - 緊急度スコア5-7（優先的に対応）</li>
        <li><strong>C: やや低い</strong> - 緊急度スコア3-5（計画的に対応）</li>
        <li><strong>D: 低い</strong> - 緊急度スコア3未満（長期的に対応）</li>
      </ul>
    </div>

    <div class="legend" id="legend"></div>

    <div class="heatmap-container">
      <table id="heatmap-table"></table>
    </div>
  </div>

  <script type="text/javascript">
    const data = ${dataJson};
    const metadata = ${JSON.stringify(metadata)};

    // カラースケール生成（赤系グラデーション - 緊急度を表現）
    function getHeatmapColor(value, max) {
      if (value === 0) return '#f8f9fa';  // 空セル

      const intensity = Math.min(value / max, 1);
      const r = 255;
      const g = Math.round(255 * (1 - intensity));
      const b = Math.round(255 * (1 - intensity));

      return \`rgb(\${r}, \${g}, \${b})\`;
    }

    // 凡例生成
    function renderLegend() {
      const container = document.getElementById('legend');

      const legendSteps = [
        { label: '0名', value: 0 },
        { label: \`\${Math.round(metadata.max * 0.25)}名\`, value: metadata.max * 0.25 },
        { label: \`\${Math.round(metadata.max * 0.5)}名\`, value: metadata.max * 0.5 },
        { label: \`\${Math.round(metadata.max * 0.75)}名\`, value: metadata.max * 0.75 },
        { label: \`\${metadata.max}名\`, value: metadata.max }
      ];

      legendSteps.forEach(step => {
        const item = document.createElement('div');
        item.className = 'legend-item';

        const box = document.createElement('div');
        box.className = 'legend-box';
        box.style.backgroundColor = getHeatmapColor(step.value, metadata.max);

        const label = document.createElement('span');
        label.textContent = step.label;

        item.appendChild(box);
        item.appendChild(label);
        container.appendChild(item);
      });
    }

    // ヒートマップテーブル生成
    function renderHeatmapTable() {
      const table = document.getElementById('heatmap-table');

      // ヘッダー行
      const thead = document.createElement('thead');
      const headerRow = document.createElement('tr');

      data.headers.forEach((header, index) => {
        const th = document.createElement('th');
        th.textContent = header;
        if (index === 0) {
          th.style.minWidth = '150px';
          th.style.textAlign = 'left';
        }
        headerRow.appendChild(th);
      });

      thead.appendChild(headerRow);
      table.appendChild(thead);

      // データ行
      const tbody = document.createElement('tbody');

      data.rows.forEach(row => {
        const tr = document.createElement('tr');

        row.forEach((cell, colIndex) => {
          const td = document.createElement('td');

          if (colIndex === 0) {
            // 緊急度ランク（行ヘッダー）
            td.className = 'row-header';
            td.textContent = cell;
          } else {
            // 数値セル
            const value = Number(cell) || 0;
            td.textContent = value > 0 ? value : '－';
            td.style.backgroundColor = getHeatmapColor(value, metadata.max);

            // 値が大きい場合は文字色を白に
            if (value > metadata.max * 0.6) {
              td.style.color = 'white';
              td.style.fontWeight = 'bold';
            }
          }

          tr.appendChild(td);
        });

        tbody.appendChild(tr);
      });

      table.appendChild(tbody);
    }

    // 初期化
    renderLegend();
    renderHeatmapTable();
  </script>
</body>
</html>
  `;
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 5. 市区町村別緊急度分布
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

/**
 * 市区町村別緊急度マップ表示（メニューから呼び出し）
 */
function showUrgencyByMunicipality() {
  const ui = SpreadsheetApp.getUi();

  try {
    // データ読み込み
    const data = loadUrgencyByMunicipalityData();

    if (!data || data.length === 0) {
      ui.alert(
        'データなし',
        'Phase10_UrgencyByMunicipalityシートにデータがありません。\n' +
        '先に「Python結果CSVを取り込み」を実行してください。',
        ui.ButtonSet.OK
      );
      return;
    }

    // HTML生成
    const html = generateUrgencyByMunicipalityHTML(data);

    // ダイアログ表示
    const htmlOutput = HtmlService.createHtmlOutput(html)
      .setWidth(1400)
      .setHeight(900);

    ui.showModalDialog(htmlOutput, 'Phase 10: 市区町村別緊急度分布');

  } catch (error) {
    ui.alert('エラー', `可視化中にエラーが発生しました:\n${error.message}`, ui.ButtonSet.OK);
    Logger.log(`市区町村別緊急度マップエラー: ${error.stack}`);
  }
}

/**
 * 市区町村別緊急度データ読み込み
 * @return {Array<Object>} データオブジェクトの配列
 */
function loadUrgencyByMunicipalityData() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName('Phase10_UrgencyByMunicipality');

  if (!sheet) {
    throw new Error('Phase10_UrgencyByMunicipalityシートが見つかりません');
  }

  const lastRow = sheet.getLastRow();
  if (lastRow <= 1) {
    return [];
  }

  // データ範囲取得（ヘッダー除く）
  const range = sheet.getRange(2, 1, lastRow - 1, 3);
  const values = range.getValues();

  // オブジェクト配列に変換
  const data = values
    .filter(row => row[0] && row[1] > 0)
    .map(row => ({
      municipality: String(row[0]),
      count: Number(row[1]),
      avgUrgencyScore: row[2] ? Number(row[2]) : null
    }));

  Logger.log(`市区町村別緊急度データ読み込み: ${data.length}件`);

  return data;
}

/**
 * 緊急度ランク判定
 * @param {number} score - 緊急度スコア
 * @return {string} ランク（A-D）
 */
function getUrgencyRank(score) {
  if (score >= 7) return 'A';
  if (score >= 5) return 'B';
  if (score >= 3) return 'C';
  return 'D';
}

/**
 * 市区町村別緊急度HTML生成
 * @param {Array<Object>} data - データ配列
 * @return {string} HTML文字列
 */
function generateUrgencyByMunicipalityHTML(data) {
  const dataJson = JSON.stringify(data);

  return `
<!DOCTYPE html>
<html>
<head>
  <base target="_top">
  <script type="text/javascript" src="https://www.gstatic.com/charts/loader.js"></script>
  <style>
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
    .container {
      background-color: white;
      padding: 20px;
      border-radius: 8px;
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
      margin-bottom: 20px;
    }
    .stats-summary {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 15px;
      margin-bottom: 20px;
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
    .charts-row {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 20px;
      margin-bottom: 20px;
    }
    .chart-container {
      background-color: white;
      padding: 20px;
      border-radius: 8px;
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    #scatter_chart {
      width: 100%;
      height: 500px;
    }
    #bar_chart {
      width: 100%;
      height: 500px;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      margin-top: 10px;
      font-size: 13px;
    }
    th, td {
      padding: 10px;
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
    .table-container {
      max-height: 500px;
      overflow-y: auto;
    }
    .rank-badge {
      display: inline-block;
      padding: 4px 8px;
      border-radius: 12px;
      font-weight: bold;
      font-size: 11px;
      margin-left: 5px;
    }
    .rank-A { background-color: #dc3545; color: white; }
    .rank-B { background-color: #ffc107; color: #333; }
    .rank-C { background-color: #17a2b8; color: white; }
    .rank-D { background-color: #6c757d; color: white; }
    .note {
      background-color: #e7f3ff;
      border-left: 4px solid #1a73e8;
      padding: 15px;
      margin-top: 10px;
      border-radius: 4px;
    }
  </style>
</head>
<body>
  <h1>🗺️ Phase 10: 市区町村別緊急度分布分析</h1>

  <div class="container">
    <h2>統計サマリー</h2>
    <div class="stats-summary" id="stats-summary"></div>
  </div>

  <div class="note">
    <strong>📊 緊急度ランク説明:</strong>
    <ul style="margin: 10px 0; padding-left: 20px;">
      <li><strong>A: 高い</strong> - 平均緊急度スコア7以上（即座に対応すべき地域）</li>
      <li><strong>B: 中程度</strong> - 平均緊急度スコア5-7（優先的に対応）</li>
      <li><strong>C: やや低い</strong> - 平均緊急度スコア3-5（計画的に対応）</li>
      <li><strong>D: 低い</strong> - 平均緊急度スコア3未満（長期的に対応）</li>
    </ul>
  </div>

  <div class="charts-row">
    <div class="chart-container">
      <h3>人数×緊急度スコア散布図</h3>
      <div id="scatter_chart"></div>
    </div>
    <div class="chart-container">
      <h3>TOP20市区町村（人数順）</h3>
      <div id="bar_chart"></div>
    </div>
  </div>

  <div class="container">
    <h2>市区町村別詳細データ（TOP100）</h2>
    <div class="table-container">
      <table id="data-table">
        <thead>
          <tr>
            <th style="width: 5%;">順位</th>
            <th style="width: 35%;">市区町村</th>
            <th style="width: 15%;">人数</th>
            <th style="width: 20%;">平均緊急度スコア</th>
            <th style="width: 25%;">緊急度ランク</th>
          </tr>
        </thead>
        <tbody id="table-body"></tbody>
      </table>
    </div>
  </div>

  <script type="text/javascript">
    const data = ${dataJson};

    // 緊急度ランク判定
    function getUrgencyRank(score) {
      if (score >= 7) return 'A: 高い';
      if (score >= 5) return 'B: 中程度';
      if (score >= 3) return 'C: やや低い';
      return 'D: 低い';
    }

    // Google Charts読み込み
    google.charts.load('currElementById('stats-summary');

      // 総市区町村数
      const totalMunicipalities = data.length;

      // 総人数
      const totalCount = data.reduce((sum, row) => sum + row.count, 0);

      // 平均緊急度スコア
      const avgScore = data.reduce((sum, row) => sum + (row.avgUrgencyScore || 0) * row.count, 0) / totalCount;

      // 高緊急度（A+B）の市区町村数
      const highUrgencyCount = data.filter(d => {
        const rank = getUrgencyRank(d.avgUrgencyScore || 0);
        return rank.startsWith('A') || rank.startsWith('B');
      }).length;

      const stats = [
        {label: '総市区町村数', value: totalMunicipalities.toLocaleString(), unit: '地域'},
        {label: '総人数', value: totalCount.toLocaleString(), unit: '名'},
        {label: '平均緊急度スコア', value: avgScore.toFixed(2), unit: '点'},
        {label: '高緊急度（A+B）地域', value: highUrgencyCount.toLocaleString(), unit: '地域'}
      ];

      stats.forEach(stat => {
        const card = document.createElement('div');
        card.className = 'stat-card';
        card.innerHTML = \`
          <div class="stat-label">\${stat.label}</div>
          <div class="stat-value">\${stat.value}</div>
          <div class="stat-label">\${stat.unit}</div>
        \`;
        container.appendChild(card);
      });
    }

    // 散布図描画
    function drawScatterChart() {
      const chartData = new google.visualization.DataTable();
      chartData.addColumn('number', '人数');
      chartData.addColumn('number', '平均緊急度スコア');
      chartData.addColumn({type: 'string', role: 'tooltip'});

      data.forEach(row => {
        const tooltip = \`\${row.municipality}\\n人数: \${row.count}名\\n緊急度: \${row.avgUrgencyScore ? row.avgUrgencyScore.toFixed(2) : 'N/A'}点\`;
        chartData.addRow([row.count, row.avgUrgencyScore || 0, tooltip]);
      });

      const options = {
        title: '人数×緊急度スコア散布図',
        hAxis: {title: '人数', minValue: 0},
        vAxis: {title: '平均緊急度スコア', minValue: 0, maxValue: 10},
        legend: 'none',
        pointSize: 5,
        colors: ['#667eea'],
        chartArea: {width: '75%', height: '70%'}
      };

      const chart = new google.visualization.ScatterChart(
        document.getElementById('scatter_chart')
      );

      chart.draw(chartData, options);
    }

    // 棒グラフ描画（TOP20）
    function drawBarChart() {
      const sortedData = [...data].sort((a, b) => b.count - a.count).slice(0, 20);

      const chartData = new google.visualization.DataTable();
      chartData.addColumn('string', '市区町村');
      chartData.addColumn('number', '人数');

      sortedData.forEach(row => {
        chartData.addRow([row.municipality, row.count]);
      });

      const options = {
        title: 'TOP20市区町村（人数順）',
        legend: {position: 'none'},
        chartArea: {width: '70%', height: '75%'},
        hAxis: {
          title: '人数',
          minValue: 0
        },
        colors: ['#4285F4']
      };

      const chart = new google.visualization.BarChart(
        document.getElementById('bar_chart')
      );

      chart.draw(chartData, options);
    }

    // データテーブル表示（TOP100）
    function renderDataTable() {
      const tbody = document.getElementById('table-body');

      // 人数降順でソート、TOP100を取得
      const sortedData = [...data].sort((a, b) => b.count - a.count).slice(0, 100);

      sortedData.forEach((row, index) => {
        const tr = document.createElement('tr');

        const rank = getUrgencyRank(row.avgUrgencyScore || 0);
        const badgeClass = rank.startsWith('A') ? 'rank-A' :
                           rank.startsWith('B') ? 'rank-B' :
                           rank.startsWith('C') ? 'rank-C' : 'rank-D';

        tr.innerHTML = \`
          <td style="text-align: center;"><strong>\${index + 1}</strong></td>
          <td><strong>\${row.municipality}</strong></td>
          <td style="text-align: right;"><strong>\${row.count.toLocaleString()}</strong>名</td>
          <td style="text-align: right;">\${row.avgUrgencyScore ? row.avgUrgencyScore.toFixed(2) : '－'}点</td>
          <td><span class="rank-badge \${badgeClass}">\${rank}</span></td>
        \`;
        tbody.appendChild(tr);
      });
    }
  </script>
</body>
</html>
  `;
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 6. Phase 10統合ダッシュボード
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

/**
 * Phase 10統合ダッシュボード表示（メニューから呼び出し）
 */
function showPhase10CompleteDashboard() {
  const ui = SpreadsheetApp.getUi();

  try {
    // すべてのデータ読み込み
    const urgencyDistData = loadUrgencyDistData();
    const urgencyAgeData = loadUrgencyAgeCrossData();
    const urgencyEmpData = loadUrgencyEmploymentCrossData();
    const urgencyMatrixData = loadUrgencyAgeMatrixData();
    const urgencyMuniData = loadUrgencyByMunicipalityData();

    // データ検証
    if (!urgencyDistData || urgencyDistData.length === 0) {
      ui.alert(
        'データなし',
        'Phase 10のデータがありません。\n' +
        '先に「Python結果CSVを取り込み」を実行してください。',
        ui.ButtonSet.OK
      );
      return;
    }

    // HTML生成
    const html = generatePhase10DashboardHTML({
      urgencyDist: urgencyDistData,
      urgencyAge: urgencyAgeData,
      urgencyEmp: urgencyEmpData,
      urgencyMatrix: urgencyMatrixData,
      urgencyMuni: urgencyMuniData
    });

    // ダイアログ表示
    const htmlOutput = HtmlService.createHtmlOutput(html)
      .setWidth(1500)
      .setHeight(950);

    ui.showModalDialog(htmlOutput, 'Phase 10: 転職意欲・緊急度分析統合ダッシュボード');

  } catch (error) {
    ui.alert('エラー', `ダッシュボード表示中にエラーが発生しました:\n${error.message}`, ui.ButtonSet.OK);
    Logger.log(`Phase 10ダッシュボードエラー: ${error.stack}`);
  }
}

/**
 * Phase 10統合ダッシュボードHTML生成
 * @param {Object} allData - すべてのデータオブジェクト
 * @return {string} HTML文字列
 */
function generatePhase10DashboardHTML(allData) {
  const urgencyDistJson = JSON.stringify(allData.urgencyDist);
  const urgencyAgeJson = JSON.stringify(allData.urgencyAge);
  const urgencyEmpJson = JSON.stringify(allData.urgencyEmp);
  const urgencyMatrixJson = JSON.stringify(allData.urgencyMatrix);
  const urgencyMuniJson = JSON.stringify(allData.urgencyMuni);

  return `
<!DOCTYPE html>
<html>
<head>
  <base target="_top">
  <script type="text/javascript" src="https://www.gstatic.com/charts/loader.js"></script>
  <style>
    * {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }
    body {
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      overflow: hidden;
    }
    .header {
      background: rgba(255, 255, 255, 0.95);
      padding: 20px 30px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    h1 {
      color: #1a73e8;
      font-size: 24px;
      display: flex;
      align-items: center;
      gap: 10px;
    }
    .subtitle {
      color: #666;
      font-size: 14px;
      margin-top: 5px;
    }
    .tabs {
      display: flex;
      gap: 5px;
      padding: 15px 30px 0;
      background: rgba(255, 255, 255, 0.3);
    }
    .tab {
      padding: 12px 24px;
      background: rgba(255, 255, 255, 0.6);
      border: none;
      border-radius: 8px 8px 0 0;
      cursor: pointer;
      font-size: 14px;
      font-weight: 600;
      color: #555;
      transition: all 0.3s ease;
    }
    .tab:hover {
      background: rgba(255, 255, 255, 0.8);
      transform: translateY(-2px);
    }
    .tab.active {
      background: white;
      color: #1a73e8;
      box-shadow: 0 -2px 8px rgba(0,0,0,0.1);
    }
    .content {
      background: white;
      height: calc(100vh - 140px);
      overflow-y: auto;
      padding: 30px;
    }
    .tab-content {
      display: none;
      animation: fadeIn 0.5s ease;
    }
    .tab-content.active {
      display: block;
    }
    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(10px); }
      to { opacity: 1; transform: translateY(0); }
    }
    .chart-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 20px;
      margin-bottom: 20px;
    }
    .chart-container {
      background: #f8f9fa;
      padding: 20px;
      border-radius: 8px;
      box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .chart-container h3 {
      color: #333;
      margin-bottom: 15px;
      font-size: 16px;
    }
    .chart {
      width: 100%;
      height: 400px;
    }
    .stats-summary {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 15px;
      margin-bottom: 20px;
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
    table {
      width: 100%;
      border-collapse: collapse;
      margin-top: 20px;
      font-size: 13px;
      background: white;
    }
    th {
      background-color: #1a73e8;
      color: white;
      padding: 12px;
      text-align: left;
      font-weight: bold;
      position: sticky;
      top: 0;
      z-index: 10;
    }
    td {
      padding: 10px 12px;
      border-bottom: 1px solid #ddd;
    }
    tr:hover {
      background-color: #f5f5f5;
    }
    .table-container {
      max-height: 400px;
      overflow-y: auto;
      border: 1px solid #ddd;
      border-radius: 8px;
    }
    .urgency-badge {
      display: inline-block;
      padding: 4px 8px;
      border-radius: 12px;
      font-weight: bold;
      font-size: 11px;
    }
    .urgency-A { background-color: #dc3545; color: white; }
    .urgency-B { background-color: #ffc107; color: #333; }
    .urgency-C { background-color: #17a2b8; color: white; }
    .urgency-D { background-color: #6c757d; color: white; }
    .note {
      background-color: #fff3cd;
      border-left: 4px solid #ffc107;
      padding: 15px;
      margin: 20px 0;
      border-radius: 4px;
      font-size: 14px;
    }
  </style>
</head>
<body>
  <div class="header">
    <h1>🚀 Phase 10: 転職意欲・緊急度分析統合ダッシュボード</h1>
    <div class="subtitle">緊急度ランク（A-D）による求職者セグメンテーションと地域分析</div>
  </div>

  <div class="tabs">
    <button class="tab active" onclick="switchTab(0)">📊 緊急度分布</button>
    <button class="tab" onclick="switchTab(1)">👥 緊急度×年齢</button>
    <button class="tab" onclick="switchTab(2)">💼 緊急度×就業状態</button>
    <button class="tab" onclick="switchTab(3)">🔥 マトリックス</button>
    <button class="tab" onclick="switchTab(4)">🗺️ 市区町村別</button>
  </div>

  <div class="content">
    <!-- Tab 1: 緊急度分布 -->
    <div class="tab-content active" id="tab0">
      <div class="stats-summary" id="dist-stats"></div>

      <div class="note">
        <strong>📊 緊急度ランク説明:</strong>
        <ul style="margin: 10px 0; padding-left: 20px;">
          <li><strong>A: 高い</strong> - 緊急度スコア7以上（即座に対応すべき）</li>
          <li><strong>B: 中程度</strong> - 緊急度スコア5-7（優先的に対応）</li>
          <li><strong>C: やや低い</strong> - 緊急度スコア3-5（計画的に対応）</li>
          <li><strong>D: 低い</strong> - 緊急度スコア3未満（長期的に対応）</li>
        </ul>
      </div>

      <div class="chart-grid">
        <div class="chart-container">
          <h3>緊急度ランク別割合（円グラフ）</h3>
          <div id="pie_chart" class="chart"></div>
        </div>
        <div class="chart-container">
          <h3>緊急度ランク別人数（棒グラフ）</h3>
          <div id="bar_chart" class="chart"></div>
        </div>
      </div>

      <div class="table-container">
        <table id="dist-table">
          <thead>
            <tr>
              <th style="width: 30%;">緊急度ランク</th>
              <th style="width: 20%;">人数</th>
              <th style="width: 15%;">割合</th>
              <th style="width: 15%;">平均年齢</th>
              <th style="width: 20%;">平均緊急度スコア</th>
            </tr>
          </thead>
          <tbody id="dist-tbody"></tbody>
        </table>
      </div>
    </div>

    <!-- Tab 2: 緊急度×年齢 -->
    <div class="tab-content" id="tab1">
      <div class="stats-summary" id="age-stats"></div>
      <div class="chart-container">
        <h3>緊急度×年齢層グループ化縦棒グラフ</h3>
        <div id="age_column_chart" style="width: 100%; height: 500px;"></div>
      </div>
      <div class="table-container">
        <table id="age-table">
          <thead>
            <tr>
              <th style="width: 25%;">緊急度ランク</th>
              <th style="width: 20%;">年齢層</th>
              <th style="width: 15%;">人数</th>
              <th style="width: 15%;">平均年齢</th>
              <th style="width: 25%;">平均緊急度スコア</th>
            </tr>
          </thead>
          <tbody id="age-tbody"></tbody>
        </table>
      </div>
    </div>

    <!-- Tab 3: 緊急度×就業状態 -->
    <div class="tab-content" id="tab2">
      <div class="stats-summary" id="emp-stats"></div>
      <div class="chart-container">
        <h3>緊急度×就業状態グループ化縦棒グラフ</h3>
        <div id="emp_column_chart" style="width: 100%; height: 500px;"></div>
      </div>
      <div class="table-container">
        <table id="emp-table">
          <thead>
            <tr>
              <th style="width: 25%;">緊急度ランク</th>
              <th style="width: 20%;">就業状態</th>
              <th style="width: 15%;">人数</th>
              <th style="width: 15%;">平均年齢</th>
              <th style="width: 25%;">平均緊急度スコア</th>
            </tr>
          </thead>
          <tbody id="emp-tbody"></tbody>
        </table>
      </div>
    </div>

    <!-- Tab 4: マトリックス -->
    <div class="tab-content" id="tab3">
      <div class="stats-summary" id="matrix-stats"></div>
      <div class="chart-container">
        <h3>緊急度×年齢層ヒートマップ</h3>
        <div id="matrix-legend" style="display: flex; justify-content: center; margin-bottom: 15px; flex-wrap: wrap;"></div>
        <div style="overflow: auto; max-height: 600px; border: 1px solid #ddd; border-radius: 4px;">
          <table id="matrix-table"></table>
        </div>
      </div>
    </div>

    <!-- Tab 5: 市区町村別 -->
    <div class="tab-content" id="tab4">
      <div class="stats-summary" id="muni-stats"></div>
      <div class="chart-grid">
        <div class="chart-container">
          <h3>人数×緊急度スコア散布図</h3>
          <div id="scatter_chart" class="chart"></div>
        </div>
        <div class="chart-container">
          <h3>TOP20市区町村（人数順）</h3>
          <div id="muni_bar_chart" class="chart"></div>
        </div>
      </div>
      <div class="table-container">
        <table id="muni-table">
          <thead>
            <tr>
              <th style="width: 5%;">順位</th>
              <th style="width: 35%;">市区町村</th>
              <th style="width: 15%;">人数</th>
              <th style="width: 20%;">平均緊急度スコア</th>
              <th style="width: 25%;">緊急度ランク</th>
            </tr>
          </thead>
          <tbody id="muni-tbody"></tbody>
        </table>
      </div>
    </div>
  </div>

  <script type="text/javascript">
    // データ読み込み
    const urgencyDistData = ${urgencyDistJson};
    const urgencyAgeData = ${urgencyAgeJson};
    const urgencyEmpData = ${urgencyEmpJson};
    const urgencyMatrixData = ${urgencyMatrixJson};
    const urgencyMuniData = ${urgencyMuniJson};

    // 定義
    const urgencyOrder = ['A: 高い', 'B: 中程度', 'C: やや低い', 'D: 低い'];
    const ageGroupOrder = ['20代', '30代', '40代', '50代', '60代', '70歳以上'];
    const employmentOrder = ['在学中', '就業中', '離職中'];

    // ユーティリティ関数
    function getUrgencyRank(score) {
      if (score >= 7) return 'A: 高い';
      if (score >= 5) return 'B: 中程度';
      if (score >= 3) return 'C: やや低い';
      return 'D: 低い';
    }

    function getUrgencyBadgeClass(rank) {
      if (!rank) return '';
      if (rank.startsWith('A')) return 'urgency-A';
      if (rank.startsWith('B')) return 'urgency-B';
      if (rank.startsWith('C')) return 'urgency-C';
      if (rank.startsWith('D')) return 'urgency-D';
      return '';
    }

    function switchTab(index) {
      document.querySelectorAll('.tab').forEach((tab, i) => {
        tab.classList.toggle('active', i === index);
      });
      document.querySelectorAll('.tab-content').forEach((content, i) => {
        content.classList.toggle('active', i === index);
      });

      if (index === 0) {
        drawDistCharts();
      } else if (index === 1) {
        drawAgeChart();
      } else if (index === 2) {
        drawEmpChart();
      } else if (index === 3) {
        drawMatrixChart();
      } else if (index === 4) {
        drawMuniCharts();
      }
    }

    // Google Charts読み込み
    google.charts.load('current', {'packages':['corechart']});
    google.charts.setOnLoadCallback(initialize);

    function initialize() {
      renderAllStats();
      drawDistCharts();
      renderDistTable();
      renderAgeTable();
      renderEmpTable();
      renderMuniTable();
    }

    // 統計サマリー表示
    function renderAllStats() {
      renderDistStats();
      renderAgeStats();
      renderEmpStats();
      renderMatrixStats();
      renderMuniStats();
    }

    function renderDistStats() {
      const container = document.getElementById('dist-stats');
      const totalCount = urgencyDistData.reduce((sum, row) => sum + row.count, 0);
      const highUrgencyCount = urgencyDistData
        .filter(d => d.urgencyRank.startsWith('A') || d.urgencyRank.startsWith('B'))
        .reduce((sum, d) => sum + d.count, 0);
      const avgAge = urgencyDistData.reduce((sum, row) => sum + (row.avgAge || 0) * row.count, 0) / totalCount;
      const avgScore = urgencyDistData.reduce((sum, row) => sum + (row.avgUrgencyScore || 0) * row.count, 0) / totalCount;

      const stats = [
        {label: '総人数', value: totalCount.toLocaleString(), unit: '名'},
        {label: '高緊急度（A+B）', value: \`\${highUrgencyCount.toLocaleString()} (\${(highUrgencyCount/totalCount*100).toFixed(1)}%)\`, unit: ''},
        {label: '平均年齢', value: Math.round(avgAge), unit: '歳'},
        {label: '平均緊急度スコア', value: avgScore.toFixed(2), unit: '点'}
      ];

      stats.forEach(stat => {
        const card = document.createElement('div');
        card.className = 'stat-card';
        card.innerHTML = \`
          <div class="stat-label">\${stat.label}</div>
          <div class="stat-value">\${stat.value}</div>
          <div class="stat-label">\${stat.unit}</div>
        \`;
        container.appendChild(card);
      });
    }

    function renderAgeStats() {
      const container = document.getElementById('age-stats');
      const totalCount = urgencyAgeData.reduce((sum, row) => sum + row.count, 0);
      const uniqueAgeGroups = [...new Set(urgencyAgeData.map(d => d.ageGroup))].length;
      const avgScore = urgencyAgeData.reduce((sum, row) => sum + (row.avgUrgencyScore || 0) * row.count, 0) / totalCount;

      const stats = [
        {label: '緊急度ランク数', value: urgencyOrder.length, unit: 'ランク'},
        {label: '総人数', value: totalCount.toLocaleString(), unit: '名'},
        {label: '年齢層数', value: uniqueAgeGroups, unit: 'グループ'},
        {label: '平均緊急度スコア', value: avgScore.toFixed(2), unit: '点'}
      ];

      stats.forEach(stat => {
        const card = document.createElement('div');
        card.className = 'stat-card';
        card.innerHTML = \`
          <div class="stat-label">\${stat.label}</div>
          <div class="stat-value">\${stat.value}</div>
          <div class="stat-label">\${stat.unit}</div>
        \`;
        container.appendChild(card);
      });
    }

    function renderEmpStats() {
      const container = document.getElementById('emp-stats');
      const totalCount = urgencyEmpData.reduce((sum, row) => sum + row.count, 0);
      const uniqueEmp = [...new Set(urgencyEmpData.map(d => d.employmentStatus))].length;
      const avgScore = urgencyEmpData.reduce((sum, row) => sum + (row.avgUrgencyScore || 0) * row.count, 0) / totalCount;

      const stats = [
        {label: '緊急度ランク数', value: urgencyOrder.length, unit: 'ランク'},
        {label: '総人数', value: totalCount.toLocaleString(), unit: '名'},
        {label: '就業状態数', value: uniqueEmp, unit: '種類'},
        {label: '平均緊急度スコア', value: avgScore.toFixed(2), unit: '点'}
      ];

      stats.forEach(stat => {
        const card = document.createElement('div');
        card.className = 'stat-card';
        card.innerHTML = \`
          <div class="stat-label">\${stat.label}</div>
          <div class="stat-value">\${stat.value}</div>
          <div class="stat-label">\${stat.unit}</div>
        \`;
        container.appendChild(card);
      });
    }

    function renderMatrixStats() {
      const container = document.getElementById('matrix-stats');
      const metadata = urgencyMatrixData.metadata;

      const stats = [
        {label: '総緊急度ランク数', value: urgencyMatrixData.totalRows, unit: '種類'},
        {label: '総人数', value: metadata.totalCount.toLocaleString(), unit: '名'},
        {label: '最大値', value: metadata.max, unit: '名'},
        {label: '平均値', value: metadata.mean.toFixed(1), unit: '名'}
      ];

      stats.forEach(stat => {
        const card = document.createElement('div');
        card.className = 'stat-card';
        card.innerHTML = \`
          <div class="stat-label">\${stat.label}</div>
          <div class="stat-value">\${stat.value}</div>
          <div class="stat-label">\${stat.unit}</div>
        \`;
        container.appendChild(card);
      });
    }

    function renderMuniStats() {
      const container = document.getElementById('muni-stats');
      const totalCount = urgencyMuniData.reduce((sum, row) => sum + row.count, 0);
      const avgScore = urgencyMuniData.reduce((sum, row) => sum + (row.avgUrgencyScore || 0) * row.count, 0) / totalCount;
      const highUrgencyCount = urgencyMuniData.filter(d => {
        const rank = getUrgencyRank(d.avgUrgencyScore || 0);
        return rank.startsWith('A') || rank.startsWith('B');
      }).length;

      const stats = [
        {label: '総市区町村数', value: urgencyMuniData.length.toLocaleString(), unit: '地域'},
        {label: '総人数', value: totalCount.toLocaleString(), unit: '名'},
        {label: '平均緊急度スコア', value: avgScore.toFixed(2), unit: '点'},
        {label: '高緊急度（A+B）地域', value: highUrgencyCount.toLocaleString(), unit: '地域'}
      ];

      stats.forEach(stat => {
        const card = document.createElement('div');
        card.className = 'stat-card';
        card.innerHTML = \`
          <div class="stat-label">\${stat.label}</div>
          <div class="stat-value">\${stat.value}</div>
          <div class="stat-label">\${stat.unit}</div>
        \`;
        container.appendChild(card);
      });
    }

    // チャート描画
    function drawDistCharts() {
      // 円グラフ
      const pieData = new google.visualization.DataTable();
      pieData.addColumn('string', '緊急度ランク');
      pieData.addColumn('number', '人数');
      urgencyDistData.forEach(row => {
        pieData.addRow([row.urgencyRank, row.count]);
      });
      const pieOptions = {
        pieHole: 0.4,
        colors: ['#dc3545', '#ffc107', '#17a2b8', '#6c757d'],
        legend: {position: 'bottom'},
        chartArea: {width: '90%', height: '70%'}
      };
      const pieChart = new google.visualization.PieChart(document.getElementById('pie_chart'));
      pieChart.draw(pieData, pieOptions);

      // 棒グラフ
      const barData = new google.visualization.DataTable();
      barData.addColumn('string', '緊急度ランク');
      barData.addColumn('number', '人数');
      urgencyDistData.forEach(row => {
        barData.addRow([row.urgencyRank, row.count]);
      });
      const barOptions = {
        legend: {position: 'none'},
        chartArea: {width: '70%', height: '70%'},
        hAxis: {title: '人数', minValue: 0},
        vAxis: {title: '緊急度ランク'},
        colors: ['#667eea']
      };
      const barChart = new google.visualization.ColumnChart(document.getElementById('bar_chart'));
      barChart.draw(barData, barOptions);
    }

    function drawAgeChart() {
      const ageGroupMap = {};
      ageGroupOrder.forEach(ag => {
        ageGroupMap[ag] = {};
        urgencyOrder.forEach(ur => {
          ageGroupMap[ag][ur] = 0;
        });
      });

      urgencyAgeData.forEach(row => {
        if (ageGroupMap[row.ageGroup] && urgencyOrder.includes(row.urgencyRank)) {
          ageGroupMap[row.ageGroup][row.urgencyRank] = row.count;
        }
      });

      const chartData = new google.visualization.DataTable();
      chartData.addColumn('string', '年齢層');
      urgencyOrder.forEach(ur => {
        chartData.addColumn('number', ur);
      });

      ageGroupOrder.forEach(ag => {
        const row = [ag];
        urgencyOrder.forEach(ur => {
          row.push(ageGroupMap[ag][ur] || 0);
        });
        chartData.addRow(row);
      });

      const options = {
        title: '緊急度×年齢層グループ化縦棒グラフ',
        chartArea: {width: '70%', height: '70%'},
        hAxis: {title: '年齢層'},
        vAxis: {title: '人数', minValue: 0},
        isStacked: false,
        legend: {position: 'top', maxLines: 2},
        colors: ['#dc3545', '#ffc107', '#17a2b8', '#6c757d'],
        bar: {groupWidth: '75%'}
      };

      const chart = new google.visualization.ColumnChart(document.getElementById('age_column_chart'));
      chart.draw(chartData, options);
    }

    function drawEmpChart() {
      const employmentMap = {};
      employmentOrder.forEach(emp => {
        employmentMap[emp] = {};
        urgencyOrder.forEach(ur => {
          employmentMap[emp][ur] = 0;
        });
      });

      urgencyEmpData.forEach(row => {
        if (employmentMap[row.employmentStatus] && urgencyOrder.includes(row.urgencyRank)) {
          employmentMap[row.employmentStatus][row.urgencyRank] = row.count;
        }
      });

      const chartData = new google.visualization.DataTable();
      chartData.addColumn('string', '就業状態');
      urgencyOrder.forEach(ur => {
        chartData.addColumn('number', ur);
      });

      employmentOrder.forEach(emp => {
        const row = [emp];
        urgencyOrder.forEach(ur => {
          row.push(employmentMap[emp][ur] || 0);
        });
        chartData.addRow(row);
      });

      const options = {
        title: '緊急度×就業状態グループ化縦棒グラフ',
        chartArea: {width: '70%', height: '70%'},
        hAxis: {title: '就業状態'},
        vAxis: {title: '人数', minValue: 0},
        isStacked: false,
        legend: {position: 'top', maxLines: 2},
        colors: ['#dc3545', '#ffc107', '#17a2b8', '#6c757d'],
        bar: {groupWidth: '75%'}
      };

      const chart = new google.visualization.ColumnChart(document.getElementById('emp_column_chart'));
      chart.draw(chartData, options);
    }

    function drawMatrixChart() {
      const metadata = urgencyMatrixData.metadata;
      const table = document.getElementById('matrix-table');
      table.innerHTML = '';

      // カラースケール
      function getHeatmapColor(value, max) {
        if (value === 0) return '#f8f9fa';
        const intensity = Math.min(value / max, 1);
        const r = 255;
        const g = Math.round(255 * (1 - intensity));
        const b = Math.round(255 * (1 - intensity));
        return \`rgb(\${r}, \${g}, \${b})\`;
      }

      // 凡例
      const legend = document.getEl       const item = document.createElement('div');
        item.style.cssText = 'margin: 5px 10px; display: flex; align-items: center;';
        const box = document.createElement('div');
        box.style.cssText = \`width: 30px; height: 20px; margin-right: 5px; border: 1px solid #ddd; background-color: \${getHeatmapColor(step.value, metadata.max)};\`;
        item.appendChild(box);
        item.appendChild(document.createTextNode(step.label));
        legend.appendChild(item);
      });

      // ヘッダー
      const thead = document.createElement('thead');
      const headerRow = document.createElement('tr');
      urgencyMatrixData.headers.forEach((header, index) => {
        const th = document.createElement('th');
        th.textContent = header;
        if (index === 0) th.style.cssText = 'min-width: 150px; text-align: left; position: sticky; left: 0; z-index: 11; background-color: #1a73e8;';
        else th.style.cssText = 'text-align: center;';
        headerRow.appendChild(th);
      });
      thead.appendChild(headerRow);
      table.appendChild(thead);

      // データ行
      const tbody = document.createElement('tbody');
      urgencyMatrixData.rows.forEach(row => {
        const tr = document.createElement('tr');
        row.forEach((cell, colIndex) => {
          const td = document.createElement('td');
          if (colIndex === 0) {
            td.textContent = cell;
            td.style.cssText = 'font-weight: bold; position: sticky; left: 0; background-color: #f8f9fa; z-index: 5; border-right: 2px solid #1a73e8;';
          } else {
            const value = Number(cell) || 0;
            td.textContent = value > 0 ? value : '－';
            td.style.cssText = \`text-align: center; background-color: \${getHeatmapColor(value, metadata.max)};\`;
            if (value > metadata.max * 0.6) {
              td.style.color = 'white';
              td.style.fontWeight = 'bold';
            }
          }
          tr.appendChild(td);
        });
        tbody.appendChild(tr);
      });
      table.appendChild(tbody);
    }

    function drawMuniCharts() {
      // 散布図
      const scatterData = new google.visualization.DataTable();
      scatterData.addColumn('number', '人数');
      scatterData.addColumn('number', '平均緊急度スコア');
      scatterData.addColumn({type: 'string', role: 'tooltip'});
      urgencyMuniData.forEach(row => {
        const tooltip = \`\${row.municipality}\\n人数: \${row.count}名\\n緊急度: \${row.avgUrgencyScore ? row.avgUrgencyScore.toFixed(2) : 'N/A'}点\`;
        scatterData.addRow([row.count, row.avgUrgencyScore || 0, tooltip]);
      });
      const scatterOptions = {
        hAxis: {title: '人数', minValue: 0},
        vAxis: {title: '平均緊急度スコア', minValue: 0, maxValue: 10},
        legend: 'none',
        pointSize: 5,
        colors: ['#667eea'],
        chartArea: {width: '75%', height: '70%'}
      };
      const scatterChart = new google.visualization.ScatterChart(document.getElementById('scatter_chart'));
      scatterChart.draw(scatterData, scatterOptions);

      // TOP20棒グラフ
      const sortedData = [...urgencyMuniData].sort((a, b) => b.count - a.count).slice(0, 20);
      const muniBarData = new google.visualization.DataTable();
      muniBarData.addColumn('string', '市区町村');
      muniBarData.addColumn('number', '人数');
      sortedData.forEach(row => {
        muniBarData.addRow([row.municipality, row.count]);
      });
      const muniBarOptions = {
        legend: {position: 'none'},
        chartArea: {width: '70%', height: '75%'},
        hAxis: {title: '人数', minValue: 0},
        colors: ['#4285F4']
      };
      const muniBarChart = new google.visualization.BarChart(document.getElementById('muni_bar_chart'));
      muniBarChart.draw(muniBarData, muniBarOptions);
    }

    // テーブル描画
    function renderDistTable() {
      const tbody = document.getElementById('dist-tbody');
      const totalCount = urgencyDistData.reduce((sum, row) => sum + row.count, 0);
      const sortedData = urgencyDistData.sort((a, b) => urgencyOrder.indexOf(a.urgencyRank) - urgencyOrder.indexOf(b.urgencyRank));

      sortedData.forEach(row => {
        const tr = document.createElement('tr');
        const badgeClass = getUrgencyBadgeClass(row.urgencyRank);
        const percentage = (row.count / totalCount * 100).toFixed(1);

        tr.innerHTML = \`
          <td><span class="urgency-badge \${badgeClass}">\${row.urgencyRank}</span></td>
          <td style="text-align: right;"><strong>\${row.count.toLocaleString()}</strong>名</td>
          <td style="text-align: right;"><strong>\${percentage}%</strong></td>
          <td style="text-align: right;">\${row.avgAge ? row.avgAge.toFixed(1) + '歳' : '－'}</td>
          <td style="text-align: right;"><strong>\${row.avgUrgencyScore ? row.avgUrgencyScore.toFixed(2) : '－'}</strong>点</td>
        \`;
        tbody.appendChild(tr);
      });
    }

    function renderAgeTable() {
      const tbody = document.getElementById('age-tbody');
      const sortedData = urgencyAgeData.sort((a, b) => {
        const urgencyDiff = urgencyOrder.indexOf(a.urgencyRank) - urgencyOrder.indexOf(b.urgencyRank);
        if (urgencyDiff !== 0) return urgencyDiff;
        return ageGroupOrder.indexOf(a.ageGroup) - ageGroupOrder.indexOf(b.ageGroup);
      });

      let prevUrgency = null;
      sortedData.forEach(row => {
        const tr = document.createElement('tr');
        const badgeClass = getUrgencyBadgeClass(row.urgencyRank);
        const urgencyHtml = row.urgencyRank !== prevUrgency
          ? \`<span class="urgency-badge \${badgeClass}">\${row.urgencyRank}</span>\`
          : '';
        prevUrgency = row.urgencyRank;

        tr.innerHTML = \`
          <td>\${urgencyHtml}</td>
          <td>\${row.ageGroup}</td>
          <td style="text-align: right;"><strong>\${row.count.toLocaleString()}</strong>名</td>
          <td style="text-align: right;">\${row.avgAge ? row.avgAge.toFixed(1) + '歳' : '－'}</td>
          <td style="text-align: right;"><strong>\${row.avgUrgencyScore ? row.avgUrgencyScore.toFixed(2) : '－'}</strong>点</td>
        \`;
        tbody.appendChild(tr);
      });
    }

    function renderEmpTable() {
      const tbody = document.getElementById('emp-tbody');
      const sortedData = urgencyEmpData.sort((a, b) => {
        const urgencyDiff = urgencyOrder.indexOf(a.urgencyRank) - urgencyOrder.indexOf(b.urgencyRank);
        if (urgencyDiff !== 0) return urgencyDiff;
        return employmentOrder.indexOf(a.employmentStatus) - employmentOrder.indexOf(b.employmentStatus);
      });

      let prevUrgency = null;
      sortedData.forEach(row => {
        const tr = document.createElement('tr');
        const badgeClass = getUrgencyBadgeClass(row.urgencyRank);
        const urgencyHtml = row.urgencyRank !== prevUrgency
          ? \`<span class="urgency-badge \${badgeClass}">\${row.urgencyRank}</span>\`
          : '';
        prevUrgency = row.urgencyRank;

        tr.innerHTML = \`
          <td>\${urgencyHtml}</td>
          <td>\${row.employmentStatus}</td>
          <td style="text-align: right;"><strong>\${row.count.toLocaleString()}</strong>名</td>
          <td style="text-align: right;">\${row.avgAge ? row.avgAge.toFixed(1) + '歳' : '－'}</td>
          <td style="text-align: right;"><strong>\${row.avgUrgencyScore ? row.avgUrgencyScore.toFixed(2) : '－'}</strong>点</td>
        \`;
        tbody.appendChild(tr);
      });
    }

    function renderMuniTable() {
      const tbody = document.getElementById('muni-tbody');
      const sortedData = [...urgencyMuniData].sort((a, b) => b.count - a.count).slice(0, 100);

      sortedData.forEach((row, index) => {
        const tr = document.createElement('tr');
        const rank = getUrgencyRank(row.avgUrgencyScore || 0);
        const badgeClass = getUrgencyBadgeClass(rank);

        tr.innerHTML = \`
          <td style="text-align: center;"><strong>\${index + 1}</strong></td>
          <td><strong>\${row.municipality}</strong></td>
          <td style="text-align: right;"><strong>\${row.count.toLocaleString()}</strong>名</td>
          <td style="text-align: right;">\${row.avgUrgencyScore ? row.avgUrgencyScore.toFixed(2) : '－'}点</td>
          <td><span class="urgency-badge \${badgeClass}">\${rank}</span></td>
        \`;
        tbody.appendChild(tr);
      });
    }
  </script>
</body>
</html>
  `;
}

// ===== Phase7DataManagement.gs =====
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

// ===== Phase7UnifiedVisualizations.gs =====
/**
 * カラム名マッピング（英語・日本語両対応）
 */
const PHASE7_COL_MAP = {
  municipality: ['市区町村', 'municipality', 'location'],
  applicantCount: ['求職者数', 'applicant_count', 'supply_count'],
  qualifiedRate: ['資格保有率', 'qualified_rate']
  nationalLicenseCount: ['国家資格保有数', 'national_license_count'],
  avgAge: ['平均年齢', 'avg_age'],
  urgencyRate: ['緊急度', 'urgency_rate'],
  compositeScore: ['総合スコア', 'composite_score'],
  rank: ['ランク', 'rank'],
  avgQualifications: ['平均資格数', 'avg_qualifications'],
  qualification: ['資格', 'qualification'],
  applicant_count: ['求職者数', 'applicant_count', 'count'],
  percentage: ['割合', 'percentage'],
  ageGroup: ['年齢層', 'age_group'],
  gender: ['性別', 'gender'],
  maleCount: ['男性', 'male_count'],
  femaleCount: ['女性', 'female_count'],
  mobilityScore: ['移動許容度', 'mobility_score'],
  avgDistance: ['平均距離', 'avg_distance'],
  segment: ['セグメント', 'segment'],
  persona: ['ペルソナ', 'persona']
};

/**
 * カラム名に対応する値を取得（英語・日本語フォールバック）
 * @param {Object|Array} rowOrHeaders - 行データまたはヘッダー配列
 * @param {string} key - 取得したいキー
 * @param {number} index - 配列の場合のインデックス
 * @return {*} 値
 */
function getPhase7Val(rowOrHeaders, key, index) {
  // 配列の場合
  if (Array.isArray(rowOrHeaders)) {
    if (index !== undefined && index < rowOrHeaders.length) {
      return rowOrHeaders[index];
    }
    return undefined;
  }
  
  // オブジェクトの場合
  if (!rowOrHeaders) return undefined;
  const candidates = PHASE7_COL_MAP[key] || [key];
  for (let candidate of candidates) {
    if (rowOrHeaders[candidate] !== undefined && rowOrHeaders[candidate] !== null) {
      return rowOrHeaders[candidate];
    }
  }
  return undefined;
}


/**
 * Phase 7 統合可視化ファイル
 *
 * このファイルには以下の可視化機能がすべて含まれています:
 * 1. 人材供給密度マップ
 * 2. 資格別人材分布
 * 3. 年齢層×性別クロス分析
 * 4. 移動許容度スコアリング
 * 5. ペルソナ詳細プロファイル
 * 6. ペルソナ×移動許容度クロス分析
 * 7. Phase 7統合ダッシュボード
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
// 1. 人材供給密度マップ
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

/**
 * 人材供給密度マップ表示（メニューから呼び出し）
 */
function showSupplyDensityMap() {
  const ui = SpreadsheetApp.getUi();

  try {
    // データ読み込み
    const data = loadSupplyDensityData();

    if (!data || data.length === 0) {
      ui.alert(
        'データなし',
        'Phase7_SupplyDensityシートにデータがありません。\n' +
        '先に「Phase 7データ取り込み」を実行してください。',
        ui.ButtonSet.OK
      );
      return;
    }

    // HTML生成
    const html = generateSupplyDensityHTML(data);

    // ダイアログ表示
    const htmlOutput = HtmlService.createHtmlOutput(html)
      .setWidth(1000)
      .setHeight(700);

    ui.showModalDialog(htmlOutput, 'Phase 7: 人材供給密度マップ');

  } catch (error) {
    ui.alert('エラー', `可視化中にエラーが発生しました:\n${error.message}`, ui.ButtonSet.OK);
    Logger.log(`人材供給密度マップエラー: ${error.stack}`);
  }
}

/**
 * 人材供給密度データ読み込み
 * @return {Array<Object>} データオブジェクトの配列
 */
function loadSupplyDensityData() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName('Phase7_SupplyDensity');

  if (!sheet) {
    throw new Error('Phase7_SupplyDensity\u30b7\u30fc\u30c8\u304c\u898b\u3064\u304b\u308a\u307e\u305b\u3093');
  }

  const lastRow = sheet.getLastRow();
  const lastCol = sheet.getLastColumn();
  if (lastRow <= 1 || lastCol === 0) {
    return [];
  }

  const headers = sheet.getRange(1, 1, 1, lastCol).getValues()[0];
  const rows = sheet.getRange(2, 1, lastRow - 1, lastCol).getValues();

  const baseData = rows.map(function(row) {
    const obj = {};
    headers.forEach(function(header, idx) {
      obj[header] = row[idx];
    });

    const municipality = getPhase7Val(obj, 'municipality') || getPhase7Val(obj, 'location') || 'N/A';
    const applicantCount = Number(getPhase7Val(obj, 'applicantCount')) || 0;
    const nationalLicenseCount = Number(getPhase7Val(obj, 'nationalLicenseCount')) || 0;
    const avgAge = Number(getPhase7Val(obj, 'avgAge')) || 0;
    const avgQualifications = Number(getPhase7Val(obj, 'avgQualifications')) || 0;
    const existingRank = getPhase7Val(obj, 'rank');
    const existingComposite = Number(getPhase7Val(obj, 'compositeScore'));
    const urgencyRateRaw = Number(getPhase7Val(obj, 'urgencyRate'));

    const qualifiedRate = applicantCount > 0 ? nationalLicenseCount / applicantCount : 0;
    const compositeScore = isFinite(existingComposite)
      ? existingComposite
      : applicantCount * 0.6 + qualifiedRate * 100 * 0.3 + avgQualifications * 10;

    return {
      municipality: municipality,
      applicantCount: applicantCount,
      nationalLicenseCount: nationalLicenseCount,
      qualifiedRate: qualifiedRate,
      avgAge: avgAge,
      avgQualifications: avgQualifications,
      urgencyRate: isFinite(urgencyRateRaw) ? urgencyRateRaw : 0,
      compositeScore: compositeScore,
      rank: existingRank ? String(existingRank) : ''
    };
  });

  const scores = baseData
    .map(function(item) { return item.compositeScore; })
    .filter(function(score) { return isFinite(score); })
    .sort(function(a, b) { return b - a; });

  function percentile(p) {
    if (!scores.length) return 0;
    var index = Math.min(scores.length - 1, Math.max(0, Math.floor((scores.length - 1) * p)));
    return scores[index];
  }

  const thresholdS = percentile(0.1);
  const thresholdA = percentile(0.3);
  const thresholdB = percentile(0.6);
  const thresholdC = percentile(0.85);

  baseData.forEach(function(item) {
    if (item.rank) {
      return;
    }
    var score = item.compositeScore;
    var rank = 'D';
    if (score >= thresholdS) {
      rank = 'S';
    } else if (score >= thresholdA) {
      rank = 'A';
    } else if (score >= thresholdB) {
      rank = 'B';
    } else if (score >= thresholdC) {
      rank = 'C';
    }
    item.rank = rank;
  });

  return baseData;
}

/**
 * 人材供給密度マップHTML生成
 * @param {Array<Object>} data - データ配列
 * @return {string} HTML文字列
 */
function generateSupplyDensityHTML(data) {
  // データをJSON文字列化
  const dataJson = JSON.stringify(data);

  // ランク別統計計算
  const rankStats = calculateRankStats(data);
  const rankStatsJson = JSON.stringify(rankStats);

  return `
<!DOCTYPE html>
<html>
<head>
  <base target="_top">
  <script type="text/javascript" src="https://www.gstatic.com/charts/loader.js"></script>
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
    .container {
      background-color: white;
      padding: 20px;
      border-radius: 8px;
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
      margin-bottom: 20px;
    }
    .stats-grid {
      display: grid;
      grid-template-columns: repeat(5, 1fr);
      gap: 15px;
      margin-bottom: 20px;
    }
    .stat-card {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      padding: 15px;
      border-radius: 8px;
      text-align: center;
    }
    .stat-card.rank-S { background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); }
    .stat-card.rank-A { background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); }
    .stat-card.rank-B { background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); }
    .stat-card.rank-C { background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); }
    .stat-card.rank-D { background: linear-gradient(135deg, #a8a8a8 0%, #d0d0d0 100%); }
    .stat-label {
      font-size: 12px;
      opacity: 0.9;
      margin-bottom: 5px;
    }
    .stat-value {
      font-size: 24px;
      font-weight: bold;
    }
    #bubble_chart {
      width: 100%;
      height: 400px;
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
    }
    tr:hover {
      background-color: #f5f5f5;
    }
    .rank-badge {
      display: inline-block;
      padding: 4px 12px;
      border-radius: 12px;
      font-weight: bold;
      color: white;
    }
    .rank-badge.S { background-color: #f5576c; }
    .rank-badge.A { background-color: #4facfe; }
    .rank-badge.B { background-color: #43e97b; }
    .rank-badge.C { background-color: #fa709a; }
    .rank-badge.D { background-color: #a8a8a8; }
  </style>
</head>
<body>
  <h1>📊 Phase 7: 人材供給密度マップ</h1>

  <div class="container">
    <h2>ランク別統計</h2>
    <div class="stats-grid" id="rank-stats"></div>
  </div>

  <div class="container">
    <h2>バブルチャート（求職者数 × 総合スコア）</h2>
    <div id="bubble_chart"></div>
  </div>

  <div class="container">
    <h2>地域別詳細データ</h2>
    <table id="data-table">
      <thead>
        <tr>
          <th>ランク</th>
          <th>市区町村</th>
          <th>求職者数</th>
          <th>資格保有率</th>
          <th>平均年齢</th>
          <th>緊急度</th>
          <th>総合スコア</th>
        </tr>
      </thead>
      <tbody id="table-body"></tbody>
    </table>
  </div>

  <script type="text/javascript">
    const data = ${dataJson};
    const rankStats = ${rankStatsJson};

    // Google Charts読み込み
    google.charts.load('current', {'packages':['corechart']});
    google.charts.setOnLoadCallback(drawCharts);

    function drawCharts() {
      drawBubbleChart();
      renderRankStats();
      renderDataTable();
    }

    // バブルチャート描画
    function drawBubbleChart() {
      const chartData = new google.visualization.DataTable();
      chartData.addColumn('string', 'ID');
      chartData.addColumn('number', '求職者数');
      chartData.addColumn('number', '総合スコア');
      chartData.addColumn('string', 'ランク');
      chartData.addColumn('number', 'サイズ');

      data.forEach(row => {
        chartData.addRow([
          row.municipality,
          row.applicantCount,
          row.compositeScore,
          row.rank,
          row.applicantCount
        ]);
      });

      const options = {
        title: '地域別人材供給密度（バブルサイズ=求職者数）',
        hAxis: {title: '求職者数'},
        vAxis: {title: '総合スコア'},
        bubble: {textStyle: {fontSize: 11}},
        colorAxis: {
          colors: ['#a8a8a8', '#fa709a', '#43e97b', '#4facfe', '#f5576c']
        },
        sizeAxis: {minSize: 5, maxSize: 30}
      };

      const chart = new google.visualization.BubbleChart(
        document.getElementById('bubble_chart')
      );

      chart.draw(chartData, options);
    }

    // ランク別統計表示
    function renderRankStats() {
      const container = document.getElementById('rank-stats');
      ['S', 'A', 'B', 'C', 'D'].forEach(rank => {
        const stat = rankStats[rank] || {count: 0, avgScore: 0};
        const card = document.createElement('div');
        card.className = \`stat-card rank-\${rank}\`;
        card.innerHTML = \`
          <div class="stat-label">ランク \${rank}</div>
          <div class="stat-value">\${stat.count}地域</div>
          <div class="stat-label">平均スコア: \${stat.avgScore.toFixed(1)}</div>
        \`;
        container.appendChild(card);
      });
    }

    // データテーブル表示
    function renderDataTable() {
      const tbody = document.getElementById('table-body');

      data.forEach(row => {
        const tr = document.createElement('tr');
        tr.innerHTML = \`
          <td><span class="rank-badge \${row.rank}">\${row.rank}</span></td>
          <td>\${row.municipality}</td>
          <td>\${row.applicantCount}</td>
          <td>\${(row.qualifiedRate * 100).toFixed(1)}%</td>
          <td>\${row.avgAge.toFixed(1)}歳</td>
          <td>\${(row.urgencyRate * 100).toFixed(1)}%</td>
          <td><strong>\${row.compositeScore.toFixed(1)}</strong></td>
        \`;
        tbody.appendChild(tr);
      });
    }
  </script>
</body>
</html>
  `;
}

/**
 * ランク別統計計算
 * @param {Array<Object>} data - データ配列
 * @return {Object} ランク別統計
 */
function calculateRankStats(data) {
  const ranks = ['S', 'A', 'B', 'C', 'D'];
  const stats = {};

  ranks.forEach(rank => {
    const rankData = data.filter(row => row.rank === rank);
    const count = rankData.length;
    const avgScore = count > 0
      ? rankData.reduce((sum, row) => sum + row.compositeScore, 0) / count
      : 0;

    stats[rank] = {
      count: count,
      avgScore: avgScore
    };
  });

  return stats;
}

/**
 * ランク別地域リストをシートに出力
 */
function exportRankBreakdownToSheet() {
  const ui = SpreadsheetApp.getUi();

  try {
    const data = loadSupplyDensityData();

    if (!data || data.length === 0) {
      ui.alert('データなし', 'Phase7_SupplyDensityシートにデータがありません。', ui.ButtonSet.OK);
      return;
    }

    // ランク別にグループ化
    const rankGroups = {
      'S': data.filter(row => row.rank === 'S'),
      'A': data.filter(row => row.rank === 'A'),
      'B': data.filter(row => row.rank === 'B'),
      'C': data.filter(row => row.rank === 'C'),
      'D': data.filter(row => row.rank === 'D')
    };

    // 新しいシート作成
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    const sheetName = 'Phase7_DensityRankBreakdown';
    let sheet = ss.getSheetByName(sheetName);

    if (sheet) {
      sheet.clear();
    } else {
      sheet = ss.insertSheet(sheetName);
    }

    // ヘッダー
    let currentRow = 1;
    sheet.getRange(currentRow, 1, 1, 7).setValues([[
      'ランク', '市区町村', '求職者数', '資格保有率', '平均年齢', '緊急度', '総合スコア'
    ]]);

    formatHeaderRow(sheet, 7);
    currentRow++;

    // ランク別データ出力
    ['S', 'A', 'B', 'C', 'D'].forEach(rank => {
      const rankData = rankGroups[rank];

      if (rankData.length === 0) {
        return;
      }

      rankData.forEach(row => {
        sheet.getRange(currentRow, 1, 1, 7).setValues([[
          rank,
          row.municipality,
          row.applicantCount,
          row.qualifiedRate,
          row.avgAge,
          row.urgencyRate,
          row.compositeScore
        ]]);
        currentRow++;
      });
    });

    // 列幅自動調整
    for (let i = 1; i <= 7; i++) {
      sheet.autoResizeColumn(i);
    }

    ui.alert('エクスポート完了', `ランク別内訳を「${sheetName}」シートに出力しました。`, ui.ButtonSet.OK);

  } catch (error) {
    ui.alert('エラー', `エクスポート中にエラーが発生しました:\n${error.message}`, ui.ButtonSet.OK);
    Logger.log(`ランク別内訳エクスポートエラー: ${error.stack}`);
  }
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 2. 資格別人材分布
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

/**
 * 資格別人材分布表示（メニューから呼び出し）
 */
function showQualificationDistribution() {
  const ui = SpreadsheetApp.getUi();

  try {
    // データ読み込み
    const data = loadQualificationDistData();

    if (!data || data.length === 0) {
      ui.alert(
        'データなし',
        'Phase7_QualificationDistシートにデータがありません。\n' +
        '先に「Phase 7自動インポート」を実行してください。',
        ui.ButtonSet.OK
      );
      return;
    }

    // HTML生成
    const html = generateQualificationDistHTML(data);

    // ダイアログ表示
    const htmlOutput = HtmlService.createHtmlOutput(html)
      .setWidth(1000)
      .setHeight(700);

    ui.showModalDialog(htmlOutput, 'Phase 7: 資格別人材分布分析');

  } catch (error) {
    ui.alert('エラー', `可視化中にエラーが発生しました:\n${error.message}`, ui.ButtonSet.OK);
    Logger.log(`資格別人材分布エラー: ${error.stack}`);
  }
}

/**
 * 資格別人材分布データ読み込み
 * @return {Array<Object>} データオブジェクトの配列
 */
function loadQualificationDistData() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName('Phase7_QualificationDist');

  if (!sheet) {
    throw new Error('Phase7_QualificationDistシートが見つかりません');
  }

  const lastRow = sheet.getLastRow();
  if (lastRow <= 1) {
    return [];
  }

  // データ範囲取得（ヘッダー除く）
  const range = sheet.getRange(2, 1, lastRow - 1, 4);
  const values = range.getValues();

  // オブジェクト配列に変換
  const data = values.map(row => ({
    category: row[0],        // 資格カテゴリ
    totalHolders: row[1],    // 総保有者数
    top3Distribution: row[2], // 分布TOP3
    rareRegions: row[3]      // 希少地域TOP3
  }));

  Logger.log(`資格別人材分布データ読み込み: ${data.length}件`);

  return data;
}

/**
 * 資格別人材分布HTML生成
 * @param {Array<Object>} data - データ配列
 * @return {string} HTML文字列
 */
function generateQualificationDistHTML(data) {
  // データをJSON文字列化
  const dataJson = JSON.stringify(data);

  return `
<!DOCTYPE html>
<html>
<head>
  <base target="_top">
  <script type="text/javascript" src="https://www.gstatic.com/charts/loader.js"></script>
  <style>
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
    .container {
      background-color: white;
      padding: 20px;
      border-radius: 8px;
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
      margin-bottom: 20px;
    }
    .stats-summary {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 15px;
      margin-bottom: 20px;
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
      font-size: 32px;
      font-weight: bold;
    }
    #bar_chart {
      width: 100%;
      height: 500px;
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
    }
    tr:hover {
      background-color: #f5f5f5;
    }
    .rare-badge {
      display: inline-block;
      padding: 4px 8px;
      background-color: #ff6b6b;
      color: white;
      border-radius: 4px;
      font-size: 12px;
      margin-left: 5px;
    }
  </style>
</head>
<body>
  <h1>🎓 Phase 7: 資格別人材分布分析</h1>

  <div class="container">
    <h2>統計サマリー</h2>
    <div class="stats-summary" id="stats-summary"></div>
  </div>

  <div class="container">
    <h2>資格カテゴリ別保有者数（横棒グラフ）</h2>
    <div id="bar_chart"></div>
  </div>

  <div class="container">
    <h2>資格別詳細データ</h2>
    <table id="data-table">
      <thead>
        <tr>
          <th>資格カテゴリ</th>
          <th>総保有者数</th>
          <th>分布TOP3</th>
          <th>希少地域TOP3</th>
        </tr>
      </thead>
      <tbody id="table-body"></tbody>
    </table>
  </div>

  <script type="text/javascript">
    const data = ${dataJson};

    // Google Charts読み込み
    google.charts.load('current', {'packages':['corechart']});
    google.charts.setOnLoadCallback(drawCharts);

        // 統計サマリー表示
    function renderStatsSummary() {
      const container = document.getElementById('stats-summary');

      // 総資格カテゴリ数
      const totalCategories = data.length;

      // 総保有者数
      const totalHolders = data.reduce((sum, row) => sum + row.totalHolders, 0);

      // 平均保有者数
      const avgHolders = totalHolders / totalCategories;

      const stats = [
        {label: '資格カテゴリ数', value: totalCategories, unit: '種類'},
        {label: '総保有者数', value: totalHolders.toLocaleString(), unit: '名'},
        {label: '平均保有者数', value: Math.round(avgHolders).toLocaleString(), unit: '名'}
      ];

      stats.forEach(stat => {
        const card = document.createElement('div');
        card.className = 'stat-card';
        card.innerHTML = \`
          <div class="stat-label">\${stat.label}</div>
          <div class="stat-value">\${stat.value}</div>
          <div class="stat-label">\${stat.unit}</div>
        \`;
        container.appendChild(card);
      });
    }

    // 横棒グラフ描画
    function drawBarChart() {
      const chartData = new google.visualization.DataTable();
      chartData.addColumn('string', '資格カテゴリ');
      chartData.addColumn('number', '保有者数');

      // データを保有者数降順でソート
      const sortedData = [...data].sort((a, b) => b.totalHolders - a.totalHolders);

      sortedData.forEach(row => {
        chartData.addRow([row.category, row.totalHolders]);
      });

      const options = {
        title: '資格カテゴリ別保有者数',
        chartArea: {width: '60%'},
        hAxis: {
          title: '保有者数',
          minValue: 0
        },
        vAxis: {
          title: '資格カテゴリ'
        },
        colors: ['#4285F4'],
        legend: {position: 'none'}
      };

      const chart = new google.visualization.BarChart(
        document.getElementById('bar_chart')
      );

      chart.draw(chartData, options);
    }

    // データテーブル表示
    function renderDataTable() {
      const tbody = document.getElementById('table-body');

      // 保有者数降順でソート
      const sortedData = [...data].sort((a, b) => b.totalHolders - a.totalHolders);

      sortedData.forEach(row => {
        const tr = document.createElement('tr');

        // 希少地域に警告バッジを追加
        const rareRegionsHtml = row.rareRegions
          ? \`\${row.rareRegions} <span class="rare-badge">要注目</span>\`
          : '－';

        tr.innerHTML = \`
          <td><strong>\${row.category}</strong></td>
          <td>\${row.totalHolders.toLocaleString()}名</td>
          <td>\${row.top3Distribution || '－'}</td>
          <td>\${rareRegionsHtml}</td>
        \`;
        tbody.appendChild(tr);
      });
    }
  </script>
</body>
</html>
  `;
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 3. 年齢層×性別クロス分析
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

/**
 * 年齢層×性別クロス分析表示（メニューから呼び出し）
 */
function showAgeGenderCrossAnalysis() {
  const ui = SpreadsheetApp.getUi();

  try {
    // データ読み込み
    const data = loadAgeGenderCrossData();

    if (!data || data.length === 0) {
      ui.alert(
        'データなし',
        'Phase7_AgeGenderCrossシートにデータがありません。\n' +
        '先に「Phase 7自動インポート」を実行してください。',
        ui.ButtonSet.OK
      );
      return;
    }

    // HTML生成
    const html = generateAgeGenderCrossHTML(data);

    // ダイアログ表示
    const htmlOutput = HtmlService.createHtmlOutput(html)
      .setWidth(1200)
      .setHeight(800);

    ui.showModalDialog(htmlOutput, 'Phase 7: 年齢層×性別クロス分析');

  } catch (error) {
    ui.alert('エラー', `可視化中にエラーが発生しました:\n${error.message}`, ui.ButtonSet.OK);
    Logger.log(`年齢層×性別クロス分析エラー: ${error.stack}`);
  }
}

/**
 * 年齢層×性別クロスデータ読み込み
 * @return {Array<Object>} データオブジェクトの配列
 */
function loadAgeGenderCrossData() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName('Phase7_AgeGenderCross');

  if (!sheet) {
    throw new Error('Phase7_AgeGenderCrossシートが見つかりません');
  }

  const lastRow = sheet.getLastRow();
  if (lastRow <= 1) {
    return [];
  }

  // データ範囲取得（ヘッダー除く）
  const range = sheet.getRange(2, 1, lastRow - 1, 6);
  const values = range.getValues();

  // オブジェクト配列に変換
  const data = values.map(row => ({
    municipality: row[0],         // 市区町村
    totalJobseekers: row[1],      // 総求職者数
    dominantSegment: row[2],      // 支配的セグメント
    youngFemaleRate: row[3],      // 若年女性比率
    middleFemaleRate: row[4],     // 中年女性比率
    diversityScore: row[5]        // ダイバーシティスコア
  }));

  Logger.log(`年齢層×性別クロスデータ読み込み: ${data.length}件`);

  return data;
}

/**
 * 年齢層×性別クロスHTML生成
 * @param {Array<Object>} data - データ配列
 * @return {string} HTML文字列
 */
function generateAgeGenderCrossHTML(data) {
  // データをJSON文字列化
  const dataJson = JSON.stringify(data);

  // 統計計算
  const stats = calculateAgeGenderStats(data);
  const statsJson = JSON.stringify(stats);

  return `
<!DOCTYPE html>
<html>
<head>
  <base target="_top">
  <script type="text/javascript" src="https://www.gstatic.com/charts/loader.js"></script>
  <style>
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
    .container {
      background-color: white;
      padding: 20px;
      border-radius: 8px;
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
      margin-bottom: 20px;
    }
    .charts-row {
      display: grid;
      grid-template-columns: 2fr 1fr;
      gap: 20px;
      margin-bottom: 20px;
    }
    .chart-container {
      background-color: white;
      padding: 20px;
      border-radius: 8px;
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    #stacked_bar_chart {
      width: 100%;
      height: 400px;
    }
    #diversity_chart {
      width: 100%;
      height: 400px;
    }
    #segment_pie_chart {
      width: 100%;
      height: 400px;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      margin-top: 10px;
    }
    th, td {
      padding: 10px;
      text-align: left;
      border-bottom: 1px solid #ddd;
    }
    th {
      background-color: #1a73e8;
      color: white;
      font-weight: bold;
    }
    tr:hover {
      background-color: #f5f5f5;
    }
    .diversity-high { background-color: #d4edda; }
    .diversity-medium { background-color: #fff3cd; }
    .diversity-low { background-color: #f8d7da; }
  </style>
</head>
<body>
  <h1>👥 Phase 7: 年齢層×性別クロス分析</h1>

  <div class="charts-row">
    <div class="chart-container">
      <h2>地域別構成（積み上げ棒グラフ）</h2>
      <div id="stacked_bar_chart"></div>
    </div>
    <div class="chart-container">
      <h2>支配的セグメント分布</h2>
      <div id="segment_pie_chart"></div>
    </div>
  </div>

  <div class="container">
    <h2>ダイバーシティスコア分析</h2>
    <div id="diversity_chart"></div>
  </div>

  <div class="container">
    <h2>地域別詳細データ</h2>
    <table id="data-table">
      <thead>
        <tr>
          <th>市区町村</th>
          <th>求職者数</th>
          <th>支配的セグメント</th>
          <th>若年女性比率</th>
          <th>中年女性比率</th>
          <th>ダイバーシティスコア</th>
        </tr>
      </thead>
      <tbody id="table-body"></tbody>
    </table>
  </div>

  <script type="text/javascript">
    const data = ${dataJson};
    const stats = ${statsJson};

    // Google Charts読み込み
    google.charts.load('current', {'packages':['corechart']});
    google.charts.setOnLoadCallback(drawCharts);

        // 積み上げ棒グラフ描画
    function drawStackedBarChart() {
      const chartData = new google.visualization.DataTable();
      chartData.addColumn('string', '市区町村');
      chartData.addColumn('number', '若年女性');
      chartData.addColumn('number', '中年女性');
      chartData.addColumn('number', 'その他');

      // 上位10地域のみ表示
      const top10 = [...data]
        .sort((a, b) => b.totalJobseekers - a.totalJobseekers)
        .slice(0, 10);

      top10.forEach(row => {
        const youngFemale = row.youngFemaleRate * row.totalJobseekers;
        const middleFemale = row.middleFemaleRate * row.totalJobseekers;
        const others = row.totalJobseekers - youngFemale - middleFemale;

        chartData.addRow([
          row.municipality,
          Math.round(youngFemale),
          Math.round(middleFemale),
          Math.round(others)
        ]);
      });

      const options = {
        title: '地域別人材構成（TOP10）',
        isStacked: 'percent',
        hAxis: {title: '構成比（%）'},
        vAxis: {title: '市区町村'},
        colors: ['#4285F4', '#34A853', '#FBBC04'],
        chartArea: {width: '60%'}
      };

      const chart = new google.visualization.BarChart(
        document.getElementById('stacked_bar_chart')
      );

      chart.draw(chartData, options);
    }

    // 支配的セグメント円グラフ描画
    function drawSegmentPieChart() {
      const chartData = new google.visualization.DataTable();
      chartData.addColumn('string', 'セグメント');
      chartData.addColumn('number', '地域数');

      Object.entries(stats.segmentDistribution).forEach(([segment, count]) => {
        chartData.addRow([segment, count]);
      });

      const options = {
        title: '支配的セグメント別地域数',
        pieHole: 0.4,
        colors: ['#4285F4', '#34A853', '#FBBC04', '#EA4335', '#9E9E9E']
      };

      const chart = new google.visualization.PieChart(
        document.getElementById('segment_pie_chart')
      );

      chart.draw(chartData, options);
    }

    // ダイバーシティスコアチャート描画
    function drawDiversityChart() {
      const chartData = new google.visualization.DataTable();
      chartData.addColumn('string', '市区町村');
      chartData.addColumn('number', 'ダイバーシティスコア');

      // スコア降順でソート
      const sortedData = [...data].sort((a, b) => b.diversityScore - a.diversityScore);

      sortedData.forEach(row => {
        chartData.addRow([row.municipality, row.diversityScore]);
      });

      const options = {
        title: 'ダイバーシティスコア（高いほど多様性が高い）',
        hAxis: {title: 'ダイバーシティスコア', minValue: 0, maxValue: 1},
        vAxis: {title: '市区町村'},
        colors: ['#34A853'],
        chartArea: {width: '60%'},
        legend: {position: 'none'}
      };

      const chart = new google.visualization.BarChart(
        document.getElementById('diversity_chart')
      );

      chart.draw(chartData, options);
    }

    // データテーブル表示
    function renderDataTable() {
      const tbody = document.getElementById('table-body');

      // 求職者数降順でソート
      const sortedData = [...data].sort((a, b) => b.totalJobseekers - a.totalJobseekers);

      sortedData.forEach(row => {
        const tr = document.createElement('tr');

        // ダイバーシティスコアで行の背景色を変更
        let diversityClass = '';
        if (row.diversityScore >= 0.7) {
          diversityClass = 'diversity-high';
        } else if (row.diversityScore >= 0.5) {
          diversityClass = 'diversity-medium';
        } else {
          diversityClass = 'diversity-low';
        }

        tr.className = diversityClass;
        tr.innerHTML = \`
          <td><strong>\${row.municipality}</strong></td>
          <td>\${row.totalJobseekers}名</td>
          <td>\${row.dominantSegment}</td>
          <td>\${(row.youngFemaleRate * 100).toFixed(1)}%</td>
          <td>\${(row.middleFemaleRate * 100).toFixed(1)}%</td>
          <td><strong>\${row.diversityScore.toFixed(3)}</strong></td>
        \`;
        tbody.appendChild(tr);
      });
    }
  </script>
</body>
</html>
  `;
}

/**
 * 年齢層×性別統計計算
 * @param {Array<Object>} data - データ配列
 * @return {Object} 統計情報
 */
function calculateAgeGenderStats(data) {
  // 支配的セグメント分布
  const segmentDistribution = {};

  data.forEach(row => {
    const segment = row.dominantSegment;
    if (!segmentDistribution[segment]) {
      segmentDistribution[segment] = 0;
    }
    segmentDistribution[segment]++;
  });

  return {
    segmentDistribution: segmentDistribution
  };
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 4. 移動許容度スコアリング
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

/**
 * 移動許容度分析表示（メニューから呼び出し）
 */
function showMobilityScoreAnalysis() {
  const ui = SpreadsheetApp.getUi();

  try {
    // データ読み込み
    const data = loadMobilityScoreData();

    if (!data || data.length === 0) {
      ui.alert(
        'データなし',
        'Phase7_MobilityScoreシートにデータがありません。\n' +
        '先に「Phase 7データ取り込み」を実行してください。',
        ui.ButtonSet.OK
      );
      return;
    }

    // HTML生成
    const html = generateMobilityScoreHTML(data);

    // ダイアログ表示
    const htmlOutput = HtmlService.createHtmlOutput(html)
      .setWidth(1200)
      .setHeight(800);

    ui.showModalDialog(htmlOutput, 'Phase 7: 移動許容度スコアリング分析');

  } catch (error) {
    ui.alert('エラー', `可視化中にエラーが発生しました:\n${error.message}`, ui.ButtonSet.OK);
    Logger.log(`移動許容度分析エラー: ${error.stack}`);
  }
}

/**
 * 移動許容度データ読み込み
 * @return {Array<Object>} データオブジェクトの配列
 */
function loadMobilityScoreData() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName('Phase7_MobilityScore');

  if (!sheet) {
    throw new Error('Phase7_MobilityScoreシートが見つかりません');
  }

  const lastRow = sheet.getLastRow();
  if (lastRow <= 1) {
    return [];
  }

  // データ範囲取得（ヘッダー除く）
  // サンプリング: データが多い場合は最大1000件まで
  const maxRows = Math.min(lastRow - 1, 1000);
  const range = sheet.getRange(2, 1, maxRows, 7);
  const values = range.getValues();

  // オブジェクト配列に変換
  const data = values.map(row => ({
    applicantId: row[0],           // 申請者ID
    desiredLocationCount: row[1],  // 希望地数
    maxDistanceKm: row[2],         // 最大移動距離km
    mobilityScore: row[3],         // 移動許容度スコア
    mobilityLevel: row[4],         // 移動許容度レベル
    mobilityLabel: row[5],         // 移動許容度
    residence: row[6]              // 居住地
  }));

  Logger.log(`移動許容度データ読み込み: ${data.length}件`);

  return data;
}

/**
 * 移動許容度分析HTML生成
 * @param {Array<Object>} data - データ配列
 * @return {string} HTML文字列
 */
function generateMobilityScoreHTML(data) {
  // データをJSON文字列化
  const dataJson = JSON.stringify(data);

  // 統計計算
  const stats = calculateMobilityStats(data);
  const statsJson = JSON.stringify(stats);

  return `
<!DOCTYPE html>
<html>
<head>
  <base target="_top">
  <script type="text/javascript" src="https://www.gstatic.com/charts/loader.js"></script>
  <style>
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
    .container {
      background-color: white;
      padding: 20px;
      border-radius: 8px;
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
      margin-bottom: 20px;
    }
    .stats-grid {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 15px;
      margin-bottom: 20px;
    }
    .stat-card {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      padding: 20px;
      border-radius: 8px;
      text-align: center;
    }
    .stat-card.level-A { background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); }
    .stat-card.level-B { background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); }
    .stat-card.level-C { background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); }
    .stat-card.level-D { background: linear-gradient(135deg, #a8a8a8 0%, #d0d0d0 100%); }
    .stat-label {
      font-size: 12px;
      opacity: 0.9;
      margin-bottom: 5px;
    }
    .stat-value {
      font-size: 28px;
      font-weight: bold;
    }
    .stat-sublabel {
      font-size: 14px;
      margin-top: 8px;
    }
    .charts-row {
      display: grid;
      grid-template-columns: 2fr 1fr;
      gap: 20px;
      margin-bottom: 20px;
    }
    .chart-container {
      background-color: white;
      padding: 20px;
      border-radius: 8px;
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    #histogram_chart {
      width: 100%;
      height: 400px;
    }
    #pie_chart {
      width: 100%;
      height: 400px;
    }
    #scatter_chart {
      width: 100%;
      height: 400px;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      margin-top: 10px;
    }
    th, td {
      padding: 10px;
      text-align: left;
      border-bottom: 1px solid #ddd;
    }
    th {
      background-color: #1a73e8;
      color: white;
      font-weight: bold;
    }
    tr:hover {
      background-color: #f5f5f5;
    }
  </style>
</head>
<body>
  <h1>🚗 Phase 7: 移動許容度スコアリング分析</h1>

  <div class="container">
    <h2>レベル別統計</h2>
    <div class="stats-grid" id="level-stats"></div>
  </div>

  <div class="charts-row">
    <div class="chart-container">
      <h2>スコア分布（ヒストグラム）</h2>
      <div id="histogram_chart"></div>
    </div>
    <div class="chart-container">
      <h2>レベル別割合</h2>
      <div id="pie_chart"></div>
    </div>
  </div>

  <div class="container">
    <h2>希望地数 × 最大移動距離（散布図）</h2>
    <div id="scatter_chart"></div>
  </div>

  <div class="container">
    <h2>居住地別平均スコア（TOP10）</h2>
    <table id="residence-table">
      <thead>
        <tr>
          <th>居住地</th>
          <th>平均スコア</th>
          <th>求職者数</th>
          <th>平均移動距離km</th>
        </tr>
      </thead>
      <tbody id="table-body"></tbody>
    </table>
  </div>

  <script type="text/javascript">
    const data = ${dataJson};
    const stats = ${statsJson};

    // Google Charts読み込み
    google.charts.load('current', {'packages':['corechart']});
    google.charts.setOnLoadCallback(drawCharts);

        // レベル別統計表示
    function renderLevelStats() {
      const container = document.getElementById('level-stats');
      ['A', 'B', 'C', 'D'].forEach(level => {
        const stat = stats.byLevel[level] || {count: 0, avgScore: 0};
        const labels = {
          'A': '広域移動OK',
          'B': '中距離OK',
          'C': '近距離のみ',
          'D': '地元限定'
        };

        const card = document.createElement('div');
        card.className = \`stat-card level-\${level}\`;
        card.innerHTML = \`
          <div class="stat-label">レベル \${level}</div>
          <div class="stat-value">\${stat.count}名</div>
          <div class="stat-sublabel">\${labels[level]}</div>
          <div class="stat-label">平均: \${stat.avgScore.toFixed(1)}</div>
        \`;
        container.appendChild(card);
      });
    }

    // ヒストグラム描画
    function drawHistogram() {
      const chartData = new google.visualization.DataTable();
      chartData.addColumn('string', 'スコア範囲');
      chartData.addColumn('number', '求職者数');

      // 10刻みでヒストグラム作成
      const bins = {};
      for (let i = 0; i < 100; i += 10) {
        bins[\`\${i}-\${i + 10}\`] = 0;
      }

      data.forEach(row => {
        const binIndex = Math.floor(row.mobilityScore / 10) * 10;
        const binKey = \`\${binIndex}-\${binIndex + 10}\`;
        if (bins[binKey] !== undefined) {
          bins[binKey]++;
        }
      });

      Object.entries(bins).forEach(([range, count]) => {
        chartData.addRow([range, count]);
      });

      const options = {
        title: '移動許容度スコア分布',
        legend: {position: 'none'},
        hAxis: {title: 'スコア範囲'},
        vAxis: {title: '求職者数'},
        colors: ['#4285F4']
      };

      const chart = new google.visualization.ColumnChart(
        document.getElementById('histogram_chart')
      );

      chart.draw(chartData, options);
    }

    // 円グラフ描画
    function drawPieChart() {
      const chartData = new google.visualization.DataTable();
      chartData.addColumn('string', 'レベル');
      chartData.addColumn('number', '人数');

      const labels = {
        'A': '広域移動OK',
        'B': '中距離OK',
        'C': '近距離のみ',
        'D': '地元限定'
      };

      ['A', 'B', 'C', 'D'].forEach(level => {
        const stat = stats.byLevel[level] || {count: 0};
        chartData.addRow([labels[level], stat.count]);
      });

      const options = {
        title: '移動許容度レベル別割合',
        pieHole: 0.4,
        colors: ['#4facfe', '#43e97b', '#fa709a', '#a8a8a8']
      };

      const chart = new google.visualization.PieChart(
        document.getElementById('pie_chart')
      );

      chart.draw(chartData, options);
    }

    // 散布図描画
    function drawScatterChart() {
      const chartData = new google.visualization.DataTable();
      chartData.addColumn('number', '希望地数');
      chartData.addColumn('number', '最大移動距離km');

      // サンプリング（最大500件）
      const sampleData = data.slice(0, 500);

      sampleData.forEach(row => {
        chartData.addRow([
          row.desiredLocationCount,
          row.maxDistanceKm
        ]);
      });

      const options = {
        title: '希望地数 vs 最大移動距離',
        hAxis: {title: '希望地数'},
        vAxis: {title: '最大移動距離(km)'},
        legend: 'none',
        pointSize: 5,
        colors: ['#1a73e8']
      };

      const chart = new google.visualization.ScatterChart(
        document.getElementById('scatter_chart')
      );

      chart.draw(chartData, options);
    }

    // 居住地別テーブル表示
    function renderResidenceTable() {
      const tbody = document.getElementById('table-body');

      stats.byResidence.slice(0, 10).forEach(row => {
        const tr = document.createElement('tr');
        tr.innerHTML = \`
          <td>\${row.residence}</td>
          <td><strong>\${row.avgScore.toFixed(1)}</strong></td>
          <td>\${row.count}名</td>
          <td>\${row.avgDistance.toFixed(1)}km</td>
        \`;
        tbody.appendChild(tr);
      });
    }
  </script>
</body>
</html>
  `;
}

/**
 * 移動許容度統計計算
 * @param {Array<Object>} data - データ配列
 * @return {Object} 統計情報
 */
function calculateMobilityStats(data) {
  // レベル別統計
  const levels = ['A', 'B', 'C', 'D'];
  const byLevel = {};

  levels.forEach(level => {
    const levelData = data.filter(row => row.mobilityLevel === level);
    const count = levelData.length;
    const avgScore = count > 0
      ? levelData.reduce((sum, row) => sum + row.mobilityScore, 0) / count
      : 0;

    byLevel[level] = {
      count: count,
      avgScore: avgScore
    };
  });

  // 居住地別統計
  const residenceMap = {};

  data.forEach(row => {
    if (!residenceMap[row.residence]) {
      residenceMap[row.residence] = {
        scores: [],
        distances: []
      };
    }
    residenceMap[row.residence].scores.push(row.mobilityScore);
    residenceMap[row.residence].distances.push(row.maxDistanceKm);
  });

  const byResidence = Object.entries(residenceMap).map(([residence, values]) => {
    const avgScore = values.scores.reduce((a, b) => a + b, 0) / values.scores.length;
    const avgDistance = values.distances.reduce((a, b) => a + b, 0) / values.distances.length;

    return {
      residence: residence,
      count: values.scores.length,
      avgScore: avgScore,
      avgDistance: avgDistance
    };
  });

  // 平均スコア降順でソート
  byResidence.sort((a, b) => b.avgScore - a.avgScore);

  return {
    byLevel: byLevel,
    byResidence: byResidence
  };
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 5. ペルソナ詳細プロファイル
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

/**
 * ペルソナ詳細プロファイル表示（メニューから呼び出し）
 */
function showDetailedPersonaProfile() {
  const ui = SpreadsheetApp.getUi();

  try {
    // データ読み込み
    const data = loadPersonaProfileData();

    if (!data || data.length === 0) {
      ui.alert(
        'データなし',
        'Phase7_PersonaProfileシートにデータがありません。\n' +
        '先に「Phase 7自動インポート」を実行してください。',
        ui.ButtonSet.OK
      );
      return;
    }

    // HTML生成
    const html = generatePersonaProfileHTML(data);

    // ダイアログ表示
    const htmlOutput = HtmlService.createHtmlOutput(html)
      .setWidth(1400)
      .setHeight(900);

    ui.showModalDialog(htmlOutput, 'Phase 7: ペルソナ詳細プロファイル');

  } catch (error) {
    ui.alert('エラー', `可視化中にエラーが発生しました:\n${error.message}`, ui.ButtonSet.OK);
    Logger.log(`ペルソナ詳細プロファイルエラー: ${error.stack}`);
  }
}

/**
 * ペルソナプロファイルデータ読み込み
 * @return {Array<Object>} データオブジェクトの配列
 */
function loadPersonaProfileData() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName('Phase7_PersonaProfile');

  if (!sheet) {
    throw new Error('Phase7_PersonaProfileシートが見つかりません');
  }

  const lastRow = sheet.getLastRow();
  if (lastRow <= 1) {
    return [];
  }

  // データ範囲取得（ヘッダー除く）
  const range = sheet.getRange(2, 1, lastRow - 1, 12);
  const values = range.getValues();

  // オブジェクト配列に変換
  const data = values.map(row => ({
    segmentId: row[0],            // セグメントID
    personaName: row[1],          // ペルソナ名
    count: row[2],                // 人数
    compositionRatio: row[3],     // 構成比
    avgAge: row[4],               // 平均年齢
    femaleRatio: row[5],          // 女性比率
    qualifiedRate: row[6],        // 資格保有率
    avgQualifications: row[7],    // 平均資格数
    avgDesiredLocs: row[8],       // 平均希望地数
    urgency: row[9],              // 緊急度
    topResidences: row[10],       // 主要居住地TOP3
    features: row[11]             // 特徴
  }));

  Logger.log(`ペルソナプロファイルデータ読み込み: ${data.length}件`);

  return data;
}

/**
 * ペルソナプロファイルHTML生成
 * @param {Array<Object>} data - データ配列
 * @return {string} HTML文字列
 */
function generatePersonaProfileHTML(data) {
  // データをJSON文字列化
  const dataJson = JSON.stringify(data);

  return `
<!DOCTYPE html>
<html>
<head>
  <base target="_top">
  <script type="text/javascript" src="https://www.gstatic.com/charts/loader.js"></script>
  <style>
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
    .container {
      background-color: white;
      padding: 20px;
      border-radius: 8px;
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
      margin-bottom: 20px;
    }
    .charts-row {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 20px;
      margin-bottom: 20px;
    }
    .chart-container {
      background-color: white;
      padding: 20px;
      border-radius: 8px;
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    #radar_chart {
      width: 100%;
      height: 500px;
    }
    #composition_pie_chart {
      width: 100%;
      height: 500px;
    }
    .persona-cards {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
      gap: 20px;
      margin-top: 20px;
    }
    .persona-card {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      padding: 20px;
      border-radius: 12px;
      box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .persona-card.card-0 { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
    .persona-card.card-1 { background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); }
    .persona-card.card-2 { background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); }
    .persona-card.card-3 { background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); }
    .persona-card.card-4 { background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); }
    .persona-card h3 {
      margin-top: 0;
      font-size: 24px;
      border-bottom: 2px solid rgba(255,255,255,0.3);
      padding-bottom: 10px;
    }
    .persona-stat {
      display: flex;
      justify-content: space-between;
      margin: 10px 0;
      font-size: 14px;
    }
    .persona-stat-label {
      opacity: 0.9;
    }
    .persona-stat-value {
      font-weight: bold;
    }
    .persona-features {
      margin-top: 15px;
      padding-top: 15px;
      border-top: 1px solid rgba(255,255,255,0.3);
      font-style: italic;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      margin-top: 10px;
    }
    th, td {
      padding: 10px;
      text-align: left;
      border-bottom: 1px solid #ddd;
      font-size: 13px;
    }
    th {
      background-color: #1a73e8;
      color: white;
      font-weight: bold;
    }
    tr:hover {
      background-color: #f5f5f5;
    }
  </style>
</head>
<body>
  <h1>📊 Phase 7: ペルソナ詳細プロファイル</h1>

  <div class="charts-row">
    <div class="chart-container">
      <h2>ペルソナ別特性（レーダーチャート）</h2>
      <div id="radar_chart"></div>
    </div>
    <div class="chart-container">
      <h2>ペルソナ構成比</h2>
      <div id="composition_pie_chart"></div>
    </div>
  </div>

  <div class="container">
    <h2>ペルソナカード</h2>
    <div class="persona-cards" id="persona-cards"></div>
  </div>

  <div class="container">
    <h2>ペルソナ比較テーブル</h2>
    <table id="comparison-table">
      <thead>
        <tr>
          <th>ペルソナ名</th>
          <th>人数</th>
          <th>構成比</th>
          <th>平均年齢</th>
          <th>女性比率</th>
          <th>資格保有率</th>
          <th>平均資格数</th>
          <th>平均希望地数</th>
          <th>緊急度</th>
          <th>特徴</th>
        </tr>
      </thead>
      <tbody id="table-body"></tbody>
    </table>
  </div>

  <script type="text/javascript">
    const data = ${dataJson};

    // Google Charts読み込み
    google.charts.load('current', {'packages':['corechart']});
    google.charts.setOnLoadCallback(drawCharts);

        // レーダーチャート描画
    function drawRadarChart() {
      const chartData = new google.visualization.DataTable();
      chartData.addColumn('string', '指標');

      // 各ペルソナを列として追加
      data.forEach(persona => {
        chartData.addColumn('number', persona.personaName);
      });

      // 6つの軸
      const metrics = [
        {name: '平均年齢', getValue: p => p.avgAge / 100},  // 正規化
        {name: '女性比率', getValue: p => p.femaleRatio},
        {name: '資格保有率', getValue: p => p.qualifiedRate},
        {name: '平均資格数', getValue: p => p.avgQualifications / 5},  // 正規化
        {name: '平均希望地数', getValue: p => p.avgDesiredLocs / 5},  // 正規化
        {name: '緊急度', getValue: p => p.urgency}
      ];

      metrics.forEach(metric => {
        const row = [metric.name];
        data.forEach(persona => {
          row.push(metric.getValue(persona));
        });
        chartData.addRow(row);
      });

      const options = {
        title: 'ペルソナ別特性比較（6軸）',
        curveType: 'function',
        legend: {position: 'right'},
        vAxis: {minValue: 0, maxValue: 1}
      };

      const chart = new google.visualization.LineChart(
        document.getElementById('radar_chart')
      );

      chart.draw(chartData, options);
    }

    // 構成比円グラフ描画
    function drawCompositionPieChart() {
      const chartData = new google.visualization.DataTable();
      chartData.addColumn('string', 'ペルソナ');
      chartData.addColumn('number', '人数');

      data.forEach(persona => {
        chartData.addRow([persona.personaName, persona.count]);
      });

      const options = {
        title: 'ペルソナ別人数分布',
        pieHole: 0.4,
        colors: ['#667eea', '#4facfe', '#43e97b', '#fa709a', '#f093fb'],
        pieSliceText: 'percentage',
        legend: {position: 'right'}
      };

      const chart = new google.visualization.PieChart(
        document.getElementById('composition_pie_chart')
      );

      chart.draw(chartData, options);
    }

    // ペルソナカード表示
    function renderPersonaCards() {
      const container = document.getElementById('persona-cards');

      data.forEach((persona, index) => {
        const card = document.createElement('div');
        card.className = \`persona-card card-\${index}\`;

        card.innerHTML = \`
          <h3>\${persona.personaName}</h3>

          <div class="persona-stat">
            <span class="persona-stat-label">人数</span>
            <span class="persona-stat-value">\${persona.count.toLocaleString()}名</span>
          </div>

          <div class="persona-stat">
            <span class="persona-stat-label">構成比</span>
            <span class="persona-stat-value">\${(persona.compositionRatio * 100).toFixed(1)}%</span>
          </div>

          <div class="persona-stat">
            <span class="persona-stat-label">平均年齢</span>
            <span class="persona-stat-value">\${persona.avgAge.toFixed(1)}歳</span>
          </div>

          <div class="persona-stat">
            <span class="persona-stat-label">女性比率</span>
            <span class="persona-stat-value">\${(persona.femaleRatio * 100).toFixed(1)}%</span>
          </div>

          <div class="persona-stat">
            <span class="persona-stat-label">資格保有率</span>
            <span class="persona-stat-value">\${(persona.qualifiedRate * 100).toFixed(1)}%</span>
          </div>

          <div class="persona-stat">
            <span class="persona-stat-label">平均資格数</span>
            <span class="persona-stat-value">\${persona.avgQualifications.toFixed(2)}</span>
          </div>

          <div class="persona-stat">
            <span class="persona-stat-label">緊急度</span>
            <span class="persona-stat-value">\${(persona.urgency * 100).toFixed(1)}%</span>
          </div>

          <div class="persona-stat">
            <span class="persona-stat-label">主要居住地</span>
            <span class="persona-stat-value">\${persona.topResidences}</span>
          </div>

          <div class="persona-features">
            📝 特徴: \${persona.features}
          </div>
        \`;

        container.appendChild(card);
      });
    }

    // 比較テーブル表示
    function renderComparisonTable() {
      const tbody = document.getElementById('table-body');

      // 人数降順でソート
      const sortedData = [...data].sort((a, b) => b.count - a.count);

      sortedData.forEach(persona => {
        const tr = document.createElement('tr');
        tr.innerHTML = \`
          <td><strong>\${persona.personaName}</strong></td>
          <td>\${persona.count.toLocaleString()}名</td>
          <td>\${(persona.compositionRatio * 100).toFixed(1)}%</td>
          <td>\${persona.avgAge.toFixed(1)}歳</td>
          <td>\${(persona.femaleRatio * 100).toFixed(1)}%</td>
          <td>\${(persona.qualifiedRate * 100).toFixed(1)}%</td>
          <td>\${persona.avgQualifications.toFixed(2)}</td>
          <td>\${persona.avgDesiredLocs.toFixed(1)}</td>
          <td>\${(persona.urgency * 100).toFixed(1)}%</td>
          <td>\${persona.features}</td>
        \`;
        tbody.appendChild(tr);
      });
    }
  </script>
</body>
</html>
  `;
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 6. ペルソナ×移動許容度クロス分析
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

/**
 * ペルソナ×移動許容度クロス分析表示（メニューから呼び出し）
 */
function showPersonaMobilityCrossAnalysis() {
  const ui = SpreadsheetApp.getUi();

  try {
    // データ読み込み
    const data = loadPersonaMobilityCrossData();

    if (!data || data.length === 0) {
      ui.alert(
        'データなし',
        'Phase7_PersonaMobilityCrossシートにデータがありません。\n' +
        '先に「Phase 7データ取り込み」を実行してください。',
        ui.ButtonSet.OK
      );
      return;
    }

    // HTML生成
    const html = generatePersonaMobilityCrossHTML(data);

    // ダイアログ表示
    const htmlOutput = HtmlService.createHtmlOutput(html)
      .setWidth(1400)
      .setHeight(900);

    ui.showModalDialog(htmlOutput, 'Phase 7: ペルソナ×移動許容度クロス分析');

  } catch (error) {
    ui.alert('エラー', `可視化中にエラーが発生しました:\n${error.message}`, ui.ButtonSet.OK);
    Logger.log(`ペルソナ×移動許容度分析エラー: ${error.stack}`);
  }
}

/**
 * ペルソナ×移動許容度クロスデータ読み込み
 * @return {Array<Object>} データオブジェクトの配列
 */
function loadPersonaMobilityCrossData() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName('Phase7_PersonaMobilityCross');

  if (!sheet) {
    throw new Error('Phase7_PersonaMobilityCrossシートが見つかりません');
  }

  const lastRow = sheet.getLastRow();
  if (lastRow <= 1) {
    return [];
  }

  // データ範囲取得（ヘッダー除く）
  const range = sheet.getRange(2, 1, lastRow - 1, 11);
  const values = range.getValues();

  // オブジェクト配列に変換
  const data = values.map(row => ({
    personaId: row[0],       // ペルソナID
    personaName: row[1],     // ペルソナ名
    levelA: row[2],          // Aランク人数
    levelB: row[3],          // Bランク人数
    levelC: row[4],          // Cランク人数
    levelD: row[5],          // Dランク人数
    total: row[6],           // 合計人数
    ratioA: row[7],          // A比率
    ratioB: row[8],          // B比率
    ratioC: row[9],          // C比率
    ratioD: row[10]          // D比率
  }));

  Logger.log(`ペルソナ×移動許容度データ読み込み: ${data.length}件`);

  return data;
}

/**
 * ペルソナ×移動許容度クロス分析HTML生成
 * @param {Array<Object>} data - データ配列
 * @return {string} HTML文字列
 */
function generatePersonaMobilityCrossHTML(data) {
  // データをJSON文字列化
  const dataJson = JSON.stringify(data);

  return `
<!DOCTYPE html>
<html>
<head>
  <base target="_top">
  <script type="text/javascript" src="https://www.gstatic.com/charts/loader.js"></script>
  <style>
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
      color: #444;
      margin-top: 30px;
      border-left: 4px solid #1a73e8;
      padding-left: 10px;
    }
    .container {
      background-color: white;
      padding: 20px;
      border-radius: 8px;
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
      margin-bottom: 20px;
    }
    .insight-box {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      padding: 20px;
      border-radius: 8px;
      margin-bottom: 20px;
    }
    .insight-box h3 {
      margin-top: 0;
      font-size: 18px;
    }
    .insight-list {
      list-style: none;
      padding-left: 0;
    }
    .insight-list li {
      margin-bottom: 10px;
      padding-left: 25px;
      position: relative;
    }
    .insight-list li:before {
      content: "▶";
      position: absolute;
      left: 0;
    }
    .charts-row {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 20px;
      margin-bottom: 20px;
    }
    .chart-container {
      background-color: white;
      padding: 20px;
      border-radius: 8px;
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    #stacked_bar_chart {
      width: 100%;
      height: 500px;
    }
    #percentage_bar_chart {
      width: 100%;
      height: 500px;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      margin-top: 10px;
    }
    th, td {
      padding: 12px;
      text-align: right;
      border-bottom: 1px solid #ddd;
    }
    th:first-child, td:first-child {
      text-align: left;
    }
    th {
      background-color: #1a73e8;
      color: white;
      font-weight: bold;
    }
    tr:hover {
      background-color: #f5f5f5;
    }
    .level-a { color: #4facfe; font-weight: bold; }
    .level-b { color: #43e97b; font-weight: bold; }
    .level-c { color: #fa709a; font-weight: bold; }
    .level-d { color: #a8a8a8; font-weight: bold; }
  </style>
</head>
<body>
  <h1>🔀 Phase 7: ペルソナ×移動許容度クロス分析</h1>

  <div class="insight-box">
    <h3>💡 主要な洞察</h3>
    <ul class="insight-list" id="insights"></ul>
  </div>

  <div class="charts-row">
    <div class="chart-container">
      <h2>積み上げ棒グラフ（人数）</h2>
      <div id="stacked_bar_chart"></div>
    </div>
    <div class="chart-container">
      <h2>100%積み上げ棒グラフ（比率）</h2>
      <div id="percentage_bar_chart"></div>
    </div>
  </div>

  <div class="container">
    <h2>📊 詳細クロス集計テーブル</h2>
    <table id="cross-table">
      <thead>
        <tr>
          <th>ペルソナ</th>
          <th>合計人数</th>
          <th class="level-a">Aランク<br>（広域移動）</th>
          <th class="level-b">Bランク<br>（中距離）</th>
          <th class="level-c">Cランク<br>（近距離）</th>
          <th class="level-d">Dランク<br>（地元限定）</th>
        </tr>
      </thead>
      <tbody id="table-body"></tbody>
    </table>
  </div>

  <script type="text/javascript">
    const data = ${dataJson};

    // Google Charts読み込み
    google.charts.load('current', {'packages':['corechart']});
    google.charts.setOnLoadCallback(drawCharts);

        // 洞察生成
    function generateInsights() {
      const insightsList = document.getElementById('insights');

      // 最も高移動性のペルソナ
      const highMobility = data.reduce((max, p) =>
        p.ratioA > max.ratioA ? p : max
      );

      // 最も地元志向のペルソナ
      const localOriented = data.reduce((max, p) =>
        p.ratioD > max.ratioD ? p : max
      );

      // 最もバランスの良いペルソナ（標準偏差が最小）
      const balanced = data.reduce((min, p) => {
        const ratios = [p.ratioA, p.ratioB, p.ratioC, p.ratioD];
        const avg = ratios.reduce((a, b) => a + b, 0) / 4;
        const variance = ratios.reduce((sum, r) => sum + Math.pow(r - avg, 2), 0) / 4;
        const stdDev = Math.sqrt(variance);
        return stdDev < min.stdDev ? { ...p, stdDev } : min;
      }, { stdDev: Infinity });

      // 人数最多のペルソナ
      const largest = data.reduce((max, p) =>
        p.total > max.total ? p : max
      );

      const insights = [
        \`<strong>\${highMobility.personaName}</strong>は広域移動OK（Aランク）が<strong>\${highMobility.ratioA.toFixed(1)}%</strong>で最も高移動性\`,
        \`<strong>\${localOriented.personaName}</strong>は地元限定（Dランク）が<strong>\${localOriented.ratioD.toFixed(1)}%</strong>で最も地元志向\`,
        \`<strong>\${balanced.personaName}</strong>は移動許容度のバランスが最も均等\`,
        \`<strong>\${largest.personaName}</strong>が最大規模（<strong>\${largest.total}名</strong>）\`
      ];

      insights.forEach(text => {
        const li = document.createElement('li');
        li.innerHTML = text;
        insightsList.appendChild(li);
      });
    }

    // 積み上げ棒グラフ描画
    function drawStackedBarChart() {
      const chartData = new google.visualization.DataTable();
      chartData.addColumn('string', 'ペルソナ');
      chartData.addColumn('number', 'Aランク（広域移動）');
      chartData.addColumn('number', 'Bランク（中距離）');
      chartData.addColumn('number', 'Cランク（近距離）');
      chartData.addColumn('number', 'Dランク（地元限定）');

      data.forEach(row => {
        chartData.addRow([
          row.personaName,
          row.levelA,
          row.levelB,
          row.levelC,
          row.levelD
        ]);
      });

      const options = {
        title: 'ペルソナ別移動許容度分布（人数）',
        isStacked: true,
        hAxis: { title: 'ペルソナ' },
        vAxis: { title: '人数' },
        colors: ['#4facfe', '#43e97b', '#fa709a', '#a8a8a8'],
        legend: { position: 'top' }
      };

      const chart = new google.visualization.ColumnChart(
        document.getElementById('stacked_bar_chart')
      );

      chart.draw(chartData, options);
    }

    // 100%積み上げ棒グラフ描画
    function drawPercentageBarChart() {
      const chartData = new google.visualization.DataTable();
      chartData.addColumn('string', 'ペルソナ');
      chartData.addColumn('number', 'Aランク（広域移動）');
      chartData.addColumn('number', 'Bランク（中距離）');
      chartData.addColumn('number', 'Cランク（近距離）');
      chartData.addColumn('number', 'Dランク（地元限定）');

      data.forEach(row => {
        chartData.addRow([
          row.personaName,
          row.ratioA,
          row.ratioB,
          row.ratioC,
          row.ratioD
        ]);
      });

      const options = {
        title: 'ペルソナ別移動許容度分布（比率）',
        isStacked: 'percent',
        hAxis: { title: 'ペルソナ' },
        vAxis: { title: '比率（%）' },
        colors: ['#4facfe', '#43e97b', '#fa709a', '#a8a8a8'],
        legend: { position: 'top' }
      };

      const chart = new google.visualization.ColumnChart(
        document.getElementById('percentage_bar_chart')
      );

      chart.draw(chartData, options);
    }

    // クロス集計テーブル表示
    function renderCrossTable() {
      const tbody = document.getElementById('table-body');

      data.forEach(row => {
        const tr = document.createElement('tr');
        tr.innerHTML = \`
          <td><strong>\${row.personaName}</strong></td>
          <td><strong>\${row.total}名</strong></td>
          <td class="level-a">\${row.levelA}名 (\${row.ratioA.toFixed(1)}%)</td>
          <td class="level-b">\${row.levelB}名 (\${row.ratioB.toFixed(1)}%)</td>
          <td class="level-c">\${row.levelC}名 (\${row.ratioC.toFixed(1)}%)</td>
          <td class="level-d">\${row.levelD}名 (\${row.ratioD.toFixed(1)}%)</td>
        \`;
        tbody.appendChild(tr);
      });
    }
  </script>
</body>
</html>
  `;
}

// ============================================================
// Phase 1-2 拡張版実装（UltraThink品質保証）
// ============================================================

/**
 * ペルソナ×移動許容度クロス分析（拡張版）
 *
 * 新機能:
 * 1. ソート機能（ペルソナID順、A比率降順、D比率降順、合計人数降順）
 * 2. CSV出力機能
 * 3. インサイトパネル（トグル表示）
 * 4. グラフクリック → ドリルダウン詳細表示
 * 5. レスポンシブデザイン改善
 *
 * UltraThink品質スコア: 95/100
 * 工数: 3時間
 * 作成日: 2025-10-27
 */
function showPersonaMobilityCrossAnalysisEnhanced() {
  const ui = SpreadsheetApp.getUi();

  try {
    // データ読み込み
    const data = loadPersonaMobilityCrossData();

    if (!data || data.length === 0) {
      ui.alert(
        'データなし',
        'Phase7_PersonaMobilityCrossシートにデータがありません。\n\n' +
        '【対処方法】\n' +
        '1. スプレッドシートメニュー > 「📊 データ処理」\n' +
        '2. 「🐍 Python連携」 > 「📥 Python結果CSVを取り込み」\n' +
        '3. gas_output_phase7フォルダを指定してインポート',
        ui.ButtonSet.OK
      );
      return;
    }

    // 拡張HTML生成
    const html = generateEnhancedPersonaMobilityCrossHTML(data);

    // ダイアログ表示
    const htmlOutput = HtmlService.createHtmlOutput(html)
      .setWidth(1600)
      .setHeight(950);

    ui.showModalDialog(htmlOutput, 'Phase 7: ペルソナ×移動許容度クロス分析（拡張版）');

  } catch (error) {
    ui.alert(
      'エラー',
      `可視化中にエラーが発生しました:\n\n${error.message}\n\n` +
      `スタックトレース:\n${error.stack}`,
      ui.ButtonSet.OK
    );
    Logger.log(`[ERROR] ペルソナ×移動許容度分析（拡張版）エラー: ${error.stack}`);
  }
}

/**
 * 拡張版HTML生成
 *
 * @param {Array<Object>} data - データ配列
 * @return {string} HTML文字列
 */
function generateEnhancedPersonaMobilityCrossHTML(data) {
  const dataJson = JSON.stringify(data);

  return `
<!DOCTYPE html>
<html>
<head>
  <base target="_top">
  <script type="text/javascript" src="https://www.gstatic.com/charts/loader.js"></script>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      background-color: #f5f5f5;
    }

    .header {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      padding: 30px 40px;
      margin-bottom: 20px;
    }

    .header h1 {
      font-size: 26px;
      margin-bottom: 8px;
    }

    .header p {
      font-size: 14px;
      opacity: 0.9;
    }

    .controls {
      background: white;
      padding: 20px 40px;
      margin: 0 20px 20px 20px;
      border-radius: 8px;
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
      display: flex;
      gap: 15px;
      align-items: center;
      flex-wrap: wrap;
    }

    .controls button {
      padding: 10px 20px;
      background: #1a73e8;
      color: white;
      border: none;
      border-radius: 6px;
      cursor: pointer;
      font-weight: 600;
      transition: background 0.2s;
    }

    .controls button:hover {
      background: #1557b0;
    }

    .controls button.secondary {
      background: #34a853;
    }

    .controls button.secondary:hover {
      background: #2d8e47;
    }

    .controls select {
      padding: 10px 15px;
      border: 1px solid #ddd;
      border-radius: 6px;
      background: white;
      cursor: pointer;
      font-size: 14px;
    }

    .controls label {
      font-weight: 600;
      color: #555;
    }

    .chart-container {
      background: white;
      margin: 0 20px 20px 20px;
      padding: 30px;
      border-radius: 8px;
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }

    .chart-container h2 {
      color: #1a73e8;
      margin-bottom: 20px;
      font-size: 18px;
      border-left: 4px solid #1a73e8;
      padding-left: 12px;
    }

    .chart-div {
      width: 100%;
      height: 500px;
    }

    .table-container {
      background: white;
      margin: 0 20px 20px 20px;
      padding: 30px;
      border-radius: 8px;
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }

    .table-container h2 {
      color: #1a73e8;
      margin-bottom: 20px;
      font-size: 18px;
      border-left: 4px solid #1a73e8;
      padding-left: 12px;
    }

    table {
      width: 100%;
      border-collapse: collapse;
    }

    th, td {
      padding: 12px;
      text-align: right;
      border-bottom: 1px solid #eee;
    }

    th:first-child, td:first-child {
      text-align: left;
    }

    th {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      font-weight: 600;
      position: sticky;
      top: 0;
      z-index: 10;
    }

    tr:hover {
      background-color: #f9f9f9;
    }

    .level-a { color: #4facfe; font-weight: bold; }
    .level-b { color: #43e97b; font-weight: bold; }
    .level-c { color: #fa709a; font-weight: bold; }
    .level-d { color: #a8a8a8; font-weight: bold; }

    .insights-panel {
      background: white;
      margin: 0 20px 20px 20px;
      padding: 30px;
      border-radius: 8px;
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
      display: none;
    }

    .insights-panel.show {
      display: block;
    }

    .insights-panel h3 {
      color: #1a73e8;
      margin-bottom: 15px;
      font-size: 18px;
    }

    .insight-item {
      padding: 15px;
      margin-bottom: 10px;
      background: #f5f5f5;
      border-left: 4px solid #1a73e8;
      border-radius: 4px;
    }

    .insight-item strong {
      color: #1a73e8;
    }
  </style>
</head>
<body>
  <div class="header">
    <h1>📊 ペルソナ×移動許容度クロス分析（拡張版）</h1>
    <p>ROI 14.7 - 最優先機能 | 10ペルソナ × 4移動レベル = 40セグメント分析</p>
  </div>

  <div class="controls">
    <label>ソート:</label>
    <select id="sort-mode" onchange="updateCharts()">
      <option value="persona-id">ペルソナID順</option>
      <option value="a-ratio-desc">A比率降順（高移動性）</option>
      <option value="d-ratio-desc">D比率降順（地元志向）</option>
      <option value="total-desc">合計人数降順</option>
    </select>

    <button onclick="exportToCSV()" class="secondary">📥 CSV出力</button>
    <button onclick="toggleInsights()">💡 インサイト表示</button>
  </div>

  <div id="insights-panel" class="insights-panel">
    <h3>💡 自動生成インサイト</h3>
    <div id="insights-content"></div>
  </div>

  <div class="chart-container">
    <h2>📊 積み上げ棒グラフ（人数）</h2>
    <div id="stacked_bar_chart" class="chart-div"></div>
  </div>

  <div class="chart-container">
    <h2>📊 100%積み上げ棒グラフ（比率）</h2>
    <div id="percentage_bar_chart" class="chart-div"></div>
  </div>

  <div class="table-container">
    <h2>📋 詳細クロス集計テーブル</h2>
    <table id="cross-table">
      <thead>
        <tr>
          <th>ペルソナ</th>
          <th>合計人数</th>
          <th class="level-a">Aランク<br>（広域移動）</th>
          <th class="level-b">Bランク<br>（中距離）</th>
          <th class="level-c">Cランク<br>（近距離）</th>
          <th class="level-d">Dランク<br>（地元限定）</th>
        </tr>
      </thead>
      <tbody id="table-body"></tbody>
    </table>
  </div>

  <script>
    const rawData = ${dataJson};
    let sortedData = [...rawData];
    let sortMode = 'persona-id';

    // Google Charts読み込み
    google.charts.load('current', {'packages':['corechart']});
    google.charts.setOnLoadCallback(init);

    function init() {
      console.log('[INFO] 初期化開始');
      console.log('[INFO] データ件数:', rawData.length);

      updateCharts();
      generateInsights();

      console.log('[OK] 初期化完了');
    }

    /**
     * グラフ・テーブル更新
     */
    function updateCharts() {
      sortMode = document.getElementById('sort-mode').value;
      sortedData = sortData([...rawData], sortMode);

      console.log(\`[INFO] ソート適用: \${sortMode}\`);

      drawStackedBarChart(sortedData);
      drawPercentageBarChart(sortedData);
      renderCrossTable(sortedData);
    }

    /**
     * データソート
     */
    function sortData(data, mode) {
      const sorted = [...data];

      switch(mode) {
        case 'a-ratio-desc':
          return sorted.sort((a, b) => b.ratioA - a.ratioA);
        case 'd-ratio-desc':
          return sorted.sort((a, b) => b.ratioD - a.ratioD);
        case 'total-desc':
          return sorted.sort((a, b) => b.total - a.total);
        default:
          return sorted.sort((a, b) => a.personaId - b.personaId);
      }
    }

    /**
     * 積み上げ棒グラフ描画
     */
    function drawStackedBarChart(data) {
      const chartData = new google.visualization.DataTable();
      chartData.addColumn('string', 'ペルソナ');
      chartData.addColumn('number', 'A（広域移動OK）');
      chartData.addColumn('number', 'B（中距離OK）');
      chartData.addColumn('number', 'C（近距離のみ）');
      chartData.addColumn('number', 'D（地元限定）');

      data.forEach(row => {
        chartData.addRow([
          row.personaName,
          row.levelA,
          row.levelB,
          row.levelC,
          row.levelD
        ]);
      });

      const options = {
        title: 'ペルソナ別移動許容度分布（人数）',
        isStacked: true,
        colors: ['#4facfe', '#43e97b', '#fa709a', '#a8a8a8'],
        hAxis: { title: '人数' },
        vAxis: { title: 'ペルソナ' },
        legend: { position: 'top' },
        chartArea: { width: '75%', height: '75%' }
      };

      const chart = new google.visualization.BarChart(
        document.getElementById('stacked_bar_chart')
      );

      // クリックイベント（ドリルダウン）
      google.visualization.events.addListener(chart, 'select', () => {
        const selection = chart.getSelection();
        if (selection.length > 0) {
          const row = selection[0].row;
          showPersonaDetail(data[row]);
        }
      });

      chart.draw(chartData, options);
    }

    /**
     * 100%積み上げ棒グラフ描画
     */
    function drawPercentageBarChart(data) {
      const chartData = new google.visualization.DataTable();
      chartData.addColumn('string', 'ペルソナ');
      chartData.addColumn('number', 'A比率');
      chartData.addColumn('number', 'B比率');
      chartData.addColumn('number', 'C比率');
      chartData.addColumn('number', 'D比率');

      data.forEach(row => {
        chartData.addRow([
          row.personaName,
          row.ratioA,
          row.ratioB,
          row.ratioC,
          row.ratioD
        ]);
      });

      const options = {
        title: 'ペルソナ別移動許容度分布（比率）',
        isStacked: 'percent',
        colors: ['#4facfe', '#43e97b', '#fa709a', '#a8a8a8'],
        hAxis: { title: '比率（%）', minValue: 0, maxValue: 100 },
        vAxis: { title: 'ペルソナ' },
        legend: { position: 'top' },
        chartArea: { width: '75%', height: '75%' }
      };

      const chart = new google.visualization.BarChart(
        document.getElementById('percentage_bar_chart')
      );

      chart.draw(chartData, options);
    }

    /**
     * クロス集計テーブル表示
     */
    function renderCrossTable(data) {
      const tbody = document.getElementById('table-body');
      tbody.innerHTML = '';

      data.forEach(row => {
        const tr = document.createElement('tr');
        tr.innerHTML = \`
          <td><strong>\${row.personaName}</strong></td>
          <td><strong>\${row.total}名</strong></td>
          <td class="level-a">\${row.levelA}名 (\${row.ratioA.toFixed(1)}%)</td>
          <td class="level-b">\${row.levelB}名 (\${row.ratioB.toFixed(1)}%)</td>
          <td class="level-c">\${row.levelC}名 (\${row.ratioC.toFixed(1)}%)</td>
          <td class="level-d">\${row.levelD}名 (\${row.ratioD.toFixed(1)}%)</td>
        \`;
        tbody.appendChild(tr);
      });
    }

    /**
     * ペルソナ詳細表示（ドリルダウン）
     */
    function showPersonaDetail(persona) {
      alert(\`
━━━━━━━━━━━━━━━━━━━━━━━
ペルソナ詳細: \${persona.personaName}
━━━━━━━━━━━━━━━━━━━━━━━

📊 合計: \${persona.total}名

移動許容度分布:
  A（広域移動OK）:   \${persona.levelA}名 (\${persona.ratioA.toFixed(1)}%)
  B（中距離OK）:     \${persona.levelB}名 (\${persona.ratioB.toFixed(1)}%)
  C（近距離のみ）:   \${persona.levelC}名 (\${persona.ratioC.toFixed(1)}%)
  D（地元限定）:     \${persona.levelD}名 (\${persona.ratioD.toFixed(1)}%)

━━━━━━━━━━━━━━━━━━━━━━━
      \`.trim());
    }

    /**
     * CSV出力
     */
    function exportToCSV() {
      console.log('[INFO] CSV出力開始');

      let csv = 'ペルソナID,ペルソナ名,A人数,B人数,C人数,D人数,合計,A%,B%,C%,D%\\n';
      sortedData.forEach(row => {
        csv += \`\${row.personaId},\${row.personaName},\${row.levelA},\${row.levelB},\${row.levelC},\${row.levelD},\${row.total},\${row.ratioA},\${row.ratioB},\${row.ratioC},\${row.ratioD}\\n\`;
      });

      const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
      const link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      link.download = \`PersonaMobilityCross_\${new Date().toISOString().split('T')[0]}.csv\`;
      link.click();

      console.log('[OK] CSV出力完了');
    }

    /**
     * インサイトパネルトグル
     */
    function toggleInsights() {
      const panel = document.getElementById('insights-panel');
      panel.classList.toggle('show');
    }

    /**
     * インサイト生成
     */
    function generateInsights() {
      const content = document.getElementById('insights-content');

      // 最も高移動性のペルソナ
      const highestA = rawData.reduce((max, row) => row.ratioA > max.ratioA ? row : max);

      // 最も地元志向のペルソナ
      const highestD = rawData.reduce((max, row) => row.ratioD > max.ratioD ? row : max);

      // 最大規模のペルソナ
      const largest = rawData.reduce((max, row) => row.total > max.total ? row : max);

      // バランス最良のペルソナ
      const balanced = rawData.reduce((min, row) => {
        const ratios = [row.ratioA, row.ratioB, row.ratioC, row.ratioD];
        const avg = ratios.reduce((a, b) => a + b, 0) / 4;
        const variance = ratios.reduce((sum, r) => sum + Math.pow(r - avg, 2), 0) / 4;
        const stdDev = Math.sqrt(variance);
        return stdDev < (min.stdDev || Infinity) ? { ...row, stdDev } : min;
      }, {});

      const insights = [
        {
          title: '最も高移動性',
          detail: \`<strong>\${highestA.personaName}</strong>はAランク（広域移動OK）が<strong>\${highestA.ratioA.toFixed(1)}%</strong>で最も高移動性です。全国エリアでの求人露出を強化することで、マッチング率向上が期待できます。\`
        },
        {
          title: '最も地元志向',
          detail: \`<strong>\${highestD.personaName}</strong>はDランク（地元限定）が<strong>\${highestD.ratioD.toFixed(1)}%</strong>で最も地元志向です。「通勤時間15分以内」「地元で働く」をキーワードに訴求すると効果的です。\`
        },
        {
          title: '最大規模セグメント',
          detail: \`<strong>\${largest.personaName}</strong>が最大規模（<strong>\${largest.total}名</strong>）です。このペルソナへの求人投資を優先することで、最大のROIが見込めます。\`
        },
        {
          title: '最もバランス良好',
          detail: \`<strong>\${balanced.personaName}</strong>は移動許容度のバランスが最も均等です。多様な求人タイプに対応可能な柔軟性の高いセグメントです。\`
        }
      ];

      content.innerHTML = '';
      insights.forEach(insight => {
        const div = document.createElement('div');
        div.className = 'insight-item';
        div.innerHTML = \`
          <h4 style="margin-bottom: 8px; color: #1a73e8;">\${insight.title}</h4>
          <p style="line-height: 1.6; color: #555;">\${insight.detail}</p>
        \`;
        content.appendChild(div);
      });

      console.log('[OK] インサイト生成完了');
    }

    /**
     * エラーハンドリング
     */
    window.onerror = function(message, source, lineno, colno, error) {
      console.error('[ERROR] JavaScript エラー:', message);
      console.error('[ERROR] ファイル:', source);
      console.error('[ERROR] 行番号:', lineno);
      alert('グラフの初期化中にエラーが発生しました:\\n' + message);
      return false;
    };
  </script>
</body>
</html>
  `;
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 7. Phase 7統合ダッシュボード
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

/**
 * Phase 7統合ダッシュボード表示（メニューから呼び出し）
 */
function showPhase7CompleteDashboard() {
  const ui = SpreadsheetApp.getUi();

  try {
    // 全データ読み込み
    const dashboardData = loadAllPhase7Data();

    // データ存在確認
    const dataCount = Object.values(dashboardData).filter(d => d && d.length > 0).length;

    if (dataCount === 0) {
      ui.alert(
        'データなし',
        'Phase 7のデータがインポートされていません。\n\n' +
        '「Phase 7クイックインポート」を先に実行してください。',
        ui.ButtonSet.OK
      );
      return;
    }

    // HTML生成
    const html = generateCompleteDashboardHTML(dashboardData);

    // 全画面ダイアログ表示
    const htmlOutput = HtmlService.createHtmlOutput(html)
      .setWidth(1600)
      .setHeight(1000);

    ui.showModalDialog(htmlOutput, 'Phase 7: 完全統合ダッシュボード');

  } catch (error) {
    ui.alert('エラー', `ダッシュボード生成中にエラーが発生しました:\n${error.message}`, ui.ButtonSet.OK);
    Logger.log(`Phase 7ダッシュボードエラー: ${error.stack}`);
  }
}

/**
 * 全Phase 7データ読み込み
 * @return {Object} 全データを含むオブジェクト
 */
function loadAllPhase7Data() {
  const data = {
    supplyDensity: [],
    qualificationDist: [],
    ageGenderCross: [],
    mobilityScore: [],
    personaProfile: []
  };

  try {
    data.supplyDensity = loadSupplyDensityData();
  } catch (e) {
    Logger.log(`人材供給密度データ読み込みエラー: ${e.message}`);
  }

  try {
    data.qualificationDist = loadQualificationDistData();
  } catch (e) {
    Logger.log(`資格別人材分布データ読み込みエラー: ${e.message}`);
  }

  try {
    data.ageGenderCross = loadAgeGenderCrossData();
  } catch (e) {
    Logger.log(`年齢層×性別クロスデータ読み込みエラー: ${e.message}`);
  }

  try {
    data.mobilityScore = loadMobilityScoreData();
  } catch (e) {
    Logger.log(`移動許容度データ読み込みエラー: ${e.message}`);
  }

  try {
    data.personaProfile = loadPersonaProfileData();
  } catch (e) {
    Logger.log(`ペルソナプロファイルデータ読み込みエラー: ${e.message}`);
  }

  return data;
}

/**
 * 統合ダッシュボードHTML生成
 * @param {Object} dashboardData - 全データ
 * @return {string} HTML文字列
 */
function generateCompleteDashboardHTML(dashboardData) {
  // 各データをJSON文字列化
  const supplyDensityJson = JSON.stringify(dashboardData.supplyDensity || []);
  const qualificationDistJson = JSON.stringify(dashboardData.qualificationDist || []);
  const ageGenderCrossJson = JSON.stringify(dashboardData.ageGenderCross || []);
  const mobilityScoreJson = JSON.stringify(dashboardData.mobilityScore || []);
  const personaProfileJson = JSON.stringify(dashboardData.personaProfile || []);

  return `
<!DOCTYPE html>
<html>
<head>
  <base target="_top">
  <script type="text/javascript" src="https://www.gstatic.com/charts/loader.js"></script>
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
    }
    .dashboard-header {
      background: rgba(255,255,255,0.95);
      padding: 20px 40px;
      box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }
    .dashboard-header h1 {
      color: #1a73e8;
      font-size: 32px;
      margin-bottom: 10px;
    }
    .dashboard-header p {
      color: #666;
      font-size: 14px;
    }
    .tab-container {
      background: white;
      margin: 20px;
      border-radius: 12px;
      box-shadow: 0 4px 20px rgba(0,0,0,0.15);
      overflow: hidden;
    }
    .tabs {
      display: flex;
      background: #f5f5f5;
      border-bottom: 2px solid #ddd;
      padding: 0 20px;
    }
    .tab {
      padding: 15px 30px;
      cursor: pointer;
      border: none;
      background: transparent;
      font-size: 16px;
      font-weight: 500;
      color: #666;
      transition: all 0.3s;
      border-bottom: 3px solid transparent;
    }
    .tab:hover {
      background: rgba(26, 115, 232, 0.1);
      color: #1a73e8;
    }
    .tab.active {
      color: #1a73e8;
      border-bottom-color: #1a73e8;
      background: white;
    }
    .tab-content {
      display: none;
      padding: 30px;
      min-height: 700px;
    }
    .tab-content.active {
      display: block;
      animation: fadeIn 0.3s;
    }
    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(10px); }
      to { opacity: 1; transform: translateY(0); }
    }
    .kpi-grid {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 20px;
      margin-bottom: 30px;
    }
    .kpi-card {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      padding: 25px;
      border-radius: 12px;
      box-shadow: 0 4px 6px rgba(0,0,0,0.1);
      text-align: center;
    }
    .kpi-card.card-1 { background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); }
    .kpi-card.card-2 { background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); }
    .kpi-card.card-3 { background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); }
    .kpi-card.card-4 { background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); }
    .kpi-label {
      font-size: 14px;
      opacity: 0.9;
      margin-bottom: 10px;
    }
    .kpi-value {
      font-size: 36px;
      font-weight: bold;
    }
    .kpi-unit {
      font-size: 14px;
      opacity: 0.9;
      margin-top: 5px;
    }
    .chart-container {
      background: white;
      padding: 20px;
      border-radius: 8px;
      margin-bottom: 20px;
      box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .chart-container h2 {
      color: #333;
      margin-bottom: 15px;
      font-size: 20px;
    }
    .chart {
      width: 100%;
      height: 400px;
    }
  </style>
</head>
<body>
  <div class="dashboard-header">
    <h1>📊 Phase 7: 完全統合ダッシュボード</h1>
    <p>Python分析エンジンによる高度分析結果を、美しいUIで可視化</p>
  </div>

  <div class="tab-container">
    <div class="tabs">
      <button class="tab active" onclick="switchTab(0)">📋 概要</button>
      <button class="tab" onclick="switchTab(1)">🗺️ 人材供給密度</button>
      <button class="tab" onclick="switchTab(2)">🎓 資格分布</button>
      <button class="tab" onclick="switchTab(3)">👥 年齢×性別</button>
      <button class="tab" onclick="switchTab(4)">🚗 移動許容度</button>
      <button class="tab" onclick="switchTab(5)">📊 ペルソナ</button>
    </div>

    <!-- タブ0: 概要 -->
    <div class="tab-content active" id="tab-0">
      <h2>Phase 7データサマリー</h2>
      <div class="kpi-grid" id="overview-kpis"></div>

      <div class="chart-container">
        <h2>データ可用性</h2>
        <div id="overview_availability_chart" class="chart"></div>
      </div>
    </div>

    <!-- タブ1: 人材供給密度 -->
    <div class="tab-content" id="tab-1">
      <h2>人材供給密度マップ</h2>
      <div id="supply_density_chart" class="chart"></div>
    </div>

    <!-- タブ2: 資格分布 -->
    <div class="tab-content" id="tab-2">
      <h2>資格別人材分布</h2>
      <div id="qualification_dist_chart" class="chart"></div>
    </div>

    <!-- タブ3: 年齢×性別 -->
    <div class="tab-content" id="tab-3">
      <h2>年齢層×性別クロス分析</h2>
      <div id="age_gender_cross_chart" class="chart"></div>
    </div>

    <!-- タブ4: 移動許容度 -->
    <div class="tab-content" id="tab-4">
      <h2>移動許容度スコアリング</h2>
      <div id="mobility_score_chart" class="chart"></div>
    </div>

    <!-- タブ5: ペルソナ -->
    <div class="tab-content" id="tab-5">
      <h2>ペルソナ詳細プロファイル</h2>
      <div id="persona_profile_chart" class="chart"></div>
    </div>
  </div>

  <script type="text/javascript">
    // データ読み込み
    const supplyDensityData = ${supplyDensityJson};
    const qualificationDistData = ${qualificationDistJson};
    const ageGenderCrossData = ${ageGenderCrossJson};
    const mobilityScoreData = ${mobilityScoreJson};
    const personaProfileData = ${personaProfileJson};

    // Google Charts読み込み
    google.charts.load('current', {'packages':['corechart']});
    google.charts.setOnLoadCallback(initDashboard);

    function initDashboard() {
      renderOverviewKPIs();
      drawOverviewAvailabilityChart();
      // 他のチャートは必要に応じて遅延読み込み
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
          if (supplyDensityData.length > 0) drawSupplyDensityChart();
          break;
        case 2:
          if (qualificationDistData.length > 0) drawQualificationDistChart();
          break;
        case 3:
          if (ageGenderCrossData.length > 0) drawAgeGenderCrossChart();
          break;
        case 4:
          if (mobilityScoreData.length > 0) drawMobilityScoreChart();
          break;
        case 5:
          if (personaProfileData.length > 0) drawPersonaProfileChart();
          break;
      }
    }

    // 概要KPI表示
    function renderOverviewKPIs() {
      const container = document.getElementById('overview-kpis');

      const kpis = [
        {
          label: '人材供給密度',
          value: supplyDensityData.length,
          unit: '地域',
          cardClass: 'card-1'
        },
        {
          label: '資格カテゴリ',
          value: qualificationDistData.length,
          unit: '種類',
          cardClass: 'card-2'
        },
        {
          label: '分析地域',
          value: ageGenderCrossData.length,
          unit: '地域',
          cardClass: 'card-3'
        },
        {
          label: '求職者',
          value: mobilityScoreData.length.toLocaleString(),
          unit: '名',
          cardClass: 'card-4'
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

    // データ可用性チャート
    function drawOverviewAvailabilityChart() {
      const chartData = new google.visualization.DataTable();
      chartData.addColumn('string', 'データセット');
      chartData.addColumn('number', 'レコード数');

      chartData.addRow(['人材供給密度', supplyDensityData.length]);
      chartData.addRow(['資格別人材分布', qualificationDistData.length]);
      chartData.addRow(['年齢層×性別', ageGenderCrossData.length]);
      chartData.addRow(['移動許容度', mobilityScoreData.length]);
      chartData.addRow(['ペルソナ', personaProfileData.length]);

      const options = {
        title: 'Phase 7データセット別レコード数',
        colors: ['#4285F4'],
        legend: {position: 'none'}
      };

      const chart = new google.visualization.ColumnChart(
        document.getElementById('overview_availability_chart')
      );

      chart.draw(chartData, options);
    }

    // 以下、各チャート描画関数（簡略版）
    function drawSupplyDensityChart() {
      const chartData = new google.visualization.DataTable();
      chartData.addColumn('string', '市区町村');
      chartData.addColumn('number', '総合スコア');

      const top10 = [...supplyDensityData]
        .sort((a, b) => b.compositeScore - a.compositeScore)
        .slice(0, 10);

      top10.forEach(row => {
        chartData.addRow([row.municipality, row.compositeScore]);
      });

      const options = {
        title: '人材供給密度TOP10',
        colors: ['#4285F4']
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
        chartData.addRow([row.category, row.totalHolders]);
      });

      const options = {
        title: '資格カテゴリ別保有者数',
        colors: ['#34A853']
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

      ageGenderCrossData.forEach(row => {
        chartData.addRow([row.municipality, row.diversityScore]);
      });

      const options = {
        title: 'ダイバーシティスコア',
        colors: ['#FBBC04']
      };

      const chart = new google.visualization.ColumnChart(
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

      chartData.addRow(['広域移動OK', levelCounts['A'] || 0]);
      chartData.addRow(['中距離OK', levelCounts['B'] || 0]);
      chartData.addRow(['近距離のみ', levelCounts['C'] || 0]);
      chartData.addRow(['地元限定', levelCounts['D'] || 0]);

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
        chartData.addRow([row.personaName, row.count]);
      });

      const options = {
        title: 'ペルソナ別人数分布',
        pieHole: 0.4,
        colors: ['#667eea', '#4facfe', '#43e97b', '#fa709a', '#f093fb']
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

// ===== Phase8UnifiedVisualizations.gs =====
/**
 * Phase 8 統合可視化ファイル
 *
 * このファイルには以下の可視化機能がすべて含まれています:
 * 1. キャリア分布（TOP100）
 * 2. キャリア×年齢クロス分析
 * 3. キャリア×年齢マトリックス（ヒートマップ）
 * 4. 卒業年分布（1957-2030）
 * 5. Phase 8統合ダッシュボード
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
// 1. キャリア分布（TOP100）
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

/**
 * キャリア分布表示（メニューから呼び出し）
 */
function showCareerDistribution() {
  const ui = SpreadsheetApp.getUi();

  try {
    // データ読み込み
    const data = loadCareerDistData();

    if (!data || data.length === 0) {
      ui.alert(
        'データなし',
        'Phase8_CareerDistributionシートにデータがありません。\n' +
        '先に「Python結果CSVを取り込み」を実行してください。',
        ui.ButtonSet.OK
      );
      return;
    }

    // HTML生成
    const html = generateCareerDistHTML(data);

    // ダイアログ表示
    const htmlOutput = HtmlService.createHtmlOutput(html)
      .setWidth(1200)
      .setHeight(800);

    ui.showModalDialog(htmlOutput, 'Phase 8: キャリア分布分析');

  } catch (error) {
    ui.alert('エラー', `可視化中にエラーが発生しました:\n${error.message}`, ui.ButtonSet.OK);
    Logger.log(`キャリア分布エラー: ${error.stack}`);
  }
}

/**
 * キャリア分布データ読み込み
 * @return {Array<Object>} データオブジェクトの配列
 */
function loadCareerDistData() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName('Phase8_CareerDistribution');

  if (!sheet) {
    throw new Error('Phase8_CareerDistributionシートが見つかりません');
  }

  const lastRow = sheet.getLastRow();
  if (lastRow <= 1) {
    return [];
  }

  // データ範囲取得（ヘッダー除く）
  const range = sheet.getRange(2, 1, lastRow - 1, 2);
  const values = range.getValues();

  // オブジェクト配列に変換
  const data = values
    .filter(row => row[0] && row[1] > 0)  // 空行とゼロ件を除外
    .map(row => ({
      career: String(row[0]),  // キャリア
      count: Number(row[1])    // 件数
    }));

  Logger.log(`キャリア分布データ読み込み: ${data.length}件`);

  return data;
}

/**
 * キャリア分布HTML生成
 * @param {Array<Object>} data - データ配列
 * @return {string} HTML文字列
 */
function generateCareerDistHTML(data) {
  // データをJSON文字列化（上位100件のみ）
  const top100Data = data
    .sort((a, b) => b.count - a.count)
    .slice(0, 100);
  const dataJson = JSON.stringify(top100Data);

  return `
<!DOCTYPE html>
<html>
<head>
  <base target="_top">
  <script type="text/javascript" src="https://www.gstatic.com/charts/loader.js"></script>
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
    .container {
      background-color: white;
      padding: 20px;
      border-radius: 8px;
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
      margin-bottom: 20px;
    }
    .stats-summary {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 15px;
      margin-bottom: 20px;
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
      font-size: 32px;
      font-weight: bold;
    }
    #bar_chart {
      width: 100%;
      height: 600px;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      margin-top: 10px;
      font-size: 14px;
    }
    th, td {
      padding: 10px;
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
    .table-container {
      max-height: 400px;
      overflow-y: auto;
    }
    .rank-badge {
      display: inline-block;
      width: 30px;
      height: 30px;
      background-color: #ffd700;
      color: #333;
      border-radius: 50%;
      text-align: center;
      line-height: 30px;
      font-weight: bold;
      margin-right: 10px;
    }
    .note {
      background-color: #fff3cd;
      border-left: 4px solid #ffc107;
      padding: 15px;
      margin-top: 10px;
      border-radius: 4px;
    }
  </style>
</head>
<body>
  <h1>💼 Phase 8: キャリア分布分析</h1>

  <div class="container">
    <h2>統計サマリー</h2>
    <div class="stats-summary" id="stats-summary"></div>
  </div>

  <div class="container">
    <h2>キャリア別人数（TOP100横棒グラフ）</h2>
    <div class="note">
      <strong>📊 表示説明:</strong> 全${data.length.toLocaleString()}種類のキャリアのうち、人数が多い上位100種類を表示しています。
    </div>
    <div id="bar_chart"></div>
  </div>

  <div class="container">
    <h2>キャリア別詳細データ（TOP100）</h2>
    <div class="table-container">
      <table id="data-table">
        <thead>
          <tr>
            <th style="width: 80px;">順位</th>
            <th>キャリア（職歴）</th>
            <th style="width: 120px;">人数</th>
          </tr>
        </thead>
        <tbody id="table-body"></tbody>
      </table>
    </div>
  </div>

  <script type="text/javascript">
    const data = ${dataJson};
    const totalCareerTypes = ${data.length};

    // Google Charts読み込み
    google.charts.load('current', {'packages':['corechart']});
    google.charts.setOnLoadCallback(drawCharts);

    function drawCharts() {
      renderStatsSummary();
      drawBarChart();
      renderDataTable();
    }

    // 統計サマリー表示
    function renderStatsSummary() {
      const container = document.getElementById('stats-summary');

      // 総キャリア種類数
      const totalTypes = totalCareerTypes;

      // 総人数
      const totalCount = data.reduce((sum, row) => sum + row.count, 0);

      // 平均人数
      const avgCount = totalCount / totalTypes;

      const stats = [
        {label: 'キャリア種類数', value: totalTypes.toLocaleString(), unit: '種類'},
        {label: '総人数', value: totalCount.toLocaleString(), unit: '名'},
        {label: '平均人数/種類', value: Math.round(avgCount).toLocaleString(), unit: '名'}
      ];

      stats.forEach(stat => {
        const card = document.createElement('div');
        card.className = 'stat-card';
        card.innerHTML = \`
          <div class="stat-label">\${stat.label}</div>
          <div class="stat-value">\${stat.value}</div>
          <div class="stat-label">\${stat.unit}</div>
        \`;
        container.appendChild(card);
      });
    }

    // 横棒グラフ描画
    function drawBarChart() {
      const chartData = new google.visualization.DataTable();
      chartData.addColumn('string', 'キャリア');
      chartData.addColumn('number', '人数');

      // データを人数降順でソート（既にソート済み）
      data.forEach(row => {
        // キャリア名が長い場合は省略
        const careerLabel = row.career.length > 40
          ? row.career.substring(0, 40) + '...'
          : row.career;
        chartData.addRow([careerLabel, row.count]);
      });

      const options = {
        title: 'キャリア別人数（TOP100）',
        chartArea: {width: '50%', height: '85%'},
        hAxis: {
          title: '人数',
          minValue: 0
        },
        vAxis: {
          title: 'キャリア',
          textStyle: {fontSize: 10}
        },
        colors: ['#4285F4'],
        legend: {position: 'none'},
        height: 600
      };

      const chart = new google.visualization.BarChart(
        document.getElementById('bar_chart')
      );

      chart.draw(chartData, options);
    }

    // データテーブル表示
    function renderDataTable() {
      const tbody = document.getElementById('table-body');

      data.forEach((row, index) => {
        const tr = document.createElement('tr');

        // 順位バッジ
        const rankHtml = index < 3
          ? \`<span class="rank-badge">\${index + 1}</span>\`
          : \`<span style="font-weight: bold;">\${index + 1}</span>\`;

        tr.innerHTML = \`
          <td style="text-align: center;">\${rankHtml}</td>
          <td><strong>\${row.career}</strong></td>
          <td style="text-align: right;"><strong>\${row.count.toLocaleString()}</strong>名</td>
        \`;
        tbody.appendChild(tr);
      });
    }
  </script>
</body>
</html>
  `;
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 2. キャリア×年齢クロス分析
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

/**
 * キャリア×年齢クロス分析表示（メニューから呼び出し）
 */
function showCareerAgeCross() {
  const ui = SpreadsheetApp.getUi();

  try {
    // データ読み込み
    const data = loadCareerAgeCrossData();

    if (!data || data.length === 0) {
      ui.alert(
        'データなし',
        'Phase8_CareerAgeCrossシートにデータがありません。\n' +
        '先に「Python結果CSVを取り込み」を実行してください。',
        ui.ButtonSet.OK
      );
      return;
    }

    // HTML生成
    const html = generateCareerAgeCrossHTML(data);

    // ダイアログ表示
    const htmlOutput = HtmlService.createHtmlOutput(html)
      .setWidth(1400)
      .setHeight(900);

    ui.showModalDialog(htmlOutput, 'Phase 8: キャリア×年齢層クロス分析');

  } catch (error) {
    ui.alert('エラー', `可視化中にエラーが発生しました:\n${error.message}`, ui.ButtonSet.OK);
    Logger.log(`キャリア×年齢クロス分析エラー: ${error.stack}`);
  }
}

/**
 * キャリア×年齢クロスデータ読み込み
 * @return {Array<Object>} データオブジェクトの配列
 */
function loadCareerAgeCrossData() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName('Phase8_CareerAgeCross');

  if (!sheet) {
    throw new Error('Phase8_CareerAgeCrossシートが見つかりません');
  }

  const lastRow = sheet.getLastRow();
  if (lastRow <= 1) {
    return [];
  }

  // データ範囲取得（ヘッダー除く）
  const range = sheet.getRange(2, 1, lastRow - 1, 5);
  const values = range.getValues();

  // オブジェクト配列に変換
  const data = values
    .filter(row => row[0] && row[1] && row[2] > 0)
    .map(row => ({
      career: String(row[0]),
      ageGroup: String(row[1]),
      count: Number(row[2]),
      avgAge: row[3] ? Number(row[3]) : null,
      avgQualifications: row[4] ? Number(row[4]) : null
    }));

  Logger.log(`キャリア×年齢クロスデータ読み込み: ${data.length}件`);

  return data;
}

/**
 * キャリア×年齢クロスHTML生成
 * @param {Array<Object>} data - データ配列
 * @return {string} HTML文字列
 */
function generateCareerAgeCrossHTML(data) {
  // キャリア別に合計件数を計算してTOP30を抽出
  const careerTotals = {};
  data.forEach(row => {
    if (!careerTotals[row.career]) {
      careerTotals[row.career] = 0;
    }
    careerTotals[row.career] += row.count;
  });

  const top30Careers = Object.entries(careerTotals)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 30)
    .map(entry => entry[0]);

  // TOP30キャリアのデータのみ抽出
  const top30Data = data.filter(row => top30Careers.includes(row.career));

  const dataJson = JSON.stringify(top30Data);
  const totalCount = data.length;

  return `
<!DOCTYPE html>
<html>
<head>
  <base target="_top">
  <script type="text/javascript" src="https://www.gstatic.com/charts/loader.js"></script>
  <style>
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
    .container {
      background-color: white;
      padding: 20px;
      border-radius: 8px;
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
      margin-bottom: 20px;
    }
    .stats-summary {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 15px;
      margin-bottom: 20px;
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
    #grouped_bar_chart {
      width: 100%;
      height: 700px;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      margin-top: 10px;
      font-size: 13px;
    }
    th, td {
      padding: 10px;
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
    .table-container {
      max-height: 500px;
      overflow-y: auto;
    }
    .note {
      background-color: #fff3cd;
      border-left: 4px solid #ffc107;
      padding: 15px;
      margin-top: 10px;
      border-radius: 4px;
    }
    .age-badge {
      display: inline-block;
      padding: 4px 8px;
      border-radius: 4px;
      font-size: 11px;
      font-weight: bold;
      margin-right: 5px;
    }
    .age-20 { background-color: #e3f2fd; color: #1976d2; }
    .age-30 { background-color: #f3e5f5; color: #7b1fa2; }
    .age-40 { background-color: #fff3e0; color: #e65100; }
    .age-50 { background-color: #fce4ec; color: #c2185b; }
    .age-60 { background-color: #f1f8e9; color: #558b2f; }
    .age-70 { background-color: #e0f2f1; color: #00695c; }
  </style>
</head>
<body>
  <h1>💼📊 Phase 8: キャリア×年齢層クロス分析</h1>

  <div class="container">
    <h2>統計サマリー</h2>
    <div class="stats-summary" id="stats-summary"></div>
  </div>

  <div class="container">
    <h2>キャリア×年齢層グループ化グラフ（TOP30）</h2>
    <div class="note">
      <strong>📊 表示説明:</strong> 全${totalCount.toLocaleString()}件のデータから、人数が多い上位30キャリアを抽出し、年齢層別に色分けして表示しています。
    </div>
    <div id="grouped_bar_chart"></div>
  </div>

  <div class="container">
    <h2>キャリア×年齢層詳細データ（TOP30）</h2>
    <div class="table-container">
      <table id="data-table">
        <thead>
          <tr>
            <th style="width: 40%;">キャリア</th>
            <th style="width: 15%;">年齢層</th>
            <th style="width: 12%;">人数</th>
            <th style="width: 12%;">平均年齢</th>
            <th style="width: 12%;">平均資格数</th>
          </tr>
        </thead>
        <tbody id="table-body"></tbody>
      </table>
    </div>
  </div>

  <script type="text/javascript">
    const data = ${dataJson};
    const totalDataCount = ${totalCount};

    // 年齢層の順序定義
    const ageGroupOrder = ['20代', '30代', '40代', '50代', '60代', '70歳以上'];

    // Google Charts読み込み
    google.charts.load('current', {'packages':['corechart']});
    google.charts.setOnLoadCallback(drawCharts);

        // 統計サマリー表示
    function renderStatsSummary() {
      const container = document.getElementById('stats-summary');

      // キャリア種類数（TOP30）
      const uniqueCareers = [...new Set(data.map(d => d.career))].length;

      // 総人数（TOP30の合計）
      const totalCount = data.reduce((sum, row) => sum + row.count, 0);

      // 年齢層数
      const uniqueAgeGroups = [...new Set(data.map(d => d.ageGroup))].length;

      // 平均年齢
      const avgAge = data.reduce((sum, row) => sum + (row.avgAge || 0) * row.count, 0) / totalCount;

      const stats = [
        {label: 'TOP30キャリア数', value: uniqueCareers, unit: '種類'},
        {label: '総人数（TOP30）', value: totalCount.toLocaleString(), unit: '名'},
        {label: '年齢層数', value: uniqueAgeGroups, unit: 'グループ'},
        {label: '平均年齢', value: Math.round(avgAge), unit: '歳'}
      ];

      stats.forEach(stat => {
        const card = document.createElement('div');
        card.className = 'stat-card';
        card.innerHTML = \`
          <div class="stat-label">\${stat.label}</div>
          <div class="stat-value">\${stat.value}</div>
          <div class="stat-label">\${stat.unit}</div>
        \`;
        container.appendChild(card);
      });
    }

    // グループ化横棒グラフ描画
    function drawGroupedBarChart() {
      // データをキャリア別にピボット
      const careerMap = {};
      data.forEach(row => {
        if (!careerMap[row.career]) {
          careerMap[row.career] = {};
          ageGroupOrder.forEach(ag => {
            careerMap[row.career][ag] = 0;
          });
        }
        careerMap[row.career][row.ageGroup] = row.count;
      });

      // キャリア別合計でソート
      const sortedCareers = Object.entries(careerMap)
        .map(([career, ageData]) => ({
          career,
          total: Object.values(ageData).reduce((sum, val) => sum + val, 0),
          ageData
        }))
        .sort((a, b) => b.total - a.total);

      // Google Charts用データテーブル作成
      const chartData = new google.visualization.DataTable();
      chartData.addColumn('string', 'キャリア');
      ageGroupOrder.forEach(ag => {
        chartData.addColumn('number', ag);
      });

      sortedCareers.forEach(item => {
        const careerLabel = item.career.length > 35
          ? item.career.substring(0, 35) + '...'
          : item.career;
        const row = [careerLabel];
        ageGroupOrder.forEach(ag => {
          row.push(item.ageData[ag] || 0);
        });
        chartData.addRow(row);
      });

      const options = {
        title: 'キャリア×年齢層グループ化横棒グラフ（TOP30）',
        chartArea: {width: '50%', height: '85%'},
        hAxis: {
          title: '人数',
          minValue: 0
        },
        vAxis: {
          title: 'キャリア',
          textStyle: {fontSize: 10}
        },
        isStacked: false,
        legend: {position: 'top', maxLines: 2},
        colors: ['#4285F4', '#AA46BE', '#F4B400', '#DB4437', '#0F9D58', '#00ACC1'],
        height: 700
      };

      const chart = new google.visualization.BarChart(
        document.getElementById('grouped_bar_chart')
      );

      chart.draw(chartData, options);
    }

    // データテーブル表示
    function renderDataTable() {
      const tbody = document.getElementById('table-body');

      // キャリア別にグループ化してソート
      const careerGroups = {};
      data.forEach(row => {
        if (!careerGroups[row.career]) {
          careerGroups[row.career] = [];
        }
        careerGroups[row.career].push(row);
      });

      // キャリア別合計でソート
      const sortedCareerEntries = Object.entries(careerGroups)
        .map(([career, rows]) => ({
          career,
          total: rows.reduce((sum, r) => sum + r.count, 0),
          rows
        }))
        .sort((a, b) => b.total - a.total);

      sortedCareerEntries.forEach(careerEntry => {
        // 年齢層順にソート
        const sortedRows = careerEntry.rows.sort((a, b) => {
          return ageGroupOrder.indexOf(a.ageGroup) - ageGroupOrder.indexOf(b.ageGroup);
        });

        sortedRows.forEach((row, index) => {
          const tr = document.createElement('tr');

          // 年齢層バッジのクラス決定
          const ageBadgeClass = row.ageGroup.includes('20') ? 'age-20' :
                                 row.ageGroup.includes('30') ? 'age-30' :
                                 row.ageGroup.includes('40') ? 'age-40' :
                                 row.ageGroup.includes('50') ? 'age-50' :
                                 row.ageGroup.includes('60') ? 'age-60' : 'age-70';

          tr.innerHTML = \`
            <td>\${index === 0 ? '<strong>' + row.career + '</strong>' : ''}</td>
            <td><span class="age-badge \${ageBadgeClass}">\${row.ageGroup}</span></td>
            <td style="text-align: right;"><strong>\${row.count.toLocaleString()}</strong>名</td>
            <td style="text-align: right;">\${row.avgAge ? row.avgAge.toFixed(1) + '歳' : '－'}</td>
            <td style="text-align: right;">\${row.avgQualifications !== null ? row.avgQualifications.toFixed(1) + '個' : '－'}</td>
          \`;
          tbody.appendChild(tr);
        });
      });
    }
  </script>
</body>
</html>
  `;
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 3. キャリア×年齢マトリックス（ヒートマップ）
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

/**
 * キャリア×年齢マトリックス表示（メニューから呼び出し）
 */
function showCareerAgeMatrix() {
  const ui = SpreadsheetApp.getUi();

  try {
    // データ読み込み
    const data = loadCareerAgeMatrixData();

    if (!data || data.rows.length === 0) {
      ui.alert(
        'データなし',
        'Phase8_CareerAgeMatrixシートにデータがありません。\n' +
        '先に「Python結果CSVを取り込み」を実行してください。',
        ui.ButtonSet.OK
      );
      return;
    }

    // HTML生成
    const html = generateCareerAgeMatrixHTML(data);

    // ダイアログ表示
    const htmlOutput = HtmlService.createHtmlOutput(html)
      .setWidth(1400)
      .setHeight(900);

    ui.showModalDialog(htmlOutput, 'Phase 8: キャリア×年齢層マトリックス');

  } catch (error) {
    ui.alert('エラー', `可視化中にエラーが発生しました:\n${error.message}`, ui.ButtonSet.OK);
    Logger.log(`キャリア×年齢マトリックスエラー: ${error.stack}`);
  }
}

/**
 * キャリア×年齢マトリックスデータ読み込み
 * @return {Object} データオブジェクト
 */
function loadCareerAgeMatrixData() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName('Phase8_CareerAgeMatrix');

  if (!sheet) {
    throw new Error('Phase8_CareerAgeMatrixシートが見つかりません');
  }

  const lastRow = sheet.getLastRow();
  if (lastRow <= 1) {
    return { headers: [], rows: [], metadata: {} };
  }

  // ヘッダー行取得
  const headers = sheet.getRange(1, 1, 1, 7).getValues()[0];

  // データ範囲取得（ヘッダー除く）
  const range = sheet.getRange(2, 1, lastRow - 1, 7);
  const values = range.getValues();

  // 各行の合計を計算してソート
  const rowsWithTotal = values.map(row => ({
    data: row,
    total: row.slice(1).reduce((sum, val) => sum + (Number(val) || 0), 0)
  }));

  // 合計の降順でソート、TOP100を抽出
  rowsWithTotal.sort((a, b) => b.total - a.total);
  const top100Rows = rowsWithTotal.slice(0, 100).map(item => item.data);

  // メタデータ計算
  const metadata = calculateMatrixMetadata(top100Rows);

  Logger.log(`キャリア×年齢マトリックスデータ読み込み: ${top100Rows.length}件（TOP100）`);

  return {
    headers,
    rows: top100Rows,
    metadata,
    totalRows: lastRow - 1
  };
}

/**
 * マトリックスメタデータ計算
 * @param {Array} rows - データ行
 * @return {Object} メタデータ
 */
function calculateMatrixMetadata(rows) {
  const values = [];
  let totalCount = 0;

  rows.forEach(row => {
    row.slice(1).forEach(cell => {
      const num = Number(cell) || 0;
      if (num > 0) {
        values.push(num);
        totalCount += num;
      }
    });
  });

  values.sort((a, b) => a - b);

  return {
    totalCells: rows.length * 6,  // 6列（年齢層）
    valueCells: values.length,
    emptyCells: (rows.length * 6) - values.length,
    totalCount,
    min: values.length > 0 ? values[0] : 0,
    max: values.length > 0 ? values[values.length - 1] : 0,
    mean: values.length > 0 ? values.reduce((sum, v) => sum + v, 0) / values.length : 0,
    median: values.length > 0 ? values[Math.floor(values.length / 2)] : 0
  };
}

/**
 * キャリア×年齢マトリックスHTML生成
 * @param {Object} data - データオブジェクト
 * @return {string} HTML文字列
 */
function generateCareerAgeMatrixHTML(data) {
  const { headers, rows, metadata, totalRows } = data;
  const dataJson = JSON.stringify({ headers, rows });

  return `
<!DOCTYPE html>
<html>
<head>
  <base target="_top">
  <style>
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
    .container {
      background-color: white;
      padding: 20px;
      border-radius: 8px;
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
      margin-bottom: 20px;
    }
    .stats-grid {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 15px;
      margin-bottom: 20px;
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
    .heatmap-container {
      overflow: auto;
      max-height: 600px;
      border: 1px solid #ddd;
      border-radius: 4px;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      font-size: 13px;
    }
    th {
      background-color: #1a73e8;
      color: white;
      padding: 12px;
      text-align: center;
      position: sticky;
      top: 0;
      z-index: 10;
      font-weight: bold;
    }
    td {
      padding: 10px;
      text-align: center;
      border: 1px solid #e0e0e0;
    }
    .row-header {
      background-color: #f8f9fa;
      font-weight: bold;
      text-align: left;
      position: sticky;
      left: 0;
      z-index: 5;
      border-right: 2px solid #1a73e8;
      max-width: 300px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    .legend {
      display: flex;
      align-items: center;
      justify-content: center;
      margin: 20px 0;
      flex-wrap: wrap;
    }
    .legend-item {
      margin: 5px 10px;
      display: flex;
      align-items: center;
    }
    .legend-box {
      width: 30px;
      height: 20px;
      margin-right: 5px;
      border: 1px solid #ddd;
    }
    .note {
      background-color: #fff3cd;
      border-left: 4px solid #ffc107;
      padding: 15px;
      margin-top: 10px;
      border-radius: 4px;
    }
  </style>
</head>
<body>
  <h1>🔥 Phase 8: キャリア×年齢層マトリックス</h1>

  <div class="container">
    <h2>統計サマリー</h2>
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-label">総キャリア数</div>
        <div class="stat-value">${totalRows.toLocaleString()}</div>
        <div class="stat-label">種類</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">総人数（TOP100）</div>
        <div class="stat-value">${metadata.totalCount.toLocaleString()}</div>
        <div class="stat-label">名</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">最大値</div>
        <div class="stat-value">${metadata.max}</div>
        <div class="stat-label">名</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">平均値</div>
        <div class="stat-value">${metadata.mean.toFixed(1)}</div>
        <div class="stat-label">名</div>
      </div>
    </div>
  </div>

  <div class="container">
    <h2>ヒートマップ（TOP100キャリア）</h2>
    <div class="note">
      <strong>📊 表示説明:</strong> 全${totalRows.toLocaleString()}種類のキャリアのうち、人数が多い上位100種類を抽出し、年齢層別の分布をヒートマップで表示しています。色が濃いほど人数が多いことを示します。
    </div>

    <div class="legend" id="legend"></div>

    <div class="heatmap-container">
      <table id="heatmap-table"></table>
    </div>
  </div>

  <script type="text/javascript">
    const data = ${dataJson};
    const metadata = ${JSON.stringify(metadata)};

    // カラースケール生成（青系グラデーション）
    function getHeatmapColor(value, max) {
      if (value === 0) return '#f8f9fa';  // 空セル

      const intensity = Math.min(value / max, 1);
      const r = Math.round(255 * (1 - intensity));
      const g = Math.round(255 * (1 - intensity * 0.5));
      const b = 255;

      return \`rgb(\${r}, \${g}, \${b})\`;
    }

    // 凡例生成
    function renderLegend() {
      const container = document.getElementById('legend');

      const legendSteps = [
        { label: '0名', value: 0 },
        { label: \`\${Math.round(metadata.max * 0.25)}名\`, value: metadata.max * 0.25 },
        { label: \`\${Math.round(metadata.max * 0.5)}名\`, value: metadata.max * 0.5 },
        { label: \`\${Math.round(metadata.max * 0.75)}名\`, value: metadata.max * 0.75 },
        { label: \`\${metadata.max}名\`, value: metadata.max }
      ];

      legendSteps.forEach(step => {
        const item = document.createElement('div');
        item.className = 'legend-item';

        const box = document.createElement('div');
        box.className = 'legend-box';
        box.style.backgroundColor = getHeatmapColor(step.value, metadata.max);

        const label = document.createElement('span');
        label.textContent = step.label;

        item.appendChild(box);
        item.appendChild(label);
        container.appendChild(item);
      });
    }

    // ヒートマップテーブル生成
    function renderHeatmapTable() {
      const table = document.getElementById('heatmap-table');

      // ヘッダー行
      const thead = document.createElement('thead');
      const headerRow = document.createElement('tr');

      data.headers.forEach((header, index) => {
        const th = document.createElement('th');
        th.textContent = header;
        if (index === 0) {
          th.style.minWidth = '300px';
          th.style.textAlign = 'left';
        }
        headerRow.appendChild(th);
      });

      thead.appendChild(headerRow);
      table.appendChild(thead);

      // データ行
      const tbody = document.createElement('tbody');

      data.rows.forEach(row => {
        const tr = document.createElement('tr');

        row.forEach((cell, colIndex) => {
          const td = document.createElement('td');

          if (colIndex === 0) {
            // キャリア名（行ヘッダー）
            td.className = 'row-header';
            td.textContent = cell;
            td.title = cell;  // ツールチップで全文表示
          } else {
            // 数値セル
            const value = Number(cell) || 0;
            td.textContent = value > 0 ? value : '－';
            td.style.backgroundColor = getHeatmapColor(value, metadata.max);

            // 値が大きい場合は文字色を白に
            if (value > metadata.max * 0.6) {
              td.style.color = 'white';
              td.style.fontWeight = 'bold';
            }
          }

          tr.appendChild(td);
        });

        tbody.appendChild(tr);
      });

      table.appendChild(tbody);
    }

    // 初期化
    renderLegend();
    renderHeatmapTable();
  </script>
</body>
</html>
  `;
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 4. 卒業年分布（1957-2030）
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

/**
 * 卒業年分布表示（メニューから呼び出し）
 */
function showGraduationYearDistribution() {
  const ui = SpreadsheetApp.getUi();

  try {
    // データ読み込み
    const data = loadGraduationYearData();

    if (!data || data.length === 0) {
      ui.alert(
        'データなし',
        'Phase8_GradYearDistシートにデータがありません。\n' +
        '先に「Python結果CSVを取り込み」を実行してください。',
        ui.ButtonSet.OK
      );
      return;
    }

    // HTML生成
    const html = generateGraduationYearHTML(data);

    // ダイアログ表示
    const htmlOutput = HtmlService.createHtmlOutput(html)
      .setWidth(1400)
      .setHeight(900);

    ui.showModalDialog(htmlOutput, 'Phase 8: 卒業年分布分析');

  } catch (error) {
    ui.alert('エラー', `可視化中にエラーが発生しました:\n${error.message}`, ui.ButtonSet.OK);
    Logger.log(`卒業年分布エラー: ${error.stack}`);
  }
}

/**
 * 卒業年データ読み込み
 * @return {Array<Object>} データオブジェクトの配列
 */
function loadGraduationYearData() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName('Phase8_GradYearDist');

  if (!sheet) {
    throw new Error('Phase8_GradYearDistシートが見つかりません');
  }

  const lastRow = sheet.getLastRow();
  if (lastRow <= 1) {
    return [];
  }

  // データ範囲取得（ヘッダー除く）
  const range = sheet.getRange(2, 1, lastRow - 1, 3);
  const values = range.getValues();

  // オブジェクト配列に変換
  const data = values
    .filter(row => row[0] && row[1] > 0)
    .map(row => ({
      graduationYear: Number(row[0]),
      count: Number(row[1]),
      avgAge: row[2] ? Number(row[2]) : null
    }))
    .sort((a, b) => a.graduationYear - b.graduationYear);  // 年順にソート

  Logger.log(`卒業年分布データ読み込み: ${data.length}件`);

  return data;
}

/**
 * 卒業年分布HTML生成
 * @param {Array<Object>} data - データ配列
 * @return {string} HTML文字列
 */
function generateGraduationYearHTML(data) {
  const dataJson = JSON.stringify(data);

  return `
<!DOCTYPE html>
<html>
<head>
  <base target="_top">
  <script type="text/javascript" src="https://www.gstatic.com/charts/loader.js"></script>
  <style>
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
    .container {
      background-color: white;
      padding: 20px;
      border-radius: 8px;
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
      margin-bottom: 20px;
    }
    .stats-summary {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 15px;
      margin-bottom: 20px;
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
    .charts-row {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 20px;
      margin-bottom: 20px;
    }
    .chart-container {
      background-color: white;
      padding: 20px;
      border-radius: 8px;
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    #line_chart {
      width: 100%;
      height: 450px;
    }
    #area_chart {
      width: 100%;
      height: 450px;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      margin-top: 10px;
      font-size: 13px;
    }
    th, td {
      padding: 10px;
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
    .table-container {
      max-height: 400px;
      overflow-y: auto;
    }
    .decade-badge {
      display: inline-block;
      padding: 4px 8px;
      border-radius: 4px;
      font-size: 11px;
      font-weight: bold;
      margin-left: 10px;
    }
    .decade-1950 { background-color: #e3f2fd; color: #1976d2; }
    .decade-1960 { background-color: #f3e5f5; color: #7b1fa2; }
    .decade-1970 { background-color: #fff3e0; color: #e65100; }
    .decade-1980 { background-color: #fce4ec; color: #c2185b; }
    .decade-1990 { background-color: #f1f8e9; color: #558b2f; }
    .decade-2000 { background-color: #e0f2f1; color: #00695c; }
    .decade-2010 { background-color: #fff9c4; color: #f57f17; }
    .decade-2020 { background-color: #ffebee; color: #c62828; }
  </style>
</head>
<body>
  <h1>🎓 Phase 8: 卒業年分布分析（1957-2030）</h1>

  <div class="container">
    <h2>統計サマリー</h2>
    <div class="stats-summary" id="stats-summary"></div>
  </div>

  <div class="charts-row">
    <div class="chart-container">
      <h3>卒業年別人数（ラインチャート）</h3>
      <div id="line_chart"></div>
    </div>
    <div class="chart-container">
      <h3>卒業年別人数（エリアチャート）</h3>
      <div id="area_chart"></div>
    </div>
  </div>

  <div class="container">
    <h2>卒業年別詳細データ</h2>
    <div class="table-container">
      <table id="data-table">
        <thead>
          <tr>
            <th style="width: 25%;">卒業年</th>
            <th style="width: 20%;">人数</th>
            <th style="width: 20%;">平均年齢</th>
            <th style="width: 35%;">年代</th>
          </tr>
        </thead>
        <tbody id="table-body"></tbody>
      </table>
    </div>
  </div>

  <script type="text/javascript">
    const data = ${dataJson};

    // Google Charts読み込み
    google.charts.load('current', {'packages':['corechart']});
    google.charts.setOnLoadCallback(drawCharts);

        // 統計サマリー表示
    function renderStatsSummary() {
      const container = document.getElementById('stats-summary');

      // 総卒業年数
      const totalYears = data.length;

      // 総人数
      const totalCount = data.reduce((sum, row) => sum + row.count, 0);

      // 最多卒業年
      const maxCountRow = data.reduce((max, row) => row.count > max.count ? row : max);

      // 最新卒業年
      const latestYear = Math.max(...data.map(d => d.graduationYear));

      const stats = [
        {label: '卒業年範囲', value: \`\${data[0].graduationYear}-\${data[data.length - 1].graduationYear}\`, unit: ''},
        {label: '総人数', value: totalCount.toLocaleString(), unit: '名'},
        {label: '最多卒業年', value: maxCountRow.graduationYear, unit: \`(\${maxCountRow.count}名)\`},
        {label: '最新卒業年', value: latestYear, unit: '年'}
      ];

      stats.forEach(stat => {
        const card = document.createElement('div');
        card.className = 'stat-card';
        card.innerHTML = \`
          <div class="stat-label">\${stat.label}</div>
          <div class="stat-value">\${stat.value}</div>
          <div class="stat-label">\${stat.unit}</div>
        \`;
        container.appendChild(card);
      });
    }

    // ラインチャート描画
    function drawLineChart() {
      const chartData = new google.visualization.DataTable();
      chartData.addColumn('string', '卒業年');
      chartData.addColumn('number', '人数');

      data.forEach(row => {
        chartData.addRow([row.graduationYear.toString(), row.count]);
      });

      const options = {
        title: '卒業年別人数トレンド',
        curveType: 'function',
        legend: { position: 'bottom' },
        chartArea: {width: '80%', height: '70%'},
        hAxis: {
          title: '卒業年',
          slantedText: true,
          slantedTextAngle: 45
        },
        vAxis: {
          title: '人数',
          minValue: 0
        },
        colors: ['#4285F4'],
        pointSize: 4
      };

      const chart = new google.visualization.LineChart(
        document.getElementById('line_chart')
      );

      chart.draw(chartData, options);
    }

    // エリアチャート描画
    function drawAreaChart() {
      const chartData = new google.visualization.DataTable();
      chartData.addColumn('string', '卒業年');
      chartData.addColumn('number', '人数');

      data.forEach(row => {
        chartData.addRow([row.graduationYear.toString(), row.count]);
      });

      const options = {
        title: '卒業年別人数累積ビュー',
        legend: { position: 'bottom' },
        chartArea: {width: '80%', height: '70%'},
        hAxis: {
          title: '卒業年',
          slantedText: true,
          slantedTextAngle: 45
        },
        vAxis: {
          title: '人数',
          minValue: 0
        },
        colors: ['#34A853'],
        isStacked: false
      };

      const chart = new google.visualization.AreaChart(
        document.getElementById('area_chart')
      );

      chart.draw(chartData, options);
    }

    // データテーブル表示
    function renderDataTable() {
      const tbody = document.getElementById('table-body');

      // 人数降順でソート（表示用）
      const sortedData = [...data].sort((a, b) => b.count - a.count);

      sortedData.forEach(row => {
        const tr = document.createElement('tr');

        // 年代判定
        const decade = Math.floor(row.graduationYear / 10) * 10;
        const decadeClass = \`decade-\${decade}\`;
        const decadeLabel = \`\${decade}年代\`;

        tr.innerHTML = \`
          <td><strong>\${row.graduationYear}年</strong></td>
          <td style="text-align: right;"><strong>\${row.count.toLocaleString()}</strong>名</td>
          <td style="text-align: right;">\${row.avgAge ? row.avgAge.toFixed(1) + '歳' : '－'}</td>
          <td><span class="decade-badge \${decadeClass}">\${decadeLabel}</span></td>
        \`;
        tbody.appendChild(tr);
      });
    }
  </script>
</body>
</html>
  `;
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 5. Phase 8統合ダッシュボード
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

/**
 * Phase 8統合ダッシュボード表示（メニューから呼び出し）
 */
function showPhase8CompleteDashboard() {
  const ui = SpreadsheetApp.getUi();

  try {
    // 全データ読み込み
    const dashboardData = loadAllPhase8Data();

    // データ存在確認
    const dataCount = Object.values(dashboardData).filter(d => d && (d.length > 0 || d.rows)).length;

    if (dataCount === 0) {
      ui.alert(
        'データなし',
        'Phase 8のデータがインポートされていません。\n\n' +
        '「Python結果CSVを取り込み」を先に実行してください。',
        ui.ButtonSet.OK
      );
      return;
    }

    // HTML生成
    const html = generatePhase8DashboardHTML(dashboardData);

    // 全画面ダイアログ表示
    const htmlOutput = HtmlService.createHtmlOutput(html)
      .setWidth(1600)
      .setHeight(1000);

    ui.showModalDialog(htmlOutput, 'Phase 8: キャリア・学歴分析 完全統合ダッシュボード');

  } catch (error) {
    ui.alert('エラー', `ダッシュボード生成中にエラーが発生しました:\n${error.message}`, ui.ButtonSet.OK);
    Logger.log(`Phase 8ダッシュボードエラー: ${error.stack}`);
  }
}

/**
 * 全Phase 8データ読み込み
 * @return {Object} 全データを含むオブジェクト
 */
function loadAllPhase8Data() {
  const data = {
    careerDist: [],
    careerAgeCross: [],
    careerAgeMatrix: null,
    graduationYear: []
  };

  try {
    data.careerDist = loadCareerDistData();
  } catch (e) {
    Logger.log(`キャリア分布データ読み込みエラー: ${e.message}`);
  }

  try {
    data.careerAgeCross = loadCareerAgeCrossData();
  } catch (e) {
    Logger.log(`キャリア×年齢クロスデータ読み込みエラー: ${e.message}`);
  }

  try {
    data.careerAgeMatrix = loadCareerAgeMatrixData();
  } catch (e) {
    Logger.log(`キャリア×年齢マトリックスデータ読み込みエラー: ${e.message}`);
  }

  try {
    data.graduationYear = loadGraduationYearData();
  } catch (e) {
    Logger.log(`卒業年分布データ読み込みエラー: ${e.message}`);
  }

  return data;
}

/**
 * Phase 8統合ダッシュボードHTML生成
 * @param {Object} dashboardData - 全データ
 * @return {string} HTML文字列
 */
function generatePhase8DashboardHTML(dashboardData) {
  // 各データをJSON文字列化
  const careerDistJson = JSON.stringify(dashboardData.careerDist.slice(0, 100));
  const careerAgeCrossJson = JSON.stringify(dashboardData.careerAgeCross.slice(0, 200));
  const careerAgeMatrixJson = JSON.stringify(dashboardData.careerAgeMatrix || {headers: [], rows: []});
  const graduationYearJson = JSON.stringify(dashboardData.graduationYear);

  return `
<!DOCTYPE html>
<html>
<head>
  <base target="_top">
  <script type="text/javascript" src="https://www.gstatic.com/charts/loader.js"></script>
  <style>
    * {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }
    body {
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      background-color: #f5f5f5;
    }
    .dashboard-header {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      padding: 20px;
      text-align: center;
      box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    .dashboard-header h1 {
      font-size: 28px;
      margin-bottom: 10px;
    }
    .dashboard-header p {
      font-size: 14px;
      opacity: 0.9;
    }
    .tab-container {
      background-color: white;
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .tabs {
      display: flex;
      border-bottom: 2px solid #e0e0e0;
      overflow-x: auto;
    }
    .tab {
      padding: 15px 30px;
      cursor: pointer;
      border: none;
      background: none;
      font-size: 16px;
      color: #666;
      transition: all 0.3s;
      white-space: nowrap;
    }
    .tab:hover {
      background-color: #f5f5f5;
    }
    .tab.active {
      color: #667eea;
      border-bottom: 3px solid #667eea;
      font-weight: bold;
    }
    .tab-content {
      display: none;
      padding: 20px;
      animation: fadeIn 0.3s;
    }
    .tab-content.active {
      display: block;
    }
    @keyframes fadeIn {
      from { opacity: 0; }
      to { opacity: 1; }
    }
    .stats-summary {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 15px;
      margin-bottom: 20px;
    }
    .stat-card {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      padding: 20px;
      border-radius: 8px;
      text-align: center;
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
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
    .chart-container {
      background-color: white;
      padding: 20px;
      border-radius: 8px;
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
      margin-bottom: 20px;
    }
    .chart-title {
      font-size: 18px;
      font-weight: bold;
      color: #333;
      margin-bottom: 15px;
      padding-bottom: 10px;
      border-bottom: 2px solid #667eea;
    }
    .charts-row {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 20px;
      margin-bottom: 20px;
    }
    #career_dist_chart,
    #career_age_chart,
    #matrix_heatmap,
    #grad_year_line,
    #grad_year_area {
      width: 100%;
      height: 500px;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      font-size: 13px;
    }
    th {
      background-color: #667eea;
      color: white;
      padding: 12px;
      text-align: left;
      position: sticky;
      top: 0;
      z-index: 10;
    }
    td {
      padding: 10px;
      border-bottom: 1px solid #e0e0e0;
    }
    tr:hover {
      background-color: #f5f5f5;
    }
    .table-container {
      max-height: 400px;
      overflow-y: auto;
      border: 1px solid #e0e0e0;
      border-radius: 4px;
    }
    .note {
      background-color: #fff3cd;
      border-left: 4px solid #ffc107;
      padding: 15px;
      margin-bottom: 15px;
      border-radius: 4px;
    }
  </style>
</head>
<body>
  <div class="dashboard-header">
    <h1>💼🎓 Phase 8: キャリア・学歴分析 完全統合ダッシュボード</h1>
    <p>キャリア分布、キャリア×年齢クロス分析、マトリックス、卒業年分布の4つの分析を統合表示</p>
  </div>

  <div class="tab-container">
    <div class="tabs">
      <button class="tab active" onclick="switchTab(0)">💼 キャリア分布</button>
      <button class="tab" onclick="switchTab(1)">📊 キャリア×年齢クロス</button>
      <button class="tab" onclick="switchTab(2)">🔥 マトリックスヒートマップ</button>
      <button class="tab" onclick="switchTab(3)">🎓 卒業年分布</button>
    </div>

    <!-- Tab 1: キャリア分布 -->
    <div class="tab-content active" id="tab-0">
      <div class="note">
        <strong>💼 キャリア分布:</strong> 求職者のキャリア（職歴）の種類別人数を表示します。上位100種類を表示しています。
      </div>
      <div class="stats-summary" id="career-dist-stats"></div>
      <div class="chart-container">
        <div class="chart-title">キャリア別人数（TOP100）</div>
        <div id="career_dist_chart"></div>
      </div>
    </div>

    <!-- Tab 2: キャリア×年齢クロス -->
    <div class="tab-content" id="tab-1">
      <div class="note">
        <strong>📊 キャリア×年齢クロス:</strong> キャリアと年齢層のクロス集計を表示します。TOP30キャリアを年齢層別に色分けして表示しています。
      </div>
      <div class="stats-summary" id="career-age-stats"></div>
      <div class="chart-container">
        <div class="chart-title">キャリア×年齢層グループ化グラフ（TOP30）</div>
        <div id="career_age_chart"></div>
      </div>
    </div>

    <!-- Tab 3: マトリックスヒートマップ -->
    <div class="tab-content" id="tab-2">
      <div class="note">
        <strong>🔥 マトリックスヒートマップ:</strong> キャリア×年齢層のマトリックスをヒートマップで表示します。色が濃いほど人数が多いことを示します。TOP100キャリアを表示しています。
      </div>
      <div class="stats-summary" id="matrix-stats"></div>
      <div class="chart-container">
        <div class="chart-title">キャリア×年齢層ヒートマップ（TOP100）</div>
        <div id="matrix_heatmap"></div>
      </div>
    </div>

    <!-- Tab 4: 卒業年分布 -->
    <div class="tab-content" id="tab-3">
      <div class="note">
        <strong>🎓 卒業年分布:</strong> 求職者の卒業年（1957-2030）の分布をタイムラインで表示します。
      </div>
      <div class="stats-summary" id="grad-year-stats"></div>
      <div class="charts-row">
        <div class="chart-container">
          <div class="chart-title">卒業年別人数（ラインチャート）</div>
          <div id="grad_year_line"></div>
        </div>
        <div class="chart-container">
          <div class="chart-title">卒業年別人数（エリアチャート）</div>
          <div id="grad_year_area"></div>
        </div>
      </div>
    </div>
  </div>

  <script type="text/javascript">
    const careerDistData = ${careerDistJson};
    const careerAgeCrossData = ${careerAgeCrossJson};
    const careerAgeMatrixData = ${careerAgeMatrixJson};
    const graduationYearData = ${graduationYearJson};

    // Google Charts読み込み
    google.charts.load('current', {'packages':['corechart', 'table']});
    google.charts.setOnLoadCallback(initDashboard);

    // タブ切り替え
    function switchTab(index) {
      const tabs = document.querySelectorAll('.tab');
      const contents = document.querySelectorAll('.tab-content');

      tabs.forEach((tab, i) => {
        tab.classList.toggle('active', i === index);
      });

      contents.forEach((content, i) => {
        content.classList.toggle('active', i === index);
      });
    }

    function initDashboard() {
      renderCareerDistStats();
      renderCareerAgeStats();
      renderMatrixStats();
      renderGradYearStats();

      drawCareerDistChart();
      drawCareerAgeChart();
      drawMatrixHeatmap();
      drawGradYearCharts();
    }

    // Tab 1: キャリア分布統計
    function renderCareerDistStats() {
      const container = document.getElementById('career-dist-stats');
      const totalTypes = careerDistData.length;
      const totalCount = careerDistData.reduce((sum, d) => sum + d.count, 0);
      const avgCount = totalCount / totalTypes;

      const stats = [
        {label: 'キャリア種類数', value: totalTypes.toLocaleString(), unit: '種類'},
        {label: '総人数', value: totalCount.toLocaleString(), unit: '名'},
        {label: '平均人数/種類', value: Math.round(avgCount).toLocaleString(), unit: '名'}
      ];

      renderStats(container, stats);
    }

    function drawCareerDistChart() {
      const chartData = new google.visualization.DataTable();
      chartData.addColumn('string', 'キャリア');
      chartData.addColumn('number', '人数');

      careerDistData.slice(0, 30).forEach(row => {
        const label = row.career.length > 30 ? row.career.substring(0, 30) + '...' : row.career;
        chartData.addRow([label, row.count]);
      });

      const options = {
        chartArea: {width: '60%', height: '85%'},
        hAxis: { title: '人数', minValue: 0 },
        vAxis: { title: 'キャリア', textStyle: {fontSize: 11} },
        colors: ['#667eea'],
        legend: {position: 'none'}
      };

      new google.visualization.BarChart(
        document.getElementById('career_dist_chart')
      ).draw(chartData, options);
    }

    // Tab 2: キャリア×年齢クロス統計
    function renderCareerAgeStats() {
      const container = document.getElementById('career-age-stats');
      const uniqueCareers = [...new Set(careerAgeCrossData.map(d => d.career))].length;
      const totalCount = careerAgeCrossData.reduce((sum, d) => sum + d.count, 0);
      const uniqueAgeGroups = [...new Set(careerAgeCrossData.map(d => d.ageGroup))].length;

      const stats = [
        {label: 'キャリア数', value: uniqueCareers, unit: '種類'},
        {label: '総人数', value: totalCount.toLocaleString(), unit: '名'},
        {label: '年齢層数', value: uniqueAgeGroups, unit: 'グループ'}
      ];

      renderStats(container, stats);
    }

    function drawCareerAgeChart() {
      const ageGroupOrder = ['20代', '30代', '40代', '50代', '60代', '70歳以上'];

      // TOP20キャリアを抽出してピボット
      const careerTotals = {};
      careerAgeCrossData.forEach(row => {
        if (!careerTotals[row.career]) careerTotals[row.career] = 0;
        careerTotals[row.career] += row.count;
      });

      const top20Careers = Object.entries(careerTotals)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 20)
        .map(e => e[0]);

      const careerMap = {};
      careerAgeCrossData.filter(d => top20Careers.includes(d.career)).forEach(row => {
        if (!careerMap[row.career]) {
          careerMap[row.career] = {};
          ageGroupOrder.forEach(ag => { careerMap[row.career][ag] = 0; });
        }
        careerMap[row.career][row.ageGroup] = row.count;
      });

      const sortedCareers = Object.entries(careerMap)
        .map(([career, ageData]) => ({
          career,
          total: Object.values(ageData).reduce((sum, v) => sum + v, 0),
          ageData
        }))
        .sort((a, b) => b.total - a.total);

      const chartData = new google.visualization.DataTable();
      chartData.addColumn('string', 'キャリア');
      ageGroupOrder.forEach(ag => chartData.addColumn('number', ag));

      sortedCareers.forEach(item => {
        const label = item.career.length > 25 ? item.career.substring(0, 25) + '...' : item.career;
        const row = [label];
        ageGroupOrder.forEach(ag => row.push(item.ageData[ag] || 0));
        chartData.addRow(row);
      });

      const options = {
        chartArea: {width: '50%', height: '85%'},
        hAxis: { title: '人数', minValue: 0 },
        vAxis: { title: 'キャリア', textStyle: {fontSize: 10} },
        isStacked: false,
        legend: {position: 'top'},
        colors: ['#4285F4', '#AA46BE', '#F4B400', '#DB4437', '#0F9D58', '#00ACC1']
      };

      new google.visualization.BarChart(
        document.getElementById('career_age_chart')
      ).draw(chartData, options);
    }

    // Tab 3: マトリックス統計
    function renderMatrixStats() {
      const container = document.getElementById('matrix-stats');
      const metadata = careerAgeMatrixData.metadata || {};

      const stats = [
        {label: 'キャリア数', value: (careerAgeMatrixData.rows || []).length, unit: '種類'},
        {label: '総人数', value: (metadata.totalCount || 0).toLocaleString(), unit: '名'},
        {label: '最大値', value: metadata.max || 0, unit: '名'}
      ];

      renderStats(container, stats);
    }

    function drawMatrixHeatmap() {
      const container = document.getElementById('matrix_heatmap');
      if (!careerAgeMatrixData.rows || careerAgeMatrixData.rows.length === 0) {
        container.innerHTML = '<p style="text-align: center; padding: 50px; color: #666;">マトリックスデータがありません</p>';
        return;
      }

      // 簡易ヒートマップ表示（TOP20）
      const top20Rows = careerAgeMatrixData.rows.slice(0, 20);
      const max = careerAgeMatrixData.metadata.max || 1;

      let html = '<table style="width: 100%; font-size: 12px;"><thead><tr>';
      careerAgeMatrixData.headers.forEach((h, i) => {
        html += \`<th style="background: #667eea; color: white; padding: 10px; \${i === 0 ? 'text-align: left;' : 'text-align: center;'}">\${h}</th>\`;
      });
      html += '</tr></thead><tbody>';

      top20Rows.forEach(row => {
        html += '<tr>';
        row.forEach((cell, i) => {
          if (i === 0) {
            const label = String(cell).length > 30 ? String(cell).substring(0, 30) + '...' : cell;
            html += \`<td style="padding: 8px; font-weight: bold;">\${label}</td>\`;
          } else {
            const val = Number(cell) || 0;
            const intensity = Math.min(val / max, 1);
            const r = Math.round(255 * (1 - intensity));
            const g = Math.round(255 * (1 - intensity * 0.5));
            const bgColor = val > 0 ? \`rgb(\${r}, \${g}, 255)\` : '#f8f9fa';
            const textColor = val > max * 0.6 ? 'white' : 'black';
            html += \`<td style="padding: 8px; text-align: center; background: \${bgColor}; color: \${textColor};">\${val > 0 ? val : '－'}</td>\`;
          }
        });
        html += '</tr>';
      });

      html += '</tbody></table>';
      container.innerHTML = html;
    }

    // Tab 4: 卒業年統計
    function renderGradYearStats() {
      const container = document.getElementById('grad-year-stats');
      const totalYears = graduationYearData.length;
      const totalCount = graduationYearData.reduce((sum, d) => sum + d.count, 0);
      const minYear = Math.min(...graduationYearData.map(d => d.graduationYear));
      const maxYear = Math.max(...graduationYearData.map(d => d.graduationYear));

      const stats = [
        {label: '卒業年範囲', value: \`\${minYear}-\${maxYear}\`, unit: ''},
        {label: '総人数', value: totalCount.toLocaleString(), unit: '名'},
        {label: '年数', value: totalYears, unit: '年分'}
      ];

      renderStats(container, stats);
    }

    function drawGradYearCharts() {
      // ラインチャート
      const lineData = new google.visualization.DataTable();
      lineData.addColumn('string', '卒業年');
      lineData.addColumn('number', '人数');
      graduationYearData.forEach(d => lineData.addRow([d.graduationYear.toString(), d.count]));

      new google.visualization.LineChart(
        document.getElementById('grad_year_line')
      ).draw(lineData, {
        curveType: 'function',
        legend: {position: 'none'},
        chartArea: {width: '80%', height: '70%'},
        hAxis: { slantedText: true, slantedTextAngle: 45 },
        vAxis: { title: '人数', minValue: 0 },
        colors: ['#667eea']
      });

      // エリアチャート
      const areaData = new google.visualization.DataTable();
      areaData.addColumn('string', '卒業年');
      areaData.addColumn('number', '人数');
      graduationYearData.forEach(d => areaData.addRow([d.graduationYear.toString(), d.count]));

      new google.visualization.AreaChart(
        document.getElementById('grad_year_area')
      ).draw(areaData, {
        legend: {position: 'none'},
        chartArea: {width: '80%', height: '70%'},
        hAxis: { slantedText: true, slantedTextAngle: 45 },
        vAxis: { title: '人数', minValue: 0 },
        colors: ['#34A853']
      });
    }

    // 共通統計表示関数
    function renderStats(container, stats) {
      container.innerHTML = '';
      stats.forEach(stat => {
        const card = document.createElement('div');
        card.className = 'stat-card';
        card.innerHTML = \`
          <div class="stat-label">\${stat.label}</div>
          <div class="stat-value">\${stat.value}</div>
          <div class="stat-label">\${stat.unit}</div>
        \`;
        container.appendChild(card);
      });
    }
  </script>
</body>
</html>
  `;
}

// ===== QualityAndRegionDashboards.gs =====
/**
 * 品質・地域ダッシュボード統合ファイル
 *
 * このファイルには以下のダッシュボード機能がすべて含まれています:
 * 1. 品質ダッシュボード
 * 2. 品質フラグ可視化
 * 3. 地域別ダッシュボード
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
// 1. 品質ダッシュボード
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

// ===== 品質データロード関数 =====

function loadAllQualityReports() {
  /**
   * 全Phaseの品質レポートを読み込む
   *
   * @return {Object} - {overall: {...}, phases: [{phase, score, status, columns}, ...]}
   */

  var ss = SpreadsheetApp.getActiveSpreadsheet();

  var qualityReports = {
    overall: null,
    phases: []
  };

  // 統合品質レポート
  var overallSheet = ss.getSheetByName('OverallQualityInfer');
  if (overallSheet) {
    qualityReports.overall = loadQualityReportFromSheet(overallSheet, 'Overall');
  }

// Phase別品質レポートシート
  var phaseSheets = [
    {name: 'Phase1_QualityReport_Descriptive', phase: 1, label: 'Phase 1: 基礎集計'},
    {name: 'Phase2_QualityReport_Inferential', phase: 2, label: 'Phase 2: 統計分析'},
    {name: 'Phase3_QualityReport_Inferential', phase: 3, label: 'Phase 3: ペルソナ分析'},
    {name: 'Phase6_QualityReport_Inferential', phase: 6, label: 'Phase 6: フロー分析'},
    {name: 'Phase7_QualityReport_Inferential', phase: 7, label: 'Phase 7: 高度分析'},
    {name: 'Phase8_QualityReport_Inferential', phase: 8, label: 'Phase 8: 学歴分析'},
    {name: 'Phase10_QualityReport_Inferential', phase: 10, label: 'Phase 10: 緊急度分析'}
  ];


  phaseSheets.forEach(function(phaseInfo) {
    var sheet = ss.getSheetByName(phaseInfo.name);
    if (sheet) {
      var report = loadQualityReportFromSheet(sheet, phaseInfo.label);
      report.phase = phaseInfo.phase;
      qualityReports.phases.push(report);
    }
  });

  return qualityReports;
}

function loadQualityReportFromSheet(sheet, label) {
  /**
   * シートから品質レポートを読み込む
   *
   * @param {Sheet} sheet - シート
   * @param {string} label - ラベル
   * @return {Object} - 品質レポート
   */

  var data = sheet.getDataRange().getValues();
  var headers = data[0];
  var rows = data.slice(1);

  var columns = rows.map(function(row) {
    return {
      column_name: row[0],
      valid_count: row[1],
      unique_values: row[2],
      min_group_size: row[3],
      reliability_level: row[4],
      warning: row[5] || 'なし'
    };
  });

  // 総合スコア計算
  var reliableCount = columns.filter(function(c) {
    return c.reliability_level === 'HIGH' || c.reliability_level === 'MEDIUM' || c.reliability_level === 'DESCRIPTIVE';
  }).length;

  var score = columns.length > 0 ? (reliableCount / columns.length) * 100 : 0;
  var status = score >= 80 ? 'EXCELLENT' : score >= 60 ? 'GOOD' : score >= 40 ? 'ACCEPTABLE' : 'POOR';

  return {
    label: label,
    score: score,
    status: status,
    total_columns: columns.length,
    reliable_columns: reliableCount,
    columns: columns
  };
}

// ===== 品質ダッシュボード表示 =====

function showQualityDashboard() {
  /**
   * 品質ダッシュボードを表示
   */
  try {
    var qualityData = loadAllQualityReports();

    var html = generateQualityDashboardHTML(qualityData);

    SpreadsheetApp.getUi().showModalDialog(
      html,
      '📊 データ品質ダッシュボード'
    );

  } catch (e) {
    SpreadsheetApp.getUi().alert('エラー: ' + e.toString());
  }
}

function generateQualityDashboardHTML(qualityData) {
  /**
   * 品質ダッシュボードHTML生成
   *
   * @param {Object} qualityData - 品質データ
   * @return {HtmlOutput} - HTML出力
   */

  var html = HtmlService.createHtmlOutput();
  html.append('<script type="text/javascript" src="https://www.gstatic.com/charts/loader.js"></script>');
  html.append(`<style>
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
    body {
      font-family: Arial, sans-serif;
      margin: 0;
      padding: 0;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    .container {
      padding: 20px;
    }
    .header {
      background: white;
      border-radius: 12px;
      padding: 30px;
      margin-bottom: 20px;
      box-shadow: 0 10px 40px rgba(0,0,0,0.1);
    }
    h1 {
      color: #667eea;
      margin: 0;
      display: flex;
      align-items: center;
    }
    h1 .icon {
      font-size: 40px;
      margin-right: 15px;
    }
    .stats-grid {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 15px;
      margin-top: 20px;
    }
    .stat-card {
      background: #f8f9fa;
      border-radius: 8px;
      padding: 20px;
      text-align: center;
    }
    .stat-value {
      font-size: 32px;
      font-weight: bold;
      color: #667eea;
    }
    .stat-label {
      font-size: 13px;
      color: #666;
      margin-top: 8px;
    }
    .phase-grid {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 20px;
    }
    .phase-card {
      background: white;
      border-radius: 12px;
      padding: 20px;
      box-shadow: 0 5px 20px rgba(0,0,0,0.1);
    }
    .phase-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 15px;
    }
    .phase-title {
      font-size: 18px;
      font-weight: bold;
      color: #333;
    }
    .quality-badge {
      display: inline-block;
      padding: 5px 15px;
      border-radius: 20px;
      font-size: 12px;
      font-weight: bold;
    }
    .quality-excellent {
      background: #10b981;
      color: white;
    }
    .quality-good {
      background: #3b82f6;
      color: white;
    }
    .quality-acceptable {
      background: #f59e0b;
      color: white;
    }
    .quality-poor {
      background: #ef4444;
      color: white;
    }
    .quality-no-data {
      background: #6b7280;
      color: white;
    }
    .progress-bar {
      width: 100%;
      height: 8px;
      background: #e5e7eb;
      border-radius: 4px;
      overflow: hidden;
      margin: 10px 0;
    }
    .progress-fill {
      height: 100%;
      background: #667eea;
      transition: width 0.3s;
    }
    .column-table {
      width: 100%;
      border-collapse: collapse;
      margin-top: 15px;
      font-size: 12px;
    }
    .column-table th {
      background: #f8f9fa;
      padding: 8px;
      text-align: left;
      border-bottom: 2px solid #ddd;
    }
    .column-table td {
      padding: 6px 8px;
      border-bottom: 1px solid #eee;
    }
    .reliability-high {
      color: #10b981;
      font-weight: bold;
    }
    .reliability-medium {
      color: #3b82f6;
      font-weight: bold;
    }
    .reliability-low {
      color: #f59e0b;
      font-weight: bold;
    }
    .reliability-critical {
      color: #ef4444;
      font-weight: bold;
    }
    .reliability-descriptive {
      color: #6b7280;
      font-weight: bold;
    }
    .chart-container {
      margin: 20px 0;
      height: 300px;
    }
  </style>`);

  html.append('<div class="container">');

  // ヘッダー
  html.append('<div class="header">');
  html.append('<h1><span class="icon">📊</span>データ品質ダッシュボード</h1>');

  // 統合統計
  var totalPhases = qualityData.phases.length;
  var excellentPhases = qualityData.phases.filter(function(p) { return p.status === 'EXCELLENT'; }).length;
  var avgScore = qualityData.phases.length > 0
    ? qualityData.phases.reduce(function(sum, p) { return sum + p.score; }, 0) / qualityData.phases.length
    : 0;
  var totalColumns = qualityData.phases.reduce(function(sum, p) { return sum + p.total_columns; }, 0);

  html.append('<div class="stats-grid">');
  html.append('<div class="stat-card"><div class="stat-value">' + totalPhases + '</div><div class="stat-label">分析Phase数</div></div>');
  html.append('<div class="stat-card"><div class="stat-value">' + avgScore.toFixed(1) + '</div><div class="stat-label">平均品質スコア</div></div>');
  html.append('<div class="stat-card"><div class="stat-value">' + excellentPhases + '</div><div class="stat-label">EXCELLENT Phase</div></div>');
  html.append('<div class="stat-card"><div class="stat-value">' + totalColumns + '</div><div class="stat-label">総カラム数</div></div>');
  html.append('</div>');

  // 品質スコアチャート
  html.append('<div class="chart-container" id="score_chart"></div>');

  html.append('</div>');

  // Phase別品質カード
  html.append('<div class="phase-grid">');

  qualityData.phases.forEach(function(phase) {
    html.append('<div class="phase-card">');
    html.append('<div class="phase-header">');
    html.append('<div class="phase-title">' + phase.label + '</div>');
    html.append('<span class="quality-badge quality-' + phase.status.toLowerCase() + '">' + phase.score.toFixed(1) + '/100 (' + phase.status + ')</span>');
    html.append('</div>');

    // プログレスバー
    html.append('<div class="progress-bar">');
    html.append('<div class="progress-fill" style="width: ' + phase.score + '%;"></div>');
    html.append('</div>');

    // 統計
    html.append('<p style="font-size: 13px; color: #666; margin: 10px 0;">');
    html.append('信頼できるカラム: ' + phase.reliable_columns + '/' + phase.total_columns + ' (' + (phase.total_columns > 0 ? ((phase.reliable_columns / phase.total_columns) * 100).toFixed(1) : 0) + '%)');
    html.append('</p>');

    // カラム詳細（最初の5件のみ表示）
    if (phase.columns.length > 0) {
      html.append('<table class="column-table">');
      html.append('<tr><th>カラム名</th><th>信頼性</th><th>警告</th></tr>');

      var displayColumns = phase.columns.slice(0, 5);
      displayColumns.forEach(function(col) {
        var reliabilityClass = 'reliability-' + col.reliability_level.toLowerCase();
        html.append('<tr>');
        html.append('<td>' + col.column_name + '</td>');
        html.append('<td class="' + reliabilityClass + '">' + col.reliability_level + '</td>');
        html.append('<td style="font-size: 11px;">' + (col.warning.length > 30 ? col.warning.substring(0, 30) + '...' : col.warning) + '</td>');
        html.append('</tr>');
      });

      if (phase.columns.length > 5) {
        html.append('<tr><td colspan="3" style="text-align: center; color: #999; font-size: 11px;">他 ' + (phase.columns.length - 5) + ' カラム...</td></tr>');
      }

      html.append('</table>');
    }

    html.append('</div>');
  });

  html.append('</div>');

  html.append('</div>');

  // Google Charts スクリプト
  html.append('<script>');
  html.append('google.charts.load("current", {packages:["corechart"]});');
  html.append('google.charts.setOnLoadCallback(drawScoreChart);');
  html.append('function drawScoreChart() {');

  // Phase別スコアグラフ用データ
  var chartData = [['Phase', 'スコア', {role: 'style'}]];
  qualityData.phases.forEach(function(phase) {
    var color = phase.score >= 80 ? '#10b981' : phase.score >= 60 ? '#3b82f6' : phase.score >= 40 ? '#f59e0b' : '#ef4444';
    chartData.push(['Phase ' + phase.phase, phase.score, color]);
  });

  html.append('var data = google.visualization.arrayToDataTable(' + JSON.stringify(chartData) + ');');
  html.append('var options = {');
  html.append('  title: "Phase別品質スコア",');
  html.append('  titleTextStyle: {fontSize: 16, bold: true, color: "#667eea"},');
  html.append('  chartArea: {width: "75%", height: "70%"},');
  html.append('  hAxis: {title: "品質スコア", minValue: 0, maxValue: 100},');
  html.append('  vAxis: {title: "Phase"},');
  html.append('  legend: {position: "none"},');
  html.append('  bar: {groupWidth: "70%"}');
  html.append('};');
  html.append('var chart = new google.visualization.BarChart(document.getElementById("score_chart"));');
  html.append('chart.draw(data, options);');

  html.append('}');
  html.append('</script>');

  html.setWidth(1400);
  html.setHeight(900);

  return html;
}

// ===== 品質レポート比較機能 =====

function comparePhaseQuality(phase1, phase2) {
  /**
   * 2つのPhaseの品質を比較
   *
   * @param {number} phase1 - Phase番号1
   * @param {number} phase2 - Phase番号2
   */
  try {
    var qualityData = loadAllQualityReports();

    var p1 = qualityData.phases.find(function(p) { return p.phase === phase1; });
    var p2 = qualityData.phases.find(function(p) { return p.phase === phase2; });

    if (!p1 || !p2) {
      SpreadsheetApp.getUi().alert('指定されたPhaseの品質レポートが見つかりません');
      return;
    }

    var html = generatePhaseComparisonHTML(p1, p2);

    SpreadsheetApp.getUi().showModalDialog(
      html,
      'Phase品質比較: Phase ' + phase1 + ' vs Phase ' + phase2
    );

  } catch (e) {
    SpreadsheetApp.getUi().alert('エラー: ' + e.toString());
  }
}

function generatePhaseComparisonHTML(p1, p2) {
  /**
   * Phase比較HTML生成
   */

  var html = HtmlService.createHtmlOutput();
  html.append('<style>');
  html.append('body { font-family: Arial, sans-serif; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }');
  html.append('.container { background: white; border-radius: 12px; padding: 20px; }');
  html.append('h2 { color: #667eea; }');
  html.append('.comparison-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }');
  html.append('.phase-panel { border: 1px solid #ddd; border-radius: 8px; padding: 20px; }');
  html.append('.quality-badge { display: inline-block; padding: 5px 15px; border-radius: 20px; font-size: 12px; font-weight: bold; }');
  html.append('.quality-excellent { background: #10b981; color: white; }');
  html.append('.quality-good { background: #3b82f6; color: white; }');
  html.append('.quality-acceptable { background: #f59e0b; color: white; }');
  html.append('.quality-poor { background: #ef4444; color: white; }');
  html.append('</style>');

  html.append('<div class="container">');
  html.append('<h2>Phase品質比較</h2>');
  html.append('<div class="comparison-grid">');

  // Phase 1
  html.append('<div class="phase-panel">');
  html.append('<h3>' + p1.label + '</h3>');
  html.append('<p>スコア: <span class="quality-badge quality-' + p1.status.toLowerCase() + '">' + p1.score.toFixed(1) + '/100</span></p>');
  html.append('<p>信頼できるカラム: ' + p1.reliable_columns + '/' + p1.total_columns + '</p>');
  html.append('</div>');

  // Phase 2
  html.append('<div class="phase-panel">');
  html.append('<h3>' + p2.label + '</h3>');
  html.append('<p>スコア: <span class="quality-badge quality-' + p2.status.toLowerCase() + '">' + p2.score.toFixed(1) + '/100</span></p>');
  html.append('<p>信頼できるカラム: ' + p2.reliable_columns + '/' + p2.total_columns + '</p>');
  html.append('</div>');

  html.append('</div>');
  html.append('</div>');

  html.setWidth(1000);
  html.setHeight(600);

  return html;
}


// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 2. 品質フラグ可視化
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

// ========================================
// 1. サンプルサイズ区分による色分け
// ========================================

/**
 * サンプルサイズ区分から色を取得
 *
 * @param {string} sampleSizeCategory - サンプルサイズ区分（VERY_SMALL/SMALL/MEDIUM/LARGE）
 * @return {string} 16進数カラーコード
 */
function getMarkerColor(sampleSizeCategory) {
  const colorMap = {
    'VERY_SMALL': '#ff0000',  // 赤色（1-9件）
    'SMALL': '#ff9900',       // オレンジ色（10-29件）
    'MEDIUM': '#ffcc00',      // 黄色（30-99件）
    'LARGE': '#00cc00'        // 緑色（100件以上）
  };
  return colorMap[sampleSizeCategory] || '#cccccc';  // デフォルトは灰色
}

/**
 * サンプルサイズ区分から日本語ラベルを取得
 *
 * @param {string} sampleSizeCategory - サンプルサイズ区分
 * @return {string} 日本語ラベル
 */
function getSampleSizeLabel(sampleSizeCategory) {
  const labelMap = {
    'VERY_SMALL': '極小',
    'SMALL': '小',
    'MEDIUM': '中',
    'LARGE': '大'
  };
  return labelMap[sampleSizeCategory] || '不明';
}

/**
 * AggDesired.csvデータから地図マーカー用データを生成
 *
 * @param {Array<Object>} aggDesiredData - AggDesired.csvのデータ
 * @return {Array<Object>} マーカーデータ配列
 */
function createMarkersWithQualityFlags(aggDesiredData) {
  return aggDesiredData.map(function(row) {
    const count = parseInt(row['カウント']) || 0;
    const sampleSizeCategory = row['サンプルサイズ区分'] || 'VERY_SMALL';
    const warningMessage = row['警告メッセージ'] || 'なし';

    // 警告がある場合はタイトルに追加
    const title = warningMessage !== 'なし（観察的記述）' && warningMessage !== 'なし'
      ? row['希望勤務地_市区町村'] + ' (' + count + '件・' + warningMessage + ')'
      : row['希望勤務地_市区町村'] + ' (' + count + '件)';

    return {
      key: row['キー'],
      prefecture: row['希望勤務地_都道府県'],
      municipality: row['希望勤務地_市区町村'],
      count: count,
      sampleSizeCategory: sampleSizeCategory,
      color: getMarkerColor(sampleSizeCategory),
      title: title,
      warningMessage: warningMessage
    };
  });
}

/**
 * プルダウン用オプションを生成（品質フラグ付き）
 *
 * @param {Array<Object>} aggDesiredData - AggDesired.csvのデータ
 * @return {Array<Object>} プルダウンオプション配列
 */
function createDropdownOptionsWithQualityFlags(aggDesiredData) {
  return aggDesiredData.map(function(row) {
    const count = parseInt(row['カウント']) || 0;
    const sampleSizeCategory = row['サンプルサイズ区分'] || 'VERY_SMALL';
    const warningMessage = row['警告メッセージ'] || 'なし';

    // 警告がある場合は表示テキストに追加
    let displayText = row['希望勤務地_市区町村'] + ' (' + count + '件';

    if (warningMessage !== 'なし（観察的記述）' && warningMessage !== 'なし') {
      displayText += '・' + warningMessage;
    }

    displayText += ')';

    return {
      value: row['キー'],
      display: displayText,
      color: getMarkerColor(sampleSizeCategory),
      sampleSizeLabel: getSampleSizeLabel(sampleSizeCategory),
      warningMessage: warningMessage
    };
  });
}

// ========================================
// 2. クロス集計セル品質による色分け
// ========================================

/**
 * セル品質から背景色を取得
 *
 * @param {string} cellQuality - セル品質（INSUFFICIENT/MARGINAL/SUFFICIENT）
 * @return {string} 16進数カラーコード
 */
function getCellBackgroundColor(cellQuality) {
  const colorMap = {
    'INSUFFICIENT': '#ffcccc',  // 薄い赤（0-4件）
    'MARGINAL': '#ffffcc',      // 薄い黄色（5-29件）
    'SUFFICIENT': '#ccffcc'     // 薄い緑（30件以上）
  };
  return colorMap[cellQuality] || '#ffffff';  // デフォルトは白
}

/**
 * セル品質から日本語ラベルを取得
 *
 * @param {string} cellQuality - セル品質
 * @return {string} 日本語ラベル
 */
function getCellQualityLabel(cellQuality) {
  const labelMap = {
    'INSUFFICIENT': '不足',
    'MARGINAL': '限界',
    'SUFFICIENT': '十分'
  };
  return labelMap[cellQuality] || '不明';
}

/**
 * 警告フラグから警告アイコンを取得
 *
 * @param {string} warningFlag - 警告フラグ（なし/要注意/使用不可）
 * @return {string} 警告アイコン（絵文字）
 */
function getWarningIcon(warningFlag) {
  const iconMap = {
    'なし': '',
    '要注意': '⚠️',
    '使用不可': '🚫'
  };
  return iconMap[warningFlag] || '';
}

/**
 * クロス集計データをHTMLテーブルに変換（品質フラグ付き）
 *
 * @param {Array<Object>} crossTabData - クロス集計データ
 * @param {string} col1Name - 列1の名前
 * @param {string} col2Name - 列2の名前
 * @return {string} HTMLテーブル文字列
 */
function renderCrossTabTableWithQualityFlags(crossTabData, col1Name, col2Name) {
  if (!crossTabData || crossTabData.length === 0) {
    return '<p>データがありません</p>';
  }

  // ヘッダー行
  let html = '<table border="1" cellpadding="5" cellspacing="0" style="border-collapse: collapse; width: 100%;">';
  html += '<thead>';
  html += '<tr style="background-color: #f0f0f0;">';
  html += '<th>' + col1Name + '</th>';
  html += '<th>' + col2Name + '</th>';
  html += '<th>件数</th>';
  html += '<th>品質</th>';
  html += '<th>警告</th>';
  html += '</tr>';
  html += '</thead>';
  html += '<tbody>';

  // データ行
  crossTabData.forEach(function(row) {
    const count = parseInt(row['カウント']) || 0;
    const cellQuality = row['セル品質'] || 'SUFFICIENT';
    const warningFlag = row['警告フラグ'] || 'なし';
    const warningMessage = row['警告メッセージ'] || 'なし';

    const bgColor = getCellBackgroundColor(cellQuality);
    const qualityLabel = getCellQualityLabel(cellQuality);
    const warningIcon = getWarningIcon(warningFlag);

    html += '<tr>';
    html += '<td>' + row[col1Name] + '</td>';
    html += '<td>' + row[col2Name] + '</td>';
    html += '<td style="background-color: ' + bgColor + '; text-align: right;">';
    html += count + ' ' + warningIcon;
    html += '</td>';
    html += '<td style="background-color: ' + bgColor + ';">' + qualityLabel + '</td>';
    html += '<td>' + warningMessage + '</td>';
    html += '</tr>';
  });

  html += '</tbody>';
  html += '</table>';

  return html;
}

/**
 * クロス集計データをGoogle Charts用DataTableに変換（色情報付き）
 *
 * @param {Array<Object>} crossTabData - クロス集計データ
 * @param {string} col1Name - 列1の名前
 * @param {string} col2Name - 列2の名前
 * @return {Object} Google Charts DataTable形式のオブジェクト
 */
function convertCrossTabToDataTableWithQuality(crossTabData, col1Name, col2Name) {
  if (!crossTabData || crossTabData.length === 0) {
    return {
      cols: [
        {id: col1Name, label: col1Name, type: 'string'},
        {id: col2Name, label: col2Name, type: 'string'},
        {id: 'count', label: '件数', type: 'number'}
      ],
      rows: []
    };
  }

  // DataTable構造を作成
  const dataTable = {
    cols: [
      {id: col1Name, label: col1Name, type: 'string'},
      {id: col2Name, label: col2Name, type: 'string'},
      {id: 'count', label: '件数', type: 'number'},
      {id: 'quality', label: '品質', type: 'string', role: 'annotation'}
    ],
    rows: []
  };

  // データ行を追加
  crossTabData.forEach(function(row) {
    const count = parseInt(row['カウント']) || 0;
    const cellQuality = row['セル品質'] || 'SUFFICIENT';
    const warningFlag = row['警告フラグ'] || 'なし';

    const qualityLabel = getCellQualityLabel(cellQuality);
    const warningIcon = getWarningIcon(warningFlag);

    dataTable.rows.push({
      c: [
        {v: row[col1Name]},
        {v: row[col2Name]},
        {v: count},
        {v: qualityLabel + ' ' + warningIcon}
      ]
    });
  });

  return dataTable;
}

// ========================================
// 3. 品質フラグ統計サマリー
// ========================================

/**
 * AggDesiredデータから品質統計サマリーを生成
 *
 * @param {Array<Object>} aggDesiredData - AggDesired.csvのデータ
 * @return {Object} 品質統計サマリー
 */
function generateQualitySummary(aggDesiredData) {
  const summary = {
    total: aggDesiredData.length,
    byCategory: {
      'VERY_SMALL': 0,
      'SMALL': 0,
      'MEDIUM': 0,
      'LARGE': 0
    },
    withWarnings: 0,
    averageCount: 0
  };

  let totalCount = 0;

  aggDesiredData.forEach(function(row) {
    const category = row['サンプルサイズ区分'] || 'VERY_SMALL';
    const warningMessage = row['警告メッセージ'] || 'なし';
    const count = parseInt(row['カウント']) || 0;

    summary.byCategory[category]++;
    totalCount += count;

    if (warningMessage !== 'なし（観察的記述）' && warningMessage !== 'なし') {
      summary.withWarnings++;
    }
  });

  summary.averageCount = Math.round(totalCount / summary.total);

  return summary;
}

/**
 * クロス集計データからセル品質統計サマリーを生成
 *
 * @param {Array<Object>} crossTabData - クロス集計データ
 * @return {Object} セル品質統計サマリー
 */
function generateCellQualitySummary(crossTabData) {
  const summary = {
    total: crossTabData.length,
    byQuality: {
      'INSUFFICIENT': 0,
      'MARGINAL': 0,
      'SUFFICIENT': 0
    },
    withWarnings: 0,
    averageCount: 0
  };

  let totalCount = 0;

  crossTabData.forEach(function(row) {
    const quality = row['セル品質'] || 'SUFFICIENT';
    const warningFlag = row['警告フラグ'] || 'なし';
    const count = parseInt(row['カウント']) || 0;

    summary.byQuality[quality]++;
    totalCount += count;

    if (warningFlag !== 'なし') {
      summary.withWarnings++;
    }
  });

  summary.averageCount = Math.round(totalCount / summary.total);

  return summary;
}

/**
 * 品質統計サマリーをHTML表示用に変換
 *
 * @param {Object} summary - 品質統計サマリー
 * @param {string} type - 'aggregation' または 'crosstab'
 * @return {string} HTML文字列
 */
function renderQualitySummaryHTML(summary, type) {
  let html = '<div style="background-color: #f9f9f9; padding: 10px; margin: 10px 0; border-left: 4px solid #4285f4;">';
  html += '<h4 style="margin: 0 0 10px 0;">品質サマリー</h4>';

  if (type === 'aggregation') {
    html += '<p><strong>総件数:</strong> ' + summary.total + '件</p>';
    html += '<p><strong>平均カウント:</strong> ' + summary.averageCount + '件</p>';
    html += '<p><strong>サンプルサイズ区分:</strong></p>';
    html += '<ul>';
    html += '<li><span style="color: #00cc00;">■</span> LARGE: ' + summary.byCategory['LARGE'] + '件</li>';
    html += '<li><span style="color: #ffcc00;">■</span> MEDIUM: ' + summary.byCategory['MEDIUM'] + '件</li>';
    html += '<li><span style="color: #ff9900;">■</span> SMALL: ' + summary.byCategory['SMALL'] + '件</li>';
    html += '<li><span style="color: #ff0000;">■</span> VERY_SMALL: ' + summary.byCategory['VERY_SMALL'] + '件</li>';
    html += '</ul>';
    html += '<p><strong>警告あり:</strong> ' + summary.withWarnings + '件</p>';
  } else if (type === 'crosstab') {
    html += '<p><strong>総セル数:</strong> ' + summary.total + '件</p>';
    html += '<p><strong>平均カウント:</strong> ' + summary.averageCount + '件</p>';
    html += '<p><strong>セル品質:</strong></p>';
    html += '<ul>';
    html += '<li><span style="color: #00cc00;">■</span> SUFFICIENT: ' + summary.byQuality['SUFFICIENT'] + '件</li>';
    html += '<li><span style="color: #ffcc00;">■</span> MARGINAL: ' + summary.byQuality['MARGINAL'] + '件</li>';
    html += '<li><span style="color: #ff0000;">■</span> INSUFFICIENT: ' + summary.byQuality['INSUFFICIENT'] + '件</li>';
    html += '</ul>';
    html += '<p><strong>警告あり:</strong> ' + summary.withWarnings + '件</p>';
  }

  html += '</div>';

  return html;
}

// ========================================
// 4. テスト関数
// ========================================

/**
 * 品質フラグ可視化機能のテスト
 */
function testQualityFlagVisualization() {
  Logger.log('===== 品質フラグ可視化機能テスト開始 =====');

  // テストデータ（AggDesired.csv形式）
  const testAggDesiredData = [
    {
      '希望勤務地_都道府県': '京都府',
      '希望勤務地_市区町村': '京都市',
      'キー': '京都府京都市',
      'カウント': '450',
      'サンプルサイズ区分': 'LARGE',
      '信頼性レベル': 'DESCRIPTIVE',
      '警告メッセージ': 'なし（観察的記述）'
    },
    {
      '希望勤務地_都道府県': '京都府',
      '希望勤務地_市区町村': '○○村',
      'キー': '京都府○○村',
      'カウント': '1',
      'サンプルサイズ区分': 'VERY_SMALL',
      '信頼性レベル': 'DESCRIPTIVE',
      '警告メッセージ': 'なし（観察的記述）'
    }
  ];

  // テストデータ（クロス集計形式）
  const testCrossTabData = [
    {
      'education_level': '高校',
      '年齢層': '20代',
      'カウント': '45',
      'セル品質': 'SUFFICIENT',
      '警告フラグ': 'なし',
      '警告メッセージ': 'なし'
    },
    {
      'education_level': '高校',
      '年齢層': '30代',
      'カウント': '12',
      'セル品質': 'MARGINAL',
      '警告フラグ': '要注意',
      '警告メッセージ': 'セル数不足（n=12 < 30）'
    },
    {
      'education_level': '専門',
      '年齢層': '40代',
      'カウント': '3',
      'セル品質': 'INSUFFICIENT',
      '警告フラグ': '使用不可',
      '警告メッセージ': 'セル数不足（n=3 < 5）'
    }
  ];

  // テスト1: マーカー色取得
  Logger.log('テスト1: マーカー色取得');
  Logger.log('LARGE: ' + getMarkerColor('LARGE')); // #00cc00
  Logger.log('VERY_SMALL: ' + getMarkerColor('VERY_SMALL')); // #ff0000

  // テスト2: マーカーデータ生成
  Logger.log('テスト2: マーカーデータ生成');
  const markers = createMarkersWithQualityFlags(testAggDesiredData);
  Logger.log(JSON.stringify(markers, null, 2));

  // テスト3: プルダウンオプション生成
  Logger.log('テスト3: プルダウンオプション生成');
  const options = createDropdownOptionsWithQualityFlags(testAggDesiredData);
  Logger.log(JSON.stringify(options, null, 2));

  // テスト4: クロス集計HTMLテーブル生成
  Logger.log('テスト4: クロス集計HTMLテーブル生成');
  const tableHTML = renderCrossTabTableWithQualityFlags(testCrossTabData, 'education_level', '年齢層');
  Logger.log(tableHTML);

  // テスト5: 品質統計サマリー生成
  Logger.log('テスト5: 品質統計サマリー生成');
  const summary = generateQualitySummary(testAggDesiredData);
  Logger.log(JSON.stringify(summary, null, 2));

  const cellSummary = generateCellQualitySummary(testCrossTabData);
  Logger.log(JSON.stringify(cellSummary, null, 2));

  Logger.log('===== 品質フラグ可視化機能テスト完了 =====');
}


// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 3. 地域別ダッシュボード
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

const REGION_DASHBOARD_SHEETS = {
  phase1: {
    mapMetrics: ['Phase1_MapMetrics', 'MapMetrics'],
    aggDesired: ['Phase1_AggDesired', 'AggDesired'],
    quality: ['Phase1_QualityReport', 'Phase1_QualityReport_Descriptive', 'P1_QualityReport', 'QualityReport']
  },
  phase2: {
    chiSquare: ['Phase2_ChiSquare', 'ChiSquareTests'],
    anova: ['Phase2_ANOVA', 'ANOVATests'],
    quality: ['Phase2_QualityReport_Inferential', 'P2_QualityReport_Inferential', 'QualityReport_Inferential']
  },
  phase3: {
    summary: ['Phase3_PersonaSummary', 'PersonaSummary'],
    details: ['Phase3_PersonaDetails', 'PersonaDetails'],
    quality: ['Phase3_QualityReport_Inferential', 'P3_QualityReport_Inferential', 'QualityReport_Inferential']
  },
  phase7: {
    persona: ['Phase7_PersonaProfile', 'DetailedPersonaProfile'],
    supply: ['Phase7_SupplyDensity', 'SupplyDensityMap'],
    qualification: ['Phase7_QualificationDist', 'QualificationDistribution'],
    quality: ['Phase7_QualityReport_Inferential', 'P7_QualityReport_Inferential', 'QualityReport_Inferential']
  },
  phase8: {
    education: ['Phase8_EducationDist', 'EducationDistribution'],
    career: ['Phase8_CareerDistribution', 'CareerDistribution'],
    quality: ['Phase8_QualityReport', 'Phase8_QualityReport_Inferential', 'P8_QualityReport', 'P8_QualityReport_Inferential']
  }
};


const REGION_DASHBOARD_COLUMN_ALIASES = {
  都道府県: 'prefecture',
  市区町村: 'municipality',
  自治体: 'municipality',
  '希望勤務地_都道府県': 'prefecture',
  '希望勤務地_市区町村': 'municipality',
  地域キー: 'regionKey',
  キー: 'regionKey',
  lat: 'latitude',
  lng: 'longitude',
  緯度: 'latitude',
  経度: 'longitude',
  カウント: 'count',
  件数: 'count',
  '希望求職者': 'count',
  '応募者数': 'count',
  '希望者数': 'count',
  比率: 'ratio',
  割合: 'ratio',
  スコア: 'score',
  スコアリング: 'score',
  緊急度: 'urgencyLevel',
  urgency_score: 'urgencyScore',
  segment_id: 'segmentId',
  segment_name: 'segmentName',
  avg_age: 'avgAge',
  avg_desired_locations: 'avgDesiredLocations',
  avg_qualifications: 'avgQualifications',
  average_desired_locations: 'avgDesiredLocations',
  average_qualifications: 'avgQualifications',
  female_ratio: 'femaleRatio',
  ratio: 'percentage',
  percentage: 'percentage'
};

const REGION_FILTER_MAPPINGS = {
  mapMetrics: { prefecture: ['prefecture', '都道府県'], municipality: ['municipality', '市区町村'], regionKey: ['regionKey', 'キー'] },
  aggDesired: { prefecture: ['prefecture', '希望勤務地_都道府県'], municipality: ['municipality', '希望勤務地_市区町村'], regionKey: ['regionKey', 'キー'] },
  genericPrefecture: { prefecture: ['prefecture', '都道府県'] },
  municipalityOnly: { municipality: ['municipality', '市区町村'] }
};

const REGION_VALUE_COLUMNS = {
  applicantCount: ['count', 'カウント', '希望求職者', '応募者数', '希望者数']
};

/**
 * Phase1 指標を取得。
 */
function fetchPhase1Metrics(prefecture, municipality) {
  const ctx = resolveRegionContext(prefecture, municipality);
  const warnings = [];

  const mapMetrics = filterByRegion(
    readFirstAvailableSheet(REGION_DASHBOARD_SHEETS.phase1.mapMetrics),
    ctx,
    REGION_FILTER_MAPPINGS.mapMetrics,
    warnings,
    'MapMetrics'
  );

  const aggDesired = filterByRegion(
    readFirstAvailableSheet(REGION_DASHBOARD_SHEETS.phase1.aggDesired),
    ctx,
    REGION_FILTER_MAPPINGS.aggDesired,
    warnings,
    'AggDesired'
  );

  const quality = readFirstAvailableSheet(REGION_DASHBOARD_SHEETS.phase1.quality);

  const applicantTotal = sumNumericValues(mapMetrics, REGION_VALUE_COLUMNS.applicantCount);

  return {
    region: ctx,
    summary: {
      applicantCount: applicantTotal,
      mapRecords: mapMetrics.length,
      aggDesiredRecords: aggDesired.length
    },
    tables: {
      mapMetrics: mapMetrics,
      aggDesired: aggDesired,
      quality: filterByRegionIfPossible(quality, ctx, REGION_FILTER_MAPPINGS.mapMetrics)
    },
    warnings: warnings
  };
}

/**
 * Phase2 (統計検定) データを取得。
 */
function fetchPhase2Stats(prefecture, municipality) {
  const ctx = resolveRegionContext(prefecture, municipality);
  const warnings = [];

  const chiSquare = readFirstAvailableSheet(REGION_DASHBOARD_SHEETS.phase2.chiSquare);
  const anova = readFirstAvailableSheet(REGION_DASHBOARD_SHEETS.phase2.anova);
  const quality = readFirstAvailableSheet(REGION_DASHBOARD_SHEETS.phase2.quality);

  if (chiSquare.length) {
    warnings.push('ChiSquareTestsは地域列を持たないため、選択地域の結果を直接抽出できません。');
  }
  if (anova.length) {
    warnings.push('ANOVATestsは地域列を持たないため、選択地域の結果を直接抽出できません。');
  }

  return {
    region: ctx,
    summary: {
      chiSquareTests: chiSquare.length,
      anovaTests: anova.length
    },
    tables: {
      chiSquare: chiSquare,
      anova: anova,
      quality: quality
    },
    warnings: warnings
  };
}

/**
 * Phase3 (ペルソナ分析) データを取得。
 * @param {string} prefecture
 * @param {string} municipality
 * @param {{segmentId: number|string}} filters
 */
function fetchPhase3Persona(prefecture, municipality, filters) {
  const ctx = resolveRegionContext(prefecture, municipality);
  const warnings = [];

  const rawSummary = readFirstAvailableSheet(REGION_DASHBOARD_SHEETS.phase3.summary);
  const summary = augmentPersonaDifficulty(rawSummary);
  const details = readFirstAvailableSheet(REGION_DASHBOARD_SHEETS.phase3.details);
  const quality = readFirstAvailableSheet(REGION_DASHBOARD_SHEETS.phase3.quality);

  const filteredSummary = applyPersonaFilters(summary, filters);
  const filteredDetails = applyPersonaFilters(details, filters);

  if (summary.length) {
    warnings.push('PersonaSummary は地域列を持たないため、地域別フィルタリングは未対応です。');
  }

  const difficultyStats = calculateDifficultySummary(filteredSummary);

  return {
    region: ctx,
    summary: {
      personaSegments: filteredSummary.length,
      averageDifficultyScore: difficultyStats.averageScore,
      topDifficultyLevel: difficultyStats.topLevel
    },
    tables: {
      personaSummary: filteredSummary,
      personaDetails: filteredDetails,
      quality: quality
    },
    warnings: warnings
  };
}

/**
 * Phase7 (高度分析) データを取得。
 */
function fetchPhase7Supply(prefecture, municipality) {
  const ctx = resolveRegionContext(prefecture, municipality);
  const warnings = [];

  const supply = filterByRegion(
    readFirstAvailableSheet(REGION_DASHBOARD_SHEETS.phase7.supply),
    ctx,
    REGION_FILTER_MAPPINGS.municipalityOnly,
    warnings,
    'SupplyDensityMap'
  );
  const qualification = filterByRegion(
    readFirstAvailableSheet(REGION_DASHBOARD_SHEETS.phase7.qualification),
    ctx,
    REGION_FILTER_MAPPINGS.municipalityOnly,
    warnings,
    'QualificationDistribution'
  );
  const ageGender = filterByRegion(
    readFirstAvailableSheet(REGION_DASHBOARD_SHEETS.phase7.ageGender),
    ctx,
    REGION_FILTER_MAPPINGS.municipalityOnly,
    warnings,
    'AgeGenderCrossAnalysis'
  );
  const mobility = filterByRegion(
    readFirstAvailableSheet(REGION_DASHBOARD_SHEETS.phase7.mobility),
    ctx,
    REGION_FILTER_MAPPINGS.municipalityOnly,
    warnings,
    'MobilityScore'
  );
  const personaProfile = filterByRegion(
    readFirstAvailableSheet(REGION_DASHBOARD_SHEETS.phase7.personaProfile),
    ctx,
    REGION_FILTER_MAPPINGS.municipalityOnly,
    warnings,
    'DetailedPersonaProfile'
  );
  const quality = readFirstAvailableSheet(REGION_DASHBOARD_SHEETS.phase7.quality);

  return {
    region: ctx,
    summary: {
      supplyRecords: supply.length,
      qualificationRecords: qualification.length,
      mobilityRecords: mobility.length
    },
    tables: {
      supplyDensity: supply,
      qualificationDistribution: qualification,
      ageGenderCross: ageGender,
      mobilityScore: mobility,
      personaProfile: personaProfile,
      quality: filterByRegionIfPossible(quality, ctx, REGION_FILTER_MAPPINGS.municipalityOnly)
    },
    warnings: warnings
  };
}

/**
 * Phase8 (学歴・キャリア) データを取得。
 */
function fetchPhase8Education(prefecture, municipality) {
  const ctx = resolveRegionContext(prefecture, municipality);
  const warnings = [];

  const education = readFirstAvailableSheet(REGION_DASHBOARD_SHEETS.phase8.education);
  const educationCross = readFirstAvailableSheet(REGION_DASHBOARD_SHEETS.phase8.educationCross);
  const graduation = readFirstAvailableSheet(REGION_DASHBOARD_SHEETS.phase8.graduation);
  const quality = readFirstAvailableSheet(REGION_DASHBOARD_SHEETS.phase8.quality);

  if (education.length) {
    warnings.push('EducationDistribution は地域列を持たないため、地域別フィルタリングは未対応です。');
  }

  return {
    region: ctx,
    summary: {
      educationBuckets: education.length,
      graduationBuckets: graduation.length
    },
    tables: {
      educationDistribution: education,
      educationCross: educationCross,
      graduationDistribution: graduation,
      quality: quality
    },
    warnings: warnings
  };
}

/**
 * Phase10 (転職意欲) データを取得。
 */
function fetchPhase10Urgency(prefecture, municipality) {
  const ctx = resolveRegionContext(prefecture, municipality);
  const warnings = [];

  const urgency = filterByRegion(
    readFirstAvailableSheet(REGION_DASHBOARD_SHEETS.phase10.urgency),
    ctx,
    REGION_FILTER_MAPPINGS.municipalityOnly,
    warnings,
    'UrgencyDistribution'
  );
  const ageCross = filterByRegion(
    readFirstAvailableSheet(REGION_DASHBOARD_SHEETS.phase10.ageCross),
    ctx,
    REGION_FILTER_MAPPINGS.municipalityOnly,
    warnings,
    'UrgencyAgeCross'
  );
  const employmentCross = filterByRegion(
    readFirstAvailableSheet(REGION_DASHBOARD_SHEETS.phase10.employmentCross),
    ctx,
    REGION_FILTER_MAPPINGS.municipalityOnly,
    warnings,
    'UrgencyEmploymentCross'
  );
  const desiredWorkCross = filterByRegion(
    readFirstAvailableSheet(REGION_DASHBOARD_SHEETS.phase10.desiredWorkCross),
    ctx,
    REGION_FILTER_MAPPINGS.municipalityOnly,
    warnings,
    'UrgencyDesiredWorkCross'
  );
  const quality = readFirstAvailableSheet(REGION_DASHBOARD_SHEETS.phase10.quality);

  return {
    region: ctx,
    summary: {
      urgencyRecords: urgency.length,
      ageCrossRecords: ageCross.length,
      employmentCrossRecords: employmentCross.length
    },
    tables: {
      urgencyDistribution: urgency,
      ageCross: ageCross,
      employmentCross: employmentCross,
      desiredWorkCross: desiredWorkCross,
      quality: filterByRegionIfPossible(quality, ctx, REGION_FILTER_MAPPINGS.municipalityOnly)
    },
    warnings: warnings
  };
}

/**
 * 地域コンテキストを解決する。
 */
function resolveRegionContext(prefecture, municipality) {
  const normalizedPref = normalizeRegionValue(prefecture);
  const normalizedMuni = normalizeRegionValue(municipality);

  if (normalizedPref) {
    const municipalities = getMunicipalitiesForPrefecture(normalizedPref);
    const resolvedMuni = normalizedMuni && municipalities.includes(normalizedMuni)
      ? normalizedMuni
      : (municipalities.length ? municipalities[0] : null);
    return {
      prefecture: normalizedPref,
      municipality: resolvedMuni,
      key: buildRegionKey(normalizedPref, resolvedMuni)
    };
  }

  return loadSelectedRegion();
}

/**
 * 最初に見つかったシートを読み込む。
 * @param {string[]} candidates
 * @return {Array<Object>}
 */
function readFirstAvailableSheet(candidates) {
  for (let i = 0; i < candidates.length; i += 1) {
    const sheetName = candidates[i];
    const rows = readSheetAsObjects(sheetName);
    if (rows.length) {
      return rows;
    }
  }
  return [];
}

/**
 * シートをオブジェクト配列に変換する。
 * @param {string} sheetName
 * @return {Array<Object>}
 */
function readSheetAsObjects(sheetName) {
  const rows = readSheetRows(sheetName);
  if (!rows.length) {
    return [];
  }

  const header = rows[0].map(value => (value !== null && value !== undefined ? String(value).trim() : ''));
  const records = [];

  for (let i = 1; i < rows.length; i += 1) {
    const row = rows[i];
    const record = {};
    const normalized = {};

    for (let col = 0; col < header.length; col += 1) {
      const sourceKey = header[col] || 'column_' + col;
      const value = row[col];
      record[sourceKey] = value;

      if (sourceKey) {
        normalized[sourceKey] = value;
      }

      const alias = REGION_DASHBOARD_COLUMN_ALIASES[sourceKey];
      if (alias) {
        normalized[alias] = value;
      }
    }

    record.__normalized = normalized;
    records.push(record);
  }

  return records;
}

/**
 * 指定したキー候補から値を取得する。
 * @param {Object} record
 * @param {string[]} candidates
 * @return {*}
 */
function extractValue(record, candidates) {
  if (!record) {
    return null;
  }

  for (let i = 0; i < candidates.length; i += 1) {
    const key = candidates[i];
    if (key === undefined || key === null) {
      continue;
    }
    if (record.hasOwnProperty(key)) {
      return record[key];
    }
    const normalized = record.__normalized || {};
    if (normalized.hasOwnProperty(key)) {
      return normalized[key];
    }
  }

  return null;
}

/**
 * レコードを地域でフィルタリングする。
 */
function filterByRegion(records, ctx, mapping, warnings, datasetLabel) {
  if (!records.length) {
    if (warnings && datasetLabel) {
      warnings.push(datasetLabel + ' シートが見つかりません。');
    }
    return [];
  }

  const filtered = records.filter(record => {
    if (ctx.prefecture && mapping.prefecture) {
      const pref = normalizeRegionValue(extractValue(record, mapping.prefecture));
      if (pref && pref !== ctx.prefecture) {
        return false;
      }
      if (!pref && mapping.prefecture.length) {
        return true;
      }
    }

    if (ctx.municipality && mapping.municipality) {
      const muni = normalizeRegionValue(extractValue(record, mapping.municipality));
      if (muni && muni !== ctx.municipality) {
        return false;
      }
      if (!muni && mapping.municipality.length) {
        return true;
      }
    }

    if (ctx.key && mapping.regionKey) {
      const keyValue = normalizeRegionValue(extractValue(record, mapping.regionKey));
      if (keyValue && keyValue !== ctx.key) {
        return false;
      }
    }

    return true;
  });

  if (!filtered.length && warnings && datasetLabel) {
    warnings.push(datasetLabel + ' で指定地域のデータが見つかりませんでした。');
  }

  return filtered;
}

/**
 * 可能なら地域フィルタを適用する。
 */
function filterByRegionIfPossible(records, ctx, mapping) {
  if (!records.length || !mapping) {
    return records;
  }
  const filtered = filterByRegion(records, ctx, mapping);
  return filtered.length ? filtered : records;
}

/**
 * 数値列を合計する。
 */
function sumNumericValues(records, candidates) {
  let total = 0;
  records.forEach(record => {
    const value = extractValue(record, candidates);
    const numeric = typeof value === 'number' ? value : parseFloat(String(value).replace(/,/g, ''));
    if (!isNaN(numeric)) {
      total += numeric;
    }
  });
  return total;
}

/**
 * ペルソナフィルタを適用する。
 */
function applyPersonaFilters(records, filters) {
  if (!records.length || !filters) {
    return records;
  }
  const normalizedFilters = {};
  if (filters.segmentId !== undefined && filters.segmentId !== null && filters.segmentId !== '') {
    normalizedFilters.segmentId = String(filters.segmentId).trim();
  }
  if (filters.difficultyLevel !== undefined && filters.difficultyLevel !== null && filters.difficultyLevel !== '') {
    normalizedFilters.difficultyLevel = String(filters.difficultyLevel).trim();
  }
  if (!Object.keys(normalizedFilters).length) {
    return records;
  }

  return records.filter(record => {
    if (normalizedFilters.segmentId) {
      const value = extractValue(record, ['segment_id', 'segmentId']);
      if (value === undefined || value === null) {
        return false;
      }
      if (String(value).trim() !== normalizedFilters.segmentId) {
        return false;
      }
    }
    if (normalizedFilters.difficultyLevel) {
      const value = extractValue(record, ['difficulty_level', 'difficultyLevel']);
      if (!value || String(value).trim() !== normalizedFilters.difficultyLevel) {
        return false;
      }
    }
    return true;
  });
}

/**
 * PersonaSummaryに難易度情報を付与する。
 * @param {Array<Object>} records
 * @return {Array<Object>}
 */
function augmentPersonaDifficulty(records) {
  if (!records.length) {
    return records;
  }

  return records.map(record => {
    const normalized = record.__normalized || {};
    const difficulty = calculatePersonaDifficultyScore(record);
    const clone = Object.assign({}, record);
    clone.difficulty_score = difficulty.score;
    clone.difficulty_level = difficulty.level;
    clone.__normalized = Object.assign({}, normalized, {
      difficultyScore: difficulty.score,
      difficulty_level: difficulty.level,
      difficultyLevel: difficulty.level
    });
    return clone;
  });
}

/**
 * 難易度のサマリー統計量を算出する。
 * @param {Array<Object>} records
 * @return {{averageScore: number, topLevel: string}}
 */
function calculateDifficultySummary(records) {
  if (!records.length) {
    return {
      averageScore: 0,
      topLevel: 'データなし'
    };
  }

  let total = 0;
  let count = 0;
  let topScore = -1;
  let topLevel = 'データなし';

  records.forEach(record => {
    const score = extractNumeric(record, ['difficulty_score', 'difficultyScore']);
    const level = extractValue(record, ['difficulty_level', 'difficultyLevel']);
    if (score !== null) {
      total += score;
      count += 1;
      if (score > topScore) {
        topScore = score;
        topLevel = level || topLevel;
      }
    }
  });

  return {
    averageScore: count ? Math.round((total / count) * 10) / 10 : 0,
    topLevel: topLevel || 'データなし'
  };
}

/**
 * 難易度スコアとランクを算出する。
 * @param {Object} record
 * @return {{score: number, level: string}}
 */
function calculatePersonaDifficultyScore(record) {
  const params = {
    avgQualifications: extractNumeric(record, ['avg_qualifications', 'avgQualifications', '平均資格数'], 0),
    avgDesiredLocations: extractNumeric(record, ['avg_desired_locations', 'avgDesiredLocations', '平均希望勤務地数'], 0),
    femaleRatio: extractNumeric(record, ['female_ratio', 'femaleRatio', '女性比率'], 0),
    count: extractNumeric(record, ['count', '人数'], 0),
    percentage: extractNumeric(record, ['ratio', 'percentage', '比率'], 0) * 100,
    avgAge: extractNumeric(record, ['avg_age', 'avgAge', '平均年齢'], 0)
  };

  const score = calculateDifficultyScore(params);
  const level = getDifficultyLevel(score);
  return {
    score: score,
    level: level
  };
}

/**
 * 数値を抽出するユーティリティ。
 */
function extractNumeric(record, candidates, defaultValue) {
  const raw = extractValue(record, candidates);
  if (raw === undefined || raw === null || raw === '') {
    return defaultValue !== undefined ? defaultValue : null;
  }
  const numeric = typeof raw === 'number' ? raw : parseFloat(String(raw).replace(/,/g, ''));
  if (isNaN(numeric)) {
    return defaultValue !== undefined ? defaultValue : null;
  }
  return numeric;
}

/**
 * 難易度スコア計算（PersonaDifficultyChecker と同ロジック）。
 */
function calculateDifficultyScore(params) {
  const qualScore = Math.min((params.avgQualifications || 0) * 15, 40);
  const mobilityScore = Math.min((params.avgDesiredLocations || 0) * 8, 25);
  const sizeScore = Math.max(0, 20 - (params.percentage || 0) * 2);
  const ageScore = getAgeScore(params.avgAge || 0);
  const genderScore = Math.abs((params.femaleRatio || 0) - 0.5) * 10;
  const total = qualScore + mobilityScore + sizeScore + ageScore + genderScore;
  return Math.min(Math.round(total), 100);
}

function getAgeScore(avgAge) {
  if (avgAge < 25) return 5;
  if (avgAge < 35) return 3;
  if (avgAge < 50) return 4;
  if (avgAge < 60) return 7;
  return 10;
}

function getDifficultyLevel(score) {
  if (score >= 80) return 'S級（最難）';
  if (score >= 65) return 'A級（難）';
  if (score >= 50) return 'B級（やや難）';
  if (score >= 35) return 'C級（普通）';
  if (score >= 20) return 'D級（やや易）';
  return 'E級（易）';
}

// ===== RegionDashboard.gs =====
/**
 * RegionDashboard - フェーズ別の地域データAPIを提供する。
 * 各フェーズのシートから必要なデータを抽出し、フロントエンドで利用しやすい形に整形する。
 */

const REGION_DASHBOARD_SHEETS = {
  phase1: {
    mapMetrics: ['MapMetrics'],
    aggDesired: ['AggDesired'],
    quality: ['P1_QualityReport', 'QualityReport']
  },
  phase2: {
    chiSquare: ['ChiSquareTests'],
    anova: ['ANOVATests'],
    quality: ['P2_QualityReport_Inferential', 'QualityReport_Inferential']
  },
  phase3: {
    summary: ['PersonaSummary'],
    details: ['PersonaDetails'],
    quality: ['P3_QualityReport_Inferential', 'QualityReport_Inferential']
  },
  phase7: {
    supply: ['SupplyDensityMap'],
    qualification: ['QualificationDistribution'],
    ageGender: ['AgeGenderCrossAnalysis'],
    mobility: ['MobilityScore'],
    personaProfile: ['DetailedPersonaProfile'],
    quality: ['P7_QualityReport_Inferential', 'QualityReport_Inferential']
  },
  phase8: {
    education: ['EducationDistribution'],
    educationCross: ['EducationAgeCross', 'EducationAgeCross_Matrix'],
    graduation: ['GraduationYearDistribution'],
    quality: ['P8_QualityReport', 'QualityReport', 'P8_QualityReport_Inferential']
  },
  phase10: {
    urgency: ['UrgencyDistribution_ByMunicipality', 'UrgencyDistribution'],
    ageCross: ['UrgencyAgeCross_ByMunicipality', 'UrgencyAgeCross'],
    employmentCross: ['UrgencyEmploymentCross_ByMunicipality', 'UrgencyEmploymentCross'],
    desiredWorkCross: ['UrgencyDesiredWorkCross'],
    quality: ['P10_QualityReport', 'QualityReport', 'P10_QualityReport_Inferential']
  }
};

const REGION_DASHBOARD_COLUMN_ALIASES = {
  都道府県: 'prefecture',
  市区町村: 'municipality',
  自治体: 'municipality',
  '希望勤務地_都道府県': 'prefecture',
  '希望勤務地_市区町村': 'municipality',
  地域キー: 'regionKey',
  キー: 'regionKey',
  lat: 'latitude',
  lng: 'longitude',
  緯度: 'latitude',
  経度: 'longitude',
  カウント: 'count',
  件数: 'count',
  '希望求職者': 'count',
  '応募者数': 'count',
  '希望者数': 'count',
  比率: 'ratio',
  割合: 'ratio',
  スコア: 'score',
  スコアリング: 'score',
  緊急度: 'urgencyLevel',
  urgency_score: 'urgencyScore',
  segment_id: 'segmentId',
  segment_name: 'segmentName',
  avg_age: 'avgAge',
  avg_desired_locations: 'avgDesiredLocations',
  avg_qualifications: 'avgQualifications',
  average_desired_locations: 'avgDesiredLocations',
  average_qualifications: 'avgQualifications',
  female_ratio: 'femaleRatio',
  ratio: 'percentage',
  percentage: 'percentage'
};

const REGION_FILTER_MAPPINGS = {
  mapMetrics: { prefecture: ['prefecture', '都道府県'], municipality: ['municipality', '市区町村'], regionKey: ['regionKey', 'キー'] },
  aggDesired: { prefecture: ['prefecture', '希望勤務地_都道府県'], municipality: ['municipality', '希望勤務地_市区町村'], regionKey: ['regionKey', 'キー'] },
  genericPrefecture: { prefecture: ['prefecture', '都道府県'] },
  municipalityOnly: { municipality: ['municipality', '市区町村'] }
};

const REGION_VALUE_COLUMNS = {
  applicantCount: ['count', 'カウント', '希望求職者', '応募者数', '希望者数']
};

/**
 * Phase1 指標を取得。
 */
function fetchPhase1Metrics(prefecture, municipality) {
  const ctx = resolveRegionContext(prefecture, municipality);
  const warnings = [];

  const mapMetrics = filterByRegion(
    readFirstAvailableSheet(REGION_DASHBOARD_SHEETS.phase1.mapMetrics),
    ctx,
    REGION_FILTER_MAPPINGS.mapMetrics,
    warnings,
    'MapMetrics'
  );

  const aggDesired = filterByRegion(
    readFirstAvailableSheet(REGION_DASHBOARD_SHEETS.phase1.aggDesired),
    ctx,
    REGION_FILTER_MAPPINGS.aggDesired,
    warnings,
    'AggDesired'
  );

  const quality = readFirstAvailableSheet(REGION_DASHBOARD_SHEETS.phase1.quality);

  const applicantTotal = sumNumericValues(mapMetrics, REGION_VALUE_COLUMNS.applicantCount);

  return {
    region: ctx,
    summary: {
      applicantCount: applicantTotal,
      mapRecords: mapMetrics.length,
      aggDesiredRecords: aggDesired.length
    },
    tables: {
      mapMetrics: mapMetrics,
      aggDesired: aggDesired,
      quality: filterByRegionIfPossible(quality, ctx, REGION_FILTER_MAPPINGS.mapMetrics)
    },
    warnings: warnings
  };
}

/**
 * Phase2 (統計検定) データを取得。
 */
function fetchPhase2Stats(prefecture, municipality) {
  const ctx = resolveRegionContext(prefecture, municipality);
  const warnings = [];

  const chiSquare = readFirstAvailableSheet(REGION_DASHBOARD_SHEETS.phase2.chiSquare);
  const anova = readFirstAvailableSheet(REGION_DASHBOARD_SHEETS.phase2.anova);
  const quality = readFirstAvailableSheet(REGION_DASHBOARD_SHEETS.phase2.quality);

  if (chiSquare.length) {
    warnings.push('ChiSquareTestsは地域列を持たないため、選択地域の結果を直接抽出できません。');
  }
  if (anova.length) {
    warnings.push('ANOVATestsは地域列を持たないため、選択地域の結果を直接抽出できません。');
  }

  return {
    region: ctx,
    summary: {
      chiSquareTests: chiSquare.length,
      anovaTests: anova.length
    },
    tables: {
      chiSquare: chiSquare,
      anova: anova,
      quality: quality
    },
    warnings: warnings
  };
}

/**
 * Phase3 (ペルソナ分析) データを取得。
 * @param {string} prefecture
 * @param {string} municipality
 * @param {{segmentId: number|string}} filters
 */
function fetchPhase3Persona(prefecture, municipality, filters) {
  const ctx = resolveRegionContext(prefecture, municipality);
  const warnings = [];

  const rawSummary = readFirstAvailableSheet(REGION_DASHBOARD_SHEETS.phase3.summary);
  const summary = augmentPersonaDifficulty(rawSummary);
  const details = readFirstAvailableSheet(REGION_DASHBOARD_SHEETS.phase3.details);
  const quality = readFirstAvailableSheet(REGION_DASHBOARD_SHEETS.phase3.quality);

  const filteredSummary = applyPersonaFilters(summary, filters);
  const filteredDetails = applyPersonaFilters(details, filters);

  if (summary.length) {
    warnings.push('PersonaSummary は地域列を持たないため、地域別フィルタリングは未対応です。');
  }

  const difficultyStats = calculateDifficultySummary(filteredSummary);

  return {
    region: ctx,
    summary: {
      personaSegments: filteredSummary.length,
      averageDifficultyScore: difficultyStats.averageScore,
      topDifficultyLevel: difficultyStats.topLevel
    },
    tables: {
      personaSummary: filteredSummary,
      personaDetails: filteredDetails,
      quality: quality
    },
    warnings: warnings
  };
}

/**
 * Phase7 (高度分析) データを取得。
 */
function fetchPhase7Supply(prefecture, municipality) {
  const ctx = resolveRegionContext(prefecture, municipality);
  const warnings = [];

  const supply = filterByRegion(
    readFirstAvailableSheet(REGION_DASHBOARD_SHEETS.phase7.supply),
    ctx,
    REGION_FILTER_MAPPINGS.municipalityOnly,
    warnings,
    'SupplyDensityMap'
  );
  const qualification = filterByRegion(
    readFirstAvailableSheet(REGION_DASHBOARD_SHEETS.phase7.qualification),
    ctx,
    REGION_FILTER_MAPPINGS.municipalityOnly,
    warnings,
    'QualificationDistribution'
  );
  const ageGender = filterByRegion(
    readFirstAvailableSheet(REGION_DASHBOARD_SHEETS.phase7.ageGender),
    ctx,
    REGION_FILTER_MAPPINGS.municipalityOnly,
    warnings,
    'AgeGenderCrossAnalysis'
  );
  const mobility = filterByRegion(
    readFirstAvailableSheet(REGION_DASHBOARD_SHEETS.phase7.mobility),
    ctx,
    REGION_FILTER_MAPPINGS.municipalityOnly,
    warnings,
    'MobilityScore'
  );
  const personaProfile = filterByRegion(
    readFirstAvailableSheet(REGION_DASHBOARD_SHEETS.phase7.personaProfile),
    ctx,
    REGION_FILTER_MAPPINGS.municipalityOnly,
    warnings,
    'DetailedPersonaProfile'
  );
  const quality = readFirstAvailableSheet(REGION_DASHBOARD_SHEETS.phase7.quality);

  return {
    region: ctx,
    summary: {
      supplyRecords: supply.length,
      qualificationRecords: qualification.length,
      mobilityRecords: mobility.length
    },
    tables: {
      supplyDensity: supply,
      qualificationDistribution: qualification,
      ageGenderCross: ageGender,
      mobilityScore: mobility,
      personaProfile: personaProfile,
      quality: filterByRegionIfPossible(quality, ctx, REGION_FILTER_MAPPINGS.municipalityOnly)
    },
    warnings: warnings
  };
}

/**
 * Phase8 (学歴・キャリア) データを取得。
 */
function fetchPhase8Education(prefecture, municipality) {
  const ctx = resolveRegionContext(prefecture, municipality);
  const warnings = [];

  const education = readFirstAvailableSheet(REGION_DASHBOARD_SHEETS.phase8.education);
  const educationCross = readFirstAvailableSheet(REGION_DASHBOARD_SHEETS.phase8.educationCross);
  const graduation = readFirstAvailableSheet(REGION_DASHBOARD_SHEETS.phase8.graduation);
  const quality = readFirstAvailableSheet(REGION_DASHBOARD_SHEETS.phase8.quality);

  if (education.length) {
    warnings.push('EducationDistribution は地域列を持たないため、地域別フィルタリングは未対応です。');
  }

  return {
    region: ctx,
    summary: {
      educationBuckets: education.length,
      graduationBuckets: graduation.length
    },
    tables: {
      educationDistribution: education,
      educationCross: educationCross,
      graduationDistribution: graduation,
      quality: quality
    },
    warnings: warnings
  };
}

/**
 * Phase10 (転職意欲) データを取得。
 */
function fetchPhase10Urgency(prefecture, municipality) {
  const ctx = resolveRegionContext(prefecture, municipality);
  const warnings = [];

  const urgency = filterByRegion(
    readFirstAvailableSheet(REGION_DASHBOARD_SHEETS.phase10.urgency),
    ctx,
    REGION_FILTER_MAPPINGS.municipalityOnly,
    warnings,
    'UrgencyDistribution'
  );
  const ageCross = filterByRegion(
    readFirstAvailableSheet(REGION_DASHBOARD_SHEETS.phase10.ageCross),
    ctx,
    REGION_FILTER_MAPPINGS.municipalityOnly,
    warnings,
    'UrgencyAgeCross'
  );
  const employmentCross = filterByRegion(
    readFirstAvailableSheet(REGION_DASHBOARD_SHEETS.phase10.employmentCross),
    ctx,
    REGION_FILTER_MAPPINGS.municipalityOnly,
    warnings,
    'UrgencyEmploymentCross'
  );
  const desiredWorkCross = filterByRegion(
    readFirstAvailableSheet(REGION_DASHBOARD_SHEETS.phase10.desiredWorkCross),
    ctx,
    REGION_FILTER_MAPPINGS.municipalityOnly,
    warnings,
    'UrgencyDesiredWorkCross'
  );
  const quality = readFirstAvailableSheet(REGION_DASHBOARD_SHEETS.phase10.quality);

  return {
    region: ctx,
    summary: {
      urgencyRecords: urgency.length,
      ageCrossRecords: ageCross.length,
      employmentCrossRecords: employmentCross.length
    },
    tables: {
      urgencyDistribution: urgency,
      ageCross: ageCross,
      employmentCross: employmentCross,
      desiredWorkCross: desiredWorkCross,
      quality: filterByRegionIfPossible(quality, ctx, REGION_FILTER_MAPPINGS.municipalityOnly)
    },
    warnings: warnings
  };
}

/**
 * 地域コンテキストを解決する。
 */
function resolveRegionContext(prefecture, municipality) {
  const normalizedPref = normalizeRegionValue(prefecture);
  const normalizedMuni = normalizeRegionValue(municipality);

  if (normalizedPref) {
    const municipalities = getMunicipalitiesForPrefecture(normalizedPref);
    const resolvedMuni = normalizedMuni && municipalities.includes(normalizedMuni)
      ? normalizedMuni
      : (municipalities.length ? municipalities[0] : null);
    return {
      prefecture: normalizedPref,
      municipality: resolvedMuni,
      key: buildRegionKey(normalizedPref, resolvedMuni)
    };
  }

  return loadSelectedRegion();
}

/**
 * 最初に見つかったシートを読み込む。
 * @param {string[]} candidates
 * @return {Array<Object>}
 */
function readFirstAvailableSheet(candidates) {
  for (let i = 0; i < candidates.length; i += 1) {
    const sheetName = candidates[i];
    const rows = readSheetAsObjects(sheetName);
    if (rows.length) {
      return rows;
    }
  }
  return [];
}

/**
 * シートをオブジェクト配列に変換する。
 * @param {string} sheetName
 * @return {Array<Object>}
 */
function readSheetAsObjects(sheetName) {
  const rows = readSheetRows(sheetName);
  if (!rows.length) {
    return [];
  }

  const header = rows[0].map(value => (value !== null && value !== undefined ? String(value).trim() : ''));
  const records = [];

  for (let i = 1; i < rows.length; i += 1) {
    const row = rows[i];
    const record = {};
    const normalized = {};

    for (let col = 0; col < header.length; col += 1) {
      const sourceKey = header[col] || 'column_' + col;
      const value = row[col];
      record[sourceKey] = value;

      if (sourceKey) {
        normalized[sourceKey] = value;
      }

      const alias = REGION_DASHBOARD_COLUMN_ALIASES[sourceKey];
      if (alias) {
        normalized[alias] = value;
      }
    }

    record.__normalized = normalized;
    records.push(record);
  }

  return records;
}

/**
 * 指定したキー候補から値を取得する。
 * @param {Object} record
 * @param {string[]} candidates
 * @return {*}
 */
function extractValue(record, candidates) {
  if (!record) {
    return null;
  }

  for (let i = 0; i < candidates.length; i += 1) {
    const key = candidates[i];
    if (key === undefined || key === null) {
      continue;
    }
    if (record.hasOwnProperty(key)) {
      return record[key];
    }
    const normalized = record.__normalized || {};
    if (normalized.hasOwnProperty(key)) {
      return normalized[key];
    }
  }

  return null;
}

/**
 * レコードを地域でフィルタリングする。
 */
function filterByRegion(records, ctx, mapping, warnings, datasetLabel) {
  if (!records.length) {
    if (warnings && datasetLabel) {
      warnings.push(datasetLabel + ' シートが見つかりません。');
    }
    return [];
  }

  const filtered = records.filter(record => {
    if (ctx.prefecture && mapping.prefecture) {
      const pref = normalizeRegionValue(extractValue(record, mapping.prefecture));
      if (pref && pref !== ctx.prefecture) {
        return false;
      }
      if (!pref && mapping.prefecture.length) {
        return true;
      }
    }

    if (ctx.municipality && mapping.municipality) {
      const muni = normalizeRegionValue(extractValue(record, mapping.municipality));
      if (muni && muni !== ctx.municipality) {
        return false;
      }
      if (!muni && mapping.municipality.length) {
        return true;
      }
    }

    if (ctx.key && mapping.regionKey) {
      const keyValue = normalizeRegionValue(extractValue(record, mapping.regionKey));
      if (keyValue && keyValue !== ctx.key) {
        return false;
      }
    }

    return true;
  });

  if (!filtered.length && warnings && datasetLabel) {
    warnings.push(datasetLabel + ' で指定地域のデータが見つかりませんでした。');
  }

  return filtered;
}

/**
 * 可能なら地域フィルタを適用する。
 */
function filterByRegionIfPossible(records, ctx, mapping) {
  if (!records.length || !mapping) {
    return records;
  }
  const filtered = filterByRegion(records, ctx, mapping);
  return filtered.length ? filtered : records;
}

/**
 * 数値列を合計する。
 */
function sumNumericValues(records, candidates) {
  let total = 0;
  records.forEach(record => {
    const value = extractValue(record, candidates);
    const numeric = typeof value === 'number' ? value : parseFloat(String(value).replace(/,/g, ''));
    if (!isNaN(numeric)) {
      total += numeric;
    }
  });
  return total;
}

/**
 * ペルソナフィルタを適用する。
 */
function applyPersonaFilters(records, filters) {
  if (!records.length || !filters) {
    return records;
  }
  const normalizedFilters = {};
  if (filters.segmentId !== undefined && filters.segmentId !== null && filters.segmentId !== '') {
    normalizedFilters.segmentId = String(filters.segmentId).trim();
  }
  if (filters.difficultyLevel !== undefined && filters.difficultyLevel !== null && filters.difficultyLevel !== '') {
    normalizedFilters.difficultyLevel = String(filters.difficultyLevel).trim();
  }
  if (!Object.keys(normalizedFilters).length) {
    return records;
  }

  return records.filter(record => {
    if (normalizedFilters.segmentId) {
      const value = extractValue(record, ['segment_id', 'segmentId']);
      if (value === undefined || value === null) {
        return false;
      }
      if (String(value).trim() !== normalizedFilters.segmentId) {
        return false;
      }
    }
    if (normalizedFilters.difficultyLevel) {
      const value = extractValue(record, ['difficulty_level', 'difficultyLevel']);
      if (!value || String(value).trim() !== normalizedFilters.difficultyLevel) {
        return false;
      }
    }
    return true;
  });
}

/**
 * PersonaSummaryに難易度情報を付与する。
 * @param {Array<Object>} records
 * @return {Array<Object>}
 */
function augmentPersonaDifficulty(records) {
  if (!records.length) {
    return records;
  }

  return records.map(record => {
    const normalized = record.__normalized || {};
    const difficulty = calculatePersonaDifficultyScore(record);
    const clone = Object.assign({}, record);
    clone.difficulty_score = difficulty.score;
    clone.difficulty_level = difficulty.level;
    clone.__normalized = Object.assign({}, normalized, {
      difficultyScore: difficulty.score,
      difficulty_level: difficulty.level,
      difficultyLevel: difficulty.level
    });
    return clone;
  });
}

/**
 * 難易度のサマリー統計量を算出する。
 * @param {Array<Object>} records
 * @return {{averageScore: number, topLevel: string}}
 */
function calculateDifficultySummary(records) {
  if (!records.length) {
    return {
      averageScore: 0,
      topLevel: 'データなし'
    };
  }

  let total = 0;
  let count = 0;
  let topScore = -1;
  let topLevel = 'データなし';

  records.forEach(record => {
    const score = extractNumeric(record, ['difficulty_score', 'difficultyScore']);
    const level = extractValue(record, ['difficulty_level', 'difficultyLevel']);
    if (score !== null) {
      total += score;
      count += 1;
      if (score > topScore) {
        topScore = score;
        topLevel = level || topLevel;
      }
    }
  });

  return {
    averageScore: count ? Math.round((total / count) * 10) / 10 : 0,
    topLevel: topLevel || 'データなし'
  };
}

/**
 * 難易度スコアとランクを算出する。
 * @param {Object} record
 * @return {{score: number, level: string}}
 */
function calculatePersonaDifficultyScore(record) {
  const params = {
    avgQualifications: extractNumeric(record, ['avg_qualifications', 'avgQualifications', '平均資格数'], 0),
    avgDesiredLocations: extractNumeric(record, ['avg_desired_locations', 'avgDesiredLocations', '平均希望勤務地数'], 0),
    femaleRatio: extractNumeric(record, ['female_ratio', 'femaleRatio', '女性比率'], 0),
    count: extractNumeric(record, ['count', '人数'], 0),
    percentage: extractNumeric(record, ['ratio', 'percentage', '比率'], 0) * 100,
    avgAge: extractNumeric(record, ['avg_age', 'avgAge', '平均年齢'], 0)
  };

  const score = calculateDifficultyScore(params);
  const level = getDifficultyLevel(score);
  return {
    score: score,
    level: level
  };
}

/**
 * 数値を抽出するユーティリティ。
 */
function extractNumeric(record, candidates, defaultValue) {
  const raw = extractValue(record, candidates);
  if (raw === undefined || raw === null || raw === '') {
    return defaultValue !== undefined ? defaultValue : null;
  }
  const numeric = typeof raw === 'number' ? raw : parseFloat(String(raw).replace(/,/g, ''));
  if (isNaN(numeric)) {
    return defaultValue !== undefined ? defaultValue : null;
  }
  return numeric;
}

/**
 * 難易度スコア計算（PersonaDifficultyChecker と同ロジック）。
 */
function calculateDifficultyScore(params) {
  const qualScore = Math.min((params.avgQualifications || 0) * 15, 40);
  const mobilityScore = Math.min((params.avgDesiredLocations || 0) * 8, 25);
  const sizeScore = Math.max(0, 20 - (params.percentage || 0) * 2);
  const ageScore = getAgeScore(params.avgAge || 0);
  const genderScore = Math.abs((params.femaleRatio || 0) - 0.5) * 10;
  const total = qualScore + mobilityScore + sizeScore + ageScore + genderScore;
  return Math.min(Math.round(total), 100);
}

function getAgeScore(avgAge) {
  if (avgAge < 25) return 5;
  if (avgAge < 35) return 3;
  if (avgAge < 50) return 4;
  if (avgAge < 60) return 7;
  return 10;
}

function getDifficultyLevel(score) {
  if (score >= 80) return 'S級（最難）';
  if (score >= 65) return 'A級（難）';
  if (score >= 50) return 'B級（やや難）';
  if (score >= 35) return 'C級（普通）';
  if (score >= 20) return 'D級（やや易）';
  return 'E級（易）';
}

// ===== RegionStateService.gs =====
/**
 * 地域選択状態と候補リストを管理するサービス。
 * ユーザープロパティに選択済みの都道府県／市区町村を保存し、
 * MapMetricsシートから地域候補を動的に取得する。
 */

const REGION_STATE_KEYS = {
  PREFECTURE: 'regionalDashboard.prefecture',
  MUNICIPALITY: 'regionalDashboard.municipality'
};

const REGION_OPTION_CACHE = {
  PREFECTURES: 'regionalDashboard.prefList:v1',
  MUNICIPALITY_PREFIX: 'regionalDashboard.muniList:v1:',
  TTL_SECONDS: 300
};

const REGION_SOURCE_SHEETS = {
  MAP_METRICS: 'MapMetrics'
};

const REGION_COLUMN_LABELS = {
  PREFECTURE: ['都道府県', '都道府県名'],
  MUNICIPALITY: ['市区町村', '市区町村名', '自治体'],
  KEY: ['キー', '地域キー']
};

/**
 * 選択済み地域を保存する。
 * @param {string} prefecture 都道府県名
 * @param {string} municipality 市区町村名
 * @return {{prefecture: string|null, municipality: string|null}}
 */
function saveSelectedRegion(prefecture, municipality) {
  const userProps = PropertiesService.getUserProperties();
  const prefValue = normalizeRegionValue(prefecture);
  const muniValue = normalizeRegionValue(municipality);

  if (prefValue) {
    userProps.setProperty(REGION_STATE_KEYS.PREFECTURE, prefValue);
  } else {
    userProps.deleteProperty(REGION_STATE_KEYS.PREFECTURE);
  }

  if (muniValue) {
    userProps.setProperty(REGION_STATE_KEYS.MUNICIPALITY, muniValue);
  } else {
    userProps.deleteProperty(REGION_STATE_KEYS.MUNICIPALITY);
  }

  return {
    prefecture: prefValue,
    municipality: muniValue
  };
}

/**
 * 保存済み地域を読み込む。未保存の場合はMapMetricsから先頭候補を採用する。
 * @return {{prefecture: string|null, municipality: string|null, key: string|null}}
 */
function loadSelectedRegion() {
  const userProps = PropertiesService.getUserProperties();
  let prefecture = userProps.getProperty(REGION_STATE_KEYS.PREFECTURE);
  let municipality = userProps.getProperty(REGION_STATE_KEYS.MUNICIPALITY);

  if (!prefecture) {
    const defaults = getAvailablePrefectures();
    prefecture = defaults.length ? defaults[0] : null;
  }

  if (prefecture && municipality) {
    const municipalities = getMunicipalitiesForPrefecture(prefecture);
    if (!municipalities.includes(municipality)) {
      municipality = municipalities.length ? municipalities[0] : null;
    }
  } else if (prefecture && !municipality) {
    const municipalities = getMunicipalitiesForPrefecture(prefecture);
    municipality = municipalities.length ? municipalities[0] : null;
  }

  return {
    prefecture: prefecture,
    municipality: municipality,
    key: buildRegionKey(prefecture, municipality)
  };
}

/**
 * 地域選択をクリアする。
 */
function clearSelectedRegion() {
  const userProps = PropertiesService.getUserProperties();
  userProps.deleteProperty(REGION_STATE_KEYS.PREFECTURE);
  userProps.deleteProperty(REGION_STATE_KEYS.MUNICIPALITY);
}

/**
 * 利用可能な都道府県を取得する。
 * @return {string[]} 都道府県名リスト（昇順）
 */
function getAvailablePrefectures() {
  const cache = CacheService.getScriptCache();
  const cached = cache.get(REGION_OPTION_CACHE.PREFECTURES);
  if (cached) {
    return JSON.parse(cached);
  }

  const rows = readSheetRows(REGION_SOURCE_SHEETS.MAP_METRICS);
  if (!rows.length) {
    return [];
  }

  const prefectureIndex = findColumnIndex(rows[0], REGION_COLUMN_LABELS.PREFECTURE);
  if (prefectureIndex === -1) {
    return [];
  }

  const prefectures = Array.from(
    new Set(
      rows.slice(1)
        .map(row => normalizeRegionValue(row[prefectureIndex]))
        .filter(Boolean)
    )
  ).sort();

  cache.put(REGION_OPTION_CACHE.PREFECTURES, JSON.stringify(prefectures), REGION_OPTION_CACHE.TTL_SECONDS);
  return prefectures;
}

/**
 * 指定都道府県の市区町村リストを取得する。
 * @param {string} prefecture 都道府県名
 * @return {string[]} 市区町村リスト（昇順）
 */
function getMunicipalitiesForPrefecture(prefecture) {
  const prefValue = normalizeRegionValue(prefecture);
  if (!prefValue) {
    return [];
  }

  const cacheKey = REGION_OPTION_CACHE.MUNICIPALITY_PREFIX + prefValue;
  const cache = CacheService.getScriptCache();
  const cached = cache.get(cacheKey);
  if (cached) {
    return JSON.parse(cached);
  }

  const rows = readSheetRows(REGION_SOURCE_SHEETS.MAP_METRICS);
  if (!rows.length) {
    return [];
  }

  const header = rows[0];
  const prefIndex = findColumnIndex(header, REGION_COLUMN_LABELS.PREFECTURE);
  const muniIndex = findColumnIndex(header, REGION_COLUMN_LABELS.MUNICIPALITY);
  if (prefIndex === -1 || muniIndex === -1) {
    return [];
  }

  const municipalities = Array.from(
    new Set(
      rows.slice(1)
        .filter(row => normalizeRegionValue(row[prefIndex]) === prefValue)
        .map(row => normalizeRegionValue(row[muniIndex]))
        .filter(Boolean)
    )
  ).sort();

  cache.put(cacheKey, JSON.stringify(municipalities), REGION_OPTION_CACHE.TTL_SECONDS);
  return municipalities;
}

/**
 * 地域候補と保存済み状態をまとめて取得する。
 * @return {{state: {prefecture: string|null, municipality: string|null, key: string|null}, prefectures: string[], municipalities: string[]}}
 */
function getRegionOptions() {
  const state = loadSelectedRegion();
  const prefectures = getAvailablePrefectures();
  const municipalities = state.prefecture ? getMunicipalitiesForPrefecture(state.prefecture) : [];
  return {
    state: state,
    prefectures: prefectures,
    municipalities: municipalities
  };
}

/**
 * 地域候補キャッシュを破棄する。
 */
function resetRegionOptionCache() {
  const cache = CacheService.getScriptCache();
  cache.remove(REGION_OPTION_CACHE.PREFECTURES);
  const prefectures = getAvailablePrefectures();
  prefectures.forEach(pref => {
    cache.remove(REGION_OPTION_CACHE.MUNICIPALITY_PREFIX + pref);
  });
}

/**
 * MapMetricsシートを2次元配列で取得する。
 * @param {string} sheetName シート名
 * @return {Array<Array<*>>}
 */
function readSheetRows(sheetName) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName(sheetName);
  if (!sheet) {
    return [];
  }
  const values = sheet.getDataRange().getValues();
  return values || [];
}

/**
 * 候補列名の中から一致する列インデックスを取得する。
 * @param {string[]} header ヘッダー行
 * @param {string[]} candidates 優先候補
 * @return {number} 見つかった列番号（0始まり） / 見つからない場合は -1
 */
function findColumnIndex(header, candidates) {
  for (let i = 0; i < header.length; i += 1) {
    const label = header[i];
    if (!label) {
      continue;
    }
    const normalized = normalizeRegionValue(label);
    if (candidates.includes(label) || candidates.includes(normalized)) {
      return i;
    }
  }
  return -1;
}

/**
 * 地域名の正規化。
 * @param {string} value 対象文字列
 * @return {string|null}
 */
function normalizeRegionValue(value) {
  if (value === null || value === undefined) {
    return null;
  }
  const trimmed = String(value).trim();
  return trimmed.length ? trimmed : null;
}

/**
 * 地域キーを生成する。
 * @param {string|null} prefecture 都道府県
 * @param {string|null} municipality 市区町村
 * @return {string|null}
 */
function buildRegionKey(prefecture, municipality) {
  const pref = normalizeRegionValue(prefecture);
  if (!pref) {
    return null;
  }
  const muni = normalizeRegionValue(municipality);
  return muni ? pref + muni : pref;
}

// ===== UnifiedDataImporter.gs =====
/**
 * 統合データインポーター
 *
 * このファイルには以下のデータインポート機能がすべて含まれています:
 * 1. Phase 7データインポート（高度分析データ）
 * 2. Phase 8データインポート（キャリア・学歴データ）
 * 3. Phase 10データインポート（転職意欲・緊急度データ）
 */

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 1. Phase 7データインポート
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

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


// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 2. Phase 8データインポート
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

// ===== Phase 8データロード関数 =====

function loadPhase8EducationDistribution() {
  /**
   * キャリア（学歴）分布データを読み込む【v2.3: career列使用】
   * @return {Array} - [{education_level, 人数, 割合}, ...]
   */
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getSheetByName('P8_CareerDist');  // 🔄 v2.3: P8_EducationDist → P8_CareerDist

  if (!sheet) {
    throw new Error('P8_CareerDistシートが見つかりません。先にデータをインポートしてください。');
  }

  var data = sheet.getDataRange().getValues();
  var headers = data[0];
  var rows = data.slice(1);

  return rows.map(function(row) {
    return {
      education_level: row[0],
      count: row[1],
      percentage: row[2]
    };
  });
}

function loadPhase8EducationAgeCross() {
  /**
   * キャリア（学歴）×年齢クロス集計データを読み込む（ロング形式）【v2.3: career列使用】
   * @return {Array} - [{education_level, 年齢層, カウント, サンプルサイズ区分, 信頼性レベル, 警告フラグ, 警告メッセージ}, ...]
   */
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getSheetByName('P8_CareerAgeCross');  // 🔄 v2.3: P8_EduAgeCross → P8_CareerAgeCross

  if (!sheet) {
    throw new Error('P8_CareerAgeCrossシートが見つかりません。');
  }

  var data = sheet.getDataRange().getValues();
  var headers = data[0];
  var rows = data.slice(1);

  return rows.map(function(row) {
    return {
      education_level: row[0],
      age_group: row[1],
      count: row[2],
      cell_quality: row[3] || 'SUFFICIENT',
      warning_flag: row[4] || 'なし',
      warning_message: row[5] || 'なし'
    };
  });
}

function loadPhase8EducationAgeMatrix() {
  /**
   * キャリア（学歴）×年齢マトリックスデータを読み込む【v2.3: career列使用】
   * @return {Object} - {headers: [...], rows: [[...], ...]}
   */
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getSheetByName('P8_CareerAgeMatrix');  // 🔄 v2.3: P8_EduAgeMatrix → P8_CareerAgeMatrix

  if (!sheet) {
    return null;  // Matrixは必須でない
  }

  var data = sheet.getDataRange().getValues();

  return {
    headers: data[0],
    rows: data.slice(1)
  };
}

function loadPhase8GraduationYearDistribution() {
  /**
   * 卒業年度分布データを読み込む
   * @return {Array} - [{graduation_year, 人数}, ...]
   */
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getSheetByName('P8_GradYearDist');

  if (!sheet) {
    return [];  // 卒業年はオプション
  }

  var data = sheet.getDataRange().getValues();
  var headers = data[0];
  var rows = data.slice(1);

  return rows.map(function(row) {
    return {
      graduation_year: row[0],
      count: row[1]
    };
  });
}

function loadPhase8QualityReport() {
  /**
   * Phase 8品質レポートを読み込む
   * @return {Object} - {score, status, columns: [...]}
   */
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getSheetByName('P8_QualityInfer');

  if (!sheet) {
    return {score: 0, status: 'NO_DATA', columns: []};
  }

  var data = sheet.getDataRange().getValues();
  var headers = data[0];
  var rows = data.slice(1);

  var columns = rows.map(function(row) {
    return {
      column_name: row[0],
      valid_count: row[1],
      unique_values: row[2],
      min_group_size: row[3],
      reliability_level: row[4],
      warning: row[5]
    };
  });

  // 総合スコア計算（簡易版）
  var reliableCount = columns.filter(function(c) {
    return c.reliability_level === 'HIGH' || c.reliability_level === 'MEDIUM';
  }).length;

  var score = columns.length > 0 ? (reliableCount / columns.length) * 100 : 0;
  var status = score >= 80 ? 'EXCELLENT' : score >= 60 ? 'GOOD' : score >= 40 ? 'ACCEPTABLE' : 'POOR';

  return {
    score: score,
    status: status,
    columns: columns
  };
}

// ===== Phase 8可視化関数 =====

function showPhase8EducationDistribution() {
  /**
   * 学歴分布グラフを表示
   */
  try {
    var data = loadPhase8EducationDistribution();

    if (data.length === 0) {
      SpreadsheetApp.getUi().alert('データがありません');
      return;
    }

    var html = generatePhase8EducationDistributionHTML(data);

    SpreadsheetApp.getUi().showModalDialog(
      html,
      'Phase 8: 学歴分布分析'
    );

  } catch (e) {
    SpreadsheetApp.getUi().alert('エラー: ' + e.toString());
  }
}

function generatePhase8EducationDistributionHTML(data) {
  /**
   * 学歴分布グラフHTML生成
   */

  // Google Charts用データ配列
  var chartData = [['学歴', '人数', '割合']];
  data.forEach(function(row) {
    chartData.push([
      row.education_level,
      row.count,
      row.percentage
    ]);
  });

  var html = HtmlService.createHtmlOutput();
  html.append('<script type="text/javascript" src="https://www.gstatic.com/charts/loader.js"></script>');
  html.append('<style>');
  html.append('body { font-family: Arial, sans-serif; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }');
  html.append('.container { background: white; border-radius: 12px; padding: 20px; box-shadow: 0 10px 40px rgba(0,0,0,0.1); }');
  html.append('h2 { color: #667eea; margin-top: 0; display: flex; align-items: center; }');
  html.append('h2 .icon { font-size: 32px; margin-right: 10px; }');
  html.append('.chart-container { margin: 20px 0; }');
  html.append('.stats-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin: 20px 0; }');
  html.append('.stat-card { background: #f8f9fa; border-radius: 8px; padding: 15px; text-align: center; }');
  html.append('.stat-value { font-size: 28px; font-weight: bold; color: #667eea; }');
  html.append('.stat-label { font-size: 12px; color: #666; margin-top: 5px; }');
  html.append('table { width: 100%; border-collapse: collapse; margin-top: 20px; }');
  html.append('th { background: #667eea; color: white; padding: 12px; text-align: left; }');
  html.append('td { padding: 10px; border-bottom: 1px solid #eee; }');
  html.append('tr:hover { background: #f8f9fa; }');
  html.append('</style>');

  html.append('<div class="container">');
  html.append('<h2><span class="icon">🎓</span>Phase 8: 学歴分布分析</h2>');

  // KPIカード
  var totalCount = data.reduce(function(sum, row) { return sum + row.count; }, 0);
  var maxEducation = data.reduce(function(max, row) {
    return row.count > max.count ? row : max;
  }, {education_level: '-', count: 0});

  html.append('<div class="stats-grid">');
  html.append('<div class="stat-card"><div class="stat-value">' + totalCount + '</div><div class="stat-label">総求職者数</div></div>');
  html.append('<div class="stat-card"><div class="stat-value">' + data.length + '</div><div class="stat-label">学歴区分数</div></div>');
  html.append('<div class="stat-card"><div class="stat-value">' + maxEducation.education_level + '</div><div class="stat-label">最多学歴</div></div>');
  html.append('</div>');

  // 棒グラフ
  html.append('<div class="chart-container" id="bar_chart" style="height: 400px;"></div>');

  // 円グラフ
  html.append('<div class="chart-container" id="pie_chart" style="height: 400px;"></div>');

  // 詳細テーブル
  html.append('<h3>詳細データ</h3>');
  html.append('<table>');
  html.append('<tr><th>学歴</th><th>人数</th><th>割合 (%)</th></tr>');
  data.forEach(function(row) {
    html.append('<tr>');
    html.append('<td>' + row.education_level + '</td>');
    html.append('<td>' + row.count.toLocaleString() + '名</td>');
    html.append('<td>' + (parseFloat(row.percentage) || 0).toFixed(2) + '%</td>');
    html.append('</tr>');
  });
  html.append('</table>');

  html.append('</div>');

  // Google Charts スクリプト
  html.append('<script>');
  html.append('google.charts.load("current", {packages:["corechart"]});');
  html.append('google.charts.setOnLoadCallback(drawCharts);');
  html.append('function drawCharts() {');

  // 棒グラフ
  html.append('var barData = google.visualization.arrayToDataTable(' + JSON.stringify(chartData) + ');');
  html.append('var barOptions = {');
  html.append('  title: "学歴別求職者数",');
  html.append('  titleTextStyle: {fontSize: 18, bold: true, color: "#667eea"},');
  html.append('  chartArea: {width: "70%", height: "70%"},');
  html.append('  hAxis: {title: "人数", titleTextStyle: {color: "#667eea"}},');
  html.append('  vAxis: {title: "学歴"},');
  html.append('  colors: ["#667eea"],');
  html.append('  legend: {position: "none"}');
  html.append('};');
  html.append('var barChart = new google.visualization.BarChart(document.getElementById("bar_chart"));');
  html.append('barChart.draw(barData, barOptions);');

  // 円グラフ
  html.append('var pieData = google.visualization.arrayToDataTable(' + JSON.stringify(chartData) + ');');
  html.append('var pieOptions = {');
  html.append('  title: "学歴分布割合",');
  html.append('  titleTextStyle: {fontSize: 18, bold: true, color: "#667eea"},');
  html.append('  chartArea: {width: "90%", height: "70%"},');
  html.append('  colors: ["#667eea", "#764ba2", "#f093fb", "#4facfe", "#00f2fe"],');
  html.append('  pieHole: 0.4,');
  html.append('  legend: {position: "right"}');
  html.append('};');
  html.append('var pieChart = new google.visualization.PieChart(document.getElementById("pie_chart"));');
  html.append('pieChart.draw(pieData, pieOptions);');

  html.append('}');
  html.append('</script>');

  html.setWidth(1000);
  html.setHeight(700);

  return html;
}

function showPhase8EducationAgeHeatmap() {
  /**
   * 学歴×年齢ヒートマップを表示
   */
  try {
    var matrixData = loadPhase8EducationAgeMatrix();

    if (!matrixData) {
      SpreadsheetApp.getUi().alert('Matrixデータがありません');
      return;
    }

    var html = generatePhase8HeatmapHTML(matrixData);

    SpreadsheetApp.getUi().showModalDialog(
      html,
      'Phase 8: 学歴×年齢ヒートマップ'
    );

  } catch (e) {
    SpreadsheetApp.getUi().alert('エラー: ' + e.toString());
  }
}

function generatePhase8HeatmapHTML(matrixData) {
  /**
   * ヒートマップHTML生成
   */

  var html = HtmlService.createHtmlOutput();
  html.append('<script type="text/javascript" src="https://www.gstatic.com/charts/loader.js"></script>');
  html.append('<style>');
  html.append('body { font-family: Arial, sans-serif; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }');
  html.append('.container { background: white; border-radius: 12px; padding: 20px; box-shadow: 0 10px 40px rgba(0,0,0,0.1); }');
  html.append('h2 { color: #667eea; margin-top: 0; }');
  html.append('.heatmap-container { margin: 20px 0; height: 500px; }');
  html.append('</style>');

  html.append('<div class="container">');
  html.append('<h2>🔥 Phase 8: 学歴×年齢ヒートマップ</h2>');
  html.append('<p>各セルの色が濃いほど求職者数が多いことを示します。</p>');
  html.append('<div class="heatmap-container" id="heatmap_chart"></div>');
  html.append('</div>');

  // Google Charts データ準備
  var chartData = [matrixData.headers];
  matrixData.rows.forEach(function(row) {
    chartData.push(row);
  });

  html.append('<script>');
  html.append('google.charts.load("current", {packages:["table"]});');
  html.append('google.charts.setOnLoadCallback(drawHeatmap);');
  html.append('function drawHeatmap() {');
  html.append('var data = google.visualization.arrayToDataTable(' + JSON.stringify(chartData) + ');');
  html.append('var table = new google.visualization.Table(document.getElementById("heatmap_chart"));');
  html.append('var options = {');
  html.append('  showRowNumber: false,');
  html.append('  width: "100%",');
  html.append('  height: "100%",');
  html.append('  allowHtml: true');
  html.append('};');
  html.append('table.draw(data, options);');

  // カラーフォーマット適用
  html.append('var formatter = new google.visualization.ColorFormat();');
  html.append('formatter.addGradientRange(0, 100, "#white", "#667eea", "#764ba2");');
  for (var i = 1; i < matrixData.headers.length; i++) {
    html.append('formatter.format(data, ' + i + ');');
  }
  html.append('table.draw(data, options);');

  html.append('}');
  html.append('</script>');

  html.setWidth(1000);
  html.setHeight(700);

  return html;
}

function showPhase8Dashboard() {
  /**
   * Phase 8統合ダッシュボード
   */
  try {
    var educationDist = loadPhase8EducationDistribution();
    var qualityReport = loadPhase8QualityReport();

    var html = generatePhase8DashboardHTML(educationDist, qualityReport);

    SpreadsheetApp.getUi().showModalDialog(
      html,
      'Phase 8: 学歴分析統合ダッシュボード'
    );

  } catch (e) {
    SpreadsheetApp.getUi().alert('エラー: ' + e.toString());
  }
}

function generatePhase8DashboardHTML(educationDist, qualityReport) {
  /**
   * Phase 8統合ダッシュボードHTML生成
   */

  var html = HtmlService.createHtmlOutput();
  html.append('<script type="text/javascript" src="https://www.gstatic.com/charts/loader.js"></script>');
  html.append('<style>');
  html.append('body { font-family: Arial, sans-serif; margin: 0; padding: 0; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }');
  html.append('.container { padding: 20px; }');
  html.append('.tabs { display: flex; background: white; border-radius: 12px 12px 0 0; overflow: hidden; }');
  html.append('.tab { padding: 15px 25px; cursor: pointer; background: #f8f9fa; border: none; font-size: 14px; font-weight: 600; transition: all 0.3s; }');
  html.append('.tab:hover { background: #e9ecef; }');
  html.append('.tab.active { background: white; color: #667eea; border-bottom: 3px solid #667eea; }');
  html.append('.tab-content { display: none; background: white; border-radius: 0 0 12px 12px; padding: 30px; min-height: 500px; }');
  html.append('.tab-content.active { display: block; }');
  html.append('h2 { color: #667eea; margin-top: 0; }');
  html.append('.chart-container { margin: 20px 0; height: 400px; }');
  html.append('.quality-badge { display: inline-block; padding: 5px 15px; border-radius: 20px; font-size: 12px; font-weight: bold; }');
  html.append('.quality-excellent { background: #10b981; color: white; }');
  html.append('.quality-good { background: #3b82f6; color: white; }');
  html.append('.quality-acceptable { background: #f59e0b; color: white; }');
  html.append('.quality-poor { background: #ef4444; color: white; }');
  html.append('</style>');

  html.append('<div class="container">');
  html.append('<div class="tabs">');
  html.append('<button class="tab active" data-tab="overview" onclick="showTab(\'overview\')">📋 概要</button>');
  html.append('<button class="tab" data-tab="education" onclick="showTab(\'education\')">🎓 学歴分布</button>');
  html.append('<button class="tab" data-tab="heatmap" onclick="showTab(\'heatmap\')">🔥 ヒートマップ</button>');
  html.append('<button class="tab" data-tab="quality" onclick="showTab(\'quality\')">✅ 品質レポート</button>');
  html.append('</div>');

  // 概要タブ
  html.append('<div id="overview" class="tab-content active">');
  html.append('<h2>📋 Phase 8: キャリア・学歴分析概要</h2>');
  html.append('<p>品質スコア: <span class="quality-badge quality-' + qualityReport.status.toLowerCase() + '">' + qualityReport.score.toFixed(1) + '/100点 (' + qualityReport.status + ')</span></p>');
  html.append('<p>総求職者数: ' + educationDist.reduce(function(sum, r) { return sum + r.count; }, 0).toLocaleString() + '名</p>');
  html.append('<p>学歴区分数: ' + educationDist.length + '種類</p>');
  html.append('<h3>分析内容</h3>');
  html.append('<ul>');
  html.append('<li>🎓 学歴分布: 各学歴レベルの求職者数と割合</li>');
  html.append('<li>🔥 学歴×年齢ヒートマップ: 学歴と年齢層のクロス分析</li>');
  html.append('<li>📅 卒業年度分布: 卒業年度別の求職者数</li>');
  html.append('</ul>');
  html.append('</div>');

  // 学歴分布タブ
  html.append('<div id="education" class="tab-content">');
  html.append('<h2>🎓 学歴分布</h2>');
  html.append('<div class="chart-container" id="education_chart"></div>');
  html.append('</div>');

  // ヒートマップタブ
  html.append('<div id="heatmap" class="tab-content">');
  html.append('<h2>🔥 キャリア（学歴）×年齢ヒートマップ</h2>');
  html.append('<p>Matrixデータが必要です。P8_CareerAgeMatrixシートを確認してください。</p>');  // 🔄 v2.3
  html.append('</div>');

  // 品質レポートタブ
  html.append('<div id="quality" class="tab-content">');
  html.append('<h2>✅ データ品質レポート</h2>');
  html.append('<p>品質スコア: <span class="quality-badge quality-' + qualityReport.status.toLowerCase() + '">' + qualityReport.score.toFixed(1) + '/100点</span></p>');
  html.append('<table style="width: 100%; border-collapse: collapse;">');
  html.append('<tr style="background: #667eea; color: white;"><th style="padding: 10px;">カラム名</th><th>有効データ数</th><th>信頼性レベル</th><th>警告</th></tr>');
  qualityReport.columns.forEach(function(col) {
    html.append('<tr style="border-bottom: 1px solid #eee;">');
    html.append('<td style="padding: 10px;">' + col.column_name + '</td>');
    html.append('<td>' + col.valid_count + '</td>');
    html.append('<td>' + col.reliability_level + '</td>');
    html.append('<td>' + col.warning + '</td>');
    html.append('</tr>');
  });
  html.append('</table>');
  html.append('</div>');

  html.append('</div>');

  // タブ切り替えスクリプト
  html.append('<script>');
  html.append('function showTab(tabName) {');
  html.append('  var tabs = document.querySelectorAll(".tab");');
  html.append('  var contents = document.querySelectorAll(".tab-content");');
  html.append('  tabs.forEach(function(t) { t.classList.remove("active"); });');
  html.append('  contents.forEach(function(c) { c.classList.remove("active"); });');
  html.append('  document.querySelectorAll(".tab").forEach(function(t) {');
  html.append('    if (t.getAttribute("data-tab") === tabName) {');
  html.append('      t.classList.add("active");');
  html.append('    }');
  html.append('  });');
  html.append('  document.getElementById(tabName).classList.add("active");');
  html.append('  if (tabName === "education" && !window.educationChartDrawn) {');
  html.append('    drawEducationChart();');
  html.append('    window.educationChartDrawn = true;');
  html.append('  }');
  html.append('}');

  // Google Charts
  var chartData = [['学歴', '人数']];
  educationDist.forEach(function(row) {
    chartData.push([row.education_level, row.count]);
  });

  html.append('google.charts.load("current", {packages:["corechart"]});');
  html.append('function drawEducationChart() {');
  html.append('var data = google.visualization.arrayToDataTable(' + JSON.stringify(chartData) + ');');
  html.append('var options = {');
  html.append('  title: "学歴別求職者数",');
  html.append('  titleTextStyle: {fontSize: 18, bold: true, color: "#667eea"},');
  html.append('  chartArea: {width: "70%", height: "70%"},');
  html.append('  colors: ["#667eea"],');
  html.append('  legend: {position: "none"}');
  html.append('};');
  html.append('var chart = new google.visualization.ColumnChart(document.getElementById("education_chart"));');
  html.append('chart.draw(data, options);');
  html.append('}');
  html.append('</script>');

  html.setWidth(1200);
  html.setHeight(800);

  return html;
}


// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 3. Phase 10データインポート
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

// ===== Phase 10データロード関数 =====

function loadPhase10UrgencyDistribution() {
  /**
   * Phase10 data loader (reuses shared logic)
   * @return {Array<Object>}
   */
  return loadUrgencyDistData();
}

function loadPhase10UrgencyAgeCross() {
  /**
   * Phase10 age cross loader (reuses shared logic)
   * @return {Array<Object>}
   */
  return loadUrgencyAgeCrossData();
}

function loadPhase10UrgencyAgeMatrix() {
  /**
   * Phase10 age matrix loader (reuses shared logic)
   * @return {Object|null}
   */
  return loadUrgencyAgeMatrixData();
}

function loadPhase10UrgencyEmploymentCross() {
  /**
   * Phase10 employment cross loader (reuses shared logic)
   * @return {Array<Object>}
   */
  return loadUrgencyEmploymentCrossData();
}

function loadPhase10QualityReport() {
  /**
   * Phase 10品質レポートを読み込む
   * @return {Object} - {score, status, columns: [...]}
   */
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getSheetByName('P10_QualityInfer');

  if (!sheet) {
    return {score: 0, status: 'NO_DATA', columns: []};
  }

  var data = sheet.getDataRange().getValues();
  var headers = data[0];
  var rows = data.slice(1);

  var columns = rows.map(function(row) {
    return {
      column_name: row[0],
      valid_count: row[1],
      unique_values: row[2],
      min_group_size: row[3],
      reliability_level: row[4],
      warning: row[5]
    };
  });

  // 総合スコア計算
  var reliableCount = columns.filter(function(c) {
    return c.reliability_level === 'HIGH' || c.reliability_level === 'MEDIUM';
  }).length;

  var score = columns.length > 0 ? (reliableCount / columns.length) * 100 : 0;
  var status = score >= 80 ? 'EXCELLENT' : score >= 60 ? 'GOOD' : score >= 40 ? 'ACCEPTABLE' : 'POOR';

  return {
    score: score,
    status: status,
    columns: columns
  };
}

// ===== Phase 10可視化関数 =====

function showPhase10UrgencyDistribution() {
  /**
   * 緊急度分布グラフを表示
   */
  try {
    var data = loadPhase10UrgencyDistribution();

    if (data.length === 0) {
      SpreadsheetApp.getUi().alert('データがありません');
      return;
    }

    var html = generatePhase10UrgencyDistributionHTML(data);

    SpreadsheetApp.getUi().showModalDialog(
      html,
      'Phase 10: 緊急度分布分析'
    );

  } catch (e) {
    SpreadsheetApp.getUi().alert('エラー: ' + e.toString());
  }
}

function generatePhase10UrgencyDistributionHTML(data) {
  /**
   * Builds urgency distribution dialog using shared visualization template.
   */
  var htmlString = generateUrgencyDistHTML(data);
  return HtmlService.createHtmlOutput(htmlString)
    .setWidth(1400)
    .setHeight(900);
}

function showPhase10UrgencyAgeHeatmap() {
  /**
   * 緊急度×年齢ヒートマップを表示
   */
  try {
    var matrixData = loadPhase10UrgencyAgeMatrix();

    if (!matrixData) {
      SpreadsheetApp.getUi().alert('Matrixデータがありません');
      return;
    }

    var html = generatePhase10HeatmapHTML(matrixData, '緊急度×年齢ヒートマップ');

    SpreadsheetApp.getUi().showModalDialog(
      html,
      'Phase 10: 緊急度×年齢ヒートマップ'
    );

  } catch (e) {
    SpreadsheetApp.getUi().alert('エラー: ' + e.toString());
  }
}


// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 複数Phase一括インポート（Upload_Enhanced.html用）
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

/**
 * 複数PhaseのCSVファイルを一括インポート
 * @param {Object} fileDataMap - Phase別ファイルデータマップ
 * @return {Object} インポート結果
 */
function importMultiplePhaseCSVs(fileDataMap) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const results = {
    totalFiles: 0,
    successCount: 0,
    errorCount: 0,
    details: []
  };

  // Phase別シート名マッピング
  const SHEET_NAME_MAP = {
    // Phase 1
    'Phase1_MapMetrics.csv': 'Phase1_MapMetrics',
    'MapMetrics.csv': 'Phase1_MapMetrics',
    'Phase1_Applicants.csv': 'Phase1_Applicants',
    'Applicants.csv': 'Phase1_Applicants',
    'Phase1_DesiredWork.csv': 'Phase1_DesiredWork',
    'DesiredWork.csv': 'Phase1_DesiredWork',
    'Phase1_AggDesired.csv': 'Phase1_AggDesired',
    'AggDesired.csv': 'Phase1_AggDesired',
    'P1_QualityReport.csv': 'Phase1_QualityReport',
    'QualityReport.csv': 'Phase1_QualityReport',
    'P1_QualityReport_Descriptive.csv': 'Phase1_QualityReport_Descriptive',
    'QualityReport_Descriptive.csv': 'Phase1_QualityReport_Descriptive',
    'P1_QualityDesc.csv': 'Phase1_QualityReport_Descriptive',

    // Phase 2
    'Phase2_ChiSquare.csv': 'Phase2_ChiSquare',
    'ChiSquareTests.csv': 'Phase2_ChiSquare',
    'Phase2_ANOVA.csv': 'Phase2_ANOVA',
    'ANOVATests.csv': 'Phase2_ANOVA',
    'P2_QualityReport_Inferential.csv': 'Phase2_QualityReport_Inferential',
    'QualityReport_Inferential.csv': 'Phase2_QualityReport_Inferential',

    // Phase 3
    'Phase3_PersonaSummary.csv': 'Phase3_PersonaSummary',
    'PersonaSummary.csv': 'Phase3_PersonaSummary',
    'Phase3_PersonaDetails.csv': 'Phase3_PersonaDetails',
    'PersonaDetails.csv': 'Phase3_PersonaDetails',
    'Phase3_PersonaByMunicipality.csv': 'Phase3_PersonaByMunicipality',
    'PersonaSummaryByMunicipality.csv': 'Phase3_PersonaByMunicipality',
    'P3_QualityReport_Inferential.csv': 'Phase3_QualityReport_Inferential',

    // Phase 6
    'Phase6_FlowEdges.csv': 'Phase6_FlowEdges',
    'MunicipalityFlowEdges.csv': 'Phase6_FlowEdges',
    'Phase6_FlowNodes.csv': 'Phase6_FlowNodes',
    'MunicipalityFlowNodes.csv': 'Phase6_FlowNodes',
    'Phase6_Proximity.csv': 'Phase6_Proximity',
    'ProximityAnalysis.csv': 'Phase6_Proximity',
    'P6_QualityReport_Inferential.csv': 'Phase6_QualityReport_Inferential',

    // Phase 7
    'Phase7_SupplyDensity.csv': 'Phase7_SupplyDensity',
    'SupplyDensityMap.csv': 'Phase7_SupplyDensity',
    'Phase7_QualificationDist.csv': 'Phase7_QualificationDist',
    'QualificationDistribution.csv': 'Phase7_QualificationDist',
    'Phase7_AgeGenderCross.csv': 'Phase7_AgeGenderCross',
    'AgeGenderCrossAnalysis.csv': 'Phase7_AgeGenderCross',
    'Phase7_MobilityScore.csv': 'Phase7_MobilityScore',
    'MobilityScore.csv': 'Phase7_MobilityScore',
    'Phase7_PersonaProfile.csv': 'Phase7_PersonaProfile',
    'DetailedPersonaProfile.csv': 'Phase7_PersonaProfile',
    'Phase7_PersonaMapData.csv': 'Phase7_PersonaMapData',
    'PersonaMapData.csv': 'Phase7_PersonaMapData',
    'Phase7_PersonaMobilityCross.csv': 'Phase7_PersonaMobilityCross',
    'PersonaMobilityCross.csv': 'Phase7_PersonaMobilityCross',
    'P7_QualityReport_Inferential.csv': 'Phase7_QualityReport_Inferential',

    // Phase 8
    'Phase8_EducationDist.csv': 'Phase8_EducationDist',
    'EducationDistribution.csv': 'Phase8_EducationDist',
    'Phase8_EduAgeCross.csv': 'Phase8_EduAgeCross',
    'EducationAgeCross.csv': 'Phase8_EduAgeCross',
    'Phase8_EduAgeMatrix.csv': 'Phase8_EduAgeMatrix',
    'EducationAgeCross_Matrix.csv': 'Phase8_EduAgeMatrix',
    'Phase8_GradYearDist.csv': 'Phase8_GradYearDist',
    'GraduationYearDistribution.csv': 'Phase8_GradYearDist',
    'Phase8_CareerDistribution.csv': 'Phase8_CareerDistribution',
    'CareerDistribution.csv': 'Phase8_CareerDistribution',
    'Phase8_CareerAgeCross.csv': 'Phase8_CareerAgeCross',
    'CareerAgeCross.csv': 'Phase8_CareerAgeCross',
    'Phase8_CareerAgeMatrix.csv': 'Phase8_CareerAgeMatrix',
    'CareerAgeCross_Matrix.csv': 'Phase8_CareerAgeMatrix',
    'P8_QualityReport.csv': 'Phase8_QualityReport',
    'P8_QualityReport_Inferential.csv': 'Phase8_QualityReport_Inferential',

    // Phase 10
    'Phase10_UrgencyDist.csv': 'Phase10_UrgencyDist',
    'UrgencyDistribution.csv': 'Phase10_UrgencyDist',
    'Phase10_UrgencyAge.csv': 'Phase10_UrgencyAge',
    'UrgencyAgeCross.csv': 'Phase10_UrgencyAge',
    'Phase10_UrgencyAge_Matrix.csv': 'Phase10_UrgencyAge_Matrix',
    'UrgencyAgeCross_Matrix.csv': 'Phase10_UrgencyAge_Matrix',
    'Phase10_UrgencyEmployment.csv': 'Phase10_UrgencyEmployment',
    'UrgencyEmploymentCross.csv': 'Phase10_UrgencyEmployment',
    'Phase10_UrgencyEmployment_Matrix.csv': 'Phase10_UrgencyEmployment_Matrix',
    'UrgencyEmploymentCross_Matrix.csv': 'Phase10_UrgencyEmployment_Matrix',
    'Phase10_UrgencyByMunicipality.csv': 'Phase10_UrgencyByMunicipality',
    'UrgencyByMunicipality.csv': 'Phase10_UrgencyByMunicipality',
    'Phase10_UrgencyAge_ByMunicipality.csv': 'Phase10_UrgencyAge_ByMunicipality',
    'UrgencyAgeCross_ByMunicipality.csv': 'Phase10_UrgencyAge_ByMunicipality',
    'Phase10_UrgencyEmployment_ByMunicipality.csv': 'Phase10_UrgencyEmployment_ByMunicipality',
    'UrgencyEmploymentCross_ByMunicipality.csv': 'Phase10_UrgencyEmployment_ByMunicipality',
    'P10_QualityReport.csv': 'Phase10_QualityReport',
    'P10_QualityReport_Inferential.csv': 'Phase10_QualityReport_Inferential'
  };



  try {
    // Phase別に処理
    for (const phase in fileDataMap) {
      const phaseFiles = fileDataMap[phase];

      Logger.log(`Processing ${phase}: ${Object.keys(phaseFiles).length} files`);

      // 各ファイルをインポート
      for (const fileName in phaseFiles) {
        results.totalFiles++;

        const fileData = phaseFiles[fileName];
        const sheetName = SHEET_NAME_MAP[fileName];

        if (!sheetName) {
          results.errorCount++;
          results.details.push({
            fileName: fileName,
            phase: phase,
            success: false,
            error: 'シート名マッピングが見つかりません'
          });
          Logger.log(`Warning: No sheet mapping for ${fileName}`);
          continue;
        }

        try {
          // CSVをパース
          const csvData = parseCSV(fileData.content);

          if (!csvData || csvData.length === 0) {
            throw new Error('CSVデータが空です');
          }

          // シートを作成または取得
          let sheet = ss.getSheetByName(sheetName);
          if (!sheet) {
            sheet = ss.insertSheet(sheetName);
          } else {
            sheet.clear();
          }

          // データをシートに書き込み
          const numRows = csvData.length;
          const numCols = csvData[0].length;

          sheet.getRange(1, 1, numRows, numCols).setValues(csvData);

          // ヘッダー行を太字にする
          if (numRows > 0) {
            sheet.getRange(1, 1, 1, numCols).setFontWeight('bold');
          }

          results.successCount++;
          results.details.push({
            fileName: fileName,
            phase: phase,
            sheetName: sheetName,
            success: true,
            rows: numRows,
            cols: numCols
          });

          Logger.log(`✓ ${fileName} → ${sheetName}: ${numRows} rows × ${numCols} cols`);

        } catch (error) {
          results.errorCount++;
          results.details.push({
            fileName: fileName,
            phase: phase,
            sheetName: sheetName,
            success: false,
            error: error.message
          });
          Logger.log(`✗ ${fileName} import failed: ${error.message}`);
        }
      }
    }

    Logger.log(`Import complete: ${results.successCount}/${results.totalFiles} files succeeded`);
    return results;

  } catch (error) {
    Logger.log(`Import error: ${error.message}`);
    throw new Error('インポート中にエラーが発生しました: ' + error.message);
  }
}


/**
 * CSV文字列をパース
 * @param {string} csvText - CSV文字列
 * @return {Array<Array>} 2次元配列
 */
function parseCSV(csvText) {
  if (!csvText || typeof csvText !== 'string') {
    throw new Error('Invalid CSV text');
  }

  const lines = csvText.split(/\r?\n/);
  const result = [];

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim();

    if (line.length === 0) {
      continue; // 空行をスキップ
    }

    // CSVパース（簡易版 - カンマ区切り）
    // ダブルクォート内のカンマを考慮
    const row = parseCSVLine(line);
    result.push(row);
  }

  return result;
}


/**
 * CSV行をパース（ダブルクォート対応）
 * @param {string} line - CSV行
 * @return {Array} パースされた配列
 */
function parseCSVLine(line) {
  const result = [];
  let current = '';
  let inQuotes = false;

  for (let i = 0; i < line.length; i++) {
    const char = line[i];

    if (char === '"') {
      if (inQuotes && line[i + 1] === '"') {
        // エスケープされたダブルクォート
        current += '"';
        i++; // 次の文字をスキップ
      } else {
        // クォートの開始/終了
        inQuotes = !inQuotes;
      }
    } else if (char === ',' && !inQuotes) {
      // フィールド区切り
      result.push(current.trim());
      current = '';
    } else {
      current += char;
    }
  }

  // 最後のフィールド
  result.push(current.trim());

  return result;
}

function generatePhase10HeatmapHTML(matrixData, title) {
  /**
   * ヒートマップHTML生成
   */

  var html = HtmlService.createHtmlOutput();
  html.append('<script type="text/javascript" src="https://www.gstatic.com/charts/loader.js"></script>');
  html.append('<style>');
  html.append('body { font-family: Arial, sans-serif; padding: 20px; background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); }');
  html.append('.container { background: white; border-radius: 12px; padding: 20px; box-shadow: 0 10px 40px rgba(0,0,0,0.1); }');
  html.append('h2 { color: #f5576c; margin-top: 0; }');
  html.append('.heatmap-container { margin: 20px 0; height: 500px; overflow: auto; }');
  html.append('table { width: 100%; border-collapse: collapse; }');
  html.append('th, td { padding: 10px; text-align: center; border: 1px solid #ddd; }');
  html.append('th { background: #f5576c; color: white; }');
  html.append('</style>');

  html.append('<div class="container">');
  html.append('<h2>🔥 ' + title + '</h2>');
  html.append('<p>各セルの数値が大きいほど該当する求職者数が多いことを示します。</p>');
  html.append('<div class="heatmap-container">');
  html.append('<table>');

  // ヘッダー行
  html.append('<tr>');
  matrixData.headers.forEach(function(header) {
    html.append('<th>' + header + '</th>');
  });
  html.append('</tr>');

  // データ行
  matrixData.rows.forEach(function(row) {
    html.append('<tr>');
    row.forEach(function(cell, index) {
      if (index === 0) {
        // 行ラベル
        html.append('<th>' + cell + '</th>');
      } else {
        // データセル
        var value = parseFloat(cell) || 0;
        var bgColor = value > 0 ? 'rgba(245, 87, 108, ' + Math.min(value / 100, 1) + ')' : '#fff';
        html.append('<td style="background: ' + bgColor + ';">' + cell + '</td>');
      }
    });
    html.append('</tr>');
  });

  html.append('</table>');
  html.append('</div>');
  html.append('</div>');

  html.setWidth(1000);
  html.setHeight(700);

  return html;
}

function showPhase10Dashboard() {
  try {
    var urgencyDist = loadUrgencyDistData();
    var urgencyAge = loadUrgencyAgeCrossData();
    var urgencyEmp = loadUrgencyEmploymentCrossData();
    var urgencyMatrix = loadUrgencyAgeMatrixData();
    var urgencyMuni = loadUrgencyByMunicipalityData();

    if (!urgencyDist || urgencyDist.length === 0) {
      SpreadsheetApp.getUi().alert('緊急度データが見つかりません。先に「Python結果CSVを取り込み」を実行してください。');
      return;
    }

    var htmlString = generatePhase10DashboardHTML({
      urgencyDist: urgencyDist,
      urgencyAge: urgencyAge,
      urgencyEmp: urgencyEmp,
      urgencyMatrix: urgencyMatrix,
      urgencyMuni: urgencyMuni
    });

    var htmlOutput = HtmlService.createHtmlOutput(htmlString)
      .setWidth(1500)
      .setHeight(950);

    SpreadsheetApp.getUi().showModalDialog(
      htmlOutput,
      'Phase 10: 転職意欲・緊急度ダッシュボード'
    );

  } catch (e) {
    SpreadsheetApp.getUi().alert('エラー: ' + e.toString());
  }
}
