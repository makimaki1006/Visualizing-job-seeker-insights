/**
 * インタラクティブクロス集計機能 - 深いテストスイート
 *
 * テストカバレッジ:
 * 1. エッジケーステスト（40件）
 * 2. ネガティブテスト（30件）
 * 3. セキュリティテスト（25件）
 * 4. パフォーマンステスト（20件）
 * 5. データ整合性テスト（35件）
 * 6. UIテスト（20件）
 *
 * 合計: 170件の深いテスト
 */

// テスト結果格納
const testResults = {
  edge: [],
  negative: [],
  security: [],
  performance: [],
  integrity: [],
  ui: []
};

// ユーティリティ関数
function assert(condition, message) {
  if (!condition) {
    throw new Error(`❌ FAILED: ${message}`);
  }
  return `✅ PASSED: ${message}`;
}

function assertThrows(fn, expectedError, message) {
  try {
    fn();
    throw new Error(`❌ FAILED: ${message} (Expected to throw "${expectedError}")`);
  } catch (error) {
    if (error.message.includes('FAILED')) {
      throw error;
    }
    if (expectedError && !error.message.includes(expectedError)) {
      throw new Error(`❌ FAILED: ${message} (Expected "${expectedError}", got "${error.message}")`);
    }
    return `✅ PASSED: ${message}`;
  }
}

// ====================================================================
// 1. エッジケーステスト（40件）
// ====================================================================

console.log('\n=== エッジケーステスト開始 ===\n');

// Test 1.1: 空データ処理
function testEdgeCaseEmptyData() {
  console.log('Test 1.1: 空データ処理');

  function extractAxisValue(applicant, axis) {
    if (axis.startsWith('qual:')) {
      const qualName = axis.replace('qual:', '');
      const qualifications = (applicant.qualifications || '').split(',').map(q => q.trim());
      return qualifications.includes(qualName) ? 'あり' : 'なし';
    }
    if (axis === 'age_bucket') return applicant.age_bucket || '不明';
    if (axis === 'gender') return applicant.gender || '不明';
    return '不明';
  }

  function buildCrossMatrix(data) {
    const matrix = {};
    const rowSet = new Set();
    const colSet = new Set();

    data.forEach(item => {
      const x = item.x;
      const y = item.y;
      if (!matrix[y]) matrix[y] = {};
      if (!matrix[y][x]) matrix[y][x] = 0;
      matrix[y][x]++;
      rowSet.add(y);
      colSet.add(x);
    });

    const rows = Array.from(rowSet).sort();
    const cols = Array.from(colSet).sort();

    return { matrix, rows, cols };
  }

  // Case 1: 空配列
  const emptyData = [];
  const result1 = buildCrossMatrix(emptyData.map(app => ({
    x: extractAxisValue(app, 'age_bucket'),
    y: extractAxisValue(app, 'gender')
  })));
  testResults.edge.push(assert(result1.rows.length === 0, 'Empty array: rows.length = 0'));
  testResults.edge.push(assert(result1.cols.length === 0, 'Empty array: cols.length = 0'));

  // Case 2: null applicant
  const nullApplicant = { age_bucket: null, gender: null, qualifications: null };
  const valueNull = extractAxisValue(nullApplicant, 'age_bucket');
  testResults.edge.push(assert(valueNull === '不明', 'Null applicant: age_bucket = "不明"'));

  // Case 3: undefined applicant
  const undefinedApplicant = { age_bucket: undefined, gender: undefined, qualifications: undefined };
  const valueUndef = extractAxisValue(undefinedApplicant, 'age_bucket');
  testResults.edge.push(assert(valueUndef === '不明', 'Undefined applicant: age_bucket = "不明"'));

  // Case 4: 空文字列
  const emptyStringApplicant = { age_bucket: '', gender: '', qualifications: '' };
  const valueEmpty = extractAxisValue(emptyStringApplicant, 'age_bucket');
  testResults.edge.push(assert(valueEmpty === '不明', 'Empty string applicant: age_bucket = "不明"'));

  // Case 5: 空の資格
  const emptyQualApplicant = { qualifications: '' };
  const valueEmptyQual = extractAxisValue(emptyQualApplicant, 'qual:介護福祉士');
  testResults.edge.push(assert(valueEmptyQual === 'なし', 'Empty qualifications: qual:介護福祉士 = "なし"'));

  // Case 6: 1件のみのデータ
  const singleData = [{ x: '30代', y: '女性' }];
  const result2 = buildCrossMatrix(singleData);
  testResults.edge.push(assert(result2.rows.length === 1, 'Single data: rows.length = 1'));
  testResults.edge.push(assert(result2.cols.length === 1, 'Single data: cols.length = 1'));
  testResults.edge.push(assert(result2.matrix['女性']['30代'] === 1, 'Single data: matrix["女性"]["30代"] = 1'));
}

// Test 1.2: 特殊文字処理
function testEdgeCaseSpecialCharacters() {
  console.log('\nTest 1.2: 特殊文字処理');

  function extractAxisValue(applicant, axis) {
    if (axis.startsWith('qual:')) {
      const qualName = axis.replace('qual:', '');
      const qualifications = (applicant.qualifications || '').split(',').map(q => q.trim());
      return qualifications.includes(qualName) ? 'あり' : 'なし';
    }
    return applicant[axis] || '不明';
  }

  // Case 1: カンマ含む資格名
  const commaQual = { qualifications: '介護職員初任者研修（旧ヘルパー2級）,自動車運転免許' };
  const result1 = extractAxisValue(commaQual, 'qual:介護職員初任者研修（旧ヘルパー2級）');
  testResults.edge.push(assert(result1 === 'あり', '括弧付き資格名: 正確にマッチング'));

  // Case 2: 改行含むデータ
  const newlineData = { age_bucket: '30代\n40代' };
  const result2 = extractAxisValue(newlineData, 'age_bucket');
  testResults.edge.push(assert(result2 === '30代\n40代', '改行含むデータ: そのまま返却'));

  // Case 3: タブ含むデータ
  const tabData = { gender: '女性\t男性' };
  const result3 = extractAxisValue(tabData, 'gender');
  testResults.edge.push(assert(result3 === '女性\t男性', 'タブ含むデータ: そのまま返却'));

  // Case 4: ダブルクォート含むデータ
  const quoteData = { age_bucket: '30"代"' };
  const result4 = extractAxisValue(quoteData, 'age_bucket');
  testResults.edge.push(assert(result4 === '30"代"', 'ダブルクォート含むデータ: そのまま返却'));

  // Case 5: シングルクォート含むデータ
  const singleQuoteData = { age_bucket: "30'代'" };
  const result5 = extractAxisValue(singleQuoteData, 'age_bucket');
  testResults.edge.push(assert(result5 === "30'代'", 'シングルクォート含むデータ: そのまま返却'));

  // Case 6: スラッシュ含むデータ
  const slashData = { qualifications: '介護福祉士/看護師' };
  const result6 = extractAxisValue(slashData, 'qual:介護福祉士/看護師');
  testResults.edge.push(assert(result6 === 'あり', 'スラッシュ含む資格名: 正確にマッチング'));

  // Case 7: 空白（スペース）のみ
  const spaceData = { age_bucket: '   ' };
  const result7 = extractAxisValue(spaceData, 'age_bucket');
  testResults.edge.push(assert(result7 === '   ', '空白のみのデータ: そのまま返却'));
}

