# タブ統合実装計画

**作成日**: 2025年11月21日
**目的**: 現在の7タブを5タブに統合し、ユーザビリティとデータ効率を改善

---

## 現状の問題点

### 問題1: タブ数が多すぎる（7タブ）

**現在の構成**:
```
1. 📊 概要（6要素）
2. 👥 年齢・性別（3要素）
3. 🎯 ペルソナ（9グラフ）← ❌ データなし（機能不全）
4. 🔥 緊急度（4要素）
5. 💎 希少人材（11要素）
6. ⚖️ 需給バランス（9要素）
7. 🏆 競合（11グラフ）← ⚠️ 薄い実装（1グラフのみ）
```

**問題点**:
- ペルソナタブがデータ不足で機能していない（PERSONA_MUNI = 0行）
- 競合タブが11グラフ定義されているが実装は1グラフのみ
- ユーザーが目的のデータを見つけにくい
- タブ間の関連性が不明確

### 問題2: データの重複と無駄

| row_type | 行数 | 使用状況 | 問題 |
|----------|------|----------|------|
| FLOW | 966行 | 10関数定義 | ❌ UI未統合（完全未使用） |
| COMPETITION | 966行 | 4グラフ | ⚠️ 低使用率（1グラフのみ） |
| PERSONA_MUNI | 0行 | 9グラフ | ❌ データなし |
| EMPLOYMENT_AGE_CROSS | 0行 | 11関数 | ❌ データなし |

**無駄な行数**: 1,932行（FLOW 966 + COMPETITION 966）

### 問題3: 実装率が低い

- **全体実装率**: 31%（54グラフ中、実際に動作するのは一部）
- **機能不全タブ**: ペルソナタブ（0行データ）
- **薄い実装**: 競合タブ（11グラフ定義中1グラフのみ）

---

## 新しい5タブ構成（推奨）

### タブ1: 📊 市場概況

**目的**: 地域の求職者市場全体を俯瞰

**含まれる要素** (8要素):
- **KPI 4個**: 総申請者数、対象地域数、平均女性比率、平均男性比率
- **グラフ 4個**:
  1. 性別分布（円グラフ）← 既存
  2. 年齢層分布（棒グラフ）← 年齢・性別タブから移動
  3. 年齢層×性別クロス（棒グラフ）← 年齢・性別タブから移動
  4. 就業状況分布（棒グラフ）← 新規追加

**使用row_type**:
- SUMMARY: 944行
- AGE_GENDER: 4,231行
- **合計**: 5,175行

**コード変更箇所**:
```python
def page_overview() -> rx.Component:
    return rx.vstack(
        # セクション1: KPI（既存）
        rx.hstack(
            kpi_card("総申請者数", DashboardState.competition_total_applicants, "人"),
            kpi_card("対象地域数", DashboardState.competition_total_regions, "地域"),
            kpi_card("平均女性比率", DashboardState.competition_avg_female_ratio, "%"),
            kpi_card("平均男性比率", DashboardState.competition_avg_male_ratio, "%"),
        ),

        # セクション2: 性別・年齢分布（統合）
        rx.heading("性別・年齢分布", size="6"),
        rx.grid(
            # 性別分布（既存）
            create_card(
                "性別分布",
                create_pie_chart(DashboardState.competition_gender_data),
            ),
            # 年齢層分布（年齢・性別タブから移動）
            create_card(
                "年齢層分布",
                create_bar_chart(
                    DashboardState.age_distribution,
                    x_key="age_group",
                    y_key="count",
                    name_key="人数",
                ),
            ),
            columns="2",
        ),

        # セクション3: クロス分析
        rx.heading("詳細クロス分析", size="6"),
        create_card(
            "年齢層×性別クロス分析",
            create_bar_chart(
                DashboardState.age_gender_cross,
                x_key="age_group",
                y_key="count",
                name_key="gender",
            ),
        ),
    )
```

---

### タブ2: 🎯 人材プロファイル

**目的**: どんな人材がいるかを詳細に把握（ペルソナ + 年齢・性別統合）

