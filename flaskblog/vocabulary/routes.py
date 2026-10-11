"""The shared dictionary and everyone's personal word list."""

from flask import (Blueprint, Response, abort, flash, redirect, render_template,
                   request, url_for)
from flask_login import current_user, login_required

from flaskblog import db
from flaskblog.i18n import gettext as _
from flaskblog.conjugation import get_service as get_conjugation_service
from flaskblog.models import UserWord, Word
from flaskblog.permissions import is_admin
from flaskblog.vocabulary import service
from flaskblog.vocabulary.constants import (
    gender_label,
    level_label,
    part_of_speech_label,
    topic_label,
)
from flaskblog.vocabulary.forms import (
    ActionForm,
    UserWordForm,
    UserWordNoteForm,
    WordForm,
    WordImportForm,
    WordSearchForm,
)

vocabulary = Blueprint('vocabulary', __name__)

WORDS_PER_PAGE = 24


@vocabulary.app_context_processor
def inject_labels():
    """Helpers used by the dictionary templates."""
    return {
        'is_admin': is_admin,
        'topic_label': topic_label,
        'level_label': level_label,
        'part_of_speech_label': part_of_speech_label,
        'gender_label': gender_label,
    }


def _admin_only():
    if not is_admin():
        abort(403)


def _saved_word_ids():
    """Ids of the shared words the current user already saved."""
    if not current_user.is_authenticated:
        return set()
    rows = (
        db.session.query(UserWord.word_id)
        .filter(UserWord.user_id == current_user.id, UserWord.word_id.isnot(None))
        .all()
    )
    return {row[0] for row in rows}


@vocabulary.route('/dictionary')
def dictionary():
    form = WordSearchForm(request.args, meta={'csrf': False})
    page = request.args.get('page', 1, type=int)
    words = service.search(
        query_text=form.q.data,
        topic=form.topic.data,
        level=form.level.data,
        part_of_speech=form.part_of_speech.data,
    ).paginate(page=page, per_page=WORDS_PER_PAGE)

    return render_template(
        'dictionary.html',
        title=_('Словник'),
        form=form,
        words=words,
        total=Word.query.count(),
        saved_word_ids=_saved_word_ids(),
        action_form=ActionForm(),
    )


@vocabulary.route('/dictionary/<string:slug>')
def word(slug):
    word = Word.query.filter_by(slug=slug).first_or_404()
    conjugable = bool(word.is_verb and get_conjugation_service().is_known_verb(word.term))
    return render_template(
        'word.html',
        title=word.term,
        word=word,
        conjugable=conjugable,
        saved_word_ids=_saved_word_ids(),
        action_form=ActionForm(),
    )


@vocabulary.route('/dictionary/new', methods=['GET', 'POST'])
@login_required
def new_word():
    _admin_only()
    form = WordForm()
    if form.validate_on_submit():
        word = Word(
            term=form.term.data.strip(),
            translation=form.translation.data.strip(),
            part_of_speech=form.part_of_speech.data or None,
            gender=form.gender.data or None,
            pronunciation=form.pronunciation.data or None,
            topic=form.topic.data or None,
            level=form.level.data or None,
            example_ca=form.example_ca.data or None,
            example_uk=form.example_uk.data or None,
            notes=form.notes.data or None,
            user_id=current_user.id,
        )
        word.slug = service.unique_slug(word.term)
        db.session.add(word)
        db.session.commit()
        flash(_('Слово додано до словника.'), 'success')
        return redirect(url_for('vocabulary.word', slug=word.slug))
    return render_template(
        'word_form.html', title=_('Нове слово'), form=form, legend=_('Нове слово')
    )


@vocabulary.route('/dictionary/<string:slug>/edit', methods=['GET', 'POST'])
@login_required
def edit_word(slug):
    _admin_only()
    word = Word.query.filter_by(slug=slug).first_or_404()
    form = WordForm(obj=word)
    if form.validate_on_submit():
        word.term = form.term.data.strip()
        word.translation = form.translation.data.strip()
        word.part_of_speech = form.part_of_speech.data or None
        word.gender = form.gender.data or None
        word.pronunciation = form.pronunciation.data or None
        word.topic = form.topic.data or None
        word.level = form.level.data or None
        word.example_ca = form.example_ca.data or None
        word.example_uk = form.example_uk.data or None
        word.notes = form.notes.data or None
        db.session.commit()
        flash(_('Слово оновлено.'), 'success')
        return redirect(url_for('vocabulary.word', slug=word.slug))
    return render_template(
        'word_form.html',
        title=_('Редагувати слово'),
        form=form,
        legend=_('Редагувати слово'),
        word=word,
    )


@vocabulary.route('/dictionary/<string:slug>/delete', methods=['POST'])
@login_required
def delete_word(slug):
    _admin_only()
    word = Word.query.filter_by(slug=slug).first_or_404()
    db.session.delete(word)
    db.session.commit()
    flash(_('Слово видалено.'), 'success')
    return redirect(url_for('vocabulary.dictionary'))


@vocabulary.route('/dictionary/import', methods=['GET', 'POST'])
@login_required
def import_words():
    """Upload a CSV, or load the dictionary bundled with the project."""
    _admin_only()
    form = WordImportForm()
    update_existing = request.form.get('update_existing') == 'on'

    if form.validate_on_submit():
        rows = service.read_rows(form.file.data.read())
        report = service.import_rows(
            rows, author=current_user, update_existing=update_existing
        )
        db.session.commit()
        _flash_report(report)
        return redirect(url_for('vocabulary.dictionary'))

    return render_template(
        'word_import.html',
        title=_('Імпорт словника'),
        form=form,
        seed_form=ActionForm(),
        total=Word.query.count(),
    )


