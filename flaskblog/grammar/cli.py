"""``flask grammar ...`` commands for the course."""

import click
from flask.cli import AppGroup

from flaskblog import db
from flaskblog.grammar import service
from flaskblog.models import GrammarUnit

grammar_cli = AppGroup('grammar', help='Робота з курсом граматики.')


@grammar_cli.command('seed')
def seed_command():
    """Load (or refresh) the grammar units from the bundled files."""
    report = service.seed()
    db.session.commit()
    click.echo(
        'Створено: {}, оновлено: {}.'.format(report.created, report.updated)
    )


@grammar_cli.command('stats')
def stats_command():
    """Show how many units and exercises the course holds."""
    units = GrammarUnit.query.order_by(GrammarUnit.number).all()
    click.echo('Юнітів: {}'.format(len(units)))
    click.echo('Вправ (завдань): {}'.format(sum(u.exercise_count for u in units)))
    click.echo('\nРозділи:')
    for section, section_units in service.sections().items():
        numbers = [u.number for u in section_units]
        click.echo('  {:<34} {} (№ {}-{})'.format(
            section, len(section_units), min(numbers), max(numbers)
        ))
