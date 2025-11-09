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