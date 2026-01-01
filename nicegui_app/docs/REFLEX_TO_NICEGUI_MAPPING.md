# Reflex -> NiceGUI Mapping (2025-12-24)

## 現状の NiceGUI 実装
- Tabs: Overview / Demographics / Mobility / Balance / Jobmap(GAS)
- Filters: 都道府県（JIS順）・市区町村（pref 選択で更新）。互換レイヤーで `Select.on_change` を強制提供。
- Overview: total/male/female、avg_age、avg_qualification_count、market_share_pct、pref top10、pref 指定時の muni top10。
- Demographics: gender pie、avg age buckets、female_ratio、employment_rate、national_license_rate。
- Mobility: inflow/outflow/net_flow、mobility/urgency、inflow/outflow人気度％、pref/muniランキング、desired_prefecture / desired_municipality top10、co_desired_* を使った destination/source ランキング、distance stats、mobility_type 分布。
- Balance: demand/supply/gap、demand_supply_ratio、rarity_score、retention_rate、market_share_pct、rarity・retention・gap・D/S ratio 分布、資格フラグ別 retention、category1/2/3 トップ10。
- Jobmap: Reflex と同じ GAS IFrame（介護職）。

## Reflex 側主要機能（mapcomplete_dashboard.py より）
- Overview / Persona / Flow / Gap / Rarity / Competition などのパネル。
- inflow/outflow/net_flow、rarity_score、retention_rate、market_share、qualification/retention、mobility_type、flow source/destination rankings 等。

## 既に移植済みの要素
- Pref/muni フィルタと順位付け（JIS順）、主要 KPI、男女比・年齢バケット。
- 流動系: inflow/outflow/net_flow、ランキング、希望地 top10、co_desired_* の destination/source ランキング、距離統計、mobility_type 分布。
- バランス系: demand/supply/gap、D/S ratio、rarity・retention 分布、market_share_pct、資格フラグ別 retention、category1/2/3 トップ10。
- GAS Jobmap 埋め込み。

## Reflex からの追加再現方針
- flow source/destination: `co_desired_prefecture/municipality` 列がある場合、pref/muni 切替で topN を表示（実装済み）。
- qualification 詳細: category1/2/3 や is_national_license 列が埋まる場合、資格別の平均や定着率をカード/グラフで拡充。
- persona/career 指標: データ列が揃い次第、Demographics/Balanced タブに追加カードを段階的に追加。

## テスト
- `python -m py_compile main.py`
- `python -m pytest --maxfail=1`（tests/test_data_access.py）
- 手動: フィルタ操作、各タブ表示、Jobmap 埋め込み表示。