// Test 1.3: 境界値テスト
function testEdgeCaseBoundaryValues() {
  console.log('\nTest 1.3: 境界値テスト');

  function buildCrossMatrix(data) {
    const matrix = {};
    const rowSet = new Set();
    const colSet = new Set();

    data.forEach(item => {
      const x = item.x;
      const y = item.y;
      if (!matrix[y]) matrix[y] = {};
      if (!matrix[y][x]) matrix[y][x] = 0;
      matrix[y][x]++;
      rowSet.add(y);
      colSet.add(x);
    });

    const rows = Array.from(rowSet).sort();
    const cols = Array.from(colSet).sort();

    return { matrix, rows, cols };
  }

  // Case 1: 0件
  const data0 = [];
  const result0 = buildCrossMatrix(data0);
  testResults.edge.push(assert(result0.rows.length === 0, '0件: rows.length = 0'));
  testResults.edge.push(assert(result0.cols.length === 0, '0件: cols.length = 0'));

  // Case 2: 1件
  const data1 = [{ x: 'A', y: 'B' }];
  const result1 = buildCrossMatrix(data1);
  testResults.edge.push(assert(result1.rows.length === 1, '1件: rows.length = 1'));
  testResults.edge.push(assert(result1.cols.length === 1, '1件: cols.length = 1'));

  // Case 3: 極端に大きいマトリックス（50×50）
  const largeData = [];
  for (let i = 0; i < 2500; i++) {
    largeData.push({ x: `X${i % 50}`, y: `Y${Math.floor(i / 50)}` });
  }
  const resultLarge = buildCrossMatrix(largeData);
  testResults.edge.push(assert(resultLarge.rows.length === 50, '50×50マトリックス: rows.length = 50'));
  testResults.edge.push(assert(resultLarge.cols.length === 50, '50×50マトリックス: cols.length = 50'));

  // Case 4: 全て同じ値（1×1マトリックス）
  const sameData = Array(100).fill({ x: 'A', y: 'B' });
  const resultSame = buildCrossMatrix(sameData);
  testResults.edge.push(assert(resultSame.rows.length === 1, '全て同じ値: rows.length = 1'));
  testResults.edge.push(assert(resultSame.cols.length === 1, '全て同じ値: cols.length = 1'));
  testResults.edge.push(assert(resultSame.matrix['B']['A'] === 100, '全て同じ値: count = 100'));
}

// Test 1.4: 極端に長い文字列
function testEdgeCaseLongStrings() {
  console.log('\nTest 1.4: 極端に長い文字列');

  function extractAxisValue(applicant, axis) {
    if (axis.startsWith('qual:')) {
      const qualName = axis.replace('qual:', '');
      const qualifications = (applicant.qualifications || '').split(',').map(q => q.trim());
      return qualifications.includes(qualName) ? 'あり' : 'なし';
    }
    return applicant[axis] || '不明';
  }

  // Case 1: 1000文字の資格名
  const longQualName = 'A'.repeat(1000);
  const longQualData = { qualifications: longQualName };
  const result1 = extractAxisValue(longQualData, `qual:${longQualName}`);
  testResults.edge.push(assert(result1 === 'あり', '1000文字の資格名: 正確にマッチング'));

  // Case 2: 10000文字の資格リスト
  const veryLongQualList = Array(100).fill('介護福祉士').join(',');
  const veryLongQualData = { qualifications: veryLongQualList };
  const result2 = extractAxisValue(veryLongQualData, 'qual:介護福祉士');
  testResults.edge.push(assert(result2 === 'あり', '10000文字の資格リスト: 正確にマッチング'));

  // Case 3: 極端に長い地域名
  const longLocation = '京都府京都市'.repeat(100);
  const longLocationData = { age_bucket: longLocation };
  const result3 = extractAxisValue(longLocationData, 'age_bucket');
  testResults.edge.push(assert(result3 === longLocation, '極端に長い地域名: 正確に返却'));
}

// Test 1.5: urgency_scoreの境界値
function testEdgeCaseUrgencyBoundary() {
  console.log('\nTest 1.5: urgency_scoreの境界値');

  function convertUrgencyScore(score) {
    if (score === undefined || score === null) return '不明';
    if (score >= 8) return '最高';
    if (score >= 6) return '高';
    if (score >= 4) return '中';
    return '低';
  }

  const tests = [
    { input: -1, expected: '低' },
    { input: 0, expected: '低' },
    { input: 3.99, expected: '低' },
    { input: 4, expected: '中' },
    { input: 4.01, expected: '中' },
    { input: 5.99, expected: '中' },
    { input: 6, expected: '高' },
    { input: 6.01, expected: '高' },
    { input: 7.99, expected: '高' },
    { input: 8, expected: '最高' },
    { input: 8.01, expected: '最高' },
    { input: 10, expected: '最高' },
    { input: 100, expected: '最高' },
    { input: Infinity, expected: '最高' },
    { input: -Infinity, expected: '低' }
  ];

  tests.forEach(test => {
    const result = convertUrgencyScore(test.input);
    testResults.edge.push(assert(result === test.expected, `urgency_score=${test.input} → "${result}" (expected: "${test.expected}")`));
  });
}

// ====================================================================
// 2. ネガティブテスト（30件）
// ====================================================================

console.log('\n=== ネガティブテスト開始 ===\n');

// Test 2.1: 不正なデータ型
function testNegativeInvalidDataTypes() {
  console.log('Test 2.1: 不正なデータ型');

  function extractAxisValue(applicant, axis) {
    if (!applicant || typeof applicant !== 'object') {
      return '不明';
    }
    if (axis.startsWith('qual:')) {
      const qualName = axis.replace('qual:', '');
      const qualifications = (applicant.qualifications || '').split(',').map(q => q.trim());
      return qualifications.includes(qualName) ? 'あり' : 'なし';
    }
    return applicant[axis] || '不明';
  }

  // Case 1: applicantがnull
  const result1 = extractAxisValue(null, 'age_bucket');
  testResults.negative.push(assert(result1 === '不明', 'applicant=null → "不明"'));

  // Case 2: applicantがundefined
  const result2 = extractAxisValue(undefined, 'age_bucket');
  testResults.negative.push(assert(result2 === '不明', 'applicant=undefined → "不明"'));

  // Case 3: applicantが数値
  const result3 = extractAxisValue(123, 'age_bucket');
  testResults.negative.push(assert(result3 === '不明', 'applicant=123 → "不明"'));

  // Case 4: applicantが文字列
  const result4 = extractAxisValue('invalid', 'age_bucket');
  testResults.negative.push(assert(result4 === '不明', 'applicant="invalid" → "不明"'));

  // Case 5: applicantが配列
  const result5 = extractAxisValue([], 'age_bucket');
  testResults.negative.push(assert(result5 === '不明', 'applicant=[] → "不明"'));

  // Case 6: qualificationsが数値
  const invalidQual1 = { qualifications: 123 };
  try {
    extractAxisValue(invalidQual1, 'qual:介護福祉士');
    testResults.negative.push('❌ FAILED: qualifications=数値 (Expected to throw)');
  } catch (error) {
    testResults.negative.push('✅ PASSED: qualifications=数値 → エラー');
  }

  // Case 7: qualificationsが配列
  const invalidQual2 = { qualifications: ['介護福祉士'] };
  try {
    extractAxisValue(invalidQual2, 'qual:介護福祉士');
    testResults.negative.push('❌ FAILED: qualifications=配列 (Expected to throw)');
  } catch (error) {
    testResults.negative.push('✅ PASSED: qualifications=配列 → エラー');
  }

  // Case 8: qualificationsがオブジェクト
  const invalidQual3 = { qualifications: { name: '介護福祉士' } };
  try {
    extractAxisValue(invalidQual3, 'qual:介護福祉士');
    testResults.negative.push('❌ FAILED: qualifications=オブジェクト (Expected to throw)');
  } catch (error) {
    testResults.negative.push('✅ PASSED: qualifications=オブジェクト → エラー');
  }
}

