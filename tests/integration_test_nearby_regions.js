/**
 * 統合テスト: 近隣地域表示機能（GAS ⇄ HTML）
 *
 * テスト仕様書準拠:
 * - 複数コンポーネントの相互連携を確認
 * - モジュール間のデータ受け渡しを検証
 * - フローTOP → nearby_regions → マーカー表示の統合
 */

// ========================================
// モックデータ（実データに近い構造）
// ========================================

const mockPhase6FlowData = {
  region: {
    prefecture: '大阪府',
    municipality: '大阪市北区',
    key: 'osaka-kita'
  },
  summary: {
    totalInflow: 1256,
    totalOutflow: 1098,
    netFlow: 158,
    inflowRecords: 25,
    outflowRecords: 22
  },
  tables: {
    topInflows: [
      { origin_pref: '大阪府', origin_muni: '豊中市', flow_count: 186, avg_age: 48.6 },
      { origin_pref: '大阪府', origin_muni: '吹田市', flow_count: 142, avg_age: 47.2 },
      { origin_pref: '大阪府', origin_muni: '茨木市', flow_count: 128, avg_age: 46.8 },
      { origin_pref: '大阪府', origin_muni: '高槻市', flow_count: 98, avg_age: 49.1 },
      { origin_pref: '京都府', origin_muni: '京都市伏見区', flow_count: 76, avg_age: 50.3 }
    ],
    topOutflows: [
      { destination_pref: '大阪府', destination_muni: '大阪市中央区', flow_count: 162, avg_age: 49.4 },
      { destination_pref: '大阪府', destination_muni: '大阪市西区', flow_count: 142, avg_age: 47.3 },
      { destination_pref: '大阪府', destination_muni: '大阪市福島区', flow_count: 108, avg_age: 48.2 },
      { destination_pref: '大阪府', destination_muni: '大阪市淀川区', flow_count: 95, avg_age: 46.9 }
    ]
  }
};

const mockMapMetrics = [
  { prefecture: '大阪府', municipality: '豊中市', lat: 34.7816, lng: 135.4695 },
  { prefecture: '大阪府', municipality: '吹田市', lat: 34.7615, lng: 135.5155 },
  { prefecture: '大阪府', municipality: '茨木市', lat: 34.8164, lng: 135.5683 },
  { prefecture: '大阪府', municipality: '高槻市', lat: 34.8477, lng: 135.6176 },
  { prefecture: '京都府', municipality: '京都市伏見区', lat: 34.935, lng: 135.76 },
  { prefecture: '大阪府', municipality: '大阪市中央区', lat: 34.6851, lng: 135.5207 },
  { prefecture: '大阪府', municipality: '大阪市西区', lat: 34.6781, lng: 135.4867 },
  { prefecture: '大阪府', municipality: '大阪市福島区', lat: 34.6952, lng: 135.4822 },
  { prefecture: '大阪府', municipality: '大阪市淀川区', lat: 34.7172, lng: 135.4821 },
  { prefecture: '大阪府', municipality: '大阪市北区', lat: 34.7024, lng: 135.5023 }
];

// ========================================
// ヘルパー関数
// ========================================

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
  return mockMapMetrics;
}

// ========================================
// GAS側の関数（buildNearbyRegions_）
// ========================================

