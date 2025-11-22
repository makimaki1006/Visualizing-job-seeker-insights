/**
 * 包括的パフォーマンステストスイート
 * PersonaLevelDataBridge vs MapCompleteDataBridge の性能比較
 *
 * 測定対象:
 * 1. データロード時間の詳細分析
 * 2. 都道府県別のロード時間比較（小規模・中規模・大規模）
 * 3. フィルタリング性能（1-4条件）
 * 4. 集計・分析性能
 * 5. メモリ使用量推定
 * 6. 従来方式との比較
 * 7. ボトルネック分析
 *
 * @version 1.0
 * @date 2025-11-09
 */

// ============================================================
// テスト設定
// ============================================================

const TEST_CONFIG = {
  prefectures: {
    small: '鳥取県',      // 小規模（想定：50-100行）
    medium: '京都府',     // 中規模（想定：601行）
    large: '東京都'       // 大規模（想定：1,100行）
  },
  iterations: 5,          // 各テストの繰り返し回数
  warmupRuns: 2          // ウォームアップ実行回数
};

// ============================================================
// パフォーマンス測定ユーティリティ
// ============================================================

/**
 * 処理時間を測定
 * @param {Function} fn - 測定対象の関数
 * @return {Object} {result: 戻り値, duration: 実行時間(秒)}
 */
function measureTime(fn) {
  const startTime = new Date().getTime();
  const result = fn();
  const endTime = new Date().getTime();
  const duration = (endTime - startTime) / 1000;

  return {
    result: result,
    duration: duration,
    durationMs: endTime - startTime
  };
}

/**
 * 平均・中央値・標準偏差を計算
 * @param {Array<number>} values
 * @return {Object}
 */
function calculateStats(values) {
  const sorted = values.slice().sort((a, b) => a - b);
  const avg = values.reduce((sum, v) => sum + v, 0) / values.length;
  const median = sorted[Math.floor(sorted.length / 2)];

  // 標準偏差
  const variance = values.reduce((sum, v) => sum + Math.pow(v - avg, 2), 0) / values.length;
  const stdDev = Math.sqrt(variance);

  return {
    avg: avg,
    median: median,
    min: sorted[0],
    max: sorted[sorted.length - 1],
    stdDev: stdDev,
    count: values.length
  };
}

/**
 * データサイズを推定（メモリ使用量）
 * @param {Object} data
 * @return {number} サイズ（KB）
 */
function estimateDataSize(data) {
  const jsonString = JSON.stringify(data);
  return Math.round(jsonString.length / 1024);
}

// ============================================================
// テスト1: データロード時間の詳細分析
// ============================================================

function test1_DataLoadDetailedAnalysis() {
  Logger.log('=== テスト1: データロード時間の詳細分析 ===');

  const prefecture = TEST_CONFIG.prefectures.medium; // 京都府（601行）
  const results = {
    testName: 'データロード時間詳細分析',
    prefecture: prefecture,
    measurements: []
  };

  // ウォームアップ
  for (let i = 0; i < TEST_CONFIG.warmupRuns; i++) {
    getPersonaLevelData(prefecture);
  }

  // 測定実行
  for (let i = 0; i < TEST_CONFIG.iterations; i++) {
    Logger.log(`[テスト1] 実行 ${i + 1}/${TEST_CONFIG.iterations}`);

    const measurement = {};

    // 1. getDataRange() の時間
    const rangeTime = measureTime(() => {
      const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(`PersonaLevel_${prefecture}`);
      return sheet.getDataRange();
    });
    measurement.getDataRange = rangeTime.duration;

    // 2. getValues() の時間
    const valuesTime = measureTime(() => {
      const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(`PersonaLevel_${prefecture}`);
      const range = sheet.getDataRange();
      return range.getValues();
    });
    measurement.getValues = valuesTime.duration;

    // 3. オブジェクト配列への変換時間
    const conversionTime = measureTime(() => {
      const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(`PersonaLevel_${prefecture}`);
      const values = sheet.getDataRange().getValues();
      const headers = values[0];
      const dataRows = values.slice(1);

      return dataRows.map(function(row) {
        const obj = {};
        headers.forEach(function(header, index) {
          obj[header] = row[index];
        });
        return obj;
      });
    });
    measurement.conversion = conversionTime.duration;

    // 4. 全体（getPersonaLevelData）の時間
    const totalTime = measureTime(() => {
      return getPersonaLevelData(prefecture);
    });
    measurement.total = totalTime.duration;
    measurement.rowCount = totalTime.result.metadata.rowCount;
    measurement.colCount = totalTime.result.metadata.colCount;

    results.measurements.push(measurement);
  }

  // 統計計算
  results.stats = {
    getDataRange: calculateStats(results.measurements.map(m => m.getDataRange)),
    getValues: calculateStats(results.measurements.map(m => m.getValues)),
    conversion: calculateStats(results.measurements.map(m => m.conversion)),
    total: calculateStats(results.measurements.map(m => m.total))
  };

  // 期待値との比較
  results.expectations = {
    total: { expected: 3.0, actual: results.stats.total.avg, unit: '秒' },
    getDataRange: { expected: 0.5, actual: results.stats.getDataRange.avg, unit: '秒' },
    getValues: { expected: 1.5, actual: results.stats.getValues.avg, unit: '秒' },
    conversion: { expected: 1.0, actual: results.stats.conversion.avg, unit: '秒' }
  };

  // 判定
  results.passed = results.stats.total.avg < 3.0;

  Logger.log(`[テスト1] 完了 - 平均ロード時間: ${results.stats.total.avg.toFixed(2)}秒 (期待値: <3秒)`);

  return results;
}

