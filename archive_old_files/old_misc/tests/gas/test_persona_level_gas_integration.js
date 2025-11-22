/**
 * PersonaLevel統合シート GAS統合テスト
 *
 * 実際のGoogleスプレッドシート環境で動作するテストスクリプト
 * GASエディタにコピー&ペーストして実行してください
 *
 * @version 1.0
 * @date 2025-11-09
 */

/**
 * メインテスト実行関数
 * GASエディタで実行: runPersonaLevelIntegrationTests()
 */
function runPersonaLevelIntegrationTests() {
  Logger.log('╔════════════════════════════════════════════════════════════════════════════════╗');
  Logger.log('║              PersonaLevel統合シート GAS統合テストスイート                      ║');
  Logger.log('╚════════════════════════════════════════════════════════════════════════════════╝');
  Logger.log('');

  const testResults = {
    suiteName: 'PersonaLevel統合シート GAS統合テスト',
    timestamp: new Date().toISOString(),
    tests: [],
    summary: {
      total: 0,
      passed: 0,
      failed: 0
    }
  };

  // 全テスト実行
  testResults.tests.push(test1_CheckSheetExists('京都府'));
  testResults.tests.push(test2_GetPersonaLevelData('京都府'));
  testResults.tests.push(test3_FilterPersonaLevelData('京都府'));
  testResults.tests.push(test4_AnalyzePersonaDifficulty('京都府'));
  testResults.tests.push(test5_GetMunicipalityRanking('京都府'));
  testResults.tests.push(test6_PerformanceTest('京都府'));
  testResults.tests.push(test7_ErrorHandling());
  testResults.tests.push(test8_GetAvailablePrefectures());

  // サマリー計算
  testResults.tests.forEach(function(test) {
    testResults.summary.total++;
    if (test.status === 'PASS') {
      testResults.summary.passed++;
    } else {
      testResults.summary.failed++;
    }
  });

  // 結果表示
  displayTestResults(testResults);

  return testResults;
}

/**
 * テスト1: シートの存在確認
 */
function test1_CheckSheetExists(prefecture) {
  Logger.log('\n=== テスト1: シートの存在確認 ===');

  const result = {
    testName: 'test1_CheckSheetExists',
    description: 'PersonaLevel統合シートが存在するか確認',
    status: 'FAIL',
    assertions: [],
    duration: 0
  };

  const startTime = new Date().getTime();

  try {
    const exists = checkPersonaLevelSheetExists(prefecture);

    result.assertions.push({
      assertion: 'シート存在確認',
      expected: true,
      actual: exists,
      passed: exists === true
    });

    if (exists) {
      Logger.log('  ✅ シート「PersonaLevel_' + prefecture + '」が存在します');
      result.status = 'PASS';
    } else {
      Logger.log('  ❌ シート「PersonaLevel_' + prefecture + '」が見つかりません');
    }

  } catch (e) {
    Logger.log('  ❌ エラー: ' + e.toString());
    result.assertions.push({
      assertion: 'エラーなし',
      expected: 'エラーなし',
      actual: e.toString(),
      passed: false
    });
  }

  const endTime = new Date().getTime();
  result.duration = (endTime - startTime) / 1000;

  return result;
}

/**
 * テスト2: ペルソナレベルデータ取得
 */
function test2_GetPersonaLevelData(prefecture) {
  Logger.log('\n=== テスト2: ペルソナレベルデータ取得 ===');

  const result = {
    testName: 'test2_GetPersonaLevelData',
    description: 'getPersonaLevelData()が正常に動作するか確認',
    status: 'FAIL',
    assertions: [],
    duration: 0,
    performance: {}
  };

  const startTime = new Date().getTime();

  try {
    const data = getPersonaLevelData(prefecture);

    // アサーション1: データが取得できたか
    result.assertions.push({
      assertion: 'データ取得成功',
      expected: 'オブジェクト',
      actual: typeof data,
      passed: typeof data === 'object' && data !== null
    });

    // アサーション2: personasプロパティが配列か
    result.assertions.push({
      assertion: 'personasが配列',
      expected: true,
      actual: Array.isArray(data.personas),
      passed: Array.isArray(data.personas)
    });

    // アサーション3: ペルソナ件数が1件以上か
    const personaCount = data.personas.length;
    result.assertions.push({
      assertion: 'ペルソナ件数 > 0',
      expected: '> 0',
      actual: personaCount,
      passed: personaCount > 0
    });

    // アサーション4: metadataが存在するか
    result.assertions.push({
      assertion: 'metadataが存在',
      expected: true,
      actual: data.metadata !== undefined,
      passed: data.metadata !== undefined
    });

    // アサーション5: ロード時間が3秒未満か
    const loadTime = data.metadata.loadTime;
    result.assertions.push({
      assertion: 'ロード時間 < 3秒',
      expected: '< 3秒',
      actual: loadTime + '秒',
      passed: loadTime < 3.0
    });

    result.performance['データロード時間'] = loadTime + '秒';
    result.performance['ペルソナ件数'] = personaCount;
    result.performance['列数'] = data.metadata.colCount;

    // すべてのアサーションが通ればPASS
    const allPassed = result.assertions.every(function(a) { return a.passed; });
    if (allPassed) {
      result.status = 'PASS';
      Logger.log('  ✅ データ取得成功: ' + personaCount + '件、ロード時間: ' + loadTime + '秒');
    } else {
      Logger.log('  ❌ 一部のアサーションが失敗しました');
    }

  } catch (e) {
    Logger.log('  ❌ エラー: ' + e.toString());
    result.assertions.push({
      assertion: 'エラーなし',
      expected: 'エラーなし',
      actual: e.toString(),
      passed: false
    });
  }

  const endTime = new Date().getTime();
  result.duration = (endTime - startTime) / 1000;

  return result;
}

