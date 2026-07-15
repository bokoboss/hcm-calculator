"""Public facades and explicit version dispatch for ramp influence methods."""

from typing import Any

from hcmcalc.core import CalculationResult, HCMCalcError, UnsupportedScopeError


def get_merge_method(version: str):
    if version == "hcm_7_0":
        from .merge.v7_0.method import HCM70MergeSegmentMethod

        return HCM70MergeSegmentMethod()
    if version == "hcm_7_1":
        raise UnsupportedScopeError(
            "HCM 7.1 is known but unqualified for Merge Segment; no numerical fallback is allowed.",
            scope_status="known_unqualified_version",
        )
    raise UnsupportedScopeError(f"Unknown merge segment method version: {version}.", scope_status="unknown_method_version")


def get_diverge_method(version: str):
    if version == "hcm_7_0":
        from .diverge.v7_0.method import HCM70DivergeSegmentMethod

        return HCM70DivergeSegmentMethod()
    if version == "hcm_7_1":
        raise UnsupportedScopeError(
            "HCM 7.1 is known but unqualified for Diverge Segment; no numerical fallback is allowed.",
            scope_status="known_unqualified_version",
        )
    raise UnsupportedScopeError(f"Unknown diverge segment method version: {version}.", scope_status="unknown_method_version")


class MergeSegmentMethod:
    def __init__(self, version: str = "hcm_7_0") -> None:
        if not isinstance(version, str):
            raise HCMCalcError("Merge method version must be a string.")
        self.version = version
        self._method = get_merge_method(version)

    def calculate(self, inputs: dict[str, Any]) -> CalculationResult:
        if not isinstance(inputs, dict):
            raise HCMCalcError("Merge Segment inputs must be a mapping.")
        if inputs.get("method_version") != self.version:
            raise HCMCalcError("Input method_version must exactly match the selected merge method.")
        return self._method.calculate(inputs)


class DivergeSegmentMethod:
    def __init__(self, version: str = "hcm_7_0") -> None:
        if not isinstance(version, str):
            raise HCMCalcError("Diverge method version must be a string.")
        self.version = version
        self._method = get_diverge_method(version)

    def calculate(self, inputs: dict[str, Any]) -> CalculationResult:
        if not isinstance(inputs, dict):
            raise HCMCalcError("Diverge Segment inputs must be a mapping.")
        if inputs.get("method_version") != self.version:
            raise HCMCalcError("Input method_version must exactly match the selected diverge method.")
        return self._method.calculate(inputs)
