"""Add reviewable external candidate evidence."""

import sqlalchemy as sa
from alembic import op

revision = "20260920_0002"
down_revision = "20260918_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "candidate_evidence" not in inspector.get_table_names():
        op.create_table(
            "candidate_evidence",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("candidate_profile_id", sa.Integer(), sa.ForeignKey("candidate_profiles.id"), nullable=False),
            sa.Column("source", sa.String(length=50), nullable=False),
            sa.Column("source_ref", sa.String(length=500), nullable=True),
            sa.Column("title", sa.String(length=255), nullable=False),
            sa.Column("content", sa.Text(), nullable=True),
            sa.Column("extracted_skills", sa.JSON(), nullable=False),
            sa.Column("extracted_projects", sa.JSON(), nullable=False),
            sa.Column("extracted_education", sa.JSON(), nullable=False),
            sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        )
        op.create_index("ix_candidate_evidence_id", "candidate_evidence", ["id"])
        op.create_index("ix_candidate_evidence_candidate_profile_id", "candidate_evidence", ["candidate_profile_id"])


def downgrade() -> None:
    op.drop_index("ix_candidate_evidence_candidate_profile_id", table_name="candidate_evidence")
    op.drop_index("ix_candidate_evidence_id", table_name="candidate_evidence")
    op.drop_table("candidate_evidence")