"""Global exception hierarchy for OmniAgent."""

from typing import Any


class OmniAgentError(Exception):
    status_code: int = 500
    error_code: str = "INTERNAL_ERROR"

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ValidationError(OmniAgentError):
    status_code = 422
    error_code = "VALIDATION_ERROR"


class PolicyViolationError(OmniAgentError):
    status_code = 403
    error_code = "POLICY_VIOLATION"


class WorkflowExecutionError(OmniAgentError):
    status_code = 500
    error_code = "WORKFLOW_EXECUTION_ERROR"


class TraceStoreError(OmniAgentError):
    status_code = 500
    error_code = "TRACE_STORE_ERROR"


class AdapterError(OmniAgentError):
    status_code = 502
    error_code = "ADAPTER_ERROR"


class ConfigurationError(OmniAgentError):
    status_code = 500
    error_code = "CONFIGURATION_ERROR"


class ResourceNotFoundError(OmniAgentError):
    status_code = 404
    error_code = "NOT_FOUND"


class QuotaExceededError(PolicyViolationError):
    error_code = "QUOTA_EXCEEDED"


class StrategyError(OmniAgentError):
    status_code = 500
    error_code = "STRATEGY_ERROR"


class ReplayError(OmniAgentError):
    status_code = 500
    error_code = "REPLAY_ERROR"


class ConflictError(OmniAgentError):
    status_code = 409
    error_code = "CONFLICT_ERROR"