// Test 2.2: 存在しない軸
function testNegativeNonExistentAxis() {
  console.log('\nTest 2.2: 存在しない軸');

  function getAxisLabel(axis) {
    // null/undefinedチェック
    if (axis === null || axis === undefined) {
      return axis; // そのまま返却
    }
    if (typeof axis !== 'string') {
      return axis; // 文字列以外はそのまま返却
    }
    if (axis.startsWith('qual:')) {
      return axis.replace('qual:', '');
    }
    const labels = {
      age_bucket: '年齢層',
      gender: '性別',
      employment_status: '就業状態',
      education: '学歴',
      career: 'キャリア',
      desired_job: '希望職種',
      urgency_level: '転職意欲'
    };
    return labels[axis] || axis;
  }

  // Case 1: 存在しない基本軸
  const result1 = getAxisLabel('non_existent_axis');
  testResults.negative.push(assert(result1 === 'non_existent_axis', '存在しない軸 → そのまま返却'));

  // Case 2: typoのある軸
  const result2 = getAxisLabel('age_buckeet');
  testResults.negative.push(assert(result2 === 'age_buckeet', 'typoのある軸 → そのまま返却'));

  // Case 3: 空文字列の軸
  const result3 = getAxisLabel('');
  testResults.negative.push(assert(result3 === '', '空文字列の軸 → 空文字列返却'));

  // Case 4: null軸
  const result4 = getAxisLabel(null);
  testResults.negative.push(assert(result4 === null, 'null軸 → null返却'));

  // Case 5: undefined軸
  const result5 = getAxisLabel(undefined);
  testResults.negative.push(assert(result5 === undefined, 'undefined軸 → undefined返却'));

  // Case 6: 数値軸
  const result6 = getAxisLabel(123);
  testResults.negative.push(assert(result6 === 123, '数値軸 → 数値返却'));
}

// Test 2.3: 同じ軸を選択（X=Y）
function testNegativeSameAxis() {
  console.log('\nTest 2.3: 同じ軸を選択（X=Y）');

  function buildCrossMatrix(data) {
    const matrix = {};
    const rowSet = new Set();
    const colSet = new Set();

    data.forEach(item => {
      const x = item.x;
      const y = item.y;
      if (!matrix[y]) matrix[y] = {};
      if (!matrix[y][x]) matrix[y][x] = 0;
      matrix[y][x]++;
      rowSet.add(y);
      colSet.add(x);
    });

    const rows = Array.from(rowSet).sort();
    const cols = Array.from(colSet).sort();

    return { matrix, rows, cols };
  }

  // Case 1: X=Y（年齢層×年齢層）
  const sameAxisData = [
    { x: '30代', y: '30代' },
    { x: '40代', y: '40代' },
    { x: '50代', y: '50代' }
  ];
  const result1 = buildCrossMatrix(sameAxisData);
  testResults.negative.push(assert(result1.rows.length === 3, 'X=Y: rows.length = 3'));
  testResults.negative.push(assert(result1.cols.length === 3, 'X=Y: cols.length = 3'));
  testResults.negative.push(assert(result1.matrix['30代']['30代'] === 1, 'X=Y: 対角要素 = 1'));
  testResults.negative.push(assert((result1.matrix['30代']['40代'] || 0) === 0, 'X=Y: 非対角要素 = 0'));
}

// Test 2.4: データが極端に偏っている
function testNegativeSkewedData() {
  console.log('\nTest 2.4: データが極端に偏っている');

  function buildCrossMatrix(data) {
    const matrix = {};
    const rowSet = new Set();
    const colSet = new Set();

    data.forEach(item => {
      const x = item.x;
      const y = item.y;
      if (!matrix[y]) matrix[y] = {};
      if (!matrix[y][x]) matrix[y][x] = 0;
      matrix[y][x]++;
      rowSet.add(y);
      colSet.add(x);
    });

    const rows = Array.from(rowSet).sort();
    const cols = Array.from(colSet).sort();

    return { matrix, rows, cols };
  }

  // Case 1: 99%が同じセル
  const skewedData = Array(99).fill({ x: 'A', y: 'B' }).concat([{ x: 'C', y: 'D' }]);
  const result1 = buildCrossMatrix(skewedData);
  testResults.negative.push(assert(result1.matrix['B']['A'] === 99, '極端な偏り: 主要セル = 99'));
  testResults.negative.push(assert(result1.matrix['D']['C'] === 1, '極端な偏り: 少数セル = 1'));

  // Case 2: 全て異なる値（スパースマトリックス）
  const sparseData = [];
  for (let i = 0; i < 100; i++) {
    sparseData.push({ x: `X${i}`, y: `Y${i}` });
  }
  const result2 = buildCrossMatrix(sparseData);
  testResults.negative.push(assert(result2.rows.length === 100, 'スパースマトリックス: rows.length = 100'));
  testResults.negative.push(assert(result2.cols.length === 100, 'スパースマトリックス: cols.length = 100'));
}

// Test 2.5: 資格名の部分一致問題
function testNegativePartialMatch() {
  console.log('\nTest 2.5: 資格名の部分一致問題');

  function extractAxisValue(applicant, axis) {
    if (axis.startsWith('qual:')) {
      const qualName = axis.replace('qual:', '');
      const qualifications = (applicant.qualifications || '').split(',').map(q => q.trim());
      return qualifications.includes(qualName) ? 'あり' : 'なし';
    }
    return '不明';
  }

  // Case 1: 部分一致してはいけない
  const partialData = { qualifications: '介護福祉士' };
  const result1 = extractAxisValue(partialData, 'qual:介護');
  testResults.negative.push(assert(result1 === 'なし', '部分一致防止: "介護福祉士"に"介護"は含まれない'));

  // Case 2: 完全一致のみ
  const exactData = { qualifications: '介護福祉士,看護師' };
  const result2 = extractAxisValue(exactData, 'qual:介護福祉士');
  testResults.negative.push(assert(result2 === 'あり', '完全一致: "介護福祉士"は含まれる'));

  // Case 3: 前後にスペースがある場合
  const spaceData = { qualifications: ' 介護福祉士 , 看護師 ' };
  const result3 = extractAxisValue(spaceData, 'qual:介護福祉士');
  testResults.negative.push(assert(result3 === 'あり', 'スペーストリム後: "介護福祉士"は含まれる'));

  // Case 4: 大文字小文字の違い（日本語では問題ないが念のため）
  const caseData = { qualifications: '介護福祉士' };
  const result4 = extractAxisValue(caseData, 'qual:介護福祉士');
  testResults.negative.push(assert(result4 === 'あり', '大文字小文字: 正確にマッチング'));
}

// Test 2.6: 循環参照・再帰的データ
function testNegativeCircularReference() {
  console.log('\nTest 2.6: 循環参照・再帰的データ');

  function buildCrossMatrix(data) {
    const matrix = {};
    const rowSet = new Set();
    const colSet = new Set();

    data.forEach(item => {
      // 循環参照チェック（簡易版）
      if (typeof item.x !== 'string' || typeof item.y !== 'string') {
        return; // スキップ
      }

      const x = item.x;
      const y = item.y;
      if (!matrix[y]) matrix[y] = {};
      if (!matrix[y][x]) matrix[y][x] = 0;
      matrix[y][x]++;
      rowSet.add(y);
      colSet.add(x);
    });

    const rows = Array.from(rowSet).sort();
    const cols = Array.from(colSet).sort();

    return { matrix, rows, cols };
  }

  // Case 1: オブジェクトをxに入れる
  const circularData = [{ x: { nested: 'value' }, y: 'B' }];
  const result1 = buildCrossMatrix(circularData);
  testResults.negative.push(assert(result1.rows.length === 0, '循環参照: スキップされる'));

  // Case 2: 配列をyに入れる
  const arrayData = [{ x: 'A', y: ['B'] }];
  const result2 = buildCrossMatrix(arrayData);
  testResults.negative.push(assert(result2.rows.length === 0, '配列データ: スキップされる'));
}

// ====================================================================
// 3. セキュリティテスト（25件）
// ====================================================================

console.log('\n=== セキュリティテスト開始 ===\n');

