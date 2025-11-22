"""求人地図ページ

GAS Map.htmlの機能をReflex + Plotlyで再現:
- インタラクティブ地図表示（Plotly Mapbox）
- 地理的フィルタリング（都道府県・市区町村・半径）
- 給与条件フィルタリング
- マーカークリックで詳細表示
- ピン止め機能
- 統計表示
"""

import reflex as rx
import plotly.graph_objects as go
from typing import List, Dict
from job_posting_state import JobPostingState

# 配色（mapcomplete_dashboard.pyと統一）
BG_COLOR = "#0d1525"
PANEL_BG = "rgba(12, 20, 37, 0.95)"
CARD_BG = "rgba(15, 23, 42, 0.82)"
TEXT_COLOR = "#f8fafc"
MUTED_COLOR = "rgba(226, 232, 240, 0.75)"
BORDER_COLOR = "rgba(148, 163, 184, 0.22)"
PRIMARY_COLOR = "#0072B2"
SECONDARY_COLOR = "#E69F00"


def create_map_figure(jobs: List[Dict], center_lat: float, center_lng: float) -> go.Figure:
    """Plotly Mapboxを使用した地図図作成

    Args:
        jobs: 求人データリスト
        center_lat: 中心緯度
        center_lng: 中心経度

    Returns:
        Plotly Figure
    """
    if not jobs:
        # データがない場合は空の地図
        fig = go.Figure(go.Scattermapbox())
        fig.update_layout(
            mapbox=dict(
                style="open-street-map",
                center=dict(lat=center_lat, lon=center_lng),
                zoom=10
            ),
            margin=dict(l=0, r=0, t=0, b=0),
            height=600,
            paper_bgcolor=BG_COLOR,
            plot_bgcolor=BG_COLOR,
        )
        return fig

    # マーカーデータ準備
    lats = [job['latitude'] for job in jobs]
    lons = [job['longitude'] for job in jobs]
    texts = [
        f"<b>{job['facility_name']}</b><br>"
        f"{job['service_type']}<br>"
        f"給与: {job['salary_range']}<br>"
        f"{job['access']}"
        for job in jobs
    ]

    # 給与下限で色分け
    colors = [job['salary_lower'] if job['salary_lower'] else 0 for job in jobs]

    fig = go.Figure(go.Scattermapbox(
        lat=lats,
        lon=lons,
        mode='markers',
        marker=dict(
            size=12,
            color=colors,
            colorscale='Viridis',
            showscale=True,
            colorbar=dict(
                title="給与下限",
                x=1.02,
                bgcolor=CARD_BG,
                bordercolor=BORDER_COLOR,
                borderwidth=1,
                font=dict(color=TEXT_COLOR)
            )
        ),
        text=texts,
        hoverinfo='text',
        customdata=[i for i in range(len(jobs))],  # インデックスを保存
    ))

    fig.update_layout(
        mapbox=dict(
            style="open-street-map",
            center=dict(lat=center_lat, lon=center_lng),
            zoom=11
        ),
        margin=dict(l=0, r=0, t=0, b=0),
        height=600,
        paper_bgcolor=BG_COLOR,
        plot_bgcolor=BG_COLOR,
        font=dict(color=TEXT_COLOR),
        hoverlabel=dict(
            bgcolor=CARD_BG,
            font_color=TEXT_COLOR,
            bordercolor=BORDER_COLOR
        )
    )

    return fig