/**
 * テスト3: フィルタリング
 */
function test3_FilterPersonaLevelData(prefecture) {
  Logger.log('\n=== テスト3: フィルタリング ===');

  const result = {
    testName: 'test3_FilterPersonaLevelData',
    description: 'filterPersonaLevelData()が正常に動作するか確認',
    status: 'FAIL',
    assertions: [],
    duration: 0,
    performance: {}
  };

  const startTime = new Date().getTime();

  try {
    const filters = {
      age_group: '50代',
      gender: '女性',
      has_national_license: false
    };

    const filtered = filterPersonaLevelData(prefecture, filters);

    // アサーション1: データが取得できたか
    result.assertions.push({
      assertion: 'データ取得成功',
      expected: 'オブジェクト',
      actual: typeof filtered,
      passed: typeof filtered === 'object' && filtered !== null
    });

    // アサーション2: personasプロパティが配列か
    result.assertions.push({
      assertion: 'personasが配列',
      expected: true,
      actual: Array.isArray(filtered.personas),
      passed: Array.isArray(filtered.personas)
    });

    // アサーション3: フィルタ時間が1秒未満か
    const filterTime = filtered.metadata.filterTime;
    result.assertions.push({
      assertion: 'フィルタ時間 < 1秒',
      expected: '< 1秒',
      actual: filterTime + '秒',
      passed: filterTime < 1.0
    });

    // アサーション4: フィルタ後の件数が元データより少ないか等しいか
    const originalCount = filtered.metadata.originalCount;
    const filteredCount = filtered.metadata.filteredCount;
    result.assertions.push({
      assertion: 'フィルタ後 <= 元データ',
      expected: '<= ' + originalCount,
      actual: filteredCount,
      passed: filteredCount <= originalCount
    });

    result.performance['フィルタ時間'] = filterTime + '秒';
    result.performance['元データ件数'] = originalCount;
    result.performance['フィルタ後件数'] = filteredCount;

    const allPassed = result.assertions.every(function(a) { return a.passed; });
    if (allPassed) {
      result.status = 'PASS';
      Logger.log('  ✅ フィルタリング成功: ' + originalCount + '件 → ' + filteredCount + '件、処理時間: ' + filterTime + '秒');
    } else {
      Logger.log('  ❌ 一部のアサーションが失敗しました');
    }

  } catch (e) {
    Logger.log('  ❌ エラー: ' + e.toString());
    result.assertions.push({
      assertion: 'エラーなし',
      expected: 'エラーなし',
      actual: e.toString(),
      passed: false
    });
  }

  const endTime = new Date().getTime();
  result.duration = (endTime - startTime) / 1000;

  return result;
}

/**
 * テスト4: 難易度分析
 */