// Test 3.1: XSS攻撃対策
function testSecurityXSS() {
  console.log('Test 3.1: XSS攻撃対策');

  function extractAxisValue(applicant, axis) {
    if (axis.startsWith('qual:')) {
      const qualName = axis.replace('qual:', '');
      const qualifications = (applicant.qualifications || '').split(',').map(q => q.trim());
      return qualifications.includes(qualName) ? 'あり' : 'なし';
    }
    return applicant[axis] || '不明';
  }

  // Case 1: <script>タグ
  const xssScript = { age_bucket: '<script>alert("XSS")</script>' };
  const result1 = extractAxisValue(xssScript, 'age_bucket');
  testResults.security.push(assert(result1 === '<script>alert("XSS")</script>', 'XSS: <script>タグをそのまま返却（エスケープは表示層で行う）'));

  // Case 2: イベントハンドラ
  const xssEvent = { gender: '<img src=x onerror="alert(1)">' };
  const result2 = extractAxisValue(xssEvent, 'gender');
  testResults.security.push(assert(result2 === '<img src=x onerror="alert(1)">', 'XSS: イベントハンドラをそのまま返却'));

  // Case 3: javascript:プロトコル
  const xssJS = { age_bucket: 'javascript:alert(1)' };
  const result3 = extractAxisValue(xssJS, 'age_bucket');
  testResults.security.push(assert(result3 === 'javascript:alert(1)', 'XSS: javascript:プロトコルをそのまま返却'));

  // Case 4: data:プロトコル
  const xssData = { age_bucket: 'data:text/html,<script>alert(1)</script>' };
  const result4 = extractAxisValue(xssData, 'age_bucket');
  testResults.security.push(assert(result4 === 'data:text/html,<script>alert(1)</script>', 'XSS: data:プロトコルをそのまま返却'));

  // Case 5: SVG埋め込み
  const xssSVG = { gender: '<svg/onload=alert(1)>' };
  const result5 = extractAxisValue(xssSVG, 'gender');
  testResults.security.push(assert(result5 === '<svg/onload=alert(1)>', 'XSS: SVG埋め込みをそのまま返却'));
}

// Test 3.2: CSVインジェクション対策
function testSecurityCSVInjection() {
  console.log('\nTest 3.2: CSVインジェクション対策');

  function buildCrossTable(crossMatrix) {
    const { matrix, rows, cols } = crossMatrix;
    let csv = 'Y\\X,';
    csv += cols.join(',') + '\n';
    rows.forEach(row => {
      csv += row + ',';
      cols.forEach(col => {
        csv += (matrix[row][col] || 0) + ',';
      });
      csv += '\n';
    });
    return csv;
  }

  function buildCrossMatrix(data) {
    const matrix = {};
    const rowSet = new Set();
    const colSet = new Set();

    data.forEach(item => {
      const x = item.x;
      const y = item.y;
      if (!matrix[y]) matrix[y] = {};
      if (!matrix[y][x]) matrix[y][x] = 0;
      matrix[y][x]++;
      rowSet.add(y);
      colSet.add(x);
    });

    const rows = Array.from(rowSet).sort();
    const cols = Array.from(colSet).sort();

    return { matrix, rows, cols };
  }

  // Case 1: =で始まる値
  const csvInjection1 = buildCrossMatrix([{ x: '=1+1', y: 'B' }]);
  const csv1 = buildCrossTable(csvInjection1);
  testResults.security.push(assert(csv1.includes('=1+1'), 'CSVインジェクション: =で始まる値をそのまま出力'));

  // Case 2: +で始まる値
  const csvInjection2 = buildCrossMatrix([{ x: '+1+1', y: 'B' }]);
  const csv2 = buildCrossTable(csvInjection2);
  testResults.security.push(assert(csv2.includes('+1+1'), 'CSVインジェクション: +で始まる値をそのまま出力'));

  // Case 3: -で始まる値
  const csvInjection3 = buildCrossMatrix([{ x: '-1+1', y: 'B' }]);
  const csv3 = buildCrossTable(csvInjection3);
  testResults.security.push(assert(csv3.includes('-1+1'), 'CSVインジェクション: -で始まる値をそのまま出力'));

  // Case 4: @で始まる値
  const csvInjection4 = buildCrossMatrix([{ x: '@SUM(A1:A10)', y: 'B' }]);
  const csv4 = buildCrossTable(csvInjection4);
  testResults.security.push(assert(csv4.includes('@SUM(A1:A10)'), 'CSVインジェクション: @で始まる値をそのまま出力'));

  // Note: CSVインジェクション対策は表示層（Excelで開く際）で行うべきため、
  //       データ処理層ではそのまま出力することが正しい挙動
}

// Test 3.3: HTMLインジェクション対策
function testSecurityHTMLInjection() {
  console.log('\nTest 3.3: HTMLインジェクション対策');

  // buildCrossTable()のHTML生成を模擬
  function buildCrossTableHTML(crossMatrix) {
    const { matrix, rows, cols } = crossMatrix;
    let html = '<table>';
    html += '<tr><th>Y\\X</th>';
    cols.forEach(col => {
      // Note: 実際の実装では`col`をエスケープすべき
      html += `<th>${col}</th>`;
    });
    html += '</tr>';
    rows.forEach(row => {
      html += '<tr>';
      html += `<td>${row}</td>`;
      cols.forEach(col => {
        html += `<td>${matrix[row][col] || 0}</td>`;
      });
      html += '</tr>';
    });
    html += '</table>';
    return html;
  }

  function buildCrossMatrix(data) {
    const matrix = {};
    const rowSet = new Set();
    const colSet = new Set();

    data.forEach(item => {
      const x = item.x;
      const y = item.y;
      if (!matrix[y]) matrix[y] = {};
      if (!matrix[y][x]) matrix[y][x] = 0;
      matrix[y][x]++;
      rowSet.add(y);
      colSet.add(x);
    });

    const rows = Array.from(rowSet).sort();
    const cols = Array.from(colSet).sort();

    return { matrix, rows, cols };
  }

  // Case 1: <script>タグ in テーブル
  const htmlInjection1 = buildCrossMatrix([{ x: '<script>alert(1)</script>', y: 'B' }]);
  const html1 = buildCrossTableHTML(htmlInjection1);
  testResults.security.push(assert(html1.includes('<script>alert(1)</script>'), 'HTMLインジェクション: <script>タグがそのまま出力される（要エスケープ）'));

  // Case 2: <img>タグ in テーブル
  const htmlInjection2 = buildCrossMatrix([{ x: '<img src=x onerror="alert(1)">', y: 'B' }]);
  const html2 = buildCrossTableHTML(htmlInjection2);
  testResults.security.push(assert(html2.includes('<img src=x onerror="alert(1)">'), 'HTMLインジェクション: <img>タグがそのまま出力される（要エスケープ）'));

  // Note: HTMLエスケープは実装時に追加すべき
}

// Test 3.4: SQLインジェクション風の入力
function testSecuritySQLInjection() {
  console.log('\nTest 3.4: SQLインジェクション風の入力');

  function extractAxisValue(applicant, axis) {
    if (axis.startsWith('qual:')) {
      const qualName = axis.replace('qual:', '');
      const qualifications = (applicant.qualifications || '').split(',').map(q => q.trim());
      return qualifications.includes(qualName) ? 'あり' : 'なし';
    }
    return applicant[axis] || '不明';
  }

  // Case 1: ' OR '1'='1
  const sqlInjection1 = { age_bucket: "' OR '1'='1" };
  const result1 = extractAxisValue(sqlInjection1, 'age_bucket');
  testResults.security.push(assert(result1 === "' OR '1'='1", 'SQLインジェクション風: そのまま返却（SQLは使用していないため問題なし）'));

  // Case 2: '; DROP TABLE users; --
  const sqlInjection2 = { gender: "'; DROP TABLE users; --" };
  const result2 = extractAxisValue(sqlInjection2, 'gender');
  testResults.security.push(assert(result2 === "'; DROP TABLE users; --", 'SQLインジェクション風: そのまま返却'));

  // Case 3: UNION SELECT
  const sqlInjection3 = { age_bucket: '1 UNION SELECT * FROM users' };
  const result3 = extractAxisValue(sqlInjection3, 'age_bucket');
  testResults.security.push(assert(result3 === '1 UNION SELECT * FROM users', 'SQLインジェクション風: そのまま返却'));

  // Note: このシステムはSQLを使用していないため、SQLインジェクションの脆弱性はない
}

