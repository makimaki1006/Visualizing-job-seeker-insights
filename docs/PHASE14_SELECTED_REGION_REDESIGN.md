# Phase 14「人材プロファイル」選択地域軸への設計変更

**日付**: 2025年11月2日
**変更理由**: 採用担当者の実務ニーズに対応（「自分が選択した地域の人材プロファイル」を表示）
**影響範囲**: Phase 14のみ（Phase 12, 13は今後対応予定）

---

## 変更概要

### 変更前（全国ランキング視点）
- 全国Top 15の「競争が激しい地域」をランキング表示
- どの地域を選択しても同じデータが表示される
- 「データ分析ツール」的な視点

### 変更後（選択地域軸）
- **選択した地域を希望する人材のプロファイル**を表示
- 地域ごとに異なるデータが表示される
- 「採用意思決定支援システム」的な視点

---

## 実装変更詳細

### 1. GASファイル修正

**ファイル**: `gas_files/scripts/MapPhase12_14_DataBridge.gs`

**変更内容**:
```javascript
// 【Phase 12】loadPhase12()の戻り値に追加
return {
  top_gaps: topGaps,
  top_ratios: topRatios,
  all_records: records, // ★追加：全レコード
  summary: {...}
};

// 【Phase 13】loadPhase13()の戻り値に追加
return {
  rank_distribution: rankDistribution,
  top_rarity: topRarity,
  all_records: records, // ★追加：全レコード
  summary: {...}
};

// 【Phase 14】loadPhase14()の戻り値に追加
return {
  top_locations: topLocations,
  all_records: records, // ★追加：全レコード
  summary: {...}
};
```

**目的**: 全国のすべてのlocationデータをHTML側に渡す

---

### 2. HTMLファイル修正

**ファイル**: `gas_files/html/map_complete_integrated.html`

#### (1) normalizePayload()関数の変更

**変更前**:
```javascript
// 全都市に同じPhase 12-14データをコピー
cities.forEach(city => {
  city.gap = phase12to14Template.gap;
  city.rarity = phase12to14Template.rarity;
  city.competition = phase12to14Template.competition;
});
```

**変更後**:
```javascript
// Phase 14の全レコードから、各都市のlocationに一致するデータを配置
if (competitionAllRecords) {
  cities.forEach(city => {
    const competitionData = competitionAllRecords.find(r => r.location === city.id);
    if (competitionData) {
      city.competition = {
        ...competitionData,
        summary: {}
      };
    } else {
      city.competition = {
        location: city.id,
        total_applicants: 0,
        summary: {}
      };
    }
  });
}
```

**ロジック**:
1. GASから受け取った`all_records`配列を取得
2. 各都市の`id`と`all_records`の`location`を照合
3. 一致するレコードを各都市の`competition`プロパティに配置
4. 一致しない場合は空データを配置

---

#### (2) renderCompetition()関数の全面書き換え

**変更前**:
- 全国Top 15の地域をテーブル表示
- 総応募者数ランキング、女性比率ランキングをチャート表示

**変更後**:
```javascript
// データ存在チェック
if (!c.total_applicants || c.total_applicants === 0) {
  panel.innerHTML = `この地域を希望する人材データがありません。`;
  return;
}

// KPI表示（4つの主要指標）
- 総希望者数
- 最多年齢層
- 女性比率
- 国家資格保有率

// プロファイルサマリー（7つの属性）
- 選択地域
- この地域を希望する人材数
- 最も多い年齢層（割合付き）
- 性別比率（女性/男性）
- 国家資格保有率
- 最も多い就業状態（割合付き）
- 平均保有資格数

// チャート2種類
- 性別分布（Doughnut Chart）
- 年齢層・就業状態（Bar Chart）
```

---

#### (3) タブ名変更

**変更前**: `{id:'competition', label:'競合分析'}`
**変更後**: `{id:'competition', label:'人材プロファイル'}`

---

## データフロー

```
[Python] Phase 14実装（既存）
  ↓
CompetitionProfile.csv (966レコード)
  - 各location（市町村）ごとに1レコード
  - location: "京都府京都市伏見区"
  - total_applicants: 1748
  - top_age_group: "50代"
  - female_ratio: 0.64
  - etc.
  ↓
[GAS] MapPhase12_14_DataBridge.gs
  - loadPhase14()で全966レコードを読み込み
  - all_records配列として返す
  ↓
[HTML] normalizePayload()
  - all_records配列を受け取る
  - 各都市のidとlocationを照合
  - 一致するレコードを各都市に配置
  ↓
[HTML] renderCompetition()
  - 選択した都市のcompetitionデータを表示
  - "京都府京都市伏見区を希望する1,748人のプロファイル"
```

