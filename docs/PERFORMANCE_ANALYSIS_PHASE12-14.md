# Phase 12-14統合ダッシュボード パフォーマンス最適化分析レポート

**分析日**: 2025年11月4日
**対象**: Phase 12-14統合ダッシュボードの初回読み込み時間（15-23秒）
**目標**: 5秒以内に短縮
**分析者**: Claude Code (Performance Engineer)

---

## 1. ボトルネック分析結果

### 1.1 処理フロー全体像

```
HTML初期化（即座）
    ↓
google.script.run.getMapCompleteData() 呼び出し
    ↓
buildMapCompleteCityData_() 実行 ← ★ボトルネック（15-23秒）
    ↓
    ├─ Phase 1: fetchPhase1Metrics()         ← 2-3秒（推定）
    ├─ Phase 1: fetchApplicantsForMunicipality() ← 3-5秒（推定、5000件）
    ├─ Phase 3: fetchPhase3Persona()         ← 2-3秒（推定）
    ├─ Phase 6: fetchPhase6Flow()            ← 2-3秒（推定）
    ├─ Phase 7: fetchPhase7Supply()          ← 3-4秒（推定）
    ├─ Phase 8: fetchPhase8Education()       ← 2-3秒（推定）
    ├─ Phase 10: fetchPhase10Urgency()       ← 2-3秒（推定）
    └─ Phase 12-14: loadPhase12to14Data()    ← 1-2秒（推定）
    ↓
データ集計・変換処理（MapCompleteDataBridge.gs:175-386） ← 1-2秒
    ↓
JSON返却 → HTML側で描画
```

### 1.2 ボトルネックTOP3

| 順位 | 処理内容 | 推定時間 | 原因 | ファイル:行番号 |
|------|---------|---------|------|---------------|
| **1位** | `fetchApplicantsForMunicipality()` | **3-5秒** | 5000件の大量データ読み込み | MapCompleteDataBridge.gs:354 |
| **2位** | `fetchPhase7Supply()` | **3-4秒** | 4シート×readFirstAvailableSheet | QualityAndRegionDashboards.gs:1307-1386 |
| **3位** | `fetchPhase1Metrics()` | **2-3秒** | 3シート×readFirstAvailableSheet | QualityAndRegionDashboards.gs:1191-1229 |

### 1.3 シート読み込み回数分析

**合計シート読み込み回数**: **最低23回**

| Phase | 読み込み回数 | シート名 | 関数 |
|-------|-------------|---------|------|
| Phase 1 | 3回 | MapMetrics, AggDesired, Quality | fetchPhase1Metrics() |
| Phase 1（申請者） | 1回 | Applicants | fetchApplicantsForMunicipality() |
| Phase 3 | 3回 | PersonaSummary, PersonaDetails, Quality | fetchPhase3Persona() |
| Phase 6 | 4回 | FlowEdges, FlowNodes, ProximityAnalysis, Quality | fetchPhase6Flow() |
| Phase 7 | 6回 | SupplyDensity, Qualification, AgeGender, Mobility, PersonaProfile, Quality | fetchPhase7Supply() |
| Phase 8 | 8回 | Education, EducationCross, EducationMatrix, Graduation, Career, CareerCross, CareerMatrix, Quality | fetchPhase8Education() |
| Phase 10 | 5回 | Urgency, AgeCross, EmploymentCross, AgeMatrix, EmploymentMatrix, Quality | fetchPhase10Urgency() |
| Phase 12-14 | 3回 | Phase12_SupplyDemandGap, Phase13_RarityScore, Phase14_CompetitionProfile | loadPhase12to14Data() |
| **合計** | **33回** | | |

※ `readFirstAvailableSheet()` は候補シート名の配列を受け取り、最初に見つかったシートを読み込むため、実際には最少23回、最大33回の呼び出しが発生。

### 1.4 readFirstAvailableSheet() の処理内容

