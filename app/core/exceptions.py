class ApplicationError(Exception):
    """Base exception for application-level errors."""


class ResourceNotFoundError(ApplicationError):
    """Raised when a requested resource does not exist."""


class ResourceConflictError(ApplicationError):
    """Raised when a resource conflicts with existing data."""


class BusinessRuleError(ApplicationError):
    """Raised when a business rule is violated."""


class UnauthorizedError(ApplicationError):
    """Raised when authentication is required or invalid."""


class ForbiddenError(ApplicationError):
    """Raised when the authenticated user lacks permission."""