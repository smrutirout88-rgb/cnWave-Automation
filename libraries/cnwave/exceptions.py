class CnWaveError(Exception):
    """Base exception for CNWave client"""

    def __init__(self, message=None, details=None):
        super().__init__(message)
        self.message = message
        self.details = details

    def __str__(self):
        if self.details:
            return f"{self.message} | Details: {self.details}"
        return str(self.message)


class AuthenticationError(CnWaveError):
    """Raised when authentication fails"""
    pass


class ApiRequestError(CnWaveError):
    """Raised for invalid API responses"""
    pass


class ApiTimeoutError(CnWaveError):
    """Raised when API call times out"""
    pass


class ApiConnectionError(CnWaveError):
    """Raised when controller connection fails"""
    pass
