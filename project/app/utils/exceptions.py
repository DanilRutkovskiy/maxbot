class AppError(Exception):
    """Base application error."""

    def __init__(self, message: str, code: str = "app_error") -> None:
        self.message = message
        self.code = code
        super().__init__(message)


class InvalidImageError(AppError):
    def __init__(self, message: str = "Invalid or unsupported image") -> None:
        super().__init__(message, code="invalid_image")


class NoFaceDetectedError(AppError):
    def __init__(self, message: str = "No face detected in the image") -> None:
        super().__init__(message, code="no_face_detected")


class FileTooLargeError(AppError):
    def __init__(self, message: str = "File exceeds maximum allowed size") -> None:
        super().__init__(message, code="file_too_large")


class ProviderTimeoutError(AppError):
    def __init__(self, message: str = "Animation provider timed out") -> None:
        super().__init__(message, code="provider_timeout")


class GenerationFailedError(AppError):
    def __init__(self, message: str = "Animation generation failed") -> None:
        super().__init__(message, code="generation_failed")


class MaxApiError(AppError):
    def __init__(self, message: str = "MAX API request failed") -> None:
        super().__init__(message, code="max_api_error")


class UnsupportedFormatError(AppError):
    def __init__(self, message: str = "Unsupported file format") -> None:
        super().__init__(message, code="unsupported_format")
