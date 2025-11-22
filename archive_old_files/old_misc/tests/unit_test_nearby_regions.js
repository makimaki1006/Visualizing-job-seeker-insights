/**
 * ユニットテスト: buildNearbyRegions_()関数
 *
 * テスト仕様書準拠:
 * - 関数単位の正当性確認
 * - 外部依存をモック化
 * - 純粋な入力→出力の検証
 */

// モックデータ
const mockTopInflows = [
  {
    origin_pref: '大阪府',
    origin_muni: '豊中市',
    flow_count: 186
  },
  {
    origin_pref: '大阪府',
    origin_muni: '吹田市',
    flow_count: 142
  },
  {
    origin_pref: '京都府',
    origin_muni: '京都市伏見区',
    flow_count: 98
  }
];

const mockTopOutflows = [
  {
    destination_pref: '大阪府',
    destination_muni: '大阪市中央区',
    flow_count: 162
  },
  {
    destination_pref: '大阪府',
    destination_muni: '大阪市西区',
    flow_count: 142
  },
  {
    destination_pref: '大阪府',
    destination_muni: '大阪市福島区',
    flow_count: 108
  }
];

const mockMapMetrics = [
  { prefecture: '大阪府', municipality: '豊中市', lat: 34.7816, lng: 135.4695 },
  { prefecture: '大阪府', municipality: '吹田市', lat: 34.7615, lng: 135.5155 },
  { prefecture: '京都府', municipality: '京都市伏見区', lat: 34.935, lng: 135.76 },
  { prefecture: '大阪府', municipality: '大阪市中央区', lat: 34.6851, lng: 135.5207 },
  { prefecture: '大阪府', municipality: '大阪市西区', lat: 34.6781, lng: 135.4867 },
  { prefecture: '大阪府', municipality: '大阪市福島区', lat: 34.6952, lng: 135.4822 }
];

// モック関数群
function sanitizeString_(str) {
  return str ? str.trim() : '';
}

function getField_(record, candidates) {
  for (const key of candidates) {
    if (key in record && record[key] !== '') {
      return record[key];
    }
  }
  return null;
}

function parseNumber_(val) {
  const num = parseFloat(val);
  return isNaN(num) ? 0 : num;
}

function buildRegionKey(pref, muni) {
  const prefClean = (pref || '').toLowerCase().replace(/[都道府県]/g, '');
  const muniClean = (muni || '').toLowerCase().replace(/[市区町村]/g, '');
  return `${prefClean}-${muniClean}`;
}

function readFirstAvailableSheet(candidates) {
  // モックデータを返す
  return mockMapMetrics;
}

// テスト対象関数（GASコードから抽出）
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

// ========================================
// テストケース
// ========================================

console.log('='.repeat(60));
console.log('ユニットテスト: buildNearbyRegions_()');
console.log('='.repeat(60));
console.log();

let testsPassed = 0;
let testsFailed = 0;

// Test 1: 正常系 - limit=2で実行
console.log('[Test 1] 正常系 - limit=2');
try {
  const result = buildNearbyRegions_(mockTopInflows, mockTopOutflows, 2);

  // 検証1: 結果配列の長さが4であること（流入2 + 流出2）
  if (result.length !== 4) {
    throw new Error(`期待: 4地域, 実際: ${result.length}地域`);
  }

  // 検証2: 流入地域が2件含まれていること
  const inflowCount = result.filter(r => r.type === 'inflow').length;
  if (inflowCount !== 2) {
    throw new Error(`期待: 流入2件, 実際: 流入${inflowCount}件`);
  }

  // 検証3: 流出地域が2件含まれていること
  const outflowCount = result.filter(r => r.type === 'outflow').length;
  if (outflowCount !== 2) {
    throw new Error(`期待: 流出2件, 実際: 流出${outflowCount}件`);
  }

  // 検証4: すべての地域に座標が含まれていること
  const hasCoords = result.every(r => r.lat && r.lng);
  if (!hasCoords) {
    throw new Error('一部の地域に座標がありません');
  }

  // 検証5: flow_countが正しく設定されていること
  const firstInflow = result.find(r => r.type === 'inflow' && r.municipality === '豊中市');
  if (!firstInflow || firstInflow.flow_count !== 186) {
    throw new Error(`期待: 豊中市のflow_count=186, 実際: ${firstInflow?.flow_count || 'なし'}`);
  }

  console.log('  ✅ PASS');
  console.log(`  - 地域数: ${result.length}`);
  console.log(`  - 流入: ${inflowCount}, 流出: ${outflowCount}`);
  testsPassed++;
} catch (e) {
  console.log(`  ❌ FAIL: ${e.message}`);
  testsFailed++;
}
console.log();

