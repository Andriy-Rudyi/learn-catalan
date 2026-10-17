"""Meanings of words and the translation platform

word_sense / sense_translation: translations attached to the meanings of a
word, filled in here by splitting every word_translation string on ";"
along the English meanings. word_translation keeps the joined strings, so
downgrade (dropping these tables) loses nothing.

word_translation.edited: changed on the site, so deploys no longer
overwrite it with the bundled files.

translator, ui_translation, translation_suggestion, translation_change:
/translate (who translates which language, interface strings translated on
the site, suggestions, history).

Revision ID: c7e2d4a9f1b6
Revises: b3e9a1c7d204
Create Date: 2026-10-17 18:00:00.000000

"""
import re
from collections import defaultdict

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c7e2d4a9f1b6'
down_revision = 'b3e9a1c7d204'
branch_labels = None
depends_on = None

# A copy of flaskblog/vocabulary/senses.py as it was when this was written,
# so later changes to the app do not change what this migration does.
_SEPARATOR = re.compile(r'\s*;\s*')


def _joiner(lang):
    return ' ; ' if lang == 'fr' else '; '


def _parts(text):
    return [part for part in _SEPARATOR.split((text or '').strip()) if part]


def _align(parts, count, lang):
    if not parts:
        return [''] * count
    if len(parts) == count:
        return list(parts)
    if len(parts) == 1:
        return list(parts) * count
    if len(parts) > count:
        return list(parts[:count - 1]) + [_joiner(lang).join(parts[count - 1:])]
    return list(parts) + [''] * (count - len(parts))


def _count(by_lang):
    for lang in ('en', 'uk'):
        if by_lang.get(lang, ('', True))[0]:
            return max(len(_parts(by_lang[lang][0])), 1)
    for text, _ in by_lang.values():
        if text:
            return max(len(_parts(text)), 1)
    return 1


def _target_columns():
    return [
        sa.Column('lang', sa.String(length=10), nullable=False),
        sa.Column('kind', sa.String(length=10), nullable=False),
        sa.Column('sense_id', sa.Integer(), nullable=True),
        sa.Column('word_id', sa.Integer(), nullable=True),
        sa.Column('ui_key', sa.String(length=40), nullable=True),
        sa.Column('ui_source', sa.Text(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['sense_id'], ['word_sense.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['word_id'], ['word.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='SET NULL'),
    ]


def _target_indexes(table):
    with op.batch_alter_table(table, schema=None) as batch_op:
        for column in ('lang', 'sense_id', 'word_id', 'ui_key'):
            batch_op.create_index(batch_op.f('ix_{}_{}'.format(table, column)), [column], unique=False)


def upgrade():
    with op.batch_alter_table('word_translation', schema=None) as batch_op:
        batch_op.add_column(sa.Column('edited', sa.Boolean(), nullable=False, server_default=sa.false()))

    op.create_table(
        'word_sense',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('word_id', sa.Integer(), nullable=False),
        sa.Column('position', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['word_id'], ['word.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    with op.batch_alter_table('word_sense', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_word_sense_word_id'), ['word_id'], unique=False)

    op.create_table(
        'sense_translation',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('sense_id', sa.Integer(), nullable=False),
        sa.Column('lang', sa.String(length=10), nullable=False),
        sa.Column('text', sa.String(length=255), nullable=False),
        sa.Column('reviewed', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.ForeignKeyConstraint(['sense_id'], ['word_sense.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('sense_id', 'lang', name='uq_sense_translation_lang'),
    )
    with op.batch_alter_table('sense_translation', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_sense_translation_sense_id'), ['sense_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_sense_translation_lang'), ['lang'], unique=False)

    op.create_table(
        'translator',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('lang', sa.String(length=10), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'lang', name='uq_translator_lang'),
    )
    with op.batch_alter_table('translator', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_translator_user_id'), ['user_id'], unique=False)

    op.create_table(
        'ui_translation',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('lang', sa.String(length=10), nullable=False),
        sa.Column('key', sa.String(length=40), nullable=False),
        sa.Column('source', sa.Text(), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('updated_by', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['updated_by'], ['user.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('lang', 'key', name='uq_ui_translation_key'),
    )
    with op.batch_alter_table('ui_translation', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_ui_translation_lang'), ['lang'], unique=False)

    op.create_table(
        'translation_suggestion',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=10), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('decided_by', sa.Integer(), nullable=True),
        sa.Column('decided_at', sa.DateTime(), nullable=True),
        *_target_columns(),
        sa.ForeignKeyConstraint(['decided_by'], ['user.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    _target_indexes('translation_suggestion')
    with op.batch_alter_table('translation_suggestion', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_translation_suggestion_status'), ['status'], unique=False)

    op.create_table(
        'translation_change',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('action', sa.String(length=10), nullable=False),
        sa.Column('old_text', sa.Text(), nullable=True),
        sa.Column('new_text', sa.Text(), nullable=True),
        sa.Column('old_reviewed', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        *_target_columns(),
        sa.PrimaryKeyConstraint('id'),
    )
    _target_indexes('translation_change')
    with op.batch_alter_table('translation_change', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_translation_change_created_at'), ['created_at'], unique=False)

    _fill_senses()


def _fill_senses():
    """One word_sense per English meaning, and each language's part of the
    translation string on it."""
    bind = op.get_bind()
    rows = bind.execute(sa.text(
        'SELECT word_id, lang, translation, reviewed FROM word_translation ORDER BY word_id'
    )).fetchall()
    words = defaultdict(dict)
    for word_id, lang, translation, reviewed in rows:
        words[word_id][lang] = (translation or '', bool(reviewed))

    senses, texts = [], []
    sense_id = 0
    for word_id, by_lang in sorted(words.items()):
        count = _count(by_lang)
        ids = []
        for position in range(1, count + 1):
            sense_id += 1
            ids.append(sense_id)
            senses.append({'id': sense_id, 'word_id': word_id, 'position': position})
        for lang, (translation, reviewed) in sorted(by_lang.items()):
            for sid, text in zip(ids, _align(_parts(translation), count, lang)):
                if text:
                    texts.append({'id': len(texts) + 1, 'sense_id': sid, 'lang': lang,
                                  'text': text[:255], 'reviewed': reviewed})

    sense_table = sa.table('word_sense', sa.column('id', sa.Integer), sa.column('word_id', sa.Integer),
                           sa.column('position', sa.Integer))
    text_table = sa.table('sense_translation', sa.column('id', sa.Integer), sa.column('sense_id', sa.Integer),
                          sa.column('lang', sa.String), sa.column('text', sa.String),
                          sa.column('reviewed', sa.Boolean))
    for start in range(0, len(senses), 1000):
        op.bulk_insert(sense_table, senses[start:start + 1000])
    for start in range(0, len(texts), 1000):
        op.bulk_insert(text_table, texts[start:start + 1000])

    if bind.dialect.name == 'postgresql':
        # The ids were given explicitly: move the sequences past them.
        for table in ('word_sense', 'sense_translation'):
            op.execute(
                "SELECT setval(pg_get_serial_sequence('{t}', 'id'), "
                "COALESCE((SELECT MAX(id) FROM {t}), 0) + 1, false)".format(t=table)
            )


def downgrade():
    op.drop_table('translation_change')
    op.drop_table('translation_suggestion')
    op.drop_table('ui_translation')
    op.drop_table('translator')
    op.drop_table('sense_translation')
    op.drop_table('word_sense')
    with op.batch_alter_table('word_translation', schema=None) as batch_op:
        batch_op.drop_column('edited')