// ============================================================
// テスト2: 都道府県別のロード時間比較
// ============================================================

function test2_PrefectureScaleComparison() {
  Logger.log('=== テスト2: 都道府県別のロード時間比較 ===');

  const results = {
    testName: '都道府県別ロード時間比較',
    scales: {}
  };

  // 各規模ごとに測定
  Object.keys(TEST_CONFIG.prefectures).forEach(scale => {
    const prefecture = TEST_CONFIG.prefectures[scale];
    Logger.log(`[テスト2] ${scale}: ${prefecture}`);

    const times = [];
    const rowCounts = [];

    // ウォームアップ
    for (let i = 0; i < TEST_CONFIG.warmupRuns; i++) {
      getPersonaLevelData(prefecture);
    }

    // 測定
    for (let i = 0; i < TEST_CONFIG.iterations; i++) {
      const measurement = measureTime(() => {
        return getPersonaLevelData(prefecture);
      });

      times.push(measurement.duration);
      rowCounts.push(measurement.result.metadata.rowCount);
    }

    results.scales[scale] = {
      prefecture: prefecture,
      rowCount: rowCounts[0],
      stats: calculateStats(times)
    };
  });

  // 線形性の確認（行数 vs ロード時間）
  const linearityAnalysis = {
    small: results.scales.small.stats.avg / results.scales.small.rowCount,
    medium: results.scales.medium.stats.avg / results.scales.medium.rowCount,
    large: results.scales.large ? results.scales.large.stats.avg / results.scales.large.rowCount : null
  };

  results.linearity = linearityAnalysis;
  results.isLinear = (linearityAnalysis.medium / linearityAnalysis.small) < 1.5;

  Logger.log(`[テスト2] 完了 - 線形性: ${results.isLinear ? '良好' : '非線形'}`);

  return results;
}

// ============================================================
// テスト3: フィルタリング性能
// ============================================================

function test3_FilteringPerformance() {
  Logger.log('=== テスト3: フィルタリング性能 ===');

  const prefecture = TEST_CONFIG.prefectures.medium; // 京都府
  const results = {
    testName: 'フィルタリング性能',
    prefecture: prefecture,
    conditions: {}
  };

  // フィルタ条件のパターン
  const filterPatterns = {
    none: {},
    one: { age_group: '50代' },
    two: { age_group: '50代', gender: '女性' },
    three: { age_group: '50代', gender: '女性', has_national_license: false },
    four: { age_group: '50代', gender: '女性', has_national_license: false, municipality: '京都市' }
  };

  // 各条件で測定
  Object.keys(filterPatterns).forEach(conditionName => {
    const filters = filterPatterns[conditionName];
    Logger.log(`[テスト3] 条件: ${conditionName} (${Object.keys(filters).length}条件)`);

    const times = [];
    const resultCounts = [];

    // ウォームアップ
    for (let i = 0; i < TEST_CONFIG.warmupRuns; i++) {
      filterPersonaLevelData(prefecture, filters);
    }

    // 測定
    for (let i = 0; i < TEST_CONFIG.iterations; i++) {
      const measurement = measureTime(() => {
        return filterPersonaLevelData(prefecture, filters);
      });

      times.push(measurement.duration);
      resultCounts.push(measurement.result.metadata.filteredCount);
    }

    results.conditions[conditionName] = {
      filterCount: Object.keys(filters).length,
      resultCount: resultCounts[0],
      stats: calculateStats(times)
    };
  });

  Logger.log(`[テスト3] 完了`);

  return results;
}

