"""/translate: the translation platform (see service.py)."""

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from flaskblog import db
from flaskblog.i18n import gettext as _
from flaskblog.languages import LANGUAGES
from flaskblog.models import (TranslationChange, TranslationSuggestion, User, Word,
                              WordSense)
from flaskblog.translate import service
from flaskblog.translate.forms import TranslationForm

translate = Blueprint('translate', __name__, url_prefix='/translate')

WORDS_PER_PAGE = 20
STRINGS_PER_PAGE = 40


@translate.app_context_processor
def inject_translate():
    def language_label(code):
        language = LANGUAGES.get(code)
        if language is None:
            return code
        from flaskblog.i18n import get_locale
        return language.native if get_locale() == 'uk' or code == get_locale() else language.name
    return {'language_label': language_label}


def _language(lang, interface=False):
    allowed = service.interface_languages() if interface else service.dictionary_languages()
    if lang not in allowed:
        abort(404)
    return LANGUAGES[lang]


def _back(default):
    """Where to return after a POST: the page it came from on /translate."""
    target = request.form.get('next') or ''
    if target.startswith('/translate') and not target.startswith('//'):
        return redirect(target)
    return redirect(default)


@translate.route('/')
def index():
    rows = service.progress()
    return render_template(
        'translate_index.html',
        title=_('Переклад'),
        rows=rows,
        percent=service.percent,
        my_languages=service.translator_languages(current_user),
        changes=service.recent_changes(limit=10),
    )


# -- dictionary -----------------------------------------------------------------------

@translate.route('/<lang>/dictionary')
def dictionary(lang):
    language = _language(lang)
    status = request.args.get('status', 'todo')
    if status not in service.DICTIONARY_FILTERS:
        status = 'todo'
    text = (request.args.get('q') or '').strip()[:100]
    page = request.args.get('page', 1, type=int) or 1
    result = service.dictionary_query(lang, status, text or None).paginate(
        page=max(page, 1), per_page=WORDS_PER_PAGE, error_out=False)
    return render_template(
        'translate_dictionary.html',
        title=_('Переклад словника: {language}', language=language.native),
        lang=lang,
        language=language,
        status=status,
        filters=service.DICTIONARY_FILTERS,
        q=text,
        result=result,
        references=service.reference_languages(lang),
        suggestions=service.suggestions_for_words(lang, result.items),
        drafts={word.id for word in result.items if service.is_draft(word, lang)},
        can_translate=service.can_translate(lang, current_user),
        can_suggest=service.can_suggest(current_user),
        form=TranslationForm(),
    )


@translate.route('/<lang>/dictionary/<int:word_id>', methods=['POST'])
@login_required
def save_word(lang, word_id):
    _language(lang)
    word = db.session.get(Word, word_id) or abort(404)
    form = TranslationForm()
    back = url_for('translate.dictionary', lang=lang)
    if not form.validate_on_submit():
        abort(400)
    action = form.action.data
    if action == 'check':
        if not service.can_translate(lang, current_user):
            abort(403)
        if service.mark_checked(word, lang, current_user):
            db.session.commit()
            flash(_('«{term}»: позначено як перевірене.', term=word.term), 'success')
        return _back(back)

    kind = form.kind.data
    if kind == 'sense':
        sense = db.session.get(WordSense, form.sense_id.data or 0)
        if sense is None or sense.word_id != word.id:
            abort(404)
        target = service.Target('sense', lang, sense=sense)
    elif kind in ('example', 'notes'):
        target = service.Target(kind, lang, word=word)
    else:
        abort(400)
    return _save(target, form, back, label=word.term)


# -- interface ---------------------------------------------------------------------------

