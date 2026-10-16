"""``flask vocabulary ...`` commands for filling the dictionary."""

import csv

import click
from flask.cli import AppGroup

from flaskblog import db
from flaskblog.models import Word
from flaskblog.vocabulary import service, varieties

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


@vocabulary_cli.command('check-dialects')
@click.option('--apply', 'apply_changes', is_flag=True,
              help='Записати підтверджені й нові позначки в data/varieties.json.')
@click.option('--verbs', is_flag=True,
              help='Перевірити також усі дієслова дієвідміни, яких немає у словнику.')
@click.option('--report', 'report_path', default='dialect_report.csv', show_default=True,
              type=click.Path(dir_okay=False), help='CSV-звіт з результатом для кожного слова.')
@click.option('--limit', type=int, default=None, help='Перевірити лише перші N слів (для проби).')
@click.option('--editions', default='en,ca', show_default=True,
              help='Які видання Вікісловника питати.')
def check_dialects_command(apply_changes, verbs, report_path, limit, editions):
    """Check which words are not Central Catalan, using Wiktionary.

    Needs internet access. Asks the public MediaWiki API of the English and
    Catalan Wiktionary (50 words per request, one request per second) for the
    regional labels of each word. A word counts as regional when every sense
    is labelled Valencian, Balearic, North-Western, archaic…

    Missing labels do not prove that a word is Central, so marks made by the
    review are never removed automatically; the report lists them instead.
    """
    terms = sorted({word.term for word in Word.query.all()})
    if verbs:
        from flaskblog.conjugation import get_service
        known = set(terms)
        terms += sorted(v for v in get_service().infinitives if v not in known)
    if limit:
        terms = terms[:limit]
    editions = tuple(e.strip() for e in editions.split(',') if e.strip() in varieties.API)

    click.echo('Перевіряю {} слів у Вікісловнику ({})…'.format(len(terms), ', '.join(editions)))
    results = varieties.check(
        terms, editions,
        progress=lambda edition, done, total: click.echo('  {}: {}/{}'.format(edition, done, total)),
    )

    entries = dict(varieties.load())
    counts = {}
    rows = []
    for term in terms:
        per_edition = results[term]
        status, codes = varieties.verdict(per_edition)
        entry = entries.get(term)
        ours = list(varieties.parse_codes(entry.get('variety'))) if entry else []
        if status == 'regional' and entry:
            action = 'confirmed'
        elif status == 'regional':
            action = 'new'
        elif ours and status == 'central':
            action = 'conflict'
        elif ours:
            action = 'not-confirmed'
        elif status == 'partial':
            action = 'partial'
        else:
            action = ''
        counts[action or status] = counts.get(action or status, 0) + 1

        if apply_changes and action in ('confirmed', 'new'):
            source = 'wiktionary-en' if (per_edition.get('en') or {}).get('regional') else 'wiktionary-ca'
            updated = dict(entry or {})
            updated['variety'] = sorted(set(ours) | set(codes)) or ['dialectal']
            updated['source'] = source
            entries[term] = updated

        rows.append({
            'term': term,
            'ours': ','.join(ours),
            'status': status,
            'wiktionary': ','.join(codes),
            'action': action,
            'en': _senses(per_edition.get('en')),
            'ca': _senses(per_edition.get('ca')),
        })

    with open(report_path, 'w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]) if rows else ['term'])
        writer.writeheader()
        writer.writerows(rows)

    labels = {
        'confirmed': 'підтверджено', 'new': 'нові регіональні', 'conflict': 'конфлікт (у Вікісловнику — центральне)',
        'not-confirmed': 'не підтверджено (немає позначки)', 'partial': 'частково регіональні значення',
        'unlabelled': 'без позначок', 'unknown': 'немає у Вікісловнику',
    }
    for key, label in labels.items():
        if counts.get(key):
            click.echo('{:<45} {}'.format(label, counts[key]))
    click.echo('Звіт: {}'.format(report_path))

    if apply_changes:
        varieties.save(entries)
        changed = service.apply_varieties(entries)
        db.session.commit()
        click.echo('Записано data/varieties.json; змінено позначок у базі: {}.'.format(changed))
    else:
        click.echo('Нічого не змінено. Додайте --apply, щоб записати результат.')


def _senses(result):
    """'2/3' — regional senses out of all, or '-' when the page is missing."""
    if not result:
        return '-'
    return '{}/{}'.format(result['regional'], result['senses'])
