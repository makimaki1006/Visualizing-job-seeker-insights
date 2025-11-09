/**
 * GAS E2Eテスト
 * Phase 1のCSVファイルを読み込んで徹底的に検証
 */

const gasLogic = require('./gas_logic');
const path = require('path');

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
console.log('GAS E2Eテスト - Phase 1 CSV検証');
console.log('='.repeat(80));
console.log();

// Phase 1ディレクトリのパス
const phase1Dir = path.join(__dirname, '..', 'python_scripts', 'gas_output_phase1');

// ユニットテスト: CSVパーサー
console.log('【ユニットテスト: CSVパーサー】');
test('CSVパーサー: 基本的なCSV読み込み', () => {
  const testCSV = path.join(phase1Dir, 'MapMetrics.csv');
  const data = gasLogic.readCSV(testCSV);
  assertTrue(data.length > 0, 'データが読み込まれるべき');
  assertTrue('都道府県' in data[0], '都道府県カラムが存在するべき');
});

test('CSVパーサー: 空ファイル処理', () => {
  // 空ファイルのシミュレーション（実際には存在しないファイルなので、エラーハンドリングテスト）
  try {
    const data = gasLogic.readCSV('/nonexistent/file.csv');
    assertTrue(false, '存在しないファイルはエラーを投げるべき');
  } catch (error) {
    assertTrue(true, 'エラーが正しく処理された');
  }
});

console.log();

// 統合テスト: MapMetrics.csv
console.log('【統合テスト: MapMetrics.csv】');
let mapMetricsData = null;
let mapMetricsResult = null;

test('MapMetrics: ファイル存在確認', () => {
  const testCSV = path.join(phase1Dir, 'MapMetrics.csv');
  const fs = require('fs');
  assertTrue(fs.existsSync(testCSV), 'MapMetrics.csvが存在するべき');
});

test('MapMetrics: データ読み込み', () => {
  const testCSV = path.join(phase1Dir, 'MapMetrics.csv');
  mapMetricsData = gasLogic.readCSV(testCSV);
  assertTrue(mapMetricsData.length > 0, 'データが空でないべき');
});

test('MapMetrics: 必須カラム存在確認', () => {
  const requiredColumns = ['都道府県', '市区町村', 'キー', 'カウント', '緯度', '経度'];
  requiredColumns.forEach(col => {
    assertTrue(col in mapMetricsData[0], `カラム '${col}' が存在するべき`);
  });
});

test('MapMetrics: データ検証', () => {
  mapMetricsResult = gasLogic.validateMapMetrics(mapMetricsData);
  assertTrue(mapMetricsResult.valid, 'データが有効であるべき');
});

test('MapMetrics: 行数確認', () => {
  // 修正前は0行だったが、修正後は642行
  assertTrue(mapMetricsData.length >= 600, `行数が600以上であるべき (実際: ${mapMetricsData.length})`);
  assertTrue(mapMetricsData.length <= 700, `行数が700以下であるべき (実際: ${mapMetricsData.length})`);
});

test('MapMetrics: 座標の妥当性', () => {
  const validCoords = mapMetricsResult.statistics.validCoords;
  const totalRows = mapMetricsResult.statistics.totalRows;
  assertTrue(validCoords / totalRows >= 0.9, `座標の90%以上が有効であるべき (実際: ${(validCoords / totalRows * 100).toFixed(2)}%)`);
});

test('MapMetrics: カウント合計確認', () => {
  const totalCount = mapMetricsResult.statistics.totalCount;
  assertTrue(totalCount > 20000, `カウント合計が20,000以上であるべき (実際: ${totalCount})`);
});

console.log();

// 統合テスト: Applicants.csv
console.log('【統合テスト: Applicants.csv】');
let applicantsData = null;
let applicantsResult = null;

test('Applicants: ファイル存在確認', () => {
  const testCSV = path.join(phase1Dir, 'Applicants.csv');
  const fs = require('fs');
  assertTrue(fs.existsSync(testCSV), 'Applicants.csvが存在するべき');
});

test('Applicants: データ読み込み', () => {
  const testCSV = path.join(phase1Dir, 'Applicants.csv');
  applicantsData = gasLogic.readCSV(testCSV);
  assertTrue(applicantsData.length > 0, 'データが空でないべき');
});

test('Applicants: 行数確認', () => {
  assertTrue(applicantsData.length === 7390, `行数が7,390であるべき (実際: ${applicantsData.length})`);
});

test('Applicants: データ検証', () => {
  applicantsResult = gasLogic.validateApplicants(applicantsData);
  assertTrue(applicantsResult.valid, 'データが有効であるべき');
});

test('Applicants: 性別分布確認', () => {
  const genderDist = applicantsResult.statistics.genderDistribution;
  const total = genderDist['男性'] + genderDist['女性'] + genderDist[''];
  assertTrue(total === applicantsData.length, '性別分布の合計が総行数と一致するべき');
});

console.log();

// 統合テスト: DesiredWork.csv
console.log('【統合テスト: DesiredWork.csv】');
let desiredWorkData = null;
let desiredWorkResult = null;

