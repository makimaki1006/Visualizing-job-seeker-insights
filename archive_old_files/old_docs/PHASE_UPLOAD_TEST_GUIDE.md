# Phase別一括アップロード機能テストガイド

**作成日**: 2025年10月27日
**対象**: 全Phase（Phase 1, 2, 3, 6, 7）のCSVアップロード機能
**所要時間**: 約5分

---

## 📋 概要

### 実装内容

各Phase（Phase 1, 2, 3, 6, 7）ごとに**個別のCSV一括アップロード機能**を実装しました。

| Phase | ファイル数 | CSVファイル |
|-------|----------|-----------|
| **Phase 1** | 4 | MapMetrics, Applicants, DesiredWork, AggDesired |
| **Phase 2** | 2 | ChiSquareTests, ANOVATests |
| **Phase 3** | 2 | PersonaSummary, PersonaDetails |
| **Phase 6** | 3 | MunicipalityFlowEdges, MunicipalityFlowNodes, ProximityAnalysis |
| **Phase 7** | 7 | SupplyDensityMap, QualificationDistribution, AgeGenderCrossAnalysis, MobilityScore, DetailedPersonaProfile, PersonaMapData, PersonaMobilityCross |

**合計**: 18ファイル

---

## 🚀 デプロイ手順

### 必要なGASファイル（3ファイル）

| ファイル | 操作 | パス |
|---------|------|------|
| **UniversalPhaseUploader.gs** | ➕ 新規追加 | `gas_files/scripts/` |
| **PhaseUpload.html** | ➕ 新規追加 | `gas_files/html/` |
| **CompleteMenuIntegration.gs** | ✏️ 既存の `MenuIntegration.gs` に上書き | `gas_files/scripts/` |

### デプロイ手順

1. **Apps Scriptエディタを開く**:
   - Googleスプレッドシート > 拡張機能 > Apps Script

2. **UniversalPhaseUploader.gs を追加**:
   - **+** ボタン > スクリプト
   - ファイル名: `UniversalPhaseUploader`
   - 以下のファイルの内容を全てコピー:
     ```
     C:\Users\fuji1\OneDrive\Pythonスクリプト保管\job_medley_project\gas_files\scripts\UniversalPhaseUploader.gs
     ```

3. **PhaseUpload.html を追加**:
   - **+** ボタン > HTML
   - ファイル名: `PhaseUpload`
   - 以下のファイルの内容を全てコピー:
     ```
     C:\Users\fuji1\OneDrive\Pythonスクリプト保管\job_medley_project\gas_files\html\PhaseUpload.html
     ```

4. **MenuIntegration.gs を更新**:
   - 既存の `MenuIntegration.gs` を開く
   - 以下のファイルの内容を全てコピーして上書き:
     ```
     C:\Users\fuji1\OneDrive\Pythonスクリプト保管\job_medley_project\gas_files\scripts\CompleteMenuIntegration.gs
     ```
   - **重要**: 関数名が `onOpen()` のままであることを確認（変更不要）

5. **保存とリロード**:
   - ファイル > すべてを保存
   - Googleスプレッドシートをリロード（F5）

---

## 📊 テスト手順

### ステップ1: メニュー確認

Googleスプレッドシートのメニューバーで以下を確認:

```
📊 データ処理
  ├── 📥 データインポート
  │   ├── 📍 Phase 1: 基礎集計（4ファイル）
  │   ├── 📊 Phase 2: 統計分析（2ファイル）
  │   ├── 👥 Phase 3: ペルソナ分析（2ファイル）
  │   ├── 🌊 Phase 6: フロー分析（3ファイル）
  │   ├── 📈 Phase 7: 高度分析（7ファイル）
  │   └── ✅ 全Phaseアップロード状況
  ├── 📈 Phase 7高度分析
  │   └── ...
  └── ...
```

**確認ポイント**:
- [ ] 「📥 データインポート」サブメニューが表示される
- [ ] Phase 1〜7のメニュー項目が表示される
- [ ] 各項目にファイル数が表示される

---

### ステップ2: Phase 1アップロードテスト（4ファイル）

#### 2-1. ダイアログ起動

メニュー: **📊 データ処理** > **📥 データインポート** > **📍 Phase 1: 基礎集計（4ファイル）**

#### 2-2. ダイアログ表示確認

**ダイアログタイトル**: `📍 Phase 1: 基礎集計 - データアップロード`

**ファイルエリア確認（4個）**:
- [ ] 📄 地図メトリクス
- [ ] 📄 応募者情報
- [ ] 📄 希望勤務地
- [ ] 📄 集計データ

#### 2-3. ファイル選択

以下のファイルを選択（ドラッグ&ドロップまたはクリック）:

| エリア | ファイル名 | パス |
|--------|-----------|------|
| 地図メトリクス | MapMetrics.csv | `gas_output_phase1/` |
| 応募者情報 | Applicants.csv | `gas_output_phase1/` |
| 希望勤務地 | DesiredWork.csv | `gas_output_phase1/` |
| 集計データ | AggDesired.csv | `gas_output_phase1/` |

