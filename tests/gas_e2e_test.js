/**
 * GAS Phase 7 E2Eテスト
 *
 * GASのJavaScriptコードをNode.js環境でテストします。
 */

const fs = require('fs');
const path = require('path');

// テスト結果
const testResults = {
  timestamp: new Date().toISOString(),
  tests: [],
  passed: 0,
  failed: 0,
  totalScore: 0
};

// テスト関数
function test(name, fn) {
  try {
    fn();
    testResults.tests.push({ name, status: 'PASS', error: null });
    testResults.passed++;
    console.log(`✅ PASS: ${name}`);
  } catch (error) {
    testResults.tests.push({ name, status: 'FAIL', error: error.message });
    testResults.failed++;
    console.log(`❌ FAIL: ${name}`);
    console.log(`   Error: ${error.message}`);
  }
}

// アサーション関数
function assert(condition, message) {
  if (!condition) {
    throw new Error(message || 'Assertion failed');
  }
}

function assertEquals(actual, expected, message) {
  if (actual !== expected) {
    throw new Error(message || `Expected ${expected}, but got ${actual}`);
  }
}

function assertNotNull(value, message) {
  if (value === null || value === undefined) {
    throw new Error(message || 'Value is null or undefined');
  }
}

// CSV読み込み関数（GASのUtilities.parseCsvをシミュレート）
function parseCsv(csvContent) {
  const lines = csvContent.split('\n').filter(line => line.trim());
  return lines.map(line => {
    // 簡易的なCSVパース（クォート処理は省略）
    return line.split(',').map(cell => cell.trim());
  });
}

// ====================================
// Phase 7 E2Eテスト
// ====================================

console.log('='.repeat(60));
console.log('GAS Phase 7 E2Eテスト');
console.log('='.repeat(60));
console.log();

// テストデータのパス
const testDataDir = path.join(__dirname, '..', 'python_scripts', 'gas_output_phase7');

// ====================================
// Test 1: CSVファイルの存在確認
// ====================================

console.log('[Test 1] CSVファイルの存在確認');
console.log('-'.repeat(60));

const expectedFiles = [
  'SupplyDensityMap.csv',
  'AgeGenderCrossAnalysis.csv',
  'MobilityScore.csv',
  'DetailedPersonaProfile.csv'
];

expectedFiles.forEach(fileName => {
  test(`CSVファイル存在: ${fileName}`, () => {
    const filePath = path.join(testDataDir, fileName);
    assert(fs.existsSync(filePath), `File not found: ${filePath}`);
  });
});

console.log();

// ====================================
// Test 2: CSV形式の検証
// ====================================

console.log('[Test 2] CSV形式の検証');
console.log('-'.repeat(60));

expectedFiles.forEach(fileName => {
  test(`CSV形式: ${fileName}`, () => {
    const filePath = path.join(testDataDir, fileName);
    const content = fs.readFileSync(filePath, 'utf-8');

    // BOM除去
    const cleanContent = content.replace(/^\uFEFF/, '');

    // CSV解析
    const data = parseCsv(cleanContent);

    assert(data.length > 0, 'CSV has no data');
    assert(data[0].length > 0, 'CSV has no columns');
  });
});

console.log();

// ====================================
// Test 3: データ内容の検証
// ====================================

console.log('[Test 3] データ内容の検証');
console.log('-'.repeat(60));

// 3-1. SupplyDensityMap.csv
test('SupplyDensityMap: ヘッダー確認', () => {
  const filePath = path.join(testDataDir, 'SupplyDensityMap.csv');
  const content = fs.readFileSync(filePath, 'utf-8').replace(/^\uFEFF/, '');
  const data = parseCsv(content);

  const headers = data[0];
  const expectedHeaders = ['市区町村', '求職者数', '資格保有率', '平均年齢', '緊急度', '総合スコア', 'ランク'];

  expectedHeaders.forEach((header, index) => {
    assertEquals(headers[index], header, `Header mismatch at index ${index}`);
  });
});

test('SupplyDensityMap: データ行数', () => {
  const filePath = path.join(testDataDir, 'SupplyDensityMap.csv');
  const content = fs.readFileSync(filePath, 'utf-8').replace(/^\uFEFF/, '');
  const data = parseCsv(content);

  assert(data.length > 1, 'No data rows');
  console.log(`   データ行数: ${data.length - 1}行`);
});

test('SupplyDensityMap: ランク値', () => {
  const filePath = path.join(testDataDir, 'SupplyDensityMap.csv');
  const content = fs.readFileSync(filePath, 'utf-8').replace(/^\uFEFF/, '');
  const data = parseCsv(content);

  const validRanks = ['S', 'A', 'B', 'C', 'D'];

  for (let i = 1; i < data.length; i++) {
    const rank = data[i][6]; // ランク列
    assert(validRanks.includes(rank), `Invalid rank: ${rank} at row ${i}`);
  }
});

