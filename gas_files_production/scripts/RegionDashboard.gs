/**
 * RegionDashboard - フェーズ別の地域データAPIを提供する。
 * 各フェーズのシートから必要なデータを抽出し、フロントエンドで利用しやすい形に整形する。
 */

const REGION_DASHBOARD_SHEETS = {
  phase1: {
    mapMetrics: ['MapMetrics'],
    aggDesired: ['AggDesired'],
    quality: ['P1_QualityReport', 'QualityReport']
  },
  phase2: {
    chiSquare: ['ChiSquareTests'],
    anova: ['ANOVATests'],
    quality: ['P2_QualityReport_Inferential', 'QualityReport_Inferential']
  },
  phase3: {
    summary: ['PersonaSummary'],
    details: ['PersonaDetails'],
    quality: ['P3_QualityReport_Inferential', 'QualityReport_Inferential']
  },
  phase7: {
    supply: ['SupplyDensityMap'],
    qualification: ['QualificationDistribution'],
    ageGender: ['AgeGenderCrossAnalysis'],
    mobility: ['MobilityScore'],
    personaProfile: ['DetailedPersonaProfile'],
    quality: ['P7_QualityReport_Inferential', 'QualityReport_Inferential']
  },
  phase8: {
    education: ['EducationDistribution'],
    educationCross: ['EducationAgeCross', 'EducationAgeCross_Matrix'],
    graduation: ['GraduationYearDistribution'],
    quality: ['P8_QualityReport', 'QualityReport', 'P8_QualityReport_Inferential']
  },
  phase10: {
    urgency: ['UrgencyDistribution_ByMunicipality', 'UrgencyDistribution'],
    ageCross: ['UrgencyAgeCross_ByMunicipality', 'UrgencyAgeCross'],
    employmentCross: ['UrgencyEmploymentCross_ByMunicipality', 'UrgencyEmploymentCross'],
    desiredWorkCross: ['UrgencyDesiredWorkCross'],
    quality: ['P10_QualityReport', 'QualityReport', 'P10_QualityReport_Inferential']
  }
};

const REGION_DASHBOARD_COLUMN_ALIASES = {
  都道府県: 'prefecture',
  市区町村: 'municipality',
  自治体: 'municipality',
  '希望勤務地_都道府県': 'prefecture',
  '希望勤務地_市区町村': 'municipality',
  地域キー: 'regionKey',
  キー: 'regionKey',
  lat: 'latitude',
  lng: 'longitude',
  緯度: 'latitude',
  経度: 'longitude',
  カウント: 'count',
  件数: 'count',
  '希望求職者': 'count',
  '応募者数': 'count',
  '希望者数': 'count',
  比率: 'ratio',
  割合: 'ratio',
  スコア: 'score',
  スコアリング: 'score',
  緊急度: 'urgencyLevel',
  urgency_score: 'urgencyScore',
  segment_id: 'segmentId',
  segment_name: 'segmentName',
  avg_age: 'avgAge',
  avg_desired_locations: 'avgDesiredLocations',
  avg_qualifications: 'avgQualifications',
  average_desired_locations: 'avgDesiredLocations',
  average_qualifications: 'avgQualifications',
  female_ratio: 'femaleRatio',
  ratio: 'percentage',
  percentage: 'percentage'
};

const REGION_FILTER_MAPPINGS = {
  mapMetrics: { prefecture: ['prefecture', '都道府県'], municipality: ['municipality', '市区町村'], regionKey: ['regionKey', 'キー'] },
  aggDesired: { prefecture: ['prefecture', '希望勤務地_都道府県'], municipality: ['municipality', '希望勤務地_市区町村'], regionKey: ['regionKey', 'キー'] },
  genericPrefecture: { prefecture: ['prefecture', '都道府県'] },
  municipalityOnly: { municipality: ['municipality', '市区町村'] }
};

