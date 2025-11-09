# 地域別ダッシュボード構築計画（2025-10-29版）

本ドキュメントは「地図またはプルダウンで地域を選択し、Phase1/2/3/7/8/10 の分析結果をタブ形式で確認できる UI」を実現するための仕様と進め方をまとめたものです。今回のレビュー結果を反映し、これを確定版の設計書とします。

---

## 0. 目的と前提

### 目的
1. 地図（マーカークリック）または HTML プルダウンで都道府県 → 市区町村を選択できること。  
2. 選択した地域に対して、Phase1/2/3/7/8/10 の指標を同一 UI 上のタブで切り替えながら閲覧できること。  
3. Phase3（ペルソナ分析）タブでは、クラスタや属性をさらに絞り込むと、難易度をレベル表現で即時表示できること。

### データ前提
- Python 側で出力済みの CSV（`data/output_v2/` 配下）で必要なデータはすべて揃っている。追加の CSV 出力は不要。  
- 観察モードの品質レポートは `P1_QualityReport.csv`, `P8_QualityReport.csv`, `P10_QualityReport.csv`, `OverallQualityReport.csv` などのプレフィックス付きファイル名で利用可能。  
- Phase10 では、新たに市区町村単位の 2 次集計ファイル（`UrgencyDistribution_ByMunicipality.csv`, `UrgencyAgeCross_ByMunicipality.csv`, `UrgencyEmploymentCross_ByMunicipality.csv`, `UrgencyDesiredWorkCross.csv`）を生成済み。GAS 側での再集計は不要。

### 制約・配慮事項
- GAS の実行時間、呼び出し頻度、UI 応答性を考慮して設計する。  
- 既存メニュー（Phase7 ダッシュボード等）との共存を意識し、既存機能に副作用を与えない。

---

## 1. 情報整理（フェーズ1）

1. **フェーズ別データ要件**  
   - Phase1: `MapMetrics`, `AggDesired`, `P1_QualityReport` など地域単位で取得。  
   - Phase2: `ChiSquareTests`, `ANOVATests`, `P2_QualityReport_Inferential`（必要に応じて地域列との紐づけ方法を明確化）。  
   - Phase3: `PersonaSummary`, `PersonaDetails`、難易度レベル算出に必要な属性列。  
   - Phase7: `SupplyDensityMap`, `QualificationDistribution`, `AgeGenderCrossAnalysis`, `MobilityScore`, `DetailedPersonaProfile`, `P7_QualityReport_Inferential`。  
   - Phase8: `EducationDistribution`, `EducationAgeCross`, `EducationAgeCross_Matrix`, `GraduationYearDistribution`, `P8_QualityReport`, `P8_QualityReport_Inferential`。  
   - Phase10: `UrgencyDistribution.csv`（全体）、`*_ByMunicipality.csv`（市区町村別）、`P10_QualityReport`, `P10_QualityReport_Inferential`。

2. **UI ワイヤーフレーム（文章による仕様）**  
   - 画面上部に地域選択コンポーネントを配置。  
     - 都道府県セレクトボックス → Ajax で市区町村候補を取得。  
     - 選択中の地域の表示、MapVisualization からの選択を反映。  
   - 画面下部にタブメニュー（Phase1, Phase2, Phase3, Phase7, Phase8, Phase10）。  
   - 各タブは以下を表示：  
     - 指標カード（件数、割合、警告など）  
     - 詳細テーブル（品質フラグ含む）  
     - 必要に応じてチャート（Google Charts 等）。  
   - Phase3 タブには追加で属性フィルター（クラスタ、年齢帯など）と難易度レベル表示を実装。

3. **状態管理仕様**  
   - `PropertiesService.getUserProperties()` を用いて `lastSelectedPrefecture`, `lastSelectedMunicipality` を保存・取得。  
   - MapVisualization でマーカーをクリックした際にこれらプロパティを更新。  
   - ダッシュボード読み込み時にプロパティを参照して初期選択状態に反映。

4. **既存機能との連携**  
   - MapVisualization から新ダッシュボードに遷移できる導線（メニューまたはダイアログ内のリンク）を追加。  
   - Upload_Bulk37.html / QualityDashboard への影響は最小限とし、既存ファイル命名規則に合わせてインポート済み。

5. **ドキュメント**  
   - 本仕様書を最新状態に保ち、レビュー完了後は各実装フェーズで参照可能なよう README などからリンクする。

---

## 2. バックエンド（GAS）設計（フェーズ2）

