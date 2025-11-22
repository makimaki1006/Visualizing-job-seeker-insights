import json
import re
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
HTML_PATH = PROJECT_ROOT / "gas_files" / "html" / "map_complete_prototype_Ver2.html"
PHASE7_SUPPLY = PROJECT_ROOT / "python_scripts" / "data" / "output_v2" / "phase7" / "SupplyDensityMap.csv"


def _load_embedded_payload():
    html = HTML_PATH.read_text(encoding="utf-8")
    match = re.search(
        r'<script type="application/json" id="embeddedData">(.*?)</script>',
        html,
        re.S,
    )
    if not match:
        raise AssertionError("embeddedData payload not found in prototype HTML")
    return json.loads(match.group(1))


def test_embedded_payload_structure_matches_supply_outputs():
    payload = _load_embedded_payload()
    assert isinstance(payload, list) and payload, "payload must be a non-empty list"

    supply_df = pd.read_csv(PHASE7_SUPPLY, encoding="utf-8-sig")
    supply_df["location_norm"] = supply_df["location"].str.replace(" ", "")

    for city in payload:
        assert {"name", "overview", "supply", "persona", "urgency"}.issubset(city.keys())

        kpi_total = next(
            (k["value"] for k in city["overview"]["kpis"] if "求職者" in k["label"]),
            None,
        )
        status_sum = sum(city["supply"]["status_counts"].values())
        assert kpi_total == status_sum, f"KPI total mismatch for {city['name']}"

        location_key = city["name"].replace(" ", "")
        match = supply_df[supply_df["location_norm"] == location_key]
        assert not match.empty, f"Supply CSV row missing for {city['name']}"
        csv_count = int(match.iloc[0]["supply_count"])
        assert csv_count >= 0


def test_highlight_cards_render_present():
    html = HTML_PATH.read_text(encoding="utf-8")
    assert "クロス重点指標" in html
    assert "chip-grid" in html
