# サブエージェント実装仕様書

## 目的

GAS統合ダッシュボードの10タブを完全再現するため、各タブを独立したサブエージェントとして実装する。

---

## 全体アーキテクチャ

```
mapcomplete_dashboard.py (メインアプリ)
    ↓ データロード・フィルタリング
    ↓ State管理
    ↓
agents/ (サブエージェント群)
    ├── tab_age_gender.py       → 👥 年齢×性別タブ
    ├── tab_persona.py           → 🎯 ペルソナタブ
    ├── tab_flow.py              → 🌊 フローTタブ
    ├── tab_gap.py               → 📈 需給ギャップタブ
    ├── tab_rarity.py            → 💎 希少人材タブ
    ├── tab_competition.py       → 🏆 競争プロファイルタブ
    ├── tab_career_cross.py      → 💼 キャリア×年齢タブ
    ├── tab_urgency_age.py       → ⏰ 緊急度×年齢タブ
    └── tab_urgency_employment.py → 💼 緊急度×就業タブ
```

---

## 共通インターフェース

すべてのサブエージェントは以下の関数を実装：

```python
def create_[tab_name]_tab(state) -> rx.Component:
    """
    タブコンポーネントを作成

    Args:
        state: Reflexのグローバルstate（フィルタ済みデータを含む）

    Returns:
        rx.Component: タブのReflexコンポーネント
    """
    pass
```

---

## データフロー

1. **メインアプリ** (`mapcomplete_dashboard.py`)
   - CSVロード
   - 都道府県・市区町村フィルタリング
   - 各row_type別にデータ分離
   - Stateに格納

2. **サブエージェント** (`agents/tab_*.py`)
   - Stateからフィルタ済みデータ取得
   - Plotlyグラフ生成
   - Reflexコンポーネント構築
   - 完成したコンポーネントを返す

---

## 各サブエージェントの仕様

### 1. tab_age_gender.py（年齢×性別）

**row_type**: `AGE_GENDER`

**データ構造**:
```csv
prefecture,municipality,row_type,age_group,gender,count
京都府,八幡市,AGE_GENDER,20代,男性,50
京都府,八幡市,AGE_GENDER,20代,女性,45
...
```

**実装内容**:
- Plotly棒グラフ（グループ化: age_group × gender）
- データテーブル（Reflex data_table）
- CSVダウンロードボタン

**Plotlyグラフ例**:
```python
fig = go.Figure()
for gender in ['男性', '女性']:
    df_gender = df[df['gender'] == gender]
    fig.add_trace(go.Bar(
        name=gender,
        x=df_gender['age_group'],
        y=df_gender['count']
    ))
fig.update_layout(barmode='group')
```

---

### 2. tab_persona.py（ペルソナ分析）

**row_type**: `PERSONA_MUNI`

**データ構造**:
```csv
prefecture,municipality,row_type,persona_name,count
京都府,八幡市,PERSONA_MUNI,若手スキルチャレンジャー,120
京都府,八幡市,PERSONA_MUNI,安定志向ベテラン,95
...
```

**実装内容**:
- Plotly棒グラフ（降順ソート）
- データテーブル
- CSVダウンロードボタン

**Plotlyグラフ例**:
```python
df_sorted = df.sort_values('count', ascending=False)
fig = go.Figure(go.Bar(
    x=df_sorted['persona_name'],
    y=df_sorted['count'],
    marker_color='lightblue'
))
```

---

### 3. tab_flow.py（フロー分析）

**row_type**: `FLOW`

**データ構造**:
```csv
prefecture,municipality,row_type,inflow,outflow,net_flow
京都府,八幡市,FLOW,248,384,-136
```

**実装内容**:
- 3つのメトリックカード（流入・流出・純流入）
- Plotly Sankeyダイアグラム
- 流入超過/流出超過の自動判定

**Plotly Sankeyグラフ例**:
```python
fig = go.Figure(go.Sankey(
    node=dict(
        label=["他地域", "八幡市", "流出先"]
    ),
    link=dict(
        source=[0, 1],
        target=[1, 2],
        value=[inflow, outflow]
    )
))
```

---

### 4. tab_gap.py（需給ギャップ）

**row_type**: `GAP`

**データ構造**:
```csv
prefecture,municipality,row_type,demand,supply,gap
京都府,八幡市,GAP,500,384,116
```

**実装内容**:
- 3つのメトリックカード（需要・供給・ギャップ）
- Plotly棒グラフ（需要 vs 供給）
- 需要超過/供給超過の自動判定

