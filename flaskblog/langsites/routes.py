"""Pages of the language sections (see flaskblog/langsites/__init__.py)."""

from flask import Blueprint, abort, jsonify, render_template, request, url_for

from flaskblog import sites
from flaskblog.i18n import get_locale, gettext as _
from flaskblog.langsites import content as sections_content, dictionary, reading
from flaskblog.vocabulary.constants import part_of_speech_label
from flaskblog.permissions import is_admin

langsites = Blueprint('langsites', __name__)

_SLUGS = ','.join(site.slug for site in sites.SECTIONS)
_PREFIX = '/<any({}):slug>'.format(_SLUGS)

# Languages a section's entries may be translated into (the English one
# also holds the explanations of their meanings), in the default order.
_TRANSLATIONS = dictionary.LANGS

# The parts of a section, the same as the Catalan site's: (address, name,
# icon). The dictionary has its own pages; the others show that their
# material is being prepared until it is written.
PAGES = (
    ('grammar', 'Граматика', 'grammar'),
    ('dictionary', 'Словник', 'dictionary'),
    ('conjugator', 'Дієвідміна', 'conjugator'),
    ('phonetics', 'Фонетика', 'phonetics'),
    ('course', 'Курс C1/C2', 'course'),
    ('text', 'Текст', 'text'),
    ('reading', 'Читання', 'book'),
    ('translator', 'Перекладач', 'translator'),
)
# Parts that still show "being prepared" (the others have their own pages).
_EMPTY = ('translator',)

_GENDERS = {'m': 'чоловічий рід', 'f': 'жіночий рід', 'n': 'середній рід'}
_ASPECTS = {'pf': 'доконаний вид', 'ipf': 'недоконаний вид'}


@langsites.app_context_processor
def inject_sections():
    """The sections for the side menu: the switched-on ones, and for the
    editor also the hidden ones."""
    def visible():
        editor = is_admin()
        return [site for site in sites.SECTIONS if site.enabled or editor]
    return {'language_sections': visible}


def _section(slug):
    """The site of *slug*; a hidden one only for the editor."""
    site = sites.BY_SLUG[slug]
    if not site.enabled and not is_admin():
        abort(404)
    return site


def _languages(site):
    """Translation languages in the order to show them: the interface
    language first, never the language being learnt."""
    preferred = [get_locale()] + list(_TRANSLATIONS)
    order = []
    for lang in preferred:
        if lang in _TRANSLATIONS and lang != site.code and lang not in order:
            order.append(lang)
    return order


def _ready(site, page):
    """True when a part of the section has material."""
    if page == 'dictionary':
        return dictionary.available(site.code)
    if page == 'reading':
        return bool(reading.works(site.code))
    if page == 'text':
        return dictionary.available(site.code)
    return bool(sections_content.load(site.code).get(page))


def _common(site):
    def url(key):
        if key == 'dictionary':
            return url_for('langsites.dictionary_page', slug=site.slug)
        if key == 'reading':
            return url_for('langsites.library', slug=site.slug)
        if key == 'text':
            return url_for('langsites.text_page', slug=site.slug)
        if key in _EMPTY:
            return url_for('langsites.page', slug=site.slug, page=key)
        return url_for('langsites.content_page', slug=site.slug, page=key)

    pages = [{'key': key, 'name': _(name), 'icon': icon, 'ready': _ready(site, key), 'url': url(key)}
             for key, name, icon in PAGES]
    sections = {s.code: s.slug for s in sites.SECTIONS if s.enabled or is_admin()}

    def word_url(lang, word):
        """Where a translation leads: its word in the Catalan dictionary or
        in another section's."""
        word = dictionary.item_word(word).replace('\u0301', '')
        if lang == 'ca':
            return url_for('vocabulary.dictionary', q=word)
        if lang in sections and dictionary.available(lang):
            return url_for('langsites.dictionary_page', slug=sections[lang], q=word)
        return None

    return {'lang_site': site, 'hidden': not site.enabled, 'section_pages': pages,
            'word_url': word_url, 'item_word': dictionary.item_word,
            'sources': dictionary.meta(site.code).get('sources', ()),
            'gender_text': lambda value: _(_GENDERS[value]) if value in _GENDERS else '',
            'aspect_text': lambda value: _(_ASPECTS[value]) if value in _ASPECTS else ''}


@langsites.route(_PREFIX + '/')
def home(slug):
    site = _section(slug)
    return render_template('langsite_home.html', title=site.native,
                           words=dictionary.size(site.code) if dictionary.available(site.code) else 0,
                           **_common(site))


