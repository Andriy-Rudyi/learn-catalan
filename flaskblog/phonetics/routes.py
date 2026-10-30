from flask import Blueprint, abort, current_app, render_template, request, url_for

from flaskblog.i18n import content_language, gettext as _
from flaskblog.phonetics import service, trainer

phonetics = Blueprint('phonetics', __name__)


@phonetics.route('/phonetics')
def index():
    lessons = service.load_lessons()
    return render_template(
        'phonetics_index.html',
        title=_('Фонетика'),
        sections=service.sections(),
        total=len(lessons),
    )


@phonetics.route('/phonetics/trainer')
def trainer_page():
    if not current_app.config.get('PHONETICS_TRAINER', True):
        abort(404)
    lang = content_language()
    units = trainer.units(lang)
    return render_template(
        'phonetics_trainer.html',
        title=_('Тренажер вимови'),
        units=units,
        lesson_urls={unit['slug']: url_for('phonetics.lesson', slug=unit['slug']) for unit in units},
        per_round=trainer.QUESTIONS_PER_ROUND,
    )


@phonetics.route('/phonetics/<string:slug>')
def lesson(slug):
    lesson = service.get_lesson(slug)
    if lesson is None:
        abort(404)
    previous, following = service.neighbours(lesson)
    return render_template(
        'phonetics_lesson.html',
        title='{}. {}'.format(lesson['number'], lesson['title']),
        lesson=lesson,
        previous=previous,
        following=following,
        show_answers=request.args.get('answers') == '1',
    )