def filter_panel() -> rx.Component:
    """フィルタパネル（左サイドバー）

    GAS Map.html Line 40-86のコントロール部分
    """
    return rx.box(
        rx.vstack(
            rx.heading("求人地図フィルタ", size="6", color=TEXT_COLOR),

            # 都道府県・市区町村
            rx.hstack(
                rx.vstack(
                    rx.text("都道府県", color=MUTED_COLOR, font_size="14px"),
                    rx.input(
                        placeholder="例: 北海道",
                        value=JobPostingState.prefecture,
                        on_change=JobPostingState.set_prefecture,
                        bg=CARD_BG,
                        border_color=BORDER_COLOR,
                        color=TEXT_COLOR,
                        width="100%"
                    ),
                    spacing="1",
                    width="100%"
                ),
                rx.vstack(
                    rx.text("市区町村", color=MUTED_COLOR, font_size="14px"),
                    rx.input(
                        placeholder="例: 札幌市",
                        value=JobPostingState.municipality,
                        on_change=JobPostingState.set_municipality,
                        bg=CARD_BG,
                        border_color=BORDER_COLOR,
                        color=TEXT_COLOR,
                        width="100%"
                    ),
                    spacing="1",
                    width="100%"
                ),
                spacing="3",
                width="100%"
            ),

            # 検索半径
            rx.vstack(
                rx.text("検索距離 (km)", color=MUTED_COLOR, font_size="14px"),
                rx.hstack(
                    rx.slider(
                        value=JobPostingState.radius_km,
                        on_change=JobPostingState.set_radius_km,
                        min=1,
                        max=50,
                        step=1,
                        width="70%",
                        color_scheme="blue"
                    ),
                    rx.text(
                        JobPostingState.radius_km.to_string() + " km",
                        color=TEXT_COLOR,
                        font_size="14px",
                        width="30%"
                    ),
                    width="100%"
                ),
                spacing="1",
                width="100%"
            ),

            # 給与_雇用形態
            rx.vstack(
                rx.text("給与_雇用形態", color=MUTED_COLOR, font_size="14px"),
                rx.select(
                    ["正職員", "契約職員", "パート・アルバイト", "全て選択"],
                    value=JobPostingState.employment_type_filter,
                    on_change=JobPostingState.set_employment_type_filter,
                    bg=CARD_BG,
                    border_color=BORDER_COLOR,
                    color=TEXT_COLOR,
                    width="100%"
                ),
                spacing="1",
                width="100%"
            ),

            # 給与_区分
            rx.vstack(
                rx.text("給与_区分", color=MUTED_COLOR, font_size="14px"),
                rx.select(
                    ["月給", "時給", "どちらも"],
                    value=JobPostingState.salary_category_filter,
                    on_change=JobPostingState.set_salary_category_filter,
                    bg=CARD_BG,
                    border_color=BORDER_COLOR,
                    color=TEXT_COLOR,
                    width="100%"
                ),
                spacing="1",
                width="100%"
            ),

            # フィルタ実行ボタン
            rx.button(
                "フィルタ実行",
                on_click=JobPostingState.filter_jobs,
                bg=PRIMARY_COLOR,
                color=TEXT_COLOR,
                width="100%",
                size="3"
            ),

            # 統計表示
            rx.cond(
                JobPostingState.total_count > 0,
                rx.box(
                    rx.vstack(
                        rx.heading(f"検索結果: {JobPostingState.total_count}件", size="5", color=TEXT_COLOR),
                        rx.divider(border_color=BORDER_COLOR),
                        rx.text("給与下限", color=MUTED_COLOR, font_size="14px", font_weight="bold"),
                        rx.hstack(
                            rx.text("平均:", color=MUTED_COLOR, font_size="12px"),
                            rx.text(
                                JobPostingState.stats_lower['average'].to_string() + "円",
                                color=TEXT_COLOR,
                                font_size="12px"
                            ),
                            spacing="2"
                        ),
                        rx.hstack(
                            rx.text("中央値:", color=MUTED_COLOR, font_size="12px"),
                            rx.text(
                                JobPostingState.stats_lower['median'].to_string() + "円",
                                color=TEXT_COLOR,
                                font_size="12px"
                            ),
                            spacing="2"
                        ),
                        rx.hstack(
                            rx.text("最頻値:", color=MUTED_COLOR, font_size="12px"),
                            rx.text(
                                JobPostingState.stats_lower['mode'].to_string() + "円",
                                color=TEXT_COLOR,
                                font_size="12px"
                            ),
                            spacing="2"
                        ),
                        rx.text("給与上限", color=MUTED_COLOR, font_size="14px", font_weight="bold", margin_top="2"),
                        rx.hstack(
                            rx.text("平均:", color=MUTED_COLOR, font_size="12px"),
                            rx.text(
                                JobPostingState.stats_upper['average'].to_string() + "円",
                                color=TEXT_COLOR,
                                font_size="12px"
                            ),
                            spacing="2"
                        ),
                        rx.hstack(
                            rx.text("中央値:", color=MUTED_COLOR, font_size="12px"),
                            rx.text(
                                JobPostingState.stats_upper['median'].to_string() + "円",
                                color=TEXT_COLOR,
                                font_size="12px"
                            ),
                            spacing="2"
                        ),
                        rx.hstack(
                            rx.text("最頻値:", color=MUTED_COLOR, font_size="12px"),
                            rx.text(
                                JobPostingState.stats_upper['mode'].to_string() + "円",
                                color=TEXT_COLOR,
                                font_size="12px"
                            ),
                            spacing="2"
                        ),
                        spacing="2",
                        align_items="start"
                    ),
                    bg=CARD_BG,
                    border=f"1px solid {BORDER_COLOR}",
                    border_radius="8px",
                    padding="4",
                    margin_top="4"
                )
            ),

            spacing="4",
            width="100%",
            padding="4"
        ),
        bg=PANEL_BG,
        border_radius="8px",
        width="350px",
        height="100vh",
        overflow_y="auto",
        position="fixed",
        left="0",
        top="0"
    )


def map_panel() -> rx.Component:
    """地図表示パネル（メインエリア）"""
    return rx.box(
        rx.vstack(
            rx.heading("求人地図", size="7", color=TEXT_COLOR),

            # プログレスバー（フィルタ実行中）
            rx.cond(
                JobPostingState.progress_percentage < 100,
                rx.box(
                    rx.vstack(
                        rx.progress(
                            value=JobPostingState.progress_percentage,
                            max=100,
                            width="100%",
                            color_scheme="blue"
                        ),
                        rx.text(
                            JobPostingState.progress_stage,
                            color=TEXT_COLOR,
                            font_size="14px"
                        ),
                        spacing="2"
                    ),
                    bg=CARD_BG,
                    padding="4",
                    border_radius="8px",
                    border=f"1px solid {BORDER_COLOR}"
                )
            ),

            # 地図
            rx.box(
                rx.plotly(
                    data=create_map_figure(
                        JobPostingState.filtered_jobs,
                        JobPostingState.center_lat,
                        JobPostingState.center_lng
                    ),
                    width="100%",
                    height="600px"
                ),
                width="100%"
            ),

            spacing="4",
            width="100%",
            padding="6"
        ),
        margin_left="350px",  # filter_panelの幅
        width="calc(100% - 350px)",
        min_height="100vh",
        bg=BG_COLOR
    )


def job_map_page() -> rx.Component:
    """求人地図ページのメインレイアウト"""
    return rx.box(
        filter_panel(),
        map_panel(),
        width="100%",
        min_height="100vh",
        bg=BG_COLOR
    )
