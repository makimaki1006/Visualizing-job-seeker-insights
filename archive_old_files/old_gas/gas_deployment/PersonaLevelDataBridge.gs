/**
 * PersonaLevel統合シート向けデータブリッジモジュール
 *
 * 目的: MapComplete dashboardの性能最適化
 * - 従来: 15シート読み込み → 21秒
 * - 改善後: 1シート読み込み → 2-3秒（85-90%削減）
 *
 * 統合シート形式: PersonaLevel_<都道府県名>.csv
 * - 602行×43列（京都府の場合）
 * - Phase 3, 6, 7, 10, 12, 13, 14のすべてのデータをペルソナセグメントレベルで統合
 *
 * @version 1.0
 * @date 2025-11-06
 */

/**
 * Spreadsheetオブジェクトのキャッシュ
 */
var PERSONA_LEVEL_SPREADSHEET_CACHE_ = null;

/**
 * Spreadsheetオブジェクトを一度だけ取得
 * @return {Spreadsheet}
 */
function getPersonaLevelSpreadsheet_() {
  if (!PERSONA_LEVEL_SPREADSHEET_CACHE_) {
    Logger.log('[PersonaLevel] Spreadsheetオブジェクトを初回取得');
    PERSONA_LEVEL_SPREADSHEET_CACHE_ = SpreadsheetApp.getActiveSpreadsheet();
  }
  return PERSONA_LEVEL_SPREADSHEET_CACHE_;
}

/**
 * 都道府県別ペルソナレベル統合データを取得
 *
 * @param {string} prefecture - 都道府県名（例: "京都府"）
 * @return {Object} 統合データオブジェクト
 * @example
 * var data = getPersonaLevelData('京都府');
 * // data.personas: 601ペルソナセグメント
 * // data.metadata: { rowCount: 601, colCount: 43, loadTime: 2.3 }
 */
function getPersonaLevelData(prefecture) {
  const startTime = new Date().getTime();

  Logger.log('[PersonaLevel] データ取得開始: ' + prefecture);

  // 統合シート名: PersonaLevel_<都道府県名>
  const sheetName = 'PersonaLevel_' + prefecture;

  const ss = getPersonaLevelSpreadsheet_();
  const sheet = ss.getSheetByName(sheetName);

  if (!sheet) {
    Logger.log('[PersonaLevel] エラー: シート「' + sheetName + '」が見つかりません');
    throw new Error('統合シート「' + sheetName + '」が見つかりません。CSVインポートが完了しているか確認してください。');
  }

  // データ範囲を一括取得
  const dataRange = sheet.getDataRange();
  const values = dataRange.getValues();

  if (values.length === 0) {
    Logger.log('[PersonaLevel] エラー: シートが空です');
    throw new Error('統合シート「' + sheetName + '」にデータがありません。');
  }

  // ヘッダー行
  const headers = values[0];

  // データ行（ヘッダーを除く）
  const dataRows = values.slice(1);

  Logger.log('[PersonaLevel] データ読み込み完了: ' + dataRows.length + '行 × ' + headers.length + '列');

  // オブジェクト配列に変換
  const personas = dataRows.map(function(row) {
    const obj = {};
    headers.forEach(function(header, index) {
      obj[header] = row[index];
    });
    return obj;
  });

  const endTime = new Date().getTime();
  const loadTime = (endTime - startTime) / 1000; // 秒

  Logger.log('[PersonaLevel] データ処理完了: ' + loadTime + '秒');

  return {
    prefecture: prefecture,
    personas: personas,
    metadata: {
      sheetName: sheetName,
      rowCount: dataRows.length,
      colCount: headers.length,
      loadTime: loadTime,
      timestamp: new Date().toISOString()
    }
  };
}

/**
 * 都道府県別ペルソナレベルデータをフィルタリング
 *
 * @param {string} prefecture - 都道府県名
 * @param {Object} filters - フィルタ条件
 * @param {string=} filters.municipality - 市区町村名（部分一致）
 * @param {string=} filters.age_group - 年齢層（例: "50代"）
 * @param {string=} filters.gender - 性別（"男性" or "女性"）
 * @param {boolean=} filters.has_national_license - 国家資格保有
 * @return {Object} フィルタ済みデータ
 * @example
 * var filtered = filterPersonaLevelData('京都府', {
 *   municipality: '京都市',
 *   age_group: '50代',
 *   gender: '女性',
 *   has_national_license: false
 * });
 */
