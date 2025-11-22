/**
 * Phase 12-14 データブリッジ（MAP統合用）
 *
 * Python出力のCSVファイルをGASで読み込み、
 * map_complete_integrated.htmlに必要なJSON形式に変換
 *
 * 対応Phase:
 * - Phase 12: 需給ギャップ分析（SupplyDemandGap.csv）
 * - Phase 13: 希少性スコア（RarityScore.csv）
 * - Phase 14: 競合分析（CompetitionProfile.csv）
 */

/**
 * Phase 12-14のCSVデータをロードして、既存のcityデータに統合（全国データ版・非推奨）
 *
 * @deprecated 全国データを返すため、パフォーマンスが悪い。loadPhase12to14DataForRegion() を使用すること
 * @param {string} sheetNameGap - 需給ギャップシート名（デフォルト: 'Phase12_SupplyDemandGap'）
 * @param {string} sheetNameRarity - 希少性スコアシート名（デフォルト: 'Phase13_RarityScore'）
 * @param {string} sheetNameCompetition - 競合分析シート名（デフォルト: 'Phase14_CompetitionProfile'）
 * @return {Object} Phase 12-14データオブジェクト
 */
function loadPhase12to14Data(
  sheetNameGap = 'Phase12_SupplyDemandGap',
  sheetNameRarity = 'Phase13_RarityScore',
  sheetNameCompetition = 'Phase14_CompetitionProfile'
) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();

  const phase12Data = loadPhase12(ss, sheetNameGap);
  const phase13Data = loadPhase13(ss, sheetNameRarity);
  const phase14Data = loadPhase14(ss, sheetNameCompetition);

  return {
    gap: phase12Data,
    rarity: phase13Data,
    competition: phase14Data
  };
}

/**
 * Phase 12-14のCSVデータを選択地域のみロード（パフォーマンス最適化版）
 *
 * @param {string} prefecture - 都道府県名（例: '京都府'）
 * @param {string} municipality - 市区町村名（例: '宇治市'）
 * @param {string} sheetNameGap - 需給ギャップシート名（デフォルト: 'Phase12_SupplyDemandGap'）
 * @param {string} sheetNameRarity - 希少性スコアシート名（デフォルト: 'Phase13_RarityScore'）
 * @param {string} sheetNameCompetition - 競合分析シート名（デフォルト: 'Phase14_CompetitionProfile'）
 * @return {Object} Phase 12-14データオブジェクト（選択地域のみ）
 */
function loadPhase12to14DataForRegion(
  prefecture,
  municipality,
  sheetNameGap = 'Phase12_SupplyDemandGap',
  sheetNameRarity = 'Phase13_RarityScore',
  sheetNameCompetition = 'Phase14_CompetitionProfile'
) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();

  const phase12Data = loadPhase12ForRegion(ss, sheetNameGap, prefecture, municipality);
  const phase13Data = loadPhase13ForRegion(ss, sheetNameRarity, prefecture, municipality);
  const phase14Data = loadPhase14ForRegion(ss, sheetNameCompetition, prefecture, municipality);

  return {
    gap: phase12Data,
    rarity: phase13Data,
    competition: phase14Data
  };
}

/**
 * Phase 12: 需給ギャップ分析データをロード（選択地域のみ）
 *
 * @param {SpreadsheetApp.Spreadsheet} ss - スプレッドシートオブジェクト
 * @param {string} sheetName - シート名
 * @param {string} prefecture - 都道府県名
 * @param {string} municipality - 市区町村名
 * @return {Object} 選択地域の需給ギャップデータ
 */
