from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

class AppError(Exception):
    def __init__(self, status_code: int, error_code: str, message: str):
        self.status_code = status_code
        self.error_code = error_code
        self.message = message

class UnsupportedFileTypeError(AppError):
    def __init__(self, message="Unsupported file type"):
        super().__init__(415, "UNSUPPORTED_FILE_TYPE", message)

class FileTooLargeError(AppError):
    def __init__(self, message="File too large"):
        super().__init__(413, "FILE_TOO_LARGE", message)

class InvalidArchiveError(AppError):
    def __init__(self, message="Invalid archive"):
        super().__init__(400, "INVALID_ARCHIVE", message)

class MissingCRSError(AppError):
    def __init__(self, message="Missing CRS"):
        super().__init__(422, "MISSING_CRS", message)

class FileProcessingError(AppError):
    def __init__(self, message="File processing error"):
        super().__init__(422, "FILE_PROCESSING_ERROR", message)

class FileNotFoundError_(AppError):
    def __init__(self, message="File not found"):
        super().__init__(404, "FILE_NOT_FOUND", message)

class FileNotReadyError(AppError):
    def __init__(self, message="File not ready"):
        super().__init__(409, "FILE_NOT_READY", message)

def register_exception_handlers(app: FastAPI):
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError):
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": exc.error_code, "message": exc.message}},
        )
