"""add offer and rejected statuses

Revision ID: 9bd302dd34d7
Revises: 3fbc950155db
Create Date: 2026-11-27 15:08:24.183033

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from models.application import Application


# revision identifiers, used by Alembic.
revision: str = '9bd302dd34d7'
down_revision: Union[str, Sequence[str], None] = '3fbc950155db'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_constraint(constraint_name="applications_status_check", table_name="applications", type_="check")

    op.create_check_constraint(
        constraint_name="applications_status_check",
        table_name="applications",
        condition="status in ('applied', 'interview', 'offer', 'rejected')",
    )
    pass


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(constraint_name="applications_status_check", table_name="applications", type_="check")

    op.create_check_constraint(
        constraint_name="applications_status_check",
        table_name="applications",
        condition="status in ('applied', 'interview')",
    )
    pass
