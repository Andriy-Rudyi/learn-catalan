"""``flask langsites ...`` commands."""

import click
from flask.cli import AppGroup

from flaskblog.langsites import build as builder, dictionary

langsites_cli = AppGroup('langsites', help='Розділи інших мов.')


@langsites_cli.command('build')
@click.argument('code')
def build_command(code):
    """Write the dictionary file of a language section (e.g. uk)."""
    try:
        count = builder.build(code)
    except KeyError:
        raise click.UsageError('Немає даних для мови {}. Є: {}.'.format(
            code, ', '.join(sorted(builder.BUILDERS))))
    click.echo('Записів: {}; слів: {}.'.format(count, dictionary.size(code)))