// Test 2: エッジケース - limit=0
console.log('[Test 2] エッジケース - limit=0');
try {
  const result = buildNearbyRegions_(mockTopInflows, mockTopOutflows, 0);

  if (result.length !== 0) {
    throw new Error(`期待: 0地域, 実際: ${result.length}地域`);
  }

  console.log('  ✅ PASS');
  testsPassed++;
} catch (e) {
  console.log(`  ❌ FAIL: ${e.message}`);
  testsFailed++;
}
console.log();

// Test 3: エッジケース - limit > データ数
console.log('[Test 3] エッジケース - limit=10（データ数超過）');
try {
  const result = buildNearbyRegions_(mockTopInflows, mockTopOutflows, 10);

  // データは最大6地域（流入3 + 流出3）
  if (result.length > 6) {
    throw new Error(`期待: 最大6地域, 実際: ${result.length}地域`);
  }

  console.log('  ✅ PASS');
  console.log(`  - 地域数: ${result.length}`);
  testsPassed++;
} catch (e) {
  console.log(`  ❌ FAIL: ${e.message}`);
  testsFailed++;
}
console.log();

// Test 4: 空配列入力
console.log('[Test 4] 空配列入力');
try {
  const result = buildNearbyRegions_([], [], 5);

  if (result.length !== 0) {
    throw new Error(`期待: 0地域, 実際: ${result.length}地域`);
  }

  console.log('  ✅ PASS');
  testsPassed++;
} catch (e) {
  console.log(`  ❌ FAIL: ${e.message}`);
  testsFailed++;
}
console.log();

// Test 5: 重複排除テスト（流入と流出に同じ地域がある場合）
console.log('[Test 5] 重複排除テスト');
try {
  const duplicateOutflows = [
    {
      destination_pref: '大阪府',
      destination_muni: '豊中市', // 流入にもある
      flow_count: 50
    }
  ];

  const result = buildNearbyRegions_(mockTopInflows.slice(0, 1), duplicateOutflows, 5);

  // 豊中市は1回のみ追加されるべき
  const toyonakaCount = result.filter(r => r.municipality === '豊中市').length;
  if (toyonakaCount !== 1) {
    throw new Error(`期待: 豊中市1件, 実際: ${toyonakaCount}件`);
  }

  // typeはinflowであるべき（先に追加された方）
  const toyonaka = result.find(r => r.municipality === '豊中市');
  if (toyonaka.type !== 'inflow') {
    throw new Error(`期待: type='inflow', 実際: type='${toyonaka.type}'`);
  }

  console.log('  ✅ PASS');
  console.log(`  - 重複排除確認: 豊中市は1件のみ`);
  testsPassed++;
} catch (e) {
  console.log(`  ❌ FAIL: ${e.message}`);
  testsFailed++;
}
console.log();

// Test 6: データ構造検証
console.log('[Test 6] データ構造検証');
try {
  const result = buildNearbyRegions_(mockTopInflows, mockTopOutflows, 2);

  const firstRegion = result[0];
  const requiredFields = ['prefecture', 'municipality', 'lat', 'lng', 'key', 'type', 'flow_count'];

  for (const field of requiredFields) {
    if (!(field in firstRegion)) {
      throw new Error(`必須フィールド '${field}' がありません`);
    }
  }

  // 座標の型チェック
  if (typeof firstRegion.lat !== 'number' || typeof firstRegion.lng !== 'number') {
    throw new Error('座標が数値ではありません');
  }

  // typeの値チェック
  if (firstRegion.type !== 'inflow' && firstRegion.type !== 'outflow') {
    throw new Error(`不正なtype値: ${firstRegion.type}`);
  }

  console.log('  ✅ PASS');
  console.log(`  - すべての必須フィールドが存在`);
  testsPassed++;
} catch (e) {
  console.log(`  ❌ FAIL: ${e.message}`);
  testsFailed++;
}
console.log();

// ========================================
// テスト結果サマリー
// ========================================

console.log('='.repeat(60));
console.log('テスト結果サマリー');
console.log('='.repeat(60));
console.log(`総テスト数: ${testsPassed + testsFailed}`);
console.log(`成功: ${testsPassed}`);
console.log(`失敗: ${testsFailed}`);
console.log(`成功率: ${((testsPassed / (testsPassed + testsFailed)) * 100).toFixed(1)}%`);
console.log();

if (testsFailed === 0) {
  console.log('✅ すべてのテストが成功しました！');
} else {
  console.log(`❌ ${testsFailed}件のテストが失敗しました`);
}

console.log('='.repeat(60));
