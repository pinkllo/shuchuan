"""add processors table and task processor link"""

from alembic import op
import sqlalchemy as sa

revision = "20260414_0007"
down_revision = "20260412_0006"
branch_labels = None
depends_on = None

PROCESSOR_STATUS = sa.Enum("online", "offline", name="processorstatus")


def upgrade() -> None:
    PROCESSOR_STATUS.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "processors",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("task_type", sa.String(length=64), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("endpoint_url", sa.String(length=512), nullable=False),
        sa.Column("api_token", sa.String(length=128), nullable=False),
        sa.Column("status", PROCESSOR_STATUS, nullable=False, server_default="online"),
        sa.Column("last_heartbeat_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("registered_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("task_type"),
        sa.UniqueConstraint("api_token"),
    )
    op.create_index("ix_processors_task_type", "processors", ["task_type"])
    op.create_index("ix_processors_api_token", "processors", ["api_token"])
    with op.batch_alter_table("processing_tasks") as batch_op:
        batch_op.add_column(sa.Column("processor_id", sa.Integer(), nullable=True))
        batch_op.create_index("ix_processing_tasks_processor_id", ["processor_id"])
        batch_op.create_foreign_key(
            "fk_processing_tasks_processor_id",
            "processors",
            ["processor_id"],
            ["id"],
        )


def downgrade() -> None:
    with op.batch_alter_table("processing_tasks") as batch_op:
        batch_op.drop_constraint("fk_processing_tasks_processor_id", type_="foreignkey")
        batch_op.drop_index("ix_processing_tasks_processor_id")
        batch_op.drop_column("processor_id")
    op.drop_index("ix_processors_api_token", table_name="processors")
    op.drop_index("ix_processors_task_type", table_name="processors")
    op.drop_table("processors")
    PROCESSOR_STATUS.drop(op.get_bind(), checkfirst=True)
