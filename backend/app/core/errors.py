from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class AppError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400):
        self.code = code
        self.message = message
        self.status_code = status_code


class OllamaUnavailableError(AppError):
    def __init__(self, message: str | None = None):
        super().__init__(
            "OLLAMA_UNAVAILABLE",
            message
            or "Local AI is unavailable. Please start Ollama and ensure the configured model is installed.",
            503,
        )


class OllamaModelNotFoundError(AppError):
    def __init__(self, model: str):
        super().__init__(
            "OLLAMA_MODEL_MISSING",
            f"Local AI is unavailable. Please start Ollama and ensure the configured model is installed. Run: ollama pull {model}",
            503,
        )


class OllamaTimeoutError(AppError):
    def __init__(self):
        super().__init__(
            "OLLAMA_TIMEOUT",
            "The local model timed out. Try a smaller model (qwen2.5:3b or qwen2.5:1.5b) or a shorter question.",
            504,
        )


class LLMInvalidOutputError(AppError):
    def __init__(self, message: str = "The local model returned invalid JSON. Try again."):
        super().__init__("LLM_INVALID_OUTPUT", message, 502)


def error_body(code: str, message: str) -> dict:
    return {"error": {"code": code, "message": message}}


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_error_handler(_request: Request, exc: AppError):
        return JSONResponse(status_code=exc.status_code, content=error_body(exc.code, exc.message))

    @app.exception_handler(Exception)
    async def unhandled(_request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content=error_body("INTERNAL", "An unexpected server error occurred."),
        )
