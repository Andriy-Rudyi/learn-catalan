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


@langsites_cli.command('import-play')
@click.argument('xml_path', type=click.Path(exists=True, dir_okay=False))
@click.argument('code')
@click.argument('slug')
@click.option('--title', help='Назва (інакше з XML).')
@click.option('--short-title')
@click.option('--author')
@click.option('--year', type=int)
@click.option('--level')
@click.option('--source', help='Звідки текст і його ліцензія.')
def import_play_command(xml_path, code, slug, **info):
    """Import a play in Shakespeare XML (Jon Bosak) into a section."""
    from flaskblog.langsites import reading
    count = reading.import_play(xml_path, code, slug,
                                **{name: value for name, value in info.items() if value})
    click.echo('Сцен: {}.'.format(count))
