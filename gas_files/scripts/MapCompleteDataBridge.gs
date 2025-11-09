/**
 * MapComplete Ver2 UI 向けデータ集約モジュール
 *
 * 既存の fetchPhaseX 系関数を組み合わせ、map_complete_prototype_Ver2.html が
 * 期待する JSON スキーマで地域別データを返却する。
 *
 * 返却形式:
 * {
 *   selectedRegion: { prefecture, municipality, key },
 *   regionOptions: getRegionOptions(),
 *   availableRegions: [{ prefecture, municipality, key, label }],
 *   cities: [ { ...cityData } ]
 * }
 *
 * パフォーマンス最適化:
 * - Spreadsheetオブジェクトのグローバルキャッシュ（実行中のみ有効）
 * - ScriptCacheによる5分間のデータキャッシュ（全ユーザー共有）
 * - タブ別遅延ロード（必要なPhaseデータのみ読み込み）
 */

/**
 * Spreadsheetオブジェクトのグローバルキャッシュ
 * スクリプト実行中のみ有効（複数のgetActiveSpreadsheet()呼び出しを1回に削減）
 */
var SPREADSHEET_CACHE_ = null;

/**
 * Spreadsheetオブジェクトを一度だけ取得
 * @return {Spreadsheet}
 */
function getSpreadsheetOnce_() {
  if (!SPREADSHEET_CACHE_) {
    Logger.log('[Batch] Spreadsheetオブジェクトを初回取得');
    SPREADSHEET_CACHE_ = SpreadsheetApp.getActiveSpreadsheet();
  }
  return SPREADSHEET_CACHE_;
}

/**
 * すべてのシートオブジェクトを一度に取得してマップ化
 * @return {Object.<string, Sheet>} シート名をキーとしたSheetオブジェクトのマップ
 */
function getAllSheetsMap_() {
  const ss = getSpreadsheetOnce_();
  const sheets = ss.getSheets();
  const sheetMap = {};

  sheets.forEach(function(sheet) {
    sheetMap[sheet.getName()] = sheet;
  });

  Logger.log('[Batch] ' + sheets.length + '個のシートを一括取得完了');
  return sheetMap;
}

/**
 * シート名でシートオブジェクトを取得（バッチ取得版）
 * @param {string} sheetName
 * @return {Sheet|null}
 */
function getSheetByNameBatched_(sheetName) {
  const ss = getSpreadsheetOnce_();
  return ss.getSheetByName(sheetName);
}

/**
 * MapComplete UI 向けデータを取得する。
 * @param {string=} prefecture
 * @param {string=} municipality
 * @return {Object}
 */
function getMapCompleteData(prefecture, municipality) {
  const cache = CacheService.getScriptCache();
  const cacheKey = 'mapComplete_' + (prefecture || '') + '_' + (municipality || '');

  // キャッシュをチェック（5分間有効）
  const cached = cache.get(cacheKey);
  if (cached) {
    try {
      Logger.log('[getMapCompleteData] キャッシュヒット: ' + cacheKey);
      return JSON.parse(cached);
    } catch (e) {
      Logger.log('[getMapCompleteData] キャッシュのパースに失敗: ' + e);
    }
  }

  Logger.log('[getMapCompleteData] キャッシュなし、データ取得開始: ' + cacheKey);

  // Spreadsheetオブジェクトを事前にキャッシュ（バッチ化最適化）
  getSpreadsheetOnce_();

  const regionOptions = getRegionOptions();
  const target = determineTargetRegion_(prefecture, municipality, regionOptions);

  // 選択状態を永続化
  saveSelectedRegion(target.prefecture, target.municipality);

  const cityData = buildMapCompleteCityData_(target.prefecture, target.municipality);
  const availableRegions = buildAvailableRegions_(target.prefecture);

  const result = {
    selectedRegion: target,
    regionOptions: getRegionOptions(), // 再取得して state を最新化
    availableRegions: availableRegions,
    cities: [cityData]
  };

  // 結果をキャッシュ（5分間）
  try {
    cache.put(cacheKey, JSON.stringify(result), 300);
    Logger.log('[getMapCompleteData] キャッシュに保存: ' + cacheKey);
  } catch (e) {
    Logger.log('[getMapCompleteData] キャッシュの保存に失敗（データサイズ超過の可能性）: ' + e);
  }

  return result;
}

/**
 * Phase 12-14統合ダッシュボード専用の軽量データ取得関数
 * パフォーマンス最適化版：Phase 12-14のデータのみを取得
 *
 * @param {string=} prefecture
 * @param {string=} municipality
 * @return {Object}
 */
