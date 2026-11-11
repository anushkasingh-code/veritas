"""
FastAPI Application Entrypoint.
Configured with CORS middleware, global exception handlers, and routing.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import settings
from app.services.llm_factory import llm_factory

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI Lifespan Context Manager.
    Logs selected provider and model settings on application startup.
    """
    provider = settings.effective_provider
    if provider == "groq":
        model = settings.effective_groq_model
        factory_name = "ChatGroq"
    elif provider == "openai":
        model = settings.effective_openai_model
        factory_name = "ChatOpenAI"
    elif provider == "gemini":
        model = settings.effective_gemini_model
        factory_name = "ChatGoogleGenerativeAI"
    else:
        model = settings.CLAUDE_MODEL_NAME
        factory_name = "ChatAnthropic"

    print("=====================================")
    print(f"Provider: {provider}")
    print(f"Model: {model}")
    print(f"Factory: {factory_name}")
    print("=====================================")

    logger.info(f"Startup - Provider: {provider}, Model: {model}, Factory: {factory_name}")

    if provider == "gemini":
        active_model = llm_factory.get_active_gemini_model()
        logger.info(f"Validated active Gemini model on startup: '{active_model}'")

    yield
    logger.info("Shutting down application lifespan...")


app = FastAPI(
    title="Autonomous Multi-Agent Research & Fact Verification System",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS Middleware configuration for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handles request payload validation errors gracefully with structured JSON.
    """
    logger.warning(f"Validation error for request {request.url}: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "status": "error",
            "message": "Invalid request payload",
            "details": jsonable_encoder(exc.errors()),
        },
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception fallback handler to prevent unhandled 500 server crashes.
    """
    logger.error(f"Unhandled server error processing {request.url}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "status": "error",
            "message": "An unexpected server error occurred during processing.",
            "detail": str(exc),
        },
    )


app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    """
    Root API health check and documentation reference endpoint.
    """
    return {
        "message": "Autonomous Multi-Agent Research & Fact Verification API",
        "docs": "/docs",
    }