**確認ポイント**:
- [ ] ファイル選択後、エリアが緑色に変わる
- [ ] 「✅ 選択済み」と表示される
- [ ] ファイル名が表示される
- [ ] サマリーエリアに「4 / 4」と表示される

#### 2-4. アップロード実行

1. **「🚀 アップロード開始」** ボタンをクリック
2. プログレスバーが表示される
3. 完了メッセージ「✅ 4ファイルのアップロードが完了しました！」を確認

#### 2-5. シート確認

Googleスプレッドシート下部のシートタブで以下の4シートが作成されていることを確認:

- [ ] `MapMetrics`
- [ ] `Applicants`
- [ ] `DesiredWork`
- [ ] `AggDesired`

**各シートの確認ポイント**:
- [ ] ヘッダー行が太字・グレー背景
- [ ] データ行が存在する
- [ ] 列幅が自動調整されている

---

### ステップ3: Phase 2アップロードテスト（2ファイル）

#### 3-1. ダイアログ起動

メニュー: **📊 データ処理** > **📥 データインポート** > **📊 Phase 2: 統計分析（2ファイル）**

#### 3-2. ファイル選択

| エリア | ファイル名 | パス |
|--------|-----------|------|
| カイ二乗検定 | ChiSquareTests.csv | `gas_output_phase2/` |
| ANOVA検定 | ANOVATests.csv | `gas_output_phase2/` |

#### 3-3. アップロード実行

**確認ポイント**:
- [ ] サマリーに「2 / 2」と表示される
- [ ] 完了メッセージ「✅ 2ファイルのアップロードが完了しました！」

#### 3-4. シート確認

- [ ] `ChiSquareTests`
- [ ] `ANOVATests`

---

### ステップ4: Phase 3アップロードテスト（2ファイル）

#### 4-1. ダイアログ起動

メニュー: **📊 データ処理** > **📥 データインポート** > **👥 Phase 3: ペルソナ分析（2ファイル）**

#### 4-2. ファイル選択

| エリア | ファイル名 | パス |
|--------|-----------|------|
| ペルソナサマリー | PersonaSummary.csv | `gas_output_phase3/` |
| ペルソナ詳細 | PersonaDetails.csv | `gas_output_phase3/` |

#### 4-3. シート確認

- [ ] `PersonaSummary`
- [ ] `PersonaDetails`

---

### ステップ5: Phase 6アップロードテスト（3ファイル）

#### 5-1. ダイアログ起動

メニュー: **📊 データ処理** > **📥 データインポート** > **🌊 Phase 6: フロー分析（3ファイル）**

#### 5-2. ファイル選択

| エリア | ファイル名 | パス |
|--------|-----------|------|
| フローエッジ | MunicipalityFlowEdges.csv | `gas_output_phase6/` |
| フローノード | MunicipalityFlowNodes.csv | `gas_output_phase6/` |
| 移動パターン分析 | ProximityAnalysis.csv | `gas_output_phase6/` |

#### 5-3. シート確認

- [ ] `MunicipalityFlowEdges`
- [ ] `MunicipalityFlowNodes`
- [ ] `ProximityAnalysis`

---

### ステップ6: Phase 7アップロードテスト（7ファイル）

#### 6-1. ダイアログ起動

メニュー: **📊 データ処理** > **📥 データインポート** > **📈 Phase 7: 高度分析（7ファイル）**

#### 6-2. ファイル選択

| エリア | ファイル名 | パス |
|--------|-----------|------|
| 人材供給密度 | SupplyDensityMap.csv | `job_medley_project/gas_output_phase7/` |
| 資格分布 | QualificationDistribution.csv | `job_medley_project/gas_output_phase7/` |
| 年齢×性別 | AgeGenderCrossAnalysis.csv | `job_medley_project/gas_output_phase7/` |
| 移動許容度 | MobilityScore.csv | `job_medley_project/gas_output_phase7/` |
| ペルソナ詳細 | DetailedPersonaProfile.csv | `job_medley_project/gas_output_phase7/` |
| ペルソナ地図 | PersonaMapData.csv | `job_medley_project/gas_output_phase7/` |
| ペルソナ×移動 | PersonaMobilityCross.csv | `job_medley_project/gas_output_phase7/` |

#### 6-3. シート確認

- [ ] `Phase7_SupplyDensity`
- [ ] `Phase7_QualificationDist`
- [ ] `Phase7_AgeGenderCross`
- [ ] `Phase7_MobilityScore`
- [ ] `Phase7_PersonaProfile`
- [ ] `PersonaMapData`
- [ ] `PersonaMobilityCross`

---

### ステップ7: 全Phaseアップロード状況確認

#### 7-1. 状況確認ダイアログ起動

メニュー: **📊 データ処理** > **📥 データインポート** > **✅ 全Phaseアップロード状況**

#### 7-2. 確認内容

**表示内容**:
```
全Phaseアップロード状況:

✅ 📍 Phase 1: 基礎集計: 4/4
✅ 📊 Phase 2: 統計分析: 2/2
✅ 👥 Phase 3: ペルソナ分析: 2/2
✅ 🌊 Phase 6: フロー分析: 3/3
✅ 📈 Phase 7: 高度分析: 7/7

合計: 18/18ファイル

🎉 全Phaseのアップロードが完了しています！
```

