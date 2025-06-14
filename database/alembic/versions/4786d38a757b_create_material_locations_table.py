"""create_material_locations_table

Revision ID: 4786d38a757b
Revises:
Create Date: 2025-06-14 02:14:07.887839

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4786d38a757b'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'material_locations',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('material_id', sa.String(length=255), nullable=True),
        sa.Column('timestamp', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('tray_number', sa.String(length=255), nullable=False),
        sa.Column('process_id', sa.String(length=255), nullable=True),
        sa.Column('task_id', sa.String(length=255), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='empty'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_material_locations_id'), 'material_locations', ['id'], unique=False)
    op.create_index(op.f('ix_material_locations_material_id'), 'material_locations', ['material_id'], unique=False)
    op.create_index(op.f('ix_material_locations_tray_number'), 'material_locations', ['tray_number'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_material_locations_tray_number'), table_name='material_locations')
    op.drop_index(op.f('ix_material_locations_material_id'), table_name='material_locations')
    op.drop_index(op.f('ix_material_locations_id'), table_name='material_locations')
    op.drop_table('material_locations')
