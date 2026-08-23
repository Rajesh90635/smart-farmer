"""
AppError is how service-layer code raises a deliberate, farmer-facing-safe
error with a stable code and the right HTTP status - as opposed to letting
an unexpected exception fall through to the generic 500 handler. Every
raise site should pick a code from app.core.error_codes.
"""


class AppError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400):
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)
