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

While listening the page shows the text and lights up the word being read:
``/…/listen/<n>.json`` gives the part's text (flaskblog/audiobook_text.py)
and when each sentence is read (``flaskblog/audiobook_timings/``, written
with the MP3s); the words of a sentence share its time by their length.

``/audio/<file>`` passes a part on from where it is published, a piece
(1 MB) per request, for browsers that cannot reach that host themselves
(an old Android tablet); the player falls back to it when the sound does
not load.
"""

import functools
import io
import json
import os
import re
import urllib.request

from flask import Blueprint, Response, abort, redirect, request

HERE = os.path.dirname(os.path.abspath(__file__))
MANIFEST = os.path.join(HERE, 'audiobooks.json')
TIMINGS = os.path.join(HERE, 'audiobook_timings')
PIECE = 1024 * 1024  # bytes of audio passed on per request

audio_files = Blueprint('audiobooks', __name__)


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


@functools.lru_cache(maxsize=16)
def timing(file_name):
    """The sentences' timings of a part ([[piece, start, end, from, to]]), or []."""
    name = os.path.basename(file_name)
    if name.endswith('.mp3'):
        name = name[:-len('.mp3')]
    try:
        with io.open(os.path.join(TIMINGS, name + '.json'), encoding='utf-8') as handle:
            return json.load(handle).get('sentences', [])
    except (OSError, ValueError):
        return []


def text(lang, slug, number):
    """{pieces, sentences} of a part for the listening page, or None."""
    from flaskblog import audiobook_text

    found = parts(lang, slug)
    if not 1 <= number <= len(found):
        return None
    pieces = audiobook_text.pieces(lang, slug, number)
    if pieces is None:
        return None
    return {'pieces': pieces, 'sentences': timing(found[number - 1]['file'])}


def _published(name):
    """The manifest's entry of a file, or None."""
    for works in manifest().get('works', {}).values():
        for found in works.values():
            for part in found:
                if part.get('file') == name:
                    return part
    return None


@audio_files.route('/audio/<name>')
def audio(name):
    """A piece of a published part, for browsers that cannot reach its host."""
    part = _published(name)
    if part is None:
        abort(404)
    url = manifest().get('base', '') + name
    size = int(part.get('bytes') or 0)
    asked = re.match(r'bytes=(\d*)-(\d*)$', request.headers.get('Range', '').strip())
    if not asked or not size:
        return redirect(url)
    if asked.group(1):
        start = int(asked.group(1))
        end = int(asked.group(2)) if asked.group(2) else size - 1
    elif asked.group(2):
        start, end = max(0, size - int(asked.group(2))), size - 1
    else:
        return redirect(url)
    if start >= size:
        return Response(status=416, headers={'Content-Range': 'bytes */{}'.format(size)})
    end = min(end, size - 1, start + PIECE - 1)
    upstream = urllib.request.Request(url, headers={'Range': 'bytes={}-{}'.format(start, end),
                                                    'User-Agent': 'audiobook-relay'})
    try:
        with urllib.request.urlopen(upstream, timeout=20) as reply:
            body = reply.read()
            if reply.status == 200:  # the host sent all of it
                body = body[start:end + 1]
    except (OSError, ValueError):
        abort(502)
    end = start + len(body) - 1
    return Response(body, status=206, mimetype='audio/mpeg', headers={
        'Content-Range': 'bytes {}-{}/{}'.format(start, end, size),
        'Accept-Ranges': 'bytes',
        'Cache-Control': 'public, max-age=86400'})


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


def page(lang, slug, title, author, labels, read_urls, text_urls=()):
    """What templates/audiobook.html needs: (book, config for the player).
    *labels*, *read_urls* and *text_urls* go part by part ("Capítol 1", its
    reading page, its text while listening)."""
    from flask import url_for

    from flaskblog.i18n import gettext as _

    found = parts(lang, slug)
    items = []
    for index, part in enumerate(found):
        items.append({'title': labels[index] if index < len(labels) else str(index + 1),
                      'url': part['url'], 'seconds': part.get('seconds', 0),
                      'clock': clock(part.get('seconds', 0)),
                      'read_url': read_urls[index] if index < len(read_urls) else None,
                      'text_url': text_urls[index] if index < len(text_urls) else None,
                      'proxy': url_for('audiobooks.audio', name=part['file'])})
    book = {'lang': lang, 'title': title, 'author': author, 'parts': items,
            'duration': clock(sum(item['seconds'] for item in items)), 'voice': voice(lang)}
    config = {'title': title, 'author': author, 'store': 'audiobook:{}:{}'.format(lang, slug),
              'artwork': url_for('static', filename='og-image.png', _external=True),
              'parts': [{'title': item['title'], 'url': item['url'], 'seconds': item['seconds'],
                         'text': item['text_url'], 'proxy': item['proxy']} for item in items],
              'strings': {'play': _('Слухати'), 'pause': _('Пауза'),
                          'resume': _('Ви зупинилися на «{part}», {time}. Натисніть ▶, щоб продовжити.'),
                          'error': _('Не вдалося завантажити звук. Перевірте інтернет і натисніть ▶ ще раз.'),
                          'loading': _('Завантаження тексту…'),
                          'no_text': _('Текст цієї частини не вдалося завантажити.')}}
    return book, config
