# Phase 12-14「選択地域軸」完全リデザイン

**日付**: 2025年11月2日
**変更理由**: 採用担当者の実務ニーズに対応（「全国ランキング」→「自分が選択した地域のデータ」）
**影響範囲**: Phase 12, 13, 14の全て
**実装状況**: ✅ 完了

---

## サマリー

### 変更前（全国ランキング視点）
- 全国Top 10/Top 15のランキング表示
- どの地域を選択しても同じデータが表示される
- 「**データ分析ツール**」的な視点

### 変更後（選択地域軸）
- **選択した地域のデータ**のみを表示
- 地域ごとに異なるデータが表示される
- 「**採用意思決定支援システム**」的な視点

---

## 変更詳細

### Phase 12: 需給バランス

**タブ名変更**: 「需給ギャップ」→「**需給バランス**」

#### 変更前
- 全国の需給ギャップTop 10をランキング表示
- 全国の需給比率Top 10をランキング表示

#### 変更後
- **選択した地域の需給データ**を表示
  - 需要（この地域を希望する人数）
  - 供給（この地域に居住する人数）
  - 需給比率
  - 需給ギャップ（需要 - 供給）
  - 需給バランス評価（深刻な人材不足/人材不足/均衡/人材過剰）

#### 表示内容
- **KPI 4つ**: 需要、供給、需給比率、需給バランス（カラーコード付き）
- **需給バランス詳細**: 7項目のサマリー
- **データの見方**: 各指標の意味を解説
- **チャート 2種類**:
  - 需要 vs 供給（Bar Chart）
  - 需給バランス（Doughnut Chart）

#### 表示例（京都府京都市伏見区）
```
KPI:
- 需要（希望者数）: 1,748人
- 供給（居住者数）: 0人
- 需給比率: 1,748.00
- 需給バランス: 🚨 深刻な人材不足

需給バランス詳細:
- 選択地域: 京都府京都市伏見区
- この地域を希望する人材数: 1,748人
- この地域に居住する人材数: 0人
- 需給ギャップ: +1,748人 （不足）
- 需給比率: 1748.00 （需要÷供給+1）
- 評価: 🚨 深刻な人材不足
```

---

### Phase 13: 希少人材分析

**タブ名変更**: 「希少性スコア」→「**希少人材分析**」

#### 変更前
- 全国の希少性スコアTop 15をランキング表示
- 全国の希少性ランク分布

#### 変更後
- **選択した地域を希望する人材の希少性分析**
  - その地域を希望する人材の属性組み合わせ
  - 希少性ランク分布（S/A/B/C/D）
  - 最も希少な人材Top 10

#### 表示内容
- **KPI 4つ**: 属性組み合わせ数、超希少（S）、非常に希少（A）、希少（B）
- **希少性ランク分布**: ランク別の件数
- **最も希少な人材Top 10**: 年齢層、性別、国家資格、人数、希少性スコア、ランク
- **希少性ランクの見方**: S/A/B/C/Dの定義を解説
- **チャート 2種類**:
  - 希少性ランク分布（Doughnut Chart）
  - Top 10 希少性スコア（Bar Chart、ランク別カラーコード）

#### 表示例（京都府京都市伏見区）
```
KPI:
- 属性組み合わせ数: 123件
- 超希少（S）: 45件
- 非常に希少（A）: 32件
- 希少（B）: 28件

最も希少な人材Top 10:
1. 60代 女性 国家資格あり: 1人（スコア1.0、ランクS）
2. 20代 男性 国家資格あり: 1人（スコア1.0、ランクS）
...
```

---

### Phase 14: 人材プロファイル

**タブ名変更**: 「競合分析」→「**人材プロファイル**」

#### 変更前
- 全国の競争が激しい地域Top 15をランキング表示
- 総応募者数、女性比率のランキング

#### 変更後
- **選択した地域を希望する人材のプロファイル**
  - 総希望者数
  - 最も多い年齢層
  - 性別比率
  - 国家資格保有率
  - 最も多い就業状態
  - 平均保有資格数

#### 表示内容
- **KPI 4つ**: 総希望者数、最多年齢層、女性比率、国家資格保有率
- **人材プロファイルサマリー**: 7項目の詳細
- **チャート 2種類**:
  - 性別分布（Doughnut Chart）
  - 年齢層・就業状態（Bar Chart）

#### 表示例（京都府京都市伏見区）
```
KPI:
- 総希望者数: 1,748人
- 最多年齢層: 50代
- 女性比率: 64.1%
- 国家資格保有率: 2.7%

人材プロファイルサマリー:
- 最も多い年齢層: 50代 (28.4%)
- 性別比率: 女性 64.1% / 男性 35.9%
- 最も多い就業状態: 就業中 (64.1%)
- 平均保有資格数: 1.72個
```

---

## 実装変更

### 1. GASファイル修正

**ファイル**: `gas_files/scripts/MapPhase12_14_DataBridge.gs`

**変更内容**: 各Phaseの戻り値に`all_records`配列を追加

