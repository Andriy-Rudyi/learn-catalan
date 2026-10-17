"""``flask translations ...``: translators, and writing what was translated
on /translate back into the project's files."""

import csv
import json
import os

import click
from flask.cli import AppGroup

from flaskblog import db
from flaskblog.languages import CODES
from flaskblog.models import Translator, User
from flaskblog.translate import service

translations_cli = AppGroup('translations', help='Платформа перекладу (/translate).')

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DICTIONARY_DIR = os.path.join(PROJECT_DIR, 'vocabulary', 'data', 'translations')
CATALOG_DIR = os.path.join(PROJECT_DIR, 'i18n')

_CATALOG_HEADER = '''"""{name} interface strings, keyed by the Ukrainian source text.

Written by ``flask translations export {code}`` from the catalogue and what was
translated on /translate.
"""

MESSAGES = {{
'''


def _user(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        raise click.ClickException('Немає користувача {}.'.format(username))
    return user


def _lang(code):
    if code != service.ALL_LANGUAGES and code not in CODES:
        raise click.ClickException('Невідома мова {}. Мови: {}, або *.'.format(code, ', '.join(CODES)))
    return code


@translations_cli.command('grant')
@click.argument('username')
@click.argument('lang')
def grant_command(username, lang):
    """Let USERNAME translate and review LANG (* for every language)."""
    user, lang = _user(username), _lang(lang)
    if Translator.query.filter_by(user_id=user.id, lang=lang).first() is None:
        db.session.add(Translator(user_id=user.id, lang=lang))
        db.session.commit()
    click.echo('{} перекладає {}.'.format(user.username, lang))


@translations_cli.command('revoke')
@click.argument('username')
@click.argument('lang')
def revoke_command(username, lang):
    """Take LANG away from USERNAME."""
    user = _user(username)
    Translator.query.filter_by(user_id=user.id, lang=lang).delete()
    db.session.commit()
    click.echo('{} більше не перекладає {}.'.format(user.username, lang))


@translations_cli.command('export')
@click.argument('lang')
@click.option('--dictionary/--no-dictionary', default=True, help='translations/<lang>.csv')
@click.option('--interface/--no-interface', default=True, help='flaskblog/i18n/<lang>.py')
def export_command(lang, dictionary, interface):
    """Write LANG's translations from the database into the project's files,
    so they are kept with the code (commit them afterwards)."""
    _lang(lang)
    if dictionary:
        rows = service.export_dictionary(lang)
        path = os.path.join(DICTIONARY_DIR, lang + '.csv')
        with open(path, 'w', encoding='utf-8', newline='') as handle:
            writer = csv.DictWriter(handle, fieldnames=['term', 'translation', 'example', 'notes', 'reviewed'],
                                    lineterminator='\n')
            writer.writeheader()
            writer.writerows(rows)
        click.echo('Словник: {} слів у {}.'.format(len(rows), path))
    if interface and lang in service.interface_languages():
        entries = service.export_interface(lang)
        path = os.path.join(CATALOG_DIR, lang + '.py')
        from flaskblog.languages import LANGUAGES
        with open(path, 'w', encoding='utf-8') as handle:
            handle.write(_CATALOG_HEADER.format(name=LANGUAGES[lang].name, code=lang))
            for source, text in entries:
                handle.write('    {}: {},\n'.format(json.dumps(source, ensure_ascii=False),
                                                     json.dumps(text, ensure_ascii=False)))
            handle.write('}\n')
        click.echo('Інтерфейс: {} рядків у {}.'.format(len(entries), path))