// 3-2. MobilityScore.csv
test('MobilityScore: ヘッダー確認', () => {
  const filePath = path.join(testDataDir, 'MobilityScore.csv');
  const content = fs.readFileSync(filePath, 'utf-8').replace(/^\uFEFF/, '');
  const data = parseCsv(content);

  const headers = data[0];
  const expectedHeaders = ['申請者ID', '希望地数', '最大移動距離km', '移動許容度スコア', '移動許容度レベル', '移動許容度', '居住地'];

  expectedHeaders.forEach((header, index) => {
    assertEquals(headers[index], header, `Header mismatch at index ${index}`);
  });
});

test('MobilityScore: データ行数', () => {
  const filePath = path.join(testDataDir, 'MobilityScore.csv');
  const content = fs.readFileSync(filePath, 'utf-8').replace(/^\uFEFF/, '');
  const data = parseCsv(content);

  assert(data.length > 1000, 'Expected > 1000 data rows');
  console.log(`   データ行数: ${data.length - 1}行`);
});

test('MobilityScore: 移動許容度レベル', () => {
  const filePath = path.join(testDataDir, 'MobilityScore.csv');
  const content = fs.readFileSync(filePath, 'utf-8').replace(/^\uFEFF/, '');
  const data = parseCsv(content);

  const validLevels = ['A', 'B', 'C', 'D'];

  for (let i = 1; i < Math.min(data.length, 100); i++) { // 最初の100行のみチェック
    const level = data[i][4]; // 移動許容度レベル列
    assert(validLevels.includes(level), `Invalid level: ${level} at row ${i}`);
  }
});

// 3-3. AgeGenderCrossAnalysis.csv
test('AgeGenderCross: ヘッダー確認', () => {
  const filePath = path.join(testDataDir, 'AgeGenderCrossAnalysis.csv');
  const content = fs.readFileSync(filePath, 'utf-8').replace(/^\uFEFF/, '');
  const data = parseCsv(content);

  const headers = data[0];
  assert(headers.includes('市区町村'), 'Missing header: 市区町村');
  assert(headers.includes('総求職者数'), 'Missing header: 総求職者数');
});

// 3-4. DetailedPersonaProfile.csv
test('DetailedPersonaProfile: ヘッダー確認', () => {
  const filePath = path.join(testDataDir, 'DetailedPersonaProfile.csv');
  const content = fs.readFileSync(filePath, 'utf-8').replace(/^\uFEFF/, '');
  const data = parseCsv(content);

  const headers = data[0];
  assert(headers.includes('ペルソナ名'), 'Missing header: ペルソナ名');
  assert(headers.includes('人数'), 'Missing header: 人数');
});

console.log();

// ====================================
// Test 4: GASデータロード関数のシミュレーション
// ====================================

console.log('[Test 4] GASデータロード関数');
console.log('-'.repeat(60));

// loadSupplyDensityData()をシミュレート
function loadSupplyDensityData() {
  const filePath = path.join(testDataDir, 'SupplyDensityMap.csv');
  const content = fs.readFileSync(filePath, 'utf-8').replace(/^\uFEFF/, '');
  const values = parseCsv(content);

  if (values.length <= 1) {
    return [];
  }

  // ヘッダー除く
  const dataRows = values.slice(1);

  // オブジェクト配列に変換
  return dataRows.map(row => ({
    municipality: row[0],
    totalJobseekers: parseInt(row[1]),
    qualifiedRate: parseFloat(row[2]),
    avgAge: parseFloat(row[3]),
    urgency: parseFloat(row[4]),
    compositeScore: parseFloat(row[5]),
    rank: row[6]
  }));
}

test('loadSupplyDensityData: データ読み込み', () => {
  const data = loadSupplyDensityData();

  assert(data.length > 0, 'No data loaded');
  assertNotNull(data[0].municipality, 'Municipality is null');
  assertNotNull(data[0].totalJobseekers, 'TotalJobseekers is null');
  assertNotNull(data[0].rank, 'Rank is null');

  console.log(`   読み込み件数: ${data.length}件`);
  console.log(`   最初のデータ: ${data[0].municipality} (${data[0].rank}ランク)`);
});

// loadMobilityScoreData()をシミュレート
function loadMobilityScoreData() {
  const filePath = path.join(testDataDir, 'MobilityScore.csv');
  const content = fs.readFileSync(filePath, 'utf-8').replace(/^\uFEFF/, '');
  const values = parseCsv(content);

  if (values.length <= 1) {
    return [];
  }

  const dataRows = values.slice(1);

  return dataRows.map(row => ({
    applicantId: parseInt(row[0]),
    desiredLocationsCount: parseInt(row[1]),
    maxDistance: parseFloat(row[2]),
    mobilityScore: parseFloat(row[3]),
    mobilityLevel: row[4],
    mobilityLabel: row[5],
    residence: row[6]
  }));
}