function loadPhase12ForRegion(ss, sheetName, prefecture, municipality) {
  const sheet = ss.getSheetByName(sheetName);
  if (!sheet) {
    Logger.log(`[Phase12] シート "${sheetName}" が見つかりません`);
    return { data: {}, summary: {} };
  }

  const data = sheet.getDataRange().getValues();
  if (data.length < 2) {
    return { data: {}, summary: {} };
  }

  const headers = data[0];
  const rows = data.slice(1);

  // ヘッダーインデックスを取得
  const idx = {
    prefecture: findColumnIndexByLogicalName(headers, 'prefecture'),
    municipality: findColumnIndexByLogicalName(headers, 'municipality'),
    location: findColumnIndexByLogicalName(headers, 'desired_location_full'),
    demand_count: findColumnIndexByLogicalName(headers, 'demand_count'),
    supply_count: findColumnIndexByLogicalName(headers, 'supply_count'),
    demand_supply_ratio: headers.indexOf('demand_supply_ratio'),
    gap: findColumnIndexByLogicalName(headers, 'gap'),
    latitude: findColumnIndexByLogicalName(headers, 'latitude'),
    longitude: findColumnIndexByLogicalName(headers, 'longitude')
  };

  // 選択地域のデータのみフィルタリング
  const filteredRows = rows.filter(row => {
    const rowPref = safeGetColumn(row, idx.prefecture, '');
    const rowMuni = safeGetColumn(row, idx.municipality, '');
    return rowPref === prefecture && rowMuni === municipality;
  });

  if (filteredRows.length === 0) {
    Logger.log(`[Phase12] ${prefecture}${municipality}のデータが見つかりません`);
    return { data: {}, summary: {} };
  }

  // データを変換
  const record = filteredRows[0]; // 通常1件のはず
  const result = {
    prefecture: safeGetColumn(record, idx.prefecture, ''),
    municipality: safeGetColumn(record, idx.municipality, ''),
    location: safeGetColumn(record, idx.location, ''),
    demand_count: Number(safeGetColumn(record, idx.demand_count, 0)) || 0,
    supply_count: Number(safeGetColumn(record, idx.supply_count, 0)) || 0,
    demand_supply_ratio: Number(safeGetColumn(record, idx.demand_supply_ratio, 0)) || 0,
    gap: Number(safeGetColumn(record, idx.gap, 0)) || 0,
    latitude: safeGetColumn(record, idx.latitude, null),
    longitude: safeGetColumn(record, idx.longitude, null)
  };

  return {
    data: result,
    summary: {
      demand_count: result.demand_count,
      supply_count: result.supply_count,
      demand_supply_ratio: result.demand_supply_ratio,
      gap: result.gap
    }
  };
}

/**
 * Phase 12: 需給ギャップ分析データをロード（全国版・非推奨）
 * @deprecated loadPhase12ForRegion() を使用すること
 */
function loadPhase12(ss, sheetName) {
  const sheet = ss.getSheetByName(sheetName);
  if (!sheet) {
    Logger.log(`[Phase12] シート "${sheetName}" が見つかりません`);
    return { top_gaps: [], top_ratios: [], summary: {} };
  }

  const data = sheet.getDataRange().getValues();
  if (data.length < 2) {
    return { top_gaps: [], top_ratios: [], summary: {} };
  }

  const headers = data[0];
  const rows = data.slice(1);

  // ヘッダーインデックスを取得（ColumnUtils.gs を使用）
  const idx = {
    prefecture: findColumnIndexByLogicalName(headers, 'prefecture'),
    municipality: findColumnIndexByLogicalName(headers, 'municipality'),
    location: findColumnIndexByLogicalName(headers, 'desired_location_full'),
    demand_count: findColumnIndexByLogicalName(headers, 'demand_count'),
    supply_count: findColumnIndexByLogicalName(headers, 'supply_count'),
    demand_supply_ratio: headers.indexOf('demand_supply_ratio'),
    gap: findColumnIndexByLogicalName(headers, 'gap'),
    latitude: findColumnIndexByLogicalName(headers, 'latitude'),
    longitude: findColumnIndexByLogicalName(headers, 'longitude')
  };

  // データを変換（safeGetColumn で安全に取得）
  const records = rows.map(row => ({
    prefecture: safeGetColumn(row, idx.prefecture, ''),
    municipality: safeGetColumn(row, idx.municipality, ''),
    location: safeGetColumn(row, idx.location, ''),
    demand_count: Number(safeGetColumn(row, idx.demand_count, 0)) || 0,
    supply_count: Number(safeGetColumn(row, idx.supply_count, 0)) || 0,
    demand_supply_ratio: Number(safeGetColumn(row, idx.demand_supply_ratio, 0)) || 0,
    gap: Number(safeGetColumn(row, idx.gap, 0)) || 0,
    latitude: safeGetColumn(row, idx.latitude, null),
    longitude: safeGetColumn(row, idx.longitude, null)
  }));

  // Top 10 ギャップ（gap降順）
  const topGaps = records
    .sort((a, b) => b.gap - a.gap)
    .slice(0, 10);

  // Top 10 需給比率（demand_supply_ratio降順）
  const topRatios = records
    .sort((a, b) => b.demand_supply_ratio - a.demand_supply_ratio)
    .slice(0, 10);

  // サマリー
  const totalDemand = records.reduce((sum, r) => sum + r.demand_count, 0);
  const totalSupply = records.reduce((sum, r) => sum + r.supply_count, 0);
  const avgRatio = records.length > 0
    ? records.reduce((sum, r) => sum + r.demand_supply_ratio, 0) / records.length
    : 0;

  return {
    top_gaps: topGaps,
    top_ratios: topRatios,
    all_records: records, // ★追加：全レコード（各locationのデータ）
    summary: {
      total_locations: records.length,
      total_demand: totalDemand,
      total_supply: totalSupply,
      avg_ratio: avgRatio
    }
  };
}

