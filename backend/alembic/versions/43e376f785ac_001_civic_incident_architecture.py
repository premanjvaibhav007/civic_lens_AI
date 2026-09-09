"""001_civic_incident_architecture

Revision ID: 43e376f785ac
Revises: 
Create Date: 2026-09-09 23:49:52.518726

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '43e376f785ac'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('complaints', schema=None) as batch_op:
        batch_op.add_column(sa.Column('civic_incident_id', sa.String(length=36), nullable=True))
        batch_op.create_index('ix_complaints_civic_incident_id', ['civic_incident_id'], unique=False)
        batch_op.create_foreign_key('fk_complaints_civic_incident', 'civic_incidents', ['civic_incident_id'], ['id'], ondelete='SET NULL')

    with op.batch_alter_table('resolution_evidence', schema=None) as batch_op:
        batch_op.add_column(sa.Column('ai_visual_diff_score', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('ai_resolution_confidence', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('ai_likely_resolved', sa.Boolean(), server_default='1', nullable=False))


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('resolution_evidence', schema=None) as batch_op:
        batch_op.drop_column('ai_likely_resolved')
        batch_op.drop_column('ai_resolution_confidence')
        batch_op.drop_column('ai_visual_diff_score')

    with op.batch_alter_table('complaints', schema=None) as batch_op:
        batch_op.drop_constraint('fk_complaints_civic_incident', type_='foreignkey')
        batch_op.drop_index('ix_complaints_civic_incident_id')
        batch_op.drop_column('civic_incident_id')
