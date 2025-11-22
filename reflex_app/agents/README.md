# Reflexダッシュボード サブエージェント

このディレクトリには、各タブの実装を担当するサブエージェントのコードを格納します。

## サブエージェント構造

各タブごとに独立したモジュールとして実装：

```
agents/
├── tab_age_gender.py      # 年齢×性別タブ
├── tab_persona.py          # ペルソナ分析タブ
├── tab_flow.py             # フロー分析タブ
├── tab_gap.py              # 需給ギャップタブ
├── tab_rarity.py           # 希少人材タブ
├── tab_competition.py      # 競争プロファイルタブ
├── tab_career_cross.py     # キャリア×年齢タブ
├── tab_urgency_age.py      # 緊急度×年齢タブ
└── tab_urgency_employment.py  # 緊急度×就業タブ
```

## 設計方針

1. **独立性**: 各サブエージェントは他のタブに依存しない
2. **統一インターフェース**: すべてのサブエージェントが同じ関数シグネチャを持つ
3. **データフィルタ**: Stateから渡されたフィルタ済みデータを使用
4. **Plotly統合**: すべてのグラフはPlotlyで実装

## 共通インターフェース

```python
def create_tab_component(df: pd.DataFrame, state: State) -> rx.Component:
    """
    タブコンポーネントを作成

    Args:
        df: フィルタ済みDataFrame
        state: Reflexのグローバルstate

    Returns:
        rx.Component: タブのReflexコンポーネント
    """
    pass
```