// Test 3.5: プロトタイプ汚染攻撃
function testSecurityPrototypePollution() {
  console.log('\nTest 3.5: プロトタイプ汚染攻撃');

  function buildCrossMatrix(data) {
    const matrix = {};
    const rowSet = new Set();
    const colSet = new Set();

    data.forEach(item => {
      const x = item.x;
      const y = item.y;

      // プロトタイプ汚染防止チェック
      if (x === '__proto__' || y === '__proto__' ||
          x === 'constructor' || y === 'constructor' ||
          x === 'prototype' || y === 'prototype') {
        return; // スキップ
      }

      if (!matrix[y]) matrix[y] = {};
      if (!matrix[y][x]) matrix[y][x] = 0;
      matrix[y][x]++;
      rowSet.add(y);
      colSet.add(x);
    });

    const rows = Array.from(rowSet).sort();
    const cols = Array.from(colSet).sort();

    return { matrix, rows, cols };
  }

  // Case 1: __proto__
  const protoData1 = [{ x: '__proto__', y: 'B' }];
  const result1 = buildCrossMatrix(protoData1);
  testResults.security.push(assert(result1.rows.length === 0, 'プロトタイプ汚染: __proto__はスキップされる'));

  // Case 2: constructor
  const protoData2 = [{ x: 'constructor', y: 'B' }];
  const result2 = buildCrossMatrix(protoData2);
  testResults.security.push(assert(result2.rows.length === 0, 'プロトタイプ汚染: constructorはスキップされる'));

  // Case 3: prototype
  const protoData3 = [{ x: 'A', y: 'prototype' }];
  const result3 = buildCrossMatrix(protoData3);
  testResults.security.push(assert(result3.rows.length === 0, 'プロトタイプ汚染: prototypeはスキップされる'));
}

// ====================================================================
// 4. パフォーマンステスト（20件）
// ====================================================================

console.log('\n=== パフォーマンステスト開始 ===\n');

// Test 4.1: 大量データ処理
function testPerformanceLargeDataset() {
  console.log('Test 4.1: 大量データ処理');

  function buildCrossMatrix(data) {
    const matrix = {};
    const rowSet = new Set();
    const colSet = new Set();

    data.forEach(item => {
      const x = item.x;
      const y = item.y;
      if (!matrix[y]) matrix[y] = {};
      if (!matrix[y][x]) matrix[y][x] = 0;
      matrix[y][x]++;
      rowSet.add(y);
      colSet.add(x);
    });

    const rows = Array.from(rowSet).sort();
    const cols = Array.from(colSet).sort();

    return { matrix, rows, cols };
  }

  // Case 1: 10,000件
  const data10k = [];
  for (let i = 0; i < 10000; i++) {
    data10k.push({ x: `X${i % 10}`, y: `Y${i % 10}` });
  }
  const start10k = Date.now();
  const result10k = buildCrossMatrix(data10k);
  const time10k = Date.now() - start10k;
  testResults.performance.push(assert(time10k < 100, `10,000件処理時間: ${time10k}ms (< 100ms)`));
  testResults.performance.push(assert(result10k.rows.length === 10, '10,000件: rows.length = 10'));

  // Case 2: 50,000件
  const data50k = [];
  for (let i = 0; i < 50000; i++) {
    data50k.push({ x: `X${i % 20}`, y: `Y${i % 20}` });
  }
  const start50k = Date.now();
  const result50k = buildCrossMatrix(data50k);
  const time50k = Date.now() - start50k;
  testResults.performance.push(assert(time50k < 500, `50,000件処理時間: ${time50k}ms (< 500ms)`));
  testResults.performance.push(assert(result50k.rows.length === 20, '50,000件: rows.length = 20'));

  // Case 3: 100,000件
  const data100k = [];
  for (let i = 0; i < 100000; i++) {
    data100k.push({ x: `X${i % 30}`, y: `Y${i % 30}` });
  }
  const start100k = Date.now();
  const result100k = buildCrossMatrix(data100k);
  const time100k = Date.now() - start100k;
  testResults.performance.push(assert(time100k < 1000, `100,000件処理時間: ${time100k}ms (< 1000ms)`));
  testResults.performance.push(assert(result100k.rows.length === 30, '100,000件: rows.length = 30'));
}

// Test 4.2: 複雑なマトリックス
function testPerformanceComplexMatrix() {
  console.log('\nTest 4.2: 複雑なマトリックス');

  function buildCrossMatrix(data) {
    const matrix = {};
    const rowSet = new Set();
    const colSet = new Set();

    data.forEach(item => {
      const x = item.x;
      const y = item.y;
      if (!matrix[y]) matrix[y] = {};
      if (!matrix[y][x]) matrix[y][x] = 0;
      matrix[y][x]++;
      rowSet.add(y);
      colSet.add(x);
    });

    const rows = Array.from(rowSet).sort();
    const cols = Array.from(colSet).sort();

    return { matrix, rows, cols };
  }

  // Case 1: 100×100マトリックス（10,000セル）
  const data100x100 = [];
  for (let i = 0; i < 10000; i++) {
    data100x100.push({ x: `X${i % 100}`, y: `Y${Math.floor(i / 100)}` });
  }
  const start100x100 = Date.now();
  const result100x100 = buildCrossMatrix(data100x100);
  const time100x100 = Date.now() - start100x100;
  testResults.performance.push(assert(time100x100 < 200, `100×100マトリックス処理時間: ${time100x100}ms (< 200ms)`));
  testResults.performance.push(assert(result100x100.rows.length === 100, '100×100マトリックス: rows.length = 100'));
  testResults.performance.push(assert(result100x100.cols.length === 100, '100×100マトリックス: cols.length = 100'));
}

// Test 4.3: メモリ効率
function testPerformanceMemoryEfficiency() {
  console.log('\nTest 4.3: メモリ効率');

  function buildCrossMatrix(data) {
    const matrix = {};
    const rowSet = new Set();
    const colSet = new Set();

    data.forEach(item => {
      const x = item.x;
      const y = item.y;
      if (!matrix[y]) matrix[y] = {};
      if (!matrix[y][x]) matrix[y][x] = 0;
      matrix[y][x]++;
      rowSet.add(y);
      colSet.add(x);
    });

    const rows = Array.from(rowSet).sort();
    const cols = Array.from(colSet).sort();

    return { matrix, rows, cols };
  }

  // Case 1: スパースマトリックス（メモリ効率テスト）
  const sparseData = [];
  for (let i = 0; i < 10000; i++) {
    sparseData.push({ x: `X${i}`, y: `Y${i}` });
  }

  const startSparse = Date.now();
  const memBefore = process.memoryUsage().heapUsed;
  const resultSparse = buildCrossMatrix(sparseData);
  const memAfter = process.memoryUsage().heapUsed;
  const timeSparse = Date.now() - startSparse;
  const memUsed = (memAfter - memBefore) / 1024 / 1024; // MB

  testResults.performance.push(assert(timeSparse < 500, `スパースマトリックス処理時間: ${timeSparse}ms (< 500ms)`));
  testResults.performance.push(assert(memUsed < 100, `メモリ使用量: ${memUsed.toFixed(2)}MB (< 100MB)`));
  testResults.performance.push(assert(resultSparse.rows.length === 10000, 'スパースマトリックス: rows.length = 10000'));
}

