/**
 * GAS 包括的E2Eテスト（全フェーズ対応）
 * Phase 1, 2, 3, 7 のCSVファイルを読み込んで徹底的に検証
 */

const gasLogic = require('./gas_logic');
const path = require('path');
const fs = require('fs');

// テスト結果を格納
const testResults = {
  totalTests: 0,
  passed: 0,
  failed: 0,
  tests: []
};

/**
 * テストケースを実行
 * @param {string} name - テスト名
 * @param {Function} fn - テスト関数
 */
function test(name, fn) {
  testResults.totalTests++;

  try {
    fn();
    testResults.passed++;
    testResults.tests.push({
      name: name,
      status: 'PASSED',
      error: null
    });
    console.log(`✅ ${name}`);
  } catch (error) {
    testResults.failed++;
    testResults.tests.push({
      name: name,
      status: 'FAILED',
      error: error.message
    });
    console.log(`❌ ${name}`);
    console.log(`   エラー: ${error.message}`);
  }
}

/**
 * アサーション: 値が真であることを確認
 */
function assertTrue(condition, message) {
  if (!condition) {
    throw new Error(message || 'Assertion failed: expected true');
  }
}

/**
 * アサーション: 値が等しいことを確認
 */
function assertEqual(actual, expected, message) {
  if (actual !== expected) {
    throw new Error(message || `Assertion failed: expected ${expected}, got ${actual}`);
  }
}

/**
 * アサーション: 値が指定範囲内であることを確認
 */
function assertInRange(value, min, max, message) {
  if (value < min || value > max) {
    throw new Error(message || `Assertion failed: ${value} is not in range [${min}, ${max}]`);
  }
}

console.log('='.repeat(80));
console.log('GAS 包括的E2Eテスト - 全フェーズ検証');
console.log('='.repeat(80));
console.log();

// 基本ディレクトリ
const baseDir = path.join(__dirname, '..', 'python_scripts');

// =========================================
// Phase 1: 基礎集計
// =========================================
console.log('【Phase 1: 基礎集計】');
const phase1Dir = path.join(baseDir, 'gas_output_phase1');

test('Phase 1: フォルダ存在確認', () => {
  assertTrue(fs.existsSync(phase1Dir), 'Phase 1フォルダが存在するべき');
});

test('Phase 1: MapMetrics.csv 存在確認', () => {
  const testCSV = path.join(phase1Dir, 'MapMetrics.csv');
  assertTrue(fs.existsSync(testCSV), 'MapMetrics.csvが存在するべき');
});

let mapMetricsData = null;
test('Phase 1: MapMetrics.csv データ読み込み', () => {
  const testCSV = path.join(phase1Dir, 'MapMetrics.csv');
  mapMetricsData = gasLogic.readCSV(testCSV);
  assertTrue(mapMetricsData.length > 0, 'データが空でないべき');
});

test('Phase 1: MapMetrics.csv 行数確認', () => {
  assertTrue(mapMetricsData.length >= 600, `行数が600以上であるべき (実際: ${mapMetricsData.length})`);
  assertTrue(mapMetricsData.length <= 700, `行数が700以下であるべき (実際: ${mapMetricsData.length})`);
});

test('Phase 1: MapMetrics.csv データ検証', () => {
  const result = gasLogic.validateMapMetrics(mapMetricsData);
  assertTrue(result.valid, 'データが有効であるべき');
});

console.log();

// =========================================
// Phase 2: 統計検定
// =========================================
console.log('【Phase 2: 統計検定】');
const phase2Dir = path.join(baseDir, 'gas_output_phase2');

test('Phase 2: フォルダ存在確認', () => {
  assertTrue(fs.existsSync(phase2Dir), 'Phase 2フォルダが存在するべき');
});

let chiSquareData = null;
let anovaData = null;

test('Phase 2: ChiSquareTests.csv データ読み込み', () => {
  const testCSV = path.join(phase2Dir, 'ChiSquareTests.csv');
  assertTrue(fs.existsSync(testCSV), 'ChiSquareTests.csvが存在するべき');
  chiSquareData = gasLogic.readCSV(testCSV);
  assertTrue(chiSquareData.length > 0, 'カイ二乗検定データが空でないべき');
});

test('Phase 2: ANOVATests.csv データ読み込み', () => {
  const testCSV = path.join(phase2Dir, 'ANOVATests.csv');
  assertTrue(fs.existsSync(testCSV), 'ANOVATests.csvが存在するべき');
  anovaData = gasLogic.readCSV(testCSV);
  assertTrue(anovaData.length > 0, 'ANOVAデータが空でないべき');
});

