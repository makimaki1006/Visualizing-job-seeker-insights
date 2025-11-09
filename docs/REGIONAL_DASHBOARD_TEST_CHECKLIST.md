# 地域別ダッシュボード テストチェックリスト (2025-10-29)

RegionalDashboard (GAS) と MapVisualization の連携を正式に受け入れる前に確認すべき項目をまとめています。今後のフェーズ4作業では、本チェックリストをベースに結果を記録してください。

---

## 1. 前提
- Google スプレッドシートに最新の `MapMetrics`, `AggDesired`, `PersonaSummary`, `QualityReport*` シートがインポート済みであること。
- `RegionStateService.gs`, `RegionDashboard.gs`, `RegionalDashboard.html`, `MapComplete.html` を最新化済み。
- ブラウザの開発者ツールでコンソールログを確認できる状態にしておくこと。

---

## 2. 操作シナリオ

### 2.1 地図からの地域選択連携
1. `MapVisualization` メニューから「📊 求職者分析マップ (MapComplete)」を開く。
2. 任意の市区町村のマーカー（またはクラスター）をクリックし、コンソールに `Region selection saved` ログが出ることを確認。
3. そのまま RegionalDashboard を開き、都道府県／市区町村の初期選択が手順2でクリックした地域になっていること。
   - 期待値と異なる場合は `RegionStateService.saveSelectedRegion` のログ、および `PropertiesService` のキーを確認する。

### 2.2 フェーズタブの切り替え
1. Phase1 → Phase10 のタブを順番にクリックし、それぞれでサマリーカード／警告／テーブルが表示されるか確認。
2. Phase2・Phase8 など地域列を持たないフェーズでは、画面上部に警告が表示されること。
3. タブ切り替え時にブラウザコンソールにエラーが出ていないか確認。

### 2.3 フィルター操作（Phase3）
1. Phase3 タブで「ペルソナ セグメント」プルダウンを変更し、テーブル内容とサマリーが切り替わること。
2. 「難易度ランク」プルダウンを変更し、平均難易度スコア＆テーブルがフィルタに追従すること。
3. 条件に合致しない場合に警告と空テーブルが表示されること。

---

## 3. データ整合性チェック

| 対象 | 検証手順 | 期待値 |
| ---- | -------- | ------ |
| Phase1 サマリー | `data/output_v2/phase1/MapMetrics.csv` の該当地域行とダッシュボードの件数を比較 | 件数が一致 |
| Phase3 難易度 | `PersonaSummary.csv` の `avg_qualifications` 等から算出したスコアと画面表示 | ±1 以内で一致 |
| 品質レポート | `QualityReport*.csv` の CRITICAL/ACCEPTABLE 判定と画面警告 | 判定値が一致 |

検証に利用した数値・キャプチャは、テスト結果として `docs/test_logs/` フォルダ配下に保存すると便利です。

---

## 4. 既知の課題 / 今後のタスク
- Phase2／Phase8 は地域粒度の CSV が存在しないため、現状は全体集計のみ表示（警告で通知）。必要に応じて Python 側の CSV 出力を拡張する。
- UI テーブルは簡易整形のため、列順を固定したい場合は `RegionDashboard.gs` で明示的に整形すること。
- 自動テストが未整備。Apps Script 単体テスト or Puppeteer 等での UI テストを検討。

---

## 5. 実施記録メモ

| 日付 | 担当 | 実施項目 | 結果 | 備考 |
| ---- | ---- | -------- | ---- | ---- |
| 2025-10-29 | Assistant | ロジック単体テスト（`RegionDashboard.gs` 難易度計算） | ✅ | `node tests/region_dashboard_logic_test.js` を実行（Node 上で純粋関数を検証） |

---

不明点や既存仕様と異なる挙動を見つけた場合は、本ファイルに追記しつつ `REGIONAL_DASHBOARD_HANDOVER.md` へフィードバックしてください。
