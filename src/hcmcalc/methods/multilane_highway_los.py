"""Placeholder for future Multilane Highway LOS method."""

from typing import Any

from hcmcalc.core import CalculationResult, MethodNotImplementedError


class MultilaneHighwayLOSMethod:
    """Scaffold for future multilane highway LOS analysis."""

    facility_type = "multilane_highway"
    method_name = "hcm7_multilane_los"

    def calculate(self, inputs: dict[str, Any]) -> CalculationResult:
        """Raise until future methodology and validation are defined."""

        raise MethodNotImplementedError(
            "Multilane Highway LOS is a future method target and is not implemented."
        )
