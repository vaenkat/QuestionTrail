from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from pydantic import BaseModel
from questiontrail.settings import Settings, get_settings, print_provider_status
from questiontrail.api.routes import router as api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: logs provider configuration status safely."""
    print_provider_status()
    yield


app = FastAPI(
    title="QuestionTrail API",
    description="Evidence-first research workspace backend",
    version="0.1.0",
    lifespan=lifespan,
)

# Mount API routes
app.include_router(api_router)


class HealthResponse(BaseModel):
    status: str
    service: str
    llm_provider: str
    fallback_order: list[str]
    has_nvidia_key: bool
    has_gemini_key: bool


@app.get("/api/health", response_model=HealthResponse)
def get_health(settings: Settings = Depends(get_settings)) -> HealthResponse:
    """Return non-sensitive service health and provider configuration."""
    return HealthResponse(
        status="ok",
        service=settings.service_name,
        llm_provider=settings.llm_provider,
        fallback_order=settings.llm_fallback_order,
        has_nvidia_key=settings.has_nvidia_configured,
        has_gemini_key=settings.has_gemini_configured,
    )

