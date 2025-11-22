# row_type使用状況詳細分析

**作成日**: 2025年11月21日
**目的**: 各タブ・各グラフが実際に使用しているデータ量を明確化

---

## V3 CSV row_type構成

| row_type | 行数 | 割合 | 備考 |
|----------|------|------|------|
| RARITY | 4,950行 | 28.1% | Phase 13から |
| AGE_GENDER | 4,231行 | 24.0% | Phase 7から |
| URGENCY_AGE | 2,942行 | 16.7% | Phase 10から |
| URGENCY_EMPLOYMENT | 1,666行 | 9.4% | Phase 10から |
| GAP | 966行 | 5.5% | Phase 12から |
| FLOW | 966行 | 5.5% | Phase 6から |
| COMPETITION | 966行 | 5.5% | Phase 14から |
| SUMMARY | 944行 | 5.4% | Phase 1から |
| **EMPLOYMENT_AGE_CROSS** | **0行** | **0%** | ❌ **データなし** |
| **PERSONA_MUNI** | **0行** | **0%** | ❌ **データなし** |

**総行数**: 17,631行

---

## コード内でのrow_type使用状況

### 使用回数ランキング

| row_type | 使用回数 | データ行数 | 状態 |
|----------|----------|------------|------|
| **EMPLOYMENT_AGE_CROSS** | **11回** | **0行** | ❌ **データ不足・機能不全** |
| FLOW | 11回 | 966行 | ✅ 正常 |
| GAP | 11回 | 966行 | ✅ 正常 |
| RARITY | 11回 | 4,950行 | ✅ 正常 |
| **PERSONA_MUNI** | **10回** | **0行** | ❌ **データ不足・機能不全** |
| SUMMARY | 7回 | 944行 | ✅ 正常 |
| URGENCY_AGE | 6回 | 2,942行 | ✅ 正常 |
| COMPETITION | 4回 | 966行 | ⚠️ 低使用率 |
| URGENCY_EMPLOYMENT | 1回 | 1,666行 | ⚠️ 低使用率 |

### 重大な問題

1. **EMPLOYMENT_AGE_CROSS**: 11回使用されているがデータが0行
   - 関連関数（11個）が全て空データを返している
   - キャリアタブ、クロス分析タブで機能不全の可能性

2. **PERSONA_MUNI**: 10回使用されているがデータが0行
   - 関連関数（10個）が全て空データを返している
   - ペルソナタブで機能不全の可能性

---

## タブ別データ使用量（推定）

以下は各グラフ計算関数からの推定です。

### タブ1: 📊 概要

**使用row_type**:
- SUMMARY: 944行
- （AGE_GENDER: 4,231行）← 性別・年齢分布用

**グラフ数**: 6要素（KPI×4、グラフ×2）

**関数**:
- `competition_total_applicants()`: SUMMARY (944行)
- `competition_total_regions()`: SUMMARY (944行)
- `competition_avg_female_ratio()`: SUMMARY (944行)
- `competition_avg_male_ratio()`: SUMMARY (944行)
- `competition_gender_data()`: SUMMARY (944行)
- `競合タブとデータ共有している模様`

**必要行数**: 約944行

---

### タブ2: 👥 年齢・性別

**使用row_type**:
- AGE_GENDER: 4,231行

**グラフ数**: 3要素

**関数**:
- `年齢層別人数`
- `年齢層×性別クロス`
- `平均年齢KPI`

**必要行数**: 4,231行

---

### タブ3: 🎯 ペルソナ

**使用row_type**:
- **PERSONA_MUNI: 0行** ❌

**グラフ数**: 2要素

**関数**:
- `persona_bar_data()`: PERSONA_MUNI (0行) ❌
- `persona_share_data()`: PERSONA_MUNI (0行) ❌
- `persona_top_list()`: PERSONA_MUNI (0行) ❌
- `persona_full_list()`: PERSONA_MUNI (0行) ❌
- `persona_employment_breakdown_data()`: PERSONA_MUNI (0行) ❌
- `cross_gender_employment_data()`: PERSONA_MUNI (0行) ❌
- `cross_multidimensional_profile_data()`: PERSONA_MUNI (0行) + URGENCY_AGE (2,942行) ❌
- `cross_persona_qualification_age_data()`: PERSONA_MUNI (0行) + EMPLOYMENT_AGE_CROSS (0行) ❌
- `supply_persona_qual_data()`: PERSONA_MUNI (0行) ❌

**必要行数**: 0行（データなし・機能不全）

**状態**: ❌ **タブ全体が機能していない可能性**

---

### タブ4: 🔥 緊急度

**使用row_type**:
- URGENCY_AGE: 2,942行
- URGENCY_EMPLOYMENT: 1,666行

