"""Pages of the language sections (see flaskblog/langsites/__init__.py)."""

from flask import Blueprint, abort, render_template, request

from flaskblog import sites
from flaskblog.i18n import get_locale, gettext as _
from flaskblog.langsites import dictionary
from flaskblog.permissions import is_admin

langsites = Blueprint('langsites', __name__)

_SLUGS = ','.join(site.slug for site in sites.SECTIONS)
_PREFIX = '/<any({}):slug>'.format(_SLUGS)

# Languages a section's entries are translated into, besides the English
# explanations of their meanings.
_TRANSLATIONS = ('en', 'es', 'ca')

_GENDERS = {'m': 'чоловічий рід', 'f': 'жіночий рід', 'n': 'середній рід'}
_ASPECTS = {'pf': 'доконаний вид', 'ipf': 'недоконаний вид'}


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


def _common(site):
    return {'lang_site': site, 'hidden': not site.enabled,
            'gender_text': lambda value: _(_GENDERS[value]) if value in _GENDERS else '',
            'aspect_text': lambda value: _(_ASPECTS[value]) if value in _ASPECTS else ''}


@langsites.route(_PREFIX + '/')
def home(slug):
    site = _section(slug)
    return render_template('langsite_home.html', title=site.native,
                           words=dictionary.size(site.code) if dictionary.available(site.code) else 0,
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
