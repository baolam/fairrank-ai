"""FairRank-AI: Enterprise Audit & Fairness-Aware Resume Ranking REST API Service."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.routers import ingestion, ranking, audit, report, jobs, auth
from src.storage.db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="FairRank-AI REST API",
    description="Enterprise Algorithmic Accountability, Auditing, and Fairness-Aware Resume Ranking Service.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(ingestion.router)
app.include_router(ranking.router)
app.include_router(audit.router)
app.include_router(report.router)
app.include_router(jobs.router)
app.include_router(auth.router)


@app.get("/", tags=["System"])
def root_status():
    """Root endpoint verifying API service readiness."""
    return {
        "service": "FairRank-AI Core Engine",
        "status": "online",
        "documentation": "/docs",
        "version": "1.0.0",
    }


@app.get("/health", tags=["System"])
def health_check():
    """Healthcheck endpoint for container orchestration and uptime monitoring."""
    return {"status": "healthy"}