@vocabulary.route('/dictionary/import/seed', methods=['POST'])
@login_required
def import_seed_words():
    _admin_only()
    form = ActionForm()
    if form.validate_on_submit():
        report = service.import_seed(author=current_user)
        db.session.commit()
        _flash_report(report)
    return redirect(url_for('vocabulary.dictionary'))


def _flash_report(report):
    flash(
        _('Імпорт завершено: додано {created}, оновлено {updated}, пропущено {skipped}.',
          created=report.created, updated=report.updated, skipped=report.skipped),
        'success',
    )
    for error in report.errors[:10]:
        flash(error, 'warning')


@vocabulary.route('/dictionary/export.csv')
def export_dictionary():
    csv_text = service.export_csv()
    return Response(
        csv_text,
        mimetype='text/csv; charset=utf-8',
        headers={'Content-Disposition': 'attachment; filename=learn-catalan-dictionary.csv'},
    )


# --- personal dictionary --------------------------------------------------


@vocabulary.route('/my-dictionary')
@login_required
def my_dictionary():
    status = request.args.get('status') or ''
    query = UserWord.query.filter_by(user_id=current_user.id)
    if status in (UserWord.STATUS_LEARNING, UserWord.STATUS_KNOWN):
        query = query.filter(UserWord.status == status)
    items = query.order_by(UserWord.date_added.desc()).all()

    counts = {
        'all': UserWord.query.filter_by(user_id=current_user.id).count(),
        'learning': UserWord.query.filter_by(
            user_id=current_user.id, status=UserWord.STATUS_LEARNING
        ).count(),
        'known': UserWord.query.filter_by(
            user_id=current_user.id, status=UserWord.STATUS_KNOWN
        ).count(),
    }

    return render_template(
        'my_dictionary.html',
        title=_('Мій словник'),
        items=items,
        counts=counts,
        status=status,
        form=UserWordForm(),
        note_form=UserWordNoteForm(),
        action_form=ActionForm(),
    )


@vocabulary.route('/dictionary/<string:slug>/save', methods=['POST'])
@login_required
def save_word(slug):
    """Add a shared dictionary word to the current user's list."""
    word = Word.query.filter_by(slug=slug).first_or_404()
    form = ActionForm()
    if not form.validate_on_submit():
        abort(400)

    existing = UserWord.query.filter_by(
        user_id=current_user.id, word_id=word.id
    ).first()
    if existing is None:
        db.session.add(UserWord(user_id=current_user.id, word_id=word.id))
        db.session.commit()
        flash(_('«{term}» додано до вашого словника.', term=word.term), 'success')
    else:
        flash(_('«{term}» вже є у вашому словнику.', term=word.term), 'info')

    return redirect(request.referrer or url_for('vocabulary.word', slug=slug))


@vocabulary.route('/my-dictionary/add', methods=['POST'])
@login_required
def add_my_word():
    """Add a word of your own, which need not be in the shared dictionary."""
    form = UserWordForm()
    if form.validate_on_submit():
        term = form.term.data.strip()
        shared = Word.query.filter(db.func.lower(Word.term) == term.lower()).first()
        duplicate = None
        if shared is not None:
            duplicate = UserWord.query.filter_by(
                user_id=current_user.id, word_id=shared.id
            ).first()
        if duplicate is None:
            db.session.add(
                UserWord(
                    user_id=current_user.id,
                    word_id=shared.id if shared is not None else None,
                    term=term,
                    translation=form.translation.data.strip(),
                    note=form.note.data or None,
                )
            )
            db.session.commit()
            flash(_('«{term}» додано до вашого словника.', term=term), 'success')
        else:
            flash(_('«{term}» вже є у вашому словнику.', term=term), 'info')
    else:
        for errors in form.errors.values():
            for error in errors:
                flash(error, 'warning')
    return redirect(url_for('vocabulary.my_dictionary'))


def _own_word_or_404(item_id):
    item = UserWord.query.get_or_404(item_id)
    if item.user_id != current_user.id:
        abort(403)
    return item


@vocabulary.route('/my-dictionary/<int:item_id>/remove', methods=['POST'])
@login_required
def remove_my_word(item_id):
    item = _own_word_or_404(item_id)
    form = ActionForm()
    if not form.validate_on_submit():
        abort(400)
    db.session.delete(item)
    db.session.commit()
    flash(_('Слово вилучено з вашого словника.'), 'success')
    return redirect(url_for('vocabulary.my_dictionary'))


@vocabulary.route('/my-dictionary/<int:item_id>/status', methods=['POST'])
@login_required
def toggle_my_word(item_id):
    """Switch a word between 'learning' and 'known'."""
    item = _own_word_or_404(item_id)
    form = ActionForm()
    if not form.validate_on_submit():
        abort(400)
    item.status = (
        UserWord.STATUS_LEARNING if item.is_known else UserWord.STATUS_KNOWN
    )
    db.session.commit()
    return redirect(request.referrer or url_for('vocabulary.my_dictionary'))


@vocabulary.route('/my-dictionary/<int:item_id>/note', methods=['POST'])
@login_required
def edit_my_note(item_id):
    item = _own_word_or_404(item_id)
    form = UserWordNoteForm()
    if form.validate_on_submit():
        item.note = form.note.data or None
        db.session.commit()
        flash(_('Нотатку збережено.'), 'success')
    return redirect(url_for('vocabulary.my_dictionary'))


@vocabulary.route('/my-dictionary/export.csv')
@login_required
def export_my_dictionary():
    items = (
        UserWord.query.filter_by(user_id=current_user.id)
        .order_by(UserWord.date_added.desc())
        .all()
    )
    return Response(
        service.export_user_words_csv(items),
        mimetype='text/csv; charset=utf-8',
        headers={'Content-Disposition': 'attachment; filename=my-dictionary.csv'},
    )