---

## 表示例

### 選択地域：京都府京都市伏見区

**KPI**:
- 総希望者数: 1,748人
- 最多年齢層: 50代
- 女性比率: 64.1%
- 国家資格保有率: 2.7%

**プロファイルサマリー**:
- 選択地域: 京都府京都市伏見区
- この地域を希望する人材数: 1,748人
- 最も多い年齢層: 50代 (28.4%)
- 性別比率: 女性 64.1% / 男性 35.9%
- 国家資格保有率: 2.7%
- 最も多い就業状態: 就業中 (64.1%)
- 平均保有資格数: 1.72個

**チャート**:
- 性別分布（円グラフ）: 女性1,120人、男性628人
- 年齢層・就業状態（棒グラフ）: 50代28.4%、就業中64.1%

---

## 今後の対応

### Phase 12（需給ギャップ）の選択地域軸対応

現在は「全国の需給ギャップTop 10」を表示していますが、以下に変更予定：

**変更案**:
- 選択した地域の需給データを表示
  - この地域を希望する人数（demand）
  - この地域に居住している人数（supply）
  - 需給比率（demand/supply）
  - ギャップ（demand - supply）
- 意味：「この地域は人材が足りているか、不足しているか」

### Phase 13（希少性スコア）の選択地域軸対応

現在は「全国の希少性Top 15」を表示していますが、以下に変更予定：

**変更案**:
- 選択した地域を希望する人材の希少性分析
  - 希少性ランク分布（S/A/B/C/D）
  - 最も希少な属性組み合わせTop 10
  - 市場価値の高い人材の特定
- 意味：「この地域を希望する人材の中で、特に貴重な人材は誰か」

---

## メリット

1. **実務ニーズへの対応**
   - 採用担当者：「大阪市北区で採用したいけど、どんな人材が希望しているの？」
   - 従来：全国Top 15ランキング（無関係）
   - 改善後：大阪市北区を希望する159人のプロファイル

2. **意思決定支援**
   - 「50代女性が多い」→ シニア向け求人を出すべき
   - 「国家資格保有率10%」→ 有資格者向けの条件を提示
   - 「就業中62%」→ 転職潜在層へのアプローチが必要

3. **地域ごとの戦略立案**
   - 京都市伏見区：50代女性中心（1,748人）→ ベテラン採用戦略
   - 大阪市北区：30代男性中心（159人）→ 若手・中堅採用戦略
   - 福知山市：20代女性中心（153人）→ 新卒・第二新卒戦略

---

## 技術的メモ

### 照合ロジックの注意点

```javascript
// city.idとall_records[].locationの完全一致が必須
city.id = "京都府京都市伏見区"
all_records[0].location = "京都府京都市伏見区" // ✅ マッチ

city.id = "京都府京都市伏見区"
all_records[0].location = "京都市伏見区" // ❌ マッチしない（supply_count=0問題と同じ）
```

### パフォーマンス考慮

- `all_records`配列は966件（全国の市町村数）
- `Array.find()`による線形検索は問題なし（O(n)で十分高速）
- 将来的に10,000件を超える場合はMapオブジェクトでの最適化を検討

---

## 検証方法

1. GASスクリプトをデプロイ
2. HTMLファイルをGASプロジェクトに配置
3. メニューから「MAP分析」を起動
4. 京都府京都市伏見区を選択
5. 「人材プロファイル」タブを開く
6. 表示内容を確認：
   - 総希望者数: 1,748人
   - 最多年齢層: 50代
   - グラフが正しく表示されるか

---

## バージョン情報

- **変更前**: v2.0（全国ランキング表示）
- **変更後**: v2.1（選択地域軸）
- **Python側変更**: なし（Phase 14のデータ生成ロジックは変更不要）
- **GAS側変更**: MapPhase12_14_DataBridge.gs（all_records追加）
- **HTML側変更**: map_complete_integrated.html（normalizePayload, renderCompetition, タブ名）

---

## 参考資料

- CompetitionProfile.csv: `data/output_v2/phase14/CompetitionProfile.csv`
- Python実装: `python_scripts/phase12_13_14_implementation.py` (line 228-327)
- 10回反復レビュー計画: `docs/MECE_10_ITERATION_REVIEW_FINAL_PLAN.md`
- 完全再設計計画: `docs/MECE_COMPLETE_REDESIGN_PLAN.md`