**含まれる要素** (12要素):
- **KPI 3個**: ペルソナ合計数、最多ペルソナ、平均年齢
- **グラフ 9個**:
  1. ペルソナ分布（棒グラフ）← ペルソナタブから
  2. ペルソナ構成比（円グラフ）← ペルソナタブから
  3. ペルソナTOP10リスト（表）← ペルソナタブから
  4. ペルソナ全リスト（表）← ペルソナタブから
  5. ペルソナ×就業状況（棒グラフ）← ペルソナタブから
  6. 性別×就業状況クロス（ヒートマップ）← ペルソナタブから
  7. 多次元プロファイル（レーダーチャート）← ペルソナタブから
  8. ペルソナ×資格×年齢（3次元分析）← ペルソナタブから
  9. 資格別ペルソナ分布（棒グラフ）← ペルソナタブから

**使用row_type**:
- **PERSONA_MUNI: 0行** → **要生成（推定2,000-3,000行）** ⚠️

**前提条件**:
- ❌ **現在データなし**
- ✅ **Phase 3から生成可能**
- 📋 **優先度1: データ生成が必須**

**実装ステップ**:
1. `generate_mapcomplete_complete_sheets.py`修正（PERSONA_MUNIデータ生成）
2. Phase 3の`PersonaSummaryByMunicipality.csv`から変換
3. V3再生成（+2,000-3,000行）
4. mapcomplete_dashboard.pyの関数テスト
5. UIページ実装

**コード変更箇所**:
```python
def page_persona() -> rx.Component:
    return rx.vstack(
        # セクション1: KPI
        rx.hstack(
            kpi_card("ペルソナ合計", DashboardState.persona_total_count, "種類"),
            kpi_card("最多ペルソナ", DashboardState.persona_top_name, ""),
            kpi_card("平均年齢", DashboardState.age_avg, "歳"),
        ),

        # セクション2: ペルソナ基本分析
        rx.heading("ペルソナ分布", size="6"),
        rx.grid(
            create_card(
                "ペルソナ分布（TOP10）",
                create_bar_chart(
                    DashboardState.persona_bar_data,
                    x_key="persona",
                    y_key="count",
                ),
            ),
            create_card(
                "ペルソナ構成比",
                create_pie_chart(DashboardState.persona_share_data),
            ),
            columns="2",
        ),

        # セクション3: クロス分析
        rx.heading("多次元分析", size="6"),
        # ... 残り7グラフ
    )
```

---

### タブ3: ⚖️ 需給・競合分析

**目的**: 採用難易度と競合状況を把握（需給バランス + 競合統合）

**含まれる要素** (15要素):
- **KPI 6個**:
  - 総需要数、総供給数、不足地域数、過剰地域数（需給バランスから）
  - 平均資格保有数、国家資格保有率（競合から）
- **グラフ 9個**:
  1. 需給ギャップ比較（棒グラフ）← 需給バランスから
  2. 需給バランス状況（散布図）← 需給バランスから
  3. 人材不足ランキング（棒グラフ）← 需給バランスから
  4. 人材過剰ランキング（棒グラフ）← 需給バランスから
  5. 需給比率ランキング（棒グラフ）← 需給バランスから
  6. 地域別需給クロス（ヒートマップ）← 需給バランスから
  7. 資格数ランキング（棒グラフ）← 競合から
  8. 国家資格保有率ランキング（棒グラフ）← 競合から
  9. 競合女性比率ランキング（棒グラフ）← 競合から

**使用row_type**:
- GAP: 966行
- COMPETITION: 966行（縮小可能）
- SUMMARY: 944行（一部）
- **合計**: 約2,876行

