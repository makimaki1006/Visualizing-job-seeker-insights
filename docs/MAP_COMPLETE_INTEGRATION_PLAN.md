# MapComplete Ver2 × GAS 統合計画（2025-11-01）

本書は `gas_files/html/map_complete_prototype_Ver2.html` を Apps Script 環境へ組み込み、Python 出力 → スプレッドシート → GAS → HTML のデータフローを MECE に整理した統合計画である。採用コンサルタント視点（操作感）とデータサイエンティスト視点（指標整合性）の双方をカバーする。

---
## 2025-11-02 反映済み改善ポイント

| 観点 | 何を | どうやって | 効果 |
| --- | --- | --- | --- |
| UI レイアウト | サイドバー上部のスペース不足 | `map_complete_prototype_Ver2.html` のヘッダーを 2 段グリッドに再構成し、Chart.js に `resize()` を発火 | タブ領域が常にフル幅を確保でき、情報が見切れない |
| チャート描画 | 供給タブのグラフが縦伸び・比率値がそのまま | `<div class="chart-body">` ラッパーと `formatValue()` の比率判定を追加 | リサイズ時も安定した描画と直感的な数値表示を実現 |
| クロス分析 | KPI が埋もれていた | 「クロス重点指標」チップ群を追加し、ペルソナ/資格テーブルを整理 | 重要指標を即座に把握できるフローに改善 |
| データ連携 | 資格サマリー等がダミー依存 | `MapCompleteDataBridge.gs` で `qualification_summary` / `personaSummaryByMunicipality` を組み立てて返却 | 実データで UI を確認でき、Apps Script 側との整合を担保 |

## 1. 現状整理

| 項目 | 現状 | 課題 |
| --- | --- | --- |
| UI（Ver2 HTML） | サイドバー可変、タブ 5 枚（総合概要／人材供給／キャリア分析／緊急度分析／ペルソナ分析）、Chart.js + Leaflet。`embeddedData` サンプルをフォールバックに保持。 | `google.script.run` 連携未実装、Leaflet マーカー未配置、品質警告・Phase遷移導線が未整備。 |
| GAS ブリッジ | `gas_files/scripts/MapCompleteDataBridge.gs` を追加済み。`getMapCompleteData(pref, muni)` が Phase1/7/10 指標を集約し JSON で返す。 | HTML 側から未呼び出し。`availableRegions` の UI 反映、文字化け対策の徹底が必要。 |
| データ基盤 | Python (`python_scripts/run_complete_v2_perfect.py`) が `python_scripts/data/output_v2/phase*/*.csv` を生成。Apps Script 側は Phase 接頭辞付きシートにインポート済み。 | CSV が UTF-8(BOM) のため GAS→HTML 変換時に mojibake が発生。Phase7/8/10 の一部ダッシュボードで型不一致エラーが残る。 |
| メニュー体系 | `MenuIntegration.gs` が全メニューを統合。MapComplete 旧 UI（Bubble/Heatmap）を起動可能。 | `showFlowAnalysis` 等の未実装関数がメニューに残存。MapComplete Ver2 から各分析メニューへ遷移する導線を整理する必要。 |

---

## 2. データフローと責務分担

```
Python CSV (phase1/7/8/10) 
  ↓ importPythonCSVDialog / batchImportPythonResults
GAS シート (Phase1_* 〜 Phase10_*)
  ↓ MapCompleteDataBridge#getMapCompleteData
JSON (selectedRegion, regionOptions, availableRegions, cities[])
  ↓ google.script.run 経由で HTML へ
map_complete_prototype_Ver2.html（Leaflet + Chart.js）
  ↓ UI 操作
地域選択保存 (saveSelectedRegion)
```

| UIセクション | 必須フィールド | 取得元 |
| --- | --- | --- |
| サマリーカード | `overview.kpis`（求職者数・平均年齢・男女比・国家資格率） | `fetchPhase1Metrics`/`Phase7Supply` → `buildMapCompleteCityData_` |
| 年齢／性別分布 | `overview.age_gender.age_labels` / `age_totals` / `gender_totals` | Phase7 `AgeGenderCross` |
| 人材供給 | `supply.status_counts` / `qualification_buckets` / `national_license_count` | Phase7 `PersonaProfile` / `SupplyDensity` |
| キャリア分析 | `career.employment_age.rows` / `career.summary` | Phase7 `PersonaProfile` + Phase1 希望勤務地数 |
| 緊急度分析 | `urgency.by_age` / `by_employment` / `summary` | Phase10 `Urgency*` |
| ペルソナ分析 | `persona.top` | Phase7 `PersonaProfile` |

---

## 3. 実装タスク（MECE）

