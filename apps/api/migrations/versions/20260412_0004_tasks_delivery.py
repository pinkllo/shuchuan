"""tasks and delivery"""

from alembic import op
import sqlalchemy as sa

revision = "20260412_0004"
down_revision = "20260412_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "processing_tasks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("demand_id", sa.Integer(), nullable=False),
        sa.Column("input_asset_id", sa.Integer(), nullable=False),
        sa.Column("created_by", sa.Integer(), nullable=False),
        sa.Column("task_type", sa.String(length=32), nullable=False),
        sa.Column(
            "status",
            sa.Enum("queued", "running", "completed", "failed", name="taskstatus"),
            nullable=False,
        ),
        sa.Column("progress", sa.Integer(), nullable=False),
        sa.Column("config_json", sa.JSON(), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["demand_id"], ["demands.id"]),
        sa.ForeignKeyConstraint(["input_asset_id"], ["uploaded_assets.id"]),
    )
    op.create_index("ix_processing_tasks_created_by", "processing_tasks", ["created_by"], unique=False)
    op.create_index("ix_processing_tasks_demand_id", "processing_tasks", ["demand_id"], unique=False)
    op.create_index("ix_processing_tasks_input_asset_id", "processing_tasks", ["input_asset_id"], unique=False)

    op.create_table(
        "task_artifacts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("task_id", sa.Integer(), nullable=False),
        sa.Column("artifact_type", sa.String(length=64), nullable=False),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("file_path", sa.String(length=255), nullable=False),
        sa.Column("sample_count", sa.Integer(), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["task_id"], ["processing_tasks.id"]),
    )
    op.create_index("ix_task_artifacts_task_id", "task_artifacts", ["task_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_task_artifacts_task_id", table_name="task_artifacts")
    op.drop_table("task_artifacts")
    op.drop_index("ix_processing_tasks_input_asset_id", table_name="processing_tasks")
    op.drop_index("ix_processing_tasks_demand_id", table_name="processing_tasks")
    op.drop_index("ix_processing_tasks_created_by", table_name="processing_tasks")
    op.drop_table("processing_tasks")
