"""catalog upload method"""

from alembic import op
import sqlalchemy as sa

revision = "20260412_0005"
down_revision = "20260412_0004"
branch_labels = None
depends_on = None

DEFAULT_UPLOAD_METHOD = "平台上传"


def upgrade() -> None:
    op.add_column(
        "catalogs",
        sa.Column(
            "upload_method",
            sa.String(length=64),
            nullable=False,
            server_default=DEFAULT_UPLOAD_METHOD,
        ),
    )


def downgrade() -> None:
    op.drop_column("catalogs", "upload_method")
