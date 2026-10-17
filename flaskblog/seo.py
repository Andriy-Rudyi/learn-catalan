"""Search engines and link previews.

Adds to every page a canonical link, links to the other language version
(hreflang), a robots tag for pages that should stay out of search results,
Open Graph tags for previews in messengers and social networks, and serves
/robots.txt and /sitemap.xml.

All of it is switched off with SEO=False in the environment: pages then get
the head they had before (title "Learn Catalan - Page", no extra tags) and
/robots.txt and /sitemap.xml answer 404.

The two languages share URLs and the language normally comes from a cookie or
the browser, so for search engines each version gets an explicit address:
``?lang=uk`` and ``?lang=en``. The bare address is the ``x-default``.
"""

import time
from urllib.parse import urlencode

from flask import Blueprint, Response, abort, current_app, request, url_for
from markupsafe import escape

from flaskblog.i18n import LANGUAGES, get_locale

seo = Blueprint('seo', __name__)

# Pages worth finding in a search engine. Everything else (login, account,
# forms, search results with filters, errors) gets "noindex".
INDEXABLE = {
    'main.home',
    'main.faq',
    'main.conjugator',
    'grammar.index',
    'grammar.unit',
    'grammar.unit_by_number',
    'phonetics.index',
    'phonetics.lesson',
    'vocabulary.dictionary',
    'vocabulary.word',
}

# Query parameters that make a different page rather than a different view.
CANONICAL_ARGS = {
    'main.conjugator': ('verb',),
    'vocabulary.dictionary': ('page',),
}

# Dictionary filters: a filtered list is a search result, not a page to index.
DICTIONARY_FILTERS = ('q', 'topic', 'level', 'part_of_speech', 'variety')

OG_LOCALES = {'uk': 'uk_UA', 'en': 'en_US'}

SITEMAP_TTL = 3600  # seconds
_sitemap_cache = {}


def enabled():
    return bool(current_app.config.get('SEO'))


def site_url():
    """Scheme and host of the public site, without a trailing slash."""
    configured = current_app.config.get('SITE_URL')
    if configured:
        return configured.rstrip('/')
    scheme = request.headers.get('X-Forwarded-Proto', request.scheme).split(',')[0].strip()
    return '{}://{}'.format(scheme, request.host)


def _url(path, args):
    query = urlencode(args)
    return site_url() + path + ('?' + query if query else '')


def _page_args(endpoint):
    args = []
    for name in CANONICAL_ARGS.get(endpoint, ()):
        value = (request.args.get(name) or '').strip()
        if value and not (name == 'page' and value == '1'):
            args.append((name, value))
    return args


def is_indexable(endpoint):
    if endpoint not in INDEXABLE:
        return False
    if endpoint == 'vocabulary.dictionary':
        return not any(request.args.get(name) for name in DICTIONARY_FILTERS)
    return True


def head(canonical_path=None, noindex=False):
    """Values for the <head> of the current page (see layout.html).

    A template can pass ``canonical_path`` when the same page has two
    addresses, and ``noindex`` for a page that should not be found
    (e.g. a conjugation of a word that is not a verb).
    """
    endpoint = request.endpoint or ''
    path = canonical_path or request.path
    args = _page_args(endpoint)
    alternates = [(lang, _url(path, args + [('lang', lang)])) for lang in LANGUAGES]
    locale = get_locale()
    return {
        'canonical': _url(path, args + [('lang', locale)]),
        'alternates': alternates,
        'x_default': _url(path, args),
        'robots': None if is_indexable(endpoint) and not noindex else 'noindex, follow',
        'og_locale': OG_LOCALES.get(locale, 'uk_UA'),
        'og_locale_alternates': [OG_LOCALES[lang] for lang in LANGUAGES if lang != locale],
        'site_url': site_url(),
    }


def website_data():
    """schema.org description of the site, with its dictionary search."""
    root = site_url()
    return {
        '@context': 'https://schema.org',
        '@type': 'WebSite',
        'name': 'Learn Catalan',
        'url': root + '/',
        'inLanguage': list(LANGUAGES),
        'potentialAction': {
            '@type': 'SearchAction',
            'target': {
                '@type': 'EntryPoint',
                'urlTemplate': root + url_for('vocabulary.dictionary') + '?q={search_term_string}',
            },
            'query-input': 'required name=search_term_string',
        },
    }


@seo.route('/robots.txt')
def robots_txt():
    if not enabled():
        abort(404)
    lines = [
        'User-agent: *',
        'Disallow: /admin',
        'Disallow: /account',
        'Disallow: /my-dictionary',
        'Disallow: /api/',
        'Disallow: /reset_password',
        'Disallow: /dictionary/export.csv',
        'Disallow: /dictionary/import',
        '',
        'Sitemap: ' + site_url() + url_for('seo.sitemap_xml'),
        '',
    ]
    return Response('\n'.join(lines), mimetype='text/plain')


def _sitemap_paths():
    """Paths of every page worth indexing, as (path, extra query args)."""
    from flaskblog.conjugation import get_service
    from flaskblog.models import GrammarUnit, Word
    from flaskblog.phonetics.service import load_lessons

    yield url_for('main.home'), []
    yield url_for('grammar.index'), []
    for (slug,) in GrammarUnit.query.with_entities(GrammarUnit.slug).order_by(GrammarUnit.number):
        yield url_for('grammar.unit', slug=slug), []
    yield url_for('phonetics.index'), []
    for lesson in load_lessons():
        yield url_for('phonetics.lesson', slug=lesson['slug']), []
    yield url_for('vocabulary.dictionary'), []
    words = Word.query.with_entities(Word.slug, Word.term, Word.part_of_speech).order_by(Word.term).all()
    for slug, _term, _pos in words:
        yield url_for('vocabulary.word', slug=slug), []
    conjugator = url_for('main.conjugator')
    yield conjugator, []
    verbs = get_service()
    for _slug, term, pos in words:
        if pos == 'verb' and verbs.is_known_verb(term):
            yield conjugator, [('verb', term)]
    if current_app.config.get('SHOW_FAQ'):
        yield url_for('main.faq'), []


def _build_sitemap():
    out = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"'
        ' xmlns:xhtml="http://www.w3.org/1999/xhtml">',
    ]
    for path, args in _sitemap_paths():
        versions = [(lang, _url(path, args + [('lang', lang)])) for lang in LANGUAGES]
        links = ''.join(
            '<xhtml:link rel="alternate" hreflang="{}" href="{}"/>'.format(lang, escape(href))
            for lang, href in versions
        ) + '<xhtml:link rel="alternate" hreflang="x-default" href="{}"/>'.format(escape(_url(path, args)))
        for _lang, href in versions:
            out.append('<url><loc>{}</loc>{}</url>'.format(escape(href), links))
    out.append('</urlset>')
    return '\n'.join(out) + '\n'


@seo.route('/sitemap.xml')
def sitemap_xml():
    if not enabled():
        abort(404)
    key = site_url()
    cached = _sitemap_cache.get(key)
    if cached is None or time.time() - cached[0] > SITEMAP_TTL or current_app.testing:
        cached = (time.time(), _build_sitemap())
        _sitemap_cache[key] = cached
    return Response(cached[1], mimetype='application/xml')


def init_app(app):
    app.register_blueprint(seo)

    @app.context_processor
    def inject_seo():
        return {'seo_head': head, 'seo_website_data': website_data}