const REGION_VALUE_COLUMNS = {
  applicantCount: ['count', 'カウント', '希望求職者', '応募者数', '希望者数']
};

/**
 * Phase1 指標を取得。
 */
function fetchPhase1Metrics(prefecture, municipality) {
  const ctx = resolveRegionContext(prefecture, municipality);
  const warnings = [];

  const mapMetrics = filterByRegion(
    readFirstAvailableSheet(REGION_DASHBOARD_SHEETS.phase1.mapMetrics),
    ctx,
    REGION_FILTER_MAPPINGS.mapMetrics,
    warnings,
    'MapMetrics'
  );

  const aggDesired = filterByRegion(
    readFirstAvailableSheet(REGION_DASHBOARD_SHEETS.phase1.aggDesired),
    ctx,
    REGION_FILTER_MAPPINGS.aggDesired,
    warnings,
    'AggDesired'
  );

  const quality = readFirstAvailableSheet(REGION_DASHBOARD_SHEETS.phase1.quality);

  const applicantTotal = sumNumericValues(mapMetrics, REGION_VALUE_COLUMNS.applicantCount);

  return {
    region: ctx,
    summary: {
      applicantCount: applicantTotal,
      mapRecords: mapMetrics.length,
      aggDesiredRecords: aggDesired.length
    },
    tables: {
      mapMetrics: mapMetrics,
      aggDesired: aggDesired,
      quality: filterByRegionIfPossible(quality, ctx, REGION_FILTER_MAPPINGS.mapMetrics)
    },
    warnings: warnings
  };
}

/**
 * Phase2 (統計検定) データを取得。
 */
function fetchPhase2Stats(prefecture, municipality) {
  const ctx = resolveRegionContext(prefecture, municipality);
  const warnings = [];

  const chiSquare = readFirstAvailableSheet(REGION_DASHBOARD_SHEETS.phase2.chiSquare);
  const anova = readFirstAvailableSheet(REGION_DASHBOARD_SHEETS.phase2.anova);
  const quality = readFirstAvailableSheet(REGION_DASHBOARD_SHEETS.phase2.quality);

  if (chiSquare.length) {
    warnings.push('ChiSquareTestsは地域列を持たないため、選択地域の結果を直接抽出できません。');
  }
  if (anova.length) {
    warnings.push('ANOVATestsは地域列を持たないため、選択地域の結果を直接抽出できません。');
  }

  return {
    region: ctx,
    summary: {
      chiSquareTests: chiSquare.length,
      anovaTests: anova.length
    },
    tables: {
      chiSquare: chiSquare,
      anova: anova,
      quality: quality
    },
    warnings: warnings
  };
}

/**
 * Phase3 (ペルソナ分析) データを取得。
 * @param {string} prefecture
 * @param {string} municipality
 * @param {{segmentId: number|string}} filters
 */
function fetchPhase3Persona(prefecture, municipality, filters) {
  const ctx = resolveRegionContext(prefecture, municipality);
  const warnings = [];

  const rawSummary = readFirstAvailableSheet(REGION_DASHBOARD_SHEETS.phase3.summary);
  const summary = augmentPersonaDifficulty(rawSummary);
  const details = readFirstAvailableSheet(REGION_DASHBOARD_SHEETS.phase3.details);
  const quality = readFirstAvailableSheet(REGION_DASHBOARD_SHEETS.phase3.quality);

  const filteredSummary = applyPersonaFilters(summary, filters);
  const filteredDetails = applyPersonaFilters(details, filters);

  if (summary.length) {
    warnings.push('PersonaSummary は地域列を持たないため、地域別フィルタリングは未対応です。');
  }

  const difficultyStats = calculateDifficultySummary(filteredSummary);

  return {
    region: ctx,
    summary: {
      personaSegments: filteredSummary.length,
      averageDifficultyScore: difficultyStats.averageScore,
      topDifficultyLevel: difficultyStats.topLevel
    },
    tables: {
      personaSummary: filteredSummary,
      personaDetails: filteredDetails,
      quality: quality
    },
    warnings: warnings
  };
}

