"""
コロプレスマップ 本実装テスト
- 東京都の市区町村をGeoJSONで描画
- Tursoから取得した実データで色分け
- クリックでサマリーカード表示
- 選択した市区町村の関係性を可視化
"""
import json
from nicegui import ui, app
from pathlib import Path
import os
from dotenv import load_dotenv

# 環境変数読み込み
load_dotenv()

# db_helperからデータ取得関数をインポート
from db_helper import (
    get_all_data,
    get_map_markers,
    query_df,
)


def get_inflow_sources_v2(target_pref: str, target_muni: str) -> list:
    """流入元データを取得（正しいカラム名を使用）"""
    try:
        sql = """
            SELECT prefecture, municipality, SUM(count) as total_count
            FROM job_seeker_data
            WHERE row_type = 'RESIDENCE_FLOW'
            AND desired_prefecture = ?
            AND desired_municipality = ?
            GROUP BY prefecture, municipality
            ORDER BY total_count DESC
            LIMIT 10
        """
        df = query_df(sql, (target_pref, target_muni))

        if df.empty:
            return []

        results = []
        for _, row in df.iterrows():
            results.append({
                "source_area": f"{row.get('prefecture', '')}{row.get('municipality', '')}",
                "count": int(float(row.get("total_count", 0) or 0))
            })
        return results
    except Exception as e:
        print(f"[CHOROPLETH] get_inflow_sources_v2 error: {e}")
        return []


def get_competing_areas_v2(target_pref: str, target_muni: str) -> list:
    """競合地域データを取得（target_muniを希望する人が併願している他の地域）"""
    try:
        # target_muniに居住する求職者が併願している他の地域
        sql = """
            SELECT co_desired_prefecture, co_desired_municipality, SUM(count) as overlap_count
            FROM job_seeker_data
            WHERE row_type = 'DESIRED_AREA_PATTERN'
            AND prefecture = ?
            AND municipality = ?
            AND co_desired_prefecture IS NOT NULL
            AND co_desired_municipality IS NOT NULL
            AND co_desired_municipality != ?
            GROUP BY co_desired_prefecture, co_desired_municipality
            ORDER BY overlap_count DESC
            LIMIT 10
        """
        df = query_df(sql, (target_pref, target_muni, target_muni))

        if df.empty:
            return []

        results = []
        for _, row in df.iterrows():
            area = row.get('co_desired_municipality', '')
            pref = row.get('co_desired_prefecture', '')
            results.append({
                "competing_area": f"{pref}{area}",
                "overlap_count": int(float(row.get("overlap_count", 0) or 0))
            })
        return results
    except Exception as e:
        print(f"[CHOROPLETH] get_competing_areas_v2 error: {e}")
        return []

# GeoJSONファイルのパス
GEOJSON_PATH = Path(__file__).parent / "static" / "geojson" / "tokyo.json"

# テーマカラー
BG_COLOR = "#0f172a"
CARD_BG = "#1e293b"
PANEL_BG = "#1e293b"
BORDER_COLOR = "#334155"
TEXT_COLOR = "#f1f5f9"
MUTED_COLOR = "#94a3b8"
PRIMARY_COLOR = "#3b82f6"


