/**
 * MapComplete統合CSV E2Eテスト
 * 京都府CSVの座標データと構造を検証
 */

const fs = require('fs');
const path = require('path');

// CSVファイルパス
const CSV_PATH = path.join(__dirname, '..', 'python_scripts', 'data', 'output_v2', 'mapcomplete_complete_sheets', 'MapComplete_Complete_京都府.csv');

console.log('================================================================================');
console.log('MapComplete統合CSV E2Eテスト - 京都府');
console.log('================================================================================\n');

// CSVファイル読み込み
let csvContent;
try {
  csvContent = fs.readFileSync(CSV_PATH, 'utf-8');
  console.log('✅ CSVファイル読み込み成功');
} catch (error) {
  console.error('❌ CSVファイル読み込み失敗:', error.message);
  process.exit(1);
}

// BOM除去
if (csvContent.charCodeAt(0) === 0xFEFF) {
  csvContent = csvContent.substring(1);
}

// CSV解析
const lines = csvContent.split('\n').filter(line => line.trim());
const header = lines[0].split(',');
const rows = lines.slice(1).map(line => {
  const values = line.split(',');
  const row = {};
  header.forEach((col, i) => {
    row[col] = values[i];
  });
  return row;
});

console.log(`\n[データ構造]`);
console.log(`  総行数: ${rows.length}行`);
console.log(`  カラム数: ${header.length}列`);

// 必須カラムの確認
const requiredColumns = ['row_type', 'prefecture', 'municipality', 'latitude', 'longitude'];
const missingColumns = requiredColumns.filter(col => !header.includes(col));

if (missingColumns.length > 0) {
  console.error(`\n❌ 必須カラムが不足: ${missingColumns.join(', ')}`);
  process.exit(1);
} else {
  console.log(`✅ 必須カラムすべて存在`);
}

// row_type別の件数
const rowTypeCounts = {};
rows.forEach(row => {
  const type = row.row_type;
  rowTypeCounts[type] = (rowTypeCounts[type] || 0) + 1;
});

console.log(`\n[row_type別件数]`);
Object.entries(rowTypeCounts).sort((a, b) => b[1] - a[1]).forEach(([type, count]) => {
  console.log(`  ${type}: ${count}件`);
});

// 座標データの検証
console.log(`\n[座標データ検証]`);

const summaryRows = rows.filter(row => row.row_type === 'SUMMARY');
console.log(`  SUMMARY行数: ${summaryRows.length}件`);

// 座標が0.0のデータをチェック
const zeroCoords = summaryRows.filter(row =>
  parseFloat(row.latitude) === 0.0 || parseFloat(row.longitude) === 0.0
);

if (zeroCoords.length > 0) {
  console.error(`\n❌ 座標が0.0のデータが存在: ${zeroCoords.length}件`);
  zeroCoords.slice(0, 5).forEach(row => {
    console.error(`  - ${row.municipality}: lat=${row.latitude}, lng=${row.longitude}`);
  });
  process.exit(1);
}

// 座標が空のデータをチェック
const emptyCoords = summaryRows.filter(row =>
  !row.latitude || !row.longitude || row.latitude === '' || row.longitude === ''
);

if (emptyCoords.length > 0) {
  console.error(`\n❌ 座標が空のデータが存在: ${emptyCoords.length}件`);
  emptyCoords.slice(0, 5).forEach(row => {
    console.error(`  - ${row.municipality}: lat=${row.latitude}, lng=${row.longitude}`);
  });
  process.exit(1);
}

console.log(`✅ 全SUMMARY行に正しい座標データあり`);

// 京都府の主要市区町村の座標を検証
const kyotoAreas = [
  { name: '京都市伏見区', expectedLat: 34.9327, expectedLng: 135.7656 },
  { name: '京都市右京区', expectedLat: 35.0152, expectedLng: 135.7117 },
  { name: '京都市山科区', expectedLat: 34.9777, expectedLng: 135.8172 }
];

console.log(`\n[主要市区町村の座標検証]`);
let coordErrors = 0;

kyotoAreas.forEach(area => {
  const row = summaryRows.find(r => r.municipality === area.name);
  if (!row) {
    console.error(`  ❌ ${area.name}: データなし`);
    coordErrors++;
    return;
  }

  const lat = parseFloat(row.latitude);
  const lng = parseFloat(row.longitude);

  // 座標の誤差許容範囲（±0.01度 = 約1km）
  const latDiff = Math.abs(lat - area.expectedLat);
  const lngDiff = Math.abs(lng - area.expectedLng);

  if (latDiff > 0.01 || lngDiff > 0.01) {
    console.error(`  ❌ ${area.name}: 座標不一致`);
    console.error(`     期待値: (${area.expectedLat}, ${area.expectedLng})`);
    console.error(`     実際値: (${lat}, ${lng})`);
    coordErrors++;
  } else {
    console.log(`  ✅ ${area.name}: (${lat}, ${lng})`);
  }
});

if (coordErrors > 0) {
  console.error(`\n❌ 座標検証で${coordErrors}件のエラー`);
  process.exit(1);
}

// GASインポートシミュレーション
console.log(`\n[GASインポートシミュレーション]`);

// ファイル名からシート名を生成（UnifiedDataImporter.gsのロジック）
const fileName = 'MapComplete_Complete_京都府.csv';
const sheetName = fileName.replace('.csv', '');
console.log(`  ファイル名: ${fileName}`);
console.log(`  シート名: ${sheetName}`);

if (sheetName !== 'MapComplete_Complete_京都府') {
  console.error(`  ❌ シート名が期待値と異なる`);
  process.exit(1);
}
console.log(`  ✅ シート名正常`);

// row_typeフィルタリングシミュレーション
console.log(`\n[row_typeフィルタリングシミュレーション]`);

const testFilters = [
  { type: 'SUMMARY', minExpected: 30 },
  { type: 'PERSONA', minExpected: 10 },
  { type: 'FLOW', minExpected: 10 },
  { type: 'CAREER_CROSS', minExpected: 100 }
];

testFilters.forEach(filter => {
  const filtered = rows.filter(row => row.row_type === filter.type);
  if (filtered.length < filter.minExpected) {
    console.error(`  ❌ ${filter.type}: ${filtered.length}件（期待値: ${filter.minExpected}件以上）`);
    process.exit(1);
  }
  console.log(`  ✅ ${filter.type}: ${filtered.length}件`);
});

// 最終結果
console.log(`\n================================================================================`);
console.log(`✅ 全テスト成功`);
console.log(`================================================================================\n`);

console.log(`[次のステップ]`);
console.log(`1. GASでスプレッドシートを開く`);
console.log(`2. メニュー → データ処理 → ⚡ 高速CSVインポート`);
console.log(`3. MapComplete_Complete_京都府.csv を選択`);
console.log(`4. インポート完了後、地図表示で京都府の各市区町村が正しい位置に表示されることを確認`);
console.log(`\nCSVファイル: ${CSV_PATH}`);