function getMapCompleteDataPhase12to14Only(prefecture, municipality) {
  const cache = CacheService.getScriptCache();
  const cacheKey = 'phase12to14_' + (prefecture || '') + '_' + (municipality || '');

  // キャッシュをチェック（5分間有効）
  const cached = cache.get(cacheKey);
  if (cached) {
    try {
      return JSON.parse(cached);
    } catch (e) {
      Logger.log('[getMapCompleteDataPhase12to14Only] キャッシュのパースに失敗: ' + e);
    }
  }

  const regionOptions = getRegionOptions();
  const target = determineTargetRegion_(prefecture, municipality, regionOptions);

  // 選択状態を永続化
  saveSelectedRegion(target.prefecture, target.municipality);

  const cityData = buildMapCompleteCityDataPhase12to14Only_(target.prefecture, target.municipality);
  const availableRegions = buildAvailableRegions_(target.prefecture);

  const result = {
    selectedRegion: target,
    regionOptions: getRegionOptions(),
    availableRegions: availableRegions,
    cities: [cityData]
  };

  // 結果をキャッシュ（5分間）
  try {
    cache.put(cacheKey, JSON.stringify(result), 300);
  } catch (e) {
    Logger.log('[getMapCompleteDataPhase12to14Only] キャッシュの保存に失敗: ' + e);
  }

  return result;
}

/**
 * リクエスト時のターゲット地域を決定する。
 * @param {string=} prefecture
 * @param {string=} municipality
 * @param {Object} regionOptions
 * @return {{prefecture: string, municipality: string, key: string}}
 */
function determineTargetRegion_(prefecture, municipality, regionOptions) {
  const state = (regionOptions && regionOptions.state) || {};
  let resolvedPrefecture = prefecture || state.prefecture;
  let resolvedMunicipality = municipality || state.municipality;

  if (!resolvedPrefecture) {
    const candidates = (regionOptions && regionOptions.prefectures) || getAvailablePrefectures();
    resolvedPrefecture = candidates.length ? candidates[0] : null;
  }

  if (resolvedPrefecture && !resolvedMunicipality) {
    const municipalities = getMunicipalitiesForPrefecture(resolvedPrefecture);
    resolvedMunicipality = municipalities.length ? municipalities[0] : null;
  }

  if (!resolvedPrefecture || !resolvedMunicipality) {
    throw new Error('対象地域を特定できませんでした。');
  }

  var prefClean = sanitizeString_(resolvedPrefecture);
  var muniClean = sanitizeString_(resolvedMunicipality);
  return {
    prefecture: prefClean,
    municipality: muniClean,
    key: buildRegionKey(prefClean, muniClean)
  };
}

/**
 * フロントエンドのドロップダウン向けに当該都道府県の市区町村一覧を作成。
 * @param {string} prefecture
 * @return {Array<{prefecture: string, municipality: string, key: string, label: string}>}
 */
function buildAvailableRegions_(prefecture) {
  if (!prefecture) {
    return [];
  }
  return getMunicipalitiesForPrefecture(prefecture).map(function (municipality) {
    var pref = sanitizeString_(prefecture);
    var muni = sanitizeString_(municipality);
    return {
      prefecture: pref,
      municipality: muni,
      key: buildRegionKey(pref, muni),
      label: [pref, muni].filter(function (part) { return part; }).join(' ')
    };
  });
}

/**
 * 都道府県＋市区町村の集計データを生成する。
 * @param {string} prefecture
 * @param {string} municipality
 * @return {Object}
 */