test('DesiredWork: ファイル存在確認', () => {
  const testCSV = path.join(phase1Dir, 'DesiredWork.csv');
  const fs = require('fs');
  assertTrue(fs.existsSync(testCSV), 'DesiredWork.csvが存在するべき');
});

test('DesiredWork: データ読み込み', () => {
  const testCSV = path.join(phase1Dir, 'DesiredWork.csv');
  desiredWorkData = gasLogic.readCSV(testCSV);
  assertTrue(desiredWorkData.length > 0, 'データが空でないべき');
});

test('DesiredWork: 行数確認', () => {
  // 修正前は0行だったが、修正後は22,815行
  assertTrue(desiredWorkData.length > 20000, `行数が20,000以上であるべき (実際: ${desiredWorkData.length})`);
});

test('DesiredWork: データ検証', () => {
  desiredWorkResult = gasLogic.validateDesiredWork(desiredWorkData);
  assertTrue(desiredWorkResult.valid, 'データが有効であるべき');
});

test('DesiredWork: 一意申請者数確認', () => {
  const uniqueApplicants = desiredWorkResult.statistics.uniqueApplicants;
  assertEqual(uniqueApplicants, 7390, `一意申請者数が7,390であるべき (実際: ${uniqueApplicants})`);
});

test('DesiredWork: 平均希望勤務地数', () => {
  const avgDesired = parseFloat(desiredWorkResult.statistics.avgDesiredPerApplicant);
  assertInRange(avgDesired, 2.5, 4.0, `平均希望勤務地数が2.5-4.0の範囲内であるべき (実際: ${avgDesired})`);
});

console.log();

// データ整合性テスト
console.log('【データ整合性テスト】');

test('整合性: MapMetrics ↔ DesiredWork', () => {
  const mapMetricsCount = mapMetricsResult.statistics.totalCount;
  const desiredWorkCount = desiredWorkResult.statistics.totalRows;

  // カウント合計と行数が一致するはず
  assertEqual(mapMetricsCount, desiredWorkCount,
    `MapMetricsのカウント合計(${mapMetricsCount})とDesiredWorkの行数(${desiredWorkCount})が一致するべき`);
});

test('整合性: Applicants ↔ DesiredWork', () => {
  const applicantsCount = applicantsResult.statistics.totalRows;
  const uniqueApplicants = desiredWorkResult.statistics.uniqueApplicants;

  assertEqual(applicantsCount, uniqueApplicants,
    `Applicantsの行数(${applicantsCount})とDesiredWorkの一意申請者数(${uniqueApplicants})が一致するべき`);
});

console.log();

// フルバリデーション
console.log('【フルバリデーション】');
test('Phase 1完全検証', () => {
  const fullValidation = gasLogic.validatePhase1(phase1Dir);
  assertTrue(fullValidation.overall.valid, 'Phase 1全体が有効であるべき');

  // 警告がある場合は表示
  if (fullValidation.overall.warnings.length > 0) {
    console.log('   警告:');
    fullValidation.overall.warnings.forEach(warning => {
      console.log(`     - ${warning}`);
    });
  }
});

console.log();

// テスト結果サマリー
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
if (mapMetricsResult && applicantsResult && desiredWorkResult) {
  console.log('='.repeat(80));
  console.log('データ統計情報');
  console.log('='.repeat(80));

  console.log('\n【MapMetrics.csv】');
  console.log(`  総行数: ${mapMetricsResult.statistics.totalRows}`);
  console.log(`  有効座標: ${mapMetricsResult.statistics.validCoords} (${(mapMetricsResult.statistics.validCoords / mapMetricsResult.statistics.totalRows * 100).toFixed(2)}%)`);
  console.log(`  カウント合計: ${mapMetricsResult.statistics.totalCount.toLocaleString()}`);
  console.log(`  平均カウント/地点: ${mapMetricsResult.statistics.avgCountPerLocation.toFixed(2)}`);

  console.log('\n【Applicants.csv】');
  console.log(`  総行数: ${applicantsResult.statistics.totalRows.toLocaleString()}`);
  console.log(`  性別完全性: ${applicantsResult.statistics.genderCompleteness}`);
  console.log(`  年齢完全性: ${applicantsResult.statistics.ageCompleteness}`);
  console.log(`  性別分布:`);
  console.log(`    男性: ${applicantsResult.statistics.genderDistribution['男性'].toLocaleString()}`);
  console.log(`    女性: ${applicantsResult.statistics.genderDistribution['女性'].toLocaleString()}`);

  console.log('\n【DesiredWork.csv】');
  console.log(`  総行数: ${desiredWorkResult.statistics.totalRows.toLocaleString()}`);
  console.log(`  一意申請者数: ${desiredWorkResult.statistics.uniqueApplicants.toLocaleString()}`);
  console.log(`  平均希望勤務地数/人: ${desiredWorkResult.statistics.avgDesiredPerApplicant}`);
  console.log(`  都道府県数: ${desiredWorkResult.statistics.totalPrefectures}`);
  console.log(`  Top 5 都道府県:`);
  desiredWorkResult.statistics.top5Prefectures.forEach((item, index) => {
    console.log(`    ${index + 1}. ${item.prefecture}: ${item.count.toLocaleString()}`);
  });

  console.log();
}

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