function filterPersonaLevelData(prefecture, filters) {
  const startTime = new Date().getTime();

  Logger.log('[PersonaLevel] フィルタリング開始: ' + JSON.stringify(filters));

  const data = getPersonaLevelData(prefecture);

  let filtered = data.personas;

  // 市区町村フィルタ（部分一致）
  if (filters.municipality) {
    filtered = filtered.filter(function(p) {
      return p.municipality && p.municipality.indexOf(filters.municipality) !== -1;
    });
    Logger.log('[PersonaLevel] 市区町村フィルタ適用: ' + filtered.length + '件');
  }

  // 年齢層フィルタ
  if (filters.age_group) {
    filtered = filtered.filter(function(p) {
      return p.age_group === filters.age_group;
    });
    Logger.log('[PersonaLevel] 年齢層フィルタ適用: ' + filtered.length + '件');
  }

  // 性別フィルタ
  if (filters.gender) {
    filtered = filtered.filter(function(p) {
      return p.gender === filters.gender;
    });
    Logger.log('[PersonaLevel] 性別フィルタ適用: ' + filtered.length + '件');
  }

  // 国家資格フィルタ
  if (filters.has_national_license !== undefined && filters.has_national_license !== null) {
    filtered = filtered.filter(function(p) {
      // Trueの文字列または真偽値に対応
      const hasLicense = p.has_national_license === true || p.has_national_license === 'True' || p.has_national_license === 'TRUE';
      return hasLicense === filters.has_national_license;
    });
    Logger.log('[PersonaLevel] 国家資格フィルタ適用: ' + filtered.length + '件');
  }

  const endTime = new Date().getTime();
  const filterTime = (endTime - startTime) / 1000;

  Logger.log('[PersonaLevel] フィルタリング完了: ' + filterTime + '秒');

  return {
    prefecture: prefecture,
    filters: filters,
    personas: filtered,
    metadata: {
      originalCount: data.personas.length,
      filteredCount: filtered.length,
      filterTime: filterTime,
      timestamp: new Date().toISOString()
    }
  };
}

/**
 * ペルソナレベルデータを集計
 *
 * @param {string} prefecture - 都道府県名
 * @param {string} groupBy - 集計キー（"age_group", "gender", "municipality"など）
 * @return {Object} 集計結果
 * @example
 * var summary = summarizePersonaLevelData('京都府', 'age_group');
 * // { "20代": 120, "30代": 150, "40代": 180, "50代": 151 }
 */
function summarizePersonaLevelData(prefecture, groupBy) {
  Logger.log('[PersonaLevel] 集計開始: groupBy=' + groupBy);

  const data = getPersonaLevelData(prefecture);

  const summary = {};

  data.personas.forEach(function(persona) {
    const key = persona[groupBy];
    if (key) {
      if (!summary[key]) {
        summary[key] = 0;
      }
      summary[key] += 1;
    }
  });

  Logger.log('[PersonaLevel] 集計完了: ' + Object.keys(summary).length + 'グループ');

  return {
    prefecture: prefecture,
    groupBy: groupBy,
    summary: summary,
    totalGroups: Object.keys(summary).length
  };
}

/**
 * ペルソナ難易度分析（希少性スコアベース）
 *
 * @param {string} prefecture - 都道府県名
 * @param {Object} filters - フィルタ条件（filterPersonaLevelDataと同じ）
 * @return {Object} 難易度分析結果
 * @example
 * var difficulty = analyzePersonaDifficulty('京都府', {
 *   age_group: '50代',
 *   gender: '女性',
 *   has_national_license: true
 * });
 * // difficulty.avgRarityScore: 0.25
 * // difficulty.difficultyLevel: "B: 希少（3-5人）"
 */
function analyzePersonaDifficulty(prefecture, filters) {
  Logger.log('[PersonaLevel] 難易度分析開始');

  const filtered = filterPersonaLevelData(prefecture, filters);

  if (filtered.personas.length === 0) {
    return {
      prefecture: prefecture,
      filters: filters,
      avgRarityScore: null,
      difficultyLevel: 'データなし',
      matchCount: 0
    };
  }

  // 平均希少性スコア計算
  let totalRarityScore = 0;
  let validCount = 0;
  const rarityRanks = {};

  filtered.personas.forEach(function(persona) {
    if (persona.phase13_rarity_score !== null && persona.phase13_rarity_score !== undefined && persona.phase13_rarity_score !== '') {
      totalRarityScore += parseFloat(persona.phase13_rarity_score);
      validCount += 1;

      // ランク集計
      const rank = persona.phase13_rarity_rank || '不明';
      rarityRanks[rank] = (rarityRanks[rank] || 0) + 1;
    }
  });

  const avgRarityScore = validCount > 0 ? totalRarityScore / validCount : null;

  // 難易度レベル判定
  let difficultyLevel = '不明';
  if (avgRarityScore !== null) {
    if (avgRarityScore >= 0.5) {
      difficultyLevel = 'S: 超希少（採用困難）';
    } else if (avgRarityScore >= 0.2) {
      difficultyLevel = 'A: とても希少（採用難）';
    } else if (avgRarityScore >= 0.05) {
      difficultyLevel = 'B: 希少（やや難）';
    } else if (avgRarityScore >= 0.01) {
      difficultyLevel = 'C: やや希少（標準）';
    } else {
      difficultyLevel = 'D: 一般的（容易）';
    }
  }

  Logger.log('[PersonaLevel] 難易度分析完了: avgRarityScore=' + avgRarityScore);

  return {
    prefecture: prefecture,
    filters: filters,
    avgRarityScore: avgRarityScore,
    difficultyLevel: difficultyLevel,
    rarityRanks: rarityRanks,
    matchCount: filtered.personas.length,
    validCount: validCount
  };
}