test('Phase 2: 統計検定データ検証', () => {
  const result = gasLogic.validatePhase2(chiSquareData, anovaData);
  assertTrue(result.valid, '統計検定データが有効であるべき');
  assertTrue(result.statistics.totalTests > 0, '検定結果が存在するべき');
});

test('Phase 2: カイ二乗検定結果確認', () => {
  assertTrue(chiSquareData.length >= 1, 'カイ二乗検定が少なくとも1件実行されているべき');
  const firstTest = chiSquareData[0];
  assertTrue('p_value' in firstTest, 'p値が含まれるべき');
});

test('Phase 2: ANOVA検定結果確認', () => {
  assertTrue(anovaData.length >= 1, 'ANOVA検定が少なくとも1件実行されているべき');
  const firstTest = anovaData[0];
  assertTrue('f_statistic' in firstTest, 'F統計量が含まれるべき');
});

console.log();

// =========================================
// Phase 3: ペルソナ分析
// =========================================
console.log('【Phase 3: ペルソナ分析】');
const phase3Dir = path.join(baseDir, 'gas_output_phase3');

test('Phase 3: フォルダ存在確認', () => {
  assertTrue(fs.existsSync(phase3Dir), 'Phase 3フォルダが存在するべき');
});

let personaSummaryData = null;
let personaDetailsData = null;

test('Phase 3: PersonaSummary.csv データ読み込み', () => {
  const testCSV = path.join(phase3Dir, 'PersonaSummary.csv');
  assertTrue(fs.existsSync(testCSV), 'PersonaSummary.csvが存在するべき');
  personaSummaryData = gasLogic.readCSV(testCSV);
  assertTrue(personaSummaryData.length > 0, 'ペルソナサマリーデータが空でないべき');
});

test('Phase 3: PersonaDetails.csv データ読み込み', () => {
  const testCSV = path.join(phase3Dir, 'PersonaDetails.csv');
  assertTrue(fs.existsSync(testCSV), 'PersonaDetails.csvが存在するべき');
  personaDetailsData = gasLogic.readCSV(testCSV);
  assertTrue(personaDetailsData.length > 0, 'ペルソナ詳細データが空でないべき');
});

test('Phase 3: ペルソナデータ検証', () => {
  const result = gasLogic.validatePhase3(personaSummaryData, personaDetailsData);
  assertTrue(result.valid, 'ペルソナデータが有効であるべき');
  assertTrue(result.statistics.totalPersonas > 0, 'ペルソナが存在するべき');
});

test('Phase 3: ペルソナ数確認', () => {
  assertTrue(personaSummaryData.length >= 3, 'ペルソナが少なくとも3つ存在するべき');
  assertTrue(personaSummaryData.length <= 20, 'ペルソナが多すぎないべき（<=20）');
});

test('Phase 3: ペルソナ構成比確認', () => {
  let totalPercentage = 0;
  personaSummaryData.forEach(row => {
    const percentage = parseFloat(row['percentage']);
    if (!isNaN(percentage)) {
      totalPercentage += percentage;
    }
  });
  assertInRange(totalPercentage, 95, 105, `構成比合計が約100%であるべき (実際: ${totalPercentage.toFixed(2)}%)`);
});

console.log();

// =========================================
// Phase 7: 拡張分析
// =========================================
console.log('【Phase 7: 拡張分析】');
const phase7Dir = path.join(baseDir, 'gas_output_phase7');

test('Phase 7: フォルダ存在確認', () => {
  assertTrue(fs.existsSync(phase7Dir), 'Phase 7フォルダが存在するべき');
});

let ageGenderData = null;
let mobilityData = null;
let supplyDensityData = null;
let personaProfileData = null;

test('Phase 7: AgeGenderCrossAnalysis.csv データ読み込み', () => {
  const testCSV = path.join(phase7Dir, 'AgeGenderCrossAnalysis.csv');
  assertTrue(fs.existsSync(testCSV), 'AgeGenderCrossAnalysis.csvが存在するべき');
  ageGenderData = gasLogic.readCSV(testCSV);
  assertTrue(ageGenderData.length > 0, '年齢×性別クロス分析データが空でないべき');
});

test('Phase 7: MobilityScore.csv データ読み込み', () => {
  const testCSV = path.join(phase7Dir, 'MobilityScore.csv');
  assertTrue(fs.existsSync(testCSV), 'MobilityScore.csvが存在するべき');
  mobilityData = gasLogic.readCSV(testCSV);
  assertTrue(mobilityData.length > 0, 'モビリティスコアデータが空でないべき');
});