**コード変更箇所**:
```python
def page_supply_demand() -> rx.Component:
    return rx.vstack(
        # セクション1: KPI（需給 + 競合）
        rx.hstack(
            kpi_card("総需要数", DashboardState.gap_total_demand, "人"),
            kpi_card("総供給数", DashboardState.gap_total_supply, "人"),
            kpi_card("不足地域数", DashboardState.gap_shortage_count, "地域"),
            kpi_card("過剰地域数", DashboardState.gap_surplus_count, "地域"),
            kpi_card("平均資格数", DashboardState.competition_avg_qualification_count, "個"),
            kpi_card("国家資格率", DashboardState.competition_avg_national_license_rate, "%"),
        ),

        # セクション2: 需給バランス分析
        rx.heading("需給バランス", size="6"),
        rx.grid(
            create_card("需給ギャップ比較", ...),
            create_card("需給バランス状況", ...),
            columns="2",
        ),

        # セクション3: 競合分析
        rx.heading("競合状況", size="6"),
        rx.grid(
            create_card("資格数ランキング", ...),
            create_card("国家資格保有率ランキング", ...),
            create_card("女性比率ランキング", ...),
            columns="3",
        ),
    )
```

---

### タブ4: 💎 希少人材

**目的**: 採用が難しい希少人材の発見（変更なし）

**含まれる要素** (11要素):
- **KPI 6個**: S級人数、A級人数、B級人数、総希少人材数、平均希少度スコア、国家資格保有者数
- **グラフ 5個**:
  1. 年齢層別希少人材分布
  2. 性別希少人材分布
  3. 希少度ランク分布
  4. 国家資格保有者ランキング
  5. 希少度スコア分布

**使用row_type**:
- RARITY: 4,950行

**コード変更**: なし（既存のまま）

---

### タブ5: 🔥 緊急度・キャリア

**目的**: 今すぐ採用できる人材とキャリア背景を把握（緊急度 + 新キャリアタブ統合）

**含まれる要素** (予定: 15要素):
- **KPI 6個**:
  - 平均緊急度スコア、高緊急度人数（緊急度から）
  - 平均資格数、国家資格保有率（キャリアから）
  - 平均勤続年数、転職回数（キャリアから、要データ）
- **グラフ 9個**:
  1. 緊急度×年齢クロス（ヒートマップ）← 緊急度から
  2. 緊急度×就業状況クロス（ヒートマップ）← 緊急度から
  3. 緊急度×キャリア×年齢（3次元）← 新規（要EMPLOYMENT_AGE_CROSS）
  4. 年齢×就業状況クロス（ヒートマップ）← 新規（要EMPLOYMENT_AGE_CROSS）
  5. 年齢×資格クロス（ヒートマップ）← 新規（要EMPLOYMENT_AGE_CROSS）
  6. 就業状況×資格クロス（ヒートマップ）← 新規（要EMPLOYMENT_AGE_CROSS）
  7. 通勤距離×年齢×性別クロス（3次元）← 新規（要EMPLOYMENT_AGE_CROSS）
  8. 学歴分布（棒グラフ）← Phase 8から
  9. 卒業年度分布（折れ線グラフ）← Phase 8から

**使用row_type**:
- URGENCY_AGE: 2,942行
- URGENCY_EMPLOYMENT: 1,666行
- **EMPLOYMENT_AGE_CROSS: 0行** → **要生成（推定5,000-8,000行）** ⚠️

**前提条件**:
- ❌ **現在データなし**
- ✅ **V3に新規追加可能**
- 📋 **優先度1: データ生成が必須**

**実装ステップ**:
1. `generate_mapcomplete_complete_sheets.py`修正（EMPLOYMENT_AGE_CROSSデータ生成）
2. Phase 8の`CareerAgeCross.csv`から変換
3. V3再生成（+5,000-8,000行）
4. mapcomplete_dashboard.pyに新関数追加（11個）
5. UIページ実装

