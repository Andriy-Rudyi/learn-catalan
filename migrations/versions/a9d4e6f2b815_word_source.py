"""Word.source: where a dictionary word came from (None = written for the site, 'dacco')

Revision ID: a9d4e6f2b815
Revises: d5a8c3e1f907
Create Date: 2026-11-10 12:00:00.000000

Before going down, take the imported words away with
``flask vocabulary dacco-import --remove``; otherwise they stay as
ordinary words.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a9d4e6f2b815'
down_revision = 'd5a8c3e1f907'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('word', schema=None) as batch_op:
        batch_op.add_column(sa.Column('source', sa.String(length=20), nullable=True))
        batch_op.create_index(batch_op.f('ix_word_source'), ['source'], unique=False)


def downgrade():
    with op.batch_alter_table('word', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_word_source'))
        batch_op.drop_column('source')