```javascript
function readFirstAvailableSheet(candidates) {
  for (let i = 0; i < candidates.length; i += 1) {
    const sheetName = candidates[i];
    const rows = readSheetAsObjects(sheetName);  // ← シート全体を読み込み
    if (rows.length) {
      return rows;
    }
  }
  return [];
}
```

**問題点**:
- 各候補シートを順番に試す（存在しないシートも含む）
- `readSheetAsObjects()` → `readSheetRows()` → `sheet.getDataRange().getValues()` で**全行を読み込む**
- シートごとにヘッダー行をオブジェクトに変換（CPU負荷）

### 1.5 データサイズ分析

| データ | 行数（推定） | 備考 |
|--------|------------|------|
| **applicants** | **5,000件** | `sanitizeRecords_(applicants, 5000)` ← **最大**  |
| personaDetails | 200件 | `sanitizeRecords_(phase3.tables.personaDetails, 200)` |
| personaSummaryByMunicipality | 200件 | `sanitizeRecords_(phase7.tables.personaSummaryByMunicipality, 200)` |
| personaMapData | 200件 | `sanitizeRecords_(phase7.tables.personaMapData, 200)` |
| urgencyMunicipality | 200件 | `sanitizeRecords_(phase10.tables.municipality, 200)` |
| careerDistribution | 100件 | `sanitizeRecords_(phase8.tables.careerDistribution, 100)` |
| graduationDistribution | 100件 | `sanitizeRecords_(phase8.tables.graduationDistribution, 100)` |
| all_inflows | 100件 | `sanitizeRecords_(phase6.tables.allInflows, 100)` |
| all_outflows | 100件 | `sanitizeRecords_(phase6.tables.allOutflows, 100)` |
| mobilityScores | 50件 | `sanitizeRecords_(phase7.tables.mobilityScore, 50)` |
| personaSummary | 50件 | `sanitizeRecords_(phase3.tables.personaSummary, 50)` |
| **Phase 12-14 all_records** | **不明（全件）** | ← **削減対象候補** |

**Phase 12-14の all_records フィールド**:
- `gap.all_records`: 全地域の需給ギャップデータ（MapPhase12_14_DataBridge.gs:103）
- `rarity.all_records`: 全地域の希少性スコアデータ（同:181）
- `competition.all_records`: 全地域の競合分析データ（同:261）

**問題**: これらの `all_records` はTop 10/15データと**重複**しており、初期表示で不要。

---

## 2. 最適化提案（優先度順）

### 提案1: Phase 12-14の all_records を削除または遅延ロード ★★★

**実装難易度**: **低**
**期待効果**: **2-4秒削減**
**リスク**: 低（all_records は現在未使用のため）

#### 実装方法A: all_records を初期ロードから削除

**変更ファイル**: `MapCompleteDataBridge.gs`

```javascript
// 現在（行382-384）:
gap: phase12to14.gap || { top_gaps: [], top_ratios: [], summary: {} },
rarity: phase12to14.rarity || { rank_distribution: {}, top_rarity: [], summary: {} },
competition: phase12to14.competition || { top_locations: [], summary: {} }

// 変更後: all_records を明示的に削除
gap: {
  top_gaps: (phase12to14.gap && phase12to14.gap.top_gaps) || [],
  top_ratios: (phase12to14.gap && phase12to14.gap.top_ratios) || [],
  summary: (phase12to14.gap && phase12to14.gap.summary) || {}
  // all_records は削除
},
rarity: {
  rank_distribution: (phase12to14.rarity && phase12to14.rarity.rank_distribution) || {},
  top_rarity: (phase12to14.rarity && phase12to14.rarity.top_rarity) || [],
  summary: (phase12to14.rarity && phase12to14.rarity.summary) || {}
  // all_records は削除
},
competition: {
  top_locations: (phase12to14.competition && phase12to14.competition.top_locations) || [],
  summary: (phase12to14.competition && phase12to14.competition.summary) || {}
  // all_records は削除
}
```