**グラフ数**: 2要素

**関数**:
- `urgency_age_data()`: URGENCY_AGE (2,942行)
- `urgency_employment_data()`: URGENCY_EMPLOYMENT (1,666行)
- `urgency_avg_score()`: URGENCY_AGE (2,942行)
- `urgency_total_count()`: URGENCY_AGE (2,942行)
- `cross_urgency_career_age_data()`: URGENCY_AGE (2,942行) + EMPLOYMENT_AGE_CROSS (0行) ⚠️

**必要行数**: 4,608行

**状態**: ⚠️ クロス分析の一部が機能不全の可能性

---

### タブ5: 💎 希少人材

**使用row_type**:
- RARITY: 4,950行

**グラフ数**: 4要素

**関数**:
- `rarity_age_distribution()`: RARITY (4,950行)
- `rarity_gender_distribution()`: RARITY (4,950行)
- `rarity_rank_data()`: RARITY (4,950行)
- `rarity_national_license_ranking()`: RARITY (4,950行)
- `rarity_s_count()`: RARITY (4,950行)
- `rarity_a_count()`: RARITY (4,950行)
- `rarity_b_count()`: RARITY (4,950行)
- `rarity_total_count()`: RARITY (4,950行)
- `rarity_avg_score()`: RARITY (4,950行)
- `rarity_national_license_count()`: RARITY (4,950行)
- `rarity_score_data()`: RARITY (4,950行)

**必要行数**: 4,950行

**状態**: ✅ 正常動作

---

### タブ6: ⚖️ 需給バランス

**使用row_type**:
- GAP: 966行

**グラフ数**: 6要素（KPI×3、グラフ×3）

**関数**:
- `gap_total_demand()`: GAP (966行)
- `gap_total_supply()`: GAP (966行)
- `gap_shortage_count()`: GAP (966行)
- `gap_surplus_count()`: GAP (966行)
- `gap_avg_ratio()`: GAP (966行)
- `gap_compare_data()`: GAP (966行)
- `gap_balance_data()`: GAP (966行)
- `gap_shortage_ranking()`: GAP (966行)
- `gap_surplus_ranking()`: GAP (966行)
- `gap_ratio_ranking()`: GAP (966行)
- `cross_supply_demand_region_data()`: GAP (966行)

**必要行数**: 966行

**状態**: ✅ 正常動作

---

### タブ7: 🏆 競合

**使用row_type**:
- SUMMARY: 944行
- COMPETITION: 966行

**グラフ数**: 1要素（性別分布のみ）

**関数**:
- `competition_gender_data()`: SUMMARY (944行)
- `competition_age_employment_data()`: SUMMARY (944行)
- `competition_total_applicants()`: SUMMARY (944行)
- `competition_total_regions()`: SUMMARY (944行)
- `competition_avg_qualification_count()`: COMPETITION (966行)
- `competition_avg_national_license_rate()`: COMPETITION (966行)
- `competition_qualification_ranking()`: COMPETITION (966行)
- `competition_national_license_ranking()`: COMPETITION (966行)
- `competition_female_ratio_ranking()`: SUMMARY (944行)

**必要行数**: 1,910行

**状態**: ⚠️ 使用率が低い（1グラフのみ実装）

---

### タブ外: キャリア（未実装？）

**使用row_type**:
- **EMPLOYMENT_AGE_CROSS: 0行** ❌

**関数**:
- `career_employment_age_data()`: EMPLOYMENT_AGE_CROSS (0行) ❌
- `career_avg_qualifications()`: EMPLOYMENT_AGE_CROSS (0行) ❌
- `career_national_license_rate()`: EMPLOYMENT_AGE_CROSS (0行) ❌
- `cross_age_employment_data()`: EMPLOYMENT_AGE_CROSS (0行) ❌
- `cross_age_qualification_data()`: EMPLOYMENT_AGE_CROSS (0行) ❌
- `cross_employment_qualification_data()`: EMPLOYMENT_AGE_CROSS (0行) ❌
- `cross_distance_age_gender_data()`: EMPLOYMENT_AGE_CROSS (0行) ❌

**必要行数**: 0行（データなし・未実装）

**状態**: ❌ **タブ全体が未実装またはデータ不足**

---

### タブ外: フロー（未実装？）

**使用row_type**:
- FLOW: 966行

**関数**:
- `flow_inflow()`: FLOW (966行)
- `flow_outflow()`: FLOW (966行)
- `flow_net_flow()`: FLOW (966行)
- `flow_inflow_ranking()`: FLOW (966行)
- `flow_outflow_ranking()`: FLOW (966行)
- `flow_netflow_ranking()`: FLOW (966行)
- `flow_total_inflow()`: FLOW (966行)
- `flow_total_outflow()`: FLOW (966行)
- `flow_mobility_rate()`: FLOW (966行)
- `flow_popularity_rate()`: FLOW (966行)