function buildMapCompleteCityData_(prefecture, municipality) {
  const ctx = resolveRegionContext(prefecture, municipality);
  const today = Utilities.formatDate(new Date(), Session.getScriptTimeZone(), 'yyyy-MM-dd');

  const phase1 = fetchPhase1Metrics(prefecture, municipality);
  const applicants = fetchApplicantsForMunicipality(prefecture, municipality);
  const phase3 = fetchPhase3Persona(prefecture, municipality, null);
  const phase6 = fetchPhase6Flow(prefecture, municipality);
  const phase7 = fetchPhase7Supply(prefecture, municipality);
  const phase8 = fetchPhase8Education(prefecture, municipality);
  const phase10 = fetchPhase10Urgency(prefecture, municipality);

  // Phase 12-14: 需給ギャップ、希少性スコア、競合分析（選択地域のみ）
  const phase12to14 = loadPhase12to14DataForRegion(prefecture, municipality);

  const mapMetrics = phase1.tables.mapMetrics || [];
  const ageGender = phase7.tables.ageGenderCross || [];
  const personaProfile = phase7.tables.personaProfile || [];
  const urgencyDist = phase10.tables.urgencyDistribution || [];
  const urgencyAge = phase10.tables.ageCross || [];
  const urgencyEmployment = phase10.tables.employmentCross || [];

  const applicantTotal = sumRecords_(mapMetrics, ['applicant_count', 'applicants', 'count']);
  const maleTotal = sumRecords_(mapMetrics, ['male_count', 'male', '男性人数']);
  const femaleTotal = sumRecords_(mapMetrics, ['female_count', 'female', '女性人数']);
  const avgAge = weightedAverage_(mapMetrics, ['avg_age', 'average_age'], ['applicant_count', 'count']);
  const avgQualifications = weightedAverage_(mapMetrics, ['avg_qualifications', 'avg_qualification'], ['applicant_count', 'count']);

  const lat = weightedAverage_(mapMetrics, ['latitude', 'lat'], ['applicant_count', 'count']);
  const lng = weightedAverage_(mapMetrics, ['longitude', 'lng', 'lon'], ['applicant_count', 'count']);

  const ageGroups = aggregateCounts_(ageGender, ['age_group', '年齢帯'], ['count']);
  const genderGroups = aggregateCounts_(ageGender, ['gender', '性別'], ['count']);
  const avgDesired = weightedAverage_(ageGender, ['avg_desired_areas', 'avg_desired'], ['count']);
  const avgQualificationByAge = weightedAverage_(ageGender, ['avg_qualifications'], ['count']);

  const supplyDensity = phase7.tables.supplyDensity || [];
  const nationalLicenseCount = sumRecords_(supplyDensity, ['national_license_count', 'national_license']);
  const supplyAvgQualifications = weightedAverage_(supplyDensity, ['avg_qualifications'], ['supply_count', 'applicant_count', 'count']);

  const employmentMatrix = aggregateEmploymentAgeMatrix_(personaProfile, ageGroups.labels);
  const statusTotals = aggregateCounts_(personaProfile, ['employment_status', 'employmentStatus'], ['count']);
  const personaTop = buildPersonaTop_(personaProfile, applicantTotal);

  const personaQualificationSummary = buildPersonaQualificationSummary_(personaProfile);
  const personaSummaryByMunicipality = sanitizeRecords_(phase7.tables.personaSummaryByMunicipality || [], 200);
  const personaMobilityMatrix = buildMatrixFromRecords_(phase7.tables.personaMobility, ['persona_label', 'persona', 'ペルソナ', 'persona_segment'], ['mobility_rank', 'mobility_level', '移動許容度', 'mobility'], ['count', '人数']);
  const personaSummary = sanitizeRecords_(phase3.tables ? phase3.tables.personaSummary : [], 50);
  const personaDetails = sanitizeRecords_(phase3.tables ? phase3.tables.personaDetails : [], 200);
  const personaMapData = sanitizeRecords_(phase7.tables.personaMapData || [], 200);

  const urgencyTotal = sumRecords_(urgencyDist, ['count']);
  const urgencyAvgScore = weightedAverage_(urgencyDist, ['avg_urgency_score'], ['count']);
  const urgencyByAge = aggregateAverageList_(urgencyAge, ['age_group', '年齢帯'], ['count'], ['avg_urgency_score']);
  const urgencyByEmployment = aggregateAverageList_(urgencyEmployment, ['employment_status', 'employmentStatus'], ['count'], ['avg_urgency_score']);
  const urgencyAgeMatrix = buildMatrixFromRecords_(phase10.tables.ageMatrix, ['age_group', '年齢帯'], ['urgency_rank', 'rank', '緊急度', 'urgency_level'], ['count', '人数']);
  const urgencyEmploymentMatrix = buildMatrixFromRecords_(phase10.tables.employmentMatrix, ['employment_status', 'employmentStatus', '就業ステータス'], ['urgency_rank', 'rank', '緊急度', 'urgency_level'], ['count', '人数']);
  const urgencyMunicipality = sanitizeRecords_(phase10.tables.municipality || [], 200);

  const educationMatrix = buildMatrixFromRecords_(phase8.tables.educationMatrix, ['education_level', 'education', '学歴'], ['age_group', '年齢帯'], ['count', '人数']);
  const careerMatrix = buildMatrixFromRecords_(phase8.tables.careerMatrix, ['career_cluster', 'career', 'キャリア分類', '職種'], ['age_group', '年齢帯'], ['count', '人数']);
  const careerDistribution = sanitizeRecords_(phase8.tables.careerDistribution || [], 100);
  const graduationDistribution = sanitizeRecords_(phase8.tables.graduationDistribution || [], 100);

  const qualityIssues = []
    .concat(extractQualityIssues_(phase1.tables ? phase1.tables.quality : []))
    .concat(extractQualityIssues_(phase3.tables ? phase3.tables.quality : []))
    .concat(extractQualityIssues_(phase6.tables ? phase6.tables.quality : []))
    .concat(extractQualityIssues_(phase7.tables ? phase7.tables.quality : []))
    .concat(extractQualityIssues_(phase8.tables ? phase8.tables.quality : []))
    .concat(extractQualityIssues_(phase10.tables ? phase10.tables.quality : []));
  const qualityWarnings = []
    .concat(phase1.warnings || [])
    .concat(phase3.warnings || [])
    .concat(phase6.warnings || [])
    .concat(phase7.warnings || [])
    .concat(phase8.warnings || [])
    .concat(phase10.warnings || []);
  const qualitySummary = summarizeQuality_(qualityIssues, qualityWarnings);

  return {
    id: ctx.key,
    name: [sanitizeString_(ctx.prefecture), sanitizeString_(ctx.municipality)].filter(function (part) { return part; }).join(' '),
    center: (isFiniteNumber_(lat) && isFiniteNumber_(lng)) ? [lat, lng] : null,
    updated: today,
    region: {
      prefecture: sanitizeString_(ctx.prefecture),
      municipality: sanitizeString_(ctx.municipality),
      key: ctx.key
    },
    overview: {
      kpis: [
        { label: '求職者数', value: applicantTotal, unit: '人' },
        { label: '平均年齢', value: avgAge, unit: '歳' },
        {
          label: '男女比 (男性/女性)',
          labels: genderGroups.labels,
          values: genderGroups.values,
          unit: '人'
        },
        {
          label: '国家資格保有率',
          value: applicantTotal ? nationalLicenseCount / applicantTotal : null,
          unit: '割合',
          note: nationalLicenseCount ? '保有者 ' + nationalLicenseCount + '人' : null
        }
      ],
      age_gender: {
        age_labels: ageGroups.labels,
        age_totals: ageGroups.values,
        gender_labels: genderGroups.labels,
        gender_totals: genderGroups.values
      },
      averages: {
        '希望勤務地数': avgDesired,
        '保有資格数': avgQualificationByAge
      }
    },
    supply: {
      status_counts: toStatusCounts_(statusTotals.map),
      qualification_buckets: buildQualificationBuckets_(personaProfile),
      national_license_count: nationalLicenseCount,
      avg_qualifications: supplyAvgQualifications,
      mobility_matrix: personaMobilityMatrix,
      mobility_scores: sanitizeRecords_(phase7.tables.mobilityScore || [], 50)
    },
    career: {
      summary: {
        '平均保有資格数': avgQualificationByAge,
        '平均希望勤務地数': avgDesired,
        '国家資格保有率': applicantTotal ? nationalLicenseCount / applicantTotal : null
      },
      employment_age: {
        age_labels: ageGroups.labels,
        rows: employmentMatrix
      },
      matrices: {
        education: educationMatrix,
        career: careerMatrix
      },
      distributions: {
        career: careerDistribution,
        graduation: graduationDistribution
      }
    },
    urgency: {
      summary: {
        '対象人数': urgencyTotal,
        '平均スコア': urgencyAvgScore
      },
      by_age: urgencyByAge.map(function (item) {
        return {
          age_group: item.label,
          count: item.count,
          avg_score: item.average
        };
      }),
      by_employment: urgencyByEmployment.map(function (item) {
        return {
          status: item.label,
          count: item.count,
          avg_score: item.average
        };
      }),
      matrices: {
        age: urgencyAgeMatrix,
        employment: urgencyEmploymentMatrix
      },
      municipality: urgencyMunicipality
    },
    persona: {
      top: personaTop,
      summary: personaSummary,
      details: personaDetails,
      qualification_summary: personaQualificationSummary,
      personaSummaryByMunicipality: personaSummaryByMunicipality,
      mobility_matrix: personaMobilityMatrix,
      map_data: personaMapData
    },
    applicants: sanitizeRecords_(applicants, 5000),
    cross_insights: {
      personaDifficulty: {
        summary: phase3.summary || {},
        table: personaSummary
      },
      educationMatrix: educationMatrix,
      careerMatrix: careerMatrix,
      urgencyAgeMatrix: urgencyAgeMatrix,
      urgencyEmploymentMatrix: urgencyEmploymentMatrix
    },
    flow: {
      summary: {
        total_inflow: phase6.summary.totalInflow,
        total_outflow: phase6.summary.totalOutflow,
        net_flow: phase6.summary.netFlow,
        inflow_sources: phase6.summary.inflowRecords,
        outflow_destinations: phase6.summary.outflowRecords
      },
      top_inflows: sanitizeRecords_(phase6.tables.topInflows, 10),
      top_outflows: sanitizeRecords_(phase6.tables.topOutflows, 10),
      all_inflows: sanitizeRecords_(phase6.tables.allInflows, 100),
      all_outflows: sanitizeRecords_(phase6.tables.allOutflows, 100),
      nearby_regions: buildNearbyRegions_(phase6.tables.topInflows, phase6.tables.topOutflows, 5)
    },
    quality: qualitySummary,

    // Phase 12-14: 需給ギャップ、希少性スコア、競合分析（選択地域のみ）
    // HTML側との互換性のため、dataオブジェクトを直接展開
    gap: Object.assign({}, phase12to14.gap.data || {}, {
      summary: phase12to14.gap.summary || {}
    }),
    rarity: {
      records: phase12to14.rarity.records || [],
      rank_distribution: phase12to14.rarity.rank_distribution || {},
      summary: phase12to14.rarity.summary || {}
    },
    competition: Object.assign({}, phase12to14.competition.data || {}, {
      summary: phase12to14.competition.summary || {}
    })
  };
}

