"""/translator: translate between Catalan and the site's languages (engine.py)."""

from datetime import datetime

from flask import Blueprint, abort, current_app, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from flaskblog import db
from flaskblog.api.routes import RateLimiter, client_ip
from flaskblog.i18n import get_locale, gettext as _
from flaskblog.languages import LANGUAGES, SOURCE
from flaskblog.models import TranslationMemory
from flaskblog.reader.routes import panel_strings
from flaskblog.translate import service as platform
from flaskblog.translator import engine
from flaskblog.vocabulary.forms import ActionForm

translator = Blueprint('translator', __name__)

TARGETS = ('uk', 'en', 'fr')
REQUESTS_PER_MINUTE = 60
_limiter = RateLimiter()


@translator.before_request
def switched_on():
    if not current_app.config.get('TRANSLATOR', True):
        abort(404)


def _languages():
    return [(code, LANGUAGES[code].native) for code in TARGETS]


def _pair(source, target):
    """(source, target) when one of them is Catalan and the other ours, else None."""
    if source == SOURCE and target in TARGETS:
        return source, target
    if target == SOURCE and source in TARGETS:
        return source, target
    return None


@translator.route('/translator')
def index():
    default = get_locale() if get_locale() in TARGETS else 'en'
    return render_template(
        'translator.html',
        title=_('Перекладач'),
        languages=_languages(),
        default_target=default,
        max_text=engine.MAX_TEXT,
        has_review=current_user.is_authenticated and bool(_review_languages()),
        panel_strings=panel_strings(),
        action_form=ActionForm(),
    )


@translator.route('/translator/run', methods=['POST'])
def run():
    data = request.get_json(silent=True) or {}
    pair = _pair(data.get('source'), data.get('target'))
    text = (data.get('text') or '').strip()
    if pair is None or not text:
        return jsonify({'error': 'bad request'}), 400
    if len(text) > engine.MAX_TEXT:
        return jsonify({'error': 'too long'}), 413
    allowed, wait = _limiter.allow(client_ip(), REQUESTS_PER_MINUTE)
    if not allowed:
        return jsonify({'error': 'too many requests', 'retry_after': wait}), 429
    result = engine.translate(text, *pair)
    for sentence in result['sentences']:
        for token in sentence.get('tokens') or ():
            if token.get('slug'):
                token['url'] = url_for('vocabulary.word', slug=token.pop('slug'))
    return jsonify(result)


@translator.route('/translator/suggest', methods=['POST'])
@login_required
def suggest():
    form = ActionForm()
    if not form.validate_on_submit():
        abort(400)
    pair = _pair(request.form.get('source'), request.form.get('target'))
    source_text = (request.form.get('source_text') or '').strip()
    target_text = (request.form.get('target_text') or '').strip()
    if pair is None or not source_text or not target_text or len(source_text) > 1000 or len(target_text) > 1000:
        abort(400)
    other = pair[1] if pair[0] == SOURCE else pair[0]
    approved = platform.can_translate(other, current_user)
    engine.propose(pair[0], pair[1], source_text, target_text, current_user, approved)
    db.session.commit()
    if approved:
        engine.forget()
    return jsonify({'status': 'approved' if approved else 'pending'})


def _review_languages():
    codes = platform.translator_languages(current_user)
    if platform.ALL_LANGUAGES in codes:
        return list(TARGETS)
    return [code for code in TARGETS if code in codes]


@translator.route('/translator/review')
@login_required
def review():
    languages = _review_languages()
    if not languages:
        abort(403)
    pending = TranslationMemory.query.filter_by(status=TranslationMemory.PENDING) \
        .order_by(TranslationMemory.created_at).all()
    pending = [row for row in pending
               if (row.target_lang if row.source_lang == SOURCE else row.source_lang) in languages][:100]
    return render_template('translator_review.html', title=_('Пропозиції перекладів'),
                           pending=pending, action_form=ActionForm())


@translator.route('/translator/review/<int:row_id>', methods=['POST'])
@login_required
def decide(row_id):
    form = ActionForm()
    if not form.validate_on_submit():
        abort(400)
    row = TranslationMemory.query.get_or_404(row_id)
    other = row.target_lang if row.source_lang == SOURCE else row.source_lang
    if not platform.can_translate(other, current_user) or row.status != TranslationMemory.PENDING:
        abort(403)
    accept = request.form.get('decision') == 'accept'
    edited = (request.form.get('target_text') or '').strip()
    if accept and edited:
        row.target_text = edited[:1000]
    row.status = TranslationMemory.APPROVED if accept else TranslationMemory.REJECTED
    row.decided_by = current_user.id
    row.decided_at = datetime.utcnow()
    db.session.commit()
    engine.forget()
    flash(_('Переклад додано до пам’яті перекладача.') if accept else _('Пропозицію відхилено.'), 'success')
    return redirect(url_for('translator.review'))
