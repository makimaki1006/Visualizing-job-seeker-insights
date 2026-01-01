"""
コロプレスマップ PoC テスト
東京都の市区町村をGeoJSONで描画し、ダミーデータで色分け
"""
import json
import random
from nicegui import ui, app
from pathlib import Path

# GeoJSONファイルのパス
GEOJSON_PATH = Path(__file__).parent / "static" / "geojson" / "tokyo.json"

def load_geojson():
    """GeoJSONデータを読み込む"""
    with open(GEOJSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def get_color(value: float) -> str:
    """値に応じて色を返す（0-100の範囲）"""
    if value >= 80:
        return "#dc2626"  # 赤（高い）
    elif value >= 60:
        return "#f97316"  # オレンジ
    elif value >= 40:
        return "#eab308"  # 黄
    elif value >= 20:
        return "#84cc16"  # 黄緑
    else:
        return "#22c55e"  # 緑（低い）

@ui.page("/")
def main_page():
    ui.label("コロプレスマップ PoC - 東京都").classes("text-2xl font-bold mb-4")

    # GeoJSON読み込み
    geojson_data = load_geojson()

    # ダミーデータ生成（市区町村ごとにランダムな値）
    municipality_values = {}
    for feature in geojson_data["features"]:
        muni_name = feature["properties"].get("N03_004", "不明")
        municipality_values[muni_name] = random.randint(0, 100)

    # 地図作成（東京都の中心付近）
    map_widget = ui.leaflet(center=(35.6895, 139.6917), zoom=10)
    map_widget.classes("w-full h-96")

    # GeoJSONレイヤーを追加
    for feature in geojson_data["features"]:
        muni_name = feature["properties"].get("N03_004", "不明")
        value = municipality_values.get(muni_name, 0)
        color = get_color(value)

        # ポリゴンの座標を取得
        geometry = feature["geometry"]

        if geometry["type"] == "Polygon":
            coords = geometry["coordinates"][0]
            # Leafletは[lat, lng]形式なので変換
            latlngs = [[c[1], c[0]] for c in coords]
            map_widget.generic_layer(
                name="polygon",
                args=[latlngs, {"color": color, "fillColor": color, "fillOpacity": 0.6, "weight": 1}]
            )
        elif geometry["type"] == "MultiPolygon":
            for polygon in geometry["coordinates"]:
                coords = polygon[0]
                latlngs = [[c[1], c[0]] for c in coords]
                map_widget.generic_layer(
                    name="polygon",
                    args=[latlngs, {"color": color, "fillColor": color, "fillOpacity": 0.6, "weight": 1}]
                )

    # 凡例
    with ui.card().classes("mt-4 p-4"):
        ui.label("凡例（ダミーデータ）").classes("font-bold mb-2")
        with ui.row().classes("gap-4"):
            ui.label("80-100").style("background:#dc2626;padding:2px 8px;color:white")
            ui.label("60-79").style("background:#f97316;padding:2px 8px;color:white")
            ui.label("40-59").style("background:#eab308;padding:2px 8px")
            ui.label("20-39").style("background:#84cc16;padding:2px 8px")
            ui.label("0-19").style("background:#22c55e;padding:2px 8px;color:white")

    # 市区町村リスト表示
    with ui.expansion("市区町村データ（63件）").classes("mt-4"):
        for muni, value in sorted(municipality_values.items(), key=lambda x: -x[1]):
            ui.label(f"{muni}: {value}")

if __name__ in {"__main__", "__mp_main__"}:
    print(f"GeoJSON path: {GEOJSON_PATH}")
    print(f"GeoJSON exists: {GEOJSON_PATH.exists()}")
    ui.run(port=8089, title="コロプレスマップ PoC")
