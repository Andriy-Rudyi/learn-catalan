from flask import Blueprint, abort, render_template, request

from flaskblog.phonetics import service

phonetics = Blueprint('phonetics', __name__)


@phonetics.route('/phonetics')
def index():
    lessons = service.load_lessons()
    return render_template(
        'phonetics_index.html',
        title='Фонетика',
        sections=service.sections(),
        total=len(lessons),
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
