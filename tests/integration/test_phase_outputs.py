from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJECT_ROOT / "python_scripts" / "data" / "output_v2"


def test_phase7_supply_density_columns():
    csv_path = OUTPUT_DIR / "phase7" / "SupplyDensityMap.csv"
    assert csv_path.exists()

    df = pd.read_csv(csv_path, encoding="utf-8-sig")
    required = {
        "location",
        "supply_count",
        "avg_age",
        "national_license_count",
        "avg_qualifications",
    }
    assert required.issubset(df.columns)

    numeric_cols = ["supply_count", "avg_age", "national_license_count", "avg_qualifications"]
    numeric_df = df[numeric_cols].apply(pd.to_numeric, errors="coerce")
    assert numeric_df.notnull().all().all()


def test_phase10_urgency_distribution_alignment():
    dist_path = OUTPUT_DIR / "phase10" / "UrgencyDistribution.csv"
    muni_path = OUTPUT_DIR / "phase10" / "UrgencyByMunicipality.csv"
    assert dist_path.exists() and muni_path.exists()

    dist_df = pd.read_csv(dist_path, encoding="utf-8-sig")
    muni_df = pd.read_csv(muni_path, encoding="utf-8-sig")

    assert {"urgency_rank", "count"}.issubset(dist_df.columns)
    assert {"location", "count"}.issubset(muni_df.columns)

    total_from_municipality = pd.to_numeric(muni_df["count"], errors="coerce").sum()
    total_from_distribution = pd.to_numeric(dist_df["count"], errors="coerce").sum()
    assert total_from_distribution > 0
    # by-municipality オリジナル集計は希望勤務地ごとに展開されるため、全体件数以上になることがある
    assert total_from_municipality >= total_from_distribution
