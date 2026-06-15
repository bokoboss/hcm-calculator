"""Method registry scaffold."""

from dataclasses import dataclass

from hcmcalc.core import CalculationMethod, MethodNotImplementedError
from hcmcalc.methods.multilane_highway_los import MultilaneHighwayLOSMethod
from hcmcalc.methods.two_lane_highway_ch15 import TwoLaneHighwayChapter15Method


@dataclass(frozen=True)
class MethodMetadata:
    """Describes a planned or implemented HCM method."""

    key: str
    facility_type: str
    hcm_reference: str
    status: str


def available_methods() -> list[MethodMetadata]:
    """Return known method targets, including future planned methods."""

    return [
        MethodMetadata(
            key="hcm7_ch15_two_lane_motorized",
            facility_type="two_lane_highway",
            hcm_reference="HCM 7th Edition Chapter 15",
            status="implemented_example_only",
        ),
        MethodMetadata(
            key="hcm7_multilane_los",
            facility_type="multilane_highway",
            hcm_reference="HCM 7th Edition Chapter 12 and Chapter 26 Example Problem 4",
            status="implemented_example_only",
        ),
    ]


def get_method(method_key: str, facility_type: str) -> CalculationMethod:
    """Return the registered calculation method for a fixture case."""

    methods: dict[str, CalculationMethod] = {
        TwoLaneHighwayChapter15Method.method_name: TwoLaneHighwayChapter15Method(),
        MultilaneHighwayLOSMethod.method_name: MultilaneHighwayLOSMethod(),
    }
    method = methods.get(method_key)
    if method is None:
        raise MethodNotImplementedError(f"Unknown calculation method: {method_key}")
    if method.facility_type != facility_type:
        raise MethodNotImplementedError(
            f"Method {method_key} does not support facility type {facility_type}."
        )
    return method
