"""initial_credentials_table

Revision ID: 2b61ff06858c
Revises:
Create Date: 2026-02-07 22:22:01.418370

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2b61ff06858c"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "stargate_credentials",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("org_id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("service", sa.String(), nullable=False),
        sa.Column("credential_type", sa.String(), nullable=False),
        sa.Column("access_pattern", sa.String(), nullable=True),
        sa.Column("access_token_encrypted", sa.Text(), nullable=False),
        sa.Column("refresh_token_encrypted", sa.Text(), nullable=True),
        sa.Column("token_expiry", sa.DateTime(), nullable=True),
        sa.Column("realm_id", sa.String(), nullable=True),
        sa.Column("extra_data", sa.JSON(), nullable=True),
        sa.Column("created_by", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_stargate_credentials_credential_type"), "stargate_credentials", ["credential_type"]
    )
    op.create_index(op.f("ix_stargate_credentials_org_id"), "stargate_credentials", ["org_id"])
    op.create_index(op.f("ix_stargate_credentials_service"), "stargate_credentials", ["service"])
    op.create_index(op.f("ix_stargate_credentials_user_id"), "stargate_credentials", ["user_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_stargate_credentials_user_id"), table_name="stargate_credentials")
    op.drop_index(op.f("ix_stargate_credentials_service"), table_name="stargate_credentials")
    op.drop_index(op.f("ix_stargate_credentials_org_id"), table_name="stargate_credentials")
    op.drop_index(
        op.f("ix_stargate_credentials_credential_type"), table_name="stargate_credentials"
    )
    op.drop_table("stargate_credentials")
