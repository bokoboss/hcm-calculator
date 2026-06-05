"""Project exceptions."""


class HCMCalcError(Exception):
    """Base exception for HCM calculator errors."""


class MethodNotImplementedError(HCMCalcError):
    """Raised when a scaffolded method is called before implementation."""