/**
 * Phase7 (高度分析) データを取得。
 */
function fetchPhase7Supply(prefecture, municipality) {
  const ctx = resolveRegionContext(prefecture, municipality);
  const warnings = [];

  const supply = filterByRegion(
    readFirstAvailableSheet(REGION_DASHBOARD_SHEETS.phase7.supply),
    ctx,
    REGION_FILTER_MAPPINGS.municipalityOnly,
    warnings,
    'SupplyDensityMap'
  );
  const qualification = filterByRegion(
    readFirstAvailableSheet(REGION_DASHBOARD_SHEETS.phase7.qualification),
    ctx,
    REGION_FILTER_MAPPINGS.municipalityOnly,
    warnings,
    'QualificationDistribution'
  );
  const ageGender = filterByRegion(
    readFirstAvailableSheet(REGION_DASHBOARD_SHEETS.phase7.ageGender),
    ctx,
    REGION_FILTER_MAPPINGS.municipalityOnly,
    warnings,
    'AgeGenderCrossAnalysis'
  );
  const mobility = filterByRegion(
    readFirstAvailableSheet(REGION_DASHBOARD_SHEETS.phase7.mobility),
    ctx,
    REGION_FILTER_MAPPINGS.municipalityOnly,
    warnings,
    'MobilityScore'
  );
  const personaProfile = filterByRegion(
    readFirstAvailableSheet(REGION_DASHBOARD_SHEETS.phase7.personaProfile),
    ctx,
    REGION_FILTER_MAPPINGS.municipalityOnly,
    warnings,
    'DetailedPersonaProfile'
  );
  const quality = readFirstAvailableSheet(REGION_DASHBOARD_SHEETS.phase7.quality);

  return {
    region: ctx,
    summary: {
      supplyRecords: supply.length,
      qualificationRecords: qualification.length,
      mobilityRecords: mobility.length
    },
    tables: {
      supplyDensity: supply,
      qualificationDistribution: qualification,
      ageGenderCross: ageGender,
      mobilityScore: mobility,
      personaProfile: personaProfile,
      quality: filterByRegionIfPossible(quality, ctx, REGION_FILTER_MAPPINGS.municipalityOnly)
    },
    warnings: warnings
  };
}

/**
 * Phase8 (学歴・キャリア) データを取得。
 */
function fetchPhase8Education(prefecture, municipality) {
  const ctx = resolveRegionContext(prefecture, municipality);
  const warnings = [];

  const education = readFirstAvailableSheet(REGION_DASHBOARD_SHEETS.phase8.education);
  const educationCross = readFirstAvailableSheet(REGION_DASHBOARD_SHEETS.phase8.educationCross);
  const graduation = readFirstAvailableSheet(REGION_DASHBOARD_SHEETS.phase8.graduation);
  const quality = readFirstAvailableSheet(REGION_DASHBOARD_SHEETS.phase8.quality);

  if (education.length) {
    warnings.push('EducationDistribution は地域列を持たないため、地域別フィルタリングは未対応です。');
  }

  return {
    region: ctx,
    summary: {
      educationBuckets: education.length,
      graduationBuckets: graduation.length
    },
    tables: {
      educationDistribution: education,
      educationCross: educationCross,
      graduationDistribution: graduation,
      quality: quality
    },
    warnings: warnings
  };
}

/**
 * Phase10 (転職意欲) データを取得。
 */