**確認ポイント**:
- [ ] 全Phaseに「✅」マークが表示される
- [ ] 合計が「18/18ファイル」と表示される
- [ ] 完了メッセージが表示される

---

## ✅ テスト完了チェックリスト

### 必須項目

- [ ] GASファイル3つをデプロイ完了
- [ ] Googleスプレッドシートのメニューに「📥 データインポート」が表示される
- [ ] Phase 1アップロードで4シート作成
- [ ] Phase 2アップロードで2シート作成
- [ ] Phase 3アップロードで2シート作成
- [ ] Phase 6アップロードで3シート作成
- [ ] Phase 7アップロードで7シート作成
- [ ] 全Phaseアップロード状況で「18/18ファイル」完了表示

### 合計シート数

**18シート** が作成されていることを確認

---

## 🚨 トラブルシューティング

### エラー1: 「関数が見つかりません」

**症状**: メニューをクリックしても何も起こらない

**原因**: 関数名が間違っている、またはファイルが保存されていない

**対処**:
1. Apps Scriptエディタで **ファイル** > **すべてを保存**
2. 関数名のスペルミスを確認（`showPhaseUploadDialog` が存在するか）
3. Googleスプレッドシートをリロード（F5）

---

### エラー2: 「メニューが表示されない」

**症状**: Googleスプレッドシートに「📥 データインポート」メニューが表示されない

**原因**: `onOpen()` 関数が正しく実行されていない

**対処**:
1. Apps Scriptエディタで `MenuIntegration.gs` を開く
2. 関数名が `onOpen()` になっているか確認
3. Googleスプレッドシートを**完全に閉じて**再度開く

---

### エラー3: 「ダイアログが開かない」

**症状**: メニューをクリックしてもダイアログが開かない

**原因**: `PhaseUpload.html` が追加されていない

**対処**:
1. Apps Scriptエディタで **ファイル一覧** を確認
2. `PhaseUpload.html` が存在するか確認
3. 存在しない場合は、デプロイ手順の「PhaseUpload.html を追加」を実行

---

### エラー4: 「シートが作成されない」

**症状**: アップロード完了メッセージが表示されるが、シートが見つからない

**原因**: GASスクリプトでエラーが発生している

**対処**:
1. Apps Scriptエディタで **表示** > **ログ** を確認
2. エラーメッセージを確認
3. `UniversalPhaseUploader.gs` が正しくコピペされているか確認

---

## 📊 期待される結果

### シート一覧（18シート）

#### Phase 1（4シート）
| シート名 | 行数（例） | 列数 | 説明 |
|---------|-----------|------|------|
| MapMetrics | 792 | 6 | 地図メトリクス |
| Applicants | 11,000+ | 10 | 応募者情報 |
| DesiredWork | 30,000+ | 5 | 希望勤務地 |
| AggDesired | 792 | 4 | 集計データ |

#### Phase 2（2シート）
| シート名 | 行数（例） | 列数 | 説明 |
|---------|-----------|------|------|
| ChiSquareTests | 5 | 6 | カイ二乗検定 |
| ANOVATests | 3 | 7 | ANOVA検定 |

#### Phase 3（2シート）
| シート名 | 行数（例） | 列数 | 説明 |
|---------|-----------|------|------|
| PersonaSummary | 11 | 8 | ペルソナサマリー |
| PersonaDetails | 11,000+ | 12 | ペルソナ詳細 |

#### Phase 6（3シート）
| シート名 | 行数（例） | 列数 | 説明 |
|---------|-----------|------|------|
| MunicipalityFlowEdges | 6,862 | 4 | フローエッジ |
| MunicipalityFlowNodes | 805 | 6 | フローノード |
| ProximityAnalysis | 11,000+ | 8 | 移動パターン分析 |

#### Phase 7（7シート）
| シート名 | 行数（例） | 列数 | 説明 |
|---------|-----------|------|------|
| Phase7_SupplyDensity | 792 | 5 | 人材供給密度 |
| Phase7_QualificationDist | 20 | 3 | 資格分布 |
| Phase7_AgeGenderCross | 42 | 4 | 年齢×性別 |
| Phase7_MobilityScore | 11,000+ | 6 | 移動許容度 |
| Phase7_PersonaProfile | 11 | 10 | ペルソナ詳細 |
| PersonaMapData | 792 | 7 | ペルソナ地図 |
| PersonaMobilityCross | 11 | 6 | ペルソナ×移動 |

---

## 📝 次のステップ

テストが完了したら:

1. **データ更新**: `python run_complete.py` を実行して最新データを生成
2. **再アップロード**: 各Phaseメニューから更新
3. **ステークホルダーレビュー**: ビジネス関係者にデモを実施
4. **本番運用開始**: Phase別アップロード機能を運用

---

**テスト完了お疲れ様でした！🎉**

Phase別一括アップロード機能により、全18ファイルを効率的にアップロードできるようになりました。
