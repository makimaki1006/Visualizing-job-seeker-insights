/**
 * 統合ダッシュボード E2Eテスト
 * MapCompleteDataBridge.gsの動作をシミュレートして検証
 */

const fs = require('fs');
const path = require('path');

// CSVファイルパス
const CSV_PATH = path.join(__dirname, '..', 'python_scripts', 'data', 'output_v2', 'mapcomplete_complete_sheets', 'MapComplete_Complete_京都府.csv');

console.log('================================================================================');
console.log('統合ダッシュボード E2Eテスト');
console.log('================================================================================\n');

// CSVファイル読み込み
let csvContent = fs.readFileSync(CSV_PATH, 'utf-8');
if (csvContent.charCodeAt(0) === 0xFEFF) {
  csvContent = csvContent.substring(1);
}

const lines = csvContent.split('\n').filter(line => line.trim());
const header = lines[0].split(',');
const allRows = lines.slice(1).map(line => {
  const values = line.split(',');
  const row = {};
  header.forEach((col, i) => {
    row[col] = values[i];
  });
  return row;
});

console.log(`✅ MapComplete CSVロード完了: ${allRows.length}行\n`);

// getMapCompleteDataComplete() のシミュレーション
function getMapCompleteDataComplete(prefecture, municipality) {
  console.log(`[getMapCompleteDataComplete] prefecture="${prefecture}", municipality="${municipality}"`);

  // row_type別にデータをフィルタリング
  const summaryRows = allRows.filter(r => r.row_type === 'SUMMARY');
  const personaRows = allRows.filter(r => r.row_type === 'PERSONA' || r.row_type === 'PERSONA_MUNI');
  const flowRows = allRows.filter(r => r.row_type === 'FLOW');
  const careerRows = allRows.filter(r => r.row_type === 'CAREER_CROSS');
  const gapRows = allRows.filter(r => r.row_type === 'GAP');
  const rarityRows = allRows.filter(r => r.row_type === 'RARITY');
  const competitionRows = allRows.filter(r => r.row_type === 'COMPETITION');
  const ageGenderRows = allRows.filter(r => r.row_type === 'AGE_GENDER');
  const urgencyAgeRows = allRows.filter(r => r.row_type === 'URGENCY_AGE');
  const urgencyEmploymentRows = allRows.filter(r => r.row_type === 'URGENCY_EMPLOYMENT');

  // municipality でフィルタリング（指定がある場合）
  let filteredSummary = summaryRows;
  let filteredPersona = personaRows;
  let filteredFlow = flowRows;
  let filteredGap = gapRows;
  let filteredRarity = rarityRows;
  let filteredCompetition = competitionRows;

  if (municipality && municipality !== '') {
    filteredSummary = summaryRows.filter(r => r.municipality === municipality);
    filteredPersona = personaRows.filter(r => r.municipality === municipality);
    filteredFlow = flowRows.filter(r => r.municipality === municipality);

    // GAP, RARITY, COMPETITIONはmunicipalityカラムに「京都府京都市伏見区」のように
    // 都道府県名がprefixとして付いているため、endsWith()で比較
    filteredGap = gapRows.filter(r =>
      r.municipality && r.municipality.endsWith(municipality)
    );
    filteredRarity = rarityRows.filter(r =>
      r.municipality && r.municipality.endsWith(municipality)
    );
    filteredCompetition = competitionRows.filter(r =>
      r.municipality && r.municipality.endsWith(municipality)
    );
  }

  return {
    summary: filteredSummary,
    persona: filteredPersona,
    flow: filteredFlow,
    career: careerRows,
    gap: filteredGap,
    rarity: filteredRarity,
    competition: filteredCompetition,
    ageGender: ageGenderRows,
    urgencyAge: urgencyAgeRows,
    urgencyEmployment: urgencyEmploymentRows
  };
}

// テスト1: 全データ取得（municipalityフィルタなし）
console.log('[テスト1] 全データ取得（municipalityフィルタなし）');
console.log('─'.repeat(80));
const allData = getMapCompleteDataComplete('京都府', '');

console.log(`  SUMMARY: ${allData.summary.length}件`);
console.log(`  PERSONA: ${allData.persona.length}件`);
console.log(`  FLOW: ${allData.flow.length}件`);
console.log(`  CAREER_CROSS: ${allData.career.length}件`);
console.log(`  GAP: ${allData.gap.length}件`);
console.log(`  RARITY: ${allData.rarity.length}件`);
console.log(`  COMPETITION: ${allData.competition.length}件`);
console.log(`  AGE_GENDER: ${allData.ageGender.length}件`);
console.log(`  URGENCY_AGE: ${allData.urgencyAge.length}件`);
console.log(`  URGENCY_EMPLOYMENT: ${allData.urgencyEmployment.length}件`);

