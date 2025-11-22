# 加工ロジック修正計画書（2025-11-19）

## 目的
- run_complete_v2_perfect.py の加工ロジックを、元データの表記ゆれ・複数指定・主観時系列の特性に適合させ、記述的ダッシュボードに十分な品質へ底上げする。
- 個別最適のハードコーディングを避け、外部辞書＋正規化レイヤで横断的に改善する。

## スコープ
- 対象: 学歴/専攻/卒年（career）、経験職種（experienced_job）、保有資格（qualifications）、希望勤務形態（workstyle）、希望時期（desired_start）。
- 非対象: モデル推論などの高度分析（将来検討）。

## 成果物（Deliverables）
- `python_scripts/normalization.py`（正規化レイヤ・関数群）
- `python_scripts/dims/*.csv`（辞書：job_titles/qualifications/education_levels/workstyle/fields）
- run_complete_v2_perfect.py 差分（正規化の導入、正規化列の出力、既存集計の正規化列優先）
- （任意）DETAIL 系 row_type 追加（EXPERIENCE_DETAIL/QUALIFICATIONS_DETAIL/EDUCATION_SUMMARY）
- Notebook/pytest による検証スクリプト（抽出率・未マッチ・回帰）
- ドキュメント更新（本計画・再設計ガイド・CHARTS_SPEC）

## 進め方（WBS）
### Phase 0: 設計・準備（0.5日）
- 辞書フォーマット合意：カラム構成と区切り（synonyms は '|' 区切り）。
- normalization.py の関数インターフェース確定（normalize_master ほか）。

### Phase 1: 正規化レイヤ実装（1.0日）
- 実装: Unicode/空白/区切り統一、真偽・比率正規化、辞書マッチ関数。
- career: 学歴レベル・専攻・卒年（任意）・confidence。
- experienced_job: 職種コード＋経験月数（複数）；最長経験抽出。
- qualifications: 詳細コード＋family/national・その他テキスト保全。
- workstyle: 複数指定→配列化；上位カテゴリ射影も可能に。
- desired_start: バケット化＋基準日抽出＋stale 判定。
- 単体テスト（10–20ケース）。

### Phase 2: パイプライン組み込み（0.5–1.0日）
- run_complete_v2_perfect.py に normalize_master を組み込み（読み込み直後と統合直前）。
- 既存 row_type 生成で正規化列を優先（従来列フォールバック）。
- （任意）DETAIL 系 row_type を追加し、アウトプットへ含める。

### Phase 3: アプリ受け入れ最小対応（0.5日）
- 既存 row_type はそのまま表示（互換）。
- 新 row_type は現時点では未表示のまま（将来拡張）。
- 低品質フェーズ（Phase 3/10）の可視化に注記（現状維持、品質フラグ導入は次ステップ）。

### Phase 4: 検証・回帰（0.5–1.0日）
- 再生成: `results_*.csv` → 統合CSV → 行数・列数・row_type 件数の回帰チェック。
- Notebook/pytest: 抽出率・未マッチ語彙トップ・比率0–1・gap 整合。
- アプリ動作: 主要チャートの目視、React 警告無し、横棒ランキング OK。

### Phase 5: ドキュメントと引継ぎ（0.5日）
- docs 更新：本計画・再設計ガイド・CHARTS_SPEC の整合。
- 運用手順書：辞書の更新方法・検証手順。

## 受け入れ基準（Acceptance Criteria）
- 正規化列が追加され、欠損や表記ゆれに対する抽出率が改善（ベースライン比向上）。
- 主要 row_type（FLOW/GAP/RARITY/COMPETITION）の件数が想定範囲に収束（±5–10% 以内）。
- アプリでの React 警告（tick key 重複等）が消失。
- 比率列が 0–1 に正規化され、可視化での%表現が一貫。
- DETAIL 系 row_type（導入時）はドロップ無く出力される（将来拡張用）。

## リスクと緩和
- 語彙の未マッチ: 未知語頻度表を自動出力し、辞書を継続改善。
- 過度な集約・重複削除: キー定義を明文化し、仕様外の圧縮を防ぐ。回帰テストで検知。
- 需要/供給比の定義不一致: パイプライン側を demand/supply へ統一し、既存列は参照のみ。

## スケジュール（目安）
- Phase 0–1: 1.5日
- Phase 2–3: 1.5日
- Phase 4–5: 1.5日
- 合計: 4.5日（辞書作成の粒度により±1日）

## 体制・役割
- データ正規化/辞書設計: Data Eng（本修正）
- パイプライン組み込み/回帰: Data Eng
- アプリ受け入れ: App Eng（最小差分）
- 品質検証/受入: QA/Data Analyst

## 変更管理
- ブランチ: `feature/normalization-layer`
- PR: 2本（レイヤ実装、パイプライン組み込み）
- CI: 単体/回帰/Notebook（抽出率・未マッチ）

