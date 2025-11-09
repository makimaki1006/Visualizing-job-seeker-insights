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
    // Phase 12-14: 統合分析ダッシュボード（クロス分析機能含む）
    .addSubMenu(ui.createMenu('🎯 Phase 12-14: 統合分析ダッシュボード')
      .addItem('📊 統合ダッシュボード（クロス分析機能含む）', 'showMapPhase12to14')
      .addSeparator()
      .addSubMenu(ui.createMenu('📊 個別分析')
        .addItem('⚖️ Phase 12: 需給バランス分析', 'showPhase12SupplyDemandGap')
        .addItem('💎 Phase 13: 希少人材分析', 'showPhase13RarityScore')
        .addItem('👤 Phase 14: 人材プロファイル分析', 'showPhase14CompetitionProfile'))
      .addSeparator()
      .addItem('📥 Phase 12-14データをインポート', 'importPhase12to14Data')
      .addItem('✅ Phase 12-14データ検証', 'testPhase12to14Load'))
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
    // キャッシュ管理（30秒制限対策）⏰ NEW
    .addSubMenu(ui.createMenu('⏰ キャッシュ管理')
      .addItem('🔄 今すぐキャッシュ生成（全47都道府県）', 'warmUpMapCompleteCache')
      .addItem('⏰ 自動更新トリガー設定（単一バッチ）', 'setupDailyWarmUpTrigger')
      .addItem('📊 最終実行結果を確認', 'checkLastWarmUpResult')
      .addSeparator()
      .addItem('🌐 3バッチトリガー設定（全国データ用）✨', 'setupDailyWarmUpTrigger_3Batches')
      .addItem('📈 全バッチ実行結果を確認', 'checkAllBatchResults')
      .addItem('🗑️ 全バッチトリガー削除', 'removeAllBatchTriggers')
      .addSeparator()
      .addItem('📊 キャッシュ状態を確認', 'checkCacheStatus')
      .addItem('🧹 古いキャッシュを削除（24時間以上）', 'clearOldCache')
      .addItem('⚠️ 全キャッシュ削除（緊急用）', 'clearAllCache'))
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

// ===== Phase 12-14: 統合分析ダッシュボード =====

/**
 * Phase 12-14統合ダッシュボード表示
 */
function showMapPhase12to14() {
  var html = HtmlService.createHtmlOutputFromFile('map_complete_integrated')
    .setWidth(1200)
    .setHeight(800);
  SpreadsheetApp.getUi().showModalDialog(html, '📊 Phase 12-14統合ダッシュボード');
}

/**
 * Phase 12: 需給バランス分析
 */
