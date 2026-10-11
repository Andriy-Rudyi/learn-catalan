"""The grammar course: an index of units and one page per unit."""

from flask import Blueprint, abort, render_template, request

from flaskblog.grammar import service
from flaskblog.i18n import gettext as _
from flaskblog.models import GrammarUnit

grammar = Blueprint('grammar', __name__)

SORT_BY_NUMBER = 'number'
SORT_BY_TOPIC = 'topic'
SORT_ORDERS = (SORT_BY_NUMBER, SORT_BY_TOPIC)


@grammar.route('/grammar')
def index():
    """All units, either in course order or grouped by topic (?sort=topic)."""
    sort = request.args.get('sort', SORT_BY_NUMBER)
    if sort not in SORT_ORDERS:
        sort = SORT_BY_NUMBER

    units = GrammarUnit.query.order_by(GrammarUnit.number).all()
    return render_template(
        'grammar_index.html',
        title=_('Граматика'),
        sort=sort,
        units=units,
        sections=service.sections() if sort == SORT_BY_TOPIC else None,
        total=len(units),
    )


@grammar.route('/grammar/<string:slug>')
def unit(slug):
    unit = GrammarUnit.query.filter_by(slug=slug).first_or_404()
    previous, following = service.neighbours(unit)
    return render_template(
        'grammar_unit.html',
        title='{}. {}'.format(unit.number, unit.l_title),
        unit=unit,
        previous=previous,
        following=following,
        show_answers=request.args.get('answers') == '1',
    )


@grammar.route('/grammar/unit/<int:number>')
def unit_by_number(number):
    """Stable link by unit number, e.g. /grammar/unit/7."""
    unit = GrammarUnit.query.filter_by(number=number).first()
    if unit is None:
        abort(404)
    previous, following = service.neighbours(unit)
    return render_template(
        'grammar_unit.html',
        title='{}. {}'.format(unit.number, unit.l_title),
        unit=unit,
        previous=previous,
        following=following,
        show_answers=request.args.get('answers') == '1',
    )
