/**
 * GASロジックのNode.js再現
 * Google Apps Script の主要な処理ロジックをNode.js環境で再現
 */

const fs = require('fs');
const path = require('path');

/**
 * CSVファイルを読み込んでパースする
 * @param {string} filePath - CSVファイルのパス
 * @returns {Array<Object>} - パースされたデータの配列
 */
function readCSV(filePath) {
  const content = fs.readFileSync(filePath, 'utf-8');
  const lines = content.trim().split('\n');

  if (lines.length === 0) {
    return [];
  }

  // ヘッダー行を解析
  const headers = lines[0].split(',').map(h => h.trim().replace(/^"|"$/g, ''));

  // データ行を解析
  const data = [];
  for (let i = 1; i < lines.length; i++) {
    const values = parseCSVLine(lines[i]);
    if (values.length === headers.length) {
      const row = {};
      headers.forEach((header, index) => {
        row[header] = values[index];
      });
      data.push(row);
    }
  }

  return data;
}

/**
 * CSV行をパースする（カンマ区切りで引用符を考慮）
 * @param {string} line - CSV行
 * @returns {Array<string>} - パースされた値の配列
 */
function parseCSVLine(line) {
  const values = [];
  let current = '';
  let inQuotes = false;

  for (let i = 0; i < line.length; i++) {
    const char = line[i];

    if (char === '"') {
      inQuotes = !inQuotes;
    } else if (char === ',' && !inQuotes) {
      values.push(current.trim().replace(/^"|"$/g, ''));
      current = '';
    } else {
      current += char;
    }
  }

  // 最後の値を追加
  values.push(current.trim().replace(/^"|"$/g, ''));

  return values;
}

/**
 * MapMetrics.csvを検証する
 * @param {Array<Object>} data - MapMetricsデータ
 * @returns {Object} - 検証結果
 */
function validateMapMetrics(data) {
  const result = {
    valid: true,
    errors: [],
    warnings: [],
    statistics: {}
  };

  // 必須カラムチェック
  const requiredColumns = ['都道府県', '市区町村', 'キー', 'カウント', '緯度', '経度'];

  if (data.length === 0) {
    result.valid = false;
    result.errors.push('データが空です');
    return result;
  }

  const firstRow = data[0];
  requiredColumns.forEach(col => {
    if (!(col in firstRow)) {
      result.valid = false;
      result.errors.push(`必須カラム '${col}' が見つかりません`);
    }
  });

  if (!result.valid) {
    return result;
  }

  // データ品質チェック
  let validCoords = 0;
  let invalidCoords = 0;
  let totalCount = 0;

  data.forEach((row, index) => {
    // 座標の検証
    const lat = parseFloat(row['緯度']);
    const lng = parseFloat(row['経度']);

    if (isNaN(lat) || isNaN(lng)) {
      invalidCoords++;
      result.warnings.push(`行${index + 2}: 無効な座標 (緯度=${row['緯度']}, 経度=${row['経度']})`);
    } else if (lat < -90 || lat > 90 || lng < -180 || lng > 180) {
      invalidCoords++;
      result.warnings.push(`行${index + 2}: 範囲外の座標 (緯度=${lat}, 経度=${lng})`);
    } else {
      validCoords++;
    }

    // カウントの検証
    const count = parseInt(row['カウント']);
    if (isNaN(count) || count < 0) {
      result.warnings.push(`行${index + 2}: 無効なカウント値 (${row['カウント']})`);
    } else {
      totalCount += count;
    }

    // キーの検証
    if (!row['キー'] || row['キー'].length === 0) {
      result.warnings.push(`行${index + 2}: 空のキー`);
    }
  });

  // 統計情報
  result.statistics = {
    totalRows: data.length,
    validCoords: validCoords,
    invalidCoords: invalidCoords,
    totalCount: totalCount,
    avgCountPerLocation: totalCount / data.length
  };

  // 警告が多すぎる場合はエラーに昇格
  if (invalidCoords > data.length * 0.5) {
    result.valid = false;
    result.errors.push(`座標の50%以上が無効です (${invalidCoords}/${data.length})`);
  }

  return result;
}

/**
 * Applicants.csvを検証する
 * @param {Array<Object>} data - Applicantsデータ
 * @returns {Object} - 検証結果
 */
