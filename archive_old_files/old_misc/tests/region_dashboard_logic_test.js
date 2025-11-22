/**
 * RegionDashboard.gs ロジック簡易テスト
 * Apps Script 環境依存の機能を除いた純粋関数の動作を Node.js 上で検証する。
 */

const fs = require('fs');
const vm = require('vm');

function loadRegionDashboard() {
  const code = fs.readFileSync(
    require('path').join(__dirname, '..', 'gas_files', 'scripts', 'RegionDashboard.gs'),
    'utf8'
  );

  const context = {
    console,
    Math,
    JSON
  };

  vm.createContext(context);
  vm.runInContext(code, context);
  return context;
}

function assertClose(actual, expected, tolerance, message) {
  if (Math.abs(actual - expected) > tolerance) {
    throw new Error(`${message} (expected ${expected}, got ${actual})`);
  }
}

function assertEqual(actual, expected, message) {
  if (actual !== expected) {
    throw new Error(`${message} (expected ${expected}, got ${actual})`);
  }
}

function runTests() {
  const ctx = loadRegionDashboard();

  const sampleRecord = {
    segment_id: 0,
    segment_name: 'テストセグメント',
    count: 2768,
    ratio: 0.37,
    avg_age: 55.4,
    female_ratio: 1.0,
    avg_desired_locations: 2.3,
    avg_qualifications: 2.0,
    __normalized: {
      segmentId: 0,
      segmentName: 'テストセグメント',
      count: 2768,
      percentage: 0.37,
      avgAge: 55.4,
      femaleRatio: 1.0,
      avgDesiredLocations: 2.3,
      avgQualifications: 2.0
    }
  };

  // augmentPersonaDifficulty
  const augmented = ctx.augmentPersonaDifficulty([sampleRecord])[0];
  assertEqual(
    augmented.difficulty_level,
    'B級（やや難）',
    '難易度ランクが期待値と異なります'
  );
  assertClose(
    augmented.difficulty_score,
    60,
    0,
    '難易度スコアが期待値と異なります'
  );

  // calculateDifficultySummary
  const summary = ctx.calculateDifficultySummary([augmented]);
  assertClose(
    summary.averageScore,
    60,
    0,
    '平均難易度スコアが一致しません'
  );
  assertEqual(
    summary.topLevel,
    'B級（やや難）',
    '最難ランクが一致しません'
  );

  // applyPersonaFilters with difficulty filter
  const filtered = ctx.applyPersonaFilters(
    [augmented],
    { difficultyLevel: 'B級（やや難）' }
  );
  assertEqual(filtered.length, 1, '難易度フィルタで該当レコードが取得できません');

  const filteredEmpty = ctx.applyPersonaFilters(
    [augmented],
    { difficultyLevel: 'S級（最難）' }
  );
  assertEqual(filteredEmpty.length, 0, '難易度フィルタで不一致レコードが除外されていません');

  // calculateDifficultyScore（生パラメータ）
  const scoreFromParams = ctx.calculateDifficultyScore({
    avgQualifications: 2.0,
    avgDesiredLocations: 2.3,
    femaleRatio: 1.0,
    count: 2768,
    percentage: 37.0,
    avgAge: 55.4
  });
  assertEqual(scoreFromParams, 60, 'calculateDifficultyScore が期待値と一致しません');

  console.log('✅ RegionDashboard logic tests passed');
}

runTests();
