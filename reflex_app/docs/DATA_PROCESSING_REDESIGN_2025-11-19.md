# データ加工再設計ガイド（2025-11-19）

## 背景と目的
- 目的: 可視化（ダッシュボード）に適した一貫性あるデータを生成するため、run_complete_v2_perfect.py 側の加工ロジックを「正規化→分解→集約」に再設計する。
- 背景: 元データは表記ゆれ・複数指定・日付付きの主観情報など、加工後にまとめる必要が大きい。可視化側だけで吸収するのは限界があるため、パイプラインでの正規化を第一責務とする。
- 現状の品質: フェーズ別品質スコアより、Phase 3（ペルソナ）・Phase 10（緊急度）が 40/100（記述専用）、Phase 6/7/8/12/13/14 は 60〜80 台で実用的。観察的記述の範囲を明示しつつ、加工品質を底上げする。

## 設計方針（負債を増やさない）
- 正規化レイヤの一元化: normalization.py を追加し、読み込み直後（Phase 0）と最終統合直前で適用。
- 外部辞書管理: `python_scripts/dims/*.csv` に語彙を集約（追加はCSV追記で完結）。
- 追跡性: 元列は残し、正規化列を追加（`*_norm` ではなく意味的な新列名）。解析困難はフラグ付け（confidence/stale/unknown）。
- 互換性: 既存 row_type は維持。必要に応じて DETAIL 系 row_type を追加（アプリは未知 row_type を無視可能）。

## 外部辞書（例）
- dims/job_titles.csv: `canonical,display,synonyms`
- dims/qualifications.csv: `canonical,display,family,national,synonyms`
- dims/education_levels.csv: `canonical,display,synonyms,rank`
- dims/workstyle.csv: `canonical,display,synonyms,superclass`
- dims/fields.csv（専攻）: `canonical,display,synonyms`

## 正規化プリミティブ（共通）
- Unicode NFKC 正規化、全角空白→半角、前後空白除去、区切り記号統一（・ ･ · ／ / | , など→「,」や「・」に統一）、括弧類の統一。
- 真偽値標準化: '1/0/true/false/yes/no' → 'True'/'False'（文字列運用）
- 比率列の正規化: '65%'/'65'/0.65 → 0.65（0〜1）

## 項目別ロジック
### 1) career（学歴/専攻/卒年）
- ねらい: 学歴レベル・専攻・卒年（任意）を抽出。欠損・表記ゆれ許容。confidence を付与。
- レベル判定: 辞書（高校/高等学校→high_school、短大→junior_college、大学→university、大学院→graduate、専門学校→vocational、…）。
- 卒年抽出: 正規表現で (19|20)\d{2} を中心に「卒」付近のパターンも許容。無ければ None。
- 専攻: “学部|学科|専攻|コース” 近傍語を辞書で正規化（例: 農業土木→agri_civil）。
- 出力列: `education_level_code`, `education_field_code`, `graduation_year`, `edu_confidence`（high|medium|low）。

### 2) experienced_job（経験職種）
- ねらい: 旧 desired_job の誤解を是正。職種×経験年数を分解・正規化（複数カンマ対応）。
- 抽出: トークン毎に「職種名」「期間(10年以上|5年未満|1年未満|N年)」。期間は月数に換算（“未満”は区間カテゴリも保持）。
- 職種名: 辞書（介護職/ヘルパー→kaigo_helper、サービス提供責任者→sv_provider、管理職（介護）→kaigo_manager、…）。
- 出力列: `experienced_jobs_json`（list[{job_code, months, bucket}]）、`experienced_job_primary`（最長）、`experienced_months_max`。

### 3) qualifications（保有資格の詳細化）
- ねらい: 国家資格の丸めから詳細コードへ。複数カンマ対応、family/national 属性を保持。
- 抽出: トークン毎に辞書マップ（例: care_worker/看護師/准看護師/実務者研修/初任者研修/運転免許…）。
- 出力列: `qualifications_codes_json`（list[{code,family,national}]）、`has_national`（bool）、`qual_counts_by_family_json`、`qualification_other_text`（未知の保持）。

### 4) desired_workstyle（希望勤務形態）
- ねらい: 「正職員/契約職員/パート・バイト」等を辞書で正規化し、複数指定を配列化。上位カテゴリ（常勤/非常勤）射影も可能。
- 出力列: `workstyle_codes`（list）、`workstyle_primary`。

### 5) desired_start（転職希望時期＋基準日）
- ねらい: バケット(now/<=3m/consider/unknown) と基準日抽出、stale 判定（例: 90日超）。
- 出力列: `desired_start_bucket`, `desired_start_asof`, `desired_start_stale`。

## row_type 拡張（将来の可視化用）
- 既存 row_type は維持。必要に応じて以下の DETAIL を追加可能：
  - `EXPERIENCE_DETAIL`: category1=job_code, category2=experience_bucket（'<1y','1-5y','>=10y' 等）, count。
  - `QUALIFICATIONS_DETAIL`: category1=qualification_code, category2=family, category3='national'/'non', count。
  - `EDUCATION_SUMMARY`: category1=education_level_code, category2=graduation_decade（'2010s' 等）, count。

## アプリ側の受け入れ
- 既存の可視化は row_type ベースのため互換性あり。新しい DETAIL 系は将来的にタブ追加で拡張可能。
- 低品質フェーズ（Phase 3/10）に由来する可視化は「観察的記述専用」の注記を常備。将来は統合CSVに `quality_flag` 列を持ち込み、注記の自動化を推奨。
- 既に横棒向け `layout="vertical"`、ランキングの前集約、Unicode/比率正規化はアプリ側で実施済み。

## 検証（品質メトリクス）
- 抽出率: 卒年・教育レベル・職種コード・経験年数・資格コード。
- 非マッチ率: 各辞書の未マッチ語彙の頻度表（辞書更新ループに供する）。
- 値域チェック: 比率 0–1、count 非負、`gap ≈ demand - supply` の整合。
- 回帰: 主要 row_type の件数差（導入前後の比較）と代表チャートの再現性。

## リスクと対応
- 過度な重複削除: PERSONA/RARITY のキー設計を明文化（prefecture/municipality/row_type/category1/2/3）。
- 定義ズレ: 需給比率は demand/supply へ統一。既存列が異なる場合は再計算列を優先。
- 解析不能: `*_confidence`/`*_stale`/`*_unknown` を付与し、落とさず保全。

---

# 参考：run_complete_v2_perfect.py への組み込み指針
1. NORMALIZE ブロック直後に `normalization.normalize_master(df, dims_dir)` を呼び、新列を追加。
2. 統合前に正規化列を優先して row_type 生成に使用（従来列はフォールバック）。
3. 統合CSVに DETAIL 系 row_type を追加（任意）。既存 row_type はそのまま。
4. Notebook/pytest による自動検証（抽出率/非マッチ/値域/回帰）。

