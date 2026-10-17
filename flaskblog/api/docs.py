"""The page for developers: what the open API offers and how to call it."""

from flask import Blueprint, render_template

from flaskblog.api.routes import absolute
from flaskblog.i18n import gettext as _
from flaskblog.languages import LANGUAGES

api_docs = Blueprint('api_docs', __name__)


@api_docs.route('/developers')
def developers():
    base = absolute('api.index').rstrip('/')
    return render_template(
        'developers.html',
        title=_('API для розробників'),
        base=base,
        languages=LANGUAGES.values(),
    )