/**
 * Phase 13: 希少性スコアデータをロード
 */
function loadPhase13(ss, sheetName) {
  const sheet = ss.getSheetByName(sheetName);
  if (!sheet) {
    Logger.log(`[Phase13] シート "${sheetName}" が見つかりません`);
    return { rank_distribution: {}, top_rarity: [], summary: {} };
  }

  const data = sheet.getDataRange().getValues();
  if (data.length < 2) {
    return { rank_distribution: {}, top_rarity: [], summary: {} };
  }

  const headers = data[0];
  const rows = data.slice(1);

  // ヘッダーインデックスを取得（ColumnUtils.gs を使用）
  const idx = {
    prefecture: findColumnIndexByLogicalName(headers, 'prefecture'),
    municipality: findColumnIndexByLogicalName(headers, 'municipality'),
    location: findColumnIndexByLogicalName(headers, 'desired_location_full'),
    age_bucket: headers.indexOf('age_bucket'),
    gender: findColumnIndexByLogicalName(headers, 'gender'),
    has_national_license: findColumnIndexByLogicalName(headers, 'has_national_license'),
    count: findColumnIndexByLogicalName(headers, 'count'),
    rarity_score: headers.indexOf('rarity_score'),
    rarity_rank: headers.indexOf('rarity_rank'),
    latitude: findColumnIndexByLogicalName(headers, 'latitude'),
    longitude: findColumnIndexByLogicalName(headers, 'longitude')
  };

  // データを変換（safeGetColumn で安全に取得）
  const records = rows.map(row => ({
    prefecture: safeGetColumn(row, idx.prefecture, ''),
    municipality: safeGetColumn(row, idx.municipality, ''),
    location: safeGetColumn(row, idx.location, ''),
    age_bucket: safeGetColumn(row, idx.age_bucket, ''),
    gender: safeGetColumn(row, idx.gender, ''),
    has_national_license: safeGetColumn(row, idx.has_national_license, false) === true || safeGetColumn(row, idx.has_national_license, '') === 'True',
    count: Number(safeGetColumn(row, idx.count, 0)) || 0,
    rarity_score: Number(safeGetColumn(row, idx.rarity_score, 0)) || 0,
    rarity_rank: safeGetColumn(row, idx.rarity_rank, ''),
    latitude: safeGetColumn(row, idx.latitude, null),
    longitude: safeGetColumn(row, idx.longitude, null)
  }));

  // 希少性ランク分布
  const rankDistribution = {};
  records.forEach(r => {
    const rank = r.rarity_rank || 'その他';
    rankDistribution[rank] = (rankDistribution[rank] || 0) + 1;
  });

  // Top 15 希少性スコア（rarity_score降順）
  const topRarity = records
    .sort((a, b) => b.rarity_score - a.rarity_score)
    .slice(0, 15);

  // サマリー
  const sRank = records.filter(r => r.rarity_rank.startsWith('S')).length;
  const aRank = records.filter(r => r.rarity_rank.startsWith('A')).length;
  const bRank = records.filter(r => r.rarity_rank.startsWith('B')).length;

  return {
    rank_distribution: rankDistribution,
    top_rarity: topRarity,
    all_records: records, // ★追加：全レコード（各locationのデータ）
    summary: {
      total_combinations: records.length,
      s_rank: sRank,
      a_rank: aRank,
      b_rank: bRank
    }
  };
}

/**
 * Phase 14: 競合分析データをロード
 */