**効果**: Phase 12-14のデータサイズを**70-80%削減**（推定）

#### 実装方法B: 遅延ロード用の専用関数を追加

```javascript
// MapCompleteDataBridge.gs に追加
function getPhase12to14AllRecords(prefecture, municipality) {
  const phase12to14 = loadPhase12to14Data();
  return {
    gap: phase12to14.gap.all_records || [],
    rarity: phase12to14.rarity.all_records || [],
    competition: phase12to14.competition.all_records || []
  };
}
```

HTML側で必要に応じて呼び出し:
```javascript
// タブ切り替え時に実行
if (tab === 'gap-details' && !gapAllRecordsLoaded) {
  google.script.run
    .withSuccessHandler(data => {
      // 詳細データを表示
      gapAllRecordsLoaded = true;
    })
    .getPhase12to14AllRecords(prefecture, municipality);
}
```

---

### 提案2: applicants データの削減 ★★★

**実装難易度**: **低**
**期待効果**: **1-2秒削減**
**リスク**: 低（5000件は過剰、実際には500-1000件で十分）

#### 実装方法

**変更ファイル**: `MapCompleteDataBridge.gs:354`

```javascript
// 現在:
applicants: sanitizeRecords_(applicants, 5000),

// 変更後:
applicants: sanitizeRecords_(applicants, 1000), // 5000 → 1000 に削減
```

**根拠**:
- 初期表示では詳細な申請者リストは不要
- overviewタブでは集計値のみ表示
- 詳細が必要な場合は別途ロード可能

---

### 提案3: シート読み込みの一括バッチ化 ★★☆

**実装難易度**: **中**
**期待効果**: **3-5秒削減**
**リスク**: 中（GASの処理時間制限に注意）

#### 実装方法

**新規関数を作成**: `MapCompleteDataBridge.gs`

```javascript
/**
 * 全シートを一度に読み込み、キャッシュする
 * @return {Object} シート名をキーとした2次元配列のマップ
 */
function batchLoadAllSheets_() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const allSheets = ss.getSheets();
  const sheetMap = {};

  allSheets.forEach(sheet => {
    const sheetName = sheet.getName();
    try {
      const data = sheet.getDataRange().getValues();
      if (data.length > 0) {
        sheetMap[sheetName] = data;
      }
    } catch (e) {
      Logger.log(`[batchLoadAllSheets_] シート "${sheetName}" の読み込みに失敗: ${e}`);
    }
  });

  return sheetMap;
}

/**
 * キャッシュされたシートマップからオブジェクト配列を取得
 * @param {Object} sheetMap - batchLoadAllSheets_()の返却値
 * @param {Array<string>} candidates - シート名候補
 * @return {Array<Object>} オブジェクト配列
 */
function getSheetFromCache_(sheetMap, candidates) {
  for (let i = 0; i < candidates.length; i++) {
    const sheetName = candidates[i];
    if (sheetMap[sheetName]) {
      const rows = sheetMap[sheetName];
      if (rows.length < 2) continue;

      const header = rows[0].map(value => String(value || '').trim());
      const records = [];

      for (let j = 1; j < rows.length; j++) {
        const record = {};
        header.forEach((col, idx) => {
          record[col] = rows[j][idx];
        });
        records.push(record);
      }

      return records;
    }
  }
  return [];
}
```

**buildMapCompleteCityData_() を修正**:

```javascript
function buildMapCompleteCityData_(prefecture, municipality) {
  const ctx = resolveRegionContext(prefecture, municipality);
  const today = Utilities.formatDate(new Date(), Session.getScriptTimeZone(), 'yyyy-MM-dd');

  // ★一括シート読み込み
  const sheetMap = batchLoadAllSheets_();

  // ★キャッシュから取得（readFirstAvailableSheet の代わり）
  const phase1 = fetchPhase1MetricsFromCache(prefecture, municipality, sheetMap);
  const applicants = fetchApplicantsForMunicipalityFromCache(prefecture, municipality, sheetMap);
  // ... 以下同様
}
```

