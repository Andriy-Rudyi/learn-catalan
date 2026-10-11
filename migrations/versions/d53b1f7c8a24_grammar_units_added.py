"""GrammarUnit model added

Revision ID: d53b1f7c8a24
Revises: a1c4f7b92e10
Create Date: 2026-10-11 14:40:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd53b1f7c8a24'
down_revision = 'a1c4f7b92e10'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'grammar_unit',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('number', sa.Integer(), nullable=False),
        sa.Column('slug', sa.String(length=120), nullable=False),
        sa.Column('title', sa.String(length=150), nullable=False),
        sa.Column('section', sa.String(length=80), nullable=False),
        sa.Column('level', sa.String(length=5), nullable=True),
        sa.Column('summary', sa.String(length=300), nullable=True),
        sa.Column('explanation', sa.Text(), nullable=False),
        sa.Column('examples', sa.Text(), nullable=True),
        sa.Column('exercises', sa.Text(), nullable=True),
        sa.Column('date_added', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('number'),
        sa.UniqueConstraint('slug'),
    )
    with op.batch_alter_table('grammar_unit', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_grammar_unit_number'), ['number'], unique=False)
        batch_op.create_index(batch_op.f('ix_grammar_unit_section'), ['section'], unique=False)
        batch_op.create_index(batch_op.f('ix_grammar_unit_level'), ['level'], unique=False)


def downgrade():
    with op.batch_alter_table('grammar_unit', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_grammar_unit_level'))
        batch_op.drop_index(batch_op.f('ix_grammar_unit_section'))
        batch_op.drop_index(batch_op.f('ix_grammar_unit_number'))
    op.drop_table('grammar_unit')