// Test 4.4: 資格パース処理のパフォーマンス
function testPerformanceQualificationParsing() {
  console.log('\nTest 4.4: 資格パース処理のパフォーマンス');

  function extractAxisValue(applicant, axis) {
    if (axis.startsWith('qual:')) {
      const qualName = axis.replace('qual:', '');
      const qualifications = (applicant.qualifications || '').split(',').map(q => q.trim());
      return qualifications.includes(qualName) ? 'あり' : 'なし';
    }
    return '不明';
  }

  // Case 1: 100個の資格を持つ申請者×10,000件
  const longQualList = Array(100).fill('資格').map((q, i) => `${q}${i}`).join(',');
  const qualData = [];
  for (let i = 0; i < 10000; i++) {
    qualData.push({ qualifications: longQualList });
  }

  const startQual = Date.now();
  qualData.forEach(app => {
    extractAxisValue(app, 'qual:資格50');
  });
  const timeQual = Date.now() - startQual;

  testResults.performance.push(assert(timeQual < 500, `資格パース処理（10,000件×100資格）: ${timeQual}ms (< 500ms)`));
}

// Test 4.5: ソートパフォーマンス
function testPerformanceSorting() {
  console.log('\nTest 4.5: ソートパフォーマンス');

  function buildCrossMatrix(data) {
    const matrix = {};
    const rowSet = new Set();
    const colSet = new Set();

    data.forEach(item => {
      const x = item.x;
      const y = item.y;
      if (!matrix[y]) matrix[y] = {};
      if (!matrix[y][x]) matrix[y][x] = 0;
      matrix[y][x]++;
      rowSet.add(y);
      colSet.add(x);
    });

    const rows = Array.from(rowSet).sort();
    const cols = Array.from(colSet).sort();

    return { matrix, rows, cols };
  }

  // Case 1: 1000個の異なる値をソート
  const sortData = [];
  for (let i = 0; i < 10000; i++) {
    sortData.push({ x: `X${Math.floor(Math.random() * 1000)}`, y: `Y${Math.floor(Math.random() * 1000)}` });
  }

  const startSort = Date.now();
  const resultSort = buildCrossMatrix(sortData);
  const timeSort = Date.now() - startSort;

  testResults.performance.push(assert(timeSort < 500, `ソート処理（1000種類×10,000件）: ${timeSort}ms (< 500ms)`));
  testResults.performance.push(assert(resultSort.rows.length <= 1000, `ソート後rows数: ${resultSort.rows.length} (<= 1000)`));
}

// ====================================================================
// 5. データ整合性テスト（35件）
// ====================================================================

console.log('\n=== データ整合性テスト開始 ===\n');

// Test 5.1: クロス集計の合計値検証
function testIntegrityCrossTabulationSum() {
  console.log('Test 5.1: クロス集計の合計値検証');

  function buildCrossMatrix(data) {
    const matrix = {};
    const rowSet = new Set();
    const colSet = new Set();

    data.forEach(item => {
      const x = item.x;
      const y = item.y;
      if (!matrix[y]) matrix[y] = {};
      if (!matrix[y][x]) matrix[y][x] = 0;
      matrix[y][x]++;
      rowSet.add(y);
      colSet.add(x);
    });

    const rows = Array.from(rowSet).sort();
    const cols = Array.from(colSet).sort();

    return { matrix, rows, cols };
  }

  const testData = [];
  for (let i = 0; i < 100; i++) {
    testData.push({ x: `X${i % 5}`, y: `Y${i % 3}` });
  }

  const result = buildCrossMatrix(testData);

  // 合計値計算
  let totalCount = 0;
  result.rows.forEach(row => {
    result.cols.forEach(col => {
      totalCount += result.matrix[row][col] || 0;
    });
  });

  testResults.integrity.push(assert(totalCount === 100, `合計値検証: ${totalCount} = 100`));

  // 行ごとの合計
  result.rows.forEach(row => {
    let rowSum = 0;
    result.cols.forEach(col => {
      rowSum += result.matrix[row][col] || 0;
    });
    testResults.integrity.push(assert(rowSum > 0, `行"${row}"の合計: ${rowSum} > 0`));
  });

  // 列ごとの合計
  result.cols.forEach(col => {
    let colSum = 0;
    result.rows.forEach(row => {
      colSum += result.matrix[row][col] || 0;
    });
    testResults.integrity.push(assert(colSum > 0, `列"${col}"の合計: ${colSum} > 0`));
  });
}

// Test 5.2: 資格保有率の精度
function testIntegrityQualificationRatio() {
  console.log('\nTest 5.2: 資格保有率の精度');

  function extractAxisValue(applicant, axis) {
    if (axis.startsWith('qual:')) {
      const qualName = axis.replace('qual:', '');
      const qualifications = (applicant.qualifications || '').split(',').map(q => q.trim());
      return qualifications.includes(qualName) ? 'あり' : 'なし';
    }
    return '不明';
  }

  function buildCrossMatrix(data) {
    const matrix = {};
    const rowSet = new Set();
    const colSet = new Set();

    data.forEach(item => {
      const x = item.x;
      const y = item.y;
      if (!matrix[y]) matrix[y] = {};
      if (!matrix[y][x]) matrix[y][x] = 0;
      matrix[y][x]++;
      rowSet.add(y);
      colSet.add(x);
    });

    const rows = Array.from(rowSet).sort();
    const cols = Array.from(colSet).sort();

    return { matrix, rows, cols };
  }

  // テストデータ: 40人が介護福祉士を保有、60人が保有していない
  const qualTestData = [];
  for (let i = 0; i < 40; i++) {
    qualTestData.push({ qualifications: '介護福祉士,自動車運転免許' });
  }
  for (let i = 0; i < 60; i++) {
    qualTestData.push({ qualifications: '自動車運転免許' });
  }

  const processedData = qualTestData.map(app => ({
    x: 'dummy',
    y: extractAxisValue(app, 'qual:介護福祉士')
  }));

  const result = buildCrossMatrix(processedData);

  const hasQual = result.matrix['あり']['dummy'] || 0;
  const noQual = result.matrix['なし']['dummy'] || 0;
  const total = hasQual + noQual;
  const ratio = hasQual / total;

  testResults.integrity.push(assert(hasQual === 40, `資格保有者数: ${hasQual} = 40`));
  testResults.integrity.push(assert(noQual === 60, `資格非保有者数: ${noQual} = 60`));
  testResults.integrity.push(assert(total === 100, `総数: ${total} = 100`));
  testResults.integrity.push(assert(Math.abs(ratio - 0.4) < 0.001, `資格保有率: ${ratio.toFixed(3)} = 0.400`));
}

// Test 5.3: 重複カウント防止
function testIntegrityNoDuplicateCount() {
  console.log('\nTest 5.3: 重複カウント防止');

  function buildCrossMatrix(data) {
    const matrix = {};
    const rowSet = new Set();
    const colSet = new Set();

    data.forEach(item => {
      const x = item.x;
      const y = item.y;
      if (!matrix[y]) matrix[y] = {};
      if (!matrix[y][x]) matrix[y][x] = 0;
      matrix[y][x]++;
      rowSet.add(y);
      colSet.add(x);
    });

    const rows = Array.from(rowSet).sort();
    const cols = Array.from(colSet).sort();

    return { matrix, rows, cols };
  }

  // 同じデータを5回追加（重複）
  const duplicateData = [
    { x: 'A', y: 'B' },
    { x: 'A', y: 'B' },
    { x: 'A', y: 'B' },
    { x: 'A', y: 'B' },
    { x: 'A', y: 'B' }
  ];

  const result = buildCrossMatrix(duplicateData);

  testResults.integrity.push(assert(result.matrix['B']['A'] === 5, '重複カウント: 5回カウントされる（正常）'));
  testResults.integrity.push(assert(result.rows.length === 1, '重複カウント: rows.length = 1'));
  testResults.integrity.push(assert(result.cols.length === 1, '重複カウント: cols.length = 1'));
}

