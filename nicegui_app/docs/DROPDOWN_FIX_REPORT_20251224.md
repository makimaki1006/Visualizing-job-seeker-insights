# Dropdown Fix Report (2025-12-24)

- **Status**: 完了  
- **Scope**: `main.py` (prefecture / municipality filters, NiceGUI compatibility)

---

## 概要
NiceGUI 版 MapComplete Dashboard で、都道府県を選んでも市区町村が更新されない／「All」固定になる、`Select.on_change` が存在せず 500 になる、ドロップダウンが背景と同色で見えない、といった問題を修正しました。

## 原因
- フィルタのイベントハンドラがネストの外にあり、`df` を参照できない場合があった。  
- NiceGUI のバージョン差分で `Select.on_change` が存在しないことがあり、実行時例外となっていた。  
- スタイル未設定で、背景色と同化して視認できなかった。  

## 実施内容
1) `dashboard_page` 内にドロップダウン生成・ハンドラを集約し、`df` を確実に参照。  
2) `Select.on_change` が無い場合は `on_value_change` をエイリアスする互換レイヤーを追加。  
3) pref/muni の選択肢を JIS 北→南順でソート。  
4) ドロップダウンの枠線・テキスト・ポップアップを白系にスタイリングし、イベントで `ui.notify` とログを出力。  

## 検証
- 手動: 都道府県変更で市区町村が更新され、選択値に応じてカード／グラフがフィルタされることを確認。  
- `python -m py_compile main.py`  
- `python -m pytest --maxfail=1`（`tests/test_data_access.py` 通過）  

## 今後の推奨
- NiceGUI バージョンアップ時も `Select.on_change` 互換チェックを残す。  
- プレイブックとして E2E（Playwright など）でドロップダウン選択とフィルタ結果の回帰テストを追加。  
- データソース差分（Turso / CSV）を跨いで pref/muni が揃うかを定期チェック。  
