# パフォーマンス最適化 Phase 1 レポート

**作成日**: 2025年12月12日
**対象**: `mapcomplete_dashboard/mapcomplete_dashboard.py`
**ステータス**: 完了（効果限定的）

---

## 1. エグゼクティブサマリー

### 実施内容

| Phase | 内容 | 結果 |
|-------|------|------|
| Phase 1 | 未使用heatmap_html @rx.var削除 | 5個削除 |
| Phase 2 | 未使用中間キャッシュ削除 | 2個削除 |
| Phase 3 | Lazy Loading実装 | 32個に適用 |

### 結論

| 項目 | 値 |
|------|-----|
| **実際のUI待機時間** | **約12秒** |
| **今回の改善効果** | 約0.5秒（4%程度） |
| **体感改善** | **ほぼなし** |

**今回の最適化は@rx.var計算コストに焦点を当てたが、真のボトルネックは別の場所にある可能性が高い。**

---

## 2. 実施した最適化

### 2.1 Phase 1: 未使用heatmap_html削除

**削除対象（5個）**:

| @rx.var名 | 旧行番号 | 処理内容 |
|-----------|----------|----------|
| `desired_area_age_gender_heatmap_html` | 2267-2357 | Plotly→HTML変換 |
| `desired_area_pattern_heatmap_html` | 3016-3073 | Plotly→HTML変換 |
| `desired_area_pattern_heatmap_muni_html` | 3075-3155 | Plotly→HTML変換 |
| `residence_flow_heatmap_html` | 3262-3319 | Plotly→HTML変換 |
| `residence_flow_heatmap_muni_html` | 3321-3402 | Plotly→HTML変換 |

**削除理由**:
- UIで参照されていない孤立した@rx.var
- 過去のリファクタリングで使用箇所が削除されたが、関数定義が残存
- Reflexの仕様上、cache=Falseの@rx.varは**UIで使用されていなくても毎イベントで再計算される**

**ベンチマーク結果**:
- 1つのto_html(): 約94ms
- 5つ合計: 約468ms/イベント削減

### 2.2 Phase 2: 未使用中間キャッシュ削除

**削除対象（2個）**:

| @rx.var名 | 旧行番号 |
|-----------|----------|
| `_cached_persona_muni_filtered` | 1547-1556 |
| `_cached_employment_age_filtered` | 1558-1567 |

**削除理由**:
- 定義されているが、他の@rx.varから参照されていない
- 過去の最適化試行の残骸と推定

### 2.3 Phase 3: Lazy Loading実装

**実装内容**:
各@rx.varの先頭に、表示タブをチェックする条件を追加：

```python
@rx.var(cache=False)
def gap_total_demand(self) -> str:
    # Lazy Loading: gapタブ以外では計算をスキップ
    if self.active_tab != "gap":
        return "0"
    # 以下、実際の計算処理
    ...
```

**適用数**:

| タブ | @rx.var数 | 主要関数 |
|------|-----------|----------|
| gap | 8 | gap_total_demand, gap_shortage_ranking等 |
| persona | 6 | persona_top_list, persona_bar_data等 |
| region | 18 | talent_flow_*, residence_flow_*, competition_*, mobility_* |
| **合計** | **32** | |

---

## 3. 変更前後の比較

### ファイル統計

| 指標 | 変更前 | 変更後 | 差分 |
|------|--------|--------|------|
| ファイルサイズ | 391,238 bytes | 379,000 bytes | -12,238 bytes |
| 行数 | 9,454 | 9,166 | -288行 |
| @rx.var総数 | 138 | 131 | -7 |

### 計算コスト（理論値）

| 状況 | 変更前 | 変更後 |
|------|--------|--------|
| overviewタブ表示時 | 138個計算 | 99個計算（32個スキップ） |
| gapタブ表示時 | 138個計算 | 107個計算（24個スキップ） |
| personaタブ表示時 | 138個計算 | 105個計算（26個スキップ） |
| regionタブ表示時 | 138個計算 | 117個計算（14個スキップ） |

