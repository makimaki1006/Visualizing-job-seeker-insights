/**
 * ペルソナ難易度確認機能
 * セグメント別の採用難易度を多角的に分析・表示
 */

// ===== ペルソナ難易度確認ダイアログ表示 =====
function showPersonaDifficultyChecker() {
  var html = HtmlService.createHtmlOutputFromFile('PersonaDifficultyCheckerUI')
    .setWidth(1400)
    .setHeight(900);
  SpreadsheetApp.getUi().showModalDialog(html, '🎯 ペルソナ難易度確認');
}

// ===== ペルソナデータ取得 =====
function getPersonaDataForDifficulty() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var summarySheet = ss.getSheetByName('PersonaSummary');
  var detailsSheet = ss.getSheetByName('PersonaDetails');
  var applicantsSheet = ss.getSheetByName('Applicants');

  if (!summarySheet || summarySheet.getLastRow() <= 1) {
    return { success: false, message: 'PersonaSummaryデータが見つかりません' };
  }

  // PersonaSummaryデータ取得
  var summaryData = summarySheet.getDataRange().getValues();
  var summaryHeaders = summaryData[0];
  var summaryRows = summaryData.slice(1);

  // 各ペルソナの詳細分析
  var personas = summaryRows.map(function(row) {
    var segmentId = row[0];
    var segmentName = row[1];
    var count = parseInt(row[2]) || 0;
    var percentage = parseFloat(row[3]) || 0;
    var avgAge = parseFloat(row[4]) || 0;
    var femaleRatio = parseFloat(row[5]) || 0;
    var avgQualifications = parseFloat(row[6]) || 0;
    var topPrefecture = row[7];
    var avgDesiredLocations = parseFloat(row[8]) || 0;

    // 難易度スコア計算（0-100）
    var difficultyScore = calculateDifficultyScore({
      avgQualifications: avgQualifications,
      avgDesiredLocations: avgDesiredLocations,
      femaleRatio: femaleRatio,
      count: count,
      percentage: percentage,
      avgAge: avgAge
    });

    return {
      segmentId: segmentId,
      segmentName: segmentName,
      count: count,
      percentage: percentage,
      avgAge: avgAge,
      femaleRatio: femaleRatio,
      avgQualifications: avgQualifications,
      topPrefecture: topPrefecture,
      avgDesiredLocations: avgDesiredLocations,
      difficultyScore: difficultyScore,
      difficultyLevel: getDifficultyLevel(difficultyScore),
      ageGroup: getAgeGroup(avgAge),
      qualificationLevel: getQualificationLevel(avgQualifications),
      mobilityLevel: getMobilityLevel(avgDesiredLocations),
      genderCategory: getGenderCategory(femaleRatio),
      marketSizeCategory: getMarketSizeCategory(percentage)
    };
  });

  // 難易度スコアでソート
  personas.sort(function(a, b) {
    return b.difficultyScore - a.difficultyScore;
  });

  return {
    success: true,
    personas: personas,
    totalCount: personas.reduce(function(sum, p) { return sum + p.count; }, 0)
  };
}

// ===== 難易度スコア計算 =====
function calculateDifficultyScore(params) {
  // スコア計算ロジック（重み付け）
  var qualScore = Math.min(params.avgQualifications * 15, 40);  // 資格数（最大40点）
  var mobilityScore = Math.min(params.avgDesiredLocations * 8, 25);  // 希望地数（最大25点）
  var sizeScore = Math.max(0, 20 - params.percentage * 2);  // 市場サイズ（小さいほど難）
  var ageScore = getAgeScore(params.avgAge);  // 年齢（10点）
  var genderScore = Math.abs(params.femaleRatio - 0.5) * 10;  // 性別偏り（5点）

  var totalScore = qualScore + mobilityScore + sizeScore + ageScore + genderScore;
  return Math.min(Math.round(totalScore), 100);
}

// ===== 年齢スコア =====
function getAgeScore(avgAge) {
  if (avgAge < 25) return 5;  // 若年層：やや難
  if (avgAge < 35) return 3;  // 若手：普通
  if (avgAge < 50) return 4;  // 中堅：やや難
  if (avgAge < 60) return 7;  // シニア：難
  return 10;  // 高齢：最難
}

// ===== 難易度レベル判定 =====
function getDifficultyLevel(score) {
  if (score >= 80) return 'S級（最難）';
  if (score >= 65) return 'A級（難）';
  if (score >= 50) return 'B級（やや難）';
  if (score >= 35) return 'C級（普通）';
  if (score >= 20) return 'D級（やや易）';
  return 'E級（易）';
}

// ===== 年齢グループ分類 =====
function getAgeGroup(avgAge) {
  if (avgAge < 25) return '新卒層（～24歳）';
  if (avgAge < 30) return '若手層（25～29歳）';
  if (avgAge < 35) return '若手中堅層（30～34歳）';
  if (avgAge < 40) return '中堅層（35～39歳）';
  if (avgAge < 45) return 'ミドル層（40～44歳）';
  if (avgAge < 50) return 'シニアミドル層（45～49歳）';
  if (avgAge < 55) return 'プレシニア層（50～54歳）';
  if (avgAge < 60) return 'シニア層（55～59歳）';
  if (avgAge < 65) return 'アクティブシニア層（60～64歳）';
  return '高齢層（65歳～）';
}

// ===== 資格レベル分類 =====
function getQualificationLevel(avgQualifications) {
  if (avgQualifications >= 5.0) return '超高資格層（5個以上）';
  if (avgQualifications >= 3.0) return '高資格層（3～4個）';
  if (avgQualifications >= 2.0) return '中資格層（2～3個）';
  if (avgQualifications >= 1.0) return '低資格層（1～2個）';
  if (avgQualifications >= 0.5) return '微資格層（0.5～1個）';
  return '無資格層（0.5個未満）';
}