function showPhase12SupplyDemandGap() {
  var data = loadPhase12to14Data();

  var html = HtmlService.createHtmlOutput(`
    <!DOCTYPE html>
    <html>
    <head>
      <style>
        body { font-family: Arial, sans-serif; padding: 20px; }
        h2 { color: #667eea; }
        .summary { background: #f7fafc; padding: 15px; border-radius: 8px; margin: 20px 0; }
        .summary-item { margin: 10px 0; }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        th, td { padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background: #667eea; color: white; }
        tr:hover { background: #f7fafc; }
      </style>
    </head>
    <body>
      <h2>⚖️ Phase 12: 需給バランス分析</h2>

      <div class="summary">
        <h3>📊 サマリー</h3>
        <div class="summary-item">総需要数: ${data.gap.summary.total_demand || 0}件</div>
        <div class="summary-item">総供給数: ${data.gap.summary.total_supply || 0}件</div>
        <div class="summary-item">平均需給比率: ${(data.gap.summary.avg_ratio || 0).toFixed(2)}</div>
      </div>

      <h3>🔝 需給ギャップTOP10</h3>
      <table>
        <thead>
          <tr>
            <th>市区町村</th>
            <th>需要数</th>
            <th>供給数</th>
            <th>ギャップ</th>
            <th>需給比率</th>
          </tr>
        </thead>
        <tbody>
          ${data.gap.top_gaps.map(row => `
            <tr>
              <td>${row.location}</td>
              <td>${row.demand_count}</td>
              <td>${row.supply_count}</td>
              <td>${row.gap}</td>
              <td>${row.demand_supply_ratio.toFixed(2)}</td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    </body>
    </html>
  `)
  .setWidth(900)
  .setHeight(700);

  SpreadsheetApp.getUi().showModalDialog(html, '⚖️ Phase 12: 需給バランス分析');
}

/**
 * Phase 13: 希少人材分析
 */
function showPhase13RarityScore() {
  var data = loadPhase12to14Data();

  var html = HtmlService.createHtmlOutput(`
    <!DOCTYPE html>
    <html>
    <head>
      <style>
        body { font-family: Arial, sans-serif; padding: 20px; }
        h2 { color: #667eea; }
        .summary { background: #f7fafc; padding: 15px; border-radius: 8px; margin: 20px 0; }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        th, td { padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background: #667eea; color: white; }
        tr:hover { background: #f7fafc; }
        .rarity-high { color: #e53e3e; font-weight: bold; }
        .rarity-medium { color: #dd6b20; }
        .rarity-low { color: #38a169; }
      </style>
    </head>
    <body>
      <h2>💎 Phase 13: 希少人材分析</h2>

      <div class="summary">
        <h3>📊 サマリー</h3>
        <div>平均レアリティスコア: ${(data.rarity.summary.avg_rarity || 0).toFixed(2)}</div>
      </div>

      <h3>🔝 希少人材TOP10</h3>
      <table>
        <thead>
          <tr>
            <th>市区町村</th>
            <th>資格名</th>
            <th>レアリティスコア</th>
            <th>希少度ランク</th>
          </tr>
        </thead>
        <tbody>
          ${data.rarity.top_rare.map(row => `
            <tr>
              <td>${row.location}</td>
              <td>${row.qualification_name}</td>
              <td class="rarity-${row.rarity_rank}">${row.rarity_score.toFixed(2)}</td>
              <td>${row.rarity_rank}</td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    </body>
    </html>
  `)
  .setWidth(900)
  .setHeight(700);

  SpreadsheetApp.getUi().showModalDialog(html, '💎 Phase 13: 希少人材分析');
}

/**
 * Phase 14: 人材プロファイル分析
 */
function showPhase14CompetitionProfile() {
  var data = loadPhase12to14Data();

  var html = HtmlService.createHtmlOutput(`
    <!DOCTYPE html>
    <html>
    <head>
      <style>
        body { font-family: Arial, sans-serif; padding: 20px; }
        h2 { color: #667eea; }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        th, td { padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background: #667eea; color: white; }
        tr:hover { background: #f7fafc; }
      </style>
    </head>
    <body>
      <h2>👤 Phase 14: 人材プロファイル分析</h2>

      <h3>🔝 高競合地域TOP10</h3>
      <table>
        <thead>
          <tr>
            <th>市区町村</th>
            <th>競合スコア</th>
            <th>求職者数</th>
            <th>需要数</th>
          </tr>
        </thead>
        <tbody>
          ${data.competition.top_competition.map(row => `
            <tr>
              <td>${row.location}</td>
              <td>${row.competition_score.toFixed(2)}</td>
              <td>${row.applicant_count}</td>
              <td>${row.demand_count}</td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    </body>
    </html>
  `)
  .setWidth(900)
  .setHeight(700);

  SpreadsheetApp.getUi().showModalDialog(html, '👤 Phase 14: 人材プロファイル分析');
}

/**
 * Phase 12-14データインポート
 */
function importPhase12to14Data() {
  SpreadsheetApp.getUi().alert(
    '📥 データインポート',
    'メニュー「データ処理 → データインポート → CSVファイルを個別アップロード」から\n' +
    '以下のファイルをアップロードしてください:\n\n' +
    '• Phase12_SupplyDemandGap.csv\n' +
    '• Phase13_RarityScore.csv\n' +
    '• Phase14_CompetitionProfile.csv',
    SpreadsheetApp.getUi().ButtonSet.OK
  );
}

/**
 * Phase 12-14データ検証
 */
function testPhase12to14Load() {
  try {
    var data = loadPhase12to14Data();

    var message = '✅ Phase 12-14データ検証結果:\n\n';
    message += 'Phase 12 (需給ギャップ): ' + (data.gap.top_gaps.length > 0 ? '✅ データあり' : '❌ データなし') + '\n';
    message += 'Phase 13 (希少人材): ' + (data.rarity.top_rare.length > 0 ? '✅ データあり' : '❌ データなし') + '\n';
    message += 'Phase 14 (人材プロファイル): ' + (data.competition.top_competition.length > 0 ? '✅ データあり' : '❌ データなし') + '\n';

    SpreadsheetApp.getUi().alert('✅ データ検証完了', message, SpreadsheetApp.getUi().ButtonSet.OK);
  } catch (e) {
    SpreadsheetApp.getUi().alert('❌ エラー', 'データ検証に失敗しました:\n' + e.toString(), SpreadsheetApp.getUi().ButtonSet.OK);
  }
}