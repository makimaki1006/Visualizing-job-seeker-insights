/**
 * 完全統合メニュー（最小限版）
 *
 * 既存のGAS関数のみを使用します。
 *
 * 作成日: 2025-10-27
 * バージョン: 3.0（最小限版）
 */

function onOpen() {
  const ui = SpreadsheetApp.getUi();
  let menu = ui.createMenu('📊 データ処理');

  // データインポート
  menu.addSubMenu(ui.createMenu('📥 データインポート')
    .addItem('📍 Phase 1: 基礎集計（4ファイル）', 'uploadPhase1')
    .addItem('📊 Phase 2: 統計分析（2ファイル）', 'uploadPhase2')
    .addItem('👥 Phase 3: ペルソナ分析（2ファイル）', 'uploadPhase3')
    .addItem('🌊 Phase 6: フロー分析（3ファイル）', 'uploadPhase6')
    .addItem('📈 Phase 7: 高度分析（7ファイル）', 'uploadPhase7')
    .addSeparator()
    .addItem('✅ 全Phaseアップロード状況', 'showAllPhasesUploadStatus')
  );

  menu.addSeparator();

  // Phase 7高度分析
  const phase7Menu = ui.createMenu('📈 Phase 7高度分析')
    .addSubMenu(ui.createMenu('📊 個別分析')
      .addItem('🗺️ 人材供給密度マップ', 'showSupplyDensityMap')
      .addItem('🎓 資格別人材分布', 'showQualificationDistribution')
      .addItem('👥 年齢層×性別クロス分析', 'showAgeGenderCrossAnalysis')
      .addItem('🚗 移動許容度スコアリング', 'showMobilityScoreAnalysis')
      .addItem('📊 ペルソナ詳細プロファイル', 'showDetailedPersonaProfile')
    )
    .addSeparator()
    .addSubMenu(ui.createMenu('🎯 統合ダッシュボード')
      .addItem('📊 Phase 7統合ダッシュボード', 'showPhase7CompleteDashboard')
      .addItem('🌐 完全統合ダッシュボード（全Phase）', 'showCompleteIntegratedDashboard')
    )
    .addSeparator()
    .addSubMenu(ui.createMenu('🔧 データ管理')
      .addItem('✅ データ検証', 'validatePhase7Data')
      .addItem('📊 データサマリー', 'showPhase7DataSummary')
      .addSeparator()
      .addItem('🧹 全データクリア', 'clearAllPhase7Data')
    )
    .addSeparator()
    .addItem('❓ Phase 7クイックスタート', 'showPhase7QuickStart');

  menu.addSubMenu(phase7Menu);
  menu.addSeparator();

  // 地図表示メニュー（Leaflet.js + OpenStreetMap）
  menu.addItem('🗺️ 地図表示（完全版）', 'showMapComplete');
  menu.addSeparator();

  // Phase 2/3 統計分析・ペルソナ
  menu.addSubMenu(ui.createMenu('📈 統計分析・ペルソナ')
    .addItem('🔬 カイ二乗検定結果', 'showChiSquareTests')
    .addItem('📊 ANOVA検定結果', 'showANOVATests')
    .addSeparator()
    .addItem('👥 ペルソナサマリー', 'showPersonaSummary')
    .addItem('📋 ペルソナ詳細', 'showPersonaDetails')
  );
  menu.addSeparator();

  // その他の分析
  menu.addItem('🌊 自治体間フロー分析', 'showMunicipalityFlowNetworkVisualization');
  menu.addItem('🗺️ ペルソナマップ可視化', 'showPersonaMapVisualization');
  menu.addItem('🎯 ペルソナ難易度確認', 'showPersonaDifficultyChecker');

  menu.addToUi();
}

// Phase別アップロード関数
function uploadPhase1() { showPhaseUploadDialog('phase1'); }
function uploadPhase2() { showPhaseUploadDialog('phase2'); }
function uploadPhase3() { showPhaseUploadDialog('phase3'); }
function uploadPhase6() { showPhaseUploadDialog('phase6'); }
function uploadPhase7() { showPhaseUploadDialog('phase7'); }

// クイックスタートガイド
function showPhase7QuickStart() {
  const ui = SpreadsheetApp.getUi();
  const message = `
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Phase 1-7 完全版クイックスタート
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

【ステップ1】Pythonでデータ生成 🐍
1. run_complete.py を実行
2. CSVファイルを選択
3. 全Phase出力確認（18ファイル）

【ステップ2】GASに一括アップロード 📤
メニュー: 📊 データ処理 > 📥 データインポート
各Phaseを選択してアップロード

【ステップ3】可視化 📊
完全統合ダッシュボードで全データを確認

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  `;
  ui.alert('クイックスタート', message, ui.ButtonSet.OK);
}
