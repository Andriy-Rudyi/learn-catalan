"""``flask vocabulary ...`` commands for filling the dictionary."""

import click
from flask.cli import AppGroup

from flaskblog import db
from flaskblog.models import Word
from flaskblog.vocabulary import service

vocabulary_cli = AppGroup('vocabulary', help='Робота зі словником слів.')


def _report(report):
    click.echo(
        'Додано: {}, оновлено: {}, пропущено: {}.'.format(
            report.created, report.updated, report.skipped
        )
    )
    for error in report.errors:
        click.echo('  {}'.format(error), err=True)


@vocabulary_cli.command('seed')
@click.option('--update', is_flag=True, help='Оновити слова, які вже є.')
def seed_command(update):
    """Load the dictionary bundled with the project."""
    report = service.import_seed(update_existing=update)
    db.session.commit()
    _report(report)


@vocabulary_cli.command('import')
@click.argument('path', type=click.Path(exists=True, dir_okay=False))
@click.option('--update', is_flag=True, help='Оновити слова, які вже є.')
def import_command(path, update):
    """Import dictionary entries from a CSV file."""
    report = service.import_file(path, update_existing=update)
    db.session.commit()
    _report(report)


@vocabulary_cli.command('export')
@click.argument('path', type=click.Path(dir_okay=False), required=False)
def export_command(path):
    """Write the dictionary to a CSV file, or to standard output."""
    csv_text = service.export_csv()
    if path:
        with open(path, 'w', encoding='utf-8', newline='') as handle:
            handle.write(csv_text)
        click.echo('Записано {} слів у {}.'.format(Word.query.count(), path))
    else:
        click.echo(csv_text)


@vocabulary_cli.command('stats')
def stats_command():
    """Show how many words the dictionary holds, by topic and level."""
    click.echo('Усього слів: {}'.format(Word.query.count()))
    for column, title in ((Word.topic, 'Теми'), (Word.level, 'Рівні')):
        click.echo('\n{}:'.format(title))
        rows = (
            db.session.query(column, db.func.count(Word.id))
            .group_by(column)
            .order_by(db.func.count(Word.id).desc())
            .all()
        )
        for value, count in rows:
            click.echo('  {:<20} {}'.format(value or '(не вказано)', count))