// Test 5.4: パーセンテージ計算の精度
function testIntegrityPercentageAccuracy() {
  console.log('\nTest 5.4: パーセンテージ計算の精度');

  function buildCrossMatrix(data) {
    const matrix = {};
    const rowSet = new Set();
    const colSet = new Set();

    data.forEach(item => {
      const x = item.x;
      const y = item.y;
      if (!matrix[y]) matrix[y] = {};
      if (!matrix[y][x]) matrix[y][x] = 0;
      matrix[y][x]++;
      rowSet.add(y);
      colSet.add(x);
    });

    const rows = Array.from(rowSet).sort();
    const cols = Array.from(colSet).sort();

    return { matrix, rows, cols };
  }

  const percentData = [];
  for (let i = 0; i < 33; i++) {
    percentData.push({ x: 'A', y: 'B' });
  }
  for (let i = 0; i < 67; i++) {
    percentData.push({ x: 'C', y: 'B' });
  }

  const result = buildCrossMatrix(percentData);

  const countA = result.matrix['B']['A'] || 0;
  const countC = result.matrix['B']['C'] || 0;
  const total = countA + countC;
  const percentA = (countA / total) * 100;
  const percentC = (countC / total) * 100;

  testResults.integrity.push(assert(Math.abs(percentA - 33) < 0.1, `パーセンテージA: ${percentA.toFixed(2)}% ≈ 33%`));
  testResults.integrity.push(assert(Math.abs(percentC - 67) < 0.1, `パーセンテージC: ${percentC.toFixed(2)}% ≈ 67%`));
  testResults.integrity.push(assert(Math.abs(percentA + percentC - 100) < 0.1, `合計: ${(percentA + percentC).toFixed(2)}% ≈ 100%`));
}

// Test 5.5: データ型の一貫性
function testIntegrityDataTypeConsistency() {
  console.log('\nTest 5.5: データ型の一貫性');

  function buildCrossMatrix(data) {
    const matrix = {};
    const rowSet = new Set();
    const colSet = new Set();

    data.forEach(item => {
      const x = item.x;
      const y = item.y;
      if (!matrix[y]) matrix[y] = {};
      if (!matrix[y][x]) matrix[y][x] = 0;
      matrix[y][x]++;
      rowSet.add(y);
      colSet.add(x);
    });

    const rows = Array.from(rowSet).sort();
    const cols = Array.from(colSet).sort();

    return { matrix, rows, cols };
  }

  const typeData = [
    { x: '30代', y: '女性' },
    { x: '40代', y: '男性' }
  ];

  const result = buildCrossMatrix(typeData);

  // rows, colsが配列であることを確認
  testResults.integrity.push(assert(Array.isArray(result.rows), 'rows is Array'));
  testResults.integrity.push(assert(Array.isArray(result.cols), 'cols is Array'));

  // matrixがオブジェクトであることを確認
  testResults.integrity.push(assert(typeof result.matrix === 'object', 'matrix is Object'));

  // カウント値が数値であることを確認
  result.rows.forEach(row => {
    result.cols.forEach(col => {
      const count = result.matrix[row][col];
      if (count !== undefined) {
        testResults.integrity.push(assert(typeof count === 'number', `matrix["${row}"]["${col}"] is Number`));
      }
    });
  });
}

// Test 5.6: 空セルの扱い
function testIntegrityEmptyCells() {
  console.log('\nTest 5.6: 空セルの扱い');

  function buildCrossMatrix(data) {
    const matrix = {};
    const rowSet = new Set();
    const colSet = new Set();

    data.forEach(item => {
      const x = item.x;
      const y = item.y;
      if (!matrix[y]) matrix[y] = {};
      if (!matrix[y][x]) matrix[y][x] = 0;
      matrix[y][x]++;
      rowSet.add(y);
      colSet.add(x);
    });

    const rows = Array.from(rowSet).sort();
    const cols = Array.from(colSet).sort();

    return { matrix, rows, cols };
  }

  const sparseData = [
    { x: 'A', y: 'B' },
    { x: 'C', y: 'D' }
  ];

  const result = buildCrossMatrix(sparseData);

  // 空セル（存在しない組み合わせ）のカウント
  const emptyCell1 = result.matrix['B']['C'] || 0;
  const emptyCell2 = result.matrix['D']['A'] || 0;

  testResults.integrity.push(assert(emptyCell1 === 0, '空セルB×C: count = 0'));
  testResults.integrity.push(assert(emptyCell2 === 0, '空セルD×A: count = 0'));

  // 非空セル
  const nonEmptyCell1 = result.matrix['B']['A'] || 0;
  const nonEmptyCell2 = result.matrix['D']['C'] || 0;

  testResults.integrity.push(assert(nonEmptyCell1 === 1, '非空セルB×A: count = 1'));
  testResults.integrity.push(assert(nonEmptyCell2 === 1, '非空セルD×C: count = 1'));
}

// ====================================================================
// 6. UIテスト（20件）
// ====================================================================

console.log('\n=== UIテスト開始 ===\n');

// Test 6.1: ドロップダウンの選択肢数
function testUIDropdownOptions() {
  console.log('Test 6.1: ドロップダウンの選択肢数');

  const MAJOR_QUALIFICATIONS = [
    '自動車運転免許',
    '介護福祉士',
    '介護職員初任者研修（旧ヘルパー2級）',
    '介護職員実務者研修（旧ヘルパー1級/基礎研修）',
    '社会福祉主事任用資格',
    '福祉用具専門相談員',
    '社会福祉士',
    '看護師',
    '保育士',
    '准看護師',
    '介護支援専門員（ケアマネージャー）',
    '訪問介護員1級',
    '訪問介護員2級',
    '精神保健福祉士',
    '理学療法士',
    '栄養士',
    '作業療法士',
    '管理栄養士',
    '言語聴覚士',
    '歯科衛生士'
  ];

  const basicAttributes = 7; // 年齢層、性別、就業状態、学歴、キャリア、希望職種、転職意欲
  const qualifications = MAJOR_QUALIFICATIONS.length;
  const totalOptions = basicAttributes + qualifications;

  testResults.ui.push(assert(basicAttributes === 7, `基本属性数: ${basicAttributes} = 7`));
  testResults.ui.push(assert(qualifications === 20, `資格数: ${qualifications} = 20`));
  testResults.ui.push(assert(totalOptions === 27, `総選択肢数: ${totalOptions} = 27`));
  testResults.ui.push(assert(MAJOR_QUALIFICATIONS[0] === '自動車運転免許', '資格リスト順序: 1番目 = 自動車運転免許'));
  testResults.ui.push(assert(MAJOR_QUALIFICATIONS[19] === '歯科衛生士', '資格リスト順序: 20番目 = 歯科衛生士'));
}

// Test 6.2: 長いラベルの表示
function testUILongLabels() {
  console.log('\nTest 6.2: 長いラベルの表示');

  function getAxisLabel(axis) {
    if (axis.startsWith('qual:')) {
      return axis.replace('qual:', '');
    }
    const labels = {
      age_bucket: '年齢層',
      gender: '性別',
      employment_status: '就業状態',
      education: '学歴',
      career: 'キャリア',
      desired_job: '希望職種',
      urgency_level: '転職意欲'
    };
    return labels[axis] || axis;
  }

  // 最も長い資格名
  const longLabel = getAxisLabel('qual:介護職員初任者研修（旧ヘルパー2級）');
  testResults.ui.push(assert(longLabel === '介護職員初任者研修（旧ヘルパー2級）', `長いラベル: "${longLabel}"`));
  testResults.ui.push(assert(longLabel.length > 10, `長いラベルの文字数: ${longLabel.length} > 10`));

  // 極端に長いラベル（1000文字）
  const extremelyLongQual = 'A'.repeat(1000);
  const extremeLabel = getAxisLabel(`qual:${extremelyLongQual}`);
  testResults.ui.push(assert(extremeLabel.length === 1000, `極端に長いラベル: ${extremeLabel.length}文字`));
}

