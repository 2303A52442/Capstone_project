"""Centralized pytest test fixtures for AI Career Twin test suite."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import create_access_token, hash_password
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.candidate_profile import CandidateProfile
from app.models.user import User

# Ensure all models are registered in Base.metadata
from app.models import (  # noqa: F401
    candidate_profile,
    career_twin,
    evidence,
    performance,
    projects,
    recommendation,
    skill,
    user,
)

TEST_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(autouse=True)
def init_test_db():
    """Create all tables before each test and drop them after."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db():
    """Yield a database session bound to the test engine."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db):
    """Yield a TestClient with get_db overridden to use the test session."""
    def _override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    test_client = TestClient(app)
    yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db):
    """Create and return a default test user with candidate profile."""
    user_record = User(
        email="test_candidate@example.com",
        username="test_candidate",
        full_name="Test Candidate",
        hashed_password=hash_password("password123"),
    )
    db.add(user_record)
    db.flush()
    profile = CandidateProfile(
        user_id=user_record.id,
        name=user_record.full_name,
        career_goal="Backend Developer",
        bio="Test candidate profile",
    )
    db.add(profile)
    db.commit()
    db.refresh(user_record)
    return user_record


@pytest.fixture
def auth_headers(test_user):
    """Generate bearer auth headers for the test user."""
    token = create_access_token(test_user.id)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def second_user(db):
    """Create and return a second test user for multi-user isolation tests."""
    user_record = User(
        email="other_candidate@example.com",
        username="other_candidate",
        full_name="Other Candidate",
        hashed_password=hash_password("password456"),
    )
    db.add(user_record)
    db.flush()
    profile = CandidateProfile(
        user_id=user_record.id,
        name=user_record.full_name,
        career_goal="Data Analyst",
        bio="Other candidate profile",
    )
    db.add(profile)
    db.commit()
    db.refresh(user_record)
    return user_record


@pytest.fixture
def second_auth_headers(second_user):
    """Generate bearer auth headers for the second user."""
    token = create_access_token(second_user.id)
    return {"Authorization": f"Bearer {token}"}