function buildNearbyRegions_(topInflows, topOutflows, limit) {
  var nearbyRegions = [];
  var mapMetrics = readFirstAvailableSheet(['Phase1_MapMetrics', 'MapMetrics']);

  if (!mapMetrics || mapMetrics.length === 0) {
    return nearbyRegions;
  }

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

  var outflowsToAdd = topOutflows.slice(0, limit);
  outflowsToAdd.forEach(function(record) {
    var destPref = sanitizeString_(getField_(record, ['destination_pref', 'destination_prefecture']));
    var destMuni = sanitizeString_(getField_(record, ['destination_muni', 'destination_municipality']));

    if (destPref && destMuni) {
      var key = buildRegionKey(destPref, destMuni);
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
// HTML側のロジック（マーカー生成）
// ========================================

function generateMarkerData(cityData) {
  const markers = [];

  // 選択中の地域のマーカー
  if (cityData && cityData.center && Array.isArray(cityData.center) && cityData.center.length >= 2) {
    markers.push({
      lat: cityData.center[0],
      lng: cityData.center[1],
      type: 'current',
      name: cityData.name || '選択中',
      color: '#ef4444',
      radius: 11
    });
  }

  // 近隣地域のマーカー
  const nearbyRegions = cityData?.flow?.nearby_regions || [];
  nearbyRegions.forEach((region) => {
    if (!region || !region.lat || !region.lng) {
      return;
    }

    markers.push({
      lat: region.lat,
      lng: region.lng,
      type: region.type,
      name: `${region.prefecture} ${region.municipality}`,
      color: region.type === 'inflow' ? '#3b82f6' : '#f97316',
      radius: 8,
      flow_count: region.flow_count,
      prefecture: region.prefecture,
      municipality: region.municipality
    });
  });

  return markers;
}

// ========================================
// 統合テストケース
// ========================================

console.log('='.repeat(60));
console.log('統合テスト: 近隣地域表示機能（GAS ⇄ HTML）');
console.log('='.repeat(60));
console.log();

let testsPassed = 0;
let testsFailed = 0;

// Test 1: GAS側データ生成 → HTML側データ構造の統合
console.log('[Test 1] データフロー統合: GAS → HTML');
try {
  // Step 1: GAS側でnearby_regionsを生成
  const nearbyRegions = buildNearbyRegions_(
    mockPhase6FlowData.tables.topInflows,
    mockPhase6FlowData.tables.topOutflows,
    5
  );

  // Step 2: HTML側で受け取るデータ構造を模擬
  const cityData = {
    id: 'osaka-kita',
    name: '大阪府 大阪市北区',
    center: [34.7024, 135.5023],
    flow: {
      summary: mockPhase6FlowData.summary,
      nearby_regions: nearbyRegions
    }
  };

  // Step 3: HTML側でマーカーデータを生成
  const markers = generateMarkerData(cityData);

  // 検証1: マーカー数が正しいこと（選択中1 + 近隣地域）
  const expectedMarkers = 1 + nearbyRegions.length;
  if (markers.length !== expectedMarkers) {
    throw new Error(`期待: ${expectedMarkers}マーカー, 実際: ${markers.length}マーカー`);
  }

  // 検証2: 選択中マーカーが含まれていること
  const currentMarker = markers.find(m => m.type === 'current');
  if (!currentMarker) {
    throw new Error('選択中マーカーが見つかりません');
  }

  // 検証3: 流入マーカーが存在すること
  const inflowMarkers = markers.filter(m => m.type === 'inflow');
  if (inflowMarkers.length === 0) {
    throw new Error('流入マーカーが見つかりません');
  }

  // 検証4: 流出マーカーが存在すること
  const outflowMarkers = markers.filter(m => m.type === 'outflow');
  if (outflowMarkers.length === 0) {
    throw new Error('流出マーカーが見つかりません');
  }

  // 検証5: すべてのマーカーに必要な情報が含まれていること
  const hasAllFields = markers.every(m => m.lat && m.lng && m.color && m.radius);
  if (!hasAllFields) {
    throw new Error('一部のマーカーに必要な情報が不足しています');
  }

  console.log('  ✅ PASS');
  console.log(`  - 総マーカー数: ${markers.length}`);
  console.log(`  - 選択中: 1, 流入: ${inflowMarkers.length}, 流出: ${outflowMarkers.length}`);
  testsPassed++;
} catch (e) {
  console.log(`  ❌ FAIL: ${e.message}`);
  testsFailed++;
}
console.log();

// Test 2: フロー数の整合性確認
console.log('[Test 2] フロー数の整合性確認（GAS → HTML）');
try {
  const nearbyRegions = buildNearbyRegions_(
    mockPhase6FlowData.tables.topInflows,
    mockPhase6FlowData.tables.topOutflows,
    5
  );

  const cityData = {
    center: [34.7024, 135.5023],
    flow: { nearby_regions: nearbyRegions }
  };

  const markers = generateMarkerData(cityData);

  // 検証: 豊中市のflow_countが正しく伝播しているか
  const toyonakaMarker = markers.find(m => m.name && m.name.includes('豊中市'));
  if (!toyonakaMarker) {
    throw new Error('豊中市のマーカーが見つかりません');
  }

  const expectedFlowCount = mockPhase6FlowData.tables.topInflows[0].flow_count;
  if (toyonakaMarker.flow_count !== expectedFlowCount) {
    throw new Error(`期待: flow_count=${expectedFlowCount}, 実際: flow_count=${toyonakaMarker.flow_count}`);
  }

  console.log('  ✅ PASS');
  console.log(`  - 豊中市のflow_count: ${toyonakaMarker.flow_count}人`);
  testsPassed++;
} catch (e) {
  console.log(`  ❌ FAIL: ${e.message}`);
  testsFailed++;
}
console.log();

// Test 3: 色分けロジックの統合確認
console.log('[Test 3] 色分けロジック（type → color）');
try {
  const nearbyRegions = buildNearbyRegions_(
    mockPhase6FlowData.tables.topInflows,
    mockPhase6FlowData.tables.topOutflows,
    3
  );

  const cityData = {
    center: [34.7024, 135.5023],
    flow: { nearby_regions: nearbyRegions }
  };

  const markers = generateMarkerData(cityData);

  // 検証1: 流入マーカーが青色であること
  const inflowMarkers = markers.filter(m => m.type === 'inflow');
  const allInflowsBlue = inflowMarkers.every(m => m.color === '#3b82f6');
  if (!allInflowsBlue) {
    throw new Error('流入マーカーの色が正しくありません（期待: #3b82f6）');
  }

  // 検証2: 流出マーカーがオレンジ色であること
  const outflowMarkers = markers.filter(m => m.type === 'outflow');
  const allOutflowsOrange = outflowMarkers.every(m => m.color === '#f97316');
  if (!allOutflowsOrange) {
    throw new Error('流出マーカーの色が正しくありません（期待: #f97316）');
  }

  // 検証3: 選択中マーカーが赤色であること
  const currentMarker = markers.find(m => m.type === 'current');
  if (currentMarker.color !== '#ef4444') {
    throw new Error(`選択中マーカーの色が正しくありません（期待: #ef4444, 実際: ${currentMarker.color}）`);
  }

  console.log('  ✅ PASS');
  console.log(`  - 流入: 青(#3b82f6), 流出: オレンジ(#f97316), 選択中: 赤(#ef4444)`);
  testsPassed++;
} catch (e) {
  console.log(`  ❌ FAIL: ${e.message}`);
  testsFailed++;
}
console.log();

// Test 4: 座標データの正確性確認
console.log('[Test 4] 座標データの正確性確認');
try {
  const nearbyRegions = buildNearbyRegions_(
    mockPhase6FlowData.tables.topInflows,
    mockPhase6FlowData.tables.topOutflows,
    2
  );

  // 検証: buildNearbyRegions_が返した座標が、元のMapMetricsと一致すること
  const toyonaka = nearbyRegions.find(r => r.municipality === '豊中市');
  if (!toyonaka) {
    throw new Error('豊中市のデータが見つかりません');
  }

  const expectedCoords = mockMapMetrics.find(m => m.municipality === '豊中市');
  if (toyonaka.lat !== expectedCoords.lat || toyonaka.lng !== expectedCoords.lng) {
    throw new Error(`座標が一致しません（期待: [${expectedCoords.lat}, ${expectedCoords.lng}], 実際: [${toyonaka.lat}, ${toyonaka.lng}]）`);
  }

  console.log('  ✅ PASS');
  console.log(`  - 豊中市の座標: [${toyonaka.lat}, ${toyonaka.lng}]`);
  testsPassed++;
} catch (e) {
  console.log(`  ❌ FAIL: ${e.message}`);
  testsFailed++;
}
console.log();

// Test 5: エンドツーエンドのデータ完全性
console.log('[Test 5] エンドツーエンドのデータ完全性');
try {
  // フルフロー: Phase6データ → nearby_regions → マーカー
  const nearbyRegions = buildNearbyRegions_(
    mockPhase6FlowData.tables.topInflows,
    mockPhase6FlowData.tables.topOutflows,
    5
  );

  const fullCityData = {
    id: 'osaka-kita',
    name: '大阪府 大阪市北区',
    center: [34.7024, 135.5023],
    region: mockPhase6FlowData.region,
    flow: {
      summary: mockPhase6FlowData.summary,
      top_inflows: mockPhase6FlowData.tables.topInflows,
      top_outflows: mockPhase6FlowData.tables.topOutflows,
      nearby_regions: nearbyRegions
    }
  };

  const markers = generateMarkerData(fullCityData);

  // 検証: すべてのマーカーがクリック可能な情報を持っていること
  const clickableMarkers = markers.filter(m => m.prefecture && m.municipality);
  const expectedClickable = nearbyRegions.length; // 近隣地域のみクリック可能

  if (clickableMarkers.length !== expectedClickable) {
    throw new Error(`期待: ${expectedClickable}個のクリック可能マーカー, 実際: ${clickableMarkers.length}個`);
  }

  console.log('  ✅ PASS');
  console.log(`  - クリック可能マーカー: ${clickableMarkers.length}個`);
  console.log(`  - データ完全性: 確認済み`);
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
  console.log('✅ すべての統合テストが成功しました！');
  console.log('   GAS ⇄ HTML のデータフローが正常に動作しています。');
} else {
  console.log(`❌ ${testsFailed}件のテストが失敗しました`);
}

console.log('='.repeat(60));
