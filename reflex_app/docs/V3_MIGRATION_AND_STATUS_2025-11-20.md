# V2→V3 移行と現在の状況（技術サマリー）

## 背景と目的
- 目的: V2 の可視化・集計を完全踏襲しつつ、V3 では「raw→正規化→row_type構築→最終CSV」の単独パイプラインへ移行し、分析の粒度・堅牢性・再現性を向上させる。
- トリガーとなった課題（V2）:
  - 横棒グラフの `layout="horizontal"` による描画不整合、y軸カテゴリ重複による tick キー衝突（`tick-0`）。
  - 一部指標が空（0件）になる事象。表記ゆれ・辞書未整備・集約ヶ所の重複処理不足に起因。
  - 参照粒度が十分でない箇所（特に RARITY/COMPETITION）があり、分析の深さに制約。
  - V2 の row_type 組立が Phase 生成物依存（多段）であり、V3 では 1 パスで再現可能にしたい。

## 設計方針（V3）
- 完全上位互換: V2 の行粒度・指標を下回らない（= 同等以上の粒度）を保証。
- 単独パイプライン: raw を直接読み込み、正規化→row_type 構築→MECE 集約→最終 CSV 出力までを V3 で完結。
- 中央集権的正規化: Unicode/NFKC、比率・真偽・語彙の標準化、列検出の語彙拡充、辞書の未マッチ収集（pending→overlay 昇格）。
- 再計算の明示化: GAP は demand/supply に統一、ゼロ割保護。RARITY は 1/count の定義を厳密化しランク付与。

## 実装概要
- 主スクリプト: `python_scripts/run_complete_v3.py:1`
  - 入力: UI ダイアログで raw `results_*.csv` を選択（V2 踏襲）。
  - 正規化/抽出: 年齢・性別、居住地、希望勤務地、資格、就業状態、希望勤務形態、希望開始などを一元的に整備。
  - row_type 構築（V3 単独）:
    - SUMMARY, AGE_GENDER, FLOW, GAP（需要/供給）, COMPETITION（全自治体網羅）, RARITY（目的地×年齢×性別×国家資格）, URGENCY_AGE, URGENCY_EMPLOYMENT。
  - MECE 集約: 完全重複を排除して再集約。
  - RARITY キャリブレーション（任意）: 参照 CSV（V2）に対し都道府県単位のスケール補正を適用可能（オプション）。
  - 出力: `MapComplete_Complete_All_FIXED.csv`（V2 と互換の列順）。
- 辞書/語彙: `python_scripts/dims_manager.py:1`
  - base+overlay ロード、未マッチは pending へ吐き出し、自動昇格（AUTO_PROMOTE）も選択可能。
- ダッシュボード（Recharts）: `mapcomplete_dashboard/mapcomplete_dashboard.py:1`
  - 横棒は `layout="vertical"` に統一、ランキングはカテゴリで事前集約して tick キー衝突を解消、Y軸ラベル・デュアル軸など可読性改善。

## 変更点（要所）
- グラフ描画の安定化
  - 横棒: `layout="vertical"`、ランキング: 事前 groupby→TopN（重複カテゴリの排除）。
  - 競合ランキングに Y 軸ラベル、Cross 系はデュアル Y 軸（必要箇所）。
- RARITY の厳密化
  - 目的地×年齢バケット×性別×国家資格で行生成、`rarity_score=1/count`、S/A/B/C/D ランクをしきい値で決定。
- URGENCY の追加
  - `desired_start` を正規化（now/<=3m/consider/unknown, as_of, stale）→ AGE/EMPLOYMENT クロスへ反映（`avg_urgency_score`）。
- 列検出の語彙拡充
  - location/desired_area/qualifications/employment_status/desired_start/workstyle/experienced_job/career 等で別表記に対応。

## 出力スキーマ（主要）
- 代表列: `row_type, prefecture, municipality, category1, category2, category3`
- 指標例: `applicant_count, avg_age, male_count, female_count, avg_qualifications, inflow, outflow, net_flow, demand_count, supply_count, gap, demand_supply_ratio, rarity_score, total_applicants, top_age_ratio, female_ratio, male_ratio, top_employment_ratio, avg_qualification_count, avg_urgency_score`

## 行数サマリー（V3 生成物）
- `MapComplete_Complete_All_FIXED.csv`
  - RARITY: 4,950
  - AGE_GENDER: 4,231
  - URGENCY_AGE: 2,942
  - URGENCY_EMPLOYMENT: 1,666
  - FLOW: 966 / GAP: 966 / COMPETITION: 966 / SUMMARY: 944

## テストと回帰
- ユニット: `tests/run_unit_tests.py:1` → 15/15 PASS
- 統合: `tests/run_integration_tests.py:1` → 15/15 PASS
- E2E（安定版）: `tests/run_e2e_tests.py:1` → PASS
  - 安定化方針: テキスト依存を避け、`#csv_upload` の file input に直接 `set_input_files()`、続くボタンをクリック→Recharts 要素の出現で検証。
  - スクリーンショット: `tests/e2e_screenshot.png:1`

## 実行手順（V3 単独）
- 生成
  - `py -3.13 python_scripts\run_complete_v3.py`
  - UI で `results_*.csv` を選択 → 出力フォルダ選択 → `MapComplete_Complete_All_FIXED.csv` を生成。
- Reflex で確認
  - `reflex run`（別ターミナルで起動）→ 画面の CSV アップロードから読み込み。
- 回帰テスト
  - UT: `py -3.13 tests\run_unit_tests.py`
  - IT: `py -3.13 tests\run_integration_tests.py`
  - E2E: `py -3.13 tests\run_e2e_tests.py`

## 現在の状況（まとめ）
- V3 は V2 の完全上位互換を満たす粒度（特に RARITY/COMPETITION/URGENCY）で出力し、UT/IT/E2E を全てパス。
- グラフは横棒の向き・ランキング集約を見直し、重複キー警告（tick-0）を抑止。
- 列検出の語彙と辞書運用（pending→overlay）で、raw の表記ゆれ・欠落に強い構成へ。

## 今後の拡張候補
- RARITY のキャリブレーション自動化
  - V2 参照 CSV（Phase13_RarityScore）を与え、都道府県単位の補正係数を適用して一致率を高める仕組みを追加。
- URGENCY のパラメトリック化
  - `now/<=3m/consider/unknown` のスコア、`stale_days/stale_decay` を引数化・設定ファイル化。
- E2E の更なる安定化
  - UI 要素（アップロード実行/都道府県/市区町村）に test 用 id を付与し、E2E セレクタの依存性を低減。
- DB 連携・本番デプロイ
  - `db_helper.py:1` と `docs/TURSO_DATABASE_*.md:1` に基づく DB 統合、本番デプロイ運用の確立。

---

### 参考ファイル
- パイプライン本体: `python_scripts/run_complete_v3.py:1`
- 辞書管理: `python_scripts/dims_manager.py:1`
- ダッシュボード: `mapcomplete_dashboard/mapcomplete_dashboard.py:1`
- テスト: `tests/run_unit_tests.py:1`, `tests/run_integration_tests.py:1`, `tests/run_e2e_tests.py:1`
- 既存資料: `docs/CHARTS_SPEC_2025-11-19.md:1`, `docs/DATA_PROCESSING_REDESIGN_2025-11-19.md:1`, `docs/CORRECTION_PLAN_2025-11-19.md:1`

