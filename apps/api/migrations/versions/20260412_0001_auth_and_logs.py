"""auth and logs"""

from alembic import op
import sqlalchemy as sa

revision = "20260412_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    _create_users_table()
    _create_registration_applications_table()
    _create_operation_logs_table()


def downgrade() -> None:
    op.drop_table("operation_logs")
    op.drop_table("registration_applications")
    op.drop_table("users")


def _create_users_table() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("username", sa.String(length=64), nullable=False, unique=True),
        sa.Column("display_name", sa.String(length=128), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False, unique=True),
        sa.Column(
            "role",
            sa.Enum("admin", "provider", "aggregator", "consumer", name="userrole"),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum("active", "disabled", name="userstatus"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_users_username", "users", ["username"], unique=True)
    op.create_index("ix_users_email", "users", ["email"], unique=True)


def _create_registration_applications_table() -> None:
    op.create_table(
        "registration_applications",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("username", sa.String(length=64), nullable=False, unique=True),
        sa.Column("display_name", sa.String(length=128), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False, unique=True),
        sa.Column(
            "requested_role",
            sa.Enum("admin", "provider", "aggregator", "consumer", name="userrole"),
            nullable=False,
        ),
        sa.Column("application_note", sa.Text(), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "pending_review",
                "approved",
                "rejected",
                name="registrationstatus",
            ),
            nullable=False,
        ),
        sa.Column("review_note", sa.Text(), nullable=True),
        sa.Column("reviewed_by", sa.Integer(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["reviewed_by"], ["users.id"]),
    )
    op.create_index(
        "ix_registration_applications_username",
        "registration_applications",
        ["username"],
        unique=True,
    )
    op.create_index(
        "ix_registration_applications_email",
        "registration_applications",
        ["email"],
        unique=True,
    )


def _create_operation_logs_table() -> None:
    op.create_table(
        "operation_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("actor_id", sa.Integer(), nullable=True),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("target_type", sa.String(length=64), nullable=False),
        sa.Column("target_id", sa.Integer(), nullable=False),
        sa.Column("detail", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"]),
    )
    op.create_index("ix_operation_logs_action", "operation_logs", ["action"], unique=False)
