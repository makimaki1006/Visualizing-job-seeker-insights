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
  const props = PropertiesService.getScriptProperties();
  const cacheKey = 'mapComplete_' + (prefecture || '') + '_' + (municipality || '');
  const timestampKey = cacheKey + '_timestamp';

  // キャッシュをチェック（24時間有効）⏰
  const cached = props.getProperty(cacheKey);
  const timestamp = props.getProperty(timestampKey);

  if (cached && timestamp) {
    try {
      const cacheAge = Date.now() - parseInt(timestamp);
      const cacheMaxAge = 24 * 60 * 60 * 1000; // 24時間（ミリ秒）

      if (cacheAge < cacheMaxAge) {
        Logger.log('[getMapCompleteData] キャッシュヒット: ' + cacheKey + ' (経過: ' + Math.floor(cacheAge / 1000 / 60) + '分)');
        return JSON.parse(cached);
      } else {
        Logger.log('[getMapCompleteData] キャッシュ期限切れ: ' + cacheKey + ' (経過: ' + Math.floor(cacheAge / 1000 / 60 / 60) + '時間)');
        // 期限切れキャッシュを削除
        props.deleteProperty(cacheKey);
        props.deleteProperty(timestampKey);
      }
    } catch (e) {
      Logger.log('[getMapCompleteData] キャッシュのパースに失敗: ' + e);
      // 壊れたキャッシュを削除
      props.deleteProperty(cacheKey);
      props.deleteProperty(timestampKey);
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

  // 結果をキャッシュ（PropertiesService: 9MB制限、24時間有効）⏰
  try {
    const dataJson = JSON.stringify(result);
    const dataSizeKB = Math.round(dataJson.length / 1024);

    props.setProperty(cacheKey, dataJson);
    props.setProperty(timestampKey, Date.now().toString());

    Logger.log('[getMapCompleteData] キャッシュに保存成功: ' + cacheKey + ' (' + dataSizeKB + 'KB)');
  } catch (e) {
    Logger.log('[getMapCompleteData] キャッシュの保存に失敗（データサイズ超過の可能性）: ' + e);
    // 保存失敗時はキャッシュキーも削除
    try {
      props.deleteProperty(cacheKey);
      props.deleteProperty(timestampKey);
    } catch (cleanupError) {
      Logger.log('[getMapCompleteData] クリーンアップ失敗: ' + cleanupError);
    }
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
  const props = PropertiesService.getScriptProperties();
  const cacheKey = 'phase12to14_' + (prefecture || '') + '_' + (municipality || '');
  const timestampKey = cacheKey + '_timestamp';

  // キャッシュをチェック（24時間有効）⏰
  const cached = props.getProperty(cacheKey);
  const timestamp = props.getProperty(timestampKey);

  if (cached && timestamp) {
    try {
      const cacheAge = Date.now() - parseInt(timestamp);
      const cacheMaxAge = 24 * 60 * 60 * 1000; // 24時間（ミリ秒）

      if (cacheAge < cacheMaxAge) {
        Logger.log('[getMapCompleteDataPhase12to14Only] キャッシュヒット: ' + cacheKey + ' (経過: ' + Math.floor(cacheAge / 1000 / 60) + '分)');
        return JSON.parse(cached);
      } else {
        Logger.log('[getMapCompleteDataPhase12to14Only] キャッシュ期限切れ: ' + cacheKey);
        props.deleteProperty(cacheKey);
        props.deleteProperty(timestampKey);
      }
    } catch (e) {
      Logger.log('[getMapCompleteDataPhase12to14Only] キャッシュのパースに失敗: ' + e);
      props.deleteProperty(cacheKey);
      props.deleteProperty(timestampKey);
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

  // 結果をキャッシュ（PropertiesService: 9MB制限、24時間有効）⏰
  try {
    const dataJson = JSON.stringify(result);
    const dataSizeKB = Math.round(dataJson.length / 1024);

    props.setProperty(cacheKey, dataJson);
    props.setProperty(timestampKey, Date.now().toString());

    Logger.log('[getMapCompleteDataPhase12to14Only] キャッシュに保存成功: ' + cacheKey + ' (' + dataSizeKB + 'KB)');
  } catch (e) {
    Logger.log('[getMapCompleteDataPhase12to14Only] キャッシュの保存に失敗: ' + e);
    try {
      props.deleteProperty(cacheKey);
      props.deleteProperty(timestampKey);
    } catch (cleanupError) {
      Logger.log('[getMapCompleteDataPhase12to14Only] クリーンアップ失敗: ' + cleanupError);
    }
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

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 事前キャッシュ生成機能（30秒制限回避）
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

/**
 * すべての都道府県のキャッシュを事前生成
 * 時間駆動トリガーで毎日自動実行することで、ユーザーアクセス時は常にキャッシュヒット
 *
 * ⏰ 推奨実行時間: 毎日深夜2時（ユーザーアクセスが少ない時間帯）
 * ⏱️ 実行時間: 約3-5分（47都道府県 × 平均4秒）
 *
 * @return {Object} 生成結果の統計情報
 */
function warmUpMapCompleteCache() {
  const startTime = new Date();
  Logger.log('=== キャッシュウォームアップ開始 ===');

  const regionOptions = getRegionOptions();
  const prefectures = regionOptions.prefectures || [];

  let successCount = 0;
  let failureCount = 0;
  const errors = [];

  prefectures.forEach(function(prefecture, index) {
    try {
      Logger.log('[' + (index + 1) + '/' + prefectures.length + '] ' + prefecture + ' のキャッシュ生成中...');

      // 都道府県レベルのキャッシュ生成
      getMapCompleteData(prefecture, null);
      successCount++;

      // スクリプト実行時間制限を考慮（6分 = 360秒）
      const elapsed = (new Date() - startTime) / 1000;
      if (elapsed > 300) { // 5分経過したら中断（安全マージン）
        Logger.log('⚠️ 実行時間制限に近づいたため中断します（' + Math.floor(elapsed) + '秒経過）');
        return false; // forEach を中断
      }

      // API制限を考慮して少し待機（Quota超過防止）
      Utilities.sleep(100);

    } catch (e) {
      failureCount++;
      errors.push(prefecture + ': ' + e.message);
      Logger.log('❌ ' + prefecture + ' のキャッシュ生成に失敗: ' + e.message);
    }
  });

  const endTime = new Date();
  const totalSeconds = Math.floor((endTime - startTime) / 1000);

  const result = {
    timestamp: endTime.toISOString(),
    duration_seconds: totalSeconds,
    total_prefectures: prefectures.length,
    success: successCount,
    failure: failureCount,
    errors: errors
  };

  Logger.log('=== キャッシュウォームアップ完了 ===');
  Logger.log('実行時間: ' + totalSeconds + '秒');
  Logger.log('成功: ' + successCount + '件 / 失敗: ' + failureCount + '件');

  // 結果をPropertiesServiceに保存（確認用）
  try {
    PropertiesService.getScriptProperties().setProperty(
      'lastWarmUpResult',
      JSON.stringify(result)
    );
  } catch (e) {
    Logger.log('⚠️ 結果の保存に失敗: ' + e.message);
  }

  return result;
}

/**
 * 時間駆動トリガーを設定（1回だけ実行）
 * メニューから手動実行してトリガーを追加
 *
 * ⏰ 設定内容: 毎日深夜2時に warmUpMapCompleteCache() を自動実行
 *
 * ⚠️ 注意: この関数は1回だけ実行してください（重複トリガー防止）
 */
function setupDailyWarmUpTrigger() {
  // 既存のトリガーを確認
  const triggers = ScriptApp.getProjectTriggers();
  const existingTrigger = triggers.find(function(trigger) {
    return trigger.getHandlerFunction() === 'warmUpMapCompleteCache';
  });

  if (existingTrigger) {
    Logger.log('⚠️ warmUpMapCompleteCache のトリガーは既に設定されています');
    SpreadsheetApp.getUi().alert(
      'トリガー設定済み',
      'warmUpMapCompleteCache の自動実行トリガーは既に設定されています。\n\n' +
      '確認: 拡張機能 > Apps Script > トリガー',
      SpreadsheetApp.getUi().ButtonSet.OK
    );
    return;
  }

  // 新しいトリガーを作成（毎日深夜2時）
  ScriptApp.newTrigger('warmUpMapCompleteCache')
    .timeBased()
    .atHour(2)
    .everyDays(1)
    .create();

  Logger.log('✅ warmUpMapCompleteCache の時間駆動トリガーを設定しました（毎日深夜2時）');

  SpreadsheetApp.getUi().alert(
    'トリガー設定完了',
    'warmUpMapCompleteCache の自動実行トリガーを設定しました。\n\n' +
    '実行時間: 毎日深夜2時\n' +
    '実行内容: 全都道府県のキャッシュを事前生成\n\n' +
    '確認: 拡張機能 > Apps Script > トリガー',
    SpreadsheetApp.getUi().ButtonSet.OK
  );
}

/**
 * 最後のキャッシュウォームアップ結果を確認
 * メニューから実行可能
 */
function checkLastWarmUpResult() {
  try {
    const resultJson = PropertiesService.getScriptProperties().getProperty('lastWarmUpResult');
    if (!resultJson) {
      SpreadsheetApp.getUi().alert(
        'ウォームアップ未実施',
        'まだキャッシュウォームアップが実行されていません。\n\n' +
        'setupDailyWarmUpTrigger() を実行してトリガーを設定してください。',
        SpreadsheetApp.getUi().ButtonSet.OK
      );
      return;
    }

    const result = JSON.parse(resultJson);
    const message =
      '最終実行: ' + result.timestamp + '\n' +
      '実行時間: ' + result.duration_seconds + '秒\n' +
      '成功: ' + result.success + '件 / 失敗: ' + result.failure + '件\n\n' +
      (result.errors.length > 0 ? 'エラー:\n' + result.errors.join('\n') : '');

    SpreadsheetApp.getUi().alert(
      'キャッシュウォームアップ結果',
      message,
      SpreadsheetApp.getUi().ButtonSet.OK
    );

    Logger.log(message);
  } catch (e) {
    SpreadsheetApp.getUi().alert(
      'エラー',
      '結果の取得に失敗しました: ' + e.message,
      SpreadsheetApp.getUi().ButtonSet.OK
    );
  }
}

// ============================================================
// 全国データ対応: 3バッチ分割方式
// ============================================================

/**
 * バッチ1: 北海道・東北（7都道府県）
 * 毎日深夜2時実行
 *
 * @return {Object} 処理結果
 */
function warmUpMapCompleteCache_Batch1() {
  const startTime = new Date();
  Logger.log('=== キャッシュウォームアップ バッチ1 開始 ===');

  const batch1Prefectures = [
    '北海道', '青森県', '岩手県', '宮城県', '秋田県', '山形県', '福島県'
  ];

  const result = warmUpMapCompleteCacheBatch(batch1Prefectures, 'バッチ1（北海道・東北）');

  const endTime = new Date();
  const totalSeconds = Math.floor((endTime - startTime) / 1000);

  Logger.log('=== バッチ1 完了: ' + totalSeconds + '秒 ===');

  // 結果を保存
  try {
    PropertiesService.getScriptProperties().setProperty(
      'lastWarmUpResult_Batch1',
      JSON.stringify({
        timestamp: endTime.toISOString(),
        duration_seconds: totalSeconds,
        total_prefectures: batch1Prefectures.length,
        success: result.success,
        failure: result.failure,
        errors: result.errors
      })
    );
  } catch (e) {
    Logger.log('⚠️ バッチ1結果の保存に失敗: ' + e.message);
  }

  return result;
}

/**
 * バッチ2: 関東・中部（16都道府県）
 * 毎日深夜2時15分実行（バッチ1の15分後）
 *
 * @return {Object} 処理結果
 */
function warmUpMapCompleteCache_Batch2() {
  const startTime = new Date();
  Logger.log('=== キャッシュウォームアップ バッチ2 開始 ===');

  const batch2Prefectures = [
    '茨城県', '栃木県', '群馬県', '埼玉県', '千葉県', '東京都', '神奈川県',
    '新潟県', '富山県', '石川県', '福井県', '山梨県', '長野県', '岐阜県', '静岡県', '愛知県'
  ];

  const result = warmUpMapCompleteCacheBatch(batch2Prefectures, 'バッチ2（関東・中部）');

  const endTime = new Date();
  const totalSeconds = Math.floor((endTime - startTime) / 1000);

  Logger.log('=== バッチ2 完了: ' + totalSeconds + '秒 ===');

  // 結果を保存
  try {
    PropertiesService.getScriptProperties().setProperty(
      'lastWarmUpResult_Batch2',
      JSON.stringify({
        timestamp: endTime.toISOString(),
        duration_seconds: totalSeconds,
        total_prefectures: batch2Prefectures.length,
        success: result.success,
        failure: result.failure,
        errors: result.errors
      })
    );
  } catch (e) {
    Logger.log('⚠️ バッチ2結果の保存に失敗: ' + e.message);
  }

  return result;
}

/**
 * バッチ3: 近畿・中国・四国・九州・沖縄（24都道府県）
 * 毎日深夜2時30分実行（バッチ2の15分後）
 *
 * @return {Object} 処理結果
 */
function warmUpMapCompleteCache_Batch3() {
  const startTime = new Date();
  Logger.log('=== キャッシュウォームアップ バッチ3 開始 ===');

  const batch3Prefectures = [
    '三重県', '滋賀県', '京都府', '大阪府', '兵庫県', '奈良県', '和歌山県',
    '鳥取県', '島根県', '岡山県', '広島県', '山口県',
    '徳島県', '香川県', '愛媛県', '高知県',
    '福岡県', '佐賀県', '長崎県', '熊本県', '大分県', '宮崎県', '鹿児島県', '沖縄県'
  ];

  const result = warmUpMapCompleteCacheBatch(batch3Prefectures, 'バッチ3（近畿・中国・四国・九州・沖縄）');

  const endTime = new Date();
  const totalSeconds = Math.floor((endTime - startTime) / 1000);

  Logger.log('=== バッチ3 完了: ' + totalSeconds + '秒 ===');

  // 結果を保存
  try {
    PropertiesService.getScriptProperties().setProperty(
      'lastWarmUpResult_Batch3',
      JSON.stringify({
        timestamp: endTime.toISOString(),
        duration_seconds: totalSeconds,
        total_prefectures: batch3Prefectures.length,
        success: result.success,
        failure: result.failure,
        errors: result.errors
      })
    );
  } catch (e) {
    Logger.log('⚠️ バッチ3結果の保存に失敗: ' + e.message);
  }

  return result;
}

/**
 * 共通バッチ処理関数
 *
 * @param {Array<string>} prefectures - 処理する都道府県のリスト
 * @param {string} batchName - バッチ名（ログ用）
 * @return {Object} 処理結果 {success: number, failure: number, errors: Array<string>}
 */
function warmUpMapCompleteCacheBatch(prefectures, batchName) {
  let successCount = 0;
  let failureCount = 0;
  const errors = [];

  prefectures.forEach(function(prefecture, index) {
    try {
      Logger.log('[' + batchName + '] [' + (index + 1) + '/' + prefectures.length + '] ' + prefecture + ' のキャッシュ生成中...');

      // 都道府県レベルのキャッシュ生成
      getMapCompleteData(prefecture, null);
      successCount++;

      // API制限を考慮して少し待機
      Utilities.sleep(100);

    } catch (e) {
      failureCount++;
      errors.push(prefecture + ': ' + e.message);
      Logger.log('❌ ' + prefecture + ' のキャッシュ生成に失敗: ' + e.message);
    }
  });

  return {
    success: successCount,
    failure: failureCount,
    errors: errors
  };
}

/**
 * 3つのバッチトリガーを一括設定
 * メニューから手動実行してトリガーを追加
 *
 * 実行スケジュール:
 * - バッチ1（北海道・東北）: 毎日深夜2:00
 * - バッチ2（関東・中部）: 毎日深夜2:15
 * - バッチ3（近畿以西）: 毎日深夜2:30
 */
function setupDailyWarmUpTrigger_3Batches() {
  const ui = SpreadsheetApp.getUi();

  // 既存のトリガーを確認
  const triggers = ScriptApp.getProjectTriggers();
  const existingBatch1 = triggers.find(function(t) { return t.getHandlerFunction() === 'warmUpMapCompleteCache_Batch1'; });
  const existingBatch2 = triggers.find(function(t) { return t.getHandlerFunction() === 'warmUpMapCompleteCache_Batch2'; });
  const existingBatch3 = triggers.find(function(t) { return t.getHandlerFunction() === 'warmUpMapCompleteCache_Batch3'; });

  if (existingBatch1 && existingBatch2 && existingBatch3) {
    ui.alert(
      'トリガー設定済み',
      '3つのバッチトリガーは既に設定されています。\n\n' +
      '確認: 拡張機能 > Apps Script > トリガー',
      ui.ButtonSet.OK
    );
    return;
  }

  // バッチ1: 深夜2時
  if (!existingBatch1) {
    ScriptApp.newTrigger('warmUpMapCompleteCache_Batch1')
      .timeBased()
      .atHour(2)
      .everyDays(1)
      .create();
    Logger.log('✅ バッチ1トリガー設定完了（毎日深夜2:00）');
  }

  // バッチ2: 深夜2時15分
  if (!existingBatch2) {
    ScriptApp.newTrigger('warmUpMapCompleteCache_Batch2')
      .timeBased()
      .atHour(2)
      .nearMinute(15)
      .everyDays(1)
      .create();
    Logger.log('✅ バッチ2トリガー設定完了（毎日深夜2:15）');
  }

  // バッチ3: 深夜2時30分
  if (!existingBatch3) {
    ScriptApp.newTrigger('warmUpMapCompleteCache_Batch3')
      .timeBased()
      .atHour(2)
      .nearMinute(30)
      .everyDays(1)
      .create();
    Logger.log('✅ バッチ3トリガー設定完了（毎日深夜2:30）');
  }

  ui.alert(
    'トリガー設定完了 ✅',
    '3つのバッチトリガーを設定しました。\n\n' +
    'バッチ1（北海道・東北 7都道府県）: 毎日深夜2:00\n' +
    'バッチ2（関東・中部 16都道府県）: 毎日深夜2:15\n' +
    'バッチ3（近畿以西 24都道府県）: 毎日深夜2:30\n\n' +
    '合計47都道府県のキャッシュを自動生成します。\n\n' +
    '確認: 拡張機能 > Apps Script > トリガー',
    ui.ButtonSet.OK
  );
}

/**
 * 全バッチの実行結果を確認
 * メニューから手動実行して各バッチの実行状況を確認
 */
function checkAllBatchResults() {
  const props = PropertiesService.getScriptProperties();

  const batch1Json = props.getProperty('lastWarmUpResult_Batch1');
  const batch2Json = props.getProperty('lastWarmUpResult_Batch2');
  const batch3Json = props.getProperty('lastWarmUpResult_Batch3');

  let message = '=== 全バッチ実行結果 ===\n\n';
  let totalSuccess = 0;
  let totalFailure = 0;
  let totalDuration = 0;

  if (batch1Json) {
    const batch1 = JSON.parse(batch1Json);
    message += '【バッチ1（北海道・東北 7都道府県）】\n' +
      '最終実行: ' + batch1.timestamp + '\n' +
      '実行時間: ' + batch1.duration_seconds + '秒\n' +
      '成功: ' + batch1.success + '件 / 失敗: ' + batch1.failure + '件\n\n';
    totalSuccess += batch1.success;
    totalFailure += batch1.failure;
    totalDuration += batch1.duration_seconds;
  } else {
    message += '【バッチ1】未実行\n\n';
  }

  if (batch2Json) {
    const batch2 = JSON.parse(batch2Json);
    message += '【バッチ2（関東・中部 16都道府県）】\n' +
      '最終実行: ' + batch2.timestamp + '\n' +
      '実行時間: ' + batch2.duration_seconds + '秒\n' +
      '成功: ' + batch2.success + '件 / 失敗: ' + batch2.failure + '件\n\n';
    totalSuccess += batch2.success;
    totalFailure += batch2.failure;
    totalDuration += batch2.duration_seconds;
  } else {
    message += '【バッチ2】未実行\n\n';
  }

  if (batch3Json) {
    const batch3 = JSON.parse(batch3Json);
    message += '【バッチ3（近畿以西 24都道府県）】\n' +
      '最終実行: ' + batch3.timestamp + '\n' +
      '実行時間: ' + batch3.duration_seconds + '秒\n' +
      '成功: ' + batch3.success + '件 / 失敗: ' + batch3.failure + '件\n\n';
    totalSuccess += batch3.success;
    totalFailure += batch3.failure;
    totalDuration += batch3.duration_seconds;
  } else {
    message += '【バッチ3】未実行\n\n';
  }

  // 統合サマリー
  if (batch1Json || batch2Json || batch3Json) {
    message += '━━━━━━━━━━━━━━━━━━━━\n';
    message += '【統合サマリー】\n';
    message += '合計成功: ' + totalSuccess + ' / 47都道府県\n';
    message += '合計失敗: ' + totalFailure + '件\n';
    message += '合計実行時間: ' + totalDuration + '秒（' + Math.floor(totalDuration / 60) + '分' + (totalDuration % 60) + '秒）\n';
  }

  SpreadsheetApp.getUi().alert(
    'バッチ実行結果',
    message,
    SpreadsheetApp.getUi().ButtonSet.OK
  );

  Logger.log(message);
}

/**
 * すべてのバッチトリガーを削除
 * トリガーをリセットする場合に使用
 */
function removeAllBatchTriggers() {
  const ui = SpreadsheetApp.getUi();

  const response = ui.alert(
    'トリガー削除確認',
    '3つのバッチトリガーをすべて削除しますか？\n\n' +
    'この操作は元に戻せません。',
    ui.ButtonSet.YES_NO
  );

  if (response !== ui.Button.YES) {
    return;
  }

  const triggers = ScriptApp.getProjectTriggers();
  let removedCount = 0;

  triggers.forEach(function(trigger) {
    const funcName = trigger.getHandlerFunction();
    if (funcName === 'warmUpMapCompleteCache_Batch1' ||
        funcName === 'warmUpMapCompleteCache_Batch2' ||
        funcName === 'warmUpMapCompleteCache_Batch3') {
      ScriptApp.deleteTrigger(trigger);
      removedCount++;
      Logger.log('削除: ' + funcName);
    }
  });

  ui.alert(
    'トリガー削除完了',
    removedCount + '個のバッチトリガーを削除しました。',
    ui.ButtonSet.OK
  );

  Logger.log('✅ ' + removedCount + '個のバッチトリガーを削除');
}

// ============================================================
// PropertiesService キャッシュ管理
// ============================================================

/**
 * 古いキャッシュを削除
 * PropertiesServiceは有効期限がないため、定期的に古いキャッシュを削除する必要がある
 *
 * @return {Object} 削除結果 {deletedCount: number, currentSize: number, keys: Array<string>}
 */
function clearOldCache() {
  const props = PropertiesService.getScriptProperties();
  const allProps = props.getProperties();
  const cacheMaxAge = 24 * 60 * 60 * 1000; // 24時間（ミリ秒）

  let deletedCount = 0;
  const deletedKeys = [];

  Object.keys(allProps).forEach(function(key) {
    // キャッシュキー（mapComplete_ または phase12to14_ で始まる）のみ処理
    if (key.indexOf('mapComplete_') === 0 || key.indexOf('phase12to14_') === 0) {
      // タイムスタンプキーの場合はスキップ（データキーと一緒に削除される）
      if (key.indexOf('_timestamp') > 0) {
        return;
      }

      const timestampKey = key + '_timestamp';
      const timestamp = allProps[timestampKey];

      if (timestamp) {
        const cacheAge = Date.now() - parseInt(timestamp);

        if (cacheAge > cacheMaxAge) {
          // 期限切れ
          try {
            props.deleteProperty(key);
            props.deleteProperty(timestampKey);
            deletedCount++;
            deletedKeys.push(key);
            Logger.log('[clearOldCache] 削除: ' + key + ' (経過: ' + Math.floor(cacheAge / 1000 / 60 / 60) + '時間)');
          } catch (e) {
            Logger.log('[clearOldCache] 削除失敗: ' + key + ' - ' + e);
          }
        }
      } else {
        // タイムスタンプがない古いキャッシュ（移行前の残骸）
        try {
          props.deleteProperty(key);
          deletedCount++;
          deletedKeys.push(key);
          Logger.log('[clearOldCache] タイムスタンプなしキャッシュを削除: ' + key);
        } catch (e) {
          Logger.log('[clearOldCache] 削除失敗: ' + key + ' - ' + e);
        }
      }
    }
  });

  // 残存キャッシュサイズを計算
  const remainingProps = props.getProperties();
  let totalSize = 0;
  Object.keys(remainingProps).forEach(function(key) {
    if (key.indexOf('mapComplete_') === 0 || key.indexOf('phase12to14_') === 0) {
      totalSize += remainingProps[key].length;
    }
  });

  const result = {
    deletedCount: deletedCount,
    deletedKeys: deletedKeys,
    currentSizeKB: Math.round(totalSize / 1024),
    currentSizeMB: (totalSize / 1024 / 1024).toFixed(2)
  };

  Logger.log('[clearOldCache] 完了 - 削除: ' + deletedCount + '件, 残存サイズ: ' + result.currentSizeKB + 'KB (' + result.currentSizeMB + 'MB)');

  return result;
}

/**
 * すべてのキャッシュを削除（緊急用）
 * PropertiesServiceの容量が逼迫した場合に使用
 */
function clearAllCache() {
  const ui = SpreadsheetApp.getUi();

  const response = ui.alert(
    'キャッシュ全削除確認',
    'すべてのキャッシュを削除しますか？\n\n' +
    '削除後は再度キャッシュ生成が必要です。\n' +
    'この操作は元に戻せません。',
    ui.ButtonSet.YES_NO
  );

  if (response !== ui.Button.YES) {
    return;
  }

  const props = PropertiesService.getScriptProperties();
  const allProps = props.getProperties();

  let deletedCount = 0;

  Object.keys(allProps).forEach(function(key) {
    // キャッシュキー（mapComplete_ または phase12to14_ で始まる）のみ削除
    if (key.indexOf('mapComplete_') === 0 || key.indexOf('phase12to14_') === 0) {
      try {
        props.deleteProperty(key);
        deletedCount++;
        Logger.log('[clearAllCache] 削除: ' + key);
      } catch (e) {
        Logger.log('[clearAllCache] 削除失敗: ' + key + ' - ' + e);
      }
    }
  });

  ui.alert(
    'キャッシュ削除完了',
    deletedCount + '個のキャッシュを削除しました。\n\n' +
    '次回アクセス時にキャッシュが再生成されます。',
    ui.ButtonSet.OK
  );

  Logger.log('[clearAllCache] 完了 - 削除: ' + deletedCount + '件');
}

/**
 * キャッシュの状態を確認
 * 現在のキャッシュサイズと件数を表示
 */
function checkCacheStatus() {
  const props = PropertiesService.getScriptProperties();
  const allProps = props.getProperties();

  let cacheCount = 0;
  let totalSize = 0;
  const cacheKeys = [];

  Object.keys(allProps).forEach(function(key) {
    if ((key.indexOf('mapComplete_') === 0 || key.indexOf('phase12to14_') === 0) && key.indexOf('_timestamp') < 0) {
      cacheCount++;
      totalSize += allProps[key].length;
      cacheKeys.push(key);
    }
  });

  const totalSizeKB = Math.round(totalSize / 1024);
  const totalSizeMB = (totalSize / 1024 / 1024).toFixed(2);
  const usagePercent = ((totalSize / (9 * 1024 * 1024)) * 100).toFixed(1);

  const message =
    '=== キャッシュ状態 ===\n\n' +
    'キャッシュ件数: ' + cacheCount + '件\n' +
    '合計サイズ: ' + totalSizeKB + 'KB (' + totalSizeMB + 'MB)\n' +
    '使用率: ' + usagePercent + '% / 9MB\n\n' +
    (cacheCount > 0 ? 'キャッシュキー（最初の5件）:\n' + cacheKeys.slice(0, 5).join('\n') : 'キャッシュなし');

  SpreadsheetApp.getUi().alert(
    'キャッシュ状態',
    message,
    SpreadsheetApp.getUi().ButtonSet.OK
  );

  Logger.log(message);

  return {
    cacheCount: cacheCount,
    totalSizeKB: totalSizeKB,
    totalSizeMB: parseFloat(totalSizeMB),
    usagePercent: parseFloat(usagePercent),
    cacheKeys: cacheKeys
  };
}