function loadPhase14(ss, sheetName) {
  const sheet = ss.getSheetByName(sheetName);
  if (!sheet) {
    Logger.log(`[Phase14] シート "${sheetName}" が見つかりません`);
    return { top_locations: [], summary: {} };
  }

  const data = sheet.getDataRange().getValues();
  if (data.length < 2) {
    return { top_locations: [], summary: {} };
  }

  const headers = data[0];
  const rows = data.slice(1);

  // ヘッダーインデックスを取得
  const idx = {
    prefecture: headers.indexOf('prefecture'),
    municipality: headers.indexOf('municipality'),
    location: headers.indexOf('location'),
    total_applicants: headers.indexOf('total_applicants'),
    top_age_group: headers.indexOf('top_age_group'),
    top_age_ratio: headers.indexOf('top_age_ratio'),
    female_ratio: headers.indexOf('female_ratio'),
    male_ratio: headers.indexOf('male_ratio'),
    national_license_rate: headers.indexOf('national_license_rate'),
    top_employment_status: headers.indexOf('top_employment_status'),
    top_employment_ratio: headers.indexOf('top_employment_ratio'),
    avg_qualification_count: headers.indexOf('avg_qualification_count'),
    latitude: headers.indexOf('latitude'),
    longitude: headers.indexOf('longitude')
  };

  // データを変換
  const records = rows.map(row => ({
    prefecture: row[idx.prefecture] || '',
    municipality: row[idx.municipality] || '',
    location: row[idx.location] || '',
    total_applicants: Number(row[idx.total_applicants]) || 0,
    top_age_group: row[idx.top_age_group] || '',
    top_age_ratio: Number(row[idx.top_age_ratio]) || 0,
    female_ratio: Number(row[idx.female_ratio]) || 0,
    male_ratio: Number(row[idx.male_ratio]) || 0,
    national_license_rate: Number(row[idx.national_license_rate]) || 0,
    top_employment_status: row[idx.top_employment_status] || '',
    top_employment_ratio: Number(row[idx.top_employment_ratio]) || 0,
    avg_qualification_count: Number(row[idx.avg_qualification_count]) || 0,
    latitude: row[idx.latitude] || null,
    longitude: row[idx.longitude] || null
  }));

  // Top 15 総応募者数（total_applicants降順）
  const topLocations = records
    .sort((a, b) => b.total_applicants - a.total_applicants)
    .slice(0, 15);

  // サマリー
  const totalApplicants = records.reduce((sum, r) => sum + r.total_applicants, 0);
  const avgFemaleRatio = records.length > 0
    ? records.reduce((sum, r) => sum + r.female_ratio, 0) / records.length
    : 0;
  const avgNationalLicenseRate = records.length > 0
    ? records.reduce((sum, r) => sum + r.national_license_rate, 0) / records.length
    : 0;

  return {
    top_locations: topLocations,
    all_records: records, // ★追加：全レコード（各locationのデータ）
    summary: {
      total_locations: records.length,
      total_applicants: totalApplicants,
      avg_female_ratio: avgFemaleRatio,
      avg_national_license_rate: avgNationalLicenseRate
    }
  };
}

/**
 * Phase 12-14データを含むMAPデータを生成
 *
 * 既存のgetMapCompleteData()関数を拡張して、Phase 12-14データを追加
 *
 * @return {Array<Object>} 都市データ配列
 */
function getMapCompleteDataWithPhase12to14() {
  // 既存のgetMapCompleteData()を呼び出し（既存のPhase 1-10データ）
  // ※ 実際の実装では、既存のgetMapCompleteData()関数をインポートまたは統合する必要があります
  const citiesData = getMapCompleteData(); // 既存関数を呼び出し

  // Phase 12-14データをロード
  const phase12to14Data = loadPhase12to14Data();

  // 各都市データにPhase 12-14を追加
  // ※ 注: 現在の実装では全都市に同じPhase 12-14データを追加していますが、
  //   実際には都市ごとにフィルタリングする必要がある場合があります
  citiesData.forEach(city => {
    city.gap = phase12to14Data.gap;
    city.rarity = phase12to14Data.rarity;
    city.competition = phase12to14Data.competition;
  });

  return citiesData;
}

/**
 * テスト用: Phase 12-14データのみをログ出力
 */