**効果**:
- シート読み込みを**1回**に削減（現在23-33回 → 1回）
- `SpreadsheetApp.getActiveSpreadsheet()` の呼び出しを最小化
- GAS APIコール回数を**90%削減**

**リスク**:
- メモリ使用量増加（全シートを一度にメモリに読み込む）
- GASの6分間タイムアウト制限に注意（大規模シートの場合）

---

### 提案4: 並列実行は不可（GASの制約）

**結論**: **実装不可**

**理由**:
- Google Apps Scriptは**シングルスレッド**実行のみ
- `Promise.all()` やWeb Workersは使用不可
- `google.script.run` による並列呼び出しも、サーバー側は逐次処理

---

### 提案5: タブごとの遅延ロード（Lazy Loading） ★★★

**実装難易度**: **中**
**期待効果**: **初回表示を1-2秒に短縮**
**リスク**: 低（UX改善も期待できる）

#### 実装方法

**Phase A: 初回表示はOverviewタブのみ**

**新規関数**: `MapCompleteDataBridge.gs`

```javascript
/**
 * Overview タブ用の最小限データ取得
 * @param {string} prefecture
 * @param {string} municipality
 * @return {Object}
 */
function getMapCompleteDataOverviewOnly(prefecture, municipality) {
  const cache = CacheService.getScriptCache();
  const cacheKey = 'overview_' + (prefecture || '') + '_' + (municipality || '');

  const cached = cache.get(cacheKey);
  if (cached) {
    try {
      return JSON.parse(cached);
    } catch (e) {
      Logger.log('[getMapCompleteDataOverviewOnly] キャッシュのパースに失敗: ' + e);
    }
  }

  const regionOptions = getRegionOptions();
  const target = determineTargetRegion_(prefecture, municipality, regionOptions);
  saveSelectedRegion(target.prefecture, target.municipality);

  // Phase 1 のみ取得
  const phase1 = fetchPhase1Metrics(target.prefecture, target.municipality);
  const mapMetrics = phase1.tables.mapMetrics || [];

  const applicantTotal = sumRecords_(mapMetrics, ['applicant_count', 'applicants', 'count']);
  const maleTotal = sumRecords_(mapMetrics, ['male_count', 'male', '男性人数']);
  const femaleTotal = sumRecords_(mapMetrics, ['female_count', 'female', '女性人数']);
  const avgAge = weightedAverage_(mapMetrics, ['avg_age', 'average_age'], ['applicant_count', 'count']);

  const lat = weightedAverage_(mapMetrics, ['latitude', 'lat'], ['applicant_count', 'count']);
  const lng = weightedAverage_(mapMetrics, ['longitude', 'lng', 'lon'], ['applicant_count', 'count']);

  const result = {
    selectedRegion: target,
    regionOptions: getRegionOptions(),
    availableRegions: buildAvailableRegions_(target.prefecture),
    cities: [{
      id: buildRegionKey(target.prefecture, target.municipality),
      name: [target.prefecture, target.municipality].filter(p => p).join(' '),
      center: (lat && lng) ? [lat, lng] : null,
      updated: Utilities.formatDate(new Date(), Session.getScriptTimeZone(), 'yyyy-MM-dd'),
      region: target,
      overview: {
        kpis: [
          { label: '求職者数', value: applicantTotal, unit: '人' },
          { label: '平均年齢', value: avgAge, unit: '歳' },
          { label: '男性', value: maleTotal, unit: '人' },
          { label: '女性', value: femaleTotal, unit: '人' }
        ]
      }
    }]
  };

  // キャッシュに保存（5分間）
  try {
    cache.put(cacheKey, JSON.stringify(result), 300);
  } catch (e) {
    Logger.log('[getMapCompleteDataOverviewOnly] キャッシュの保存に失敗: ' + e);
  }

  return result;
}

/**
 * 特定タブのデータを取得
 * @param {string} prefecture
 * @param {string} municipality
 * @param {string} tab - 'supply', 'career', 'urgency', 'persona', 'flow', 'gap', 'rarity', 'competition'
 * @return {Object}
 */
function getMapCompleteDataByTab(prefecture, municipality, tab) {
  const ctx = resolveRegionContext(prefecture, municipality);

  switch (tab) {
    case 'supply':
      return { supply: buildSupplyData_(ctx.prefecture, ctx.municipality) };
    case 'career':
      return { career: buildCareerData_(ctx.prefecture, ctx.municipality) };
    case 'urgency':
      return { urgency: buildUrgencyData_(ctx.prefecture, ctx.municipality) };
    case 'persona':
      return { persona: buildPersonaData_(ctx.prefecture, ctx.municipality) };
    case 'flow':
      return { flow: buildFlowData_(ctx.prefecture, ctx.municipality) };
    case 'gap':
      const phase12 = loadPhase12(SpreadsheetApp.getActiveSpreadsheet(), 'Phase12_SupplyDemandGap');
      return {
        gap: {
          top_gaps: phase12.top_gaps,
          top_ratios: phase12.top_ratios,
          summary: phase12.summary
        }
      };
    case 'rarity':
      const phase13 = loadPhase13(SpreadsheetApp.getActiveSpreadsheet(), 'Phase13_RarityScore');
      return {
        rarity: {
          rank_distribution: phase13.rank_distribution,
          top_rarity: phase13.top_rarity,
          summary: phase13.summary
        }
      };
    case 'competition':
      const phase14 = loadPhase14(SpreadsheetApp.getActiveSpreadsheet(), 'Phase14_CompetitionProfile');
      return {
        competition: {
          top_locations: phase14.top_locations,
          summary: phase14.summary
        }
      };
    default:
      return {};
  }
}
```

