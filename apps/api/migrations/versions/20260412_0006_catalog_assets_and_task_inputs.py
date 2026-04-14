"""catalog assets and task input assets"""

from alembic import op
import sqlalchemy as sa

revision = "20260412_0006"
down_revision = "20260412_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "catalog_assets",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("catalog_id", sa.Integer(), sa.ForeignKey("catalogs.id"), nullable=False),
        sa.Column("uploaded_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("file_path", sa.String(length=255), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("file_type", sa.String(length=128), nullable=False),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_catalog_assets_catalog_id", "catalog_assets", ["catalog_id"])
    op.create_index("ix_catalog_assets_uploaded_by", "catalog_assets", ["uploaded_by"])

    op.create_table(
        "task_input_assets",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("task_id", sa.Integer(), sa.ForeignKey("processing_tasks.id"), nullable=False),
        sa.Column(
            "catalog_asset_id",
            sa.Integer(),
            sa.ForeignKey("catalog_assets.id"),
            nullable=False,
        ),
        sa.UniqueConstraint("task_id", "catalog_asset_id"),
    )
    op.create_index("ix_task_input_assets_task_id", "task_input_assets", ["task_id"])
    op.create_index(
        "ix_task_input_assets_catalog_asset_id",
        "task_input_assets",
        ["catalog_asset_id"],
    )
    op.execute(
        """
        INSERT INTO catalog_assets
            (catalog_id, uploaded_by, file_name, file_path, file_size, file_type, uploaded_at)
        SELECT
            demands.catalog_id,
            uploaded_assets.uploaded_by,
            uploaded_assets.file_name,
            uploaded_assets.file_path,
            uploaded_assets.file_size,
            uploaded_assets.file_type,
            uploaded_assets.uploaded_at
        FROM uploaded_assets
        JOIN demands ON demands.id = uploaded_assets.demand_id
        """
    )
    op.execute(
        """
        INSERT INTO task_input_assets (task_id, catalog_asset_id)
        SELECT
            processing_tasks.id,
            catalog_assets.id
        FROM processing_tasks
        JOIN uploaded_assets ON uploaded_assets.id = processing_tasks.input_asset_id
        JOIN demands ON demands.id = uploaded_assets.demand_id
        JOIN catalog_assets
            ON catalog_assets.catalog_id = demands.catalog_id
           AND catalog_assets.file_path = uploaded_assets.file_path
        """
    )
    with op.batch_alter_table("processing_tasks") as batch_op:
        batch_op.alter_column(
            "input_asset_id",
            existing_type=sa.Integer(),
            nullable=True,
        )


def downgrade() -> None:
    op.drop_index("ix_task_input_assets_catalog_asset_id", table_name="task_input_assets")
    op.drop_index("ix_task_input_assets_task_id", table_name="task_input_assets")
    op.drop_table("task_input_assets")
    op.drop_index("ix_catalog_assets_uploaded_by", table_name="catalog_assets")
    op.drop_index("ix_catalog_assets_catalog_id", table_name="catalog_assets")
    op.drop_table("catalog_assets")
