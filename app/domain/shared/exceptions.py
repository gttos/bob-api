class DomainError(Exception):
    """Base class for all domain exceptions."""
    pass


class ResourceNotFoundError(DomainError):
    """Raised when a requested resource is not found."""
    pass


class InvalidStateTransitionError(DomainError):
    """Raised when an invalid state transition is attempted."""
    pass


class DomainValidationError(DomainError):
    """Raised when domain validation fails."""
    pass


class DuplicateResourceError(DomainError):
    """Raised when attempting to create a resource that already exists."""
    pass