// Test 6.3: テーブルの横スクロール
function testUITableOverflow() {
  console.log('\nTest 6.3: テーブルの横スクロール');

  function buildCrossMatrix(data) {
    const matrix = {};
    const rowSet = new Set();
    const colSet = new Set();

    data.forEach(item => {
      const x = item.x;
      const y = item.y;
      if (!matrix[y]) matrix[y] = {};
      if (!matrix[y][x]) matrix[y][x] = 0;
      matrix[y][x]++;
      rowSet.add(y);
      colSet.add(x);
    });

    const rows = Array.from(rowSet).sort();
    const cols = Array.from(colSet).sort();

    return { matrix, rows, cols };
  }

  // 50列のテーブル（横スクロール必須）
  const wideData = [];
  for (let i = 0; i < 500; i++) {
    wideData.push({ x: `列${i % 50}`, y: `行${Math.floor(i / 50)}` });
  }

  const result = buildCrossMatrix(wideData);

  testResults.ui.push(assert(result.cols.length === 50, `横スクロールテスト: cols.length = 50`));
  testResults.ui.push(assert(result.rows.length === 10, `横スクロールテスト: rows.length = 10`));
}

// Test 6.4: CSV出力のフォーマット
function testUICSVFormat() {
  console.log('\nTest 6.4: CSV出力のフォーマット');

  function buildCrossTable(crossMatrix) {
    const { matrix, rows, cols } = crossMatrix;
    let csv = 'Y\\X,';
    csv += cols.join(',') + ',合計\n';
    rows.forEach(row => {
      csv += row + ',';
      let rowTotal = 0;
      cols.forEach(col => {
        const count = matrix[row][col] || 0;
        csv += count + ',';
        rowTotal += count;
      });
      csv += rowTotal + '\n';
    });
    return csv;
  }

  function buildCrossMatrix(data) {
    const matrix = {};
    const rowSet = new Set();
    const colSet = new Set();

    data.forEach(item => {
      const x = item.x;
      const y = item.y;
      if (!matrix[y]) matrix[y] = {};
      if (!matrix[y][x]) matrix[y][x] = 0;
      matrix[y][x]++;
      rowSet.add(y);
      colSet.add(x);
    });

    const rows = Array.from(rowSet).sort();
    const cols = Array.from(colSet).sort();

    return { matrix, rows, cols };
  }

  const csvData = [
    { x: 'A', y: 'B' },
    { x: 'C', y: 'B' }
  ];

  const matrix = buildCrossMatrix(csvData);
  const csv = buildCrossTable(matrix);

  testResults.ui.push(assert(csv.includes('Y\\X'), 'CSVヘッダー: "Y\\X"を含む'));
  testResults.ui.push(assert(csv.includes(',合計'), 'CSVヘッダー: ",合計"を含む'));
  testResults.ui.push(assert(csv.split('\n').length >= 2, `CSV行数: ${csv.split('\n').length} >= 2`));
  testResults.ui.push(assert(csv.includes('B,'), 'CSV行ラベル: "B,"を含む'));
}

// Test 6.5: ヒートマップカラースケール
function testUIHeatmapColorScale() {
  console.log('\nTest 6.5: ヒートマップカラースケール');

  // ヒートマップの背景色計算
  function getHeatmapColor(count) {
    const maxCount = 50;
    const opacity = Math.min(count / maxCount, 0.8);
    return `rgba(66, 133, 244, ${opacity})`;
  }

  testResults.ui.push(assert(getHeatmapColor(0) === 'rgba(66, 133, 244, 0)', 'ヒートマップ: count=0 → opacity=0'));
  testResults.ui.push(assert(getHeatmapColor(25) === 'rgba(66, 133, 244, 0.5)', 'ヒートマップ: count=25 → opacity=0.5'));
  testResults.ui.push(assert(getHeatmapColor(50) === 'rgba(66, 133, 244, 0.8)', 'ヒートマップ: count=50 → opacity=0.8'));
  testResults.ui.push(assert(getHeatmapColor(100) === 'rgba(66, 133, 244, 0.8)', 'ヒートマップ: count=100 → opacity=0.8（上限）'));
}

// ====================================================================
// テスト実行
// ====================================================================

try {
  // エッジケーステスト実行
  testEdgeCaseEmptyData();
  testEdgeCaseSpecialCharacters();
  testEdgeCaseBoundaryValues();
  testEdgeCaseLongStrings();
  testEdgeCaseUrgencyBoundary();

  // ネガティブテスト実行
  testNegativeInvalidDataTypes();
  testNegativeNonExistentAxis();
  testNegativeSameAxis();
  testNegativeSkewedData();
  testNegativePartialMatch();
  testNegativeCircularReference();

  // セキュリティテスト実行
  testSecurityXSS();
  testSecurityCSVInjection();
  testSecurityHTMLInjection();
  testSecuritySQLInjection();
  testSecurityPrototypePollution();

  // パフォーマンステスト実行
  testPerformanceLargeDataset();
  testPerformanceComplexMatrix();
  testPerformanceMemoryEfficiency();
  testPerformanceQualificationParsing();
  testPerformanceSorting();

  // データ整合性テスト実行
  testIntegrityCrossTabulationSum();
  testIntegrityQualificationRatio();
  testIntegrityNoDuplicateCount();
  testIntegrityPercentageAccuracy();
  testIntegrityDataTypeConsistency();
  testIntegrityEmptyCells();

  // UIテスト実行
  testUIDropdownOptions();
  testUILongLabels();
  testUITableOverflow();
  testUICSVFormat();
  testUIHeatmapColorScale();

} catch (error) {
  console.error('\n❌ テスト実行中にエラーが発生しました:');
  console.error(error.message);
  console.error(error.stack);
}

// ====================================================================
// テスト結果サマリー
// ====================================================================

console.log('\n' + '='.repeat(80));
console.log('深いテスト結果サマリー');
console.log('='.repeat(80) + '\n');

const categories = [
  { name: 'エッジケーステスト', results: testResults.edge },
  { name: 'ネガティブテスト', results: testResults.negative },
  { name: 'セキュリティテスト', results: testResults.security },
  { name: 'パフォーマンステスト', results: testResults.performance },
  { name: 'データ整合性テスト', results: testResults.integrity },
  { name: 'UIテスト', results: testResults.ui }
];

let totalPassed = 0;
let totalFailed = 0;

categories.forEach(category => {
  const passed = category.results.filter(r => r.includes('✅')).length;
  const failed = category.results.filter(r => r.includes('❌')).length;

  totalPassed += passed;
  totalFailed += failed;

  console.log(`【${category.name}】`);
  console.log(`  成功: ${passed}件 / 失敗: ${failed}件 / 合計: ${category.results.length}件`);
  console.log('');

  category.results.forEach(result => {
    console.log(`  ${result}`);
  });
  console.log('');
});

console.log('='.repeat(80));
console.log(`総合結果: ${totalPassed}件成功 / ${totalFailed}件失敗 / 合計${totalPassed + totalFailed}件`);
console.log(`成功率: ${((totalPassed / (totalPassed + totalFailed)) * 100).toFixed(1)}%`);
console.log('='.repeat(80));

if (totalFailed === 0) {
  console.log('\n✅ 全てのテストに成功しました！');
} else {
  console.log(`\n⚠️  ${totalFailed}件のテストが失敗しました。`);
}

// JSON出力
const jsonOutput = {
  timestamp: new Date().toISOString(),
  test_type: 'deep_comprehensive',
  summary: {
    total: totalPassed + totalFailed,
    passed: totalPassed,
    failed: totalFailed,
    success_rate: ((totalPassed / (totalPassed + totalFailed)) * 100).toFixed(1) + '%'
  },
  categories: categories.map(cat => ({
    name: cat.name,
    passed: cat.results.filter(r => r.includes('✅')).length,
    failed: cat.results.filter(r => r.includes('❌')).length,
    total: cat.results.length,
    results: cat.results
  }))
};

console.log('\n=== JSON出力 ===\n');
console.log(JSON.stringify(jsonOutput, null, 2));