/**
 * Phase 12-14専用の都道府県＋市区町村データを生成（軽量版）
 * パフォーマンス最適化：Phase 1の基本情報 + Phase 12-14のみ取得
 *
 * @param {string} prefecture
 * @param {string} municipality
 * @return {Object}
 */
function buildMapCompleteCityDataPhase12to14Only_(prefecture, municipality) {
  const ctx = resolveRegionContext(prefecture, municipality);
  const today = Utilities.formatDate(new Date(), Session.getScriptTimeZone(), 'yyyy-MM-dd');

  // Phase 1から最小限の基本情報のみ取得（座標、求職者数など）
  const phase1 = fetchPhase1Metrics(prefecture, municipality);
  const mapMetrics = phase1.tables.mapMetrics || [];

  const applicantTotal = sumRecords_(mapMetrics, ['applicant_count', 'applicants', 'count']);
  const maleTotal = sumRecords_(mapMetrics, ['male_count', 'male', '男性人数']);
  const femaleTotal = sumRecords_(mapMetrics, ['female_count', 'female', '女性人数']);
  const avgAge = weightedAverage_(mapMetrics, ['avg_age', 'average_age'], ['applicant_count', 'count']);

  const lat = weightedAverage_(mapMetrics, ['latitude', 'lat'], ['applicant_count', 'count']);
  const lng = weightedAverage_(mapMetrics, ['longitude', 'lng', 'lon'], ['applicant_count', 'count']);

  // Phase 12-14: 需給ギャップ、希少性スコア、競合分析（選択地域のみ）
  const phase12to14 = loadPhase12to14DataForRegion(prefecture, municipality);

  return {
    id: ctx.key,
    name: [sanitizeString_(ctx.prefecture), sanitizeString_(ctx.municipality)].filter(function (part) { return part; }).join(' '),
    center: (isFiniteNumber_(lat) && isFiniteNumber_(lng)) ? [lat, lng] : null,
    updated: today,
    region: {
      prefecture: sanitizeString_(ctx.prefecture),
      municipality: sanitizeString_(ctx.municipality),
      key: ctx.key
    },
    overview: {
      kpis: [
        { label: '求職者数', value: applicantTotal, unit: '人' },
        { label: '平均年齢', value: avgAge, unit: '歳' },
        { label: '男性', value: maleTotal, unit: '人' },
        { label: '女性', value: femaleTotal, unit: '人' }
      ]
    },
    // Phase 12-14: 需給ギャップ、希少性スコア、競合分析（選択地域のみ）
    // HTML側との互換性のため、dataオブジェクトを直接展開
    gap: Object.assign({}, phase12to14.gap.data || {}, {
      summary: phase12to14.gap.summary || {}
    }),
    rarity: {
      records: phase12to14.rarity.records || [],
      rank_distribution: phase12to14.rarity.rank_distribution || {},
      summary: phase12to14.rarity.summary || {}
    },
    competition: Object.assign({}, phase12to14.competition.data || {}, {
      summary: phase12to14.competition.summary || {}
    }),
    quality: { status: 'ok', label: '品質良好', message: '', color: '#10b981', issues: [], warnings: [] }
  };
}

