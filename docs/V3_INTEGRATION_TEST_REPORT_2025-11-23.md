# V3 CSV生成パイプライン統合テストレポート

**実施日**: 2025年11月23日
**テスト実行**: run_complete_v3.py --input results_20251119_073325.csv
**ステータス**: ✅ 成功（Phase 1-14すべて完了）

---

## テスト結果サマリー

### 全Phase成功

**実行Phase**: 10フェーズ（Phase 1, 2, 3, 6, 7, 8, 10, 12, 13, 14）
**生成ファイル**: 54 CSVファイル
**出力先**: `reflex_app/python_scripts/data/output_v2/`
**統合品質スコア**: 全カラムDESCRIPTIVE（警告なし）

---

## Phase別実行結果

| Phase | 説明 | ファイル数 | 品質スコア | ステータス | 注記 |
|-------|------|-----------|-----------|----------|------|
| **Phase 1** | 基礎集計 | 11 | - | ✅ 成功 | Applicants, DesiredWork, AggDesired等 |
| **Phase 2** | 統計分析 | 3 | - | ✅ 成功 | ChiSquare, ANOVA |
| **Phase 3** | ペルソナ分析 | 4 | - | ✅ 成功 | PersonaSummary, PersonaDetails |
| **Phase 6** | フロー分析 | 5 | - | ✅ 成功 | MunicipalityFlow, ProximityAnalysis |
| **Phase 7** | 高度分析 | 6 | - | ✅ 成功 | SupplyDensity, AgeGenderCross等 |
| **Phase 8** | キャリア・学歴分析 | 6 | 73.8/100 | ✅ 成功 (GOOD) | CareerDistribution, GraduationYear |
| **Phase 10** | 転職意欲・緊急度 | 10 | 40.0/100 | ⚠️ 観察的記述専用 (POOR) | UrgencyDistribution, UrgencyCross |
| **Phase 12** | 需給ギャップ分析 | 3 | 70.0/100 | ✅ 成功 (GOOD) | SupplyDemandGap |
| **Phase 13** | 希少性スコア | 3 | 80.9/100 | ✅ 成功 (EXCELLENT) | RarityScore |
| **Phase 14** | 競合分析 | 3 | 70.0/100 | ✅ 成功 (GOOD) | CompetitionProfile |

**合計**: 54ファイル生成

---

## Phase 8詳細（キャリア・学歴分析）

**品質スコア**: 73.8/100 (GOOD)

**生成ファイル**:
1. CareerDistribution.csv - 7,029件
2. CareerAgeCross.csv - 11,146件
3. CareerAgeCross_Matrix.csv - 7,029行 x 6列
4. GraduationYearDistribution.csv - 74件
5. P8_QualityReport_Inferential.csv
6. P8_QualityReport.csv

**評価**: 推論的考察に十分な品質

---

## Phase 10詳細（転職意欲・緊急度分析）

**品質スコア**: 40.0/100 (POOR)

**生成ファイル**:
1. UrgencyDistribution.csv - 4件
2. UrgencyAgeCross.csv - 24件
3. UrgencyAgeCross_Matrix.csv - 4行 x 6列
4. UrgencyEmploymentCross.csv - 11件
5. UrgencyEmploymentCross_Matrix.csv - 4行 x 3列
6. UrgencyByMunicipality.csv - 1,423件
7. UrgencyAgeCross_ByMunicipality.csv - 6,055件
8. UrgencyEmploymentCross_ByMunicipality.csv - 3,163件
9. P10_QualityReport_Inferential.csv
10. P10_QualityReport.csv

**警告**:
- 品質スコア40.0/100（POOR）のため推論的考察には使用不可
- **観察的記述のみ使用可能**（件数、平均値などの記述）
- 自動的に選択肢1（観察的記述専用）で保存

**評価**: データ数不足のため傾向分析には適さない、事実記述のみ使用

---

## Phase 12詳細（需給ギャップ分析）

**品質スコア**: 70.0/100 (GOOD)

**生成ファイル**:
1. SupplyDemandGap.csv - 1,452件
2. P12_QualityReport_Descriptive.csv
3. P12_QualityReport.csv

**評価**: 観察的記述に十分な品質

---

## Phase 13詳細（希少性スコア）

**品質スコア**: 80.9/100 (EXCELLENT)