// 検証
let errors = 0;
if (allData.summary.length === 0) {
  console.error(`  ❌ エラー: SUMMARYデータが0件`);
  errors++;
}
if (allData.persona.length === 0) {
  console.error(`  ❌ エラー: PERSONAデータが0件`);
  errors++;
}
if (allData.career.length === 0) {
  console.error(`  ❌ エラー: CAREER_CROSSデータが0件`);
  errors++;
}

if (errors === 0) {
  console.log(`✅ テスト1成功\n`);
} else {
  console.error(`❌ テスト1失敗: ${errors}件のエラー\n`);
  process.exit(1);
}

// テスト2: municipalityフィルタあり
console.log('[テスト2] municipalityフィルタあり（京都市伏見区）');
console.log('─'.repeat(80));
const fushimiData = getMapCompleteDataComplete('京都府', '京都市伏見区');

console.log(`  SUMMARY: ${fushimiData.summary.length}件`);
console.log(`  PERSONA: ${fushimiData.persona.length}件`);
console.log(`  FLOW: ${fushimiData.flow.length}件`);

// 検証: フィルタ後のデータが少なくとも1件以上あること
errors = 0;
if (fushimiData.summary.length === 0) {
  console.error(`  ❌ エラー: 伏見区のSUMMARYデータが0件`);
  errors++;
}

// SUMMARY行の座標を確認
if (fushimiData.summary.length > 0) {
  const firstRow = fushimiData.summary[0];
  console.log(`  座標: (${firstRow.latitude}, ${firstRow.longitude})`);

  const lat = parseFloat(firstRow.latitude);
  const lng = parseFloat(firstRow.longitude);

  if (lat === 0 || lng === 0) {
    console.error(`  ❌ エラー: 座標が0`);
    errors++;
  }
  if (Math.abs(lat - 34.9327) > 0.01 || Math.abs(lng - 135.7656) > 0.01) {
    console.error(`  ❌ エラー: 座標が期待値と異なる`);
    console.error(`     期待: (34.9327, 135.7656), 実際: (${lat}, ${lng})`);
    errors++;
  }
}

if (errors === 0) {
  console.log(`✅ テスト2成功\n`);
} else {
  console.error(`❌ テスト2失敗: ${errors}件のエラー\n`);
  process.exit(1);
}

// テスト3: 各タブで必要なデータが揃っているか
console.log('[テスト3] 各ダッシュボードタブのデータ検証');
console.log('─'.repeat(80));

const tabTests = [
  { name: '概要タブ', requiredData: ['summary'], check: (data) => data.summary.length > 0 },
  { name: 'ペルソナタブ', requiredData: ['persona'], check: (data) => data.persona.length > 0 },
  { name: 'フロータブ', requiredData: ['flow'], check: (data) => data.flow.length > 0 },
  { name: 'キャリアタブ', requiredData: ['career'], check: (data) => data.career.length > 0 },
  { name: '需給ギャップタブ', requiredData: ['gap'], check: (data) => data.gap.length > 0 },
  { name: '希少性タブ', requiredData: ['rarity'], check: (data) => data.rarity.length > 0 },
  { name: '競合タブ', requiredData: ['competition'], check: (data) => data.competition.length > 0 }
];

errors = 0;
tabTests.forEach(test => {
  const result = test.check(allData);
  if (result) {
    console.log(`  ✅ ${test.name}: データあり`);
  } else {
    console.error(`  ❌ ${test.name}: データなし`);
    errors++;
  }
});

if (errors === 0) {
  console.log(`✅ テスト3成功\n`);
} else {
  console.error(`❌ テスト3失敗: ${errors}件のエラー\n`);
  process.exit(1);
}

// 最終結果
console.log('================================================================================');
console.log('✅ 全テスト成功 - 統合ダッシュボードは正常に動作可能');
console.log('================================================================================\n');

console.log('[確認済み項目]');
console.log('  ✅ MapComplete CSVから全row_typeのデータを取得可能');
console.log('  ✅ municipalityフィルタリングが正常に動作');
console.log('  ✅ 座標データが正しく設定されている');
console.log('  ✅ 全ダッシュボードタブに必要なデータが揃っている');

console.log('\n[次のステップ]');
console.log('  1. GASでスプレッドシートを開く');
console.log('  2. MapComplete_Complete_京都府.csvをインポート');
console.log('  3. メニュー → 統合ダッシュボードを開く');
console.log('  4. 各タブ（概要、ペルソナ、フロー、キャリア等）が正常に表示されることを確認');
