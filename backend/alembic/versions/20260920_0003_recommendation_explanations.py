"""Add recommendation explanations table."""

import sqlalchemy as sa
from alembic import op

revision = "20260920_0003"
down_revision = "20260920_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "recommendation_explanations" not in inspector.get_table_names():
        op.create_table(
            "recommendation_explanations",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("recommendation_id", sa.Integer(), sa.ForeignKey("recommendations.id"), nullable=False, unique=True),
            sa.Column("explanation", sa.Text(), nullable=False),
            sa.Column("generated_at", sa.DateTime(timezone=True), nullable=True),
        )
        op.create_index("ix_recommendation_explanations_id", "recommendation_explanations", ["id"])
        op.create_index("ix_recommendation_explanations_recommendation_id", "recommendation_explanations", ["recommendation_id"])


def downgrade() -> None:
    op.drop_index("ix_recommendation_explanations_recommendation_id", table_name="recommendation_explanations")
    op.drop_index("ix_recommendation_explanations_id", table_name="recommendation_explanations")
    op.drop_table("recommendation_explanations")
