"""/c1: the C1/C2 course: its programme mapped to the site, frases fetes,
and trainers for the opinion article and the monologue (course/content.py)."""

from flask import Blueprint, abort, current_app, render_template, url_for

from flaskblog.course import content, phrases
from flaskblog.i18n import content_language, gettext as _
from flaskblog.models import GrammarUnit

course = Blueprint('course', __name__)


@course.before_request
def switched_on():
    if not current_app.config.get('COURSE_C1', True):
        abort(404)


def _programme():
    """The programme with the units that exist on the site."""
    numbers = {n for _part, topics in content.PROGRAMME for _t, units, _e in topics for n in units}
    found = {unit.number: unit for unit in
             GrammarUnit.query.filter(GrammarUnit.number.in_(numbers)).all()} if numbers else {}
    programme = []
    for part, topics in content.PROGRAMME:
        rows = []
        for topic, units, endpoint in topics:
            rows.append({
                'topic': topic,
                'units': [found[n] for n in units if n in found],
                'page': url_for(endpoint) if endpoint else None,
            })
        programme.append((part, rows))
    return programme


@course.route('/c1')
def index():
    return render_template('course_index.html', title=_('Курс C1/C2'),
                           programme=_programme(), article_words=content.ARTICLE_WORDS,
                           monologue_minutes=content.MONOLOGUE_MINUTES,
                           phrase_count=len(phrases.load()))


@course.route('/c1/frases-fetes')
def phrases_page():
    lang = content_language()
    items = phrases.load()
    return render_template('course_phrases.html', title=_('Сталі вирази (frases fetes)'),
                           phrases=items, themes=phrases.themes(), lang=lang,
                           phrases_meanings=[phrases.meaning(p, lang) for p in items])


@course.route('/c1/article')
def article():
    return render_template('course_article.html', title=_('Стаття-думка'),
                           words=content.ARTICLE_WORDS, topics=content.ARTICLE_TOPICS,
                           connectors=content.ARTICLE_CONNECTORS,
                           structure=content.ARTICLE_STRUCTURE)


@course.route('/c1/monologue')
def monologue():
    return render_template('course_monologue.html', title=_('Монолог'),
                           minutes=content.MONOLOGUE_MINUTES, topics=content.MONOLOGUE_TOPICS,
                           connectors=content.MONOLOGUE_CONNECTORS,
                           checklist=content.MONOLOGUE_CHECKLIST)
