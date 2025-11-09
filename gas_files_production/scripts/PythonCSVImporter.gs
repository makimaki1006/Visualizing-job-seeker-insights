/**
 * Python出力CSVファイルをGoogle Sheetsに取り込む
 * 同じスプレッドシートのフォルダ内のCSVファイルを自動検出
 */

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
      {name: 'P1_QualityReport.csv', sheetName: 'P1_QualityReport', required: false, phase: 1, subfolder: 'phase1'},
      {name: 'QualityReport_Descriptive.csv', sheetName: 'P1_QualityDesc', required: false, phase: 1, subfolder: 'phase1'},

      // Phase 2: 統計的検定結果
      {name: 'ChiSquareTests.csv', sheetName: 'ChiSquareTests', required: false, phase: 2, subfolder: 'phase2'},
      {name: 'ANOVATests.csv', sheetName: 'ANOVATests', required: false, phase: 2, subfolder: 'phase2'},
      {name: 'P2_QualityReport_Inferential.csv', sheetName: 'P2_QualityInfer', required: false, phase: 2, subfolder: 'phase2'},

      // Phase 3: ペルソナ分析結果
      {name: 'PersonaSummary.csv', sheetName: 'PersonaSummary', required: false, phase: 3, subfolder: 'phase3'},
      {name: 'PersonaDetails.csv', sheetName: 'PersonaDetails', required: false, phase: 3, subfolder: 'phase3'},
      {name: 'P3_QualityReport_Inferential.csv', sheetName: 'P3_QualityInfer', required: false, phase: 3, subfolder: 'phase3'},

      // Phase 6: フロー・近接分析
      {name: 'MunicipalityFlowEdges.csv', sheetName: 'Phase6_MunicipalityFlowEdges', required: false, phase: 6, subfolder: 'phase6'},
      {name: 'MunicipalityFlowNodes.csv', sheetName: 'Phase6_MunicipalityFlowNodes', required: false, phase: 6, subfolder: 'phase6'},
      {name: 'ProximityAnalysis.csv', sheetName: 'ProximityAnalysis', required: false, phase: 6, subfolder: 'phase6'},
      {name: 'P6_QualityReport_Inferential.csv', sheetName: 'P6_QualityInfer', required: false, phase: 6, subfolder: 'phase6'},

      // Phase 7: 高度分析
      {name: 'SupplyDensityMap.csv', sheetName: 'Phase7_SupplyDensity', required: false, phase: 7, subfolder: 'phase7'},
      {name: 'QualificationDistribution.csv', sheetName: 'Phase7_QualificationDist', required: false, phase: 7, subfolder: 'phase7'},
      {name: 'AgeGenderCrossAnalysis.csv', sheetName: 'Phase7_AgeGenderCross', required: false, phase: 7, subfolder: 'phase7'},
      {name: 'MobilityScore.csv', sheetName: 'Phase7_MobilityScore', required: false, phase: 7, subfolder: 'phase7'},
      {name: 'DetailedPersonaProfile.csv', sheetName: 'Phase7_PersonaProfile', required: false, phase: 7, subfolder: 'phase7'},
      {name: 'P7_QualityReport_Inferential.csv', sheetName: 'P7_QualityInfer', required: false, phase: 7, subfolder: 'phase7'},

      // Phase 8: キャリア・学歴分析【v2.3: career列使用版】
      {name: 'CareerDistribution.csv', sheetName: 'P8_CareerDist', required: false, phase: 8, subfolder: 'phase8'},  // 🔄 v2.3
      {name: 'CareerAgeCross.csv', sheetName: 'P8_CareerAgeCross', required: false, phase: 8, subfolder: 'phase8'},  // 🔄 v2.3
      {name: 'CareerAgeCross_Matrix.csv', sheetName: 'P8_CareerAgeMatrix', required: false, phase: 8, subfolder: 'phase8'},  // 🔄 v2.3
      {name: 'GraduationYearDistribution.csv', sheetName: 'P8_GradYearDist', required: false, phase: 8, subfolder: 'phase8'},
      {name: 'P8_QualityReport.csv', sheetName: 'P8_QualityReport', required: false, phase: 8, subfolder: 'phase8'},
      {name: 'P8_QualityReport_Inferential.csv', sheetName: 'P8_QualityInfer', required: false, phase: 8, subfolder: 'phase8'},

      // Phase 10: 転職意欲・緊急度分析
      {name: 'UrgencyDistribution.csv', sheetName: 'P10_UrgencyDist', required: false, phase: 10, subfolder: 'phase10'},
      {name: 'UrgencyDistribution_ByMunicipality.csv', sheetName: 'P10_UrgencyDist_Muni', required: false, phase: 10, subfolder: 'phase10'},
      {name: 'UrgencyAgeCross.csv', sheetName: 'P10_UrgencyAge', required: false, phase: 10, subfolder: 'phase10'},
      {name: 'UrgencyAgeCross_ByMunicipality.csv', sheetName: 'P10_UrgencyAge_Muni', required: false, phase: 10, subfolder: 'phase10'},
      {name: 'UrgencyAgeCross_Matrix.csv', sheetName: 'P10_UrgencyAgeMatrix', required: false, phase: 10, subfolder: 'phase10'},
      {name: 'UrgencyEmploymentCross.csv', sheetName: 'P10_UrgencyEmp', required: false, phase: 10, subfolder: 'phase10'},
      {name: 'UrgencyEmploymentCross_Matrix.csv', sheetName: 'P10_UrgencyEmpMatrix', required: false, phase: 10, subfolder: 'phase10'},
      {name: 'UrgencyEmploymentCross_ByMunicipality.csv', sheetName: 'P10_UrgencyEmp_Muni', required: false, phase: 10, subfolder: 'phase10'},
      {name: 'UrgencyDesiredWorkCross.csv', sheetName: 'P10_UrgencyDesired', required: false, phase: 10, subfolder: 'phase10'},
      {name: 'P10_QualityReport.csv', sheetName: 'P10_QualityReport', required: false, phase: 10, subfolder: 'phase10'},
      {name: 'P10_QualityReport_Inferential.csv', sheetName: 'P10_QualityInfer', required: false, phase: 10, subfolder: 'phase10'},

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
// ===== HTMLアップロードからの単一CSVインポート =====
function importSingleCSVFromHTML(fileName, sheetName, csvContent) {
  /**
   * Upload_Bulk37.htmlからアップロードされたCSVファイルを処理
   *
   * @param {string} fileName - ファイル名（検証用）
   * @param {string} sheetName - シート名（例: P1_Applicants）
   * @param {string} csvContent - CSVファイルの内容（文字列）
   * @return {Object} - 処理結果 {success: boolean, fileName: string, sheetName: string, rows: number}
   */

  try {
    var ss = SpreadsheetApp.getActiveSpreadsheet();

    // BOMを除去
    if (csvContent.charCodeAt(0) === 0xFEFF) {
      csvContent = csvContent.substring(1);
    }

    // CSVパース
    var data = Utilities.parseCsv(csvContent);

    if (data.length === 0) {
      throw new Error('空のCSVファイル: ' + fileName);
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

    // Auto-resize columns
    for (var i = 1; i <= data[0].length; i++) {
      sheet.autoResizeColumn(i);
    }

    console.log('[HTML Upload] ' + sheetName + ': ' + (data.length - 1) + ' rows imported');

    return {
      success: true,
      fileName: fileName,
      sheetName: sheetName,
      rows: data.length - 1
    };

  } catch (e) {
    console.error('[HTMLアップロードエラー] ' + fileName + ': ' + e.toString());
    return {
      success: false,
      fileName: fileName,
      sheetName: sheetName,
      error: e.toString()
    };
  }
}