function test4_AnalyzePersonaDifficulty(prefecture) {
  Logger.log('\n=== テスト4: 難易度分析 ===');

  const result = {
    testName: 'test4_AnalyzePersonaDifficulty',
    description: 'analyzePersonaDifficulty()が正常に動作するか確認',
    status: 'FAIL',
    assertions: [],
    duration: 0,
    performance: {}
  };

  const startTime = new Date().getTime();

  try {
    const filters = {
      age_group: '50代',
      gender: '女性',
      has_national_license: true
    };

    const analysisStart = new Date().getTime();
    const difficulty = analyzePersonaDifficulty(prefecture, filters);
    const analysisEnd = new Date().getTime();
    const analysisTime = (analysisEnd - analysisStart) / 1000;

    // アサーション1: データが取得できたか
    result.assertions.push({
      assertion: 'データ取得成功',
      expected: 'オブジェクト',
      actual: typeof difficulty,
      passed: typeof difficulty === 'object' && difficulty !== null
    });

    // アサーション2: 分析時間が1秒未満か
    result.assertions.push({
      assertion: '分析時間 < 1秒',
      expected: '< 1秒',
      actual: analysisTime + '秒',
      passed: analysisTime < 1.0
    });

    // アサーション3: 難易度レベルが取得できたか
    result.assertions.push({
      assertion: '難易度レベル取得',
      expected: '文字列',
      actual: typeof difficulty.difficultyLevel,
      passed: typeof difficulty.difficultyLevel === 'string' && difficulty.difficultyLevel !== ''
    });

    // アサーション4: avgRarityScoreが数値または null か
    const avgRarityScore = difficulty.avgRarityScore;
    result.assertions.push({
      assertion: 'avgRarityScoreが数値またはnull',
      expected: '数値またはnull',
      actual: avgRarityScore === null ? 'null' : typeof avgRarityScore,
      passed: avgRarityScore === null || typeof avgRarityScore === 'number'
    });

    result.performance['分析時間'] = analysisTime + '秒';
    result.performance['マッチ件数'] = difficulty.matchCount;
    result.performance['平均希少性スコア'] = avgRarityScore;
    result.performance['難易度レベル'] = difficulty.difficultyLevel;

    const allPassed = result.assertions.every(function(a) { return a.passed; });
    if (allPassed) {
      result.status = 'PASS';
      Logger.log('  ✅ 難易度分析成功: ' + difficulty.difficultyLevel + '、スコア: ' + avgRarityScore + '、処理時間: ' + analysisTime + '秒');
    } else {
      Logger.log('  ❌ 一部のアサーションが失敗しました');
    }

  } catch (e) {
    Logger.log('  ❌ エラー: ' + e.toString());
    result.assertions.push({
      assertion: 'エラーなし',
      expected: 'エラーなし',
      actual: e.toString(),
      passed: false
    });
  }

  const endTime = new Date().getTime();
  result.duration = (endTime - startTime) / 1000;

  return result;
}

/**
 * テスト5: 市区町村別ランキング
 */
function test5_GetMunicipalityRanking(prefecture) {
  Logger.log('\n=== テスト5: 市区町村別ランキング ===');

  const result = {
    testName: 'test5_GetMunicipalityRanking',
    description: 'getMunicipalityDifficultyRanking()が正常に動作するか確認',
    status: 'FAIL',
    assertions: [],
    duration: 0,
    performance: {}
  };

  const startTime = new Date().getTime();

  try {
    const topN = 10;
    const rankingStart = new Date().getTime();
    const ranking = getMunicipalityDifficultyRanking(prefecture, topN);
    const rankingEnd = new Date().getTime();
    const rankingTime = (rankingEnd - rankingStart) / 1000;

    // アサーション1: ランキングが配列か
    result.assertions.push({
      assertion: 'ランキングが配列',
      expected: true,
      actual: Array.isArray(ranking),
      passed: Array.isArray(ranking)
    });

    // アサーション2: ランキング時間が2秒未満か
    result.assertions.push({
      assertion: 'ランキング時間 < 2秒',
      expected: '< 2秒',
      actual: rankingTime + '秒',
      passed: rankingTime < 2.0
    });

    // アサーション3: ランキング件数が10件以下か
    result.assertions.push({
      assertion: 'ランキング件数 <= 10',
      expected: '<= 10',
      actual: ranking.length,
      passed: ranking.length <= topN
    });

    // アサーション4: スコア降順か
    let isSorted = true;
    for (var i = 0; i < ranking.length - 1; i++) {
      if (ranking[i].avgRarityScore < ranking[i + 1].avgRarityScore) {
        isSorted = false;
        break;
      }
    }
    result.assertions.push({
      assertion: 'スコア降順',
      expected: true,
      actual: isSorted,
      passed: isSorted
    });

    result.performance['ランキング生成時間'] = rankingTime + '秒';
    result.performance['ランキング件数'] = ranking.length;

    const allPassed = result.assertions.every(function(a) { return a.passed; });
    if (allPassed) {
      result.status = 'PASS';
      Logger.log('  ✅ ランキング取得成功: ' + ranking.length + '件、処理時間: ' + rankingTime + '秒');
    } else {
      Logger.log('  ❌ 一部のアサーションが失敗しました');
    }

  } catch (e) {
    Logger.log('  ❌ エラー: ' + e.toString());
    result.assertions.push({
      assertion: 'エラーなし',
      expected: 'エラーなし',
      actual: e.toString(),
      passed: false
    });
  }

  const endTime = new Date().getTime();
  result.duration = (endTime - startTime) / 1000;

  return result;
}

