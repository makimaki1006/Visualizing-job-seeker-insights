# Reflexでのピン止め地図上配置の実現可能性分析

**作成日**: 2025年11月21日
**質問**: Leaflet + カスタムHTMLは出来なくても、ピン止め地図上配置は出来るか？

---

## 結論: **部分的に可能** ⚠️

Reflexでピン止め地図上配置を実現する方法は**3つ**あります：

| 方法 | 実現可能性 | 難易度 | 制約 | 推奨度 |
|------|-----------|--------|------|--------|
| **A. Plotly annotations** | ✅ **可能** | 低 | 静的配置のみ、ドラッグ不可 | ⭐⭐⭐⭐ 推奨 |
| **B. Plotly + カスタムHTML（絶対配置）** | ✅ **可能** | 中 | 地図との連動が手動、ズーム時にズレる | ⭐⭐⭐ 良い |
| **C. カスタムReactコンポーネント（react-leaflet）** | ✅ **可能** | 高 | Reflexの高度な知識必要 | ⭐⭐ 可能だが複雑 |

---

## 方法A: Plotly annotations（推奨） ⭐⭐⭐⭐

### 概要
Plotlyの`annotations`機能を使用して、地図上に固定テキスト/ボックスを配置

### 実装例

```python
import plotly.graph_objects as go

def create_map_with_annotations(jobs, pinned_jobs):
    """ピン止めカードをPlotly annotationsで表示"""

    # 通常マーカー
    fig = go.Figure(go.Scattermapbox(
        lat=[job['latitude'] for job in jobs],
        lon=[job['longitude'] for job in jobs],
        mode='markers',
        marker=dict(size=10, color='blue')
    ))

    # ピン止めカード（annotations）
    annotations = []
    for job in pinned_jobs:
        annotations.append(dict(
            x=job['longitude'],
            y=job['latitude'],
            text=f"<b>{job['facility_name']}</b><br>"
                 f"給与: {job['salary_range']}<br>"
                 f"{job['access'][:50]}...",
            showarrow=True,
            arrowhead=2,
            arrowsize=1,
            arrowwidth=2,
            arrowcolor='red',
            ax=50,  # 矢印のx方向オフセット
            ay=-50,  # 矢印のy方向オフセット
            bgcolor='rgba(255, 255, 255, 0.9)',
            bordercolor='red',
            borderwidth=2,
            font=dict(size=10, color='black')
        ))

    fig.update_layout(
        mapbox=dict(
            style='open-street-map',
            center=dict(lat=35, lon=139),
            zoom=10
        ),
        annotations=annotations,
        margin=dict(l=0, r=0, t=0, b=0),
        height=600
    )

    return fig
```

### メリット ✅
- ✅ **実装簡単**: Plotlyネイティブ機能
- ✅ **地図と連動**: ズーム・パンに自動追従
- ✅ **矢印表示**: マーカーからカードへの接続線を自動描画
- ✅ **カスタマイズ可能**: 背景色、枠線、フォントなど

### デメリット ❌
- ❌ **ドラッグ不可**: annotationsは固定位置（相対位置調整のみ）
- ❌ **サイズ制限**: テキスト量が多いと表示が崩れる
- ❌ **クリックイベント**: annotations自体のクリックイベントは制限あり

### 推奨度: ⭐⭐⭐⭐
**GASの機能の70%を再現可能**
- ✅ 地図上配置
- ✅ 矢印接続
- ❌ ドラッグ&ドロップ（省略可能）

---

## 方法B: Plotly + カスタムHTML（絶対配置） ⭐⭐⭐

### 概要
Plotlyの地図の上に、Reflexの`rx.box`を絶対配置（`position="absolute"`）でオーバーレイ

### 実装例

```python
import reflex as rx

def map_with_overlay() -> rx.Component:
    """地図の上にピン止めカードをオーバーレイ"""

    return rx.box(
        # 地図（背景）
        rx.plotly(
            data=create_map_figure(...),
            width="100%",
            height="600px"
        ),

        # ピン止めカード（オーバーレイ）
        rx.foreach(
            JobPostingState.pinned_jobs,
            lambda job, idx: rx.box(
                rx.vstack(
                    rx.text(job['facility_name'], font_weight="bold"),
                    rx.text(f"給与: {job['salary_range']}", font_size="12px"),
                    rx.button("×", on_click=lambda: JobPostingState.remove_pinned_job(idx)),
                    spacing="1"
                ),
                position="absolute",
                # 緯度経度から座標変換が必要（手動計算）
                left=f"{calculate_x_from_lng(job['longitude'])}px",
                top=f"{calculate_y_from_lat(job['latitude'])}px",
                bg="white",
                border="2px solid red",
                border_radius="8px",
                padding="2",
                z_index=1000
            )
        ),

        position="relative",
        width="100%",
        height="600px"
    )


def calculate_x_from_lng(lng: float) -> int:
    """経度からピクセル座標を計算（簡易版）

    問題: Plotlyのズーム・パン状態に応じて動的に計算する必要あり
    """
    # 現在の地図の境界（center, zoom）から計算
    # → Plotlyのrelayoutイベントを監視する必要あり（困難）
    pass
```

