class FeatureNotImplementedError(RuntimeError):
    """Raised when an API endpoint is scaffolded but business logic is pending."""


class ServiceError(RuntimeError):
    status_code = 400
    code = "service_error"

    def __init__(self, message: str) -> None:
        super().__init__(message)


class NotFoundError(ServiceError):
    status_code = 404
    code = "not_found"


class ConflictError(ServiceError):
    status_code = 409
    code = "conflict"