function validateApplicants(data) {
  const result = {
    valid: true,
    errors: [],
    warnings: [],
    statistics: {}
  };

  // 必須カラムチェック
  const requiredColumns = ['ID', '性別', '年齢', '年齢バケット', '居住地_都道府県', '居住地_市区町村'];

  if (data.length === 0) {
    result.valid = false;
    result.errors.push('データが空です');
    return result;
  }

  const firstRow = data[0];
  requiredColumns.forEach(col => {
    if (!(col in firstRow)) {
      result.valid = false;
      result.errors.push(`必須カラム '${col}' が見つかりません`);
    }
  });

  if (!result.valid) {
    return result;
  }

  // データ品質チェック
  let validGender = 0;
  let validAge = 0;
  const genderCount = { '男性': 0, '女性': 0, '': 0 };
  const ageDistribution = {};

  data.forEach((row, index) => {
    // 性別の検証
    if (row['性別'] === '男性' || row['性別'] === '女性') {
      validGender++;
      genderCount[row['性別']]++;
    } else {
      genderCount['']++;
    }

    // 年齢の検証
    const age = parseInt(row['年齢']);
    if (!isNaN(age) && age >= 0 && age <= 120) {
      validAge++;
      const bucket = row['年齢バケット'] || 'unknown';
      ageDistribution[bucket] = (ageDistribution[bucket] || 0) + 1;
    }

    // IDの検証
    if (!row['ID'] || row['ID'].length === 0) {
      result.warnings.push(`行${index + 2}: 空のID`);
    }
  });

  // 統計情報
  result.statistics = {
    totalRows: data.length,
    validGender: validGender,
    validAge: validAge,
    genderDistribution: genderCount,
    ageDistribution: ageDistribution,
    genderCompleteness: (validGender / data.length * 100).toFixed(2) + '%',
    ageCompleteness: (validAge / data.length * 100).toFixed(2) + '%'
  };

  return result;
}

/**
 * DesiredWork.csvを検証する
 * @param {Array<Object>} data - DesiredWorkデータ
 * @returns {Object} - 検証結果
 */
function validateDesiredWork(data) {
  const result = {
    valid: true,
    errors: [],
    warnings: [],
    statistics: {}
  };

  // 必須カラムチェック
  const requiredColumns = ['申請者ID', '希望勤務地_都道府県', '希望勤務地_市区町村', 'キー'];

  if (data.length === 0) {
    result.valid = false;
    result.errors.push('データが空です');
    return result;
  }

  const firstRow = data[0];
  requiredColumns.forEach(col => {
    if (!(col in firstRow)) {
      result.valid = false;
      result.errors.push(`必須カラム '${col}' が見つかりません`);
    }
  });

  if (!result.valid) {
    return result;
  }

  // データ品質チェック
  const prefectureCounts = {};
  const uniqueApplicants = new Set();

  data.forEach((row, index) => {
    // 申請者IDの記録
    if (row['申請者ID']) {
      uniqueApplicants.add(row['申請者ID']);
    }

    // 都道府県の集計
    const pref = row['希望勤務地_都道府県'];
    if (pref) {
      prefectureCounts[pref] = (prefectureCounts[pref] || 0) + 1;
    }

    // キーの検証
    if (!row['キー'] || row['キー'].length === 0) {
      result.warnings.push(`行${index + 2}: 空のキー`);
    }
  });

  // Top 5 都道府県
  const top5Prefs = Object.entries(prefectureCounts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 5)
    .map(([pref, count]) => ({ prefecture: pref, count: count }));

  // 統計情報
  result.statistics = {
    totalRows: data.length,
    uniqueApplicants: uniqueApplicants.size,
    avgDesiredPerApplicant: (data.length / uniqueApplicants.size).toFixed(2),
    totalPrefectures: Object.keys(prefectureCounts).length,
    top5Prefectures: top5Prefs
  };

  return result;
}

/**
 * Phase 1の全ファイルを検証する
 * @param {string} phase1Dir - Phase 1出力ディレクトリ
 * @returns {Object} - 検証結果サマリー
 */
/**
 * Phase 2（統計検定）を検証する
 * @param {Array<Object>} chiSquareData - カイ二乗検定データ
 * @param {Array<Object>} anovaData - ANOVA検定データ
 * @returns {Object} - 検証結果
 */