**Plotlyグラフ例**:
```python
fig = go.Figure()
fig.add_trace(go.Bar(name='需要', x=['需給バランス'], y=[demand]))
fig.add_trace(go.Bar(name='供給', x=['需給バランス'], y=[supply]))
fig.update_layout(barmode='group')
```

---

### 5. tab_rarity.py（希少人材分析）

**row_type**: `RARITY`

**データ構造**:
```csv
prefecture,municipality,row_type,category,rarity_score,count
京都府,八幡市,RARITY,資格保有者,8.5,25
京都府,八幡市,RARITY,経験年数15年以上,7.2,18
...
```

**実装内容**:
- Plotly棒グラフ（希少度スコア）
- データテーブル
- CSVダウンロードボタン

---

### 6. tab_competition.py（競争プロファイル）

**row_type**: `COMPETITION`

**データ構造**:
```csv
prefecture,municipality,row_type,competition_score,difficulty_rank,difficulty_level
京都府,八幡市,COMPETITION,75.5,B,中程度
```

**実装内容**:
- 3つのメトリックカード（競争スコア・難易度ランク・難易度レベル）
- 詳細説明テキスト

---

### 7. tab_career_cross.py（キャリア×年齢）

**row_type**: `CAREER_CROSS`

**データ構造**:
```csv
prefecture,municipality,row_type,career_type,age_group,count
京都府,八幡市,CAREER_CROSS,新卒,20代,30
京都府,八幡市,CAREER_CROSS,中途,30代,50
...
```

**実装内容**:
- Plotly棒グラフ（グループ化: career_type × age_group）
- データテーブル
- CSVダウンロードボタン

---

### 8. tab_urgency_age.py（緊急度×年齢）

**row_type**: `URGENCY_AGE`

**データ構造**:
```csv
prefecture,municipality,row_type,urgency_level,age_group,count
京都府,八幡市,URGENCY_AGE,高,20代,25
京都府,八幡市,URGENCY_AGE,中,30代,40
...
```

**実装内容**:
- Plotlyヒートマップ（urgency_level × age_group）
- データテーブル
- CSVダウンロードボタン

**Plotlyヒートマップ例**:
```python
pivot = df.pivot_table(
    values='count',
    index='urgency_level',
    columns='age_group',
    fill_value=0
)
fig = go.Figure(go.Heatmap(
    z=pivot.values,
    x=pivot.columns,
    y=pivot.index,
    colorscale='Viridis'
))
```

---

### 9. tab_urgency_employment.py（緊急度×就業状況）

**row_type**: `URGENCY_EMPLOYMENT`

**データ構造**:
```csv
prefecture,municipality,row_type,urgency_level,employment_status,count
京都府,八幡市,URGENCY_EMPLOYMENT,高,在職中,50
京都府,八幡市,URGENCY_EMPLOYMENT,中,離職中,30
...
```

**実装内容**:
- Plotly棒グラフ（グループ化: urgency_level × employment_status）
- データテーブル
- CSVダウンロードボタン

---

## 開発手順

### Phase 1: 基本構造（各サブエージェント共通）

1. ファイル作成
2. Stateからデータ取得
3. データ存在チェック
4. エラーハンドリング

### Phase 2: Plotlyグラフ実装

1. `@rx.var`でPlotly figureを生成
2. `rx.plotly()`でReflexに統合

### Phase 3: データテーブル実装

1. DataFrameを辞書形式に変換
2. `rx.data_table()`で表示

### Phase 4: CSVダウンロード実装（オプション）

1. `rx.download()`ボタン追加

---

## コーディング規約

1. **関数名**: `create_[tab_name]_tab`
2. **docstring**: Google Style
3. **型ヒント**: すべての関数に型ヒントを追加
4. **エラーハンドリング**: データ不足時は適切なメッセージ表示
5. **コメント**: 日本語で記述（コード自体は英語）

---

## テスト計画

各サブエージェントの動作確認:

1. **京都府八幡市**でテスト（実データあり）
2. **データ不足地域**でテスト（エラーハンドリング確認）
3. **都道府県全体**でテスト（大量データパフォーマンス確認）

---

## 次のステップ

1. ✅ agentsディレクトリ作成
2. ✅ `__init__.py`作成
3. ✅ `AGENT_SPECIFICATION.md`作成（このファイル）
4. 🔄 各サブエージェントを順番に実装（9ファイル）
5. ⏳ メインアプリとの統合
6. ⏳ E2Eテスト

---

**実装準備完了。各サブエージェントの実装を開始します。**