// ============================================================
// テスト4: 集計・分析性能
// ============================================================

function test4_AggregationPerformance() {
  Logger.log('=== テスト4: 集計・分析性能 ===');

  const prefecture = TEST_CONFIG.prefectures.medium; // 京都府
  const results = {
    testName: '集計・分析性能',
    prefecture: prefecture,
    functions: {}
  };

  // 測定対象関数
  const testFunctions = {
    summarize: () => summarizePersonaLevelData(prefecture, 'age_group'),
    difficulty: () => analyzePersonaDifficulty(prefecture, { age_group: '50代', gender: '女性', has_national_license: true }),
    ranking: () => getMunicipalityDifficultyRanking(prefecture, 10)
  };

  // 各関数で測定
  Object.keys(testFunctions).forEach(funcName => {
    const fn = testFunctions[funcName];
    Logger.log(`[テスト4] 関数: ${funcName}`);

    const times = [];

    // ウォームアップ
    for (let i = 0; i < TEST_CONFIG.warmupRuns; i++) {
      fn();
    }

    // 測定
    for (let i = 0; i < TEST_CONFIG.iterations; i++) {
      const measurement = measureTime(fn);
      times.push(measurement.duration);
    }

    results.functions[funcName] = {
      stats: calculateStats(times)
    };
  });

  Logger.log(`[テスト4] 完了`);

  return results;
}

// ============================================================
// テスト5: メモリ使用量推定
// ============================================================

function test5_MemoryUsageEstimation() {
  Logger.log('=== テスト5: メモリ使用量推定 ===');

  const results = {
    testName: 'メモリ使用量推定',
    dataSize: {}
  };

  // 京都府データのサイズ推定
  const kyotoData = getPersonaLevelData('京都府');
  results.dataSize.kyoto = {
    prefecture: '京都府',
    rowCount: kyotoData.metadata.rowCount,
    colCount: kyotoData.metadata.colCount,
    sizeKB: estimateDataSize(kyotoData)
  };

  // 全都道府県の推定
  const availablePrefectures = getAvailablePrefectures();
  const estimatedTotalSize = results.dataSize.kyoto.sizeKB * availablePrefectures.length;

  results.dataSize.allPrefectures = {
    count: availablePrefectures.length,
    estimatedTotalSizeKB: estimatedTotalSize,
    estimatedTotalSizeMB: (estimatedTotalSize / 1024).toFixed(2)
  };

  // GASメモリ制限との比較（推定）
  results.memoryLimit = {
    estimatedLimitMB: 100, // GASの推定メモリ制限（不明だが推定）
    usage: results.dataSize.allPrefectures.estimatedTotalSizeMB,
    usagePercent: ((estimatedTotalSize / 1024) / 100 * 100).toFixed(1)
  };

  Logger.log(`[テスト5] 完了 - 京都府: ${results.dataSize.kyoto.sizeKB}KB, 全47都道府県推定: ${results.dataSize.allPrefectures.estimatedTotalSizeMB}MB`);

  return results;
}

// ============================================================
// テスト6: 従来方式との比較
// ============================================================

function test6_LegacyComparison() {
  Logger.log('=== テスト6: 従来方式との比較 ===');

  const prefecture = '京都府';
  const municipality = '京都市';

  const results = {
    testName: '従来方式との比較',
    comparison: {}
  };

  // 従来方式（MapCompleteDataBridge）の測定
  Logger.log('[テスト6] 従来方式（MapCompleteDataBridge）測定中...');
  const legacyTimes = [];

  for (let i = 0; i < TEST_CONFIG.iterations; i++) {
    const measurement = measureTime(() => {
      return getMapCompleteData(prefecture, municipality);
    });
    legacyTimes.push(measurement.duration);
  }

  results.comparison.legacy = {
    method: 'MapCompleteDataBridge (15シート読み込み)',
    stats: calculateStats(legacyTimes)
  };

  // 新方式（PersonaLevelDataBridge）の測定
  Logger.log('[テスト6] 新方式（PersonaLevelDataBridge）測定中...');
  const newTimes = [];

  for (let i = 0; i < TEST_CONFIG.iterations; i++) {
    const measurement = measureTime(() => {
      return getPersonaLevelData(prefecture);
    });
    newTimes.push(measurement.duration);
  }

  results.comparison.new = {
    method: 'PersonaLevelDataBridge (1シート読み込み)',
    stats: calculateStats(newTimes)
  };

  // 改善率計算
  const improvementPercent = ((results.comparison.legacy.stats.avg - results.comparison.new.stats.avg) / results.comparison.legacy.stats.avg * 100).toFixed(1);

  results.improvement = {
    avgTimeSaved: (results.comparison.legacy.stats.avg - results.comparison.new.stats.avg).toFixed(2),
    improvementPercent: improvementPercent,
    speedupFactor: (results.comparison.legacy.stats.avg / results.comparison.new.stats.avg).toFixed(2)
  };

  Logger.log(`[テスト6] 完了 - 改善率: ${improvementPercent}% (高速化: ${results.improvement.speedupFactor}倍)`);

  return results;
}

