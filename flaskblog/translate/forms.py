from flask_wtf import FlaskForm
from wtforms import HiddenField, StringField, TextAreaField
from wtforms.validators import Optional

from flaskblog.i18n import lazy_gettext as _l


class TranslationForm(FlaskForm):
    """One field on /translate. ``base`` is the text the page showed, so a
    save does not overwrite what someone else changed in the meantime."""

    text = TextAreaField(_l('Переклад'), validators=[Optional()])
    base = HiddenField()
    action = HiddenField()
    kind = HiddenField()
    sense_id = HiddenField()
    key = HiddenField()


class SearchForm(FlaskForm):
    class Meta:
        csrf = False

    q = StringField(_l('Пошук'), validators=[Optional()])