### メリット ✅
- ✅ **柔軟なUI**: Reflexの全UIコンポーネント使用可能
- ✅ **イベント処理**: ボタンクリック、削除などが自由
- ✅ **複雑なレイアウト**: 複数カード、スクロール可能

### デメリット ❌
- ❌ **座標変換が複雑**: 緯度経度 → ピクセル座標の変換が必要
- ❌ **地図との同期困難**: ズーム・パン時にカードがズレる
- ❌ **Plotlyイベント取得困難**: relayoutイベントの監視がReflexで制限あり

### 推奨度: ⭐⭐⭐
**実装可能だが、地図との連動が不完全**

---

## 方法C: カスタムReactコンポーネント（react-leaflet） ⭐⭐

### 概要
ReactのLeafletライブラリ（react-leaflet）をReflexのカスタムコンポーネントとして統合

### 実装例（概念）

```python
# custom_components/leaflet_map.py
import reflex as rx

class LeafletMap(rx.Component):
    """react-leafletをラップしたReflexコンポーネント"""

    library = "react-leaflet"
    tag = "MapContainer"

    # Props
    center: list[float] = [35, 139]
    zoom: int = 10
    markers: list[dict] = []
    pinned_cards: list[dict] = []

    def get_event_triggers(self):
        return {
            "on_marker_click": lambda marker_id: [marker_id],
            "on_card_drag": lambda card_id, x, y: [card_id, x, y]
        }


# 使用例
def job_map_page():
    return rx.box(
        LeafletMap(
            markers=JobPostingState.filtered_jobs,
            pinned_cards=JobPostingState.pinned_jobs,
            on_marker_click=JobPostingState.on_marker_click,
            on_card_drag=JobPostingState.on_card_drag
        )
    )
```

### メリット ✅
- ✅ **完全機能**: GASと同じLeaflet使用、全機能再現可能
- ✅ **ドラッグ&ドロップ**: 完全対応
- ✅ **カスタムHTML**: 自由に配置可能

### デメリット ❌
- ❌ **実装難易度高**: Reflexのカスタムコンポーネント作成が高度
- ❌ **メンテナンス負担**: Reflexバージョンアップ時に破壊的変更の可能性
- ❌ **ドキュメント不足**: Reflexのカスタムコンポーネント事例が少ない

### 推奨度: ⭐⭐
**技術的に可能だが、工数が大きい（推定3-5日）**

---

## 比較表: 3つの方法

| 評価軸 | A. Plotly annotations | B. Plotly + HTML overlay | C. カスタムReact |
|--------|----------------------|-------------------------|-----------------|
| **実装難易度** | ⭐ 低 | ⭐⭐ 中 | ⭐⭐⭐⭐⭐ 高 |
| **実装工数** | 2時間 | 4-6時間 | 3-5日 |
| **地図上配置** | ✅ 可能 | ✅ 可能 | ✅ 可能 |
| **地図との連動** | ✅ 自動 | ⚠️ 手動同期必要 | ✅ 自動 |
| **ドラッグ&ドロップ** | ❌ 不可 | ❌ 不可 | ✅ 可能 |
| **矢印接続線** | ✅ 自動 | ⚠️ 手動実装 | ✅ 可能 |
| **カスタマイズ性** | ⚠️ 制限あり | ✅ 自由 | ✅ 自由 |
| **メンテナンス性** | ✅ 良好 | ⚠️ 普通 | ❌ 複雑 |
| **総合評価** | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ |

---

## 推奨実装: 方法A（Plotly annotations） ⭐⭐⭐⭐

### 理由

1. **実装工数が最小** - 2時間で完成
2. **地図と完全連動** - ズーム・パンに自動追従
3. **矢印接続線が自動** - GASの点線機能を再現
4. **メンテナンス容易** - Plotlyネイティブ機能

### 妥協点

- ❌ ドラッグ&ドロップ不可 → **許容可能**（装飾機能であり、コア機能ではない）
- ⚠️ カードサイズ制限 → **簡潔な情報のみ表示**（詳細は右サイドバー）

---

## 実装デモコード（方法A）