---

## 4. ベンチマーク結果

### 測定環境

- DataFrame行数: 500行（実際のself.dfサイズ相当）
- 測定回数: 100回の平均

### 結果

| 処理 | 時間 |
|------|------|
| 1つの@rx.var（filter + groupby） | 0.94ms |
| 1つのto_html()（Plotly HTML生成） | 93.6ms |

### 改善効果（理論値）

| 最適化 | 削減時間 |
|--------|----------|
| to_html() 5個削除 | -468ms |
| Lazy Loading 32個スキップ | -30ms |
| **合計** | **約500ms/イベント** |

---

## 5. 問題点：真のボトルネックは別の場所

### 現実の待機時間

ユーザー報告による実際の待機時間：

| 操作 | 待機時間 |
|------|----------|
| 都道府県切り替え | 約12秒 |
| 市区町村切り替え | 約12秒 |
| タブ切り替え | 約12秒 |

### 改善効果の現実

| 項目 | 値 |
|------|-----|
| 実際の待機時間 | 12,000ms |
| 今回の改善 | 500ms |
| 改善率 | **約4%** |
| 体感改善 | **ほぼなし** |

### 真のボトルネック候補

今回分析した@rx.var計算は合計でも数百ms。**残り11秒以上が別の場所で消費されている**。

```
イベント発生
  ↓
1. set_prefecture() / set_municipality() イベントハンドラ
  ↓
2. get_filtered_data() → Tursoデータベースクエリ  ← ★最有力候補
  ↓
3. self.df / self.df_full 更新
  ↓
4. @rx.var再計算（数百ms）  ← 今回分析した部分
  ↓
5. Reflexステート同期（サーバー→クライアント）  ← ★有力候補
  ↓
6. フロントエンド再描画
```

**疑わしい箇所**:
1. **Tursoデータベースクエリ**: ネットワークレイテンシ + 61万行からのフィルタリング
2. **Reflexステート同期**: 大きなDataFrameのシリアライズ・転送
3. **フロントエンド**: 多数のRechartsグラフ再描画

---

## 6. 次のステップ

### Phase 2調査: 真のボトルネック特定

イベントハンドラにタイミング計測を追加し、12秒の内訳を特定する：

```python
async def set_prefecture(self, value: str):
    import time
    t0 = time.time()

    # データベースクエリ
    df_data = get_filtered_data(...)
    print(f"[PERF] DB query: {time.time() - t0:.2f}s")

    t1 = time.time()
    async with self:
        self.df = df_data
    print(f"[PERF] State update: {time.time() - t1:.2f}s")

    print(f"[PERF] Total handler: {time.time() - t0:.2f}s")
```

### 予想される原因と対策

| 原因 | 対策案 |
|------|--------|
| Tursoクエリが遅い | クエリ最適化、インデックス追加、キャッシュ強化 |
| DataFrameシリアライズ | df/df_fullのサイズ削減、必要カラムのみ保持 |
| ステート同期 | WebSocket最適化、差分更新 |
| フロントエンド描画 | 仮想化、遅延レンダリング |

---

## 7. バックアップ情報

| 項目 | パス |
|------|------|
| 元ファイル | `backup_20251212_perf_optimization/mapcomplete_dashboard.py` |
| サイズ | 391,238 bytes |

---

## 8. 検証結果

| チェック項目 | 結果 |
|--------------|------|
| Python構文チェック | ✅ 成功 |
| Reflexインポート | ✅ 成功 |
| DashboardState読み込み | ✅ 成功 |

---

## 9. 教訓

1. **事前のプロファイリングが重要**: 推測ではなく実測でボトルネックを特定すべきだった
2. **全体の待機時間を把握してから最適化**: 12秒中0.5秒の改善では意味がない
3. **Reflexの@rx.var最適化は限定的**: 真のボトルネックがDB/ネットワークにある場合、効果は薄い

---

*このドキュメントは2025年12月12日の作業に基づいています。*
