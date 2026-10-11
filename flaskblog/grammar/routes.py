"""The grammar course: an index of units and one page per unit."""

from flask import Blueprint, abort, render_template, request

from flaskblog.grammar import service
from flaskblog.models import GrammarUnit

grammar = Blueprint('grammar', __name__)


@grammar.route('/grammar')
def index():
    units = GrammarUnit.query.order_by(GrammarUnit.number).all()
    return render_template(
        'grammar_index.html',
        title='Граматика',
        sections=service.sections(),
        total=len(units),
    )


@grammar.route('/grammar/<string:slug>')
def unit(slug):
    unit = GrammarUnit.query.filter_by(slug=slug).first_or_404()
    previous, following = service.neighbours(unit)
    return render_template(
        'grammar_unit.html',
        title='{}. {}'.format(unit.number, unit.title),
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
        title='{}. {}'.format(unit.number, unit.title),
        unit=unit,
        previous=previous,
        following=following,
        show_answers=request.args.get('answers') == '1',
    )
