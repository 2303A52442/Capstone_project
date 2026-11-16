"""Create the initial application schema."""

from alembic import op

from app.db.base import Base
from app.models import career_twin, candidate_profile, performance, projects, recommendation, skill, user  # noqa: F401

revision = "20260918_0001"
down_revision = None
branch_labels = None
depends_on = None


V1_TABLES = [
    "users",
    "candidate_profiles",
    "target_roles",
    "skills",
    "role_skills",
    "candidate_skills",
    "candidate_target_roles",
    "projects",
    "project_skills",
    "performance_records",
    "assessment_results",
    "interview_records",
    "learning_activities",
    "recommendations",
    "recommendation_outcomes",
    "skill_gaps",
    "career_twin_snapshots",
    "candidate_events",
]


def upgrade() -> None:
    bind = op.get_bind()
    tables = [Base.metadata.tables[name] for name in V1_TABLES if name in Base.metadata.tables]
    Base.metadata.create_all(bind=bind, tables=tables)


def downgrade() -> None:
    bind = op.get_bind()
    tables = [Base.metadata.tables[name] for name in V1_TABLES if name in Base.metadata.tables]
    Base.metadata.drop_all(bind=bind, tables=tables)

