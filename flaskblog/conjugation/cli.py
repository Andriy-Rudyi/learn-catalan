"""``flask conjugation ...`` commands for checking the conjugator."""

import click
from flask.cli import AppGroup

from flaskblog.conjugation import audit as audit_module
from flaskblog.conjugation.service import get_service

conjugation_cli = AppGroup('conjugation', help='Перевірка дієвідміни.')


@conjugation_cli.command('audit')
def audit_command():
    """Compare the conjugator against the reference forms."""
    raise SystemExit(audit_module.main())


@conjugation_cli.command('check')
@click.argument('verb')
def check_command(verb):
    """Print the conjugation of one verb."""
    result = get_service().conjugate(verb)
    if not result.ok:
        click.echo('{}: {}'.format(result.query, result.error), err=True)
        if result.suggestions:
            click.echo('Можливо: {}'.format(', '.join(result.suggestions)), err=True)
        raise SystemExit(1)

    click.echo(
        '{} (зразок {}, основа {!r}, {})'.format(
            result.display_infinitive,
            result.template,
            result.stem,
            'перевірено' if result.verified else 'не перевірено',
        )
    )
    for mood, tenses in result.moods.items():
        click.echo('\n{}'.format(mood))
        for tense, forms in tenses.items():
            click.echo('  {:<22} {}'.format(tense, ', '.join(forms)))
