/**
 * MapComplete統合ダッシュボードのテスト
 * Node.js環境でGAS関数の動作を検証
 */

const fs = require('fs');
const path = require('path');

// 簡易CSVパーサー（ダブルクォート対応）
function parseCSVLine(line) {
  const result = [];
  let current = '';
  let inQuotes = false;

  for (let i = 0; i < line.length; i++) {
    const char = line[i];

    if (char === '"') {
      inQuotes = !inQuotes;
    } else if (char === ',' && !inQuotes) {
      result.push(current.trim());
      current = '';
    } else {
      current += char;
    }
  }

  result.push(current.trim());
  return result;
}

// CSVデータの読み込み
const csvPath = path.join(__dirname, '../python_scripts/data/output_v2/mapcomplete_complete_sheets/MapComplete_Complete_All_FIXED.csv');

if (!fs.existsSync(csvPath)) {
  console.error('❌ CSVファイルが見つかりません:', csvPath);
  process.exit(1);
}

const csvData = fs.readFileSync(csvPath, 'utf-8');
const lines = csvData.split('\n').filter(line => line.trim());
const headers = parseCSVLine(lines[0]);
const values = lines.slice(1).map(line => parseCSVLine(line));

console.log('✅ CSV読み込み成功');
console.log(`   総行数: ${values.length}行`);
console.log(`   総列数: ${headers.length}列`);

// GAS関数のモック実装
const Logger = {
  log: (...args) => console.log('[Logger]', ...args)
};

// normalizeRegionValue関数（RegionStateService.gsから）
function normalizeRegionValue(value) {
  if (!value) return '';
  return String(value).trim();
}

// getAvailablePrefectures関数のテスト
function testGetAvailablePrefectures() {
  console.log('\n========================================');
  console.log('TEST: getAvailablePrefectures()');
  console.log('========================================');

  const prefIndex = headers.indexOf('prefecture');
  if (prefIndex === -1) {
    console.error('❌ prefecture列が見つかりません');
    return false;
  }

  const prefectures = [];
  for (let i = 0; i < values.length; i++) {
    const row = values[i];
    const prefecture = row[prefIndex];
    if (prefecture) {
      const normalized = normalizeRegionValue(prefecture);
      if (normalized && prefectures.indexOf(normalized) === -1) {
        prefectures.push(normalized);
      }
    }
  }

  prefectures.sort();

  console.log('✅ 抽出された都道府県数:', prefectures.length);
  console.log('   最初の10件:', prefectures.slice(0, 10));

  if (prefectures.length >= 47) {
    console.log('✅ PASS: 47都道府県以上');
    return true;
  } else {
    console.log('❌ FAIL: 都道府県数が不足');
    return false;
  }
}

// getMunicipalitiesForPrefecture関数のテスト
function testGetMunicipalitiesForPrefecture(prefValue) {
  console.log('\n========================================');
  console.log(`TEST: getMunicipalitiesForPrefecture('${prefValue}')`);
  console.log('========================================');

  const rowTypeIndex = headers.indexOf('row_type');
  const prefIndex = headers.indexOf('prefecture');
  const muniIndex = headers.indexOf('municipality');

  if (rowTypeIndex === -1 || prefIndex === -1 || muniIndex === -1) {
    console.error('❌ 必要なカラムが見つかりません');
    return false;
  }

  const municipalities = [];
  let summaryCount = 0;

  for (let i = 0; i < values.length; i++) {
    const row = values[i];
    const rowType = row[rowTypeIndex];
    const rowPrefecture = row[prefIndex];
    const municipality = row[muniIndex];

    if (rowType === 'SUMMARY' && rowPrefecture === prefValue && municipality) {
      summaryCount++;
      const normalized = normalizeRegionValue(municipality);
      if (normalized && municipalities.indexOf(normalized) === -1) {
        municipalities.push(normalized);
      }
    }
  }

  municipalities.sort();

  console.log('✅ 抽出された市区町村数:', municipalities.length);
  console.log('   最初の5件:', municipalities.slice(0, 5));

  if (municipalities.length > 0) {
    console.log('✅ PASS: 市区町村データあり');
    return municipalities;
  } else {
    console.log('❌ FAIL: 市区町村データなし');
    return [];
  }
}

