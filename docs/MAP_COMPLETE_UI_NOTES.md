# MapComplete Ver2 UI 暫定仕様（2025-11-01時点）

## 目的
## 2025-11-02 改善サマリー

### 1. サイドバー上部レイアウトの再設計
- **何を**: 地域プルダウンとサマリーカードが固定幅で並び、タブ領域が圧迫されていた。
- **どうやって**: `header.app` を `app-head`/`app-controls` の2段グリッドへ組み替え、リサイズハンドルと `ResizeObserver` で Chart.js の `resize()` を都度呼ぶようにした。
- **効果**: サイドバー幅を変えてもタブ内部の表示幅が確保され、PC/タブレットどちらでも一覧性が向上。

### 2. チャート表示の安定化と値フォーマットの統一
- **何を**: 供給タブのグラフが縦に伸び続けたり、比率が小数で表示されていた。
- **どうやって**: 各カードに `<div class="chart-body">` を挿入し高さを固定、`formatValue()` で 0〜1 の値を `%` へ変換するルールを追加。
- **効果**: リサイズやスクロール時もレイアウトが崩れず、数値の意味が直感的に読み取れるようになった。

### 3. クロス分析タブの情報整理
- **何を**: テーブルが羅列されており、重要指標を探すのに時間がかかっていた。
- **どうやって**: 平均募集難易度／最多ペルソナ／資格レベル上位／応募集中地域をチップ形式で集約し、続くテーブルを `renderRecordsTable` で再利用できる構造に整理。
- **効果**: タブを開いた瞬間に主要 KPI が把握でき、詳細比較への導線が明確になった。

### 4. GAS ブリッジのデータ増強
- **何を**: HTML で必要な `qualification_summary` と `personaSummaryByMunicipality` が Apps Script から返却されず、ダミーデータに依存していた。
- **どうやって**: `MapCompleteDataBridge.gs` に資格サマリー／市区町村別サマリーの生成処理を追加し、HTML 側で `persona.*` をそのまま描画できるようにした。
- **効果**: 実データで UI の表示崩れや集計の妥当性を即時検証でき、GAS 連携時の手戻りを防止。
`gas_files/html/map_complete_prototype_Ver2.html` を基準とする MapComplete Ver2 UI の暫定仕様を整理し、採用コンサルタント／データサイエンティスト双方で認識を揃える。UI の構造・インタラクション・データ依存・現時点の課題を把握することが目的。

## 構成サマリ
- マップ：Leaflet + OpenStreetMap タイル。初期中心位置はデータの `center`（緯度経度）を利用し、未取得時は東京都心にフォールバック。
- 右サイドバー：
  - ドラッグハンドルで幅を 280px〜(ウィンドウ幅−40px) の範囲で可変。リサイズ時にチャートを再描画し縦横比を保持。
  - 選択エリア表示（プルダウン + サマリーカード）とタブバーを上段に配置。
  - タブ構成を拡張（総合概要／人材供給／キャリア分析／緊急度分析／ペルソナ分析／クロス分析）。クロス分析タブでは Phase3/7/8/10 の多重クロス集計とペルソナ×地域・資格サマリーを表示。
- チャート：Chart.js v4 (`maintainAspectRatio:false` / `resize()`)。UI カラーは既存 Talent Insight 配色を再現し、暗色背景にアクセントカラー（青／オレンジ／紫／緑）。
- データローディング：初期は `<script type="application/json" id="embeddedData">` からサンプル JSON を読み込み、GAS からの `google.script.run.getMapCompleteData` 呼び出しを想定したプレースホルダを組み込んでいる（`loadData()` 内）。

## インタラクション仕様
- **地域選択**
  - プルダウン：`availableRegions` 配列から `<option>` を構築。選択変更で `requestRegion()` を呼び出し、最新データを取得してサイドバーとマップ中心を更新。
  - ピンクリック／地図遷移：Leaflet のサークルマーカーをクリックすると `selectCityByIndex()` が発火し、サイドバーが該当地域に切り替わる。
  - GAS 連携：`loadData()` で `google.script.run.withSuccessHandler(applyPayload).getMapCompleteData(pref, municipality)` を呼び出し、失敗時は `embeddedData` にフォールバック。
- **タブ切替**
  - `syncTabs()` でタブ・パネルの `active` クラスを制御。タブクリック時に関連チャートを `resize()`。
- **サイドバーリサイズ**
  - Pointer Events で実装。`requestAnimationFrame` 経由で Chart.js を再描画し、Leaflet マップサイズも `invalidateSize()` で同期。

## データマッピング
| パネル | 表示要素 | HTML 側のデータ要求 | 想定 GAS フィールド |
| --- | --- | --- | --- |
| 総合概要 | KPI カード（求職者数、平均年齢、男女比、国家資格保有率）、年齢帯別棒グラフ、性別構成ドーナツ | `city.overview.kpis` / `city.overview.age_gender` / `city.overview.averages` | `MapCompleteDataBridge.gs: buildMapCompleteCityData_()` の `overview` ブロック |
| 人材供給 | 就業ステータス内訳、資格バケット、国家資格保有者数 | `city.supply.status_counts` / `qualification_buckets` / `national_license_count` | 同上 `supply` ブロック（Phase7 出力を集約） |
| キャリア分析 | KPI（資格数・希望勤務地数・国家資格率）、就業ステータス×年齢マトリクス | `city.career.summary` / `city.career.employment_age` | Phase7/Phase8 データを元に作成 |
| 緊急度分析 | 対象人数、平均スコア、年齢帯・就業状態別比較 | `city.urgency.summary/by_age/by_employment` | Phase10 CSV からの集計 |
| ペルソナ分析 | 上位ペルソナ TOP5 リスト | `city.persona.top` | Phase7 ペルソナプロファイルを集計 |