**HTML側の修正**: `map_complete_integrated.html`

```javascript
// 初回はOverviewタブのみロード
async function loadData() {
  try {
    if (typeof google !== 'undefined' && google.script && google.script.run) {
      const pref = selectedRegion?.prefecture || '';
      const muni = selectedRegion?.municipality || '';

      // ★初回はOverviewのみ
      google.script.run
        .withSuccessHandler(function(payload) {
          if (payload) {
            applyPayload(payload);
            currentDataState.overviewLoaded = true;
          }
        })
        .withFailureHandler(function(err) {
          console.error('Overview取得に失敗しました。', err);
        })
        .getMapCompleteDataOverviewOnly(pref, muni);
    }
  } catch (e) {
    console.error('初期ロードエラー', e);
  }
}

// タブ切り替え時に遅延ロード
function onTabChange(newTab) {
  if (!currentDataState[newTab + 'Loaded']) {
    showLoadingIndicator(newTab);

    google.script.run
      .withSuccessHandler(function(tabData) {
        // タブデータをマージ
        Object.assign(globalCityData, tabData);
        currentDataState[newTab + 'Loaded'] = true;
        renderTab(newTab);
        hideLoadingIndicator(newTab);
      })
      .withFailureHandler(function(err) {
        console.error(`タブ "${newTab}" のデータ取得に失敗しました。`, err);
        hideLoadingIndicator(newTab);
      })
      .getMapCompleteDataByTab(selectedRegion.prefecture, selectedRegion.municipality, newTab);
  } else {
    renderTab(newTab);
  }
}
```

**効果**:
- 初回表示時間: **15-23秒 → 1-2秒**（Phase 1のみ取得）
- タブ切り替え時: 2-4秒（各Phaseごとに取得）
- ユーザー体験の向上（必要なデータのみ取得）

---

### 提案6: personaDetails と personaSummary の削減 ★☆☆

**実装難易度**: **低**
**期待効果**: **0.5-1秒削減**
**リスク**: 低

#### 実装方法

**変更ファイル**: `MapCompleteDataBridge.gs`