test('Phase 7: SupplyDensityMap.csv データ読み込み', () => {
  const testCSV = path.join(phase7Dir, 'SupplyDensityMap.csv');
  assertTrue(fs.existsSync(testCSV), 'SupplyDensityMap.csvが存在するべき');
  supplyDensityData = gasLogic.readCSV(testCSV);
  assertTrue(supplyDensityData.length > 0, '供給密度データが空でないべき');
});

test('Phase 7: DetailedPersonaProfile.csv データ読み込み', () => {
  const testCSV = path.join(phase7Dir, 'DetailedPersonaProfile.csv');
  assertTrue(fs.existsSync(testCSV), 'DetailedPersonaProfile.csvが存在するべき');
  personaProfileData = gasLogic.readCSV(testCSV);
  assertTrue(personaProfileData.length > 0, '詳細ペルソナプロファイルデータが空でないべき');
});

test('Phase 7: 拡張分析データ検証', () => {
  const result = gasLogic.validatePhase7(ageGenderData, mobilityData, supplyDensityData, personaProfileData);
  // Phase 7は警告のみで失敗しない（オプショナル）
  assertTrue(result.statistics.ageGenderRecords > 0 || result.statistics.mobilityRecords > 0, '少なくとも1つのデータセットが存在するべき');
});

console.log();

// =========================================
// テスト結果サマリー
// =========================================
console.log('='.repeat(80));
console.log('テスト結果サマリー');
console.log('='.repeat(80));
console.log(`総テスト数: ${testResults.totalTests}`);
console.log(`成功: ${testResults.passed} ✅`);
console.log(`失敗: ${testResults.failed} ❌`);
console.log(`成功率: ${(testResults.passed / testResults.totalTests * 100).toFixed(2)}%`);
console.log();

if (testResults.failed > 0) {
  console.log('失敗したテスト:');
  testResults.tests.filter(t => t.status === 'FAILED').forEach(t => {
    console.log(`  ❌ ${t.name}`);
    console.log(`     ${t.error}`);
  });
  console.log();
}

// 統計情報の表示
console.log('='.repeat(80));
console.log('全フェーズ統計サマリー');
console.log('='.repeat(80));

if (mapMetricsData) {
  console.log('\n【Phase 1: 基礎集計】');
  const result = gasLogic.validateMapMetrics(mapMetricsData);
  console.log(`  総地点数: ${result.statistics.totalRows}`);
  console.log(`  有効座標: ${result.statistics.validCoords} (${(result.statistics.validCoords / result.statistics.totalRows * 100).toFixed(2)}%)`);
  console.log(`  カウント合計: ${result.statistics.totalCount.toLocaleString()}`);
}

if (chiSquareData && anovaData) {
  console.log('\n【Phase 2: 統計検定】');
  const result = gasLogic.validatePhase2(chiSquareData, anovaData);
  console.log(`  カイ二乗検定: ${result.statistics.chiSquareTests}件`);
  console.log(`  ANOVA検定: ${result.statistics.anovaTests}件`);
  console.log(`  総検定数: ${result.statistics.totalTests}件`);
}

if (personaSummaryData && personaDetailsData) {
  console.log('\n【Phase 3: ペルソナ分析】');
  const result = gasLogic.validatePhase3(personaSummaryData, personaDetailsData);
  console.log(`  ペルソナ数: ${result.statistics.totalPersonas}`);
  console.log(`  総求職者数: ${result.statistics.totalApplicants.toLocaleString()}`);
  console.log(`  平均求職者数/ペルソナ: ${result.statistics.avgApplicantsPerPersona}`);
  console.log(`  詳細レコード数: ${result.statistics.detailRecords}`);
}

if (ageGenderData || mobilityData || supplyDensityData || personaProfileData) {
  console.log('\n【Phase 7: 拡張分析】');
  const result = gasLogic.validatePhase7(ageGenderData, mobilityData, supplyDensityData, personaProfileData);
  console.log(`  年齢×性別クロス分析: ${result.statistics.ageGenderRecords}件`);
  console.log(`  モビリティスコア: ${result.statistics.mobilityRecords}件`);
  console.log(`  供給密度マップ: ${result.statistics.supplyDensityRecords}件`);
  console.log(`  詳細ペルソナプロファイル: ${result.statistics.personaProfileRecords}件`);
}

console.log();
console.log('='.repeat(80));
if (testResults.failed === 0) {
  console.log('✅ すべてのテストが成功しました！');
  console.log('='.repeat(80));
  process.exit(0);
} else {
  console.log(`❌ ${testResults.failed}個のテストが失敗しました`);
  console.log('='.repeat(80));
  process.exit(1);
}
