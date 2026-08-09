"""drop priority column from scan_results

Revision ID: 3a1b2c3d4e5f
Revises: e2f29abded28
Create Date: 2026-07-27 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '3a1b2c3d4e5f'
down_revision: Union[str, None] = 'e2f29abded28'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('scan_results') as batch_op:
        batch_op.drop_column('priority')


def downgrade() -> None:
    with op.batch_alter_table('scan_results') as batch_op:
        batch_op.add_column(sa.Column('priority', sa.String(), nullable=False, server_default='low'))