@translate.route('/<lang>/interface')
def interface(lang):
    language = _language(lang, interface=True)
    status = request.args.get('status', 'missing')
    if status not in service.INTERFACE_FILTERS:
        status = 'missing'
    text = (request.args.get('q') or '').strip()[:100]
    page = max(request.args.get('page', 1, type=int) or 1, 1)
    rows = service.interface_rows(lang, status, text or None)
    pages = max((len(rows) + STRINGS_PER_PAGE - 1) // STRINGS_PER_PAGE, 1)
    page = min(page, pages)
    shown = rows[(page - 1) * STRINGS_PER_PAGE:page * STRINGS_PER_PAGE]
    return render_template(
        'translate_interface.html',
        title=_('Переклад інтерфейсу: {language}', language=language.native),
        lang=lang,
        language=language,
        status=status,
        filters=service.INTERFACE_FILTERS,
        q=text,
        rows=shown,
        total=len(rows),
        page=page,
        pages=pages,
        key_of=service.source_key,
        suggestions=service.ui_suggestions(lang, [row[0] for row in shown]),
        can_translate=service.can_translate(lang, current_user),
        can_suggest=service.can_suggest(current_user),
        form=TranslationForm(),
    )


@translate.route('/<lang>/interface', methods=['POST'])
@login_required
def save_interface(lang):
    _language(lang, interface=True)
    form = TranslationForm()
    if not form.validate_on_submit():
        abort(400)
    sources = {service.source_key(source): source for source in service.interface_strings()}
    source = sources.get(form.key.data or '')
    if source is None:
        abort(404)
    target = service.Target('ui', lang, ui_source=source)
    return _save(target, form, url_for('translate.interface', lang=lang), label=None)


def _save(target, form, back, label):
    text = (form.text.data or '').strip()
    action = form.action.data
    if action == 'suggest' or not service.can_translate(target.lang, current_user):
        if not text:
            flash(_('Порожню пропозицію не збережено.'), 'warning')
            return _back(back)
        error = target.check(text)
        if error:
            flash(error, 'danger')
            return _back(back)
        if (not service.can_translate(target.lang, current_user)
                and service.open_suggestions(current_user) >= service.MAX_OPEN_SUGGESTIONS):
            flash(_('У вас забагато пропозицій, що чекають перевірки. Дочекайтеся, поки їх розглянуть.'), 'warning')
            return _back(back)
        service.suggest(target, text, current_user)
        db.session.commit()
        flash(_('Дякуємо! Пропозицію перевірить перекладач цієї мови.'), 'success')
        return _back(back)

    if text:
        error = target.check(text)
        if error:
            flash(error, 'danger')
            return _back(back)
    current = target.shown()
    if (current or '') != (form.base.data or ''):
        flash(_('Поки ви редагували, хтось уже змінив цей переклад: «{text}». '
                'Подивіться на нього й збережіть ще раз, якщо ваш кращий.', text=current or '—'),
              'warning')
        return _back(back)
    if text == (current or '') or (not text and target.current()[0] is None):
        return _back(back)  # nothing to change (a catalogue string cannot be emptied)
    service.change(target, text, current_user)
    db.session.commit()
    flash(_('Збережено.'), 'success')
    return _back(back)


# -- suggestions, history ------------------------------------------------------------------

@translate.route('/suggestions/<int:suggestion_id>/<decision>', methods=['POST'])
@login_required
def decide(suggestion_id, decision):
    suggestion = db.session.get(TranslationSuggestion, suggestion_id) or abort(404)
    if decision not in ('accept', 'reject'):
        abort(404)
    if not service.can_translate(suggestion.lang, current_user):
        abort(403)
    form = TranslationForm()
    if not form.validate_on_submit():
        abort(400)
    if suggestion.status != TranslationSuggestion.OPEN:
        return _back(url_for('translate.index'))
    if decision == 'accept':
        error = service.Target.of(suggestion).check(suggestion.text)
        if error:
            flash(error, 'danger')
            return _back(url_for('translate.index'))
    service.decide(suggestion, decision == 'accept', current_user)
    db.session.commit()
    flash(_('Пропозицію прийнято.') if decision == 'accept' else _('Пропозицію відхилено.'), 'success')
    return _back(url_for('translate.index'))


@translate.route('/<lang>/history')
def history(lang):
    language = _language(lang)
    return render_template(
        'translate_history.html',
        title=_('Історія перекладів: {language}', language=language.native),
        lang=lang,
        language=language,
        changes=service.recent_changes(lang, limit=200),
        users={user.id: user for user in User.query.filter(
            User.id.in_(db.session.query(TranslationChange.user_id).filter(
                TranslationChange.lang == lang)))},
        can_translate=service.can_translate(lang, current_user),
        form=TranslationForm(),
    )


@translate.route('/changes/<int:change_id>/revert', methods=['POST'])
@login_required
def revert(change_id):
    record = db.session.get(TranslationChange, change_id) or abort(404)
    if not service.can_translate(record.lang, current_user):
        abort(403)
    form = TranslationForm()
    if not form.validate_on_submit():
        abort(400)
    if service.revert(record, current_user) is None:
        flash(_('Цього вже немає у словнику.'), 'warning')
    else:
        db.session.commit()
        flash(_('Зміну скасовано.'), 'success')
    return _back(url_for('translate.history', lang=record.lang))
