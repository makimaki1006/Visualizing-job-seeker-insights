const fs = require('fs');
const path = require('path');
const vm = require('vm');

function loadScript(filePath, sandbox) {
  const code = fs.readFileSync(filePath, 'utf8');
  vm.runInContext(code, sandbox, { filename: path.basename(filePath) });
}

function createSandbox() {
  const sandbox = {
    console,
    Math,
    Number,
    Date,
    JSON,
    Map,
    Set,
    Utilities: {
      formatDate: () => '2025-11-02',
    },
    Session: {
      getScriptTimeZone: () => 'Asia/Tokyo',
    },
    saveSelectedRegion: () => {},
    getRegionOptions: () => ({
      state: { prefecture: '京都府', municipality: '京都市伏見区' },
      prefectures: ['京都府'],
    }),
    getAvailablePrefectures: () => ['京都府'],
    getMunicipalitiesForPrefecture: () => ['京都市伏見区'],
    buildRegionKey: (pref, muni) => `${pref}-${muni}`,
    resolveRegionContext: (pref, muni) => ({ prefecture: pref, municipality: muni }),
    fetchPhase1Metrics: () => ({
      tables: {
        mapMetrics: [
          {
            prefecture: '京都府',
            municipality: '京都市伏見区',
            applicant_count: 400,
            male_count: 180,
            female_count: 220,
            avg_age: 46.2,
            avg_qualifications: 1.8,
            latitude: 34.935,
            longitude: 135.76,
          },
        ],
        quality: [],
      },
    }),
    fetchPhase3Persona: () => ({
      tables: {
        personaSummary: [
          { persona: '30代女性×常勤', difficulty_level: '中', count: 120, difficulty_score: 3.8 },
        ],
        personaDetails: [
          { persona: '30代女性×常勤', attribute: '看護師経験10年以上', count: 58 },
        ],
        quality: [],
      },
      summary: { averageDifficultyScore: 3.8 },
    }),
    fetchPhase7Supply: () => ({
      tables: {
        supplyDensity: [
          {
            location: '京都府京都市伏見区',
            supply_count: 400,
            avg_age: 46.2,
            national_license_count: 42,
            avg_qualifications: 1.8,
          },
        ],
        ageGenderCross: [
          { age_group: '30代', gender: '女性', count: 120, avg_qualifications: 1.9 },
          { age_group: '40代', gender: '男性', count: 80, avg_qualifications: 1.5 },
        ],
        personaProfile: [
          {
            age_group: '30代',
            gender: '女性',
            employment_status: '常勤',
            count: 120,
            avg_qualifications: 1.9,
            qualification_bucket: '2資格',
          },
          {
            age_group: '40代',
            gender: '男性',
            employment_status: '非常勤',
            count: 60,
            avg_qualifications: 1.4,
            qualification_bucket: '1資格',
          },
        ],
        personaSummaryByMunicipality: [
          {
            municipality: '京都市伏見区',
            persona: '30代女性×常勤',
            count: 120,
            share: 0.30,
          },
        ],
        personaMobility: [
          { persona_label: '30代女性×常勤', mobility_rank: '30分圏', count: 80 },
          { persona_label: '30代女性×常勤', mobility_rank: '60分圏', count: 40 },
        ],
        personaMapData: [
          { persona: '30代女性×常勤', latitude: 34.935, longitude: 135.76, count: 80 },
        ],
        quality: [],
      },
      warnings: [],
    }),
    fetchPhase8Education: () => ({
      tables: {
        educationMatrix: [
          { education_level: '大学卒', age_group: '30代', count: 60 },
          { education_level: '短大卒', age_group: '40代', count: 40 },
        ],
        careerMatrix: [
          { career_cluster: '看護', age_group: '30代', count: 55 },
          { career_cluster: '介護', age_group: '40代', count: 35 },
        ],
        careerDistribution: [
          { career: '看護', count: 200 },
          { career: '介護', count: 150 },
        ],
        graduationDistribution: [
          { graduation_year: '2010', count: 120 },
          { graduation_year: '2015', count: 90 },
        ],
        quality: [],
      },
    }),
    fetchPhase10Urgency: () => ({
      tables: {
        urgencyDistribution: [
          { urgency_rank: 'A', count: 100, avg_urgency_score: 7.2 },
          { urgency_rank: 'B', count: 300, avg_urgency_score: 5.1 },
        ],
        ageCross: [
          { age_group: '30代', count: 150, avg_urgency_score: 6.8 },
          { age_group: '40代', count: 120, avg_urgency_score: 5.4 },
        ],
        employmentCross: [
          { employment_status: '常勤', count: 200, avg_urgency_score: 6.2 },
          { employment_status: '非常勤', count: 80, avg_urgency_score: 4.9 },
        ],
        municipality: [
          { municipality: '京都市伏見区', urgency_rank: 'A', count: 50 },
          { municipality: '京都市伏見区', urgency_rank: 'B', count: 150 },
        ],
        ageMatrix: [
          { age_group: '30代', urgency_rank: 'A', count: 70 },
          { age_group: '40代', urgency_rank: 'B', count: 80 },
        ],
        employmentMatrix: [
          { employment_status: '常勤', urgency_rank: 'A', count: 60 },
          { employment_status: '非常勤', urgency_rank: 'B', count: 90 },
        ],
        quality: [],
      },
      warnings: [],
    }),
  };

  sandbox.Display = { };

  vm.createContext(sandbox);
  return sandbox;
}

function main() {
  const projectRoot = path.resolve(__dirname, '..', '..');
  const gasPath = path.join(projectRoot, 'gas_files', 'scripts', 'MapCompleteDataBridge.gs');

  const sandbox = createSandbox();
  loadScript(gasPath, sandbox);

  if (typeof sandbox.getMapCompleteData !== 'function') {
    throw new Error('getMapCompleteData was not defined in sandbox');
  }

  const result = sandbox.getMapCompleteData('京都府', '京都市伏見区');
  if (!result || !Array.isArray(result.cities) || !result.cities.length) {
    throw new Error('getMapCompleteData did not return expected city array');
  }

  const city = result.cities[0];
  const hasQualificationSummary =
    city.persona &&
    Array.isArray(city.persona.qualification_summary) &&
    city.persona.qualification_summary.length > 0;

  const hasPersonaMunicipality =
    city.persona &&
    Array.isArray(city.persona.personaSummaryByMunicipality) &&
    city.persona.personaSummaryByMunicipality.length > 0;

  if (!hasQualificationSummary) {
    throw new Error('qualification_summary missing from persona payload');
  }
  if (!hasPersonaMunicipality) {
    throw new Error('personaSummaryByMunicipality missing from persona payload');
  }
  if (!city.cross_insights || !city.cross_insights.personaDifficulty) {
    throw new Error('cross_insights.personaDifficulty missing in payload');
  }

  console.log('getMapCompleteData sandbox test passed');
}

main();