/**
 * テスト6: パフォーマンステスト
 */
function test6_PerformanceTest(prefecture) {
  Logger.log('\n=== テスト6: パフォーマンステスト ===');

  const result = {
    testName: 'test6_PerformanceTest',
    description: '従来方式（21秒）との比較',
    status: 'FAIL',
    assertions: [],
    duration: 0,
    performance: {}
  };

  const startTime = new Date().getTime();

  try {
    // フルフロー実行: データロード → フィルタ → 分析 → ランキング
    const fullFlowStart = new Date().getTime();

    const data = getPersonaLevelData(prefecture);
    const filtered = filterPersonaLevelData(prefecture, { age_group: '50代' });
    const difficulty = analyzePersonaDifficulty(prefecture, { age_group: '50代', gender: '女性' });
    const ranking = getMunicipalityDifficultyRanking(prefecture, 10);

    const fullFlowEnd = new Date().getTime();
    const fullFlowTime = (fullFlowEnd - fullFlowStart) / 1000;

    // アサーション1: フルフロー時間が10秒未満か（従来21秒 → 目標2-3秒）
    result.assertions.push({
      assertion: 'フルフロー時間 < 10秒',
      expected: '< 10秒',
      actual: fullFlowTime + '秒',
      passed: fullFlowTime < 10.0
    });

    // アサーション2: 従来方式（21秒）より大幅に高速か
    const baselineTime = 21.0;
    const improvement = ((baselineTime - fullFlowTime) / baselineTime * 100).toFixed(1);
    result.assertions.push({
      assertion: '改善率 >= 50%',
      expected: '>= 50%',
      actual: improvement + '%',
      passed: parseFloat(improvement) >= 50.0
    });

    result.performance['フルフロー時間'] = fullFlowTime + '秒';
    result.performance['従来方式'] = baselineTime + '秒';
    result.performance['改善率'] = improvement + '%';

    const allPassed = result.assertions.every(function(a) { return a.passed; });
    if (allPassed) {
      result.status = 'PASS';
      Logger.log('  ✅ パフォーマンステスト成功: ' + fullFlowTime + '秒（' + improvement + '%改善）');
    } else {
      Logger.log('  ❌ 一部のアサーションが失敗しました');
    }

  } catch (e) {
    Logger.log('  ❌ エラー: ' + e.toString());
    result.assertions.push({
      assertion: 'エラーなし',
      expected: 'エラーなし',
      actual: e.toString(),
      passed: false
    });
  }

  const endTime = new Date().getTime();
  result.duration = (endTime - startTime) / 1000;

  return result;
}

/**
 * テスト7: エラーハンドリング
 */
function test7_ErrorHandling() {
  Logger.log('\n=== テスト7: エラーハンドリング ===');

  const result = {
    testName: 'test7_ErrorHandling',
    description: '存在しない都道府県やエラー条件での挙動確認',
    status: 'FAIL',
    assertions: [],
    duration: 0
  };

  const startTime = new Date().getTime();

  try {
    // アサーション1: 存在しない都道府県でエラーが発生するか
    let errorCaught = false;
    try {
      getPersonaLevelData('存在しない県');
    } catch (e) {
      errorCaught = true;
      Logger.log('  ✅ 期待通りエラーが発生: ' + e.toString());
    }

    result.assertions.push({
      assertion: '存在しない都道府県でエラー発生',
      expected: true,
      actual: errorCaught,
      passed: errorCaught
    });

    // アサーション2: 空フィルタでも動作するか
    let emptyFilterWorks = false;
    try {
      const emptyFiltered = filterPersonaLevelData('京都府', {});
      emptyFilterWorks = emptyFiltered.personas.length > 0;
      Logger.log('  ✅ 空フィルタで正常動作: ' + emptyFiltered.personas.length + '件');
    } catch (e) {
      Logger.log('  ❌ 空フィルタでエラー: ' + e.toString());
    }

    result.assertions.push({
      assertion: '空フィルタで正常動作',
      expected: true,
      actual: emptyFilterWorks,
      passed: emptyFilterWorks
    });

    const allPassed = result.assertions.every(function(a) { return a.passed; });
    if (allPassed) {
      result.status = 'PASS';
      Logger.log('  ✅ エラーハンドリングテスト成功');
    } else {
      Logger.log('  ❌ 一部のアサーションが失敗しました');
    }

  } catch (e) {
    Logger.log('  ❌ エラー: ' + e.toString());
    result.assertions.push({
      assertion: 'エラーなし',
      expected: 'エラーなし',
      actual: e.toString(),
      passed: false
    });
  }

  const endTime = new Date().getTime();
  result.duration = (endTime - startTime) / 1000;

  return result;
}