// ────────────────────────────────
// 近隣地域構築
// ────────────────────────────────

/**
 * 流入・流出TOP地域から近隣地域リストを構築
 * @param {Array} topInflows - 流入TOP地域
 * @param {Array} topOutflows - 流出TOP地域
 * @param {number} limit - 各方向の上限数
 * @return {Array} 近隣地域の配列（prefecture, municipality, lat, lng, key, type）
 */
function buildNearbyRegions_(topInflows, topOutflows, limit) {
  var nearbyRegions = [];
  var mapMetrics = readFirstAvailableSheet(['Phase1_MapMetrics', 'MapMetrics']);

  if (!mapMetrics || mapMetrics.length === 0) {
    return nearbyRegions;
  }

  // 座標マップを作成（高速検索用）
  var coordMap = {};
  mapMetrics.forEach(function(record) {
    var pref = sanitizeString_(getField_(record, ['都道府県', 'prefecture']));
    var muni = sanitizeString_(getField_(record, ['市区町村', 'municipality']));
    var lat = parseNumber_(getField_(record, ['緯度', 'latitude', 'lat']));
    var lng = parseNumber_(getField_(record, ['経度', 'longitude', 'lng', 'lon']));

    if (pref && muni && lat !== null && lng !== null) {
      var key = buildRegionKey(pref, muni);
      coordMap[key] = { prefecture: pref, municipality: muni, lat: lat, lng: lng, key: key };
    }
  });

  // 流入TOP地域を追加
  var inflowsToAdd = topInflows.slice(0, limit);
  inflowsToAdd.forEach(function(record) {
    var originPref = sanitizeString_(getField_(record, ['origin_pref', 'origin_prefecture']));
    var originMuni = sanitizeString_(getField_(record, ['origin_muni', 'origin_municipality']));

    if (originPref && originMuni) {
      var key = buildRegionKey(originPref, originMuni);
      if (coordMap[key]) {
        nearbyRegions.push({
          prefecture: coordMap[key].prefecture,
          municipality: coordMap[key].municipality,
          lat: coordMap[key].lat,
          lng: coordMap[key].lng,
          key: coordMap[key].key,
          type: 'inflow',
          flow_count: parseNumber_(getField_(record, ['flow_count', 'count']))
        });
      }
    }
  });

  // 流出TOP地域を追加
  var outflowsToAdd = topOutflows.slice(0, limit);
  outflowsToAdd.forEach(function(record) {
    var destPref = sanitizeString_(getField_(record, ['destination_pref', 'destination_prefecture']));
    var destMuni = sanitizeString_(getField_(record, ['destination_muni', 'destination_municipality']));

    if (destPref && destMuni) {
      var key = buildRegionKey(destPref, destMuni);

      // 既に流入で追加されていないかチェック
      var alreadyAdded = nearbyRegions.some(function(r) { return r.key === key; });

      if (!alreadyAdded && coordMap[key]) {
        nearbyRegions.push({
          prefecture: coordMap[key].prefecture,
          municipality: coordMap[key].municipality,
          lat: coordMap[key].lat,
          lng: coordMap[key].lng,
          key: coordMap[key].key,
          type: 'outflow',
          flow_count: parseNumber_(getField_(record, ['flow_count', 'count']))
        });
      }
    }
  });

  return nearbyRegions;
}