function validatePhase2(chiSquareData, anovaData) {
  const result = {
    valid: true,
    errors: [],
    warnings: [],
    statistics: {}
  };

  // カイ二乗検定の検証
  if (!chiSquareData || chiSquareData.length === 0) {
    result.valid = false;
    result.errors.push('カイ二乗検定データが空です');
    return result;
  }

  const chiSquareColumns = ['pattern', 'group1', 'group2', 'variable', 'chi_square', 'p_value'];
  const firstRow = chiSquareData[0];
  chiSquareColumns.forEach(col => {
    if (!(col in firstRow)) {
      result.valid = false;
      result.errors.push(`カイ二乗検定: 必須カラム '${col}' が見つかりません`);
    }
  });

  // ANOVA検定の検証
  if (!anovaData || anovaData.length === 0) {
    result.valid = false;
    result.errors.push('ANOVA検定データが空です');
    return result;
  }

  const anovaColumns = ['pattern', 'dependent_var', 'independent_var', 'f_statistic', 'p_value'];
  const firstAnovaRow = anovaData[0];
  anovaColumns.forEach(col => {
    if (!(col in firstAnovaRow)) {
      result.valid = false;
      result.errors.push(`ANOVA検定: 必須カラム '${col}' が見つかりません`);
    }
  });

  // 統計情報
  result.statistics = {
    chiSquareTests: chiSquareData.length,
    anovaTests: anovaData.length,
    totalTests: chiSquareData.length + anovaData.length
  };

  return result;
}

/**
 * Phase 3（ペルソナ分析）を検証する
 * @param {Array<Object>} summaryData - ペルソナサマリーデータ
 * @param {Array<Object>} detailsData - ペルソナ詳細データ
 * @returns {Object} - 検証結果
 */
function validatePhase3(summaryData, detailsData) {
  const result = {
    valid: true,
    errors: [],
    warnings: [],
    statistics: {}
  };

  // サマリーの検証
  if (!summaryData || summaryData.length === 0) {
    result.valid = false;
    result.errors.push('ペルソナサマリーデータが空です');
    return result;
  }

  const summaryColumns = ['segment_id', 'segment_name', 'count', 'percentage', 'avg_age', 'female_ratio'];
  const firstRow = summaryData[0];
  summaryColumns.forEach(col => {
    if (!(col in firstRow)) {
      result.valid = false;
      result.errors.push(`ペルソナサマリー: 必須カラム '${col}' が見つかりません`);
    }
  });

  // 詳細の検証
  if (!detailsData || detailsData.length === 0) {
    result.warnings.push('ペルソナ詳細データが空です');
  } else {
    const detailColumns = ['segment_id', 'segment_name', 'detail_type', 'detail_key', 'detail_value'];
    const firstDetailRow = detailsData[0];
    detailColumns.forEach(col => {
      if (!(col in firstDetailRow)) {
        result.valid = false;
        result.errors.push(`ペルソナ詳細: 必須カラム '${col}' が見つかりません`);
      }
    });
  }

  // 統計情報
  let totalCount = 0;
  summaryData.forEach(row => {
    const count = parseInt(row['count']);
    if (!isNaN(count)) {
      totalCount += count;
    }
  });

  result.statistics = {
    totalPersonas: summaryData.length,
    totalApplicants: totalCount,
    avgApplicantsPerPersona: (totalCount / summaryData.length).toFixed(0),
    detailRecords: detailsData ? detailsData.length : 0
  };

  return result;
}

/**
 * Phase 7（拡張分析）を検証する
 * @param {Array<Object>} ageGenderData - 年齢×性別クロス分析データ
 * @param {Array<Object>} mobilityData - モビリティスコアデータ
 * @param {Array<Object>} supplyDensityData - 供給密度データ
 * @param {Array<Object>} personaProfileData - 詳細ペルソナプロファイルデータ
 * @returns {Object} - 検証結果
 */
function validatePhase7(ageGenderData, mobilityData, supplyDensityData, personaProfileData) {
  const result = {
    valid: true,
    errors: [],
    warnings: [],
    statistics: {}
  };

  // 各データセットの検証
  const datasets = [
    { data: ageGenderData, name: '年齢×性別クロス分析', columns: ['age_bucket', 'gender', 'count'] },
    { data: mobilityData, name: 'モビリティスコア', columns: ['applicant_id', 'mobility_score'] },
    { data: supplyDensityData, name: '供給密度', columns: ['location', 'density_score'] },
    { data: personaProfileData, name: '詳細ペルソナプロファイル', columns: ['segment_id', 'profile_type'] }
  ];

  datasets.forEach(dataset => {
    if (!dataset.data || dataset.data.length === 0) {
      result.warnings.push(`${dataset.name}データが空です`);
      return;
    }

    const firstRow = dataset.data[0];
    dataset.columns.forEach(col => {
      if (!(col in firstRow)) {
        result.warnings.push(`${dataset.name}: カラム '${col}' が見つかりません`);
      }
    });
  });

  // 統計情報
  result.statistics = {
    ageGenderRecords: ageGenderData ? ageGenderData.length : 0,
    mobilityRecords: mobilityData ? mobilityData.length : 0,
    supplyDensityRecords: supplyDensityData ? supplyDensityData.length : 0,
    personaProfileRecords: personaProfileData ? personaProfileData.length : 0
  };

  return result;
}