1. **データ取得 API 設計**  
   - `fetchPhase1Metrics(pref, muni)`、`fetchPhase3Persona(pref, muni, cluster)` 等の関数を `RegionDashboard.gs`（新規）として実装。  
   - 戻り値は JSON 形式（テーブル用データ、指標サマリー、品質情報等を含む）。

2. **共通ユーティリティ**  
   - 都道府県→市区町村リストを作成（`MapMetrics` から抽出 or Python 側でマスタ CSV を用意）。  
   - `RegionStateService`（仮）を作成し、`saveSelectedRegion`, `loadSelectedRegion` を提供。

3. **フェーズ別処理**  
   - Phase1: `MapMetrics`, `AggDesired`, `P1_QualityReport` から直接フィルタ。  
   - Phase2: 統計検定結果と地域の紐づけ方法（必要なら補助テーブルを作成）。  
   - Phase3: ペルソナ指標と難易度の計算ロジックを関数化。  
   - Phase7/8/10: `_ByMunicipality` 系ファイルを使用し、GAS 側では再計算せず抽出のみ。  
   - 品質レポート（観察／推論）を併せて返却し、UI で警告表示に利用。

4. **パフォーマンス検証**  
   - 代表的な市区町村で連続呼び出しを行い、GAS 実行時間・クォータ内に収まることを確認。  
   - 必要ならキャッシュ利用（`CacheService`）も検討。

---

## 3. フロントエンド（HTML / JS）設計（フェーズ3）

1. **地域選択 UI**  
   - 都道府県セレクトの変更 → 市区町村セレクトを更新 → 選択結果を `saveSelectedRegion` に保存。  
   - MapVisualization で選択された地域を渡す導線を用意し、UI 側でも反映（状態同期）。

2. **タブ UI**  
   - タブ切替時に対応する GAS 関数を呼び出し、取得したデータで DOM を更新。  
   - 初回表示時にすべてのデータを取得するか、タブ切替時に都度取得するかを選択（パフォーマンスと UX のバランスを見て決定）。

3. **表示コンポーネント**  
   - 指標カード（件数、割合、警告）  
   - データテーブル（品質フラグ付き）  
   - チャート（必要に応じて Google Charts など）  
   - 空データや CRITICAL 警告時の表示（メッセージやアイコン）を統一。

4. **Phase3 特有機能**  
   - 属性フィルター（クラスタ、希望職種など）を提供し、難易度レベルを算出・表示。  
   - 難易度レベルは 5 段階など定義を明確にし、UI 上では色やバッジで示す。

---

## 4. テストとドキュメンテーション（フェーズ4）

1. **動作テスト**  
   - 地域選択 → タブ切替 → Phase3 属性フィルタ → 難易度表示の一連操作を検証。  
   - MapVisualization からの導線、最新選択の反映動作も確認。  
   - CSV の実データと表示値が一致しているか（スポットでファクトチェック）。

2. **性能・制限テスト**  
   - GAS 実行時間、スプレッドシートの描画速度を測定。  
   - 想定ユーザー数（同時アクセス）で支障がないか確認し、必要に応じてキャッシュやロード制御を導入。

3. **ドキュメント**  
   - README などに新 UI の操作手順を追記。  
   - `MAP_WORKFLOW_IMPROVEMENT_PLAN.md` に実装状況や既知の課題をアップデート。

---

## 5. リリース準備（フェーズ5）

1. **コードレビュー**  
   - バックエンド（GAS）とフロントエンド（HTML/JS）双方をレビューし、命名規則・エラーハンドリング・可読性を確認。

2. **段階的リリース**  
   - 必要に応じて Phase7 → 他フェーズ → Phase1 の順で段階導入し、利用ユーザーからフィードバックを得る。

3. **運用メモ**  
   - 既知の注意点、問い合わせFAQ、ログの見方などをまとめ、関係者と共有。

---

## 6. 今後の拡張・メモ

- 都道府県 → 市区町村のリストを定期更新する場合は、Python 側でマスタ CSV を出力しておくと GAS 側での候補生成が容易。  
- 今後、複数地域比較や PDF 出力へ発展させる場合、本ダッシュボードのコンポーネントを再利用できるよう意識する。  
- パフォーマンスが課題となった場合、キャッシュ化や事前集計の増加、UI の Lazy Load などを検討する。

---

以上が確定版の設計書です。次フェーズでは、この仕様に基づいて実装・テストを進めます。