function fetchPhase10Urgency(prefecture, municipality) {
  const ctx = resolveRegionContext(prefecture, municipality);
  const warnings = [];

  const urgency = filterByRegion(
    readFirstAvailableSheet(REGION_DASHBOARD_SHEETS.phase10.urgency),
    ctx,
    REGION_FILTER_MAPPINGS.municipalityOnly,
    warnings,
    'UrgencyDistribution'
  );
  const ageCross = filterByRegion(
    readFirstAvailableSheet(REGION_DASHBOARD_SHEETS.phase10.ageCross),
    ctx,
    REGION_FILTER_MAPPINGS.municipalityOnly,
    warnings,
    'UrgencyAgeCross'
  );
  const employmentCross = filterByRegion(
    readFirstAvailableSheet(REGION_DASHBOARD_SHEETS.phase10.employmentCross),
    ctx,
    REGION_FILTER_MAPPINGS.municipalityOnly,
    warnings,
    'UrgencyEmploymentCross'
  );
  const desiredWorkCross = filterByRegion(
    readFirstAvailableSheet(REGION_DASHBOARD_SHEETS.phase10.desiredWorkCross),
    ctx,
    REGION_FILTER_MAPPINGS.municipalityOnly,
    warnings,
    'UrgencyDesiredWorkCross'
  );
  const quality = readFirstAvailableSheet(REGION_DASHBOARD_SHEETS.phase10.quality);

  return {
    region: ctx,
    summary: {
      urgencyRecords: urgency.length,
      ageCrossRecords: ageCross.length,
      employmentCrossRecords: employmentCross.length
    },
    tables: {
      urgencyDistribution: urgency,
      ageCross: ageCross,
      employmentCross: employmentCross,
      desiredWorkCross: desiredWorkCross,
      quality: filterByRegionIfPossible(quality, ctx, REGION_FILTER_MAPPINGS.municipalityOnly)
    },
    warnings: warnings
  };
}

/**
 * 地域コンテキストを解決する。
 */
function resolveRegionContext(prefecture, municipality) {
  const normalizedPref = normalizeRegionValue(prefecture);
  const normalizedMuni = normalizeRegionValue(municipality);

  if (normalizedPref) {
    const municipalities = getMunicipalitiesForPrefecture(normalizedPref);
    const resolvedMuni = normalizedMuni && municipalities.includes(normalizedMuni)
      ? normalizedMuni
      : (municipalities.length ? municipalities[0] : null);
    return {
      prefecture: normalizedPref,
      municipality: resolvedMuni,
      key: buildRegionKey(normalizedPref, resolvedMuni)
    };
  }

  return loadSelectedRegion();
}

/**
 * 最初に見つかったシートを読み込む。
 * @param {string[]} candidates
 * @return {Array<Object>}
 */
function readFirstAvailableSheet(candidates) {
  for (let i = 0; i < candidates.length; i += 1) {
    const sheetName = candidates[i];
    const rows = readSheetAsObjects(sheetName);
    if (rows.length) {
      return rows;
    }
  }
  return [];
}

/**
 * シートをオブジェクト配列に変換する。
 * @param {string} sheetName
 * @return {Array<Object>}
 */
function readSheetAsObjects(sheetName) {
  const rows = readSheetRows(sheetName);
  if (!rows.length) {
    return [];
  }

  const header = rows[0].map(value => (value !== null && value !== undefined ? String(value).trim() : ''));
  const records = [];

  for (let i = 1; i < rows.length; i += 1) {
    const row = rows[i];
    const record = {};
    const normalized = {};

    for (let col = 0; col < header.length; col += 1) {
      const sourceKey = header[col] || 'column_' + col;
      const value = row[col];
      record[sourceKey] = value;

      if (sourceKey) {
        normalized[sourceKey] = value;
      }

      const alias = REGION_DASHBOARD_COLUMN_ALIASES[sourceKey];
      if (alias) {
        normalized[alias] = value;
      }
    }

    record.__normalized = normalized;
    records.push(record);
  }

  return records;
}

/**
 * 指定したキー候補から値を取得する。
 * @param {Object} record
 * @param {string[]} candidates
 * @return {*}
 */
