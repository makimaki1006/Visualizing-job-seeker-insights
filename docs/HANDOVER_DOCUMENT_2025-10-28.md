# プロジェクト引継ぎ文書（2025年10月28日）

## 概要

**プロジェクト**: ジョブメドレー求職者データ分析システム
**バージョン**: v2.1（品質検証統合版）
**ステータス**: ✅ 本番運用可能（Phase 1-10完全実装済み）

---

## 技術スタック

### Python
- pandas, numpy, scikit-learn, matplotlib, seaborn, requests
- 実行スクリプト: `python_scripts/run_complete_v2.py`

### GAS
- ✅ **Leaflet.js 1.9.4** + OpenStreetMap（地図表示、**APIキー不要**）
- ✅ **Leaflet.heat 0.2.0**（ヒートマップ）
- ✅ **Chart.js 3.9.1**（統計グラフ）
- Google Charts API（Phase 7等）

### 🔴 禁止事項
- ❌ **Google Maps JavaScript API（GAS側）**: ユーザー明確禁止、APIキー必要、クォータ制限
- ✅ **Google Maps Geocoding API（Python側）**: 座標取得のみ許可（geocache.jsonにキャッシュ）

---

## クイックスタート

### 1. 新データ処理

```bash
cd "C:\Users\fuji1\OneDrive\Pythonスクリプト保管\job_medley_project\python_scripts"
python run_complete_v2.py
```

**出力**: `data/output_v2/` に37ファイル生成（Phase 1, 2, 3, 6, 7, 8, 10）

### 2. GASへインポート

1. Google Spreadsheet → メニュー: `📊 データ処理` → `🎯 Python結果を自動インポート（推奨）`
2. 37ファイル自動インポート（約2-3分）

### 3. 地図表示

- **バブルマップ**: メニュー: `🗺️ 地図表示（バブル）`
- **ヒートマップ**: メニュー: `📍 地図表示（ヒートマップ）`

---

## トラブルシューティング

### 問題1: 「Google マップが正しく読み込まれませんでした」

**原因**: Google Maps JavaScript API使用（禁止）

**解決**:
1. BubbleMap.html、HeatMap.htmlがLeaflet.js使用か確認
2. 以下コードが**含まれていないこと**確認:
   ```html
   <!-- ❌ これがあったらNG -->
   <script src="https://maps.googleapis.com/maps/api/js?key=..."></script>
   ```

### 問題2: CSVインポートエラー

**解決**:
```bash
# Phase 1確認（6ファイル必要）
ls data/output_v2/phase1/ | wc -l

# Phase 8確認（6ファイル必要）
ls data/output_v2/phase8/ | wc -l
```

### 問題3: 品質スコアが低い（60点未満）

**解決**: `data/output_v2/phase*/QualityReport.csv` 確認、警告カラム確認

---

## 必読ドキュメント

| ドキュメント | 用途 |
|------------|------|
| `README.md` | プロジェクト全体概要 |
| `docs/CRITICAL_MISTAKE_PREVENTION_2025-10-28.md` | ミス防止ガイド |
| `docs/ARCHITECTURE.md` | 技術設計 |
| `docs/GAS_COMPLETE_FEATURE_LIST.md` | GAS完全機能一覧 |

---

## 実装前チェックリスト

新機能実装前に必ず確認:

- [ ] 既存コードを読む（BubbleMap.html、HeatMap.html等）
- [ ] 使用ライブラリ確認（scriptタグ全確認）
- [ ] ドキュメント隅々まで読む
- [ ] ユーザー過去指示確認
- [ ] 禁止事項未使用確認（Google Maps JavaScript API等）

**全てチェック完了 → 実装可能**

---

## データフロー

```
生CSV → run_complete_v2.py → 37CSV → GASインポート →
Spreadsheet → 可視化（Leaflet.js/Chart.js）
```

---

## 重要ディレクトリ

```
job_medley_project/
├── python_scripts/run_complete_v2.py    # メイン実行スクリプト
├── gas_files_production/
│   ├── scripts/*.gs                     # GASスクリプト
│   └── html/*.html                      # HTML（Leaflet.js使用）✅
├── data/output_v2/                      # 出力データ（37ファイル）
└── docs/                                # ドキュメント
```

---

## 緊急時対応

### geocache.json破損時
```bash
# 削除して再生成（約10-15分）
rm data/output_v2/geocache.json
python run_complete_v2.py
```

### GASメニュー非表示時
1. スプレッドシート再読み込み
2. MenuIntegration.gs追加確認
3. GASログ確認（表示 → ログ）

---

## よくある質問

**Q: 新Phase追加方法は？**
A: Pythonスクリプト追加 → run_complete_v2.py追加 → PythonCSVImporter.gs追加 → MenuIntegration.gs追加

**Q: テスト実行方法は？**
```bash
python test_phase7.py
python test_phase7_e2e.py
```

---

**作成日**: 2025年10月28日
**修正済みファイル**: BubbleMap.html、HeatMap.html（Leaflet.js化）
