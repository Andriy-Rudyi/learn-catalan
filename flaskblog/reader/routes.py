"""/text: paste a Catalan text, click any word (flaskblog/reader/morphology.py)."""

import time

from flask import Blueprint, abort, current_app, jsonify, render_template, request, url_for
from flask_login import current_user

from flaskblog import db
from flaskblog.conjugation.labels import mood_label, person_labels, tense_label
from flaskblog.i18n import gettext as _
from flaskblog.models import UserWord, Word
from flaskblog.reader import morphology
from flaskblog.vocabulary.constants import part_of_speech_label
from flaskblog.vocabulary.forms import ActionForm

reader = Blueprint('reader', __name__)

MAX_TEXT = 20000      # characters the page accepts
TERMS_SECONDS = 300   # how long the list of dictionary words is reused


@reader.before_request
def switched_on():
    if not current_app.config.get('READER', True):
        abort(404)


def _dictionary_terms():
    """Lower-case dictionary words, so a word only our dictionary knows is
    still recognised."""
    cache = current_app.extensions.setdefault('reader_terms', {})
    now = time.monotonic()
    if cache.get('until', 0) < now:
        cache['terms'] = {term.lower() for (term,) in db.session.query(Word.term)}
        cache['until'] = now + TERMS_SECONDS
    return cache['terms']


def _form_label(reading):
    """"Minulий простий, 3 ос. мн." or "множина, жіночий рід"."""
    if reading['kind'] == 'verb':
        mood, tense, person = reading['slot']
        parts = [mood_label(mood)]
        if tense not in ('gerundi', 'particip', 'infinitiu-present'):
            parts.append(tense_label(tense))
        persons = person_labels(mood, person + 1)
        if persons and persons[person]:
            parts.append(persons[person])
        return ', '.join(parts)
    parts = []
    if reading['plural']:
        parts.append(_('множина'))
    if reading['feminine']:
        parts.append(_('жіночий рід'))
    return ', '.join(parts)


@reader.route('/text')
def index():
    return render_template(
        'reader.html',
        title=_('Робота з текстом'),
        max_text=MAX_TEXT,
        action_form=ActionForm(),
    )


@reader.route('/text/word')
def word():
    surface = (request.args.get('w') or '')[:80]
    previous = (request.args.get('prev') or '')[:80]
    terms = _dictionary_terms()
    result = morphology.analyse(surface, previous, known=lambda lemma: lemma.lower() in terms)

    lemmas = {reading['lemma'].lower() for reading in result['readings']}
    for group in result['groups']:
        lemmas.update(item['lemma'].lower() for item in group['items'])
    found = {}
    if lemmas:
        for entry in Word.query.filter(db.func.lower(Word.term).in_(lemmas)):
            found.setdefault(entry.term.lower(), entry)
    saved = set()
    if current_user.is_authenticated and found:
        saved = {
            word_id for (word_id,) in db.session.query(UserWord.word_id).filter(
                UserWord.user_id == current_user.id,
                UserWord.word_id.in_([entry.id for entry in found.values()]))
        }

    readings, seen = [], set()
    for reading in result['readings']:
        key = (reading['lemma'], reading['kind'], tuple(reading['slot'] or ()))
        if key in seen:
            continue
        seen.add(key)
        entry = found.get(reading['lemma'].lower())
        readings.append({
            'lemma': reading['lemma'],
            'kind': reading['kind'],
            'form': _form_label(reading),
            'part_of_speech': (part_of_speech_label(entry.part_of_speech)
                               if entry is not None and entry.part_of_speech else
                               (part_of_speech_label('verb') if reading['kind'] == 'verb' else None)),
            'translation': entry.t_translation() if entry is not None else None,
            'url': url_for('vocabulary.word', slug=entry.slug) if entry is not None else None,
            'save_url': (url_for('vocabulary.save_word', slug=entry.slug)
                         if entry is not None and current_user.is_authenticated else None),
            'saved': entry is not None and entry.id in saved,
            'conjugation_url': (url_for('main.conjugator', verb=reading['lemma'])
                                if reading['kind'] == 'verb' else None),
        })

    groups = []
    for group in result['groups']:
        items = []
        for item in group['items']:
            entry = found.get(item['lemma'].lower())
            items.append({
                'text': item['text'],
                'lemma': item['lemma'],
                'register': item['register'],
                'translation': entry.t_translation() if entry is not None else None,
            })
        groups.append({'lemma': group['lemma'], 'gloss': group['gloss'], 'kind': group['kind'],
                       'items': items})

    return jsonify({'word': result['word'], 'readings': readings, 'groups': groups})
