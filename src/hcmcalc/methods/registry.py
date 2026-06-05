"""Method registry scaffold."""

from dataclasses import dataclass


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
            status="planned",
        ),
        MethodMetadata(
            key="hcm7_multilane_los",
            facility_type="multilane_highway",
            hcm_reference="HCM 7th Edition Multilane Highway LOS",
            status="future",
        ),
    ]
