# 接頭辞付きシート移行後のフォローアップ

## 完了済み（2025-10-30）
- GAS 可視化スクリプトをすべて `PhaseX_*` シート参照に統一  
  (`Phase1-6UnifiedVisualizations.gs`, `Phase8UnifiedVisualizations.gs`, `Phase10UnifiedVisualizations.gs`)
- `QualityAndRegionDashboards.gs` のシート優先順を接頭辞付きシート → 旧シートのフォールバックという並びに整理
- `Upload_Enhanced.html` と `UnifiedDataImporter.gs` のファイル／シートマッピングを同期し、不要な CSV エントリを削除
- `DataManagementUtilities.gs` の統計サマリー／一括クリア対象リストを最新シート名に更新
- `python_scripts/test_phase1_geocoding.py` を `run_complete_v2_perfect.PerfectJobSeekerAnalyzer` ベースに差し替え、`__main__` ガードで pytest 実行時の副作用を抑止

## 残タスク
1. **実機での回帰確認**
   - `python run_complete_v2_perfect.py` で最新 CSV を生成
   - GAS 側（`DataImportAndValidation` / `UnifiedDataImporter`）で取込 → `PhaseX_*` シートが作成されることを確認
   - 地図・品質ダッシュボードや Phase7/8/10 ビューなど主要メニューを手動で開き、表示崩れやエラーの有無をチェック
   - `pytest`（必要に応じてタイムアウト変更）および既存の GAS/JS 自動テストがあれば実行してスクリプトレベルの回帰を確認
2. **バンドル再生成**
   - `node tools/build_regional_dashboard_bundle.js` を再実行し、`apps_script_bundle/` を更新してから GAS 側へデプロイ

## メモ
- 将来的に Python 側の出力ファイルを `PhaseX_*.csv` へ統一する場合は、`run_complete_v2_perfect.py` の命名変更と GAS 側 `alternateNames` の整理をセットで行う。
- データ検証フローや UI のスモークテスト手順をドキュメント化しておくと、次回以降の回帰確認がスムーズになります。*** End Patch*** End Patch
