"""Translation memory for the translator

translation_memory: sentences and their translations proposed on
/translator, used once approved. Downgrade drops the table; the bundled
sentences come from the data files and are not affected.

Revision ID: d5a8c3e1f907
Revises: c7e2d4a9f1b6
Create Date: 2026-10-19 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd5a8c3e1f907'
down_revision = 'c7e2d4a9f1b6'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'translation_memory',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('source_lang', sa.String(length=10), nullable=False),
        sa.Column('target_lang', sa.String(length=10), nullable=False),
        sa.Column('source_key', sa.String(length=40), nullable=False),
        sa.Column('source_text', sa.Text(), nullable=False),
        sa.Column('target_text', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=10), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('decided_by', sa.Integer(), nullable=True),
        sa.Column('decided_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['decided_by'], ['user.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    with op.batch_alter_table('translation_memory', schema=None) as batch_op:
        batch_op.create_index('ix_translation_memory_source_key', ['source_key'], unique=False)
        batch_op.create_index('ix_translation_memory_status', ['status'], unique=False)


def downgrade():
    with op.batch_alter_table('translation_memory', schema=None) as batch_op:
        batch_op.drop_index('ix_translation_memory_status')
        batch_op.drop_index('ix_translation_memory_source_key')
    op.drop_table('translation_memory')
