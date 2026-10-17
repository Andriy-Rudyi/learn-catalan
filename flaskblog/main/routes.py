from flask import (Blueprint, abort, current_app, jsonify, render_template,
                   request)
from flask_login import current_user

from flaskblog import db
from flaskblog.i18n import gettext as _
from flaskblog.conjugation import get_service
from flaskblog.conjugation.labels import (
    error_message,
    ordered_moods,
    person_labels,
    tense_label,
)
from flaskblog.main import faq as faq_content
from flaskblog.phonetics.service import load_lessons
from flaskblog.models import (Announcement, GrammarUnit, Post, Update, UserWord,
                              Word)
from flaskblog.vocabulary import varieties
from flaskblog.vocabulary.constants import part_of_speech_label
from flaskblog.vocabulary.forms import ActionForm

main = Blueprint('main', __name__)

PROJECT_NAME = 'LearnCatalan'

# Verbs offered as examples under the conjugator's search box.
SUGGESTED_VERBS = ('ser', 'tenir', 'fer', 'anar', 'parlar', 'saber', 'viure', 'voler')


@main.route("/")
@main.route("/home")
def home():
    return render_template(
        'home.html',
        ProjectName=PROJECT_NAME,
        unit_count=GrammarUnit.query.count(),
        word_count=Word.query.count(),
        lesson_count=len(load_lessons()),
    )


@main.route("/lessons")
def lessons():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.date_posted).paginate(page=page, per_page=6)
    return render_template('lessons.html', title=_('Уроки'), posts=posts)


@main.route("/faq")
def faq():
    if not current_app.config.get('SHOW_FAQ'):
        abort(404)
    sections = faq_content.sections()
    return render_template(
        'faq.html',
        title=_('Часті запитання'),
        sections=sections,
        support_email=faq_content.SUPPORT_EMAIL,
        structured_data=[faq_content.structured_data(sections)],
    )


@main.route("/announcements")
def announcements():
    announcements = Announcement.query.order_by(Announcement.date_posted.desc())
    return render_template(
        'announcements.html', announcements=announcements, title='Announcements'
    )


@main.route("/updates")
def updates():
    updates = Update.query.order_by(Update.date_posted.desc())
    return render_template('updates.html', updates=updates)


def _dictionary_entry(infinitive):
    """The dictionary entry for a verb, so its translation can be shown."""
    if not infinitive:
        return None
    return Word.query.filter(db.func.lower(Word.term) == infinitive.lower()).first()


def _is_saved(word):
    """Whether the current user already has *word* in their own dictionary."""
    if word is None or not current_user.is_authenticated:
        return False
    return (
        UserWord.query.filter_by(user_id=current_user.id, word_id=word.id).first()
        is not None
    )


@main.route('/conjugator', methods=['GET', 'POST'])
def conjugator():
    """Conjugate a Catalan verb.

    Accepts the verb from the form or from the query string, so a
    conjugation can be linked to (``/conjugator?verb=parlar``).
    """
    query = (request.values.get('verb') or '').strip()
    result = get_service().conjugate(query) if query else None
    message = error_message(result.error) if result and not result.ok else None

    word = _dictionary_entry(result.infinitive) if result and result.ok else None
    verb_variety, verb_central, verb_source = _variety(word, result)

    return render_template(
        'conjugator.html',
        title=_('Дієвідміна'),
        query=query,
        result=result,
        error_message=message,
        word=word,
        word_is_saved=_is_saved(word),
        verb_variety=verb_variety,
        verb_central=verb_central,
        verb_variety_source=verb_source,
        action_form=ActionForm(),
        suggested_verbs=SUGGESTED_VERBS,
        ordered_moods=ordered_moods,
        tense_label=tense_label,
        person_labels=person_labels,
        part_of_speech_label=part_of_speech_label,
    )


def _variety(word, result):
    """(codes, central alternative, source) when the verb is not Central Catalan."""
    if word is not None and word.variety_codes:
        return word.variety_codes, word.central_alternative, word.variety_source
    if result is None or not result.ok:
        return (), None, None
    entry = varieties.load().get(result.infinitive) or {}
    return varieties.parse_codes(entry.get('variety')), entry.get('central'), entry.get('source')


@main.route('/api/verbs')
def api_verbs():
    """Infinitives starting with ``?q=``, for the conjugator's suggestions."""
    prefix = (request.args.get('q') or '').strip()
    limit = min(request.args.get('limit', 8, type=int) or 8, 20)
    verbs = get_service().autocomplete(prefix, limit=limit) if prefix else []
    return jsonify(verbs=verbs)