**コード変更箇所**:
```python
def page_urgency_career() -> rx.Component:
    return rx.vstack(
        # セクション1: KPI
        rx.hstack(
            kpi_card("平均緊急度", DashboardState.urgency_avg_score, "点"),
            kpi_card("高緊急度", DashboardState.urgency_high_count, "人"),
            kpi_card("平均資格数", DashboardState.career_avg_qualifications, "個"),
            kpi_card("国家資格率", DashboardState.career_national_license_rate, "%"),
        ),

        # セクション2: 緊急度分析
        rx.heading("転職意欲分析", size="6"),
        rx.grid(
            create_card(
                "緊急度×年齢クロス",
                create_heatmap(DashboardState.urgency_age_data),
            ),
            create_card(
                "緊急度×就業状況クロス",
                create_heatmap(DashboardState.urgency_employment_data),
            ),
            columns="2",
        ),

        # セクション3: キャリア分析（新規）
        rx.heading("キャリア背景分析", size="6"),
        rx.grid(
            create_card(
                "年齢×就業状況クロス",
                create_heatmap(DashboardState.cross_age_employment_data),  # 新関数
            ),
            create_card(
                "年齢×資格クロス",
                create_heatmap(DashboardState.cross_age_qualification_data),  # 新関数
            ),
            create_card(
                "就業状況×資格クロス",
                create_heatmap(DashboardState.cross_employment_qualification_data),  # 新関数
            ),
            columns="3",
        ),
    )
```

---

## 実装優先度と工数見積もり

### フェーズ1: データ不足解消（優先度: 🔴 最高）

**目的**: 既に関数もグラフもあるが、データがないだけで使えない状態を解消

**タスク1.1: PERSONA_MUNIデータ生成**
- **ファイル**: `generate_mapcomplete_complete_sheets.py`
- **変更箇所**: `_generate_persona_muni_rows()` メソッド追加
- **元データ**: `data/output_v2/phase3/PersonaSummaryByMunicipality.csv`
- **推定行数**: +2,000-3,000行
- **工数**: 4時間
- **効果**: ペルソナタブの9グラフが使用可能に

**タスク1.2: EMPLOYMENT_AGE_CROSSデータ生成**
- **ファイル**: `generate_mapcomplete_complete_sheets.py`
- **変更箇所**: `_generate_employment_age_cross_rows()` メソッド追加
- **元データ**: `data/output_v2/phase8/CareerAgeCross.csv`
- **推定行数**: +5,000-8,000行
- **工数**: 6時間
- **効果**: キャリア関連11関数が使用可能に

**タスク1.3: V3再生成とテスト**
- **実行**: `python generate_mapcomplete_complete_sheets.py`
- **検証**: 新row_typeのデータ確認、行数確認
- **工数**: 1時間
- **効果**: V3が24,631-26,631行に増加（+40-51%）

**フェーズ1合計工数**: 11時間（約1.5日）
**フェーズ1効果**: 20グラフが即座に使用可能

---

### フェーズ2: タブ統合UI実装（優先度: 🟡 高）

**タスク2.1: タブ1「市場概況」実装**
- **変更ファイル**: `mapcomplete_dashboard/mapcomplete_dashboard.py`
- **変更箇所**: `page_overview()`メソッド修正
- **追加要素**: 年齢層分布、年齢×性別クロスを移動
- **工数**: 2時間
- **テスト**: ブラウザで表示確認、フィルタ動作確認

**タスク2.2: タブ2「人材プロファイル」実装**
- **変更ファイル**: `mapcomplete_dashboard/mapcomplete_dashboard.py`
- **変更箇所**: 新規`page_persona()`メソッド作成（年齢・性別 + ペルソナ統合）
- **追加要素**: 12要素（KPI 3 + グラフ 9）
- **工数**: 4時間
- **前提**: フェーズ1完了（PERSONA_MUNIデータ存在）
- **テスト**: 9グラフすべて表示確認

**タスク2.3: タブ3「需給・競合分析」実装**
- **変更ファイル**: `mapcomplete_dashboard/mapcomplete_dashboard.py`
- **変更箇所**: 新規`page_supply_demand_competition()`メソッド作成
- **追加要素**: 15要素（KPI 6 + グラフ 9）
- **工数**: 4時間
- **テスト**: 需給と競合のデータ混在なし確認

**タスク2.4: タブ4「希少人材」維持**
- **変更**: なし（既存のまま）
- **工数**: 0時間

