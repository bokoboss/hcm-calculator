"""Project exceptions."""


class HCMCalcError(Exception):
    """Base exception for HCM calculator errors."""


class MethodNotImplementedError(HCMCalcError):
    """Raised when a scaffolded method is called before implementation."""


class UnsupportedScopeError(MethodNotImplementedError):
    """Raised when inputs are outside an explicitly supported method scope."""

    def __init__(
        self,
        message: str,
        *,
        scope_status: str = "unsupported",
        unsupported_reason: str | None = None,
        context: dict[str, object] | None = None,
    ) -> None:
        super().__init__(message)
        self.scope_status = scope_status
        self.unsupported_reason = unsupported_reason or message
        self.context = dict(context or {})
