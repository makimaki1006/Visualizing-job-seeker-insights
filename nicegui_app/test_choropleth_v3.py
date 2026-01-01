"""
コロプレスマップ 完全実装版 v3
- 東京都の市区町村をGeoJSONで描画
- Tursoから取得した実データで色分け
- ★ 地図クリックで市区町村選択
- ★ 選択地域のハイライト表示
- ★ 表示モード切替の実動作（4モード）
- ★ 関係地域の地図上可視化（線・色分け）
"""
import json
from nicegui import ui, app
from pathlib import Path
import os
from dotenv import load_dotenv

# 環境変数読み込み
load_dotenv()

# db_helperからデータ取得関数をインポート
from db_helper import query_df

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

# 選択・関係地域の色（地図と同化しない色を使用）
HIGHLIGHT_COLOR = "#00d4ff"  # 選択時のハイライト色（シアン - 目立つ）
INFLOW_COLOR = "#00ff88"     # 流入元の色（明るい緑）
COMPETING_COLOR = "#ff00ff"  # 競合地域の色（マゼンタ - 赤と区別）

# 線の色（ポリゴンと別の色で視認性向上）
INFLOW_LINE_COLOR = "#00ffff"    # 流入線（シアン）
COMPETING_LINE_COLOR = "#ff66ff" # 競合線（ピンク/マゼンタ）