**タスク2.5: タブ5「緊急度・キャリア」実装**
- **変更ファイル**: `mapcomplete_dashboard/mapcomplete_dashboard.py`
- **変更箇所**: 新規`page_urgency_career()`メソッド作成
- **追加要素**: 15要素（KPI 6 + グラフ 9）
- **追加関数**: 7個（`cross_age_employment_data`, `cross_age_qualification_data`など）
- **工数**: 6時間
- **前提**: フェーズ1完了（EMPLOYMENT_AGE_CROSSデータ存在）
- **テスト**: 新関数すべて動作確認

**タスク2.6: メインページのタブ構成変更**
- **変更ファイル**: `mapcomplete_dashboard/mapcomplete_dashboard.py`
- **変更箇所**: `index()`メソッドのタブ配列
- **変更内容**:
  ```python
  # 旧: 7タブ
  rx.tabs.root(
      rx.tabs.list(
          create_tab("📊 概要", "overview"),
          create_tab("👥 年齢・性別", "age_gender"),
          create_tab("🎯 ペルソナ", "persona"),
          create_tab("🔥 緊急度", "urgency"),
          create_tab("💎 希少人材", "rarity"),
          create_tab("⚖️ 需給バランス", "gap"),
          create_tab("🏆 競合", "competition"),
      ),
      ...
  )

  # 新: 5タブ
  rx.tabs.root(
      rx.tabs.list(
          create_tab("📊 市場概況", "overview"),
          create_tab("🎯 人材プロファイル", "persona"),
          create_tab("⚖️ 需給・競合", "supply_demand"),
          create_tab("💎 希少人材", "rarity"),
          create_tab("🔥 緊急度・キャリア", "urgency_career"),
      ),
      ...
  )
  ```
- **工数**: 1時間
- **テスト**: タブ切り替え動作確認

**フェーズ2合計工数**: 17時間（約2日）
**フェーズ2効果**: 7タブ → 5タブに削減、20グラフ統合

---

### フェーズ3: 未使用データ削減（優先度: 🟢 中）

**タスク3.1: FLOWデータ削除**
- **変更ファイル**: `generate_mapcomplete_complete_sheets.py`
- **変更箇所**: `_generate_flow_rows()` メソッドをコメントアウト
- **削減行数**: -966行
- **影響**: なし（UI未統合のため）
- **工数**: 0.5時間

**タスク3.2: COMPETITIONデータ縮小**
- **変更ファイル**: `generate_mapcomplete_complete_sheets.py`
- **変更箇所**: `_generate_competition_rows()` メソッド修正
- **戦略**: 都道府県レベルのみ保持（市区町村レベル削除）
- **削減行数**: -700行（推定）
- **影響**: 一部ランキングの粒度低下（許容範囲）
- **工数**: 1時間

**タスク3.3: mapcomplete_dashboard.pyの未使用関数削除**
- **変更ファイル**: `mapcomplete_dashboard/mapcomplete_dashboard.py`
- **削除対象**: FLOW関連10関数、CAREER_CROSS未使用関数
- **工数**: 1時間
- **効果**: コードサイズ削減、保守性向上

**タスク3.4: V3再生成とサイズ確認**
- **実行**: `python generate_mapcomplete_complete_sheets.py`
- **検証**: 行数が期待通り削減されているか確認
- **期待結果**: 約22,965-25,965行（元17,631 + 新規7,000-8,000 - 削減1,666）
- **工数**: 0.5時間

**フェーズ3合計工数**: 3時間（約0.5日）
**フェーズ3効果**: -1,666行削減、コード整理

---

### フェーズ4: E2Eテストと品質保証（優先度: 🟡 高）

**タスク4.1: ユニットテスト更新**
- **変更ファイル**: `tests/test_dashboard_state.py`（新規作成）
- **テスト内容**:
  - PERSONA_MUNI関連9関数のテスト
  - EMPLOYMENT_AGE_CROSS関連11関数のテスト
  - 新しい統合タブのState計算テスト
- **工数**: 4時間