/**
 * 市区町村別のペルソナ難易度ランキング
 *
 * @param {string} prefecture - 都道府県名
 * @param {number=} topN - 上位N件（デフォルト: 10）
 * @return {Array} ランキング配列
 */
function getMunicipalityDifficultyRanking(prefecture, topN) {
  topN = topN || 10;

  Logger.log('[PersonaLevel] 市区町村難易度ランキング取得: top' + topN);

  const data = getPersonaLevelData(prefecture);

  // 市区町村ごとに平均希少性スコアを計算
  const muniScores = {};

  data.personas.forEach(function(persona) {
    const muni = persona.municipality;
    if (!muni) return;

    if (!muniScores[muni]) {
      muniScores[muni] = {
        municipality: muni,
        totalScore: 0,
        count: 0
      };
    }

    if (persona.phase13_rarity_score !== null && persona.phase13_rarity_score !== undefined && persona.phase13_rarity_score !== '') {
      muniScores[muni].totalScore += parseFloat(persona.phase13_rarity_score);
      muniScores[muni].count += 1;
    }
  });

  // 平均スコア計算とソート
  const ranking = Object.values(muniScores)
    .map(function(item) {
      return {
        municipality: item.municipality,
        avgRarityScore: item.count > 0 ? item.totalScore / item.count : 0,
        personaCount: item.count
      };
    })
    .sort(function(a, b) {
      return b.avgRarityScore - a.avgRarityScore;
    })
    .slice(0, topN);

  Logger.log('[PersonaLevel] ランキング取得完了: ' + ranking.length + '件');

  return ranking;
}

/**
 * 統合シートが存在するかチェック
 *
 * @param {string} prefecture - 都道府県名
 * @return {boolean} 存在する場合true
 */
function checkPersonaLevelSheetExists(prefecture) {
  const sheetName = 'PersonaLevel_' + prefecture;
  const ss = getPersonaLevelSpreadsheet_();
  const sheet = ss.getSheetByName(sheetName);
  return sheet !== null;
}

/**
 * 利用可能な都道府県リストを取得
 *
 * @return {Array<string>} 都道府県名の配列
 */
function getAvailablePrefectures() {
  const ss = getPersonaLevelSpreadsheet_();
  const sheets = ss.getSheets();

  const prefectures = sheets
    .map(function(sheet) {
      const name = sheet.getName();
      if (name.indexOf('PersonaLevel_') === 0) {
        return name.replace('PersonaLevel_', '');
      }
      return null;
    })
    .filter(function(pref) {
      return pref !== null;
    });

  Logger.log('[PersonaLevel] 利用可能な都道府県: ' + prefectures.length + '件');

  return prefectures;
}

/**
 * テスト関数: 京都府データ取得
 */
function testPersonaLevelDataKyoto() {
  try {
    Logger.log('=== PersonaLevel データ取得テスト（京都府）===');

    const data = getPersonaLevelData('京都府');
    Logger.log('✅ データ取得成功');
    Logger.log('  - ペルソナ数: ' + data.personas.length);
    Logger.log('  - 列数: ' + data.metadata.colCount);
    Logger.log('  - ロード時間: ' + data.metadata.loadTime + '秒');

    // サンプルデータ表示
    if (data.personas.length > 0) {
      Logger.log('  - サンプル: ' + JSON.stringify(data.personas[0]));
    }

    return data;
  } catch (e) {
    Logger.log('❌ エラー: ' + e.toString());
    throw e;
  }
}

/**
 * テスト関数: フィルタリング
 */
function testPersonaLevelFiltering() {
  try {
    Logger.log('=== PersonaLevel フィルタリングテスト ===');

    const filtered = filterPersonaLevelData('京都府', {
      age_group: '50代',
      gender: '女性',
      has_national_license: false
    });

    Logger.log('✅ フィルタリング成功');
    Logger.log('  - 元データ: ' + filtered.metadata.originalCount + '件');
    Logger.log('  - フィルタ後: ' + filtered.metadata.filteredCount + '件');
    Logger.log('  - 処理時間: ' + filtered.metadata.filterTime + '秒');

    return filtered;
  } catch (e) {
    Logger.log('❌ エラー: ' + e.toString());
    throw e;
  }
}

/**
 * テスト関数: 難易度分析
 */
function testPersonaDifficultyAnalysis() {
  try {
    Logger.log('=== PersonaLevel 難易度分析テスト ===');

    const difficulty = analyzePersonaDifficulty('京都府', {
      age_group: '50代',
      gender: '女性',
      has_national_license: true
    });

    Logger.log('✅ 難易度分析成功');
    Logger.log('  - 平均希少性スコア: ' + difficulty.avgRarityScore);
    Logger.log('  - 難易度レベル: ' + difficulty.difficultyLevel);
    Logger.log('  - マッチ数: ' + difficulty.matchCount + '件');

    return difficulty;
  } catch (e) {
    Logger.log('❌ エラー: ' + e.toString());
    throw e;
  }
}
