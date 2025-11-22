# Apps Script Import Bundle

このフォルダには、Regional Dashboard を Google Apps Script へ移行する際に必要なファイルを 1 つずつまとめたバンドルを置いています。下記の手順で貼り付ければ、今回追加した機能を省略なく導入できます。

## ファイル一覧

| ファイル | 用途 |
|---------|------|
| `regional_dashboard.gs` | GAS 用スクリプト。`RegionStateService`, `RegionDashboard`, `MapVisualization` を結合済み。添付先の Apps Script プロジェクトにこの 1 ファイルだけ貼り付ければ OK です。 |
| `regional_dashboard_with_map.html` | HTML ダイアログ用。RegionalDashboard UI と MapComplete（地図画面）を 1 つにまとめています。 |
| `all_scripts_bundle.gs` | `gas_files/scripts/` 配下の全 `.gs` ファイルを結合した完全版。既存スクリプトをまとめて貼り付けたい場合はこちらを使用。 |
| `all_html_bundle.html` | `gas_files/html/` 配下の全 `.html` ファイルを結合した完全版。必要に応じて分割貼り付けしてください。 |
| `production_scripts_bundle.gs` | `gas_files_production/scripts/` 配下の全 `.gs` ファイルを結合した運用版。 |
| `production_html_bundle.html` | `gas_files_production/html/` 配下の全 `.html` ファイルの運用版。 |

`phases/` フォルダには、フェーズごと（Phase1、Phase7 など）にまとめた `.gs` バンドルを配置しています。必要なフェーズだけを貼り付けたい場合はこちらを利用してください。

## 貼り付け手順

1. `.gs` をすべて置き換える場合は `production_scripts_bundle.gs`（または `all_scripts_bundle.gs`）を、今回追加分のみで十分な場合は `regional_dashboard.gs` を使用してください。
2. HTML も同様に、全体を統合するなら `production_html_bundle.html`、Regional Dashboard 関連のみなら `regional_dashboard_with_map.html` を使用します。
3. フェーズ単位で貼り付けたい場合は `phases/` 配下のバンドルを利用してください。
4. 既存プロジェクトに貼り付ける前にバックアップを取得してください。

## 補足

- 元となる各ファイルは `/gas_files/scripts/` および `/gas_files/html/` にあります。
- バンドルは `tools/build_regional_dashboard_bundle.js` を実行すると再生成されます。
