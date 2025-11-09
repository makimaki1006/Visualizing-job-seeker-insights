# ジョブメドレープロジェクト v2.1 クイックスタートガイド

**最終更新**: 2025年10月28日
**対象**: 新規担当者、引き継ぎ担当者

---

## 1分で理解する

### このプロジェクトは何をするの？

ジョブメドレーの求職者データ（CSV）を分析して、以下を出力します：

- 市区町村別の人材需要マップ
- ペルソナ分析（5つのセグメント）
- 統計分析（カイ二乗検定、ANOVA）
- フロー分析（地域間の人材移動）
- 高度分析（人材供給密度、資格分布など5種類）
- キャリア・学歴分析
- 転職意欲・緊急度分析

### すぐに実行する

```bash
cd "C:\Users\fuji1\OneDrive\Pythonスクリプト保管\job_medley_project\python_scripts"
python run_complete_v2.py
```

→ GUIでCSVを選択 → 完了（32ファイル生成）

---

## 5分で理解する

### 入力データ

**場所**: `C:\Users\fuji1\OneDrive\Pythonスクリプト保管\out\results_20251027_180947.csv`

**形式**: 13カラム（page, card_index, age_gender, location, member_id, status, desired_area, desired_workstyle, desired_start, career, employment_status, desired_job, qualifications）

**データ量**: 7,487行

### 出力データ

**場所**: `job_medley_project\data\output_v2\`

**ファイル数**: 32ファイル（7つのPhase + 統合レポート）

**品質スコア**: 82.86/100 (EXCELLENT) ✅

### Phase一覧

| Phase | 内容 | ファイル数 | 品質 |
|-------|------|----------|------|
| Phase 1 | 基礎集計 | 4 | 82.0/100 |
| Phase 2 | 統計分析 | 3 | 85.0/100 |
| Phase 3 | ペルソナ分析 | 3 | 77.5/100 |
| Phase 6 | フロー分析 | 4 | 70.0/100 |
| Phase 7 | 高度分析 | 6 | 50.0/100 |
| Phase 8 | キャリア・学歴 | 6 | 70.0/100 |
| Phase 10 | 転職意欲・緊急度 | 6 | 90.0/100 |

---

## 10分で理解する

### ファイル構成

```
job_medley_project/
├── python_scripts/
│   ├── run_complete_v2.py          ← メインスクリプト（1,500行）
│   ├── data_normalizer.py          ← データ正規化（表記ゆれ対応）
│   └── data_quality_validator.py   ← 品質検証
│
├── data/
│   └── output_v2/                  ← 出力先（32ファイル）
│       ├── phase1/
│       ├── phase2/
│       ├── phase3/
│       ├── phase6/
│       ├── phase7/
│       ├── phase8/
│       ├── phase10/
│       └── OverallQualityReport_Inferential.csv
│
└── docs/
    ├── HANDOVER_v2.1_COMPLETE.md   ← 詳細引き継ぎ書（このドキュメント）
    ├── QUICKSTART_v2.1.md          ← このファイル
    └── DATA_USAGE_GUIDELINES.md    ← データ利用ガイドライン
```

### 実装済み機能（v2.1）

✅ **Phase 1-10の完全実装**（Phase 4, 5, 9は仕様上存在せず）
✅ **データ品質検証システム**（観察的記述 vs 推論的考察）
✅ **表記ゆれ自動正規化**（キャリア、学歴、希望職種など）
✅ **新データ形式対応**（13カラム簡易CSV）
✅ **統合品質レポート**（82.86/100）

### 未実装機能

❌ **Phase 1.5（ジオコーディング）**: Google Maps API統合が必要
❌ **GASとの完全連携テスト**: Phase 2, 3, 6のGAS側可視化が未確認

---

## トラブルシューティング

### Q1: エラーが出た

**A1**: まずエラーメッセージを確認
- `FileNotFoundError` → 入力CSVのパスを確認
- `TypeError: Cannot setitem` → 既に修正済み（最新版を使用）
- 警告（FutureWarning, UserWarning） → 無視して問題なし

### Q2: 出力ファイルが生成されない

**A2**: 実行ログを確認
- 各Phaseの「[OK]」表示を確認
- エラーメッセージがある場合は内容をコピー

### Q3: 品質スコアが低い

**A3**: 正常な場合もある
- 50点以上（ACCEPTABLE）は使用可能
- 50点未満の場合はデータ追加を検討

### Q4: 新しいCSVファイルを処理したい

**A4**: GUIで選択するだけ
- ファイル形式（13カラム）が一致していれば自動処理

---

## 次のステップ

### すぐにやること

1. ✅ `run_complete_v2.py`を実行して動作確認
2. ✅ `data/output_v2/`の32ファイルを確認
3. ✅ 品質レポート（QualityReport_*.csv）を確認

### 後でやること

1. 📋 GASとの連携テスト（Phase 2, 3, 6の可視化確認）
2. 📋 Phase 1.5（ジオコーディング）の実装検討
3. 📋 新しいデータでの再実行テスト

### 困ったら読むドキュメント

| ドキュメント | 用途 |
|------------|------|
| `HANDOVER_v2.1_COMPLETE.md` | 詳細な引き継ぎ情報（技術詳細・エラー対処） |
| `README.md` | プロジェクト全体の概要 |
| `DATA_USAGE_GUIDELINES.md` | データ品質検証の使い方 |
| `.claude/CLAUDE.md` | Claude Codeの設定・履歴 |

---

## 重要な注意事項

### データパス

**必ず確認**: 入力データは`C:\Users\fuji1\OneDrive\Pythonスクリプト保管\out\results_20251027_180947.csv`

**間違えやすい**: 古い`data/input/`は削除済み（使用不可）

### 品質検証の理解

- **観察的記述（Descriptive）**: 事実を記述（Phase 1）
- **推論的考察（Inferential）**: 傾向を分析（Phase 2, 3, 6, 7, 8, 10）

**重要**: Phase 1のデータでも、「1件だから○○が多い傾向」とは言えない

### 実行時間

- 通常: 約2-3分
- データ量7,487行の場合: 約5分

---

## 連絡先

### 質問がある場合

1. まずこのドキュメントを確認
2. `HANDOVER_v2.1_COMPLETE.md`を確認
3. エラーメッセージとログを添えて報告

### よくある質問（FAQ）

**Q: Phase 2のカイ二乗検定結果が0件なのは正常ですか？**
→ A: はい、データに有意な関連性がないため正常です

**Q: Phase 7の品質スコアが50点なのは問題ですか？**
→ A: いいえ、警告付きで使用可能な範囲です

**Q: GASとの連携はどうすればいいですか？**
→ A: `GAS_COMPLETE_FEATURE_LIST.md`を参照してください

---

## 作業履歴サマリー

### 2025年10月28日

- ✅ Phase 2（統計分析）実装
- ✅ Phase 3（ペルソナ分析）実装
- ✅ Phase 6（フロー分析）実装
- ✅ Phase 7（高度分析）実装
- ✅ Categorical型エラー修正
- ✅ 統合テスト成功（32ファイル生成）
- ✅ ドキュメント更新（HANDOVER, CLAUDE.md）

### 次回作業予定

- Phase 1.5（ジオコーディング）実装
- GAS連携テスト（Phase 2, 3, 6）
- 新データでの動作確認

---

**このガイドで分からないことがあれば、`HANDOVER_v2.1_COMPLETE.md`を参照してください。**

**End of Quick Start Guide**
