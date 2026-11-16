"""empty message

Revision ID: 3fbc950155db
Revises: 8b10fe5036e4
Create Date: 2026-11-16 18:59:15.813253

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3fbc950155db'
down_revision: Union[str, Sequence[str], None] = '8b10fe5036e4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add the column as nullable first #
    op.add_column('applications', sa.Column('user_id', sa.Integer(), nullable=True))
    op.create_foreign_key("fk_applications_user_id_users", 'applications', 'users', ['user_id'], ['id'])

    # Backfill existing rows
    op.execute("UPDATE applications SET user_id = 8 WHERE id IN (9, 13, 14, 17, 22, 23, 25, 26, 27, 28)")
    op.execute("UPDATE applications SET user_id = 9 WHERE id BETWEEN 29 AND 38")
    op.execute("UPDATE applications SET user_id = 10 WHERE id BETWEEN 39 AND 48")
    op.execute("UPDATE applications SET user_id = 11 WHERE id BETWEEN 49 AND 58")
    op.execute("UPDATE applications SET user_id = 12 WHERE id IN (59, 60, 61, 62, 63, 64, 65, 66, 68, 70)")
    op.execute("UPDATE applications SET user_id = 13 WHERE id BETWEEN 71 AND 75")

    # Ensure that the data migration is successful
    conn = op.get_bind()
    result = conn.execute(sa.text("SELECT COUNT(*) FROM applications WHERE user_id IS NULL"))
    count = result.scalar()
    if count is None:
        raise RuntimeError
    if count > 0:
        raise RuntimeError(f"Migration validation failed: {count} applications still have NULL user_id.")

    # Change column to non-nullable
    op.alter_column("applications", "user_id", nullable=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint("fk_applications_user_id_users", 'applications', type_='foreignkey')
    op.drop_column('applications', 'user_id')