def load_geojson():
    """GeoJSONデータを読み込む"""
    with open(GEOJSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def get_color_by_count(count: int, max_count: int) -> str:
    """求職者数に応じて色を返す"""
    if max_count == 0:
        return "#9ca3af"

    ratio = count / max_count
    if ratio >= 0.8:
        return "#dc2626"  # 赤（非常に多い）
    elif ratio >= 0.6:
        return "#f97316"  # オレンジ
    elif ratio >= 0.4:
        return "#eab308"  # 黄
    elif ratio >= 0.2:
        return "#84cc16"  # 黄緑
    else:
        return "#22c55e"  # 緑（少ない）


def get_municipality_data(pref: str = "東京都"):
    """市区町村ごとの求職者データを取得"""
    # SUMMARYデータから直接取得（applicant_count列を使用）
    from db_helper import query_df

    try:
        sql = """
            SELECT municipality, applicant_count, latitude, longitude
            FROM job_seeker_data
            WHERE row_type = 'SUMMARY'
            AND prefecture = ?
            AND municipality IS NOT NULL
            AND municipality != ''
        """
        df = query_df(sql, (pref,))

        if df.empty:
            print(f"[CHOROPLETH] No SUMMARY data for {pref}")
            return {}

        # 市区町村名 -> データ のマッピング
        data = {}
        for _, row in df.iterrows():
            muni_name = row.get("municipality", "")
            if muni_name:
                count = int(float(row.get("applicant_count", 0) or 0))
                data[muni_name] = {
                    "count": count,
                    "lat": float(row.get("latitude", 0) or 0),
                    "lng": float(row.get("longitude", 0) or 0),
                }

        print(f"[CHOROPLETH] Loaded {len(data)} municipalities, total: {sum(d['count'] for d in data.values())} applicants")
        return data

    except Exception as e:
        print(f"[CHOROPLETH] Error: {e}")
        import traceback
        traceback.print_exc()
        return {}


@ui.page("/")
def main_page():
    ui.query("body").style(f"background-color: {BG_COLOR}")

    # 状態管理
    state = app.storage.user
    state.setdefault("selected_municipality", None)
    state.setdefault("display_mode", "求職者数")

    # GeoJSON読み込み
    geojson_data = load_geojson()

    # 実データ取得
    municipality_data = get_municipality_data("東京都")

    # 最大値を計算（色分け用）
    max_count = max([d["count"] for d in municipality_data.values()]) if municipality_data else 1

    # ヘッダー
    with ui.header().style(f"background-color: {BG_COLOR}; border-bottom: 1px solid {BORDER_COLOR}"):
        ui.label("人材地図 - コロプレスマップ PoC").classes("text-xl font-bold").style(f"color: {TEXT_COLOR}")

    with ui.row().classes("w-full gap-4 p-4"):
        # 左側: 地図
        with ui.card().classes("flex-grow").style(
            f"background-color: {CARD_BG}; border: 1px solid {BORDER_COLOR}; min-width: 600px"
        ):
            ui.label("東京都 市区町村別 求職者分布").classes("text-lg font-bold mb-2").style(f"color: {TEXT_COLOR}")

            # 表示モード選択
            with ui.row().classes("mb-4 gap-4"):
                mode = ui.radio(
                    ["求職者数", "流入元", "流出/流入バランス", "競合地域"],
                    value=state["display_mode"],
                    on_change=lambda e: set_mode(e.value)
                ).props("inline").style(f"color: {TEXT_COLOR}")

            def set_mode(value):
                state["display_mode"] = value
                ui.navigate.reload()

            # 地図（東京都中心）
            map_widget = ui.leaflet(center=(35.6895, 139.6917), zoom=10)
            map_widget.classes("w-full").style("height: 500px")

            # GeoJSONポリゴンを描画
            muni_name_to_code = {}  # N03_007コード -> 市区町村名

            for feature in geojson_data["features"]:
                props = feature["properties"]
                muni_name = props.get("N03_004", "不明")
                muni_code = props.get("N03_007", "")
                muni_name_to_code[muni_code] = muni_name

                # データから求職者数を取得
                muni_info = municipality_data.get(muni_name, {})
                count = muni_info.get("count", 0)

                # 色を決定
                color = get_color_by_count(count, max_count)

                # ポリゴン描画
                geometry = feature["geometry"]

                if geometry["type"] == "Polygon":
                    coords = geometry["coordinates"][0]
                    latlngs = [[c[1], c[0]] for c in coords]
                    map_widget.generic_layer(
                        name="polygon",
                        args=[latlngs, {
                            "color": "#ffffff",
                            "fillColor": color,
                            "fillOpacity": 0.7,
                            "weight": 1
                        }]
                    )
                elif geometry["type"] == "MultiPolygon":
                    for polygon in geometry["coordinates"]:
                        coords = polygon[0]
                        latlngs = [[c[1], c[0]] for c in coords]
                        map_widget.generic_layer(
                            name="polygon",
                            args=[latlngs, {
                                "color": "#ffffff",
                                "fillColor": color,
                                "fillOpacity": 0.7,
                                "weight": 1
                            }]
                        )

            # 凡例
            with ui.row().classes("mt-4 gap-2 items-center"):
                ui.label("凡例:").style(f"color: {TEXT_COLOR}; font-weight: bold")
                ui.label("多").style(f"background: #dc2626; color: white; padding: 2px 8px; border-radius: 4px")
                ui.label("").style(f"background: #f97316; padding: 2px 8px; border-radius: 4px")
                ui.label("").style(f"background: #eab308; padding: 2px 8px; border-radius: 4px")
                ui.label("").style(f"background: #84cc16; padding: 2px 8px; border-radius: 4px")
                ui.label("少").style(f"background: #22c55e; color: white; padding: 2px 8px; border-radius: 4px")

        # 右側: サマリーカード
        with ui.card().classes("w-80").style(
            f"background-color: {CARD_BG}; border: 1px solid {BORDER_COLOR}"
        ):
            ui.label("サマリー").classes("text-lg font-bold mb-4").style(f"color: {TEXT_COLOR}")

            # 市区町村選択ドロップダウン
            muni_options = ["選択してください"] + sorted(municipality_data.keys())

            def on_muni_select(e):
                state["selected_municipality"] = e.value if e.value != "選択してください" else None
                summary_container.refresh()

            ui.select(
                muni_options,
                value=state.get("selected_municipality", "選択してください") or "選択してください",
                label="市区町村を選択",
                on_change=on_muni_select
            ).classes("w-full mb-4")

            @ui.refreshable
            def summary_container():
                selected = state.get("selected_municipality")

                if not selected:
                    ui.label("市区町村を選択すると詳細が表示されます").style(f"color: {MUTED_COLOR}")
                    return

                muni_info = municipality_data.get(selected, {})
                count = muni_info.get("count", 0)

                # 基本情報
                ui.label(f"📍 {selected}").classes("text-xl font-bold mb-2").style(f"color: {TEXT_COLOR}")

                with ui.card().classes("w-full mb-3 p-3").style(f"background-color: {PANEL_BG}"):
                    ui.label("求職者数").style(f"color: {MUTED_COLOR}; font-size: 12px")
                    ui.label(f"{count:,} 人").classes("text-2xl font-bold").style(f"color: {PRIMARY_COLOR}")

                # 流入元TOP5
                ui.label("🔽 流入元 TOP5").classes("font-bold mt-4 mb-2").style(f"color: {TEXT_COLOR}")
                inflow_data = get_inflow_sources_v2("東京都", selected)
                if inflow_data:
                    for i, item in enumerate(inflow_data[:5]):
                        source = item.get("source_area", "不明")
                        cnt = item.get("count", 0)
                        with ui.row().classes("w-full justify-between"):
                            ui.label(f"{i+1}. {source}").style(f"color: {TEXT_COLOR}")
                            ui.label(f"{cnt}人").style(f"color: {MUTED_COLOR}")
                else:
                    ui.label("データなし").style(f"color: {MUTED_COLOR}")

                # 競合地域TOP5
                ui.label("⚔️ 競合地域 TOP5").classes("font-bold mt-4 mb-2").style(f"color: {TEXT_COLOR}")
                competing = get_competing_areas_v2("東京都", selected)
                if competing:
                    for i, item in enumerate(competing[:5]):
                        area = item.get("competing_area", "不明")
                        overlap = item.get("overlap_count", 0)
                        with ui.row().classes("w-full justify-between"):
                            ui.label(f"{i+1}. {area}").style(f"color: {TEXT_COLOR}")
                            ui.label(f"{overlap}人").style(f"color: {MUTED_COLOR}")
                else:
                    ui.label("データなし").style(f"color: {MUTED_COLOR}")

            summary_container()

    # フッター: 統計サマリー
    with ui.footer().style(f"background-color: {BG_COLOR}; border-top: 1px solid {BORDER_COLOR}"):
        total_count = sum([d["count"] for d in municipality_data.values()])
        ui.label(f"東京都 総求職者数: {total_count:,}人 | 市区町村数: {len(municipality_data)}").style(f"color: {MUTED_COLOR}")


if __name__ in {"__main__", "__mp_main__"}:
    print(f"GeoJSON path: {GEOJSON_PATH}")
    print(f"GeoJSON exists: {GEOJSON_PATH.exists()}")
    ui.run(host="0.0.0.0", port=8089, title="人材地図 PoC", storage_secret="choropleth_poc", reload=False)
