"""Single explicit dispatch boundary for versioned weaving methods."""

from typing import Any

from hcmcalc.core import CalculationResult, HCMCalcError, UnsupportedScopeError


def get_weaving_method(version: str):
    if version == "hcm_7_0":
        from .v7_0.method import HCM70WeavingSegmentMethod
        return HCM70WeavingSegmentMethod()
    if version == "hcm_7_1":
        raise UnsupportedScopeError(
            "HCM 7.1 is known but unqualified: its independent validation and required Chapter 14 capacity-check coverage are not complete.",
            scope_status="known_unqualified_version",
        )
    raise UnsupportedScopeError(f"Unknown weaving method version: {version}.", scope_status="unknown_method_version")


class WeavingSegmentMethod:
    """Public version-pinned family facade; it has no numerical version branches."""

    def __init__(self, version: str = "hcm_7_0") -> None:
        if not isinstance(version, str):
            raise HCMCalcError("Weaving method version must be a string.")
        self.version = version
        self._method = get_weaving_method(version)

    def calculate(self, inputs: dict[str, Any]) -> CalculationResult:
        if not isinstance(inputs, dict):
            raise HCMCalcError("Weaving Segment inputs must be a mapping.")
        if inputs.get("method_version") != self.version:
            raise HCMCalcError("Input method_version must exactly match the selected weaving method.")
        return self._method.calculate(inputs)