// ────────────────────────────────
// 集計ヘルパー
// ────────────────────────────────

function getField_(record, candidates) {
  if (!record) {
    return null;
  }
  for (var i = 0; i < candidates.length; i += 1) {
    var key = candidates[i];
    if (key in record && record[key] !== '') {
      return sanitizeMaybeString_(record[key]);
    }
  }
  return null;
}

function toNumber_(value) {
  return parseNumber_(value);
}

function isFiniteNumber_(value) {
  return typeof value === 'number' && isFinite(value);
}

function sumRecords_(records, fieldCandidates) {
  return (records || []).reduce(function (sum, record) {
    return sum + toNumber_(getField_(record, fieldCandidates));
  }, 0);
}

function weightedAverage_(records, valueCandidates, weightCandidates) {
  var totalWeight = 0;
  var total = 0;
  (records || []).forEach(function (record) {
    var weight = parseNumber_(getField_(record, weightCandidates));
    if (!weight) {
      return;
    }
    var value = parseNumber_(getField_(record, valueCandidates));
    if (!isFiniteNumber_(value) && value !== 0) {
      return;
    }
    totalWeight += weight;
    total += value * weight;
  });
  return totalWeight ? total / totalWeight : null;
}

function aggregateCounts_(records, groupCandidates, valueCandidates) {
  var map = new Map();
  (records || []).forEach(function (record) {
    var label = sanitizeString_(getField_(record, groupCandidates));
    if (!label) {
      return;
    }
    var value = toNumber_(getField_(record, valueCandidates));
    if (!map.has(label)) {
      map.set(label, 0);
    }
    map.set(label, map.get(label) + value);
  });

  var labels = Array.from(map.keys());
  var values = labels.map(function (label) { return map.get(label); });

  return {
    labels: labels,
    values: values,
    map: map
  };
}

function aggregateAverageList_(records, groupCandidates, countCandidates, valueCandidates) {
  var map = new Map();
  (records || []).forEach(function (record) {
    var label = sanitizeString_(getField_(record, groupCandidates));
    if (!label) {
      return;
    }
    var count = parseNumber_(getField_(record, countCandidates));
    var value = parseNumber_(getField_(record, valueCandidates));
    if (!isFiniteNumber_(value) && value !== 0) {
      return;
    }
    if (!map.has(label)) {
      map.set(label, { count: 0, weighted: 0 });
    }
    var entry = map.get(label);
    entry.count += count;
    entry.weighted += value * count;
    map.set(label, entry);
  });

  return Array.from(map.entries()).map(function (entry) {
    var label = entry[0];
    var info = entry[1];
    return {
      label: label,
      count: info.count,
      average: info.count ? info.weighted / info.count : null
    };
  }).sort(function (a, b) {
    return a.label > b.label ? 1 : -1;
  });
}

function aggregateEmploymentAgeMatrix_(personaProfile, ageLabels) {
  var matrixMap = new Map();
  (personaProfile || []).forEach(function (record) {
    var status = sanitizeString_(getField_(record, ['employment_status', 'employmentStatus', '就業ステータス'])) || 'その他';
    var age = sanitizeString_(getField_(record, ['age_group', '年齢帯'])) || '不明';
    var count = toNumber_(getField_(record, ['count']));
    var key = status + '::' + age;
    if (!matrixMap.has(key)) {
      matrixMap.set(key, 0);
    }
    matrixMap.set(key, matrixMap.get(key) + count);
  });

  var statusTotals = new Map();
  matrixMap.forEach(function (value, key) {
    var status = key.split('::')[0];
    if (!statusTotals.has(status)) {
      statusTotals.set(status, 0);
    }
    statusTotals.set(status, statusTotals.get(status) + value);
  });

  var sortedStatuses = Array.from(statusTotals.entries())
    .sort(function (a, b) { return b[1] - a[1]; })
    .map(function (entry) { return entry[0]; });

  var rows = sortedStatuses.map(function (status) {
    var counts = (ageLabels || []).map(function (age) {
      var key = status + '::' + age;
      return matrixMap.has(key) ? matrixMap.get(key) : 0;
    });
    return {
      label: status,
      cells: counts.map(function (value) { return value; }),
      counts: counts
    };
  });

  return rows;
}