/**
 * テスト8: 利用可能な都道府県リスト取得
 */
function test8_GetAvailablePrefectures() {
  Logger.log('\n=== テスト8: 利用可能な都道府県リスト取得 ===');

  const result = {
    testName: 'test8_GetAvailablePrefectures',
    description: 'getAvailablePrefectures()が正常に動作するか確認',
    status: 'FAIL',
    assertions: [],
    duration: 0,
    performance: {}
  };

  const startTime = new Date().getTime();

  try {
    const prefectures = getAvailablePrefectures();

    // アサーション1: 配列が返されるか
    result.assertions.push({
      assertion: '配列が返される',
      expected: true,
      actual: Array.isArray(prefectures),
      passed: Array.isArray(prefectures)
    });

    // アサーション2: 1件以上の都道府県があるか
    result.assertions.push({
      assertion: '都道府県数 > 0',
      expected: '> 0',
      actual: prefectures.length,
      passed: prefectures.length > 0
    });

    result.performance['都道府県数'] = prefectures.length;

    const allPassed = result.assertions.every(function(a) { return a.passed; });
    if (allPassed) {
      result.status = 'PASS';
      Logger.log('  ✅ 都道府県リスト取得成功: ' + prefectures.length + '件');
      Logger.log('  都道府県: ' + prefectures.join(', '));
    } else {
      Logger.log('  ❌ 一部のアサーションが失敗しました');
    }

  } catch (e) {
    Logger.log('  ❌ エラー: ' + e.toString());
    result.assertions.push({
      assertion: 'エラーなし',
      expected: 'エラーなし',
      actual: e.toString(),
      passed: false
    });
  }

  const endTime = new Date().getTime();
  result.duration = (endTime - startTime) / 1000;

  return result;
}

/**
 * テスト結果表示
 */
function displayTestResults(testResults) {
  Logger.log('\n');
  Logger.log('╔════════════════════════════════════════════════════════════════════════════════╗');
  Logger.log('║                              最終テストレポート                                 ║');
  Logger.log('╚════════════════════════════════════════════════════════════════════════════════╝');
  Logger.log('');

  Logger.log('=== テストサマリー ===');
  Logger.log('総テスト数: ' + testResults.summary.total);
  Logger.log('成功: ' + testResults.summary.passed + ' (' + (testResults.summary.passed / testResults.summary.total * 100).toFixed(1) + '%)');
  Logger.log('失敗: ' + testResults.summary.failed + ' (' + (testResults.summary.failed / testResults.summary.total * 100).toFixed(1) + '%)');
  Logger.log('');

  Logger.log('=== テスト別詳細 ===');
  testResults.tests.forEach(function(test, index) {
    Logger.log('\n' + (index + 1) + '. ' + test.testName);
    Logger.log('   説明: ' + test.description);
    Logger.log('   ステータス: ' + (test.status === 'PASS' ? '✅ PASS' : '❌ FAIL'));
    Logger.log('   実行時間: ' + test.duration + '秒');

    if (test.performance) {
      Logger.log('   パフォーマンス:');
      Object.keys(test.performance).forEach(function(key) {
        Logger.log('     - ' + key + ': ' + test.performance[key]);
      });
    }

    Logger.log('   アサーション:');
    test.assertions.forEach(function(assertion) {
      const status = assertion.passed ? '✅' : '❌';
      Logger.log('     ' + status + ' ' + assertion.assertion + ' (期待: ' + assertion.expected + ', 実測: ' + assertion.actual + ')');
    });
  });

  Logger.log('\n');
  Logger.log('=== 本番リリース推奨可否 ===');
  const passRate = testResults.summary.passed / testResults.summary.total * 100;
  if (passRate === 100) {
    Logger.log('✅ 本番リリース推奨: すべてのテストが合格しています（合格率: ' + passRate.toFixed(1) + '%）');
  } else if (passRate >= 80) {
    Logger.log('⚠️ 注意してリリース: 一部テストが失敗していますが、大きな問題はありません（合格率: ' + passRate.toFixed(1) + '%）');
  } else {
    Logger.log('❌ リリース非推奨: 多数のテストが失敗しています。修正が必要です。（合格率: ' + passRate.toFixed(1) + '%）');
  }
}