// ===== 移動性レベル分類 =====
function getMobilityLevel(avgDesiredLocations) {
  if (avgDesiredLocations >= 10.0) return '超広域希望（10箇所以上）';
  if (avgDesiredLocations >= 6.0) return '広域希望（6～9箇所）';
  if (avgDesiredLocations >= 4.0) return '中域希望（4～5箇所）';
  if (avgDesiredLocations >= 2.5) return '狭域希望（2.5～3.5箇所）';
  if (avgDesiredLocations >= 1.5) return '限定希望（1.5～2.5箇所）';
  return '固定希望（1.5箇所未満）';
}

// ===== 性別カテゴリ分類 =====
function getGenderCategory(femaleRatio) {
  if (femaleRatio >= 0.9) return '女性特化層（90%以上）';
  if (femaleRatio >= 0.7) return '女性優勢層（70～89%）';
  if (femaleRatio >= 0.55) return '女性やや多層（55～69%）';
  if (femaleRatio >= 0.45) return '男女均衡層（45～54%）';
  if (femaleRatio >= 0.3) return '男性やや多層（31～44%）';
  if (femaleRatio >= 0.1) return '男性優勢層（11～30%）';
  return '男性特化層（10%以下）';
}

// ===== 市場規模カテゴリ分類 =====
function getMarketSizeCategory(percentage) {
  if (percentage >= 20.0) return '超大規模（20%以上）';
  if (percentage >= 15.0) return '大規模（15～19%）';
  if (percentage >= 10.0) return '中規模（10～14%）';
  if (percentage >= 7.0) return 'やや小規模（7～9%）';
  if (percentage >= 4.0) return '小規模（4～6%）';
  if (percentage >= 2.0) return '超小規模（2～3%）';
  return 'ニッチ（2%未満）';
}

// ===== フィルタリング機能 =====
function filterPersonasByConditions(filters) {
  var allData = getPersonaDataForDifficulty();

  if (!allData.success) {
    return allData;
  }

  var personas = allData.personas;

  // 難易度レベルフィルタ
  if (filters.difficultyLevels && filters.difficultyLevels.length > 0) {
    personas = personas.filter(function(p) {
      return filters.difficultyLevels.indexOf(p.difficultyLevel) !== -1;
    });
  }

  // 年齢グループフィルタ
  if (filters.ageGroups && filters.ageGroups.length > 0) {
    personas = personas.filter(function(p) {
      return filters.ageGroups.indexOf(p.ageGroup) !== -1;
    });
  }

  // 資格レベルフィルタ
  if (filters.qualificationLevels && filters.qualificationLevels.length > 0) {
    personas = personas.filter(function(p) {
      return filters.qualificationLevels.indexOf(p.qualificationLevel) !== -1;
    });
  }

  // 移動性レベルフィルタ
  if (filters.mobilityLevels && filters.mobilityLevels.length > 0) {
    personas = personas.filter(function(p) {
      return filters.mobilityLevels.indexOf(p.mobilityLevel) !== -1;
    });
  }

  // 性別カテゴリフィルタ
  if (filters.genderCategories && filters.genderCategories.length > 0) {
    personas = personas.filter(function(p) {
      return filters.genderCategories.indexOf(p.genderCategory) !== -1;
    });
  }

  // 市場規模カテゴリフィルタ
  if (filters.marketSizeCategories && filters.marketSizeCategories.length > 0) {
    personas = personas.filter(function(p) {
      return filters.marketSizeCategories.indexOf(p.marketSizeCategory) !== -1;
    });
  }

  return {
    success: true,
    personas: personas,
    totalCount: personas.reduce(function(sum, p) { return sum + p.count; }, 0),
    filteredCount: personas.length
  };
}

// ===== 統計サマリー取得 =====
function getPersonaDifficultyStatistics() {
  var data = getPersonaDataForDifficulty();

  if (!data.success) {
    return data;
  }

  var personas = data.personas;

  // 難易度レベル別集計
  var difficultyDistribution = {};
  var ageGroupDistribution = {};
  var qualificationDistribution = {};
  var mobilityDistribution = {};
  var genderDistribution = {};
  var marketSizeDistribution = {};

  personas.forEach(function(p) {
    // 難易度レベル
    difficultyDistribution[p.difficultyLevel] = (difficultyDistribution[p.difficultyLevel] || 0) + p.count;

    // 年齢グループ
    ageGroupDistribution[p.ageGroup] = (ageGroupDistribution[p.ageGroup] || 0) + p.count;

    // 資格レベル
    qualificationDistribution[p.qualificationLevel] = (qualificationDistribution[p.qualificationLevel] || 0) + p.count;

    // 移動性レベル
    mobilityDistribution[p.mobilityLevel] = (mobilityDistribution[p.mobilityLevel] || 0) + p.count;

    // 性別カテゴリ
    genderDistribution[p.genderCategory] = (genderDistribution[p.genderCategory] || 0) + p.count;

    // 市場規模カテゴリ
    marketSizeDistribution[p.marketSizeCategory] = (marketSizeDistribution[p.marketSizeCategory] || 0) + p.count;
  });

  return {
    success: true,
    avgDifficultyScore: personas.reduce(function(sum, p) { return sum + p.difficultyScore; }, 0) / personas.length,
    difficultyDistribution: difficultyDistribution,
    ageGroupDistribution: ageGroupDistribution,
    qualificationDistribution: qualificationDistribution,
    mobilityDistribution: mobilityDistribution,
    genderDistribution: genderDistribution,
    marketSizeDistribution: marketSizeDistribution,
    totalPersonas: personas.length,
    totalCount: data.totalCount
  };
}
