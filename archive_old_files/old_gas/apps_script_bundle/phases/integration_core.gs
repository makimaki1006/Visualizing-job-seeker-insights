// ===== Integration: MenuIntegration =====
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
    .addItem('🗺️ 地図表示（バブル）', 'showBubbleMap')
    .addItem('📍 地図表示（ヒートマップ）', 'showHeatMap')
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
      // .addItem('🏘️ 移動パターン分析', 'showProximityAnalysis') // 未実装
      // .addSeparator()
      // .addItem('🎯 フロー・移動統合ビュー', 'showFlowProximityDashboard') // 未実装
      )
    .addSeparator()
    // Phase 8: キャリア・学歴分析（NEW）
    .addSubMenu(ui.createMenu('🎓 Phase 8: 学歴分析')
      .addItem('📊 学歴分布グラフ', 'showPhase8EducationDistribution')
      .addItem('🔥 学歴×年齢ヒートマップ', 'showPhase8EducationAgeMatrixHeatmap')
      .addSeparator()
      .addItem('🎯 統合ダッシュボード', 'showPhase8Dashboard'))
    .addSeparator()
    // Phase 10: 転職意欲・緊急度分析（NEW）
    .addSubMenu(ui.createMenu('🚀 Phase 10: 緊急度分析')
      .addItem('📊 緊急度分布グラフ', 'showPhase10UrgencyDistribution')
      .addItem('🔥 緊急度×年齢ヒートマップ', 'showPhase10UrgencyAgeMatrixHeatmap')
      .addItem('🔥 緊急度×就業状態ヒートマップ', 'showPhase10UrgencyEmploymentMatrixHeatmap')
      .addSeparator()
      .addItem('🎯 統合ダッシュボード', 'showPhase10Dashboard'))
    .addSeparator()
    // 品質管理（NEW）
    .addSubMenu(ui.createMenu('✅ 品質管理')
      .addItem('📊 品質ダッシュボード', 'showQualityDashboard')
      .addItem('✅ データ検証レポート', 'showValidationReport')
      .addSeparator()
      .addItem('🔍 Phase品質比較', 'showPhaseQualityComparison'))
    .addSeparator()
    // データ管理
    // .addItem('🔍 データ確認', 'checkMapData') // 未実装
    // .addItem('📊 統計サマリー', 'showStatsSummary') // 未実装
    // .addItem('🧹 全データクリア', 'clearAllData') // 未実装
    // .addSeparator()
    // デバッグ
    // .addItem('🐛 デバッグログ', 'showDebugLog') // 未実装
    // .addItem('🔧 カラム分析', 'analyzeDesiredColumns') // 未実装

    .addToUi();
}

// ===== 高速CSVインポートダイアログ（新） =====
function showEnhancedUploadDialog() {
  var html = HtmlService.createHtmlOutputFromFile('Upload_Bulk37')
    .setWidth(900)
    .setHeight(700);
  SpreadsheetApp.getUi().showModalDialog(html, '⚡ 高速CSVインポート（37ファイル一括対応）');
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

// ===== Integration: PythonCSVImporter =====
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

// ===== Integration: QualityDashboard =====
/**
 * データ品質ダッシュボード
 * 全Phaseの品質レポートを統合表示
 */

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

  // Phase別品質レポート
  var phaseSheets = [
    {name: 'P1_QualityReport', phase: 1, label: 'Phase 1: 基礎集計（観察的記述）'},
    {name: 'P1_QualityDesc', phase: 1, label: 'Phase 1: 基礎集計（詳細）'},
    {name: 'P2_QualityInfer', phase: 2, label: 'Phase 2: 統計分析'},
    {name: 'P3_QualityInfer', phase: 3, label: 'Phase 3: ペルソナ分析'},
    {name: 'P6_QualityInfer', phase: 6, label: 'Phase 6: フロー分析'},
    {name: 'P7_QualityInfer', phase: 7, label: 'Phase 7: 高度分析'},
    {name: 'P8_QualityReport', phase: 8, label: 'Phase 8: 学歴分析（観察的記述）'},
    {name: 'P8_QualityInfer', phase: 8, label: 'Phase 8: 学歴分析（推論的考察）'},
    {name: 'P10_QualityReport', phase: 10, label: 'Phase 10: 緊急度分析（観察的記述）'},
    {name: 'P10_QualityInfer', phase: 10, label: 'Phase 10: 緊急度分析（推論的考察）'}
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
  html.append('<style>');
  html.append('body { font-family: Arial, sans-serif; margin: 0; padding: 0; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }');
  html.append('.container { padding: 20px; }');
  html.append('.header { background: white; border-radius: 12px; padding: 30px; margin-bottom: 20px; box-shadow: 0 10px 40px rgba(0,0,0,0.1); }');
  html.append('h1 { color: #667eea; margin: 0; display: flex; align-items: center; }');
  html.append('h1 .icon { font-size: 40px; margin-right: 15px; }');
  html.append('.stats-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-top: 20px; }');
  html.append('.stat-card { background: #f8f9fa; border-radius: 8px; padding: 20px; text-align: center; }');
  html.append('.stat-value { font-size: 32px; font-weight: bold; color: #667eea; }');
  html.append('.stat-label { font-size: 13px; color: #666; margin-top: 8px; }');
  html.append('.phase-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; }');
  html.append('.phase-card { background: white; border-radius: 12px; padding: 20px; box-shadow: 0 5px 20px rgba(0,0,0,0.1); }');
  html.append('.phase-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; }');
  html.append('.phase-title { font-size: 18px; font-weight: bold; color: #333; }');
  html.append('.quality-badge { display: inline-block; padding: 5px 15px; border-radius: 20px; font-size: 12px; font-weight: bold; }');
  html.append('.quality-excellent { background: #10b981; color: white; }');
  html.append('.quality-good { background: #3b82f6; color: white; }');
  html.append('.quality-acceptable { background: #f59e0b; color: white; }');
  html.append('.quality-poor { background: #ef4444; color: white; }');
  html.append('.quality-no-data { background: #6b7280; color: white; }');
  html.append('.progress-bar { width: 100%; height: 8px; background: #e5e7eb; border-radius: 4px; overflow: hidden; margin: 10px 0; }');
  html.append('.progress-fill { height: 100%; background: #667eea; transition: width 0.3s; }');
  html.append('.column-table { width: 100%; border-collapse: collapse; margin-top: 15px; font-size: 12px; }');
  html.append('.column-table th { background: #f8f9fa; padding: 8px; text-align: left; border-bottom: 2px solid #ddd; }');
  html.append('.column-table td { padding: 6px 8px; border-bottom: 1px solid #eee; }');
  html.append('.reliability-high { color: #10b981; font-weight: bold; }');
  html.append('.reliability-medium { color: #3b82f6; font-weight: bold; }');
  html.append('.reliability-low { color: #f59e0b; font-weight: bold; }');
  html.append('.reliability-critical { color: #ef4444; font-weight: bold; }');
  html.append('.reliability-descriptive { color: #6b7280; font-weight: bold; }');
  html.append('.chart-container { margin: 20px 0; height: 300px; }');
  html.append('</style>');

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