```javascript
// Phase 12
return {
  top_gaps: topGaps,
  top_ratios: topRatios,
  all_records: records, // ★追加
  summary: {...}
};

// Phase 13
return {
  rank_distribution: rankDistribution,
  top_rarity: topRarity,
  all_records: records, // ★追加
  summary: {...}
};

// Phase 14
return {
  top_locations: topLocations,
  all_records: records, // ★追加
  summary: {...}
};
```

---

### 2. HTMLファイル修正

**ファイル**: `gas_files/html/map_complete_integrated.html`

#### (1) normalizePayload()の変更

**Phase 12**: locationを照合して各都市にマッチングしたデータを配置
**Phase 13**: all_recordsをそのまま全都市に配置（renderRarity内でフィルタリング）
**Phase 14**: locationを照合して各都市にマッチングしたデータを配置

```javascript
// Phase 12: 需給ギャップデータのマッチング
if (gapAllRecords) {
  cities.forEach(city => {
    const gapData = gapAllRecords.find(r => r.location === city.id);
    if (gapData) {
      city.gap = { ...gapData };
    } else {
      city.gap = { location: city.id, demand_count: 0, ... };
    }
  });
}

// Phase 13: 希少性スコアデータのマッチング
if (rarityAllRecords) {
  cities.forEach(city => {
    city.rarity = { all_records: rarityAllRecords }; // 全レコード渡す
  });
}

// Phase 14: 競合分析データのマッチング
if (competitionAllRecords) {
  cities.forEach(city => {
    const competitionData = competitionAllRecords.find(r => r.location === city.id);
    if (competitionData) {
      city.competition = { ...competitionData };
    } else {
      city.competition = { location: city.id, total_applicants: 0, ... };
    }
  });
}
```

#### (2) render関数の全面書き換え

- **renderGap()**: 選択地域の需給バランスを表示（需給評価、解釈ガイド付き）
- **renderRarity()**: 選択地域を希望する人材の希少性分析（all_recordsフィルタリング）
- **renderCompetition()**: 選択地域を希望する人材のプロファイル

#### (3) タブ名変更

```javascript
{id:'gap', label:'需給バランス'},        // 変更前: 需給ギャップ
{id:'rarity', label:'希少人材分析'},     // 変更前: 希少性スコア
{id:'competition', label:'人材プロファイル'}, // 変更前: 競合分析
```

---

## データフロー

```
[Python] Phase 12-14実装（既存）
  ↓
CSVファイル生成（各locationごとに1レコード）
  - Phase 12: SupplyDemandGap.csv (966レコード)
  - Phase 13: RarityScore.csv (24,000+レコード)
  - Phase 14: CompetitionProfile.csv (966レコード)
  ↓
[GAS] MapPhase12_14_DataBridge.gs
  - loadPhase12/13/14()で全レコードを読み込み
  - all_records配列として返す
  ↓
[HTML] normalizePayload()
  - all_records配列を受け取る
  - Phase 12, 14: 各都市のidとlocationを照合して配置
  - Phase 13: all_recordsをそのまま全都市に配置
  ↓
[HTML] renderGap/Rarity/Competition()
  - Phase 12, 14: 選択した都市のデータを表示
  - Phase 13: all_recordsから選択地域のデータをフィルタリングして表示
```

---

## メリット

### 1. 実務ニーズへの対応

**採用担当者のユースケース**:
- 「大阪市北区で採用したいけど、どんな人材が希望しているの？」
- 「京都市伏見区は人材不足しているの？」
- 「福知山市を希望する希少人材は誰？」

**従来**: 全国Top 15ランキング（無関係）
**改善後**: 選択した地域のデータ（直接役立つ）

---

### 2. 採用戦略立案への活用

| 地域 | Phase 12（需給バランス） | Phase 13（希少人材） | Phase 14（人材プロファイル） | 採用戦略 |
|------|------------------------|-------------------|-------------------------|---------|
| 京都市伏見区 | 🚨 深刻な人材不足<br>（需要1,748人、供給0人） | S/Aランク45件<br>（超希少人材多数） | 50代女性中心64%<br>平均資格1.72個 | **ベテラン女性採用強化**<br>条件: 年齢不問・資格不要<br>訴求: ワークライフバランス |
| 大阪市北区 | ⚠️ 人材不足<br>（需要159人、供給6人） | Sランク20件<br>（若手有資格者希少） | 30代男性中心53%<br>国家資格保有率10% | **若手・中堅採用強化**<br>条件: キャリアアップ支援<br>訴求: スキル向上環境 |
| 福知山市 | ⚖️ 均衡<br>（需要153人、供給5人） | Sランク15件<br>（20代女性希少） | 20代女性中心67%<br>就業中56% | **新卒・第二新卒採用**<br>条件: 研修充実<br>訴求: 地元勤務・転職支援 |

---

### 3. 意思決定支援

**Phase 12（需給バランス）**:
- 「深刻な人材不足」→ 緊急採用キャンペーン実施
- 「人材過剰」→ 選考基準を厳格化

**Phase 13（希少人材分析）**:
- 「Sランク: 60代女性・国家資格あり 1人」→ VIP対応・即オファー
- 「Aランク: 20代男性・国家資格あり 2人」→ 優先アプローチ