// ============================================================
// テスト7: ボトルネック分析
// ============================================================

function test7_BottleneckAnalysis() {
  Logger.log('=== テスト7: ボトルネック分析 ===');

  const prefecture = TEST_CONFIG.prefectures.medium; // 京都府
  const results = {
    testName: 'ボトルネック分析',
    breakdown: {}
  };

  // 処理の内訳測定
  const measurement = measureTime(() => {
    return getPersonaLevelData(prefecture);
  });

  const totalTime = measurement.duration;
  const data = measurement.result;

  // 内訳推定（test1の結果を利用）
  const test1Results = test1_DataLoadDetailedAnalysis();

  results.breakdown = {
    getDataRange: {
      time: test1Results.stats.getDataRange.avg,
      percent: (test1Results.stats.getDataRange.avg / totalTime * 100).toFixed(1)
    },
    getValues: {
      time: test1Results.stats.getValues.avg,
      percent: (test1Results.stats.getValues.avg / totalTime * 100).toFixed(1)
    },
    conversion: {
      time: test1Results.stats.conversion.avg,
      percent: (test1Results.stats.conversion.avg / totalTime * 100).toFixed(1)
    },
    other: {
      time: (totalTime - test1Results.stats.getDataRange.avg - test1Results.stats.getValues.avg - test1Results.stats.conversion.avg).toFixed(2),
      percent: ((totalTime - test1Results.stats.getDataRange.avg - test1Results.stats.getValues.avg - test1Results.stats.conversion.avg) / totalTime * 100).toFixed(1)
    }
  };

  // ボトルネック特定
  const bottlenecks = [];

  Object.keys(results.breakdown).forEach(process => {
    if (parseFloat(results.breakdown[process].percent) > 30) {
      bottlenecks.push({
        process: process,
        percent: results.breakdown[process].percent
      });
    }
  });

  results.bottlenecks = bottlenecks;
  results.primaryBottleneck = bottlenecks.length > 0 ? bottlenecks[0].process : 'なし';

  Logger.log(`[テスト7] 完了 - 主要ボトルネック: ${results.primaryBottleneck}`);

  return results;
}

// ============================================================
// 統合レポート生成
// ============================================================

function generatePerformanceReport() {
  Logger.log('====================================');
  Logger.log('包括的パフォーマンステスト開始');
  Logger.log('====================================');

  const report = {
    timestamp: new Date().toISOString(),
    config: TEST_CONFIG,
    tests: {}
  };

  // 各テスト実行
  try {
    report.tests.test1 = test1_DataLoadDetailedAnalysis();
  } catch (e) {
    Logger.log('[エラー] テスト1失敗: ' + e);
    report.tests.test1 = { error: e.toString() };
  }

  try {
    report.tests.test2 = test2_PrefectureScaleComparison();
  } catch (e) {
    Logger.log('[エラー] テスト2失敗: ' + e);
    report.tests.test2 = { error: e.toString() };
  }

  try {
    report.tests.test3 = test3_FilteringPerformance();
  } catch (e) {
    Logger.log('[エラー] テスト3失敗: ' + e);
    report.tests.test3 = { error: e.toString() };
  }

  try {
    report.tests.test4 = test4_AggregationPerformance();
  } catch (e) {
    Logger.log('[エラー] テスト4失敗: ' + e);
    report.tests.test4 = { error: e.toString() };
  }

  try {
    report.tests.test5 = test5_MemoryUsageEstimation();
  } catch (e) {
    Logger.log('[エラー] テスト5失敗: ' + e);
    report.tests.test5 = { error: e.toString() };
  }

  try {
    report.tests.test6 = test6_LegacyComparison();
  } catch (e) {
    Logger.log('[エラー] テスト6失敗: ' + e);
    report.tests.test6 = { error: e.toString() };
  }

  try {
    report.tests.test7 = test7_BottleneckAnalysis();
  } catch (e) {
    Logger.log('[エラー] テスト7失敗: ' + e);
    report.tests.test7 = { error: e.toString() };
  }

  // レポート保存
  const reportJson = JSON.stringify(report, null, 2);
  Logger.log('====================================');
  Logger.log('パフォーマンステスト完了');
  Logger.log('====================================');

  return report;
}