**タスク4.2: E2Eテスト実施**
- **変更ファイル**: `tests/test_dashboard_e2e.py`
- **テスト内容**:
  - 5タブすべての表示確認
  - 都道府県フィルタ動作確認
  - 市区町村フィルタ動作確認
  - データ更新確認
- **工数**: 3時間

**タスク4.3: ブラウザ実機テスト**
- **テスト内容**:
  - CSVアップロード → 全5タブ表示確認
  - 各グラフが正しいデータを表示
  - カラーパレット一貫性確認
  - レスポンシブデザイン確認
- **工数**: 2時間

**タスク4.4: Pylintチェック**
- **実行**: `pylint mapcomplete_dashboard/`
- **基準**: スコア8.0以上
- **工数**: 1時間

**フェーズ4合計工数**: 10時間（約1.5日）
**フェーズ4効果**: 品質保証、バグ早期発見

---

## 総合工数見積もり

| フェーズ | 内容 | 工数 | 優先度 |
|---------|------|------|--------|
| フェーズ1 | データ不足解消 | 11時間（1.5日） | 🔴 最高 |
| フェーズ2 | タブ統合UI実装 | 17時間（2日） | 🟡 高 |
| フェーズ3 | 未使用データ削減 | 3時間（0.5日） | 🟢 中 |
| フェーズ4 | テスト・品質保証 | 10時間（1.5日） | 🟡 高 |
| **合計** | **全フェーズ** | **41時間（約5日）** | - |

---

## データ量変化予測

### 現在のV3構成

| row_type | 行数 | 状態 |
|----------|------|------|
| RARITY | 4,950 | ✅ 使用中 |
| AGE_GENDER | 4,231 | ✅ 使用中 |
| URGENCY_AGE | 2,942 | ✅ 使用中 |
| URGENCY_EMPLOYMENT | 1,666 | ✅ 使用中 |
| GAP | 966 | ✅ 使用中 |
| FLOW | 966 | ❌ 削除予定 |
| COMPETITION | 966 | ⚠️ 縮小予定（-700行） |
| SUMMARY | 944 | ✅ 使用中 |
| PERSONA_MUNI | 0 | 🆕 追加予定（+2,500行） |
| EMPLOYMENT_AGE_CROSS | 0 | 🆕 追加予定（+6,500行） |
| **合計** | **17,631** | - |

### 統合後のV3構成（推定）

| row_type | 行数 | 変化 |
|----------|------|------|
| RARITY | 4,950 | 変更なし |
| AGE_GENDER | 4,231 | 変更なし |
| URGENCY_AGE | 2,942 | 変更なし |
| URGENCY_EMPLOYMENT | 1,666 | 変更なし |
| GAP | 966 | 変更なし |
| ~~FLOW~~ | ~~966~~ | ❌ 削除 |
| COMPETITION | 266 | -700行 |
| SUMMARY | 944 | 変更なし |
| **PERSONA_MUNI** | **2,500** | 🆕 追加 |
| **EMPLOYMENT_AGE_CROSS** | **6,500** | 🆕 追加 |
| **合計** | **24,965** | **+7,334行（+41.6%）** |

### データ量変化の内訳

```
現在: 17,631行
削減: -1,666行（FLOW -966、COMPETITION -700）
追加: +9,000行（PERSONA_MUNI +2,500、EMPLOYMENT_AGE_CROSS +6,500）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
統合後: 24,965行（+41.6%増加）
```

**評価**:
- ✅ **許容範囲**: 5万行以下を維持
- ✅ **効果的**: 20グラフが新たに使用可能
- ✅ **効率的**: 未使用データ削減により実質的な増加は抑制
- ✅ **バランス**: 機能追加とデータ量のトレードオフが適切

---

## リスクと対策

### リスク1: データ生成失敗

**リスク**: Phase 3やPhase 8のデータが不足している場合、PERSONA_MUNIやEMPLOYMENT_AGE_CROSSを生成できない

**対策**:
1. 事前にPhase 3, 8のCSVファイル存在確認
2. データ件数の検証（最低100件以上）
3. 失敗時のロールバック手順準備

