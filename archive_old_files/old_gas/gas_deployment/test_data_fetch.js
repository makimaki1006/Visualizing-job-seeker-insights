/**
 * デバッグ用: getMapCompleteDataComplete()の返却データを確認
 */
function testDataFetch() {
  var result = getMapCompleteDataComplete('京都府', '京都市伏見区');
  
  Logger.log('========================================');
  Logger.log('データ取得テスト: 京都府 京都市伏見区');
  Logger.log('========================================');
  
  Logger.log('\n[基本情報]');
  Logger.log('  found: ' + result.found);
  Logger.log('  cities配列: ' + (result.cities ? result.cities.length : 0) + '件');
  
  if (result.cities && result.cities.length > 0) {
    var city = result.cities[0];
    
    Logger.log('\n[city.career]');
    Logger.log('  summary: ' + JSON.stringify(city.career.summary));
    Logger.log('  employment_age.age_labels: ' + city.career.employment_age.age_labels.length + '件');
    Logger.log('  employment_age.rows: ' + city.career.employment_age.rows.length + '件');
    
    Logger.log('\n[city.urgency]');
    Logger.log('  summary: ' + JSON.stringify(city.urgency.summary));
    Logger.log('  by_age: ' + city.urgency.by_age.length + '件');
    Logger.log('  by_employment: ' + city.urgency.by_employment.length + '件');
    
    Logger.log('\n[city.persona]');
    Logger.log('  top: ' + city.persona.top.length + '件');
    if (city.persona.top.length > 0) {
      Logger.log('  top[0]: ' + JSON.stringify(city.persona.top[0]));
    }
    
    Logger.log('\n[city.flow]');
    Logger.log('  nearby_regions: ' + city.flow.nearby_regions.length + '件');
    
    Logger.log('\n[city.gap]');
    Logger.log('  top_gaps: ' + (city.gap.top_gaps ? city.gap.top_gaps.length : 0) + '件');
    Logger.log('  top_ratios: ' + (city.gap.top_ratios ? city.gap.top_ratios.length : 0) + '件');
    Logger.log('  summary.total_demand: ' + (city.gap.summary ? city.gap.summary.total_demand : 0));
    Logger.log('  summary.total_supply: ' + (city.gap.summary ? city.gap.summary.total_supply : 0));

    Logger.log('\n[city.rarity]');
    Logger.log('  top_rarity: ' + (city.rarity.top_rarity ? city.rarity.top_rarity.length : 0) + '件');
    Logger.log('  summary.s_rank: ' + (city.rarity.summary ? city.rarity.summary.s_rank : 0));
    Logger.log('  summary.a_rank: ' + (city.rarity.summary ? city.rarity.summary.a_rank : 0));
    Logger.log('  summary.b_rank: ' + (city.rarity.summary ? city.rarity.summary.b_rank : 0));

    Logger.log('\n[city.competition]');
    Logger.log('  top_locations: ' + (city.competition.top_locations ? city.competition.top_locations.length : 0) + '件');
    Logger.log('  summary.total_applicants: ' + (city.competition.summary ? city.competition.summary.total_applicants : 0));
    Logger.log('  summary.avg_female_ratio: ' + (city.competition.summary ? city.competition.summary.avg_female_ratio : 0));
    Logger.log('  summary.avg_national_license_rate: ' + (city.competition.summary ? city.competition.summary.avg_national_license_rate : 0));
    
    Logger.log('\n[生データ]');
    Logger.log('  age_gender: ' + result.age_gender.length + '件');
    Logger.log('  persona: ' + result.persona.length + '件');
    Logger.log('  persona_muni: ' + result.persona_muni.length + '件');
    Logger.log('  career_cross: ' + result.career_cross.length + '件');
    Logger.log('  urgency_age: ' + result.urgency_age.length + '件');
    Logger.log('  urgency_employment: ' + result.urgency_employment.length + '件');
    Logger.log('  flow: ' + result.flow.length + '件');
    Logger.log('  gap: ' + result.gap.length + '件');
    Logger.log('  rarity: ' + result.rarity.length + '件');
    Logger.log('  competition: ' + result.competition.length + '件');
  }
  
  Logger.log('\n========================================');
  Logger.log('テスト完了');
  Logger.log('========================================');
}
