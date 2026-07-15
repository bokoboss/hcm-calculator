"""Version-neutral geometry consistency checks (no automatic geometry derivation)."""

from hcmcalc.core import HCMCalcError, UnsupportedScopeError

from .models import WeavingSegmentInputs


def validate_v70_geometry(inputs: WeavingSegmentInputs) -> None:
    if inputs.number_of_lanes not in {3, 4}:
        raise UnsupportedScopeError("HCM 7.0 qualified lane domain is N = 3 or 4.")
    for name in ("lc_rf", "lc_fr", "lc_rr"):
        value = getattr(inputs, name)
        if value is not None and (isinstance(value, bool) or not isinstance(value, int)):
            raise HCMCalcError(f"{name} must be an integer lane-change count when active.")
    if inputs.configuration == "one_sided":
        if inputs.geometry.entry_side != inputs.geometry.exit_side:
            raise HCMCalcError("One-sided geometry must have entry and exit on the same side.")
        if inputs.number_of_weaving_lanes not in {2, 3}:
            raise UnsupportedScopeError("One-sided HCM 7.0 supports NWL = 2 or 3.")
        if inputs.lc_rf is None or inputs.lc_fr is None or inputs.lc_rr is not None:
            raise HCMCalcError("One-sided geometry requires LC_RF and LC_FR and rejects inactive LC_RR.")
        if inputs.volume_rf_veh_h <= 0 or inputs.volume_fr_veh_h <= 0:
            raise UnsupportedScopeError("The qualified one-sided scope requires positive RF and FR weaving movements.")
        if any(value < 0 or value > 2 for value in (inputs.lc_rf, inputs.lc_fr)):
            raise UnsupportedScopeError("One-sided minimum lane changes must be within the documented 0 through 2 domain.")
    elif inputs.configuration == "two_sided":
        if inputs.geometry.entry_side == inputs.geometry.exit_side:
            raise HCMCalcError("Two-sided geometry must have entry and exit on opposite sides.")
        if inputs.number_of_weaving_lanes != 0:
            raise HCMCalcError("Two-sided HCM 7.0 geometry defines NWL as zero.")
        if inputs.lc_rr is None or inputs.lc_rf is not None or inputs.lc_fr is not None:
            raise HCMCalcError("Two-sided geometry requires LC_RR and rejects inactive LC_RF/LC_FR.")
        if inputs.volume_rr_veh_h <= 0:
            raise UnsupportedScopeError("The qualified two-sided scope requires positive RR weaving movement.")
        if inputs.lc_rr < 2:
            raise UnsupportedScopeError("Two-sided minimum RR lane changes must be at least two.")
    else:
        raise UnsupportedScopeError("configuration must be one_sided or two_sided.")