**生成ファイル**:
1. RarityScore.csv - 10,905件
2. P13_QualityReport_Descriptive.csv
3. P13_QualityReport.csv

**評価**: 優れた品質、観察的記述に最適

---

## Phase 14詳細（競合分析）

**品質スコア**: 70.0/100 (GOOD)

**生成ファイル**:
1. CompetitionProfile.csv - 1,423件
2. P14_QualityReport_Descriptive.csv
3. P14_QualityReport.csv

**評価**: 観察的記述に十分な品質

---

## 統合品質レポート

**ファイル**: `OverallQualityReport.csv`, `OverallQualityReport_Inferential.csv`

**総カラム数**: 30+カラム（すべてDESCRIPTIVEレベル）

**主要カラム品質**:
- prefecture: 34,685件（48都道府県、警告なし）
- municipality: 51,446件（2,861市区町村、警告なし）
- applicant_id: 472,266件（57,793ユニーク、警告なし）
- age_group: 118,877件（6グループ、警告なし）
- gender: 353,247件（2種類、警告なし）
- employment_status: 78,419件（3種類、警告なし）

**結果**: すべてのデータカラムが観察的記述に適した品質レベル

---

## 検出された問題

### 1. V2パターンデータ生成エラー

**エラー内容**: `ValueError: I/O operation on closed file`

**発生箇所**:
- run_complete_v3.py:77（パターンデータ生成開始メッセージ）
- run_complete_v3.py:88（警告メッセージ）
- run_complete_v3.py:104（エラーメッセージ）

**影響範囲**: V2パターンデータ生成（DESIRED_AREA_PATTERN）のみ
**メインPhase影響**: なし（Phase 1-14はすべて成功）

**原因分析**:
- stdoutがすでにクローズされた状態でprint()実行
- 非対話モードでの標準出力処理に問題

**修正推奨**: stdoutチェック処理の追加

```python
# 修正案
if not sys.stdout.closed:
    print("[V2] DESIRED_AREA_PATTERN生成...")
```

---

## Prefecture Extraction Bug修正の効果

**修正内容**: desired_prefectureカラム優先 + 正規表現フォールバック

**影響ファイル**:
- python_scripts/generate_mobility_pattern.py
- python_scripts/generate_residence_flow.py

**修正効果**:
- データ損失リスク解消 ✅
- 後方互換性維持 ✅
- 両データ形式対応（カラムあり/なし）✅

**テスト結果**:
- generate_mobility_pattern.py: 3,670行生成（成功）
- generate_residence_flow.py: 正常にフロー統計生成（成功）

---

## 推奨次アクション

### 優先度：高

1. **V2パターンデータ生成バグ修正**
   - run_complete_v3.py:77, 88, 104のstdoutチェック追加
   - 非対話モード対応の改善

2. **Phase 10データ補完**
   - 転職意欲・緊急度データの追加収集
   - 品質スコア40.0→60.0以上への改善

### 優先度：中

3. **ドキュメント更新**
   - README.mdにPhase 8-14の説明追加
   - DATA_USAGE_GUIDELINES.mdにPhase 10の注意事項追加

4. **データ品質モニタリング**
   - 定期的なOverallQualityReport確認
   - 品質スコア推移の追跡

### 優先度：低

5. **統合テスト自動化**
   - Phase 1-14の自動テストスクリプト作成
   - 品質スコア閾値チェック

---

## 結論

V3 CSV生成パイプライン統合テストは**成功**しました。

**成功要因**:
- 全10Phase（Phase 1, 2, 3, 6, 7, 8, 10, 12, 13, 14）が正常実行
- 54個のCSVファイル生成
- Prefecture extraction bug修正により データ損失リスク解消
- 品質検証システムが正常動作（Phase 10の低品質を正しく検出）

**注意事項**:
- Phase 10は観察的記述専用（品質スコア40.0/100）
- V2パターンデータ生成でstdoutエラー（修正推奨）

**総合評価**: ✅ 本番運用可能レベル（Phase 10除く）

---

**作成**: Claude Code
**日付**: 2025年11月23日
**プロジェクト**: ジョブメドレー求職者データ分析 V3 CSV拡張
**テスト入力**: results_20251119_073325.csv
**テスト実行時間**: 約5分（推定）