function toStatusCounts_(statusMap) {
  var result = {};
  if (!statusMap) {
    return result;
  }
  statusMap.forEach(function (value, key) {
    result[sanitizeString_(key)] = value;
  });
  return result;
}

function buildQualificationBuckets_(personaProfile) {
  var buckets = new Map();
  (personaProfile || []).forEach(function (record) {
    var qualifications = parseNumber_(getField_(record, ['avg_qualifications']));
    var count = toNumber_(getField_(record, ['count']));
    if (!isFinite(qualifications)) {
      return;
    }
    var bucket;
    if (qualifications < 0.5) {
      bucket = '資格なし';
    } else if (qualifications < 1.5) {
      bucket = '1資格';
    } else if (qualifications < 2.5) {
      bucket = '2資格';
    } else {
      bucket = '3資格以上';
    }
    if (!buckets.has(bucket)) {
      buckets.set(bucket, 0);
    }
    buckets.set(bucket, buckets.get(bucket) + count);
  });

  return ['資格なし', '1資格', '2資格', '3資格以上'].map(function (label) {
    return {
      label: label,
      value: buckets.has(label) ? buckets.get(label) : 0
    };
  });
}

function buildPersonaTop_(personaProfile, applicantTotal) {
  if (!personaProfile || !personaProfile.length) {
    return [];
  }
  var personas = new Map();
  personaProfile.forEach(function (record) {
    var age = sanitizeString_(getField_(record, ['age_group', '年齢帯'])) || '不明';
    var gender = sanitizeString_(getField_(record, ['gender', '性別'])) || '不明';
    var status = sanitizeString_(getField_(record, ['employment_status', 'employmentStatus', '就業ステータス'])) || '不明';
    var personaName = age + ' × ' + gender + ' × ' + status;
    var count = toNumber_(getField_(record, ['count']));
    if (!personas.has(personaName)) {
      personas.set(personaName, 0);
    }
    personas.set(personaName, personas.get(personaName) + count);
  });

  var entries = Array.from(personas.entries()).sort(function (a, b) {
    return b[1] - a[1];
  });

  var total = applicantTotal || entries.reduce(function (sum, entry) { return sum + entry[1]; }, 0);

  return entries.slice(0, 5).map(function (entry) {
    return {
      label: sanitizeString_(entry[0]),
      count: entry[1],
      share: total ? entry[1] / total : 0
    };
  });
}

function buildPersonaQualificationSummary_(personaProfile) {
  if (!personaProfile || !personaProfile.length) {
    return [];
  }
  var map = new Map();
  (personaProfile || []).forEach(function (record) {
    var age = sanitizeString_(getField_(record, ['age_group', '年齢帯'])) || '不明';
    var gender = sanitizeString_(getField_(record, ['gender', '性別'])) || '不明';
    var status = sanitizeString_(getField_(record, ['employment_status', 'employmentStatus', '就業ステータス'])) || '不明';
    var personaName = age + ' × ' + gender + ' × ' + status;
    var count = toNumber_(getField_(record, ['count']));
    var avgQual = parseNumber_(getField_(record, ['avg_qualifications']));
    var bucket = sanitizeString_(getField_(record, ['qualification_bucket', 'qualification_bucket_label', '資格カテゴリ'])) || 'その他';
    if (!map.has(personaName)) {
      map.set(personaName, {
        persona: personaName,
        count: 0,
        totalQualifications: 0,
        buckets: {}
      });
    }
    var entry = map.get(personaName);
    entry.count += count;
    entry.totalQualifications += (avgQual || 0) * count;
    if (!entry.buckets[bucket]) {
      entry.buckets[bucket] = 0;
    }
    entry.buckets[bucket] += count;
    map.set(personaName, entry);
  });

  return Array.from(map.values()).map(function (entry) {
    var buckets = Object.keys(entry.buckets).map(function (key) {
      return {
        label: key,
        count: entry.buckets[key]
      };
    }).sort(function (a, b) { return b.count - a.count; });
    return {
      persona: entry.persona,
      count: entry.count,
      avg_qualifications: entry.count ? entry.totalQualifications / entry.count : 0,
      top_bucket: buckets.length ? buckets[0].label : '-'
    };
  }).sort(function (a, b) {
    return b.avg_qualifications - a.avg_qualifications;
  });
}

function sanitizeRecords_(records, limit) {
  if (!records || !records.length) {
    return [];
  }
  var slice = typeof limit === 'number' ? records.slice(0, limit) : records.slice();
  return slice.map(function (record) {
    var sanitized = {};
    Object.keys(record || {}).forEach(function (key) {
      if (key === '__normalized') {
        return;
      }
      var cleanKey = sanitizeString_(key);
      var value = record[key];
      if (typeof value === 'number') {
        sanitized[cleanKey] = value;
      } else if (value === null || value === undefined) {
        sanitized[cleanKey] = '';
      } else if (typeof value === 'string') {
        sanitized[cleanKey] = sanitizeString_(value);
      } else {
        sanitized[cleanKey] = value;
      }
    });
    return sanitized;
  });
}

