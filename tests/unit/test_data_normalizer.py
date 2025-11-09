from pathlib import Path
import sys

import pandas as pd
import pytest

# --- テスト対象へのパス設定 ---
PROJECT_ROOT = Path(__file__).resolve().parents[2]
PYTHON_DIR = PROJECT_ROOT / "python_scripts"
if str(PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(PYTHON_DIR))

from data_normalizer import DataNormalizer  # noqa: E402
from constants import Gender  # noqa: E402


@pytest.fixture(scope="module")
def normalizer():
    return DataNormalizer()


def test_cap_desired_location_count(normalizer):
    assert normalizer.cap_desired_location_count(120, max_count=50) == 50
    assert normalizer.cap_desired_location_count(10, max_count=50) == 10


@pytest.mark.parametrize(
    "raw,expected_pref",
    [
        ("京都府京都市伏見区", "京都府"),
        ("大阪府大阪市北区", "大阪府"),
    ],
)
def test_parse_desired_area_multiple_locations(normalizer, raw, expected_pref):
    joined = ",".join([raw, raw])
    areas = normalizer.parse_desired_area(joined)
    assert len(areas) == 2
    assert areas[0]["prefecture"] == expected_pref


@pytest.mark.parametrize(
    "value,expected",
    [
        ("男", Gender.MALE),
        ("男性", Gender.MALE),
        ("女", Gender.FEMALE),
        ("女性", Gender.FEMALE),
        (None, None),
    ],
)
def test_normalize_gender(normalizer, value, expected):
    assert normalizer.normalize_gender(value) == expected


def test_apply_missing_value_policy_fills_required_columns(normalizer):
    df = pd.DataFrame(
        [
            {
                "applicant_id": "A001",
                "employment_status": None,
                "education": None,
                "gender": "男",
                "desired_area": None,
            }
        ]
    )
    result = normalizer.apply_missing_value_policy(df)
    assert "employment_status" in result.columns
    assert "education" in result.columns
    assert isinstance(result.loc[0, "desired_area"], list)
