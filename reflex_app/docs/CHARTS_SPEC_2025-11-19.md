# MapComplete Dashboard グラフ仕様・検証レポート（2025-11-19）

## 目的と範囲
- 本書は、MapComplete Dashboard の全グラフについて、目的・データ・可視化方式をMECEで整理し、最新修正の適合性を記録します。
- 実装参照: `mapcomplete_dashboard/mapcomplete_dashboard.py:3174` 以降の各チャート関数、対応する `DashboardState.@rx.var` プロパティ。

---

## 直近の修正サマリー（完了）
- 横棒の向き統一（13件）
  - `layout="horizontal"` → `layout="vertical"`（x=数値、y=カテゴリに一致）
  - 代表行: `mapcomplete_dashboard/mapcomplete_dashboard.py:3737`, `3781`, `3825`, `3871`, `3915`, `3959`, `4005`, `4045`, `4083`, `4121`, `4316`, `4495`, `3695`
- 競合ランキングのY軸ラベル追加（3件）
  - y軸に「ペルソナ」を付与
  - 代表行: `mapcomplete_dashboard/mapcomplete_dashboard.py:4066`, `4110`, `4154`
- Cross のデュアルY軸化（2件）
  - 年齢×資格（line+line）/ 就業×資格（bar+line）を `composed_chart` 化
  - 代表定義: `mapcomplete_dashboard/mapcomplete_dashboard.py:3288`, `3320`

---

## MECEカバレッジ（領域別の目的・データ・可視化）

### Overview（俯瞰）
- 性別シェア（pie）
  - 目的: 全体の男女構成の把握
  - データ: `overview_gender_data`（SUMMARY: male_count/female_count）
  - 実装: `mapcomplete_dashboard/mapcomplete_dashboard.py:3555`, `673`
- 年齢分布（bar）
  - 目的: 年齢層ごとの人数の比較
  - データ: `overview_age_data`（AGE_GENDER を年齢で集計）
  - 実装: `mapcomplete_dashboard/mapcomplete_dashboard.py:3583`, `704`
- 年齢×性別（grouped bar）
  - 目的: 年齢×性別の2次元分布
  - データ: `overview_age_gender_data`（AGE_GENDER）
  - 実装: `mapcomplete_dashboard/mapcomplete_dashboard.py:3174`, `442`

### Supply（供給特性）
- 就業状態（bar）
  - 目的: 在学/就業/非就業の構成（仕様モデル）
  - データ: `supply_status_data`（総数×60/30/10）
  - 実装: `mapcomplete_dashboard/mapcomplete_dashboard.py:3613`, `742`
- 資格バケット（pie / bar）
  - 目的: 保有資格数の分布（仕様モデル）
  - データ: `supply_qualification_buckets_data`（総数×20/30/25/25）
  - 実装: `mapcomplete_dashboard/mapcomplete_dashboard.py:3641`, `3524`, `618`
- ペルソナ別平均資格数（横棒）
  - 目的: ペルソナごとの平均資格数の比較
  - データ: `supply_persona_qual_data`（加重平均）
  - 実装: `mapcomplete_dashboard/mapcomplete_dashboard.py:3669`, `770`

### Flow（流動）
- 流入/流出/純フロー Top10（横棒）
  - 目的: 自治体別の流動の規模比較
  - データ: `flow_inflow_ranking` / `flow_outflow_ranking` / `flow_netflow_ranking`（FLOW）
  - 実装: `mapcomplete_dashboard/mapcomplete_dashboard.py:3709`, `3753`, `3797`, `2199`, `2233`, `2267`

### Gap（需給ギャップ）
- 不足/余剰/比率 Top10（横棒）
  - 目的: 自治体別の需給ギャップを3指標で把握
  - データ: `gap_shortage_ranking` / `gap_surplus_ranking` / `gap_ratio_ranking`（GAP）
  - 実装: `mapcomplete_dashboard/mapcomplete_dashboard.py:3843`, `3887`, `3931`, `1995`, `2030`, `2066`
- 需給比較（bar2系列）
  - 目的: 需要と供給の総量比較
  - データ: `gap_compare_data`
  - 実装: `mapcomplete_dashboard/mapcomplete_dashboard.py:4376`, `1836`