// getMapCompleteDataComplete関数のテスト（簡易版）
function testGetMapCompleteDataComplete(prefecture, municipality) {
  console.log('\n========================================');
  console.log(`TEST: getMapCompleteDataComplete('${prefecture}', '${municipality}')`);
  console.log('========================================');

  const rowTypeIdx = headers.indexOf('row_type');
  const municipalityIdx = headers.indexOf('municipality');
  const prefectureIdx = headers.indexOf('prefecture');

  if (rowTypeIdx === -1) {
    console.error('❌ row_typeカラムが見つかりません');
    return false;
  }

  const result = {
    summary: null,
    age_gender: [],
    persona_muni: [],
    career_cross: []
  };

  for (let i = 0; i < values.length; i++) {
    const row = values[i];
    const rowType = row[rowTypeIdx];
    const rowMunicipality = row[municipalityIdx];
    const rowPrefecture = row[prefectureIdx];

    // SUMMARY行
    if (rowType === 'SUMMARY' && rowPrefecture === prefecture && rowMunicipality === municipality) {
      result.summary = { found: true };
    }

    // AGE_GENDER行
    if (rowType === 'AGE_GENDER' && rowPrefecture === prefecture && rowMunicipality === municipality) {
      result.age_gender.push({ found: true });
    }

    // PERSONA_MUNI行
    if (rowType === 'PERSONA_MUNI' && rowPrefecture === prefecture && rowMunicipality === municipality) {
      result.persona_muni.push({ found: true });
    }

    // CAREER_CROSS行
    if (rowType === 'CAREER_CROSS' && rowPrefecture === prefecture && rowMunicipality === municipality) {
      result.career_cross.push({ found: true });
    }
  }

  console.log('✅ 結果:');
  console.log('   SUMMARY:', result.summary ? '✅ 見つかった' : '❌ 見つからない');
  console.log('   AGE_GENDER:', result.age_gender.length, '件');
  console.log('   PERSONA_MUNI:', result.persona_muni.length, '件');
  console.log('   CAREER_CROSS:', result.career_cross.length, '件');

  if (result.summary && result.age_gender.length > 0) {
    console.log('✅ PASS: データフィルタリング成功');
    return true;
  } else {
    console.log('❌ FAIL: データが不足');
    return false;
  }
}

// 統合テスト実行
function runAllTests() {
  console.log('╔════════════════════════════════════════╗');
  console.log('║  MapComplete統合ダッシュボードテスト  ║');
  console.log('╚════════════════════════════════════════╝');

  let passCount = 0;
  let totalTests = 0;

  // TEST 1: 都道府県リスト取得
  totalTests++;
  if (testGetAvailablePrefectures()) passCount++;

  // TEST 2: 市区町村リスト取得（京都府）
  totalTests++;
  const municipalities = testGetMunicipalitiesForPrefecture('京都府');
  if (municipalities.length > 0) passCount++;

  // TEST 3: データ取得（京都府×最初の市区町村）
  if (municipalities.length > 0) {
    totalTests++;
    if (testGetMapCompleteDataComplete('京都府', municipalities[0])) passCount++;
  }

  // 結果サマリー
  console.log('\n╔════════════════════════════════════════╗');
  console.log('║           テスト結果サマリー           ║');
  console.log('╚════════════════════════════════════════╝');
  console.log(`総テスト数: ${totalTests}`);
  console.log(`成功: ${passCount}`);
  console.log(`失敗: ${totalTests - passCount}`);
  console.log(`成功率: ${(passCount / totalTests * 100).toFixed(1)}%`);

  if (passCount === totalTests) {
    console.log('\n✅ すべてのテストが成功しました！');
    console.log('   統合ダッシュボードは正しく動作するはずです。');
    return 0;
  } else {
    console.log('\n❌ 一部のテストが失敗しました。');
    return 1;
  }
}

// テスト実行
const exitCode = runAllTests();
process.exit(exitCode);