```javascript
// 現在:
personaSummary: sanitizeRecords_(phase3.tables.personaSummary, 50),
personaDetails: sanitizeRecords_(phase3.tables.personaDetails, 200),

// 変更後:
personaSummary: sanitizeRecords_(phase3.tables.personaSummary, 30),  // 50 → 30
personaDetails: sanitizeRecords_(phase3.tables.personaDetails, 100), // 200 → 100
```

---

### 提案7: 不要なフィールドの削除 ★☆☆

**実装難易度**: **低**
**期待効果**: **0.2-0.5秒削減**
**リスク**: 低

#### 実装方法

**変更ファイル**: `MapCompleteDataBridge.gs:sanitizeRecords_()`

```javascript
function sanitizeRecords_(records, limit) {
  if (!records || !records.length) {
    return [];
  }
  var slice = typeof limit === 'number' ? records.slice(0, limit) : records.slice();
  return slice.map(function (record) {
    var sanitized = {};
    Object.keys(record || {}).forEach(function (key) {
      // ★__normalized フィールドを削除（既に実装済み）
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
```

**既に実装済み**のため、追加効果は限定的。

---

### 提案8: ScriptCache の有効期限延長 ★☆☆

**実装難易度**: **極低**
**期待効果**: **2回目以降のアクセスで高速化**
**リスク**: 低（データの鮮度が下がる）

#### 実装方法

**変更ファイル**: `MapCompleteDataBridge.gs:56`

```javascript
// 現在:
cache.put(cacheKey, JSON.stringify(result), 300); // 5分間

// 変更後:
cache.put(cacheKey, JSON.stringify(result), 3600); // 60分間
```

**注意**: データ更新頻度に応じて調整。

---

## 3. 最終推奨案（優先度TOP3）

### 🥇 推奨1: タブごとの遅延ロード（Lazy Loading）

**実装難易度**: 中
**期待効果**: **初回15-23秒 → 1-2秒**（約90%削減）
**リスク**: 低
**理由**:
- 最も効果が高く、ユーザー体験も向上
- 初回はOverviewタブのみ表示で十分
- 他のタブは必要に応じてロード

**実装手順**:
1. `getMapCompleteDataOverviewOnly()` 関数を作成
2. `getMapCompleteDataByTab()` 関数を作成
3. HTML側でタブ切り替えイベントハンドラを実装
4. ローディングインジケーターを追加

---

### 🥈 推奨2: Phase 12-14の all_records 削除

**実装難易度**: 低
**期待効果**: **2-4秒削減**
**リスク**: 極低（all_records は現在未使用）
**理由**:
- 即座に実装可能
- データサイズを70-80%削減
- 既存機能への影響なし

**実装手順**:
1. `MapCompleteDataBridge.gs:382-384` を修正
2. `all_records` フィールドを明示的に削除
3. 動作確認

---

### 🥉 推奨3: シート読み込みの一括バッチ化

**実装難易度**: 中
**期待効果**: **3-5秒削減**
**リスク**: 中（メモリ使用量増加）
**理由**:
- シート読み込み回数を90%削減
- GAS APIコール回数を最小化
- キャッシュと組み合わせることで効果倍増

**実装手順**:
1. `batchLoadAllSheets_()` 関数を作成
2. `getSheetFromCache_()` 関数を作成
3. `buildMapCompleteCityData_()` を修正
4. 各 `fetchPhaseX()` 関数を修正（シートマップを引数に追加）

---

## 4. 組み合わせ最適化案

### 組み合わせA: 推奨1 + 推奨2（最も現実的）

**期待効果**: **初回1-2秒、タブ切り替え2-4秒**
**実装難易度**: 中
**総削減時間**: **約14-21秒**（初回）

**実装順序**:
1. 推奨2（Phase 12-14 all_records削除）← 1時間
2. 推奨1（遅延ロード）← 4-6時間
3. テスト・検証 ← 2時間

**総実装時間**: 7-9時間

---

### 組み合わせB: 推奨1 + 推奨2 + 推奨3（最大効果）

