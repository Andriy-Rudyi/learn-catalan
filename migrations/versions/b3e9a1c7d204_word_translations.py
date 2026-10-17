"""Dictionary translations in their own table, one row per language

Moves word.translation / example_uk / notes (Ukrainian) and
translation_en / example_en / notes_en (English) into word_translation,
so new languages need no new columns. Downgrade puts them back.

Revision ID: b3e9a1c7d204
Revises: f4b8d2a61c37
Create Date: 2026-10-17 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b3e9a1c7d204'
down_revision = 'f4b8d2a61c37'
branch_labels = None
depends_on = None

# language: (translation column, example column, notes column) on word
OLD_COLUMNS = {
    'uk': ('translation', 'example_uk', 'notes'),
    'en': ('translation_en', 'example_en', 'notes_en'),
}


def upgrade():
    op.create_table(
        'word_translation',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('word_id', sa.Integer(), nullable=False),
        sa.Column('lang', sa.String(length=10), nullable=False),
        sa.Column('translation', sa.String(length=255), nullable=False),
        sa.Column('example', sa.String(length=255), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['word_id'], ['word.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('word_id', 'lang', name='uq_word_translation_lang'),
    )
    with op.batch_alter_table('word_translation', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_word_translation_word_id'), ['word_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_word_translation_lang'), ['lang'], unique=False)

    for lang, (translation, example, notes) in OLD_COLUMNS.items():
        op.execute(
            "INSERT INTO word_translation (word_id, lang, translation, example, notes) "
            "SELECT id, '{lang}', COALESCE({t}, ''), {e}, {n} FROM word "
            "WHERE COALESCE({t}, '') <> '' OR {e} IS NOT NULL OR {n} IS NOT NULL".format(
                lang=lang, t=translation, e=example, n=notes,
            )
        )

    with op.batch_alter_table('word', schema=None) as batch_op:
        for columns in OLD_COLUMNS.values():
            for column in columns:
                batch_op.drop_column(column)


def downgrade():
    with op.batch_alter_table('word', schema=None) as batch_op:
        batch_op.add_column(sa.Column('translation', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('example_uk', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('notes', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('translation_en', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('example_en', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('notes_en', sa.Text(), nullable=True))

    for lang, (translation, example, notes) in OLD_COLUMNS.items():
        for column, field in ((translation, 'translation'), (example, 'example'), (notes, 'notes')):
            op.execute(
                "UPDATE word SET {column} = (SELECT wt.{field} FROM word_translation wt "
                "WHERE wt.word_id = word.id AND wt.lang = '{lang}')".format(
                    column=column, field=field, lang=lang,
                )
            )
    # Languages other than Ukrainian and English have nowhere to go.
    op.execute("UPDATE word SET translation = '' WHERE translation IS NULL")
    with op.batch_alter_table('word', schema=None) as batch_op:
        batch_op.alter_column('translation', existing_type=sa.String(length=255), nullable=False)

    op.drop_table('word_translation')
