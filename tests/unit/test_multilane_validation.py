from copy import deepcopy
from pathlib import Path

import pytest

from hcmcalc.core import HCMCalcError, UnsupportedScopeError
from hcmcalc.multilane import MultilaneHighwayLOSMethod
from hcmcalc.validation import load_yaml_fixture


ROOT = Path(__file__).resolve().parents[2]


def _eastbound_inputs() -> dict:
    fixture = load_yaml_fixture(ROOT / "references" / "multilane_example_inputs.yaml")
    return deepcopy(fixture["cases"][0]["inputs"])


@pytest.mark.parametrize(
    "unsupported_key",
    [
        "basic_freeway",
        "ramps",
        "merge_diverge",
        "weaving",
        "managed_lanes",
        "work_zone",
        "reliability_analysis",
        "facility_workflow",
        "corridor_workflow",
    ],
)
def test_unsupported_workflows_are_rejected(unsupported_key: str) -> None:
    inputs = _eastbound_inputs()
    inputs[unsupported_key] = True

    with pytest.raises(UnsupportedScopeError):
        MultilaneHighwayLOSMethod().calculate(inputs)


def test_unsupported_lane_count_is_rejected() -> None:
    inputs = _eastbound_inputs()
    inputs["number_of_lanes"] = 3

    with pytest.raises(UnsupportedScopeError, match="number_of_lanes"):
        MultilaneHighwayLOSMethod().calculate(inputs)


def test_non_finite_and_physically_invalid_inputs_are_rejected() -> None:
    inputs = _eastbound_inputs()
    inputs["demand_volume_veh_h"] = float("nan")
    with pytest.raises(HCMCalcError, match="finite"):
        MultilaneHighwayLOSMethod().calculate(inputs)

    inputs = _eastbound_inputs()
    inputs["peak_hour_factor"] = 0.0
    with pytest.raises(HCMCalcError, match="peak_hour_factor"):
        MultilaneHighwayLOSMethod().calculate(inputs)


def test_missing_required_input_is_rejected() -> None:
    inputs = _eastbound_inputs()
    del inputs["median_type"]

    with pytest.raises(HCMCalcError, match="median_type"):
        MultilaneHighwayLOSMethod().calculate(inputs)