**期待効果**: **初回0.5-1秒、タブ切り替え1-2秒**
**実装難易度**: 高
**総削減時間**: **約17-22秒**（初回）

**実装順序**:
1. 推奨2（Phase 12-14 all_records削除）← 1時間
2. 推奨3（バッチロード）← 6-8時間
3. 推奨1（遅延ロード）← 4-6時間
4. テスト・検証 ← 3時間

**総実装時間**: 14-18時間

---

## 5. 補足情報

### 5.1 GASのパフォーマンス制約

- **実行時間上限**: 6分間（Google Workspace有料版）、30秒（無料版）
- **メモリ制限**: 明示的な制限なし（実質100MB程度）
- **SpreadsheetApp API呼び出し**: 1呼び出しあたり0.2-2秒
- **キャッシュサイズ**: 最大100KB（ScriptCache）

### 5.2 並列実行が不可能な理由

Google Apps Scriptは以下の制約があります:
- JavaScriptエンジンはV8だが、Web Workers非対応
- `Promise.all()` は動作するが、シート読み込みは同期処理のため並列化不可
- `google.script.run` による複数関数呼び出しも、サーバー側は逐次実行

### 5.3 既に実装済みの最適化

以下は既に実装されています:
- ✅ ScriptCache による5分間キャッシュ（MapCompleteDataBridge.gs:23-35）
- ✅ `__normalized` フィールドの削除（MapCompleteDataBridge.gs:805-807）
- ✅ `sanitizeRecords_()` によるデータ件数制限

---

## 6. 実装リスク評価

| 提案 | リスク | 対策 |
|------|-------|------|
| 遅延ロード | タブ切り替え時のUX低下 | ローディングインジケーター追加、キャッシュ活用 |
| all_records削除 | 将来的に必要になる可能性 | 専用関数を用意（必要時に呼び出し可能） |
| バッチロード | メモリ不足でクラッシュ | try-catch でエラーハンドリング、フォールバック実装 |
| applicants削減 | 詳細データ不足 | 必要に応じて別途ロード関数を用意 |

---

## 7. 測定方法（実装後の検証）

### 7.1 GAS側の測定

```javascript
function getMapCompleteData(prefecture, municipality) {
  const startTime = new Date().getTime();

  // 既存処理
  const result = ...;

  const endTime = new Date().getTime();
  const elapsedTime = (endTime - startTime) / 1000;

  Logger.log(`[Performance] getMapCompleteData: ${elapsedTime}秒`);

  return result;
}
```

### 7.2 HTML側の測定

```javascript
const startTime = performance.now();

google.script.run
  .withSuccessHandler(function(payload) {
    const endTime = performance.now();
    const elapsedTime = ((endTime - startTime) / 1000).toFixed(2);
    console.log(`[Performance] データ取得完了: ${elapsedTime}秒`);
  })
  .getMapCompleteData(pref, muni);
```

---

## 8. まとめ

### 現状の問題点

1. **全Phaseデータを一度に読み込み**（15-23秒）
2. **シート読み込み回数が過剰**（23-33回）
3. **不要なデータも含まれている**（all_records、applicants 5000件）

### 解決策

最も効果的な組み合わせ:
1. **遅延ロード**（初回1-2秒、90%削減）
2. **Phase 12-14 all_records削除**（2-4秒削減）
3. **シート一括バッチロード**（3-5秒削減）

### 期待される成果

- **初回表示**: 15-23秒 → **0.5-2秒**（目標5秒を大幅に達成）
- **タブ切り替え**: 新たに2-4秒必要（初回のみ）
- **2回目以降**: キャッシュにより約1秒

---

## 9. 次のステップ

1. ✅ このレポートをレビュー
2. 実装する最適化案を選択（推奨: 組み合わせA）
3. 開発・テスト環境で実装
4. パフォーマンス測定
5. 本番環境にデプロイ

---

**分析完了日**: 2025年11月4日
**分析者**: Claude Code (Performance Engineer)
