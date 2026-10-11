"""English content: dictionary columns and grammar unit translations

Revision ID: e7a3c1d95b02
Revises: d53b1f7c8a24
Create Date: 2026-10-11 20:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e7a3c1d95b02'
down_revision = 'd53b1f7c8a24'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('word', schema=None) as batch_op:
        batch_op.add_column(sa.Column('translation_en', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('example_en', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('notes_en', sa.Text(), nullable=True))

    with op.batch_alter_table('grammar_unit', schema=None) as batch_op:
        batch_op.add_column(sa.Column('translations', sa.Text(), nullable=True))


def downgrade():
    with op.batch_alter_table('grammar_unit', schema=None) as batch_op:
        batch_op.drop_column('translations')

    with op.batch_alter_table('word', schema=None) as batch_op:
        batch_op.drop_column('notes_en')
        batch_op.drop_column('example_en')
        batch_op.drop_column('translation_en')
