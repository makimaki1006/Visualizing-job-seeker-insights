# ペルソナレベル統合CSV生成ガイド

**作成日**: 2025年11月6日
**バージョン**: 1.0
**目的**: MapComplete dashboard性能最適化のための統合CSVシート生成

---

## 目次

1. [背景と目的](#背景と目的)
2. [データ粒度の決定](#データ粒度の決定)
3. [技術的課題と解決策](#技術的課題と解決策)
4. [生成されるCSVファイル仕様](#生成されるcsvファイル仕様)
5. [実行方法](#実行方法)
6. [GAS統合手順](#gas統合手順)
7. [トラブルシューティング](#トラブルシューティング)

---

## 背景と目的

### 問題

MapComplete dashboardは、GAS側で15シートを順次読み込むため、データロードに21秒かかり、タイムアウトリスクがありました。

**従来の構造**:
```
MapCompleteDataBridge.gs
├─ Phase1_MapMetrics (944行)
├─ Phase1_Applicants (7,487行)
├─ Phase3_PersonaSummary (609行)
├─ Phase3_PersonaDetails (7,487行)
├─ Phase6_MunicipalityFlowEdges (966行)
├─ Phase6_MunicipalityFlowNodes (966行)
├─ Phase7_SupplyDensityMap (944行)
├─ Phase7_QualificationDistribution (7,487行)
├─ Phase7_AgeGenderCrossAnalysis (7,487行)
├─ Phase10_UrgencyByMunicipality (944行)
├─ Phase12_SupplyDemandGap (966行)
├─ Phase13_RarityScore (4,885行)
└─ Phase14_CompetitionProfile (944行)
```

**パフォーマンス問題**:
- 15シート × 平均1.4秒 = 21秒のロード時間
- GASスクリプト実行タイムアウト（30秒）に接近
- UI応答性の低下

### 解決方針

**都道府県別ペルソナレベル統合CSVを生成し、1シート読み込みに削減**

```
新構造:
PersonaLevel_京都府.csv (601行 × 46列)
├─ 全Phaseデータを統合
├─ ペルソナセグメント単位（市区町村 × 年齢 × 性別 × 資格）
└─ 1シート読み込みで完結（推定2-3秒）
```

**期待効果**:
- ロード時間: 21秒 → 2-3秒（86-90%削減）
- タイムアウトリスク: ほぼ解消
- UI応答性: 大幅改善

---

## データ粒度の決定

### 検討した3つの粒度レベル

#### 1. 個人申請者レベル（7,487行）
```csv
applicant_id, name, age, gender, municipality, qualification, ...
1, 山田太郎, 25, 男性, 京都府京都市伏見区, 看護師, ...
```

**判断**: ❌ 詳細すぎる、個人情報保護の観点から不適切

#### 2. 市区町村レベル（37行、京都府の場合）
```csv
municipality, total_applicants, avg_age, ...
京都府京都市伏見区, 1748, 45.2, ...
```

**判断**: ❌ 粗すぎる、ペルソナ難易度分析に不十分

#### 3. ペルソナセグメントレベル（601行、京都府の場合）✅ 採用
```csv
municipality, age_group, gender, has_national_license, count, rarity_score, ...
京都府京都市伏見区, 20代, 女性, True, 45, 0.15, ...
京都府京都市伏見区, 20代, 女性, False, 89, 0.08, ...
京都府京都市伏見区, 20代, 男性, True, 23, 0.25, ...
```

**採用理由**:
- ✅ ペルソナ難易度分析に必要な粒度
- ✅ 市区町村 × 年齢層 × 性別 × 国家資格の組み合わせで絞り込み可能
- ✅ データ量が適切（601行は管理可能）
- ✅ プライバシー保護（集計データのみ）

### ペルソナセグメントの構成

**軸の組み合わせ**:
- 市区町村: 37箇所（京都府の場合）
- 年齢層: 6グループ（20代、30代、40代、50代、60代、70代以上）
- 性別: 2種類（男性、女性）
- 国家資格: 2種類（あり、なし）

**理論上の最大組み合わせ**: 37 × 6 × 2 × 2 = 888セグメント
**実際のデータ**: 601セグメント（データが存在する組み合わせのみ）

---

## 技術的課題と解決策

### 課題1: 都道府県名の抽出

**問題**: 市区町村名から都道府県名を正規表現で抽出しようとしたが失敗

#### 試行1: 文字クラスの誤用
```python
# ❌ 誤り: [都道府県]は1文字しかマッチしない
persona_summary['prefecture'] = persona_summary['municipality'].str.extract(r'^(.+?[都道府県])', expand=False)
# 結果: "京都府京都市" → "京都" (最初の「都」でマッチ)
```

#### 試行2: 非貪欲マッチ
```python
# ❌ 誤り: 最初の「都/道/府/県」で停止
persona_summary['prefecture'] = persona_summary['municipality'].str.extract(r'^(.+?(?:都|道|府|県))', expand=False)
# 結果: "京都府京都市" → "京都" (非貪欲なので最初の「都」)
```

#### 試行3: 貪欲マッチ
```python
# ❌ 誤り: 最後の「都/道/府/県」までマッチ
persona_summary['prefecture'] = persona_summary['municipality'].str.extract(r'^(.*(?:都|道|府|県))', expand=False)
# 結果: "京都府京都市" → "京都府京都" (最後の「市」の前まで)
```

#### ✅ 最終解決策: 権威あるデータソースを使用

```python
# Phase13_RarityScoreには既に正しいprefecture列が存在
rarity_score = self.phase_data.get('phase13', {}).get('RarityScore')
prefectures = rarity_score['prefecture'].dropna().unique()

# municipality → prefecture マッピングを作成
prefecture_map = rarity_score[['location', 'prefecture']].drop_duplicates()
prefecture_map = prefecture_map.rename(columns={'location': 'municipality'})

# マッピングをPhase3に適用
persona_summary = persona_summary.merge(prefecture_map, on='municipality', how='left')
```

**教訓**:
- 正規表現で複雑な日本語パターンを扱うのは困難
- 既存の正確なデータソースを活用する方が確実

---

### 課題2: Phase間のカラム名不一致

**問題**: Phase3とPhase13で`municipality`列の内容が異なる

#### データ構造の違い

**Phase3: Phase3_PersonaSummaryByMunicipality.csv**
```csv
municipality, age_group, gender, has_national_license, count, ...
京都府京都市伏見区, 50代, 女性, False, 340, ...
```

**Phase13: Phase13_RarityScore.csv**
```csv
prefecture, municipality, location, age_bucket, gender, has_national_license, ...
京都府, 京都市伏見区, 京都府京都市伏見区, 50代, 女性, False, ...
```

**Phase13の列の役割**:
- `prefecture`: 都道府県名（"京都府"）
- `municipality`: 市区町村名のみ（"京都市伏見区"）
- `location`: 完全な住所（"京都府京都市伏見区"）← Phase3と一致

#### ✅ 解決策: `location`列を使用

```python
# Phase3のmunicipality = Phase13のlocation
prefecture_map = rarity_score[['location', 'prefecture']].drop_duplicates()
prefecture_map = prefecture_map.rename(columns={'location': 'municipality'})
```

**Phase13データマージ時も同様**:
```python
# 元のmunicipality列（短縮形）を削除
rarity_filtered = rarity_filtered.drop(columns=['municipality'], errors='ignore')
# location列をmunicipalityにリネーム
rarity_filtered = rarity_filtered.rename(columns={'location': 'municipality'})
```

---

### 課題3: カラム名の重複エラー

**問題**: Phase13に`municipality`列が既に存在する状態で`location`を`municipality`にリネームするとエラー

```python
ValueError: The column label 'municipality' is not unique.
```

#### ✅ 解決策: 元の列を削除してからリネーム

```python
# Step 1: 元のmunicipality列（短縮形）を削除
rarity_filtered = rarity_filtered.drop(columns=['municipality'], errors='ignore')

# Step 2: location列をmunicipalityにリネーム
rarity_filtered = rarity_filtered.rename(columns={
    'location': 'municipality',
    'age_bucket': 'age_group'
})

# Step 3: マージキーで結合
base_df = base_df.merge(
    rarity_filtered,
    on=['municipality', 'age_group', 'gender', 'has_national_license'],
    how='left'
)
```

---

## 生成されるCSVファイル仕様

### ファイル構造

**ファイル名**: `PersonaLevel_<都道府県名>.csv`

**出力先**: `data/output_v2/persona_level_sheets/`

**生成数**: 47ファイル（全都道府県）

### PersonaLevel_京都府.csv 詳細

**行数**: 602行（ヘッダー1行 + データ601行）
**列数**: 46列
**ファイルサイズ**: 159KB

#### カラム構成（46列）

##### Phase 3: ペルソナサマリー（ベースデータ、12列）
| 列名 | 型 | 説明 |
|------|-----|------|
| municipality | string | 市区町村名（完全形式）例: "京都府京都市伏見区" |
| persona_name | string | ペルソナ名 例: "50代・女性・国家資格なし" |
| age_group | string | 年齢層 例: "50代" |
| gender | string | 性別 例: "女性" |
| has_national_license | boolean | 国家資格保有 True/False |
| count | integer | 該当者数 |
| total_in_municipality | integer | 市区町村の総申請者数 |
| market_share_pct | float | 市区町村内シェア（%） |
| avg_age | float | 平均年齢 |
| avg_desired_areas | float | 平均希望勤務地数 |
| avg_qualifications | float | 平均資格数 |
| employment_rate | float | 就業率 |

##### Phase 13: 希少性スコア（6列）
| 列名 | 型 | 説明 |
|------|-----|------|
| prefecture_x, prefecture_y, prefecture | string | 都道府県名（マージにより複数） |
| phase13_location | string | 完全な住所 |
| phase13_count | integer | 該当者数 |
| phase13_rarity_score | float | 希少性スコア（0-1、1に近いほど希少） |
| phase13_rarity_rank | string | 希少性ランク 例: "S: 超希少（1人のみ）", "B: 希少（3-5人）", "D: 一般的（20人超）" |
| phase13_latitude | float | 緯度 |
| phase13_longitude | float | 経度 |

##### Phase 7: 供給密度（4列）
| 列名 | 型 | 説明 |
|------|-----|------|
| phase7_supply_count | integer | 供給人材数 |
| phase7_avg_age | float | 平均年齢 |
| phase7_national_license_count | integer | 国家資格保有者数 |
| phase7_avg_qualifications | float | 平均資格数 |

##### Phase 6: フロー分析（4列）
| 列名 | 型 | 説明 |
|------|-----|------|
| phase6_inflow | integer | 流入数 |
| phase6_outflow | integer | 流出数 |
| phase6_net_flow | integer | 純フロー（流入 - 流出） |
| phase6_applicant_count | integer | 申請者数 |

##### Phase 10: 緊急度分析（2列）
| 列名 | 型 | 説明 |
|------|-----|------|
| phase10_count | integer | 緊急度データ件数 |
| phase10_avg_urgency_score | float | 平均緊急度スコア |

##### Phase 14: 競合分析（11列）
| 列名 | 型 | 説明 |
|------|-----|------|
| phase14_location | string | 地域名 |
| phase14_total_applicants | integer | 総申請者数 |
| phase14_top_age_group | string | 最多年齢層 |
| phase14_top_age_ratio | float | 最多年齢層の割合 |
| phase14_female_ratio | float | 女性比率 |
| phase14_male_ratio | float | 男性比率 |
| phase14_national_license_rate | float | 国家資格保有率 |
| phase14_top_employment_status | string | 最多就業状況 |
| phase14_top_employment_ratio | float | 最多就業状況の割合 |
| phase14_avg_qualification_count | float | 平均資格数 |
| phase14_latitude | float | 緯度 |
| phase14_longitude | float | 経度 |

##### Phase 12: 需給ギャップ（4列、都道府県レベル）
| 列名 | 型 | 説明 |
|------|-----|------|
| phase12_demand_count | float | 需要数 |
| phase12_supply_count | float | 供給数 |
| phase12_demand_supply_ratio | float | 需給比率 |
| phase12_gap | float | 需給ギャップ（需要 - 供給） |

**注**: Phase 12は都道府県レベルのデータのため、全行に同じ値がブロードキャストされます。

---

### サンプルデータ

```csv
municipality,persona_name,age_group,gender,has_national_license,count,phase13_rarity_score,phase13_rarity_rank,phase12_demand_count,phase12_supply_count,phase12_demand_supply_ratio,phase12_gap
京都府京都市伏見区,50代・女性・国家資格なし,50代,女性,False,340,0.0068,D: 一般的（20人超）,500.0,0.0,500.0,500.0
京都府京都市伏見区,30代・女性・国家資格あり,30代,女性,True,12,0.3333,B: 希少（3-5人）,500.0,0.0,500.0,500.0
京都府宇治市,50代・男性・国家資格なし,50代,男性,False,66,0.0152,D: 一般的（20人超）,500.0,0.0,500.0,500.0
```

---

## 実行方法

### 前提条件

- Python 3.x がインストールされている
- 必要なライブラリ: pandas
- Phase 1-14のCSVファイルが `data/output_v2/phase*/` に存在する

### コマンド実行

```bash
cd "C:\Users\fuji1\OneDrive\Pythonスクリプト保管\job_medley_project\python_scripts"
python generate_persona_level_sheets.py
```

### 実行結果（正常終了時）

```
============================================================
  都道府県別ペルソナレベル統合シート生成
============================================================

[LOAD] 全Phaseデータ読み込み開始...
  [OK] phase3/Phase3_PersonaSummaryByMunicipality.csv: 4885行
  [OK] phase13/Phase13_RarityScore.csv: 4885行
  [OK] phase6/Phase6_MunicipalityFlowNodes.csv: 966行
  [OK] phase7/Phase7_SupplyDensityMap.csv: 944行
  [OK] phase10/Phase10_UrgencyByMunicipality.csv: 944行
  [OK] phase14/Phase14_CompetitionProfile.csv: 944行
  [OK] phase12/Phase12_SupplyDemandGap.csv: 966行
  [OK] 全Phaseデータ読み込み完了

[GENERATE] 都道府県別ペルソナレベル統合シート生成開始...
  [INFO] 都道府県数: 47件
  [DEBUG] Phase3 municipality サンプル: ['京都府京都市伏見区', '京都府京都市伏見区', ...]
  [DEBUG] Phase13 location(→municipality) サンプル: ['三重県度会郡大紀町', '鹿児島県鹿屋市', ...]
  [DEBUG] マッピング後のprefecture欠損数: 0/4885

  [GENERATE] 京都府 のペルソナレベル統合シート生成中...
    - PersonaSummaryByMunicipality: 609行（ベース）
    - Phase13_RarityScore: 結合完了
    - Phase7_SupplyDensityMap: 結合完了
    - Phase6_MunicipalityFlowNodes: 結合完了
    - Phase10_UrgencyByMunicipality: 結合完了
    - Phase14_CompetitionProfile: 結合完了
    - Phase12_SupplyDemandGap（都道府県レベル）: 結合完了
    [OK] 出力完了: data\output_v2\persona_level_sheets\PersonaLevel_京都府.csv (601行 × 46列)

  ... (他の46都道府県も同様)

  [OK] 都道府県別ペルソナレベル統合シート生成完了: data\output_v2\persona_level_sheets

============================================================
  [OK] 処理完了
============================================================
```

### 出力ファイル確認

```bash
# 生成されたファイル一覧
ls -lh data/output_v2/persona_level_sheets/

# 京都府のファイル詳細
wc -l data/output_v2/persona_level_sheets/PersonaLevel_京都府.csv
# 出力: 602 (ヘッダー1行 + データ601行)

head -n 1 data/output_v2/persona_level_sheets/PersonaLevel_京都府.csv | tr ',' '\n' | wc -l
# 出力: 46 (列数)
```

---

## GAS統合手順

### 方法1: 手動コピー＆ペースト（最も簡単）

#### ステップ1: CSVファイルを開く

1. `PersonaLevel_京都府.csv` をExcelまたはGoogleスプレッドシートで開く
2. 全データを選択（Ctrl+A）
3. コピー（Ctrl+C）

#### ステップ2: GASスプレッドシートに貼り付け

1. 対象のGoogleスプレッドシートを開く
2. 新しいシート「PersonaLevel_京都府」を作成
3. A1セルを選択
4. ペースト（Ctrl+V）

#### ステップ3: データ形式確認

- ヘッダー行が正しく表示されているか確認
- 数値列が文字列になっていないか確認（必要に応じて形式変更）

---

### 方法2: GAS Python CSVインポート機能を使用

#### ステップ1: CSVファイルをアップロード

1. GASメニュー: `データ処理` → `Python連携` → `Python結果CSVを取り込み`
2. ファイル選択ダイアログで `PersonaLevel_京都府.csv` を選択
3. 「Phase 7」や「PersonaLevel」など適切なシート名を指定
4. インポート実行

#### ステップ2: インポート結果確認

- 新しいシート「PersonaLevel_京都府」が作成される
- 602行 × 46列のデータが格納される
- カラム名が正しく認識されているか確認

---

### 方法3: MapCompleteDataBridge.gs を改修（今後の対応）

#### 現在の実装（15シート読み込み）

```javascript
function loadPhase1Data() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const mapMetricsSheet = ss.getSheetByName('Phase1_MapMetrics');
  const applicantsSheet = ss.getSheetByName('Phase1_Applicants');
  // ... 15シート分の読み込み
}
```

#### 改修後（1シート読み込み）

```javascript
function loadPersonaLevelData(prefecture) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheetName = 'PersonaLevel_' + prefecture;
  const sheet = ss.getSheetByName(sheetName);

  if (!sheet) {
    throw new Error(`シート「${sheetName}」が見つかりません`);
  }

  const data = sheet.getDataRange().getValues();
  const headers = data[0];
  const rows = data.slice(1);

  return {
    headers: headers,
    data: rows,
    rowCount: rows.length,
    colCount: headers.length
  };
}
```

#### 使用例

```javascript
function showMapCompleteDashboard() {
  const selectedPrefecture = getUserSelectedPrefecture(); // ユーザー選択
  const personaData = loadPersonaLevelData(selectedPrefecture);

  // personaData.dataには601行 × 46列のデータが格納されている
  // Phase 3, 6, 7, 10, 12, 13, 14のすべてのデータが利用可能

  console.log(`ロード完了: ${personaData.rowCount}行 × ${personaData.colCount}列`);
  // 出力: ロード完了: 601行 × 46列

  // 以降のダッシュボード生成処理
  generateDashboard(personaData);
}
```

**期待される性能改善**:
- ロード時間: 21秒 → 2-3秒（約85-90%削減）
- タイムアウトリスク: ほぼ解消
- コードの複雑性: 15シート読み込み → 1シート読み込み

---

## トラブルシューティング

### エラー1: 「Phase13_RarityScoreまたはprefecture列が見つかりません」

**原因**: Phase 13のCSVファイルが存在しないか、prefecture列がない

**解決策**:
```bash
# Phase 13データ生成を確認
python run_complete_v2.py
# Phase 13のCSVファイルが data/output_v2/phase13/ に生成されることを確認
```

---

### エラー2: 「マッピング後のprefecture欠損数: 4885/4885」

**原因**: Phase3とPhase13の`municipality`列の値が一致していない

**解決策**:
- スクリプトが最新版であることを確認
- Phase13の`location`列を使用してマッピングしていることを確認

```python
# 正しい実装
prefecture_map = rarity_score[['location', 'prefecture']].drop_duplicates()
prefecture_map = prefecture_map.rename(columns={'location': 'municipality'})
```

---

### エラー3: 「The column label 'municipality' is not unique.」

**原因**: Phase13に`municipality`列が既に存在する状態で`location`をリネームしようとした

**解決策**:
```python
# 元のmunicipality列を削除してからリネーム
rarity_filtered = rarity_filtered.drop(columns=['municipality'], errors='ignore')
rarity_filtered = rarity_filtered.rename(columns={'location': 'municipality'})
```

---

### エラー4: 生成されたCSVのPhase 13データが空

**原因**: マージキーで`municipality`（短縮形）を使用している

**解決策**:
```python
# Phase13のlocation列を使用
rarity_filtered = rarity_filtered.drop(columns=['municipality'], errors='ignore')
rarity_filtered = rarity_filtered.rename(columns={'location': 'municipality'})
```

---

### 確認方法: Phase 13データが正しくマージされているか

```bash
# Phase 13の列が存在するか確認
head -n 1 data/output_v2/persona_level_sheets/PersonaLevel_京都府.csv | tr ',' '\n' | grep "phase13"
# 出力:
# phase13_location
# phase13_count
# phase13_rarity_score
# phase13_rarity_rank
# phase13_latitude
# phase13_longitude

# データが入っているか確認（空でないこと）
head -n 3 data/output_v2/persona_level_sheets/PersonaLevel_京都府.csv | tail -n 1 | cut -d',' -f15-20
# 出力例:
# 京都府,3,0.3333333333333333,B: 希少（3-5人）,34.9327,135.7656
```

---

## まとめ

### 成果物

| ファイル | 行数 | 列数 | サイズ | 説明 |
|---------|------|------|--------|------|
| PersonaLevel_京都府.csv | 602 | 46 | 159KB | 京都府の全ペルソナセグメント統合データ |
| PersonaLevel_大阪府.csv | 1,521 | 46 | 225KB | 大阪府の全ペルソナセグメント統合データ |
| PersonaLevel_東京都.csv | 1,102 | 46 | 93KB | 東京都の全ペルソナセグメント統合データ |
| ... | ... | ... | ... | 全47都道府県 |

### 性能改善見込み

| 項目 | 従来 | 改善後 | 効果 |
|------|------|--------|------|
| シート数 | 15シート | 1シート | 93%削減 |
| ロード時間 | 21秒 | 2-3秒 | 85-90%削減 |
| タイムアウトリスク | 高（30秒上限に接近） | 低（余裕あり） | リスクほぼ解消 |
| コードの複雑性 | 高（15関数） | 低（1関数） | 大幅簡素化 |

### 次のステップ

1. **統合CSVをスプレッドシートにインポート**（手動コピペまたはGAS機能使用）
2. **GAS側改修**: MapCompleteDataBridge.gsの都道府県別シート読み込み対応
3. **テスト**: 京都府データで動作確認
4. **デプロイ**: clasp pushで本番環境に反映

---

**関連ドキュメント**:
- [generate_persona_level_sheets.py](../python_scripts/generate_persona_level_sheets.py) - 統合CSV生成スクリプト
- [ARCHITECTURE.md](ARCHITECTURE.md) - システムアーキテクチャ
- [DATA_SPECIFICATION.md](DATA_SPECIFICATION.md) - データ仕様書
- [GAS_COMPLETE_FEATURE_LIST.md](GAS_COMPLETE_FEATURE_LIST.md) - GAS完全機能一覧
