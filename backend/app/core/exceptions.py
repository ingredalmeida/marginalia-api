class DomainError(Exception):
    """Business rule violation."""


class NotFoundError(DomainError):
    """Resource was not found."""


class ConflictError(DomainError):
    """State conflict (e.g. book already on loan)."""


class AuthError(Exception):
    """Authentication failed (invalid credentials or token)."""


class ForbiddenError(Exception):
    """Authenticated but not allowed to perform this action (e.g. non-admin)."""