// ============================================================
// 最適化提案生成
// ============================================================

function generateOptimizationSuggestions(report) {
  const suggestions = {
    timestamp: new Date().toISOString(),
    priority: [],
    details: {}
  };

  // テスト1の結果から
  if (report.tests.test1 && !report.tests.test1.error) {
    const test1 = report.tests.test1;

    if (test1.stats.getValues.avg > 1.0) {
      suggestions.priority.push({
        priority: 'HIGH',
        area: 'データ取得',
        suggestion: 'getValues()の範囲を限定する（必要な列のみ取得）',
        expectedImprovement: '30-50%の高速化',
        implementation: 'getRange(row, col, numRows, numCols).getValues()'
      });
    }
  }

  // テスト6の結果から
  if (report.tests.test6 && !report.tests.test6.error) {
    const test6 = report.tests.test6;

    if (parseFloat(test6.improvement.improvementPercent) > 80) {
      suggestions.priority.push({
        priority: 'ACHIEVED',
        area: 'システム全体',
        suggestion: `既に${test6.improvement.improvementPercent}%の改善を達成`,
        expectedImprovement: 'さらに10-20%の余地あり',
        implementation: 'ScriptCache導入、非同期処理検討'
      });
    }
  }

  // テスト7のボトルネックから
  if (report.tests.test7 && !report.tests.test7.error) {
    const test7 = report.tests.test7;

    if (test7.primaryBottleneck === 'getValues') {
      suggestions.priority.push({
        priority: 'MEDIUM',
        area: 'データ取得',
        suggestion: 'Spreadsheet APIの呼び出し回数を削減',
        expectedImprovement: '20-30%の高速化',
        implementation: 'バッチ処理、キャッシュ活用'
      });
    }
  }

  // ScriptCache導入の提案
  suggestions.priority.push({
    priority: 'LOW',
    area: 'キャッシュ',
    suggestion: 'ScriptCacheを導入して5分間データを保持',
    expectedImprovement: '2回目以降のアクセスで90%以上の高速化',
    implementation: 'CacheService.getScriptCache() を活用'
  });

  // ソート
  const priorityOrder = { ACHIEVED: 1, HIGH: 2, MEDIUM: 3, LOW: 4 };
  suggestions.priority.sort((a, b) => priorityOrder[a.priority] - priorityOrder[b.priority]);

  return suggestions;
}

// ============================================================
// メイン実行関数
// ============================================================

function runComprehensivePerformanceTest() {
  // レポート生成
  const report = generatePerformanceReport();

  // 最適化提案生成
  const suggestions = generateOptimizationSuggestions(report);

  // 統合結果
  const finalReport = {
    performanceTest: report,
    optimizationSuggestions: suggestions
  };

  // JSONとして保存
  const reportJson = JSON.stringify(finalReport, null, 2);

  // ログ出力（サマリー）
  Logger.log('\n========== サマリー ==========');

  if (report.tests.test1 && !report.tests.test1.error) {
    Logger.log(`テスト1（データロード詳細）: 平均 ${report.tests.test1.stats.total.avg.toFixed(2)}秒 (期待値: <3秒)`);
  }

  if (report.tests.test6 && !report.tests.test6.error) {
    Logger.log(`テスト6（従来方式比較）: ${report.tests.test6.improvement.improvementPercent}%改善 (${report.tests.test6.improvement.speedupFactor}倍高速化)`);
  }

  Logger.log('\n最適化提案（優先度順）:');
  suggestions.priority.forEach((s, i) => {
    Logger.log(`${i + 1}. [${s.priority}] ${s.area}: ${s.suggestion}`);
  });

  Logger.log('\n==============================\n');

  return finalReport;
}
