# 地域別ダッシュボード引き継ぎメモ（フェーズ2以降）

最終更新: 2025-10-29

---

## 1. 進捗サマリー

| フェーズ | 状態 | 内容 |
| --- | --- | --- |
| フェーズ0 | 完了 | 目的・要件整理、既存データ確認 |
| フェーズ1 | 完了 | 仕様確定（`docs/REGIONAL_DASHBOARD_PLAN.md`） |
| フェーズ2 | 実装済み（テスト中） | GAS バックエンド：`RegionStateService.gs`, `RegionDashboard.gs` |
| フェーズ3 | 実装済み（テスト中） | フロントエンド：`gas_files/html/RegionalDashboard.html` |
| フェーズ4 | 着手済み | 動作テスト・ドキュメント整備中 |
| フェーズ5 | 未着手 | レビュー・段階リリース準備 |

> 補足: MapVisualization 側でマーカー／クラスターをクリックすると `saveSelectedRegion` が呼ばれ、RegionalDashboard 初期選択に反映されるところまで実装済み。

---

## 2. 主要ファイルと役割

- `RegionStateService.gs`
  - ユーザープロパティに地域選択を保存／読み込み
  - 都道府県／市区町村リストを CacheService 経由で提供
- `RegionDashboard.gs`
  - フェーズ別 API (`fetchPhase1Metrics`, `fetchPhase3Persona`, `fetchPhase7Supply`, `fetchPhase8Education`, `fetchPhase10Urgency` など)
  - PersonaSummary に難易度スコア／ランクを付与
- `gas_files/html/RegionalDashboard.html`
  - 都道府県／市区町村セレクト、フェーズタブ、サマリーカード、警告表示、テーブル描画
  - Phase3 でセグメント／難易度ランクのフィルタを提供
- `gas_files/html/MapComplete.html`
  - マーカー／クラスターのクリックで `saveSelectedRegion` を呼び、ダッシュボード初期値と同期
- `docs/REGIONAL_DASHBOARD_TEST_CHECKLIST.md`
  - 手動テスト項目と実施ログ
- `tests/region_dashboard_logic_test.js`
  - Node.js 上で `RegionDashboard.gs` の純粋関数を検証（難易度計算など）

---

## 3. 次に行うべき作業（フェーズ4）

1. **実機検証**
   - Map → Dashboard 連携: 地図で地域を選択後、ダッシュボード初期選択に反映されるか確認
   - タブ切替／難易度フィルタ: Phase3 でセグメント・難易度ランクが想定通り動くか確認
   - 品質レポート整合性: `QualityReport*.csv` と画面の警告レベルが一致しているかスポットチェック
2. **ドキュメント更新**
   - テスト結果を `docs/REGIONAL_DASHBOARD_TEST_CHECKLIST.md` に追記
   - README や各種ハンドオーバーノートを最新状態へ更新
3. **既知の検討事項**
   - Phase2/Phase8 など地域列の無いフェーズは全体集計のみ表示（警告で通知）。必要なら Python 側で市区町村別 CSV を追加出力
   - テーブル列順を固定したい場合は `RegionDashboard.gs` 側で整形関数を用意

---

## 4. 参考資料

- `docs/REGIONAL_DASHBOARD_PLAN.md`: 設計書（最新仕様）
- `docs/REGIONAL_DASHBOARD_TEST_CHECKLIST.md`: テスト手順と記録
- `README.md` の “Regional Dashboard” セクション: ユーザー向け概要

---

## 5. 連絡メモ

- GAS 実行ログ: 地図からの地域選択保存で `[INFO] Region selection saved` が出力されることを確認
- Node テスト実行: `node tests/region_dashboard_logic_test.js`
- 追加のテスト要望や不明点があればこのドキュメントに追記し、次担当へ共有してください。
