"""Exceptions whose retry semantics are shared across projects."""


class AutomationError(Exception):
    """Base error; unclassified failures require manual inspection."""


class ConfigError(AutomationError):
    pass


class RetryableError(AutomationError):
    """Retry only when replaying the whole operation is safe."""


class PermanentError(AutomationError):
    pass


class NeedsManual(AutomationError):
    pass


class AuthenticationError(NeedsManual):
    pass


class OutcomeUnknown(NeedsManual):
    """The server may have committed the operation; reconcile before replay."""


class SkipTask(AutomationError):
    pass


class LeaseLostError(AutomationError):
    pass


class MissingDependencyError(ImportError):
    pass
