"""demands and assets"""

from alembic import op
import sqlalchemy as sa

revision = "20260412_0003"
down_revision = "20260412_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "demands",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("catalog_id", sa.Integer(), nullable=False),
        sa.Column("requester_id", sa.Integer(), nullable=False),
        sa.Column("provider_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=128), nullable=False),
        sa.Column("purpose", sa.Text(), nullable=False),
        sa.Column("delivery_plan", sa.String(length=32), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "pending_approval",
                "approved",
                "rejected",
                "data_uploaded",
                "processing",
                "delivered",
                name="demandstatus",
            ),
            nullable=False,
        ),
        sa.Column("approval_note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["catalog_id"], ["catalogs.id"]),
        sa.ForeignKeyConstraint(["provider_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["requester_id"], ["users.id"]),
    )
    op.create_index("ix_demands_catalog_id", "demands", ["catalog_id"], unique=False)
    op.create_index("ix_demands_provider_id", "demands", ["provider_id"], unique=False)
    op.create_index("ix_demands_requester_id", "demands", ["requester_id"], unique=False)

    op.create_table(
        "uploaded_assets",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("demand_id", sa.Integer(), nullable=False),
        sa.Column("uploaded_by", sa.Integer(), nullable=False),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("file_path", sa.String(length=255), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("file_type", sa.String(length=128), nullable=False),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["demand_id"], ["demands.id"]),
        sa.ForeignKeyConstraint(["uploaded_by"], ["users.id"]),
    )
    op.create_index("ix_uploaded_assets_demand_id", "uploaded_assets", ["demand_id"], unique=False)
    op.create_index("ix_uploaded_assets_uploaded_by", "uploaded_assets", ["uploaded_by"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_uploaded_assets_uploaded_by", table_name="uploaded_assets")
    op.drop_index("ix_uploaded_assets_demand_id", table_name="uploaded_assets")
    op.drop_table("uploaded_assets")
    op.drop_index("ix_demands_requester_id", table_name="demands")
    op.drop_index("ix_demands_provider_id", table_name="demands")
    op.drop_index("ix_demands_catalog_id", table_name="demands")
    op.drop_table("demands")