```python
import reflex as rx
import plotly.graph_objects as go
from typing import List, Dict

class JobMapState(rx.State):
    """求人地図State"""

    filtered_jobs: List[Dict] = []
    pinned_jobs: List[Dict] = []

    def toggle_pin(self, job_index: int):
        """ピン止めトグル"""
        job = self.filtered_jobs[job_index]
        if job in self.pinned_jobs:
            self.pinned_jobs.remove(job)
        else:
            self.pinned_jobs.append(job)


def create_map_with_pinned_cards(
    filtered_jobs: List[Dict],
    pinned_jobs: List[Dict],
    center_lat: float,
    center_lng: float
) -> go.Figure:
    """ピン止めカード付き地図生成"""

    # 通常マーカー
    fig = go.Figure(go.Scattermapbox(
        lat=[job['latitude'] for job in filtered_jobs],
        lon=[job['longitude'] for job in filtered_jobs],
        mode='markers',
        marker=dict(
            size=12,
            color=[job['salary_lower'] for job in filtered_jobs],
            colorscale='Viridis',
            showscale=True
        ),
        text=[job['facility_name'] for job in filtered_jobs],
        hoverinfo='text',
        customdata=[i for i in range(len(filtered_jobs))],
        name='求人'
    ))

    # ピン止めカード（annotations）
    annotations = []
    for idx, job in enumerate(pinned_jobs):
        # カード内容（簡潔版）
        card_text = (
            f"<b>{job['facility_name'][:20]}</b><br>"
            f"💰 {job['salary_range']}<br>"
            f"📍 {job['access'][:30]}..."
        )

        annotations.append(dict(
            lon=job['longitude'],
            lat=job['latitude'],
            text=card_text,
            showarrow=True,
            arrowhead=2,
            arrowsize=1,
            arrowwidth=2,
            arrowcolor='#D55E00',  # 朱色
            ax=60 + (idx * 20),   # 複数カードの重なり防止
            ay=-60 - (idx * 20),
            bgcolor='rgba(255, 255, 255, 0.95)',
            bordercolor='#D55E00',
            borderwidth=2,
            borderpad=4,
            font=dict(
                size=11,
                color='#0d1525',
                family='sans-serif'
            ),
            align='left',
            xanchor='left',
            yanchor='bottom'
        ))

    fig.update_layout(
        mapbox=dict(
            style='open-street-map',
            center=dict(lat=center_lat, lon=center_lng),
            zoom=11
        ),
        annotations=annotations,
        margin=dict(l=0, r=0, t=0, b=0),
        height=600,
        showlegend=False,
        paper_bgcolor='#0d1525',
        plot_bgcolor='#0d1525'
    )

    return fig


def job_map_panel() -> rx.Component:
    """求人地図パネル（ピン止め対応版）"""

    return rx.vstack(
        # 地図
        rx.plotly(
            data=create_map_with_pinned_cards(
                JobMapState.filtered_jobs,
                JobMapState.pinned_jobs,
                JobMapState.center_lat,
                JobMapState.center_lng
            ),
            width="100%",
            height="600px"
        ),

        # ピン止め管理パネル
        rx.box(
            rx.vstack(
                rx.heading(f"ピン止め: {len(JobMapState.pinned_jobs)}件", size="5"),
                rx.foreach(
                    JobMapState.pinned_jobs,
                    lambda job, idx: rx.hstack(
                        rx.text(job['facility_name'], font_size="14px"),
                        rx.button(
                            "解除",
                            on_click=lambda: JobMapState.toggle_pin(idx),
                            size="1"
                        ),
                        spacing="2"
                    )
                ),
                spacing="2"
            ),
            bg="rgba(15, 23, 42, 0.82)",
            padding="4",
            border_radius="8px"
        ),

        spacing="4",
        width="100%"
    )
```

---

## まとめ

### 質問: Leaflet + カスタムHTMLは出来なくてもピン止め地図上配置は出来るか？

### 回答: **はい、可能です** ✅

- **推奨方法**: Plotly annotations（実装工数2時間）
- **実現機能**:
  - ✅ 地図上にカード配置
  - ✅ マーカーからカードへの矢印接続
  - ✅ 地図ズーム・パンに自動追従
  - ✅ 複数カードのピン止め
  - ✅ ピン止め解除
  - ❌ ドラッグ&ドロップ（省略）

### トレードオフ

| 項目 | GAS (Leaflet) | Reflex (Plotly annotations) |
|------|---------------|---------------------------|
| 地図上配置 | ✅ | ✅ |
| 矢印接続 | ✅ (SVG) | ✅ (annotations) |
| ドラッグ&ドロップ | ✅ | ❌ → **許容可能**（装飾機能） |
| 地図連動 | ✅ | ✅ |
| カスタマイズ性 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |

---

## 次のアクション

**Plotly annotationsでピン止め地図上配置を実装しますか？**

実装する場合、以下を進めます：
1. `job_map_page.py`の更新（annotations対応）
2. `job_posting_state.py`へのピン止め機能統合
3. ダッシュボードへの統合
4. テスト実行

実装時間: **約2時間**