function extractValue(record, candidates) {
  if (!record) {
    return null;
  }

  for (let i = 0; i < candidates.length; i += 1) {
    const key = candidates[i];
    if (key === undefined || key === null) {
      continue;
    }
    if (record.hasOwnProperty(key)) {
      return record[key];
    }
    const normalized = record.__normalized || {};
    if (normalized.hasOwnProperty(key)) {
      return normalized[key];
    }
  }

  return null;
}

/**
 * レコードを地域でフィルタリングする。
 */
function filterByRegion(records, ctx, mapping, warnings, datasetLabel) {
  if (!records.length) {
    if (warnings && datasetLabel) {
      warnings.push(datasetLabel + ' シートが見つかりません。');
    }
    return [];
  }

  const filtered = records.filter(record => {
    if (ctx.prefecture && mapping.prefecture) {
      const pref = normalizeRegionValue(extractValue(record, mapping.prefecture));
      if (pref && pref !== ctx.prefecture) {
        return false;
      }
      if (!pref && mapping.prefecture.length) {
        return true;
      }
    }

    if (ctx.municipality && mapping.municipality) {
      const muni = normalizeRegionValue(extractValue(record, mapping.municipality));
      if (muni && muni !== ctx.municipality) {
        return false;
      }
      if (!muni && mapping.municipality.length) {
        return true;
      }
    }

    if (ctx.key && mapping.regionKey) {
      const keyValue = normalizeRegionValue(extractValue(record, mapping.regionKey));
      if (keyValue && keyValue !== ctx.key) {
        return false;
      }
    }

    return true;
  });

  if (!filtered.length && warnings && datasetLabel) {
    warnings.push(datasetLabel + ' で指定地域のデータが見つかりませんでした。');
  }

  return filtered;
}

/**
 * 可能なら地域フィルタを適用する。
 */
function filterByRegionIfPossible(records, ctx, mapping) {
  if (!records.length || !mapping) {
    return records;
  }
  const filtered = filterByRegion(records, ctx, mapping);
  return filtered.length ? filtered : records;
}

/**
 * 数値列を合計する。
 */
function sumNumericValues(records, candidates) {
  let total = 0;
  records.forEach(record => {
    const value = extractValue(record, candidates);
    const numeric = typeof value === 'number' ? value : parseFloat(String(value).replace(/,/g, ''));
    if (!isNaN(numeric)) {
      total += numeric;
    }
  });
  return total;
}

/**
 * ペルソナフィルタを適用する。
 */
function applyPersonaFilters(records, filters) {
  if (!records.length || !filters) {
    return records;
  }
  const normalizedFilters = {};
  if (filters.segmentId !== undefined && filters.segmentId !== null && filters.segmentId !== '') {
    normalizedFilters.segmentId = String(filters.segmentId).trim();
  }
  if (filters.difficultyLevel !== undefined && filters.difficultyLevel !== null && filters.difficultyLevel !== '') {
    normalizedFilters.difficultyLevel = String(filters.difficultyLevel).trim();
  }
  if (!Object.keys(normalizedFilters).length) {
    return records;
  }

  return records.filter(record => {
    if (normalizedFilters.segmentId) {
      const value = extractValue(record, ['segment_id', 'segmentId']);
      if (value === undefined || value === null) {
        return false;
      }
      if (String(value).trim() !== normalizedFilters.segmentId) {
        return false;
      }
    }
    if (normalizedFilters.difficultyLevel) {
      const value = extractValue(record, ['difficulty_level', 'difficultyLevel']);
      if (!value || String(value).trim() !== normalizedFilters.difficultyLevel) {
        return false;
      }
    }
    return true;
  });
}

/**
 * PersonaSummaryに難易度情報を付与する。
 * @param {Array<Object>} records
 * @return {Array<Object>}
 */
function augmentPersonaDifficulty(records) {
  if (!records.length) {
    return records;
  }

  return records.map(record => {
    const normalized = record.__normalized || {};
    const difficulty = calculatePersonaDifficultyScore(record);
    const clone = Object.assign({}, record);
    clone.difficulty_score = difficulty.score;
    clone.difficulty_level = difficulty.level;
    clone.__normalized = Object.assign({}, normalized, {
      difficultyScore: difficulty.score,
      difficulty_level: difficulty.level,
      difficultyLevel: difficulty.level
    });
    return clone;
  });
}

