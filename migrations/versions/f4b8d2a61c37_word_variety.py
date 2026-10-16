"""Word.variety: words that are not used in Central Catalan

Revision ID: f4b8d2a61c37
Revises: e7a3c1d95b02
Create Date: 2026-10-16 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f4b8d2a61c37'
down_revision = 'e7a3c1d95b02'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('word', schema=None) as batch_op:
        batch_op.add_column(sa.Column('variety', sa.String(length=80), nullable=True))
        batch_op.add_column(sa.Column('variety_source', sa.String(length=20), nullable=True))
        batch_op.create_index(batch_op.f('ix_word_variety'), ['variety'], unique=False)


def downgrade():
    with op.batch_alter_table('word', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_word_variety'))
        batch_op.drop_column('variety_source')
        batch_op.drop_column('variety')