def load_geojson():
    """GeoJSONデータを読み込む"""
    with open(GEOJSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def point_in_polygon(lat: float, lng: float, polygon_coords: list) -> bool:
    """点が多角形内にあるかをレイキャスティング法で判定"""
    n = len(polygon_coords)
    inside = False

    j = n - 1
    for i in range(n):
        # polygon_coords は [[lat, lng], ...] 形式
        yi, xi = polygon_coords[i][0], polygon_coords[i][1]
        yj, xj = polygon_coords[j][0], polygon_coords[j][1]

        if ((yi > lat) != (yj > lat)) and (lng < (xj - xi) * (lat - yi) / (yj - yi) + xi):
            inside = not inside
        j = i

    return inside


def find_municipality_at_point(lat: float, lng: float, geojson_data: dict) -> str:
    """指定座標にある市区町村を見つける"""
    for feature in geojson_data["features"]:
        props = feature["properties"]
        muni_name = props.get("N03_004", "")
        if not muni_name:
            continue

        geometry = feature["geometry"]

        if geometry["type"] == "Polygon":
            coords = geometry["coordinates"][0]
            # GeoJSONは [lng, lat] 形式なので [lat, lng] に変換
            latlngs = [[c[1], c[0]] for c in coords]
            if point_in_polygon(lat, lng, latlngs):
                return muni_name

        elif geometry["type"] == "MultiPolygon":
            for polygon in geometry["coordinates"]:
                coords = polygon[0]
                latlngs = [[c[1], c[0]] for c in coords]
                if point_in_polygon(lat, lng, latlngs):
                    return muni_name

    return None


# ========== データ取得関数 ==========

def get_municipality_data(pref: str = "東京都") -> dict:
    """市区町村ごとの求職者データを取得（拡張版）"""
    try:
        sql = """
            SELECT municipality, applicant_count, latitude, longitude,
                   avg_age, male_count, female_count, female_ratio,
                   top_age_group, top_age_ratio, avg_desired_areas
            FROM job_seeker_data
            WHERE row_type = 'SUMMARY'
            AND prefecture = ?
            AND municipality IS NOT NULL
            AND municipality != ''
        """
        df = query_df(sql, (pref,))

        if df.empty:
            return {}

        data = {}
        for _, row in df.iterrows():
            muni_name = row.get("municipality", "")
            if muni_name:
                count = int(float(row.get("applicant_count", 0) or 0))
                male = int(float(row.get("male_count", 0) or 0))
                female = int(float(row.get("female_count", 0) or 0))
                data[muni_name] = {
                    "count": count,
                    "lat": float(row.get("latitude", 0) or 0),
                    "lng": float(row.get("longitude", 0) or 0),
                    # 追加情報
                    "avg_age": float(row.get("avg_age", 0) or 0),
                    "male_count": male,
                    "female_count": female,
                    "female_ratio": float(row.get("female_ratio", 0) or 0),
                    "top_age_group": row.get("top_age_group", ""),
                    "top_age_ratio": float(row.get("top_age_ratio", 0) or 0),
                    "avg_desired_areas": float(row.get("avg_desired_areas", 0) or 0),
                }
        return data
    except Exception as e:
        print(f"[CHOROPLETH] get_municipality_data error: {e}")
        return {}


def get_inflow_data(pref: str = "東京都") -> dict:
    """各市区町村への流入数を取得"""
    try:
        sql = """
            SELECT desired_municipality, SUM(count) as total_inflow
            FROM job_seeker_data
            WHERE row_type = 'RESIDENCE_FLOW'
            AND desired_prefecture = ?
            AND desired_municipality IS NOT NULL
            GROUP BY desired_municipality
        """
        df = query_df(sql, (pref,))

        if df.empty:
            return {}

        return {row["desired_municipality"]: int(float(row.get("total_inflow", 0) or 0))
                for _, row in df.iterrows()}
    except Exception as e:
        print(f"[CHOROPLETH] get_inflow_data error: {e}")
        return {}


def get_outflow_data(pref: str = "東京都") -> dict:
    """各市区町村からの流出数を取得"""
    try:
        sql = """
            SELECT municipality, SUM(count) as total_outflow
            FROM job_seeker_data
            WHERE row_type = 'RESIDENCE_FLOW'
            AND prefecture = ?
            AND municipality IS NOT NULL
            GROUP BY municipality
        """
        df = query_df(sql, (pref,))

        if df.empty:
            return {}

        return {row["municipality"]: int(float(row.get("total_outflow", 0) or 0))
                for _, row in df.iterrows()}
    except Exception as e:
        print(f"[CHOROPLETH] get_outflow_data error: {e}")
        return {}


def get_competition_intensity(pref: str = "東京都") -> dict:
    """各市区町村の競合強度（併願される回数）を取得"""
    try:
        sql = """
            SELECT co_desired_municipality, SUM(count) as competition_count
            FROM job_seeker_data
            WHERE row_type = 'DESIRED_AREA_PATTERN'
            AND co_desired_prefecture = ?
            AND co_desired_municipality IS NOT NULL
            GROUP BY co_desired_municipality
        """
        df = query_df(sql, (pref,))

        if df.empty:
            return {}

        return {row["co_desired_municipality"]: int(float(row.get("competition_count", 0) or 0))
                for _, row in df.iterrows()}
    except Exception as e:
        print(f"[CHOROPLETH] get_competition_intensity error: {e}")
        return {}


def get_inflow_sources(target_pref: str, target_muni: str) -> list:
    """特定市区町村への流入元を取得"""
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
            muni = row.get('municipality', '')
            results.append({
                "municipality": muni,
                "full_name": f"{row.get('prefecture', '')}{muni}",
                "count": int(float(row.get("total_count", 0) or 0))
            })
        return results
    except Exception as e:
        print(f"[CHOROPLETH] get_inflow_sources error: {e}")
        return []


def get_competing_areas(target_pref: str, target_muni: str) -> list:
    """特定市区町村と競合する地域を取得"""
    try:
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
            muni = row.get('co_desired_municipality', '')
            results.append({
                "municipality": muni,
                "full_name": f"{row.get('co_desired_prefecture', '')}{muni}",
                "count": int(float(row.get("overlap_count", 0) or 0))
            })
        return results
    except Exception as e:
        print(f"[CHOROPLETH] get_competing_areas error: {e}")
        return []


# ========== 色分けロジック ==========

def get_color_by_value(value: float, max_value: float, mode: str = "default") -> str:
    """値に応じて色を返す（モード別）"""
    if max_value == 0:
        return "#9ca3af"

    ratio = value / max_value

    if mode == "balance":
        # 流出入バランス: 赤（流出超過）〜白（均衡）〜青（流入超過）
        if ratio > 0.6:
            return "#3b82f6"  # 青（流入超過）
        elif ratio > 0.4:
            return "#93c5fd"  # 薄青
        elif ratio > 0.3:
            return "#f1f5f9"  # 白（均衡）
        elif ratio > 0.2:
            return "#fca5a5"  # 薄赤
        else:
            return "#dc2626"  # 赤（流出超過）
    else:
        # デフォルト: 緑（少）〜赤（多）
        if ratio >= 0.8:
            return "#dc2626"
        elif ratio >= 0.6:
            return "#f97316"
        elif ratio >= 0.4:
            return "#eab308"
        elif ratio >= 0.2:
            return "#84cc16"
        else:
            return "#22c55e"


# ========== メインページ ==========

@ui.page("/")
def main_page(municipality: str = None, mode: str = None):
    """メインページ
    Args:
        municipality: クエリパラメータで選択された市区町村
        mode: クエリパラメータで選択された表示モード
    """
    # ダークモード有効化
    ui.dark_mode().enable()
    ui.query("body").style(f"background-color: {BG_COLOR}")

    # 状態管理（クエリパラメータから初期化）
    state = app.storage.user
    if municipality:
        state["selected_municipality"] = municipality
    else:
        state.setdefault("selected_municipality", None)

    if mode:
        state["display_mode"] = mode
    else:
        state.setdefault("display_mode", "求職者数")

    # データ読み込み
    geojson_data = load_geojson()
    municipality_data = get_municipality_data("東京都")
    inflow_data = get_inflow_data("東京都")
    outflow_data = get_outflow_data("東京都")
    competition_data = get_competition_intensity("東京都")

    # 表示モードに応じたデータ選択
    current_mode = state.get("display_mode", "求職者数")

    if current_mode == "求職者数":
        display_data = {k: v["count"] for k, v in municipality_data.items()}
        legend_labels = ["多", "", "", "", "少"]
    elif current_mode == "流入元":
        display_data = inflow_data
        legend_labels = ["多", "", "", "", "少"]
    elif current_mode == "流出/流入バランス":
        # バランス計算: 流入 / (流入 + 流出)
        display_data = {}
        for muni in municipality_data.keys():
            inflow = inflow_data.get(muni, 0)
            outflow = outflow_data.get(muni, 0)
            total = inflow + outflow
            if total > 0:
                display_data[muni] = inflow / total
            else:
                display_data[muni] = 0.5
        legend_labels = ["流入超過", "", "均衡", "", "流出超過"]
    elif current_mode == "競合地域":
        display_data = competition_data
        legend_labels = ["激戦", "", "", "", "穏やか"]
    else:
        display_data = {k: v["count"] for k, v in municipality_data.items()}
        legend_labels = ["多", "", "", "", "少"]

    max_value = max(display_data.values()) if display_data else 1
    color_mode = "balance" if current_mode == "流出/流入バランス" else "default"

    # 選択中の市区町村の関連データ
    selected_muni = state.get("selected_municipality")
    inflow_sources = []
    competing_areas = []
    related_municipalities = set()

    if selected_muni:
        inflow_sources = get_inflow_sources("東京都", selected_muni)
        competing_areas = get_competing_areas("東京都", selected_muni)
        # 関連市区町村のセットを作成
        for item in inflow_sources[:5]:
            if item["municipality"]:
                related_municipalities.add(("inflow", item["municipality"]))
        for item in competing_areas[:5]:
            if item["municipality"]:
                related_municipalities.add(("competing", item["municipality"]))

    # GeoJSON内の市区町村名 -> 座標中心点マッピング
    muni_centers = {}
    for feature in geojson_data["features"]:
        props = feature["properties"]
        muni_name = props.get("N03_004", "")
        if muni_name:
            # 座標の中心を計算
            geometry = feature["geometry"]
            all_coords = []
            if geometry["type"] == "Polygon":
                all_coords = geometry["coordinates"][0]
            elif geometry["type"] == "MultiPolygon":
                for poly in geometry["coordinates"]:
                    all_coords.extend(poly[0])
            if all_coords:
                lats = [c[1] for c in all_coords]
                lngs = [c[0] for c in all_coords]
                muni_centers[muni_name] = {
                    "lat": sum(lats) / len(lats),
                    "lng": sum(lngs) / len(lngs)
                }

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
                def on_mode_change(e):
                    new_mode = e.value
                    # URLパラメータでモードと選択を維持して遷移
                    url = f"/?mode={new_mode}"
                    if selected_muni:
                        url += f"&municipality={selected_muni}"
                    ui.navigate.to(url)

                ui.radio(
                    ["求職者数", "流入元", "流出/流入バランス", "競合地域"],
                    value=current_mode,
                    on_change=on_mode_change
                ).props("inline dark").style(f"color: {TEXT_COLOR}")

            # 地図コンテナ
            map_container = ui.element("div").classes("w-full").style("height: 500px; position: relative;")

            with map_container:
                # Leaflet地図
                map_widget = ui.leaflet(center=(35.6895, 139.6917), zoom=10)
                map_widget.classes("w-full h-full")

                # 地図クリックハンドラ
                def on_map_click(e):
                    """地図クリック時に市区町村を特定して選択"""
                    lat = e.args.get("latlng", {}).get("lat")
                    lng = e.args.get("latlng", {}).get("lng")
                    if lat and lng:
                        clicked_muni = find_municipality_at_point(lat, lng, geojson_data)
                        if clicked_muni:
                            print(f"[CHOROPLETH] Clicked: {clicked_muni} at ({lat}, {lng})")
                            url = f"/?mode={current_mode}&municipality={clicked_muni}"
                            ui.navigate.to(url)

                map_widget.on("map-click", on_map_click)

                # ポリゴンデータをJavaScriptに渡すためのJSON
                polygon_data = []

                for feature in geojson_data["features"]:
                    props = feature["properties"]
                    muni_name = props.get("N03_004", "不明")

                    # 値を取得
                    value = display_data.get(muni_name, 0)

                    # 選択状態・関連状態を判定
                    is_selected = (muni_name == selected_muni)
                    relation_type = None
                    for rel_type, rel_muni in related_municipalities:
                        if rel_muni == muni_name:
                            relation_type = rel_type
                            break

                    # 色を決定
                    if is_selected:
                        fill_color = HIGHLIGHT_COLOR
                        border_color = "#ffffff"
                        border_weight = 4
                        fill_opacity = 0.9
                    elif relation_type == "inflow":
                        fill_color = INFLOW_COLOR
                        border_color = "#ffffff"
                        border_weight = 2
                        fill_opacity = 0.8
                    elif relation_type == "competing":
                        fill_color = COMPETING_COLOR
                        border_color = "#ffffff"
                        border_weight = 2
                        fill_opacity = 0.8
                    else:
                        fill_color = get_color_by_value(value, max_value, color_mode)
                        border_color = "#ffffff"
                        border_weight = 1
                        fill_opacity = 0.7

                    geometry = feature["geometry"]

                    # ポリゴン描画
                    if geometry["type"] == "Polygon":
                        coords = geometry["coordinates"][0]
                        latlngs = [[c[1], c[0]] for c in coords]
                        map_widget.generic_layer(
                            name="polygon",
                            args=[latlngs, {
                                "color": border_color,
                                "fillColor": fill_color,
                                "fillOpacity": fill_opacity,
                                "weight": border_weight,
                                "className": f"muni-polygon muni-{muni_name.replace(' ', '_')}"
                            }]
                        )
                        polygon_data.append({
                            "name": muni_name,
                            "coords": latlngs,
                            "value": value
                        })
                    elif geometry["type"] == "MultiPolygon":
                        for polygon in geometry["coordinates"]:
                            coords = polygon[0]
                            latlngs = [[c[1], c[0]] for c in coords]
                            map_widget.generic_layer(
                                name="polygon",
                                args=[latlngs, {
                                    "color": border_color,
                                    "fillColor": fill_color,
                                    "fillOpacity": fill_opacity,
                                    "weight": border_weight,
                                    "className": f"muni-polygon muni-{muni_name.replace(' ', '_')}"
                                }]
                            )
                            polygon_data.append({
                                "name": muni_name,
                                "coords": latlngs,
                                "value": value
                            })

                # 選択地域と関連地域を結ぶ線を描画（シンプル版 - TOP3のみ）
                if selected_muni and selected_muni in muni_centers:
                    selected_center = muni_centers[selected_muni]

                    # 流入元からの線（緑 - TOP3のみ、シンプルな線）
                    for i, item in enumerate(inflow_sources[:3]):
                        muni = item["municipality"]
                        if muni in muni_centers and muni != selected_muni:
                            source_center = muni_centers[muni]
                            line_coords = [
                                [source_center["lat"], source_center["lng"]],
                                [selected_center["lat"], selected_center["lng"]]
                            ]
                            # 線の太さを順位で変える（1位が太い）
                            weight = 4 - i  # 3, 2, 1
                            map_widget.generic_layer(
                                name="polyline",
                                args=[line_coords, {
                                    "color": INFLOW_LINE_COLOR,
                                    "weight": weight,
                                    "opacity": 0.9
                                }]
                            )

                    # 競合地域への線（マゼンタ - TOP3のみ、破線）
                    for i, item in enumerate(competing_areas[:3]):
                        muni = item["municipality"]
                        if muni in muni_centers and muni != selected_muni:
                            target_center = muni_centers[muni]
                            line_coords = [
                                [selected_center["lat"], selected_center["lng"]],
                                [target_center["lat"], target_center["lng"]]
                            ]
                            weight = 4 - i  # 3, 2, 1
                            map_widget.generic_layer(
                                name="polyline",
                                args=[line_coords, {
                                    "color": COMPETING_LINE_COLOR,
                                    "weight": weight,
                                    "opacity": 0.9,
                                    "dashArray": "8, 6"
                                }]
                            )

                # ホバーエフェクト用のJavaScript（クリックはNiceGUIのmap-clickで処理）
                ui.run_javascript('''
                    // ホバーエフェクトを追加
                    setTimeout(() => {
                        const paths = document.querySelectorAll('.leaflet-overlay-pane path');
                        paths.forEach(path => {
                            path.style.cursor = 'pointer';
                            const originalStrokeWidth = path.style.strokeWidth || '1';
                            const originalOpacity = path.style.fillOpacity || '0.7';

                            path.addEventListener('mouseenter', () => {
                                path.style.strokeWidth = '3';
                                path.style.fillOpacity = '0.85';
                            });

                            path.addEventListener('mouseleave', () => {
                                path.style.strokeWidth = originalStrokeWidth;
                                path.style.fillOpacity = originalOpacity;
                            });
                        });
                        console.log('[CHOROPLETH] Hover effects added to', paths.length, 'paths');
                    }, 1000);
                ''')

            # 凡例
            with ui.row().classes("mt-4 gap-2 items-center"):
                ui.label("凡例:").style(f"color: {TEXT_COLOR}; font-weight: bold")

                if current_mode == "流出/流入バランス":
                    ui.label(legend_labels[0]).style(f"background: #3b82f6; color: white; padding: 2px 8px; border-radius: 4px")
                    ui.label("").style(f"background: #93c5fd; padding: 2px 8px; border-radius: 4px")
                    ui.label(legend_labels[2]).style(f"background: #f1f5f9; color: #1e293b; padding: 2px 8px; border-radius: 4px")
                    ui.label("").style(f"background: #fca5a5; padding: 2px 8px; border-radius: 4px")
                    ui.label(legend_labels[4]).style(f"background: #dc2626; color: white; padding: 2px 8px; border-radius: 4px")
                else:
                    ui.label(legend_labels[0]).style(f"background: #dc2626; color: white; padding: 2px 8px; border-radius: 4px")
                    ui.label("").style(f"background: #f97316; padding: 2px 8px; border-radius: 4px")
                    ui.label("").style(f"background: #eab308; padding: 2px 8px; border-radius: 4px")
                    ui.label("").style(f"background: #84cc16; padding: 2px 8px; border-radius: 4px")
                    ui.label(legend_labels[4]).style(f"background: #22c55e; color: white; padding: 2px 8px; border-radius: 4px")

                # 関係性の凡例（選択時のみ - より詳細に）
                if selected_muni:
                    ui.label("|").style(f"color: {MUTED_COLOR}; margin: 0 8px")
                    # 選択中
                    ui.label("選択中").style(f"background: {HIGHLIGHT_COLOR}; color: #000; padding: 2px 8px; border-radius: 4px; font-weight: bold")
                    # 流入元（エリア + 線）
                    with ui.row().classes("items-center gap-1"):
                        ui.element("span").style(f"display: inline-block; width: 20px; height: 4px; background: {INFLOW_LINE_COLOR}; border-radius: 2px")
                        ui.label("→流入").style(f"background: {INFLOW_COLOR}; color: #000; padding: 2px 6px; border-radius: 4px; font-size: 11px")
                    # 競合（エリア + 線）
                    with ui.row().classes("items-center gap-1"):
                        ui.element("span").style(f"display: inline-block; width: 20px; height: 4px; background: {COMPETING_LINE_COLOR}; border-radius: 2px; border: 1px dashed #fff")
                        ui.label("⇔競合").style(f"background: {COMPETING_COLOR}; color: #fff; padding: 2px 6px; border-radius: 4px; font-size: 11px")

        # 右側: サマリーカード
        with ui.card().classes("w-80").style(
            f"background-color: {CARD_BG}; border: 1px solid {BORDER_COLOR}"
        ):
            ui.label("サマリー").classes("text-lg font-bold mb-4").style(f"color: {TEXT_COLOR}")

            # 市区町村選択ドロップダウン
            muni_options = ["選択してください"] + sorted(municipality_data.keys())

            def on_muni_select(e):
                new_muni = e.value if e.value != "選択してください" else None
                # URLパラメータでモードと選択を維持して遷移
                url = f"/?mode={current_mode}"
                if new_muni:
                    url += f"&municipality={new_muni}"
                ui.navigate.to(url)

            ui.select(
                muni_options,
                value=selected_muni or "選択してください",
                label="市区町村を選択（または地図をクリック）",
                on_change=on_muni_select
            ).classes("w-full mb-4").props("dark color=white label-color=white")

            # サマリー表示
            if not selected_muni:
                ui.label("市区町村を選択すると詳細が表示されます").style(f"color: {MUTED_COLOR}")
                ui.label("💡 地図上をクリックして選択できます").style(f"color: {MUTED_COLOR}; font-size: 12px; margin-top: 8px")
            else:
                muni_info = municipality_data.get(selected_muni, {})
                count = muni_info.get("count", 0)

                # 基本情報
                ui.label(f"📍 {selected_muni}").classes("text-xl font-bold mb-2").style(f"color: {TEXT_COLOR}")

                with ui.card().classes("w-full mb-3 p-3").style(f"background-color: {PANEL_BG}"):
                    ui.label("求職者数").style(f"color: {MUTED_COLOR}; font-size: 12px")
                    ui.label(f"{count:,} 人").classes("text-2xl font-bold").style(f"color: {PRIMARY_COLOR}")

                # 性別構成
                male_count = muni_info.get("male_count", 0)
                female_count = muni_info.get("female_count", 0)
                female_ratio = muni_info.get("female_ratio", 0)
                if male_count > 0 or female_count > 0:
                    with ui.card().classes("w-full mb-3 p-3").style(f"background-color: {PANEL_BG}"):
                        ui.label("性別構成").style(f"color: {MUTED_COLOR}; font-size: 12px")
                        with ui.row().classes("items-center gap-2"):
                            ui.label(f"👨 {male_count:,}人").style(f"color: #60a5fa; font-weight: bold")
                            ui.label("/").style(f"color: {MUTED_COLOR}")
                            ui.label(f"👩 {female_count:,}人").style(f"color: #f472b6; font-weight: bold")
                        # 女性比率バー
                        with ui.row().classes("w-full items-center gap-2 mt-2"):
                            male_pct = 100 - (female_ratio * 100)
                            female_pct = female_ratio * 100
                            ui.element("div").style(
                                f"height: 8px; width: {male_pct}%; background: #60a5fa; border-radius: 4px 0 0 4px"
                            )
                            ui.element("div").style(
                                f"height: 8px; width: {female_pct}%; background: #f472b6; border-radius: 0 4px 4px 0"
                            )
                        ui.label(f"女性比率: {female_ratio*100:.1f}%").style(f"color: {MUTED_COLOR}; font-size: 11px; margin-top: 4px")

                # 年齢情報
                avg_age = muni_info.get("avg_age", 0)
                top_age_group = muni_info.get("top_age_group", "")
                top_age_ratio = muni_info.get("top_age_ratio", 0)
                if avg_age > 0:
                    with ui.card().classes("w-full mb-3 p-3").style(f"background-color: {PANEL_BG}"):
                        ui.label("年齢構成").style(f"color: {MUTED_COLOR}; font-size: 12px")
                        with ui.row().classes("items-baseline gap-2"):
                            ui.label(f"平均 {avg_age:.1f}歳").classes("text-lg font-bold").style(f"color: {TEXT_COLOR}")
                        if top_age_group:
                            ui.label(f"最多: {top_age_group} ({top_age_ratio*100:.1f}%)").style(f"color: {MUTED_COLOR}; font-size: 11px; margin-top: 4px")

                # 平均希望エリア数
                avg_areas = muni_info.get("avg_desired_areas", 0)
                if avg_areas > 0:
                    with ui.card().classes("w-full mb-3 p-3").style(f"background-color: {PANEL_BG}"):
                        ui.label("平均希望エリア数").style(f"color: {MUTED_COLOR}; font-size: 12px")
                        ui.label(f"{avg_areas:.1f} 箇所").classes("text-lg font-bold").style(f"color: {TEXT_COLOR}")
                        # 多い/少ないの目安
                        if avg_areas > 15:
                            ui.label("📍 広範囲に就活中").style(f"color: #fbbf24; font-size: 11px")
                        elif avg_areas < 5:
                            ui.label("🎯 地元志向が強い").style(f"color: #34d399; font-size: 11px")

                # 表示モードに応じた追加情報
                if current_mode == "流入元":
                    inflow_count = inflow_data.get(selected_muni, 0)
                    with ui.card().classes("w-full mb-3 p-3").style(f"background-color: {PANEL_BG}"):
                        ui.label("総流入数").style(f"color: {MUTED_COLOR}; font-size: 12px")
                        ui.label(f"{inflow_count:,} 人").classes("text-2xl font-bold").style(f"color: {INFLOW_COLOR}")

                elif current_mode == "流出/流入バランス":
                    inflow_count = inflow_data.get(selected_muni, 0)
                    outflow_count = outflow_data.get(selected_muni, 0)
                    balance = inflow_count - outflow_count
                    with ui.card().classes("w-full mb-3 p-3").style(f"background-color: {PANEL_BG}"):
                        ui.label("流入/流出バランス").style(f"color: {MUTED_COLOR}; font-size: 12px")
                        balance_color = "#3b82f6" if balance > 0 else "#dc2626" if balance < 0 else TEXT_COLOR
                        balance_text = f"+{balance:,}" if balance > 0 else f"{balance:,}"
                        ui.label(f"{balance_text} 人").classes("text-2xl font-bold").style(f"color: {balance_color}")
                        ui.label(f"(流入: {inflow_count:,} / 流出: {outflow_count:,})").style(f"color: {MUTED_COLOR}; font-size: 11px")

                elif current_mode == "競合地域":
                    comp_count = competition_data.get(selected_muni, 0)
                    with ui.card().classes("w-full mb-3 p-3").style(f"background-color: {PANEL_BG}"):
                        ui.label("競合強度（併願回数）").style(f"color: {MUTED_COLOR}; font-size: 12px")
                        ui.label(f"{comp_count:,} 回").classes("text-2xl font-bold").style(f"color: {COMPETING_COLOR}")

                # 流入元TOP5
                ui.label("🔽 流入元 TOP5").classes("font-bold mt-4 mb-2").style(f"color: {TEXT_COLOR}")
                if inflow_sources:
                    for i, item in enumerate(inflow_sources[:5]):
                        source = item.get("full_name", "不明")
                        cnt = item.get("count", 0)
                        with ui.row().classes("w-full justify-between items-center"):
                            with ui.row().classes("items-center gap-1"):
                                ui.element("span").style(f"display: inline-block; width: 8px; height: 8px; background: {INFLOW_COLOR}; border-radius: 50%")
                                ui.label(f"{i+1}. {source}").style(f"color: {TEXT_COLOR}")
                            ui.label(f"{cnt}人").style(f"color: {MUTED_COLOR}")
                else:
                    ui.label("データなし").style(f"color: {MUTED_COLOR}")

                # 競合地域TOP5
                ui.label("⚔️ 競合地域 TOP5").classes("font-bold mt-4 mb-2").style(f"color: {TEXT_COLOR}")
                if competing_areas:
                    for i, item in enumerate(competing_areas[:5]):
                        area = item.get("full_name", "不明")
                        overlap = item.get("count", 0)
                        with ui.row().classes("w-full justify-between items-center"):
                            with ui.row().classes("items-center gap-1"):
                                ui.element("span").style(f"display: inline-block; width: 8px; height: 8px; background: {COMPETING_COLOR}; border-radius: 50%")
                                ui.label(f"{i+1}. {area}").style(f"color: {TEXT_COLOR}")
                            ui.label(f"{overlap}人").style(f"color: {MUTED_COLOR}")
                else:
                    ui.label("データなし").style(f"color: {MUTED_COLOR}")

    # フッター
    with ui.footer().style(f"background-color: {BG_COLOR}; border-top: 1px solid {BORDER_COLOR}"):
        total_count = sum([d["count"] for d in municipality_data.values()])
        mode_text = f"表示モード: {current_mode}"
        selected_text = f" | 選択: {selected_muni}" if selected_muni else ""
        ui.label(f"東京都 総求職者数: {total_count:,}人 | 市区町村数: {len(municipality_data)} | {mode_text}{selected_text}").style(f"color: {MUTED_COLOR}")


if __name__ in {"__main__", "__mp_main__"}:
    print(f"[CHOROPLETH v3] Starting...")
    print(f"[CHOROPLETH v3] GeoJSON path: {GEOJSON_PATH}")
    print(f"[CHOROPLETH v3] GeoJSON exists: {GEOJSON_PATH.exists()}")
    ui.run(host="0.0.0.0", port=8089, title="人材地図 PoC v3", storage_secret="choropleth_poc_v3", reload=False)
