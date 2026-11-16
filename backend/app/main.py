from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import auth, comparison, dashboard, evidence, profile, recommendations, skills, roles, performance, career_twin
from app.core.config import settings
from app.db.base import Base
from app.db.session import engine
from app.models import evidence as candidate_evidence, projects

app = FastAPI(
    title="AI Career Twin API",
    description="Career intelligence and continuous feedback system for personalized career growth.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(profile.router, prefix="/candidate", tags=["candidate"])
app.include_router(skills.router, prefix="/skills", tags=["skills"])
app.include_router(roles.router, prefix="/roles", tags=["roles"])
app.include_router(performance.router, prefix="/performance", tags=["performance"])
app.include_router(recommendations.router, prefix="/recommendations", tags=["recommendations"])
app.include_router(career_twin.router, prefix="/career-twin", tags=["career-twin"])
app.include_router(comparison.router, prefix="/comparison", tags=["comparison"])
app.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
app.include_router(evidence.router, prefix="/evidence", tags=["evidence"])

if settings.database_url.startswith("sqlite"):
    Base.metadata.create_all(bind=engine)

@app.get("/health")
def health_check():
    return {"status": "healthy", "app": "ai-career-twin"}