**検証コマンド**:
```bash
# Phase 3確認
ls -lh data/output_v2/phase3/PersonaSummaryByMunicipality.csv

# Phase 8確認
ls -lh data/output_v2/phase8/CareerAgeCross.csv
```

### リスク2: V3再生成時のパフォーマンス低下

**リスク**: 24,965行に増加すると、生成時間が長くなる可能性

**対策**:
1. 生成スクリプトにプログレスバー追加
2. 並列処理の検討（pandasのchunksize使用）
3. キャッシュ機構の導入

**期待生成時間**:
- 現在（17,631行）: 約30秒
- 統合後（24,965行）: 約45秒（推定）

### リスク3: UI描画パフォーマンス低下

**リスク**: グラフ数が増えると、タブ切り替えが重くなる可能性

**対策**:
1. サーバーサイドフィルタリング維持（既存）
2. グラフの遅延読み込み（lazy loading）検討
3. データキャッシュの活用（`@rx.var(cache=False)`を適切に使用）

**検証方法**:
- Chrome DevToolsでパフォーマンス計測
- LighthouseスコアでUI応答性確認

### リスク4: データ整合性エラー

**リスク**: 新しいrow_typeのデータ形式が不正でエラーが発生

**対策**:
1. データバリデーション関数追加
2. スキーマチェック（カラム名、データ型）
3. 異常値検出（NULL、負の値など）

**検証関数例**:
```python
def validate_persona_muni_data(df):
    """PERSONA_MUNIデータの検証"""
    required_columns = ['row_type', 'prefecture', 'municipality', 'category1', 'category2', 'count']
    assert all(col in df.columns for col in required_columns)
    assert df['row_type'].eq('PERSONA_MUNI').all()
    assert df['count'].ge(0).all()  # 負の値なし
    assert df['count'].notna().all()  # NULL値なし
```

---

## 成功基準

### 定量的基準

1. **タブ数削減**: 7タブ → 5タブ ✅
2. **データ量増加**: +41.6%（5万行以下を維持）✅
3. **グラフ使用率**: 31% → 80%以上 ✅
4. **テスト成功率**: 100%（全テスト成功）
5. **Pylintスコア**: 8.0以上

### 定性的基準

1. **ユーザビリティ**: タブ間の移動が直感的
2. **一貫性**: カラーパレット、レイアウトが統一
3. **応答性**: 都道府県・市区町村フィルタが即座に反映
4. **保守性**: コードが整理され、重複がない

---

## 次のステップ

### ステップ1: ユーザー承認取得

以下を確認：
- [ ] 5タブ構成に同意
- [ ] データ量+41.6%増加を許容
- [ ] 工数5日を承認
- [ ] FLOWデータ削除に同意
- [ ] COMPETITIONデータ縮小に同意

### ステップ2: フェーズ1実装開始

**最初のタスク**: PERSONA_MUNIデータ生成
- `generate_mapcomplete_complete_sheets.py`に`_generate_persona_muni_rows()`追加
- Phase 3データから変換ロジック実装
- 単体テスト実施
- V3再生成

### ステップ3: 段階的デプロイ

1. **ローカル環境**: 全機能テスト
2. **ステージング環境**: E2Eテスト
3. **本番環境**: 段階的ロールアウト

---

## まとめ

**この計画の目的**:
- 📊 **ユーザビリティ向上**: 7タブ → 5タブで使いやすく
- 💾 **データ効率化**: 未使用データ削減（-1,666行）
- 📈 **機能最大化**: 既存のグラフを全て活用（20グラフ追加）
- ⚖️ **バランス**: データ量+41.6%で機能+258%（20グラフ）

**投資対効果**:
- **工数**: 5日
- **効果**: タブ削減、20グラフ追加、データ整理
- **ROI**: 非常に高い（既存の関数を活用、新規実装は最小限）

**推奨アクション**:
✅ **承認後、即座にフェーズ1を開始**（データ生成は影響範囲が小さい）
