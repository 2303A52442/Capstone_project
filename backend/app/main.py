from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import auth, comparison, dashboard, evidence, profile, recommendations, skills, roles, performance, career_twin
from app.core.config import settings
from app.db.base import Base
from app.db.catalog import ensure_catalog
from app.db.session import SessionLocal, engine
from app.models import evidence as candidate_evidence, projects

app = FastAPI(
    title="AI Career Twin API",
    description="Career intelligence and continuous feedback system for personalized career growth.",
    version="1.0.0",
)

allowed_origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
    "https://ai-career-twin-frontend.onrender.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
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

# Create missing tables on deployment without altering or deleting existing data.
Base.metadata.create_all(bind=engine)
with SessionLocal() as db:
    ensure_catalog(db)

@app.get("/health")
def health_check():
    return {"status": "healthy", "app": "ai-career-twin"}