**必要行数**: 966行

**状態**: ⚠️ **関数は定義されているがUIに未統合**

---

## タブ別必要行数まとめ

| タブ | 使用row_type | 必要行数 | 状態 |
|------|-------------|----------|------|
| 1. 📊 概要 | SUMMARY, AGE_GENDER | 5,175行 | ✅ 正常 |
| 2. 👥 年齢・性別 | AGE_GENDER | 4,231行 | ✅ 正常 |
| 3. 🎯 ペルソナ | PERSONA_MUNI | **0行** | ❌ **機能不全** |
| 4. 🔥 緊急度 | URGENCY_AGE, URGENCY_EMPLOYMENT | 4,608行 | ⚠️ 一部機能不全 |
| 5. 💎 希少人材 | RARITY | 4,950行 | ✅ 正常 |
| 6. ⚖️ 需給バランス | GAP | 966行 | ✅ 正常 |
| 7. 🏆 競合 | SUMMARY, COMPETITION | 1,910行 | ⚠️ 薄い実装 |
| （未実装）キャリア | EMPLOYMENT_AGE_CROSS | **0行** | ❌ **未実装** |
| （未実装）フロー | FLOW | 966行 | ⚠️ **UI未統合** |

**合計必要行数**: 22,806行（重複除外: 17,631行）

---

## 削減・最適化提案

### 削減候補

#### 1. FLOW row_type（966行）

**削減理由**:
- 関数は10個定義されているが、UIに統合されていない
- タブとして表示されていない
- ユーザーが体験できない機能

**影響**: なし（現在未使用）

**削減効果**: -966行 (-5.5%)

#### 2. COMPETITION row_type（966行）

**削減理由**:
- 関数は9個定義されているが、実際のグラフは1個のみ
- タブの実装が非常に薄い
- SUMMARYとデータが重複している部分がある

**影響**: 性別分布グラフ1個が削除される（概要タブで代替可能）

**削減効果**: -966行 (-5.5%)

**代替案**: COMPETITIONタブ自体を削除し、有用な関数は他タブに統合

#### 3. PERSONA_MUNIデータ不足の対応

**問題**: 10回使用されているがデータが0行
- ペルソナタブが機能していない
- 関連する9個の関数が全て空データを返している

**対策オプション**:
- オプションA: PERSONA_MUNIデータを生成（Phase 3から）
- オプションB: ペルソナタブを削除（データ不足のため）

#### 4. EMPLOYMENT_AGE_CROSSデータ不足の対応

**問題**: 11回使用されているがデータが0行
- キャリアタブが未実装
- 関連する11個の関数が全て空データを返している

**対策オプション**:
- オプションA: EMPLOYMENT_AGE_CROSSデータを生成（V3に追加）
- オプションB: キャリア関連関数を削除（未使用のため）

---

## 推奨アクション

### 優先度1: データ不足問題の解決

1. **PERSONA_MUNIデータを生成**
   - generate_mapcomplete_complete_sheets.pyでPhase 3から生成
   - 推定行数: 約2,000-3,000行

2. **EMPLOYMENT_AGE_CROSSデータを生成**
   - V3に新しいrow_typeとして追加
   - 推定行数: 約5,000-8,000行

### 優先度2: 未使用機能の削減

1. **FLOW row_type削除**: -966行
2. **COMPETITION row_type削除または縮小**: -966行

### 優先度3: タブ構成の整理

**現在の問題**:
- 7タブ中2タブが機能不全（ペルソナ、キャリア？）
- 1タブが薄い実装（競合）
- 1タブが未統合（フロー）

**推奨構成** (5タブ):
```
1. 📊 概要（変更なし）
2. 👥 人材プロファイル（年齢・性別 + ペルソナ統合）
3. ⚖️ 需給分析（需給バランス + 競合統合）
4. 💎 希少人材（変更なし）
5. 🔥 緊急度・キャリア（緊急度 + 新キャリアタブ統合）
```

---

## 次のステップ

1. **データ不足の解消**
   - PERSONA_MUNIデータを生成（V3に追加）
   - EMPLOYMENT_AGE_CROSSデータを生成（V3に追加）

2. **未使用row_typeの削減**
   - FLOWを削除（または将来の実装まで保留）
   - COMPETITIONを削減（または他タブに統合）

3. **新機能の追加**
   - ユーザー要件の5機能を最小限のrow_typeで追加

4. **タブ構成の整理**
   - 7タブ → 5タブに削減
   - 機能の統合・整理
