from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from wtforms import SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, Optional

from flaskblog.vocabulary.constants import (
    GENDERS,
    LEVELS,
    PARTS_OF_SPEECH,
    TOPICS,
)


def _choices(pairs, empty_label):
    return [('', empty_label)] + [(value, label) for value, label in pairs]


class WordForm(FlaskForm):
    """Add or edit a shared dictionary entry."""

    term = StringField('Каталонською', validators=[DataRequired(), Length(max=100)])
    translation = StringField(
        'Українською', validators=[DataRequired(), Length(max=255)]
    )
    part_of_speech = SelectField(
        'Частина мови',
        choices=_choices(PARTS_OF_SPEECH, '— не вказано —'),
        validators=[Optional()],
    )
    gender = SelectField(
        'Рід', choices=_choices(GENDERS, '— не вказано —'), validators=[Optional()]
    )
    pronunciation = StringField('Вимова', validators=[Optional(), Length(max=100)])
    topic = SelectField(
        'Тема', choices=_choices(TOPICS, '— не вказано —'), validators=[Optional()]
    )
    level = SelectField(
        'Рівень', choices=_choices(LEVELS, '— не вказано —'), validators=[Optional()]
    )
    example_ca = StringField(
        'Приклад каталонською', validators=[Optional(), Length(max=255)]
    )
    example_uk = StringField(
        'Переклад прикладу', validators=[Optional(), Length(max=255)]
    )
    notes = TextAreaField('Примітки', validators=[Optional()])
    submit = SubmitField('Зберегти')


class WordSearchForm(FlaskForm):
    """Filters above the dictionary list; submitted with GET."""

    class Meta:
        csrf = False

    q = StringField('Пошук', validators=[Optional(), Length(max=100)])
    topic = SelectField(
        'Тема', choices=_choices(TOPICS, 'Усі теми'), validators=[Optional()]
    )
    level = SelectField(
        'Рівень', choices=_choices(LEVELS, 'Усі рівні'), validators=[Optional()]
    )
    part_of_speech = SelectField(
        'Частина мови',
        choices=_choices(PARTS_OF_SPEECH, 'Усі частини мови'),
        validators=[Optional()],
    )
    submit = SubmitField('Знайти')


class UserWordForm(FlaskForm):
    """Add a word to your own dictionary."""

    term = StringField('Каталонською', validators=[DataRequired(), Length(max=100)])
    translation = StringField(
        'Українською', validators=[DataRequired(), Length(max=255)]
    )
    note = StringField('Нотатка', validators=[Optional(), Length(max=255)])
    submit = SubmitField('Додати')


class UserWordNoteForm(FlaskForm):
    """Edit the note on one of your own entries."""

    note = StringField('Нотатка', validators=[Optional(), Length(max=255)])
    submit = SubmitField('Зберегти')


class WordImportForm(FlaskForm):
    """Upload a CSV of dictionary entries."""

    file = FileField(
        'Файл CSV',
        validators=[DataRequired(), FileAllowed(['csv'], 'Потрібен файл .csv')],
    )
    submit = SubmitField('Завантажити')


class ActionForm(FlaskForm):
    """An empty form, so state-changing buttons carry a CSRF token."""

    submit = SubmitField('Готово')
