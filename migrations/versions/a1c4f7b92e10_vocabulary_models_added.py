"""Word and UserWord models added

Revision ID: a1c4f7b92e10
Revises: bf06b5ec0e16
Create Date: 2026-10-11 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1c4f7b92e10'
down_revision = 'bf06b5ec0e16'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'word',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('term', sa.String(length=100), nullable=False),
        sa.Column('slug', sa.String(length=120), nullable=False),
        sa.Column('translation', sa.String(length=255), nullable=False),
        sa.Column('part_of_speech', sa.String(length=20), nullable=True),
        sa.Column('gender', sa.String(length=10), nullable=True),
        sa.Column('pronunciation', sa.String(length=100), nullable=True),
        sa.Column('topic', sa.String(length=50), nullable=True),
        sa.Column('level', sa.String(length=5), nullable=True),
        sa.Column('example_ca', sa.String(length=255), nullable=True),
        sa.Column('example_uk', sa.String(length=255), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('date_added', sa.DateTime(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug'),
    )
    with op.batch_alter_table('word', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_word_term'), ['term'], unique=False)
        batch_op.create_index(
            batch_op.f('ix_word_part_of_speech'), ['part_of_speech'], unique=False
        )
        batch_op.create_index(batch_op.f('ix_word_topic'), ['topic'], unique=False)
        batch_op.create_index(batch_op.f('ix_word_level'), ['level'], unique=False)

    op.create_table(
        'user_word',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('word_id', sa.Integer(), nullable=True),
        sa.Column('term', sa.String(length=100), nullable=True),
        sa.Column('translation', sa.String(length=255), nullable=True),
        sa.Column('note', sa.String(length=255), nullable=True),
        sa.Column('status', sa.String(length=10), nullable=False),
        sa.Column('date_added', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.ForeignKeyConstraint(['word_id'], ['word.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'word_id', name='uq_user_word'),
    )
    with op.batch_alter_table('user_word', schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f('ix_user_word_user_id'), ['user_id'], unique=False
        )
        batch_op.create_index(
            batch_op.f('ix_user_word_word_id'), ['word_id'], unique=False
        )


def downgrade():
    with op.batch_alter_table('user_word', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_user_word_word_id'))
        batch_op.drop_index(batch_op.f('ix_user_word_user_id'))
    op.drop_table('user_word')

    with op.batch_alter_table('word', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_word_level'))
        batch_op.drop_index(batch_op.f('ix_word_topic'))
        batch_op.drop_index(batch_op.f('ix_word_part_of_speech'))
        batch_op.drop_index(batch_op.f('ix_word_term'))
    op.drop_table('word')