function testPhase12to14Load() {
  const data = loadPhase12to14Data();

  Logger.log('=== Phase 12: 需給ギャップ分析 ===');
  Logger.log(`総地域数: ${data.gap.summary.total_locations}`);
  Logger.log(`Top 5 ギャップ:`);
  data.gap.top_gaps.slice(0, 5).forEach((item, i) => {
    Logger.log(`  ${i+1}. ${item.location}: 需要=${item.demand_count}, 供給=${item.supply_count}, ギャップ=${item.gap}`);
  });

  Logger.log('\n=== Phase 13: 希少性スコア ===');
  Logger.log(`総組み合わせ数: ${data.rarity.summary.total_combinations}`);
  Logger.log(`S rank: ${data.rarity.summary.s_rank}件`);
  Logger.log(`Top 5 希少性:`);
  data.rarity.top_rarity.slice(0, 5).forEach((item, i) => {
    Logger.log(`  ${i+1}. ${item.location} ${item.age_bucket} ${item.gender}: スコア=${item.rarity_score}`);
  });

  Logger.log('\n=== Phase 14: 競合分析 ===');
  Logger.log(`総地域数: ${data.competition.summary.total_locations}`);
  Logger.log(`Top 5 競争激しい地域:`);
  data.competition.top_locations.slice(0, 5).forEach((item, i) => {
    Logger.log(`  ${i+1}. ${item.location}: 総応募者数=${item.total_applicants}, 女性比率=${(item.female_ratio*100).toFixed(1)}%`);
  });
}

/**
 * Phase 12-14用のHTMLダイアログを表示
 */
function showMapPhase12to14() {
  const html = HtmlService.createHtmlOutputFromFile('map_complete_integrated')
    .setWidth(1800)
    .setHeight(1100)
    .setTitle('求職者分析ダッシュボード | Map Complete（Phase 12-14統合版）');

  SpreadsheetApp.getUi().showModalDialog(html, '求職者分析ダッシュボード | MAP分析（Phase 12-14統合）');
}

/**
 * GAS用：Phase 12-14データをJSON形式で返す（HTML側から呼び出し）
 */
function getPhase12to14DataJSON() {
  return loadPhase12to14Data();
}

/**
 * Phase 13: 希少性スコアデータをロード（選択地域のみ）
 *
 * @param {SpreadsheetApp.Spreadsheet} ss - スプレッドシートオブジェクト
 * @param {string} sheetName - シート名
 * @param {string} prefecture - 都道府県名
 * @param {string} municipality - 市区町村名
 * @return {Object} 選択地域の希少性スコアデータ
 */
function loadPhase13ForRegion(ss, sheetName, prefecture, municipality) {
  const sheet = ss.getSheetByName(sheetName);
  if (!sheet) {
    Logger.log(`[Phase13] シート "${sheetName}" が見つかりません`);
    return { records: [], rank_distribution: {}, summary: {} };
  }

  const data = sheet.getDataRange().getValues();
  if (data.length < 2) {
    return { records: [], rank_distribution: {}, summary: {} };
  }

  const headers = data[0];
  const rows = data.slice(1);

  // ヘッダーインデックスを取得
  const idx = {
    prefecture: findColumnIndexByLogicalName(headers, 'prefecture'),
    municipality: findColumnIndexByLogicalName(headers, 'municipality'),
    location: findColumnIndexByLogicalName(headers, 'desired_location_full'),
    age_bucket: headers.indexOf('age_bucket'),
    gender: findColumnIndexByLogicalName(headers, 'gender'),
    has_national_license: findColumnIndexByLogicalName(headers, 'has_national_license'),
    count: findColumnIndexByLogicalName(headers, 'count'),
    rarity_score: headers.indexOf('rarity_score'),
    rarity_rank: headers.indexOf('rarity_rank'),
    latitude: findColumnIndexByLogicalName(headers, 'latitude'),
    longitude: findColumnIndexByLogicalName(headers, 'longitude')
  };

  // 選択地域のデータのみフィルタリング
  const filteredRows = rows.filter(row => {
    const rowPref = safeGetColumn(row, idx.prefecture, '');
    const rowMuni = safeGetColumn(row, idx.municipality, '');
    return rowPref === prefecture && rowMuni === municipality;
  });

  if (filteredRows.length === 0) {
    Logger.log(`[Phase13] ${prefecture}${municipality}のデータが見つかりません`);
    return { records: [], rank_distribution: {}, summary: {} };
  }

  // データを変換
  const records = filteredRows.map(row => ({
    prefecture: safeGetColumn(row, idx.prefecture, ''),
    municipality: safeGetColumn(row, idx.municipality, ''),
    location: safeGetColumn(row, idx.location, ''),
    age_bucket: safeGetColumn(row, idx.age_bucket, ''),
    gender: safeGetColumn(row, idx.gender, ''),
    has_national_license: safeGetColumn(row, idx.has_national_license, false) === true || safeGetColumn(row, idx.has_national_license, '') === 'True',
    count: Number(safeGetColumn(row, idx.count, 0)) || 0,
    rarity_score: Number(safeGetColumn(row, idx.rarity_score, 0)) || 0,
    rarity_rank: safeGetColumn(row, idx.rarity_rank, ''),
    latitude: safeGetColumn(row, idx.latitude, null),
    longitude: safeGetColumn(row, idx.longitude, null)
  }));

  // 希少性スコア降順でソート
  records.sort((a, b) => b.rarity_score - a.rarity_score);

  // 希少性ランク分布
  const rankDistribution = {};
  records.forEach(r => {
    const rank = r.rarity_rank || 'その他';
    rankDistribution[rank] = (rankDistribution[rank] || 0) + 1;
  });

  // サマリー
  const sRank = records.filter(r => r.rarity_rank.startsWith('S')).length;
  const aRank = records.filter(r => r.rarity_rank.startsWith('A')).length;
  const bRank = records.filter(r => r.rarity_rank.startsWith('B')).length;

  return {
    records: records,
    rank_distribution: rankDistribution,
    summary: {
      total_combinations: records.length,
      s_rank: sRank,
      a_rank: aRank,
      b_rank: bRank
    }
  };
}