### 3.1 データ整備・品質
1. CSV 読み込み統一：GAS 側で `Utilities.parseCsv(blob, 'UTF-8')` を強制し、文字化けが発生する列を洗い出す。  
2. Phase7/8/10 型チェック：`percentage.toFixed` エラーと `urgencyDist.reduce` エラーを修正し、`MapCompleteDataBridge` が null を返さないよう補正。  
3. 地域リスト整合：`getMunicipalitiesForPrefecture` が Python 出力の自治体一覧と一致するか検証し、欠落自治体を補完。

### 3.2 GAS ↔ HTML 連携
1. `map_complete_prototype_Ver2.html` の `loadData()` を更新し、`google.script.run.withSuccessHandler(applyData).getMapCompleteData(pref, muni)` を呼び出す。  
2. `applyData()` で `selectedRegion`・`regionOptions`・`availableRegions` をステートに格納し、セレクタへ反映。  
3. エラーハンドリング：呼び出し失敗時は `embeddedData` にフォールバックし、ユーザーへトースト表示。  
4. `saveSelectedRegion` を活用し、サイドバー操作 → GAS → HTML の循環を確認。

### 3.3 マップ挙動
1. `initMap()` で市区町村ごとの Marker / CircleMarker / Heatmap（段階的）を描画し、クリックで `selectCity(index)` を呼ぶ。  
2. サイドバーから選択した際に `panToCity(DATA[index])` で地図中心を移動。  
3. 品質指標（`QualityAndRegionDashboards#getMarkerColor`）を Marker カラーに反映。警告がある場合はサイドバーにバッジ表示。

### 3.4 UI 拡張
1. タブ別リンク：Phase7/8/10 旧ダッシュボードへの「詳細を見る」リンクをカード下部に配置。  
2. ペルソナカード整備：`persona.top` が空の場合は「データ不足」表示を出し、ユーザーの迷いを軽減。  
3. 右サイドバーのショートカット：`showStatsSummary` / `checkMapData` など品質チェック機能へのボタンを設置。

### 3.5 テスト & ドキュメント
1. スモークテスト：主要 5 タブ + 地図操作を手動検証し、`docs/GAS_E2E_TEST_GUIDE.md` に MapComplete 手順を追記。  
2. 自動検証（任意）：`MapCompleteDataBridge.gs` のユニットテスト用に `tests/` 配下へ `test_map_complete_bridge.js` (clasp push 前提) を検討。  
3. ドキュメント更新：今回の UI・データ仕様を `docs/MAP_COMPLETE_UI_NOTES.md` と連動、品質チェックリストを更新。

---

## 4. リスクと対策

| リスク | 影響 | 対策 |
| --- | --- | --- |
| 文字化け再発 | UI の信頼性低下、顧客向け資料に転記不可 | 取り込み処理のエンコーディング統一、`decodeURIComponent(escape())` のような暫定処理を避ける。 |
| 大規模自治体データでの描画遅延 | 地図・チャートの体感速度が落ちる | 需要の高い自治体を Lazy Load、チャートデータをタブ表示時に初期化するなど最適化。 |
| GAS 実行時間制限 | `getMapCompleteData` が重くなると 6 分制限に抵触 | 初期は単一自治体のみ返却し、周辺自治体一覧は軽量メタデータに限定。必要に応じてキャッシュを導入。 |
| 既存メニューとの二重管理 | 操作導線が分散 | MapComplete Ver2 に統合済みの機能はメニューから整理。ユーザー教育資料を更新。 |

---

## 5. 直近のネクストアクション

1. **エンコード再確認**  
   - `MapCompleteDataBridge` で取得する文字列に `Utilities.formatString('%s', value)` を適用し、UTF-8 のまま出力されるかを確認。  
2. **`loadData()` の GAS 呼び出し実装**  
   - `map_complete_prototype_Ver2.html` を更新し、HTML ロード時に GAS を呼ぶよう変更。  
3. **マップマーカー仮実装**  
   - `DATA` 配列内の `center` 座標を用いて単純な Marker を配置し、クリックでサイドバーが切り替わることを確認。  
4. **品質アラートの UI 設計**  
   - 既存 Quality Dashboard のロジックから、どの指標をサイドバーへ持ち込むか整理。  
5. **ドキュメント連携**  
   - 本計画に沿って `docs/MAP_COMPLETE_UI_NOTES.md`・`docs/GAS_FUNCTION_INVENTORY.md` を定期的に差分更新し、作業ログを `COMPLETE_TEST_REPORT.md` に紐付ける。

---

## 6. ゴール

- MapComplete Ver2 から市区町村を選択するだけで、採用難易度／人材供給／キャリア／緊急度／ペルソナがシームレスに切り替わる。  
- CSV → シート → GAS → HTML のデータ整合性が担保され、文字化けや型エラーなしで表示できる。  
- 従来メニューは必要最小限のバックアップとして残しつつ、主要業務は MapComplete Ver2 内で完結する。  
- UI／データ仕様・テスト手順がドキュメント化され、次の擦り合わせや機能拡張に即応できる。
