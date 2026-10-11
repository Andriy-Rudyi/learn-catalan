from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from wtforms import SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, Optional

from flaskblog.i18n import lazy_gettext as _l
from flaskblog.vocabulary.constants import (
    GENDERS,
    LEVELS,
    PARTS_OF_SPEECH,
    TOPICS,
)


def _choices(pairs, empty_label):
    return [('', _l(empty_label))] + [(value, _l(label)) for value, label in pairs]


class WordForm(FlaskForm):
    """Add or edit a shared dictionary entry."""

    term = StringField(_l('Каталонською'), validators=[DataRequired(), Length(max=100)])
    translation = StringField(
        _l('Українською'), validators=[DataRequired(), Length(max=255)]
    )
    part_of_speech = SelectField(
        _l('Частина мови'),
        choices=_choices(PARTS_OF_SPEECH, '— не вказано —'),
        validators=[Optional()],
    )
    gender = SelectField(
        _l('Рід'), choices=_choices(GENDERS, '— не вказано —'), validators=[Optional()]
    )
    pronunciation = StringField(_l('Вимова'), validators=[Optional(), Length(max=100)])
    topic = SelectField(
        _l('Тема'), choices=_choices(TOPICS, '— не вказано —'), validators=[Optional()]
    )
    level = SelectField(
        _l('Рівень'), choices=_choices(LEVELS, '— не вказано —'), validators=[Optional()]
    )
    example_ca = StringField(
        _l('Приклад каталонською'), validators=[Optional(), Length(max=255)]
    )
    example_uk = StringField(
        _l('Переклад прикладу'), validators=[Optional(), Length(max=255)]
    )
    notes = TextAreaField(_l('Примітки'), validators=[Optional()])
    translation_en = StringField(
        _l('Англійською'), validators=[Optional(), Length(max=255)]
    )
    example_en = StringField(
        _l('Переклад прикладу англійською'), validators=[Optional(), Length(max=255)]
    )
    notes_en = TextAreaField(_l('Примітки англійською'), validators=[Optional()])
    submit = SubmitField(_l('Зберегти'))


class WordSearchForm(FlaskForm):
    """Filters above the dictionary list; submitted with GET."""

    class Meta:
        csrf = False

    q = StringField(_l('Пошук'), validators=[Optional(), Length(max=100)])
    topic = SelectField(
        _l('Тема'), choices=_choices(TOPICS, 'Усі теми'), validators=[Optional()]
    )
    level = SelectField(
        _l('Рівень'), choices=_choices(LEVELS, 'Усі рівні'), validators=[Optional()]
    )
    part_of_speech = SelectField(
        _l('Частина мови'),
        choices=_choices(PARTS_OF_SPEECH, 'Усі частини мови'),
        validators=[Optional()],
    )
    submit = SubmitField(_l('Знайти'))


class UserWordForm(FlaskForm):
    """Add a word to your own dictionary."""

    term = StringField(_l('Каталонською'), validators=[DataRequired(), Length(max=100)])
    translation = StringField(
        _l('Переклад'), validators=[DataRequired(), Length(max=255)]
    )
    note = StringField(_l('Нотатка'), validators=[Optional(), Length(max=255)])
    submit = SubmitField(_l('Додати'))


class UserWordNoteForm(FlaskForm):
    """Edit the note on one of your own entries."""

    note = StringField(_l('Нотатка'), validators=[Optional(), Length(max=255)])
    submit = SubmitField(_l('Зберегти'))


class WordImportForm(FlaskForm):
    """Upload a CSV of dictionary entries."""

    file = FileField(
        _l('Файл CSV'),
        validators=[DataRequired(), FileAllowed(['csv'], _l('Потрібен файл .csv'))],
    )
    submit = SubmitField(_l('Завантажити'))


class ActionForm(FlaskForm):
    """An empty form, so state-changing buttons carry a CSRF token."""

    submit = SubmitField(_l('Готово'))