/**
 * Phase 14: 競合分析データをロード（選択地域のみ）
 *
 * @param {SpreadsheetApp.Spreadsheet} ss - スプレッドシートオブジェクト
 * @param {string} sheetName - シート名
 * @param {string} prefecture - 都道府県名
 * @param {string} municipality - 市区町村名
 * @return {Object} 選択地域の競合分析データ
 */
function loadPhase14ForRegion(ss, sheetName, prefecture, municipality) {
  const sheet = ss.getSheetByName(sheetName);
  if (!sheet) {
    Logger.log(`[Phase14] シート "${sheetName}" が見つかりません`);
    return { data: {}, summary: {} };
  }

  const data = sheet.getDataRange().getValues();
  if (data.length < 2) {
    return { data: {}, summary: {} };
  }

  const headers = data[0];
  const rows = data.slice(1);

  // ヘッダーインデックスを取得
  const idx = {
    prefecture: headers.indexOf('prefecture'),
    municipality: headers.indexOf('municipality'),
    location: headers.indexOf('location'),
    total_applicants: headers.indexOf('total_applicants'),
    top_age_group: headers.indexOf('top_age_group'),
    top_age_ratio: headers.indexOf('top_age_ratio'),
    female_ratio: headers.indexOf('female_ratio'),
    male_ratio: headers.indexOf('male_ratio'),
    national_license_rate: headers.indexOf('national_license_rate'),
    top_employment_status: headers.indexOf('top_employment_status'),
    top_employment_ratio: headers.indexOf('top_employment_ratio'),
    avg_qualification_count: headers.indexOf('avg_qualification_count'),
    latitude: headers.indexOf('latitude'),
    longitude: headers.indexOf('longitude')
  };

  // 選択地域のデータのみフィルタリング
  const filteredRows = rows.filter(row => {
    const rowPref = row[idx.prefecture] || '';
    const rowMuni = row[idx.municipality] || '';
    return rowPref === prefecture && rowMuni === municipality;
  });

  if (filteredRows.length === 0) {
    Logger.log(`[Phase14] ${prefecture}${municipality}のデータが見つかりません`);
    return { data: {}, summary: {} };
  }

  // データを変換（通常1件のはず）
  const record = filteredRows[0];
  const result = {
    prefecture: record[idx.prefecture] || '',
    municipality: record[idx.municipality] || '',
    location: record[idx.location] || '',
    total_applicants: Number(record[idx.total_applicants]) || 0,
    top_age_group: record[idx.top_age_group] || '',
    top_age_ratio: Number(record[idx.top_age_ratio]) || 0,
    female_ratio: Number(record[idx.female_ratio]) || 0,
    male_ratio: Number(record[idx.male_ratio]) || 0,
    national_license_rate: Number(record[idx.national_license_rate]) || 0,
    top_employment_status: record[idx.top_employment_status] || '',
    top_employment_ratio: Number(record[idx.top_employment_ratio]) || 0,
    avg_qualification_count: Number(record[idx.avg_qualification_count]) || 0,
    latitude: record[idx.latitude] || null,
    longitude: record[idx.longitude] || null
  };

  return {
    data: result,
    summary: {
      total_applicants: result.total_applicants,
      female_ratio: result.female_ratio,
      national_license_rate: result.national_license_rate,
      avg_qualification_count: result.avg_qualification_count
    }
  };
}
