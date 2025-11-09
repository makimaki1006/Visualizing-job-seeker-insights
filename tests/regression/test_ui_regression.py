from pathlib import Path
import re


PROJECT_ROOT = Path(__file__).resolve().parents[2]
HTML_PATH = PROJECT_ROOT / "gas_files" / "html" / "map_complete_prototype_Ver2.html"


def test_chart_body_wrapper_exists_for_supply_charts():
    html = HTML_PATH.read_text(encoding="utf-8")
    pattern = re.compile(r'<div class="chart-card"><header>[^<]+</header><div class="chart-body"><canvas id="spStatus"></canvas></div></div>')
    assert pattern.search(html), "chart-body wrapper missing for spStatus chart"


def test_quality_badge_placeholder_retained():
    html = HTML_PATH.read_text(encoding="utf-8")
    assert 'id="qualityBadge"' in html and "quality-badge" in html
