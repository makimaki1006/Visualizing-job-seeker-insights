/**
 * GAS市町村別ペルソナ分析ロジックテスト
 * テスト範囲: 難易度スコア計算、市場規模カテゴリ判定、年齢グループ抽出
 */

// ===== GASロジックのシミュレーション =====

// 難易度スコア計算（市町村内シェアベース）
function calculateDifficultyScoreMunicipality(params) {
  // 資格数スコア（0-40点）
  const qualScore = Math.min(params.avgQualifications * 15, 40);

  // 移動性スコア（0-25点）
  const mobilityScore = Math.min(params.avgDesiredLocations * 8, 25);

  // 市場規模スコア（0-20点、市町村内シェアが小さいほど高得点）
  const sizeScore = Math.max(0, 20 - params.marketSharePct * 2);

  // 年齢スコア（0-10点）
  const ageScore = getAgeScore(params.avgAge);

  // 性別偏りスコア（0-5点）
  const genderScore = Math.abs(params.femaleRatio - 0.5) * 10;

  const totalScore = qualScore + mobilityScore + sizeScore + ageScore + genderScore;
  return Math.min(Math.round(totalScore), 100);
}

// 年齢スコア
function getAgeScore(avgAge) {
  if (avgAge < 25) return 5;  // 若年層：やや難
  if (avgAge < 35) return 3;  // 若手：普通
  if (avgAge < 50) return 4;  // 中堅：やや難
  if (avgAge < 60) return 7;  // シニア：難
  return 10;  // 高齢：最難
}

// 難易度レベル判定
function getDifficultyLevel(score) {
  if (score >= 80) return 'S級（最難）';
  if (score >= 65) return 'A級（難）';
  if (score >= 50) return 'B級（やや難）';
  if (score >= 35) return 'C級（普通）';
  if (score >= 20) return 'D級（やや易）';
  return 'E級（易）';
}

// 市町村内シェアベースの市場規模カテゴリ
function getMarketSizeCategoryMunicipality(marketSharePct) {
  if (marketSharePct >= 20.0) return '超大規模（20%以上）';
  if (marketSharePct >= 15.0) return '大規模（15～19%）';
  if (marketSharePct >= 10.0) return '中規模（10～14%）';
  if (marketSharePct >= 7.0) return 'やや小規模（7～9%）';
  if (marketSharePct >= 4.0) return '小規模（4～6%）';
  if (marketSharePct >= 2.0) return '超小規模（2～3%）';
  return 'ニッチ（2%未満）';
}

// ペルソナ名から年齢グループ抽出
function getAgeGroup(age) {
  if (age < 25) return '新卒層（～24歳）';
  if (age < 30) return '若手層（25～29歳）';
  if (age < 35) return '若手中堅層（30～34歳）';
  if (age < 40) return '中堅層（35～39歳）';
  if (age < 45) return 'ミドル層（40～44歳）';
  if (age < 50) return 'シニアミドル層（45～49歳）';
  if (age < 55) return 'プレシニア層（50～54歳）';
  if (age < 60) return 'シニア層（55～59歳）';
  if (age < 65) return 'アクティブシニア層（60～64歳）';
  return '高齢層（65歳～）';
}

// ===== テストケース =====

const testCases = [
  {
    name: '京都市伏見区: 50代・男性・国家資格あり（超レア）',
    input: {
      avgQualifications: 3.0,
      avgDesiredLocations: 3.67,
      femaleRatio: 0.0,  // 男性
      marketSharePct: 0.172,  // 1,748人中3人
      avgAge: 54.3
    },
    expected: {
      scoreRange: [95, 100],  // 97点前後（S級）
      difficultyLevel: 'S級（最難）',
      marketSizeCategory: 'ニッチ（2%未満）'
    }
  },
  {
    name: '京都市伏見区: 50代・女性・国家資格なし（最多）',
    input: {
      avgQualifications: 1.75,
      avgDesiredLocations: 3.75,
      femaleRatio: 1.0,  // 女性
      marketSharePct: 19.45,  // 1,748人中340人
      avgAge: 54.4
    },
    expected: {
      scoreRange: [60, 70],  // 63点前後（B級）
      difficultyLevel: 'B級（やや難）',
      marketSizeCategory: '大規模（15～19%）'
    }
  },
  {
    name: '中規模市町村: 40代・男性・国家資格なし（中程度）',
    input: {
      avgQualifications: 2.0,
      avgDesiredLocations: 5.0,
      femaleRatio: 0.0,
      marketSharePct: 10.0,  // 市町村内10%
      avgAge: 45
    },
    expected: {
      scoreRange: [45, 65],  // B級～C級
      difficultyLevel: 'B級（やや難）',
      marketSizeCategory: '中規模（10～14%）'
    }
  },
  {
    name: '小規模市町村: 20代・女性・国家資格あり（若手・高資格）',
    input: {
      avgQualifications: 2.5,
      avgDesiredLocations: 8.0,
      femaleRatio: 1.0,
      marketSharePct: 5.0,  // 市町村内5%
      avgAge: 25
    },
    expected: {
      scoreRange: [78, 85],  // 81点前後（S級）
      difficultyLevel: 'S級（最難）',
      marketSizeCategory: '小規模（4～6%）'
    }
  }
];