- バランス（pie）
  - 目的: 構成比の俯瞰（注: 指標の整合は後述）
  - データ: `gap_balance_data`
  - 実装: `mapcomplete_dashboard/mapcomplete_dashboard.py:4411`, `1864`

### Rarity（希少性）
- ランク構成（pie）
  - 目的: S/A/B/C/Dランクの構成
  - データ: `rarity_rank_data`（`'^([SABCD]):'` 抽出）
  - 実装: `mapcomplete_dashboard/mapcomplete_dashboard.py:4441`, `2305`
- スコア上位（横棒）
  - 目的: 希少性スコア上位の比較
  - データ: `rarity_score_data`（Top10）
  - 実装: `mapcomplete_dashboard/mapcomplete_dashboard.py:4469`, `2351`
- 年齢/性別分布
  - 実装: `mapcomplete_dashboard/mapcomplete_dashboard.py:5036`, `5079`, `2504`, `2538`

### Competition（競合）
- 性別構成（pie）
  - データ: `competition_gender_data`（SUMMARY）
  - 実装: `mapcomplete_dashboard/mapcomplete_dashboard.py:4509`, `2681`
- トップ年齢/就業（bar）
  - データ: `competition_age_employment_data`（SUMMARY 平均）
  - 実装: `mapcomplete_dashboard/mapcomplete_dashboard.py:4537`, `2714`
- ランキング（横棒）
  - 目的: 国家資格率 / 平均資格数 / 女性比率 の比較
  - データ: `competition_national_license_ranking` / `competition_qualification_ranking` / `competition_female_ratio_ranking`
  - 実装: `mapcomplete_dashboard/mapcomplete_dashboard.py:4023`, `4061`, `4099`, `2813`, `2848`, `2883`

### Persona（ペルソナ）
- 上位人数（横棒）
  - データ: `persona_bar_data`（Top15）
  - 実装: `mapcomplete_dashboard/mapcomplete_dashboard.py:4291`, `1192`
- 就業内訳（stacked bar）
  - データ: `persona_employment_breakdown_data`（命名規則から抽出）
  - 実装: `mapcomplete_dashboard/mapcomplete_dashboard.py:4329`, `1227`
- シェア（pie）
  - データ: `persona_share_data`
  - 実装: `mapcomplete_dashboard/mapcomplete_dashboard.py:4263`, `1272`

### Career（キャリア）
- 年齢×就業（stacked bar）
  - データ: `career_employment_age_data`（EMPLOYMENT_AGE_CROSS）
  - 実装: `mapcomplete_dashboard/mapcomplete_dashboard.py:4139`, `823`

### Urgency（緊急度）
- 年齢別（composed: bar+line）/ 就業別（composed: bar+line）
  - データ: `urgency_age_data` / `urgency_employment_data`（count + avg_score）
  - 実装: `mapcomplete_dashboard/mapcomplete_dashboard.py:4185`, `4223`, `916`, `955`

### Cross（横断）
- 年齢×就業 / 性別×就業（stacked bar）
  - データ: `cross_age_employment_data` / `cross_gender_employment_data`
  - 実装: `mapcomplete_dashboard/mapcomplete_dashboard.py:3206`, `3247`, `1313`, `1350`
- 年齢×資格（composed: line+line）/ 就業×資格（composed: bar+line）
  - データ: `cross_age_qualification_data` / `cross_employment_qualification_data`
  - 実装: `mapcomplete_dashboard/mapcomplete_dashboard.py:3288`, `3320`, `1402`, `1460`
- ペルソナ×資格×年齢（scatter）
  - データ: `cross_persona_qualification_age_data`
  - 実装: `mapcomplete_dashboard/mapcomplete_dashboard.py:3352`, `1513`
- 年齢×性別の移動性（bar）
  - データ: `cross_distance_age_gender_data`（モデル計算）
  - 実装: `mapcomplete_dashboard/mapcomplete_dashboard.py:3387`, `1578`