@langsites.route(_PREFIX + '/<any({}):page>'.format(','.join(_EMPTY)))
def page(slug, page):
    site = _section(slug)
    name = next(_(label) for key, label, _icon in PAGES if key == page)
    return render_template('langsite_page.html', title=name, page_key=page, page_name=name,
                           **_common(site))


@langsites.route(_PREFIX + '/dictionary')
def dictionary_page(slug):
    site = _section(slug)
    query = (request.args.get('q') or '').strip()[:100]
    entries, how = dictionary.search(site.code, query, _languages(site)) if query else ([], None)
    return render_template('langsite_dictionary.html', title=_('Словник'), query=query,
                           entries=entries, how=how, languages=_languages(site),
                           words=dictionary.size(site.code), **_common(site))


@langsites.route(_PREFIX + '/dictionary/<path:word>')
def word(slug, word):
    site = _section(slug)
    entries = dictionary.lookup(site.code, word)
    if not entries:
        abort(404)
    return render_template('langsite_word.html', title=entries[0]['w'].replace('́', ''),
                           entries=entries, languages=_languages(site), **_common(site))


def _names():
    return {'uk': _('Українська'), 'en': _('Англійська'), 'es': _('Іспанська'),
            'ca': _('Каталанська'), 'fr': _('Французька'), 'de': _('Німецька')}


@langsites.route(_PREFIX + '/word')
def word_panel(slug):
    """A word as it stands in a text, for the word panel of the reading and
    text pages (static/reader.js, the same format as the Catalan one)."""
    site = _section(slug)
    surface = (request.args.get('w') or '')[:80]
    clean = (reading.WORD.search(surface) or None)
    clean = clean.group() if clean else ''
    entries, form = dictionary.find(site.code, clean)
    names = _names()
    readings = []
    for entry in entries:
        parts = []
        for lang in _languages(site):
            texts = dictionary.translations(entry, lang)
            if texts:
                parts.append('{}: {}'.format(names[lang], '; '.join(texts[:5])))
        readings.append({
            'lemma': entry['w'],
            'part_of_speech': part_of_speech_label(entry['pos']),
            'form': _('від «{lemma}»', lemma=entry['w']) if form and form != clean.lower() and
                    form != clean else '',
            'translation': ' · '.join(parts),
            'url': url_for('langsites.word', slug=site.slug, word=entry['k']),
        })
    return jsonify({'word': clean, 'transcription': None, 'readings': readings, 'groups': []})


def _panel_config(site, mode=None):
    from flaskblog.reader.routes import panel_strings
    strings = panel_strings()
    strings['nothing'] = _('Цього слова в словнику поки немає.')
    config = {'wordUrl': url_for('langsites.word_panel', slug=site.slug), 'loggedIn': False,
              'strings': strings, 'synonyms': False, 'speechLang': site.code,
              'store': 'langwave:{}:text:v1'.format(site.code)}
    if mode:
        config['mode'] = mode
    return config


@langsites.route(_PREFIX + '/reading')
def library(slug):
    site = _section(slug)
    return render_template('langsite_library.html', title=_('Читання'), page_key='reading',
                           works=reading.works(site.code), **_common(site))


@langsites.route(_PREFIX + '/reading/<work_slug>')
def work_page(slug, work_slug):
    site = _section(slug)
    work = reading.work(site.code, work_slug)
    if work is None:
        abort(404)
    return render_template('langsite_work.html', title=work.get('short_title') or work['title'],
                           page_key='reading', work=work, **_common(site))


@langsites.route(_PREFIX + '/reading/<work_slug>/<int:number>')
def read(slug, work_slug, number):
    site = _section(slug)
    work = reading.work(site.code, work_slug)
    if work is None:
        abort(404)
    text = reading.part(work, number)
    if text is None:
        abort(404)
    return render_template('langsite_read.html', title=work.get('short_title') or work['title'],
                           page_key='reading', work=work, number=number, text=text,
                           total=len(work['files']), parts=work['parts'],
                           panel_config=_panel_config(site, 'read'), **_common(site))


@langsites.route(_PREFIX + '/text')
def text_page(slug):
    site = _section(slug)
    content = sections_content.load(site.code)
    return render_template('langsite_text.html', title=_('Робота з текстом'), page_key='text',
                           example=content.get('text_example', ''),
                           panel_config=dict(_panel_config(site), example=content.get('text_example', '')),
                           **_common(site))


@langsites.route(_PREFIX + '/<any(grammar,phonetics,conjugator,course):page>')
def content_page(slug, page):
    site = _section(slug)
    content = sections_content.load(site.code)
    name = next(_(label) for key, label, _icon in PAGES if key == page)
    return render_template('langsite_content.html', title=name, page_key=page, page_name=name,
                           items=content.get(page, ()), explained_in=content.get('explained_in', 'uk'),
                           **_common(site))