function validatePhase1(phase1Dir) {
  const results = {
    overall: { valid: true, errors: [], warnings: [] },
    mapMetrics: null,
    applicants: null,
    desiredWork: null,
    aggDesired: null
  };

  try {
    // MapMetrics.csv
    const mapMetricsPath = path.join(phase1Dir, 'MapMetrics.csv');
    if (fs.existsSync(mapMetricsPath)) {
      const mapMetricsData = readCSV(mapMetricsPath);
      results.mapMetrics = validateMapMetrics(mapMetricsData);

      if (!results.mapMetrics.valid) {
        results.overall.valid = false;
        results.overall.errors.push('MapMetrics.csv の検証に失敗しました');
      }
    } else {
      results.overall.valid = false;
      results.overall.errors.push('MapMetrics.csv が見つかりません');
    }

    // Applicants.csv
    const applicantsPath = path.join(phase1Dir, 'Applicants.csv');
    if (fs.existsSync(applicantsPath)) {
      const applicantsData = readCSV(applicantsPath);
      results.applicants = validateApplicants(applicantsData);

      if (!results.applicants.valid) {
        results.overall.valid = false;
        results.overall.errors.push('Applicants.csv の検証に失敗しました');
      }
    } else {
      results.overall.valid = false;
      results.overall.errors.push('Applicants.csv が見つかりません');
    }

    // DesiredWork.csv
    const desiredWorkPath = path.join(phase1Dir, 'DesiredWork.csv');
    if (fs.existsSync(desiredWorkPath)) {
      const desiredWorkData = readCSV(desiredWorkPath);
      results.desiredWork = validateDesiredWork(desiredWorkData);

      if (!results.desiredWork.valid) {
        results.overall.valid = false;
        results.overall.errors.push('DesiredWork.csv の検証に失敗しました');
      }
    } else {
      results.overall.valid = false;
      results.overall.errors.push('DesiredWork.csv が見つかりません');
    }

    // AggDesired.csv
    const aggDesiredPath = path.join(phase1Dir, 'AggDesired.csv');
    if (fs.existsSync(aggDesiredPath)) {
      const aggDesiredData = readCSV(aggDesiredPath);
      // AggDesiredはMapMetricsと同じ構造なので同じ検証を使用
      results.aggDesired = validateMapMetrics(aggDesiredData);

      if (!results.aggDesired.valid) {
        results.overall.valid = false;
        results.overall.errors.push('AggDesired.csv の検証に失敗しました');
      }
    } else {
      results.overall.valid = false;
      results.overall.errors.push('AggDesired.csv が見つかりません');
    }

    // 整合性チェック
    if (results.mapMetrics && results.desiredWork) {
      const mapMetricsCount = results.mapMetrics.statistics.totalCount;
      const desiredWorkCount = results.desiredWork.statistics.totalRows;

      // MapMetricsのカウント合計とDesiredWorkの行数が一致するはず
      if (Math.abs(mapMetricsCount - desiredWorkCount) > 10) {
        results.overall.warnings.push(
          `データ整合性: MapMetricsのカウント合計(${mapMetricsCount})とDesiredWorkの行数(${desiredWorkCount})に大きな差異があります`
        );
      }
    }

    if (results.applicants && results.desiredWork) {
      const applicantsCount = results.applicants.statistics.totalRows;
      const uniqueApplicants = results.desiredWork.statistics.uniqueApplicants;

      // Applicantsの行数とDesiredWorkの一意申請者数が一致するはず
      if (applicantsCount !== uniqueApplicants) {
        results.overall.warnings.push(
          `データ整合性: Applicantsの行数(${applicantsCount})とDesiredWorkの一意申請者数(${uniqueApplicants})が不一致です`
        );
      }
    }

  } catch (error) {
    results.overall.valid = false;
    results.overall.errors.push(`検証中にエラーが発生しました: ${error.message}`);
  }

  return results;
}

module.exports = {
  readCSV,
  validateMapMetrics,
  validateApplicants,
  validateDesiredWork,
  validatePhase1,
  validatePhase2,
  validatePhase3,
  validatePhase7
};
