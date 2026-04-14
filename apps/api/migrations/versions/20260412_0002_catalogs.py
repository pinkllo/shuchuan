"""catalogs"""

from alembic import op
import sqlalchemy as sa

revision = "20260412_0002"
down_revision = "20260412_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "catalogs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("provider_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("data_type", sa.String(length=32), nullable=False),
        sa.Column("granularity", sa.String(length=128), nullable=False),
        sa.Column("version", sa.String(length=64), nullable=False),
        sa.Column("fields_description", sa.Text(), nullable=False),
        sa.Column("scale_description", sa.String(length=128), nullable=False),
        sa.Column("sensitivity_level", sa.String(length=32), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("draft", "published", "archived", name="catalogstatus"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["provider_id"], ["users.id"]),
    )
    op.create_index("ix_catalogs_provider_id", "catalogs", ["provider_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_catalogs_provider_id", table_name="catalogs")
    op.drop_table("catalogs")
