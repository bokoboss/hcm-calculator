"""Shared capacity helpers for HCM 7.0 ramp influence methods."""

from hcmcalc.core import HCMCalcError


MAX_DESIRABLE_MERGE_PC_H = 4600.0
MAX_DESIRABLE_DIVERGE_PC_H = 4400.0


def ramp_roadway_capacity_pc_h(ramp_ffs_mph: float, ramp_lanes: int = 1) -> float:
    if ramp_lanes != 1:
        raise HCMCalcError("Only one-lane ramp capacity is qualified.")
    if ramp_ffs_mph > 50:
        return 2200.0
    if ramp_ffs_mph > 40:
        return 2100.0
    if ramp_ffs_mph > 30:
        return 2000.0
    if ramp_ffs_mph >= 20:
        return 1900.0
    return 1800.0