function buildMatrixFromRecords_(records, rowCandidates, columnCandidates, valueCandidates) {
  if (!records || !records.length) {
    return null;
  }
  var rowLabels = [];
  var columnLabels = [];
  var matrix = {};

  (records || []).forEach(function (record) {
    var rowLabel = sanitizeString_(getField_(record, rowCandidates));
    var columnLabel = sanitizeString_(getField_(record, columnCandidates));
    if (!rowLabel || !columnLabel) {
      return;
    }
    if (rowLabels.indexOf(rowLabel) === -1) {
      rowLabels.push(rowLabel);
    }
    if (columnLabels.indexOf(columnLabel) === -1) {
      columnLabels.push(columnLabel);
    }
    var value = parseNumber_(getField_(record, valueCandidates));
    var key = rowLabel + '::' + columnLabel;
    matrix[key] = (matrix[key] || 0) + value;
  });

  if (!rowLabels.length || !columnLabels.length) {
    return null;
  }

  var values = rowLabels.map(function (row) {
    return columnLabels.map(function (column) {
      var key = row + '::' + column;
      return matrix.hasOwnProperty(key) ? matrix[key] : 0;
    });
  });

  var rowTotals = values.map(function (rowValues) {
    return rowValues.reduce(function (sum, current) { return sum + current; }, 0);
  });
  var columnTotals = columnLabels.map(function (_, columnIndex) {
    return values.reduce(function (sum, rowValues) {
      return sum + (rowValues[columnIndex] || 0);
    }, 0);
  });
  var grandTotal = rowTotals.reduce(function (sum, value) { return sum + value; }, 0);

  return {
    rows: rowLabels,
    columns: columnLabels,
    values: values,
    row_totals: rowTotals,
    column_totals: columnTotals,
    total: grandTotal
  };
}

function sanitizeMaybeString_(value) {
  if (typeof value === 'string') {
    return sanitizeString_(value);
  }
  return value;
}

function sanitizeString_(value) {
  if (value === null || value === undefined) {
    return '';
  }
  var text = String(value);
  if (text.charCodeAt(0) === 0xfeff) {
    text = text.substring(1);
  }
  return text.trim();
}

function parseNumber_(value) {
  if (value === null || value === undefined || value === '') {
    return 0;
  }
  if (typeof value === 'number') {
    return isFinite(value) ? value : 0;
  }
  var text = sanitizeString_(value).replace(/\u2212/g, '-');
  if (!text) {
    return 0;
  }
  var cleaned = text.replace(/,/g, '').replace(/[^\d.+-]/g, '');
  var num = Number(cleaned);
  return isFinite(num) ? num : 0;
}

function extractQualityIssues_(records) {
  var issues = [];
  (records || []).forEach(function (record) {
    var flag = sanitizeString_(getField_(record, ['警告フラグ', 'quality_flag', 'warning_flag', 'Flag']));
    if (!flag || flag === 'なし' || flag === 'OK') {
      return;
    }
    var message = sanitizeString_(getField_(record, ['警告メッセージ', 'warning_message', 'メッセージ', 'message']));
    var metric = sanitizeString_(getField_(record, ['指標', 'metric', '項目', 'Dimension']));
    issues.push({
      flag: flag,
      message: message || '',
      metric: metric || ''
    });
  });
  return issues;
}

function summarizeQuality_(issues, warnings) {
  var severityMap = {
    '使用不可': 3,
    'BLOCKED': 3,
    '要注意': 2,
    '要確認': 2,
    '注意': 2,
    'MARGINAL': 2,
    'INSUFFICIENT': 3,
    '軽微': 1,
    '軽度': 1
  };

  var worst = { score: 0, issue: null };
  issues.forEach(function (issue) {
    var score = severityMap[issue.flag] !== undefined ? severityMap[issue.flag] : 1;
    if (score >= worst.score) {
      worst = { score: score, issue: issue };
    }
  });

  var status;
  if (worst.score >= 3) {
    status = 'critical';
  } else if (worst.score === 2) {
    status = 'warning';
  } else if (issues.length || (warnings && warnings.length)) {
    status = 'notice';
  } else {
    status = 'ok';
  }

  var colorMap = {
    ok: '#10b981',
    notice: '#38bdf8',
    warning: '#f59e0b',
    critical: '#ef4444'
  };

  return {
    status: status,
    label: worst.issue ? ('品質: ' + worst.issue.flag) : '品質良好',
    message: worst.issue ? worst.issue.message : (warnings && warnings.length ? warnings.join('\n') : ''),
    color: colorMap[status] || '#38bdf8',
    issues: issues,
    warnings: warnings || []
  };
}

