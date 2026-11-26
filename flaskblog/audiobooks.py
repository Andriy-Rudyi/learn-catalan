"""Audiobooks: the reading works read aloud, to listen to like a podcast.

The MP3s (one per chapter or scene, made with Piper by
scripts/make_audiobooks.py) are assets of the GitHub release
``audiobooks``; GitHub serves them, with seeking, so the site stores and
streams nothing. ``flaskblog/audiobooks.json`` lists them::

    {"base": "https://github.com/<owner>/<repo>/releases/download/audiobooks/",
     "voices": {"ca": "Piper voice ...", ...},
     "works": {"ca": {"martin-eden": [{"file": "ca-martin-eden-01.mp3",
                                       "seconds": 1690, "bytes": 8450000}, ...]}}}

Real audio files (not the browser's speech synthesis) keep playing with
the screen locked, and the page gives the phone's lock screen and the car
its controls (static/audiobook.js, Media Session API).
"""

import functools
import io
import json
import os

MANIFEST = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'audiobooks.json')


@functools.lru_cache(maxsize=1)
def manifest():
    try:
        with io.open(MANIFEST, encoding='utf-8') as handle:
            return json.load(handle)
    except (OSError, ValueError):
        return {}


def parts(lang, slug):
    """[{url, seconds, bytes, number}] of a work in a language, or []."""
    data = manifest()
    found = data.get('works', {}).get(lang, {}).get(slug, [])
    return [dict(part, number=number, url=data.get('base', '') + part['file'])
            for number, part in enumerate(found, 1)]


def available(lang, slug):
    return bool(parts(lang, slug))


def voice(lang):
    return manifest().get('voices', {}).get(lang, '')


def duration(lang, slug):
    return sum(part.get('seconds', 0) for part in parts(lang, slug))


def clock(seconds):
    """1:02:03 or 12:34."""
    seconds = int(seconds or 0)
    hours, rest = divmod(seconds, 3600)
    minutes, seconds = divmod(rest, 60)
    return '{}:{:02d}:{:02d}'.format(hours, minutes, seconds) if hours else '{}:{:02d}'.format(minutes, seconds)


def page(lang, slug, title, author, labels, read_urls):
    """What templates/audiobook.html needs: (book, config for the player).
    *labels* and *read_urls* go part by part ("Capítol 1", its reading page)."""
    from flask import url_for

    from flaskblog.i18n import gettext as _

    found = parts(lang, slug)
    items = []
    for index, part in enumerate(found):
        items.append({'title': labels[index] if index < len(labels) else str(index + 1),
                      'url': part['url'], 'seconds': part.get('seconds', 0),
                      'clock': clock(part.get('seconds', 0)),
                      'read_url': read_urls[index] if index < len(read_urls) else None})
    book = {'lang': lang, 'title': title, 'author': author, 'parts': items,
            'duration': clock(sum(item['seconds'] for item in items)), 'voice': voice(lang)}
    config = {'title': title, 'author': author, 'store': 'audiobook:{}:{}'.format(lang, slug),
              'artwork': url_for('static', filename='og-image.png', _external=True),
              'parts': [{'title': item['title'], 'url': item['url'], 'seconds': item['seconds']} for item in items],
              'strings': {'play': _('Слухати'), 'pause': _('Пауза'),
                          'resume': _('Ви зупинилися на «{part}», {time}. Натисніть ▶, щоб продовжити.')}}
    return book, config
