/**
 * パフォーマンステスト結果をMarkdownレポートに変換
 *
 * @param {Object} testResults - runComprehensivePerformanceTest() の戻り値
 * @return {string} Markdown形式のレポート
 */
function generateMarkdownReport(testResults) {
  const report = testResults.performanceTest;
  const suggestions = testResults.optimizationSuggestions;

  let md = '';

  // ヘッダー
  md += '# パフォーマンステスト・最適化分析レポート\n\n';
  md += `**実行日時**: ${report.timestamp}\n\n`;
  md += `**テスト環境**:\n`;
  md += `- 繰り返し回数: ${report.config.iterations}回\n`;
  md += `- ウォームアップ: ${report.config.warmupRuns}回\n`;
  md += `- 中規模データ: ${report.config.prefectures.medium} (601行想定)\n\n`;

  md += '---\n\n';

  // エグゼクティブサマリー
  md += '## エグゼクティブサマリー\n\n';

  if (report.tests.test6 && !report.tests.test6.error) {
    const improvement = report.tests.test6.improvement;
    md += `### 性能改善効果\n\n`;
    md += `- **改善率**: ${improvement.improvementPercent}%\n`;
    md += `- **高速化倍率**: ${improvement.speedupFactor}倍\n`;
    md += `- **削減時間**: ${improvement.avgTimeSaved}秒/リクエスト\n\n`;

    md += `#### 従来方式 vs 新方式\n\n`;
    md += `| 方式 | 平均時間 | 中央値 | 最小 | 最大 | 標準偏差 |\n`;
    md += `|------|---------|--------|------|------|----------|\n`;
    md += `| ${report.tests.test6.comparison.legacy.method} | ${report.tests.test6.comparison.legacy.stats.avg.toFixed(2)}秒 | ${report.tests.test6.comparison.legacy.stats.median.toFixed(2)}秒 | ${report.tests.test6.comparison.legacy.stats.min.toFixed(2)}秒 | ${report.tests.test6.comparison.legacy.stats.max.toFixed(2)}秒 | ${report.tests.test6.comparison.legacy.stats.stdDev.toFixed(3)}秒 |\n`;
    md += `| ${report.tests.test6.comparison.new.method} | ${report.tests.test6.comparison.new.stats.avg.toFixed(2)}秒 | ${report.tests.test6.comparison.new.stats.median.toFixed(2)}秒 | ${report.tests.test6.comparison.new.stats.min.toFixed(2)}秒 | ${report.tests.test6.comparison.new.stats.max.toFixed(2)}秒 | ${report.tests.test6.comparison.new.stats.stdDev.toFixed(3)}秒 |\n\n`;
  }

  md += '---\n\n';

  // テスト1: データロード詳細
  if (report.tests.test1 && !report.tests.test1.error) {
    const test1 = report.tests.test1;

    md += '## 1. データロード時間の詳細分析\n\n';
    md += `**対象**: ${test1.prefecture} (${test1.measurements[0].rowCount}行 × ${test1.measurements[0].colCount}列)\n\n`;

    md += '### 処理内訳\n\n';
    md += '| 処理 | 平均時間 | 中央値 | 標準偏差 | 期待値 | 判定 |\n';
    md += '|------|---------|--------|----------|--------|------|\n';
    md += `| getDataRange() | ${test1.stats.getDataRange.avg.toFixed(2)}秒 | ${test1.stats.getDataRange.median.toFixed(2)}秒 | ${test1.stats.getDataRange.stdDev.toFixed(3)}秒 | ${test1.expectations.getDataRange.expected}秒 | ${test1.stats.getDataRange.avg < test1.expectations.getDataRange.expected ? '✅' : '⚠️'} |\n`;
    md += `| getValues() | ${test1.stats.getValues.avg.toFixed(2)}秒 | ${test1.stats.getValues.median.toFixed(2)}秒 | ${test1.stats.getValues.stdDev.toFixed(3)}秒 | ${test1.expectations.getValues.expected}秒 | ${test1.stats.getValues.avg < test1.expectations.getValues.expected ? '✅' : '⚠️'} |\n`;
    md += `| オブジェクト配列変換 | ${test1.stats.conversion.avg.toFixed(2)}秒 | ${test1.stats.conversion.median.toFixed(2)}秒 | ${test1.stats.conversion.stdDev.toFixed(3)}秒 | ${test1.expectations.conversion.expected}秒 | ${test1.stats.conversion.avg < test1.expectations.conversion.expected ? '✅' : '⚠️'} |\n`;
    md += `| **合計** | **${test1.stats.total.avg.toFixed(2)}秒** | ${test1.stats.total.median.toFixed(2)}秒 | ${test1.stats.total.stdDev.toFixed(3)}秒 | ${test1.expectations.total.expected}秒 | ${test1.passed ? '✅' : '❌'} |\n\n`;

    md += '### 分析\n\n';

    if (test1.stats.getValues.avg > 1.0) {
      md += '- ⚠️ **getValues()が最大のボトルネック** (${(test1.stats.getValues.avg / test1.stats.total.avg * 100).toFixed(1)}%)\n';
      md += '  - 原因: Spreadsheet APIの呼び出しオーバーヘッド\n';
      md += '  - 対策: 必要な列のみ取得する範囲指定を検討\n\n';
    }

    if (test1.stats.conversion.avg > 0.5) {
      md += `- ⚠️ **オブジェクト変換に時間がかかっている** (${(test1.stats.conversion.avg / test1.stats.total.avg * 100).toFixed(1)}%)\n`;
      md += '  - 原因: JavaScript の forEach() ループ処理\n';
      md += '  - 対策: V8 エンジンの最適化を活用（現状維持で問題なし）\n\n';
    }

    if (test1.passed) {
      md += '✅ **総合評価: 合格** - 期待値以内の性能を達成\n\n';
    } else {
      md += '❌ **総合評価: 不合格** - 期待値を超過、最適化が必要\n\n';
    }
  }

  md += '---\n\n';

  // テスト2: 都道府県別比較
  if (report.tests.test2 && !report.tests.test2.error) {
    const test2 = report.tests.test2;

    md += '## 2. 都道府県別のロード時間比較\n\n';

    md += '### 規模別ロード時間\n\n';
    md += '| 規模 | 都道府県 | 行数 | 平均時間 | 中央値 | 1行あたり時間 |\n';
    md += '|------|---------|------|---------|--------|---------------|\n';

    Object.keys(test2.scales).forEach(scale => {
      const data = test2.scales[scale];
      const timePerRow = (data.stats.avg / data.rowCount * 1000).toFixed(2); // ミリ秒
      md += `| ${scale} | ${data.prefecture} | ${data.rowCount}行 | ${data.stats.avg.toFixed(2)}秒 | ${data.stats.median.toFixed(2)}秒 | ${timePerRow}ms/行 |\n`;
    });

    md += '\n';

    md += '### 線形性分析\n\n';
    md += '| 規模 | 1行あたり時間 (ms) |\n';
    md += '|------|-------------------|\n';
    md += `| small | ${(test2.linearity.small * 1000).toFixed(2)}ms |\n`;
    md += `| medium | ${(test2.linearity.medium * 1000).toFixed(2)}ms |\n`;
    if (test2.linearity.large) {
      md += `| large | ${(test2.linearity.large * 1000).toFixed(2)}ms |\n`;
    }
    md += '\n';

    if (test2.isLinear) {
      md += '✅ **線形性: 良好** - データ量に比例してロード時間が増加（予測可能）\n\n';
    } else {
      md += '⚠️ **線形性: 非線形** - 大規模データで性能劣化の可能性\n\n';
    }
  }

  md += '---\n\n';

  // テスト3: フィルタリング性能
  if (report.tests.test3 && !report.tests.test3.error) {
    const test3 = report.tests.test3;

    md += '## 3. フィルタリング性能\n\n';

    md += '### 条件数別フィルタリング時間\n\n';
    md += '| 条件数 | 結果件数 | 平均時間 | 中央値 | 標準偏差 |\n';
    md += '|--------|---------|---------|--------|----------|\n';

    Object.keys(test3.conditions).forEach(conditionName => {
      const data = test3.conditions[conditionName];
      md += `| ${data.filterCount}条件 (${conditionName}) | ${data.resultCount}件 | ${data.stats.avg.toFixed(2)}秒 | ${data.stats.median.toFixed(2)}秒 | ${data.stats.stdDev.toFixed(3)}秒 |\n`;
    });

    md += '\n';

    md += '### 分析\n\n';

    const noneTime = test3.conditions.none.stats.avg;
    const fourTime = test3.conditions.four.stats.avg;
    const overhead = ((fourTime - noneTime) / noneTime * 100).toFixed(1);

    md += `- フィルタなし → 4条件: ${overhead}%のオーバーヘッド\n`;

    if (fourTime < 1.0) {
      md += '- ✅ **高速**: 4条件でも1秒未満で処理完了\n\n';
    } else {
      md += '- ⚠️ **要改善**: 4条件で1秒以上、インデックス活用を検討\n\n';
    }
  }

  md += '---\n\n';

  // テスト4: 集計・分析性能
  if (report.tests.test4 && !report.tests.test4.error) {
    const test4 = report.tests.test4;

    md += '## 4. 集計・分析性能\n\n';

    md += '### 関数別処理時間\n\n';
    md += '| 関数 | 平均時間 | 中央値 | 標準偏差 |\n';
    md += '|------|---------|--------|----------|\n';

    Object.keys(test4.functions).forEach(funcName => {
      const data = test4.functions[funcName];
      md += `| ${funcName}() | ${data.stats.avg.toFixed(2)}秒 | ${data.stats.median.toFixed(2)}秒 | ${data.stats.stdDev.toFixed(3)}秒 |\n`;
    });

    md += '\n';

    md += '### 分析\n\n';

    const avgTime = Object.values(test4.functions).reduce((sum, f) => sum + f.stats.avg, 0) / Object.keys(test4.functions).length;

    if (avgTime < 1.0) {
      md += '✅ **高速**: すべての集計・分析関数が1秒未満で処理完了\n\n';
    } else {
      md += '⚠️ **要最適化**: 平均処理時間が1秒以上、アルゴリズム改善を検討\n\n';
    }
  }

  md += '---\n\n';

  // テスト5: メモリ使用量
  if (report.tests.test5 && !report.tests.test5.error) {
    const test5 = report.tests.test5;

    md += '## 5. メモリ使用量推定\n\n';

    md += '### データサイズ\n\n';
    md += '| 対象 | 行数 | 列数 | サイズ (KB) | サイズ (MB) |\n';
    md += '|------|------|------|------------|------------|\n';
    md += `| ${test5.dataSize.kyoto.prefecture} | ${test5.dataSize.kyoto.rowCount}行 | ${test5.dataSize.kyoto.colCount}列 | ${test5.dataSize.kyoto.sizeKB}KB | ${(test5.dataSize.kyoto.sizeKB / 1024).toFixed(2)}MB |\n`;
    md += `| 全${test5.dataSize.allPrefectures.count}都道府県（推定） | - | - | ${test5.dataSize.allPrefectures.estimatedTotalSizeKB}KB | ${test5.dataSize.allPrefectures.estimatedTotalSizeMB}MB |\n\n`;

    md += '### GASメモリ制限との比較（推定）\n\n';
    md += `- **推定メモリ制限**: ${test5.memoryLimit.estimatedLimitMB}MB\n`;
    md += `- **使用量**: ${test5.memoryLimit.usage}MB (${test5.memoryLimit.usagePercent}%)\n\n`;

    if (parseFloat(test5.memoryLimit.usagePercent) < 50) {
      md += '✅ **メモリ: 十分な余裕** - 全都道府県を同時ロードしても問題なし\n\n';
    } else if (parseFloat(test5.memoryLimit.usagePercent) < 80) {
      md += '⚠️ **メモリ: やや注意** - 複数都道府県の同時ロードは避けるべき\n\n';
    } else {
      md += '❌ **メモリ: 不足の可能性** - キャッシュクリアやバッチ処理が必須\n\n';
    }
  }

  md += '---\n\n';

  // テスト7: ボトルネック分析
  if (report.tests.test7 && !report.tests.test7.error) {
    const test7 = report.tests.test7;

    md += '## 6. ボトルネック分析\n\n';

    md += '### 処理時間の内訳\n\n';
    md += '| 処理 | 時間 (秒) | 割合 (%) |\n';
    md += '|------|----------|----------|\n';

    Object.keys(test7.breakdown).forEach(process => {
      const data = test7.breakdown[process];
      md += `| ${process} | ${data.time}秒 | ${data.percent}% |\n`;
    });

    md += '\n';

    md += '### ボトルネック特定\n\n';

    if (test7.bottlenecks.length > 0) {
      md += `**主要ボトルネック**: ${test7.primaryBottleneck} (${test7.bottlenecks[0].percent}%)\n\n`;

      md += '**ボトルネックリスト** (30%以上の処理):\n\n';
      test7.bottlenecks.forEach((b, i) => {
        md += `${i + 1}. ${b.process}: ${b.percent}%\n`;
      });
      md += '\n';
    } else {
      md += '✅ **ボトルネックなし** - 処理が均等に分散されている\n\n';
    }

    md += '### I/O vs CPU vs メモリの分析\n\n';

    const ioPercent = parseFloat(test7.breakdown.getDataRange.percent) + parseFloat(test7.breakdown.getValues.percent);
    const cpuPercent = parseFloat(test7.breakdown.conversion.percent);
    const otherPercent = parseFloat(test7.breakdown.other.percent);

    md += `- **I/O（Spreadsheet API）**: ${ioPercent.toFixed(1)}%\n`;
    md += `- **CPU（オブジェクト変換）**: ${cpuPercent}%\n`;
    md += `- **その他**: ${otherPercent}%\n\n`;

    if (ioPercent > 60) {
      md += '⚠️ **I/Oボトルネック** - Spreadsheet APIの呼び出しが最大の課題\n\n';
    } else if (cpuPercent > 40) {
      md += '⚠️ **CPUボトルネック** - 計算処理の最適化が有効\n\n';
    } else {
      md += '✅ **バランス良好** - I/O と CPU が適切に分散\n\n';
    }
  }

  md += '---\n\n';

  // 最適化提案
  md += '## 最適化提案\n\n';

  if (suggestions.priority.length > 0) {
    md += '### 優先度順の提案\n\n';

    suggestions.priority.forEach((s, i) => {
      md += `#### ${i + 1}. [${s.priority}] ${s.area}\n\n`;
      md += `**提案**: ${s.suggestion}\n\n`;
      md += `**期待改善**: ${s.expectedImprovement}\n\n`;
      md += `**実装方法**: ${s.implementation}\n\n`;
      md += '---\n\n';
    });
  }

  // 最終評価
  md += '## 最終評価\n\n';

  if (report.tests.test6 && !report.tests.test6.error) {
    const improvementPercent = parseFloat(report.tests.test6.improvement.improvementPercent);

    md += '### 性能改善効果\n\n';
    md += `- **改善率**: ${improvementPercent}%\n`;
    md += `- **評価**: `;

    if (improvementPercent >= 85) {
      md += '**EXCELLENT** - 目標を大幅に超過 ✅\n\n';
    } else if (improvementPercent >= 70) {
      md += '**GOOD** - 目標達成 ✅\n\n';
    } else if (improvementPercent >= 50) {
      md += '**FAIR** - 改善あり、さらなる最適化可能 ⚠️\n\n';
    } else {
      md += '**POOR** - 大幅な最適化が必要 ❌\n\n';
    }
  }

  md += '### さらなる最適化の余地\n\n';

  if (report.tests.test1 && !report.tests.test1.error) {
    const currentTime = report.tests.test1.stats.total.avg;
    const theoreticalMin = currentTime * 0.5; // 理論的最小値（50%削減）

    md += `- **現在の処理時間**: ${currentTime.toFixed(2)}秒\n`;
    md += `- **理論的最小時間**: ${theoreticalMin.toFixed(2)}秒 (ScriptCache + API最適化)\n`;
    md += `- **さらなる改善余地**: ${((currentTime - theoreticalMin) / currentTime * 100).toFixed(1)}%\n\n`;
  }

  md += '### 推奨される次の最適化アクション\n\n';

  const topSuggestion = suggestions.priority[0];
  if (topSuggestion) {
    md += `1. **${topSuggestion.area}**: ${topSuggestion.suggestion}\n`;
    md += `   - 期待改善: ${topSuggestion.expectedImprovement}\n`;
    md += `   - 実装方法: ${topSuggestion.implementation}\n\n`;
  }

  if (suggestions.priority.length > 1) {
    const secondSuggestion = suggestions.priority[1];
    md += `2. **${secondSuggestion.area}**: ${secondSuggestion.suggestion}\n`;
    md += `   - 期待改善: ${secondSuggestion.expectedImprovement}\n`;
    md += `   - 実装方法: ${secondSuggestion.implementation}\n\n`;
  }

  md += '---\n\n';
  md += `**レポート生成日時**: ${suggestions.timestamp}\n`;

  return md;
}

/**
 * パフォーマンステストを実行してMarkdownレポートを保存
 */
function runTestAndGenerateReport() {
  Logger.log('パフォーマンステスト実行中...');

  // テスト実行
  const testResults = runComprehensivePerformanceTest();

  // Markdownレポート生成
  const markdownReport = generateMarkdownReport(testResults);

  // ログ出力
  Logger.log('\n========== Markdownレポート ==========\n');
  Logger.log(markdownReport);
  Logger.log('\n======================================\n');

  // 保存用にJSONも出力
  const jsonReport = JSON.stringify(testResults, null, 2);

  return {
    markdown: markdownReport,
    json: jsonReport,
    rawResults: testResults
  };
}