## ローカライゼーション
- 文字列はすべて日本語。ブラウザフォントは `'Noto Sans JP','Yu Gothic',Meiryo,system-ui`。
- 数値表現は `Intl.NumberFormat('ja-JP')` を使用し、割合は `style: 'percent'` で 1 桁小数に統一。

## 既知のギャップ（2025-11-01 時点）
1. **GAS とのデータ連携**  
   - `loadData()` ではまだ `embeddedData` にフォールバックしている。`MapCompleteDataBridge.gs#getMapCompleteData` と接続し、都度最新データを取得する必要がある。
2. **Leaflet マーカー描画**  
   - `DATA[i].center` に基づくマーカーやクラスタを未実装。ピン選択 → サイドバー更新の双方向連携が未達。
3. **文字化け対策**  
   - Python → GAS → HTML の経路で UTF-8（BOM）を維持する運用整理が必要。現在も CSV 由来文字列が mojibake になるケースがある。
4. **Phase 拡張の導線**  
   - 旧メニューに存在する詳細ダッシュボード（Phase7/8/10 等）へのショートカットやリンク未設置。
5. **品質アラート表示**  
   - `QualityAndRegionDashboards.gs` の品質フラグを UI 上に表示する仕掛けを未実装。

## 動作確認リスト（HTML 単体テスト想定）
1. 画面読み込み時にサイドバー上部へ京都市伏見区（サンプル）が表示され、チャートが崩れない。
2. サイドバー幅を最大まで広げてもチャートがカードにフィットしたまま再描画される。
3. タブ切替が即時に反映され、他タブのチャートが二重生成されない（`upsertChart` が効いている）。
4. ブラウザサイズ変更後に Leaflet が `invalidateSize()` で正しく再レイアウトされる。
5. `loadData()` 内の `google.script.run` 呼び出しが失敗した場合でも `embeddedData` にフォールバックする。

## 今後の議論ポイント
- 実データを用いた KPI 文言・閾値（例：資格カテゴリ、緊急度スコア）の最終定義。
- マーカーの表示方式（単ピン／クラスタ／ヒートマップ）と地図表示モード切替の UI。
- サイドバー内での Phase 拡張（Phase7/8/10 詳細へのリンク、品質フラグ表示）。
- Python 出力から集計する際のパフォーマンス（市区町村数が多い場合のロード時間対策）。
- 将来的なオフライン検証のためのサンプルデータ生成フロー整備。

## データ連携テスト状況（Apps Script 環境前提）
| テスト観点 | 手順 | 期待結果 | ステータス |
| --- | --- | --- | --- |
| `getMapCompleteData` 呼び出し | スプレッドシートのメニュー「🗺️ 求職者データ分析マップ」を起動 | 選択済み地域でサイドバーが初期化され、品質バッジが表示される | 未実行（GASデプロイ後要確認） |
| フィルタドロップダウン | 都道府県／市区町村を切り替える | `google.script.run` が再実行され、チャートと品質バッジが更新される | 未実行 |
| Leaflet マーカー | ピンをクリック | サイドバーが該当自治体に切り替わり、選択状態が保存される | 未実行 |
| Phase7/10 指標 | 総合概要/人材供給/緊急度タブを目視確認 | CSV 由来の指標が正しい値で表示され、小数が `toFixed` エラーにならない | 未実行 |
| 品質レポート反映 | 品質警告のある自治体を選択 | バッジが警告色となり、ツールチップにメッセージが表示される | 未実行 |
| フォールバック | HTML ファイルが欠損している場合 | 旧 `MapComplete.html` が起動する | 未実行 |

> デプロイ後に上記を実施し、結果を本ノートに反映すること。

## 今回実装した改善（2025-11-01）
1. **データスキーマ拡張**  
   - `MapCompleteDataBridge.getMapCompleteData()` が Phase1/3/7/8/10 のクロス／多重集計を統合し、`cross_insights`・マトリクス・詳細テーブルを返却するよう更新。  
   - `REGION_DASHBOARD_SHEETS` を拡張し、Phase7（PersonaMobility/MapData）・Phase8（教育/キャリアクロス）・Phase10（緊急度マトリクス）のシートに対応。

2. **UI/UX 改修**  
   - サイドバーに「クロス分析」タブを追加し、ペルソナ難易度・ペルソナ×移動許容度・学歴×年齢・キャリア×年齢・緊急度マトリクスを表形式で表示。  
   - チャートカードの高さとレイアウトを見直し、リサイズや大量データでも可視性が維持されるよう調整。

3. **マップ挙動の改善**
- 人材供給タブにペルソナ別平均資格保有数（横棒チャート＋詳細表）を追加し、資格分布をペルソナ視点で把握できるようにした。
  
  - `DataServiceProvider.showMapComplete` を Ver2 UI に切り替え、Leaflet マーカーと `google.script.run` を連携。旧 UI は `showMapCompleteLegacy` 経由で利用可能。  
  - 品質バッジとクロス分析が同一 UI で確認できるよう、関連ドキュメント（アーキテクチャ／UI ノート）を更新。  
  - 人材供給タブに「ペルソナ別平均資格保有数」チャートと詳細表を追加し、ペルソナとの掛け合わせで資格分布を把握できるようにした。