test('loadMobilityScoreData: データ読み込み', () => {
  const data = loadMobilityScoreData();

  assert(data.length > 1000, 'Expected > 1000 records');
  assertNotNull(data[0].applicantId, 'ApplicantId is null');
  assertNotNull(data[0].mobilityLevel, 'MobilityLevel is null');

  console.log(`   読み込み件数: ${data.length}件`);
  console.log(`   最初のデータ: ID=${data[0].applicantId}, Level=${data[0].mobilityLevel}`);
});

console.log();

// ====================================
// Test 5: Google Chartsデータ形式の検証
// ====================================

console.log('[Test 5] Google Chartsデータ形式');
console.log('-'.repeat(60));

test('Google Charts: バブルチャートデータ', () => {
  const data = loadSupplyDensityData();

  // Google Charts DataTableのシミュレーション
  const chartData = {
    cols: [
      { label: 'ID', type: 'string' },
      { label: '総求職者数', type: 'number' },
      { label: '総合スコア', type: 'number' },
      { label: 'ランク', type: 'string' },
      { label: 'バブルサイズ', type: 'number' }
    ],
    rows: []
  };

  data.forEach(row => {
    chartData.rows.push({
      c: [
        { v: row.municipality },
        { v: row.totalJobseekers },
        { v: row.compositeScore },
        { v: row.rank },
        { v: row.totalJobseekers }
      ]
    });
  });

  assert(chartData.rows.length > 0, 'No chart data');
  assert(chartData.rows[0].c.length === 5, 'Invalid chart data structure');

  console.log(`   チャートデータ行数: ${chartData.rows.length}行`);
});

test('Google Charts: 円グラフデータ', () => {
  const data = loadSupplyDensityData();

  // ランク別集計
  const rankDistribution = {};
  data.forEach(row => {
    if (!rankDistribution[row.rank]) {
      rankDistribution[row.rank] = 0;
    }
    rankDistribution[row.rank]++;
  });

  const chartData = {
    cols: [
      { label: 'ランク', type: 'string' },
      { label: '地域数', type: 'number' }
    ],
    rows: []
  };

  Object.entries(rankDistribution).forEach(([rank, count]) => {
    chartData.rows.push({
      c: [
        { v: `ランク${rank}` },
        { v: count }
      ]
    });
  });

  assert(chartData.rows.length > 0, 'No pie chart data');

  console.log(`   ランク分布:`);
  Object.entries(rankDistribution).forEach(([rank, count]) => {
    console.log(`      ${rank}: ${count}地域`);
  });
});

console.log();

// ====================================
// Test 6: HTMLダイアログ生成のシミュレーション
// ====================================

console.log('[Test 6] HTMLダイアログ生成');
console.log('-'.repeat(60));

test('HTML生成: SupplyDensityMap', () => {
  const data = loadSupplyDensityData();
  const dataJson = JSON.stringify(data);

  const html = `
<!DOCTYPE html>
<html>
<head>
  <base target="_top">
  <script type="text/javascript" src="https://www.gstatic.com/charts/loader.js"></script>
</head>
<body>
  <h1>🗺️ Phase 7: 人材供給密度マップ</h1>
  <div id="bubble_chart"></div>
  <script>
    const data = ${dataJson};
    google.charts.load('current', {'packages':['corechart']});
    console.log('Data loaded:', data.length, 'records');
  </script>
</body>
</html>
  `;

  assert(html.includes('<!DOCTYPE html>'), 'Missing DOCTYPE');
  assert(html.includes('gstatic.com/charts'), 'Missing Google Charts');
  assert(html.includes(data[0].municipality), 'Missing data in HTML');

  console.log(`   HTML長: ${html.length}文字`);
});

console.log();

// ====================================
// テスト結果サマリー
// ====================================

console.log('='.repeat(60));
console.log('テスト結果サマリー');
console.log('='.repeat(60));
console.log();

testResults.totalScore = Math.round((testResults.passed / (testResults.passed + testResults.failed)) * 100);

console.log(`合計テスト: ${testResults.passed + testResults.failed}件`);
console.log(`成功: ${testResults.passed}件 ✅`);
console.log(`失敗: ${testResults.failed}件 ❌`);
console.log(`成功率: ${testResults.totalScore}%`);
console.log();

if (testResults.failed > 0) {
  console.log('失敗したテスト:');
  testResults.tests.filter(t => t.status === 'FAIL').forEach(t => {
    console.log(`  - ${t.name}: ${t.error}`);
  });
  console.log();
}

// テスト結果をJSONファイルに保存
const outputPath = path.join(__dirname, '..', 'docs', 'GAS_E2E_TEST_RESULTS.json');
fs.writeFileSync(outputPath, JSON.stringify(testResults, null, 2), 'utf-8');
console.log(`テスト結果を保存: ${outputPath}`);
console.log();

// 終了コード
if (testResults.failed > 0) {
  console.log('❌ テスト失敗');
  process.exit(1);
} else {
  console.log('✅ すべてのテストが成功しました！');
  process.exit(0);
}