// ===== テスト実行 =====

function runTests() {
  console.log('='.repeat(80));
  console.log('GAS市町村別ペルソナ分析ロジックテスト');
  console.log('='.repeat(80));
  console.log();

  let passed = 0;
  let failed = 0;
  const results = [];

  testCases.forEach((testCase, index) => {
    console.log(`[TEST ${index + 1}] ${testCase.name}`);

    try {
      // 難易度スコア計算
      const score = calculateDifficultyScoreMunicipality(testCase.input);
      const level = getDifficultyLevel(score);
      const marketCategory = getMarketSizeCategoryMunicipality(testCase.input.marketSharePct);

      // 検証
      const scoreInRange = score >= testCase.expected.scoreRange[0] && score <= testCase.expected.scoreRange[1];
      const levelMatch = level === testCase.expected.difficultyLevel;
      const categoryMatch = marketCategory === testCase.expected.marketSizeCategory;

      if (scoreInRange && levelMatch && categoryMatch) {
        console.log('  [PASS]');
        console.log(`    難易度スコア: ${score}点 (期待範囲: ${testCase.expected.scoreRange[0]}-${testCase.expected.scoreRange[1]})`);
        console.log(`    難易度レベル: ${level} (期待: ${testCase.expected.difficultyLevel})`);
        console.log(`    市場規模: ${marketCategory} (期待: ${testCase.expected.marketSizeCategory})`);
        passed++;
        results.push({
          test: testCase.name,
          status: 'PASS',
          score: score,
          level: level,
          marketCategory: marketCategory
        });
      } else {
        console.log('  [FAIL]');
        if (!scoreInRange) {
          console.log(`    難易度スコア不一致: 実際=${score}, 期待範囲=${testCase.expected.scoreRange[0]}-${testCase.expected.scoreRange[1]}`);
        }
        if (!levelMatch) {
          console.log(`    難易度レベル不一致: 実際=${level}, 期待=${testCase.expected.difficultyLevel}`);
        }
        if (!categoryMatch) {
          console.log(`    市場規模不一致: 実際=${marketCategory}, 期待=${testCase.expected.marketSizeCategory}`);
        }
        failed++;
        results.push({
          test: testCase.name,
          status: 'FAIL',
          score: score,
          level: level,
          marketCategory: marketCategory,
          expected: testCase.expected
        });
      }
    } catch (error) {
      console.log('  [ERROR]');
      console.log(`    エラー: ${error.message}`);
      failed++;
      results.push({
        test: testCase.name,
        status: 'ERROR',
        error: error.message
      });
    }
    console.log();
  });

  // サマリー
  console.log('='.repeat(80));
  console.log('テスト結果サマリー');
  console.log('='.repeat(80));
  console.log(`[OK] 成功: ${passed}/${testCases.length}`);
  console.log(`[NG] 失敗: ${failed}/${testCases.length}`);
  console.log(`成功率: ${(passed/testCases.length*100).toFixed(1)}%`);
  console.log();

  // 結果をJSONで保存
  const fs = require('fs');
  const path = require('path');
  const resultPath = path.join(__dirname, 'results', 'GAS_MUNICIPALITY_LOGIC_TEST_RESULTS.json');

  // ディレクトリ作成
  const resultDir = path.dirname(resultPath);
  if (!fs.existsSync(resultDir)) {
    fs.mkdirSync(resultDir, { recursive: true });
  }

  fs.writeFileSync(resultPath, JSON.stringify({
    total_tests: testCases.length,
    passed: passed,
    failed: failed,
    success_rate: passed/testCases.length*100,
    test_results: results
  }, null, 2));

  console.log(`[FILE] テスト結果を保存: ${resultPath}`);

  return passed === testCases.length;
}

// 実行
if (require.main === module) {
  const success = runTests();
  process.exit(success ? 0 : 1);
}

module.exports = {
  calculateDifficultyScoreMunicipality,
  getAgeScore,
  getDifficultyLevel,
  getMarketSizeCategoryMunicipality,
  getAgeGroup,
  runTests
};
