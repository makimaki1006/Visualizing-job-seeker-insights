import pytest

import main


def test_prefecture_order_definition():
    # Ensure we have the full JIS list in order (North -> South)
    assert len(main.PREFECTURE_ORDER) == 47
    assert main.PREFECTURE_ORDER[0] == "北海道"
    assert main.PREFECTURE_ORDER[-1] == "沖縄県"
    # No duplicates
    assert len(set(main.PREFECTURE_ORDER)) == 47


def test_load_and_clean_data():
    df = main._clean_dataframe(main.load_data())
    # basic sanity
    assert not df.empty
    assert "prefecture" in df.columns
    assert "municipality" in df.columns
    # SUMMARYのみ
    if "row_type" in df.columns:
        assert set(df["row_type"].unique()) <= {"SUMMARY"}
    # prefectureは空でない
    assert df["prefecture"].astype(bool).all()


def test_prefecture_options_sorted():
    df = main._clean_dataframe(main.load_data())
    unique_prefs = [p for p in df["prefecture"].dropna().unique().tolist() if p]
    order_map = {pref: idx for idx, pref in enumerate(main.PREFECTURE_ORDER)}
    unique_prefs.sort(key=lambda x: order_map.get(x, len(main.PREFECTURE_ORDER) + 1))
    assert unique_prefs[0] == "北海道"
    assert unique_prefs[-1] == "沖縄県"
