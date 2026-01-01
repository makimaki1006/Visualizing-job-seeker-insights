"""
コロプレスマップ シンプル版（db_helper不使用）
"""
import json
import random
from nicegui import ui
from pathlib import Path

GEOJSON_PATH = Path(__file__).parent / "static" / "geojson" / "tokyo.json"

def load_geojson():
    with open(GEOJSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def get_color(value, max_val):
    if max_val == 0:
        return "#9ca3af"
    ratio = value / max_val
    if ratio >= 0.8:
        return "#dc2626"
    elif ratio >= 0.6:
        return "#f97316"
    elif ratio >= 0.4:
        return "#eab308"
    elif ratio >= 0.2:
        return "#84cc16"
    return "#22c55e"

@ui.page("/")
def main():
    ui.label("コロプレスマップ テスト").classes("text-2xl font-bold mb-4")

    geojson = load_geojson()

    # ダミーデータ
    muni_data = {}
    for f in geojson["features"]:
        name = f["properties"].get("N03_004", "")
        if name:
            muni_data[name] = random.randint(10, 500)

    max_val = max(muni_data.values()) if muni_data else 1

    map_widget = ui.leaflet(center=(35.6895, 139.6917), zoom=10)
    map_widget.classes("w-full").style("height: 600px")

    for feature in geojson["features"]:
        name = feature["properties"].get("N03_004", "")
        count = muni_data.get(name, 0)
        color = get_color(count, max_val)

        geom = feature["geometry"]
        if geom["type"] == "Polygon":
            coords = geom["coordinates"][0]
            latlngs = [[c[1], c[0]] for c in coords]
            map_widget.generic_layer(
                name="polygon",
                args=[latlngs, {"color": "#fff", "fillColor": color, "fillOpacity": 0.7, "weight": 1}]
            )
        elif geom["type"] == "MultiPolygon":
            for poly in geom["coordinates"]:
                coords = poly[0]
                latlngs = [[c[1], c[0]] for c in coords]
                map_widget.generic_layer(
                    name="polygon",
                    args=[latlngs, {"color": "#fff", "fillColor": color, "fillOpacity": 0.7, "weight": 1}]
                )

    # 凡例
    with ui.row().classes("mt-4 gap-2"):
        ui.label("多").style("background:#dc2626;color:white;padding:4px 12px")
        ui.label("").style("background:#f97316;padding:4px 12px")
        ui.label("").style("background:#eab308;padding:4px 12px")
        ui.label("").style("background:#84cc16;padding:4px 12px")
        ui.label("少").style("background:#22c55e;color:white;padding:4px 12px")

if __name__ in {"__main__", "__mp_main__"}:
    print("Starting simple choropleth test...")
    ui.run(host="0.0.0.0", port=8089, title="コロプレスマップ テスト", reload=False)