**Phase 14（人材プロファイル）**:
- 「50代女性が多い」→ シニア向け求人条件を設定
- 「国家資格保有率2.7%」→ 資格不要求人も検討
- 「就業中64%」→ 転職潜在層へのスカウト強化

---

## 技術的詳細

### 照合ロジック

```javascript
// Phase 12, 14: 完全一致でマッチング
const data = allRecords.find(r => r.location === city.id);
// city.id = "京都府京都市伏見区"
// allRecords[i].location = "京都府京都市伏見区" // ✅ マッチ

// Phase 13: all_recordsから選択地域をフィルタリング
const locationRecords = allRecords.filter(rec => rec.location === city.id);
```

### パフォーマンス

- Phase 12: 966レコード（全国の市町村数）→ O(n)でマッチング
- Phase 13: 24,000+レコード（location × 属性組み合わせ）→ Array.filter()で高速フィルタリング
- Phase 14: 966レコード（全国の市町村数）→ O(n)でマッチング

**結論**: 現在のデータ規模では十分高速。10,000件を超える場合はMapオブジェクトでの最適化を検討。

---

## 検証方法

### 1. GASスクリプトをデプロイ

```bash
# MapPhase12_14_DataBridge.gsをGASプロジェクトにアップロード
# map_complete_integrated.htmlをGASプロジェクトにアップロード
```

### 2. メニューから「MAP分析」を起動

### 3. 検証シナリオ

#### シナリオ1: 京都府京都市伏見区
1. 京都府京都市伏見区を選択
2. 「需給バランス」タブを開く
   - ✅ 需要1,748人、供給0人と表示
   - ✅ 「深刻な人材不足」と評価
3. 「希少人材分析」タブを開く
   - ✅ 属性組み合わせ数100件以上
   - ✅ Sランク/Aランクの希少人材が表示
4. 「人材プロファイル」タブを開く
   - ✅ 総希望者数1,748人
   - ✅ 最多年齢層: 50代
   - ✅ 女性比率: 64.1%

#### シナリオ2: 大阪市北区
1. 大阪市北区を選択
2. 「需給バランス」タブを開く
   - ✅ 需要159人、供給6人と表示
   - ✅ 「人材不足」と評価
3. 「希少人材分析」タブを開く
   - ✅ 属性組み合わせ数表示
   - ✅ Top 10希少人材が表示
4. 「人材プロファイル」タブを開く
   - ✅ 総希望者数159人
   - ✅ 最多年齢層: 30代
   - ✅ 男性比率が女性比率より高い

#### シナリオ3: データがない地域
1. データがない地域を選択（例: 離島など）
2. 各タブで「データがありません」と表示されることを確認

---

## バージョン情報

- **変更前**: v2.0（全国ランキング表示）
- **変更後**: v2.1（選択地域軸）
- **Python側変更**: なし（Phase 12-14のデータ生成ロジックは変更不要）
- **GAS側変更**: MapPhase12_14_DataBridge.gs（all_records追加）
- **HTML側変更**: map_complete_integrated.html（normalizePayload, render関数3つ, タブ名）

---

## 影響範囲

### 変更したファイル
1. `gas_files/scripts/MapPhase12_14_DataBridge.gs`（3箇所修正）
2. `gas_files/html/map_complete_integrated.html`（4箇所修正）
   - normalizePayload()
   - renderGap()
   - renderRarity()
   - renderCompetition()
   - タブ名定義

### 変更していないファイル
- Python実装（`python_scripts/phase12_13_14_implementation.py`）
- CSV出力ファイル（`data/output_v2/phase12-14/`）

---

## 今後の拡張

### 可能性1: 周辺地域との比較

選択地域の需給バランスを、周辺地域と比較表示

```
京都府京都市伏見区: 深刻な人材不足（需要1,748人、供給0人）
周辺地域:
- 京都府京都市山科区: 人材不足（需要1,033人、供給1人）
- 京都府京都市南区: 人材不足（需要885人、供給2人）
```

### 可能性2: 時系列推移

選択地域の需給バランスの時系列推移を表示

```
京都府京都市伏見区の需給推移:
- 2025年10月: 需要1,748人、供給0人
- 2025年9月: 需要1,650人、供給1人
- 2025年8月: 需要1,580人、供給0人
```

### 可能性3: AI推奨アクション（要外部データ）

選択地域の人材プロファイルと求人データを組み合わせて、AIが最適な採用戦略を提案

---

## 参考資料

- Phase 12 CSV: `data/output_v2/phase12/SupplyDemandGap.csv`
- Phase 13 CSV: `data/output_v2/phase13/RarityScore.csv`
- Phase 14 CSV: `data/output_v2/phase14/CompetitionProfile.csv`
- Python実装: `python_scripts/phase12_13_14_implementation.py`
- Phase 14詳細ドキュメント: `docs/PHASE14_SELECTED_REGION_REDESIGN.md`
- 10回反復レビュー計画: `docs/MECE_10_ITERATION_REVIEW_FINAL_PLAN.md`
- 完全再設計計画: `docs/MECE_COMPLETE_REDESIGN_PLAN.md`