/**
 * 難易度のサマリー統計量を算出する。
 * @param {Array<Object>} records
 * @return {{averageScore: number, topLevel: string}}
 */
function calculateDifficultySummary(records) {
  if (!records.length) {
    return {
      averageScore: 0,
      topLevel: 'データなし'
    };
  }

  let total = 0;
  let count = 0;
  let topScore = -1;
  let topLevel = 'データなし';

  records.forEach(record => {
    const score = extractNumeric(record, ['difficulty_score', 'difficultyScore']);
    const level = extractValue(record, ['difficulty_level', 'difficultyLevel']);
    if (score !== null) {
      total += score;
      count += 1;
      if (score > topScore) {
        topScore = score;
        topLevel = level || topLevel;
      }
    }
  });

  return {
    averageScore: count ? Math.round((total / count) * 10) / 10 : 0,
    topLevel: topLevel || 'データなし'
  };
}

/**
 * 難易度スコアとランクを算出する。
 * @param {Object} record
 * @return {{score: number, level: string}}
 */
function calculatePersonaDifficultyScore(record) {
  const params = {
    avgQualifications: extractNumeric(record, ['avg_qualifications', 'avgQualifications', '平均資格数'], 0),
    avgDesiredLocations: extractNumeric(record, ['avg_desired_locations', 'avgDesiredLocations', '平均希望勤務地数'], 0),
    femaleRatio: extractNumeric(record, ['female_ratio', 'femaleRatio', '女性比率'], 0),
    count: extractNumeric(record, ['count', '人数'], 0),
    percentage: extractNumeric(record, ['ratio', 'percentage', '比率'], 0) * 100,
    avgAge: extractNumeric(record, ['avg_age', 'avgAge', '平均年齢'], 0)
  };

  const score = calculateDifficultyScore(params);
  const level = getDifficultyLevel(score);
  return {
    score: score,
    level: level
  };
}

/**
 * 数値を抽出するユーティリティ。
 */
function extractNumeric(record, candidates, defaultValue) {
  const raw = extractValue(record, candidates);
  if (raw === undefined || raw === null || raw === '') {
    return defaultValue !== undefined ? defaultValue : null;
  }
  const numeric = typeof raw === 'number' ? raw : parseFloat(String(raw).replace(/,/g, ''));
  if (isNaN(numeric)) {
    return defaultValue !== undefined ? defaultValue : null;
  }
  return numeric;
}

/**
 * 難易度スコア計算（PersonaDifficultyChecker と同ロジック）。
 */
function calculateDifficultyScore(params) {
  const qualScore = Math.min((params.avgQualifications || 0) * 15, 40);
  const mobilityScore = Math.min((params.avgDesiredLocations || 0) * 8, 25);
  const sizeScore = Math.max(0, 20 - (params.percentage || 0) * 2);
  const ageScore = getAgeScore(params.avgAge || 0);
  const genderScore = Math.abs((params.femaleRatio || 0) - 0.5) * 10;
  const total = qualScore + mobilityScore + sizeScore + ageScore + genderScore;
  return Math.min(Math.round(total), 100);
}

function getAgeScore(avgAge) {
  if (avgAge < 25) return 5;
  if (avgAge < 35) return 3;
  if (avgAge < 50) return 4;
  if (avgAge < 60) return 7;
  return 10;
}

function getDifficultyLevel(score) {
  if (score >= 80) return 'S級（最難）';
  if (score >= 65) return 'A級（難）';
  if (score >= 50) return 'B級（やや難）';
  if (score >= 35) return 'C級（普通）';
  if (score >= 20) return 'D級（やや易）';
  return 'E級（易）';
}
