# Phase 1/2 空ファイル発生レポート

## 概要
- **発生現象**: `gas_output_phase1/MapMetrics.csv`・`DesiredWork.csv` と `gas_output_phase2/ChiSquareTests.csv` が 0 件で出力される。
- **発生日**: 2025-10-26 調査時再現。
- **影響範囲**: Phase 1/2 での地図表示・希望勤務地集計・統計分析（GAS 側可視化を含む）が成立しない。

## 原因分析
1. **入力データの前処理状態**
   - 調査時に使用されていた `C:\Users\fuji1\OneDrive\Pythonスクリプト保管\ai_enhanced_data_with_evidence.csv` は、既に 21 列構成へ正規化済み。
   - `o-line__item` など HTML スクレイプ直後の 200 列超カラムが存在せず、住所テキストを含む列が欠落。

2. **列検出ロジックの挙動** （`python_scripts/test_phase6_temp.py:519` 付近）
   - `AdvancedJobSeekerAnalyzer._analyze_desired_work_columns` は `o-line__item` 系のカラムをスキャンし、希望勤務地候補列を `self.desired_work_columns` に収集する設計。
   - 生データ以外を入力すると候補が 0 件となり、`desired_work_columns` が空のまま。

3. **希望勤務地抽出の停止** （`python_scripts/test_phase6_temp.py:643`）
   - `_extract_desired_locations` 冒頭で `desired_work_columns` が空の場合は即 return。
   - `df_processed` に `desired_locations_detail` など希望勤務地関連列が生成されない。

4. **依存処理への伝播**
   - `_process_applicant_data` の `location_counts` が常に空 → `MapMetrics.csv`・`DesiredWork.csv` が 0 件。
   - `_prepare_phase2_data` でも希望勤務地数が集計できず、`ChiSquareTests.csv` が空で出力。

## 再現手順
1. `run_complete.py` または `AdvancedJobSeekerAnalyzer` を `ai_enhanced_data_with_evidence.csv` で実行。
2. 標準出力に `desired_work_columns 0`、`desired_location_count` 計算スキップ等のログを確認。
3. 出力された Phase1/2 CSV がいずれもヘッダーのみであることを確認。

## 暫定的な回避策
1. **生データを入力**  
   - `data/input/` 配下のスクレイプ直後 CSV（201 列など `o-line__item` を含むファイル）を使用すると、希望勤務地列が検出され正常に出力される。
2. **加工済み CSV を投入する場合の留意点**  
   - 現行コードは加工済み（集約済み）データの解析を想定していない。
   - 運用上必要な場合は後述の恒久対策を検討。

## 恒久対策の方向性（要実装検討）
1. `_extract_desired_locations` を拡張し、`df` に希望勤務地列が見つからない場合でも `df_processed` 内の既存カラム（`desired_locations_detail` など）を利用できるよう分岐を追加。
2. `run_complete.py` 実行前に入力ファイル種別を判定し、想定外構造の場合は警告を出す。
3. ドキュメントへ「生データ／加工済みデータで期待される列構成」の説明を追記し、運用手順を明確化。

## 参考ログ
- `python_scripts/test_phase6_temp.py:519` `_analyze_desired_work_columns`
- `python_scripts/test_phase6_temp.py:643` `_extract_desired_locations`
- `python_scripts/test_phase6_temp.py:1623` `_generate_desired_work`
- `python_scripts/test_phase6_temp.py:1461` `_generate_map_metrics`