- 緊急度×資格×年齢（bar）
  - データ: `cross_urgency_career_age_data`
  - 実装: `mapcomplete_dashboard/mapcomplete_dashboard.py:3415`, `1631`
- 供給密度×需給比×ギャップ（scatter）
  - データ: `cross_supply_demand_region_data`（x: density, y: ratio, z: gap）
  - 実装: `mapcomplete_dashboard/mapcomplete_dashboard.py:3448`, `1693`
- 多次元プロファイル（radar）
  - データ: `cross_multidimensional_profile_data`
  - 実装: `mapcomplete_dashboard/mapcomplete_dashboard.py:3483`, `1747`

---

## 可視化標準（横断ルール）
- 横棒: `layout="vertical"`、`x_axis(type_="number")`、`y_axis(data_key="name", type_="category")`
- 凡例/ツールチップ: 原則 `rx.recharts.legend()` と `rx.recharts.graphing_tooltip()` を付与
- 単位/スケール: %系はデータ側で×100換算。スケール差は `composed_chart` + 左右Y軸で分離
- カラーパレット: Okabe-Ito 系（色弱対応）を採用

---

## データソース（row_type）と主要カラム
- FLOW: `inflow/outflow/net_flow`
- GAP: `gap/demand_count/supply_count/demand_supply_ratio`
- RARITY: `rarity_score` とランク（S/A/B/C/D）
- COMPETITION: `national_license_rate/avg_qualification_count/female_ratio`
- SUMMARY: `male_count/female_count/top_age_ratio/top_employment_ratio`
- AGE_GENDER: 年齢×性別の集計
- EMPLOYMENT_AGE_CROSS: 年齢×就業・資格関連（平均など）
- URGENCY_AGE/URGENCY_EMPLOYMENT: 件数 + 平均スコア
- PERSONA_MUNI: ペルソナの人数・内訳・平均資格数（加重平均）

---

## 適合性（要件充足の確認）
- 向き・軸: 横棒はすべて `vertical` で整合し、目的に合致
- ラベル/凡例/tooltip: 主要グラフは日本語ラベルあり。競合ランキングはY軸に「ペルソナ」付与
- 単位・スケール: デュアルY軸導入により、資格数と%の同時比較が明確
- 並べ替え/TopN: ランキングは降順Top10（ペルソナ人数はTop15）
- リアクティブ: `data=DashboardState.xxx` でフィルタ追従、空配列時も安全

---

## 注意点・保留事項（今後の改善候補）
- Gapバランス（pie）の指標統一
  - 現在: 「不足合計 vs 供給総量」。意図に応じ「不足 vs 余剰」または「需要 vs 供給」への統一を推奨
  - 実装参照: `mapcomplete_dashboard/mapcomplete_dashboard.py:1864`, `4411`
- Cross の需給比ラベル/式の整合
  - 現在: `demand_ratio = supply / demand`。一般名としては demand/supply の解釈が多い
  - 対応: 式を変更するか、ラベルを「供給/需要比」などに変更
  - 実装参照: `mapcomplete_dashboard/mapcomplete_dashboard.py:1711`, `3448`
- 仕様値の注記表示
  - Supply の就業状態/資格バケット、Cross の移動性スコアは仕様モデル。UIに注記を出すと期待値管理が容易

---

## テスト実行手順

### セットアップ
- 仮想環境作成: `py -3.11 -m venv .venv`
- 有効化: `.venv\Scripts\Activate.ps1`
- 依存導入: `pip install -r requirements.txt`
- テスト依存: `pip install pytest pytest-asyncio playwright`
- Playwright ブラウザ: `python -m playwright install chromium`

### ユニット
- 実行: `python -m pytest -q tests/run_unit_tests.py`

### 統合
- 実行: `python -m pytest -q tests/run_integration_tests.py`

### E2E（Playwright）
- アプリ起動（別ターミナル）: `reflex run`（既定: `http://localhost:3000`）
- 実行: `python tests/run_e2e_tests.py`
- 備考: ポート変更時は `tests/run_e2e_tests.py:BASE_URL` を起動URLに合わせて修正

---

## 付記
- 本書は 2025-11-19 時点の実装に基づく。以降の変更があれば本書も更新すること。

