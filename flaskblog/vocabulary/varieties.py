"""Regional varieties: which words are not used in Central Catalan.

The course teaches Central Catalan (Barcelona). Words that belong to another
variety (eixir, xiquet, acotxar…) or that are archaic are marked, so the
learner knows to use the central word instead.

The marks live in ``data/varieties.json``::

    {"eixir": {"variety": ["valencian"], "source": "wiktionary-en",
               "note": "Valencian for sortir"}}

``flask vocabulary seed`` copies them onto the dictionary entries, and the
conjugator reads the file directly for verbs that are not in the dictionary.

``flask vocabulary check-dialects`` verifies the marks against Wiktionary
(the English and the Catalan edition) through the public MediaWiki API, which
labels regional senses ("Valencia", "Balearic", "valencià", "balear"…).
"""

import json
import os
import re
import time
import urllib.parse
import urllib.request

from flaskblog.i18n import gettext

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'varieties.json')

# Codes stored in the data, with the label shown to learners.
VARIETIES = (
    ('valencian', 'валенсійське'),
    ('balearic', 'балеарське'),
    ('northwestern', 'північно-західне (Льєйда)'),
    ('western', 'західне'),
    ('northern', 'північнокаталанське (Руссільйон)'),
    ('alguerese', 'альгерське'),
    ('dialectal', 'діалектне'),
    ('archaic', 'застаріле'),
)
VARIETY_LABELS = dict(VARIETIES)
CODES = tuple(code for code, _ in VARIETIES)


def variety_label(code):
    return gettext(VARIETY_LABELS.get(code, code))


def parse_codes(value):
    """'valencian,balearic' or a list → a tuple of known codes."""
    if not value:
        return ()
    if isinstance(value, str):
        value = value.split(',')
    return tuple(code.strip() for code in value if code.strip() in VARIETY_LABELS)


# -- the data file -----------------------------------------------------

_cache = {}


def load(path=DATA_FILE):
    """{term: entry} from the data file (cached; empty if there is none)."""
    if path not in _cache:
        if os.path.exists(path):
            with open(path, encoding='utf-8') as handle:
                _cache[path] = json.load(handle)
        else:
            _cache[path] = {}
    return _cache[path]


def save(entries, path=DATA_FILE):
    with open(path, 'w', encoding='utf-8') as handle:
        json.dump(dict(sorted(entries.items())), handle, ensure_ascii=False, indent=1)
        handle.write('\n')
    _cache.pop(path, None)


def lookup(term, path=DATA_FILE):
    """The variety codes of a term, or () when it is Central / unknown."""
    entry = load(path).get(term)
    return parse_codes(entry.get('variety')) if entry else ()


# -- Wiktionary ----------------------------------------------------------

API = {
    'en': 'https://en.wiktionary.org/w/api.php',
    'ca': 'https://ca.wiktionary.org/w/api.php',
}
USER_AGENT = 'LearnCatalan/1.0 (https://github.com/Andriy-Rudyi/learn-catalan; dialect check)'
BATCH_SIZE = 50  # the API's limit for titles per request

# Label → code. Labels that mean the sense is Central (or common to the
# eastern dialects, which include Central) are mapped to None.
EN_LABELS = {
    'valencia': 'valencian', 'valencian': 'valencian', 'southern valencian': 'valencian',
    'balearic': 'balearic', 'majorca': 'balearic', 'mallorca': 'balearic',
    'majorcan': 'balearic', 'minorca': 'balearic', 'menorca': 'balearic',
    'ibiza': 'balearic', 'eivissa': 'balearic', 'ibizan': 'balearic',
    'north-western catalan': 'northwestern', 'northwestern catalan': 'northwestern',
    'north-western': 'northwestern', 'northwestern': 'northwestern', 'lleida': 'northwestern',
    'ribagorçan': 'northwestern', 'pallarese': 'northwestern', 'andorra': 'northwestern',
    'tortosí': 'western', 'western catalan': 'western', 'western': 'western',
    'northern catalan': 'northern', 'roussillon': 'northern', 'rossellonese': 'northern',
    'alghero': 'alguerese', 'algherese': 'alguerese',
    'dialectal': 'dialectal', 'regional': 'dialectal',
    'archaic': 'archaic', 'obsolete': 'archaic', 'dated': 'archaic', 'historical': None,
    'central catalan': None, 'central': None, 'eastern catalan': None, 'eastern': None,
    'barcelona': None, 'catalonia': None,
}
CA_LABELS = {
    'valencià': 'valencian', 'valencia': 'valencian',
    'balear': 'balearic', 'baleàric': 'balearic', 'mallorquí': 'balearic',
    'menorquí': 'balearic', 'eivissenc': 'balearic',
    'nord-occidental': 'northwestern', 'lleidatà': 'northwestern', 'ribagorçà': 'northwestern',
    'pallarès': 'northwestern', 'andorrà': 'northwestern',
    'occidental': 'western', 'tortosí': 'western',
    'septentrional': 'northern', 'rossellonès': 'northern', 'nord-català': 'northern',
    'alguerès': 'alguerese',
    'dialectal': 'dialectal', 'regional': 'dialectal',
    'antic': 'archaic', 'arcaic': 'archaic', 'arcaisme': 'archaic', 'obsolet': 'archaic',
    'desusat': 'archaic', 'en desús': 'archaic',
    'central': None, 'oriental': None, 'barceloní': None,
}

# Definitions that only point to another headword (verb forms, plurals…).
# They count as ordinary senses: a page whose main sense is "feminine of
# fill" must not look regional because of one labelled minor sense.
FORM_OF = re.compile(
    r'\{\{\s*(inflection of|infl of|ca-verb form of|verb form of|plural of|feminine of|'
    r'feminine plural of|masculine plural of|forma-conj|forma-p|forma-f|forma-fp|forma-mp)\b',
    re.I,
)
EN_LABEL_TEMPLATE = re.compile(r'\{\{\s*(?:lb|lbl|label|tlb|term-label)\s*\|\s*ca\s*\|([^{}]*)\}\}', re.I)
CA_LABEL_TEMPLATE = re.compile(r'\{\{\s*(?:marca|marca-nocat|m)\s*\|\s*ca\s*\|([^{}]*)\}\}', re.I)


def _section(wikitext, edition):
    """The Catalan part of a Wiktionary page."""
    if edition == 'en':
        match = re.search(r'^==\s*Catalan\s*==\s*$', wikitext, re.M)
    else:
        match = re.search(r'^==\s*\{\{\s*-ca-\s*\}\}\s*==\s*$', wikitext, re.M)
    if not match:
        return None
    rest = wikitext[match.end():]
    following = re.search(r'^==[^=].*==\s*$', rest, re.M)
    return rest[:following.start()] if following else rest


def _labels(line, edition):
    template = EN_LABEL_TEMPLATE if edition == 'en' else CA_LABEL_TEMPLATE
    table = EN_LABELS if edition == 'en' else CA_LABELS
    found = []
    for match in template.finditer(line):
        for part in match.group(1).split('|'):
            part = part.strip().lower()
            if not part or '=' in part or part in ('_', 'and', 'or', 'i', 'o'):
                continue
            if part in table:
                found.append(table[part])
    return found


def classify(wikitext, edition):
    """Read the regional labels of a page's Catalan senses.

    Returns None when the page has no Catalan entry, otherwise a dict:
    ``senses`` (definitions counted), ``regional`` (definitions marked as not
    Central), ``codes`` (their varieties), ``central`` (True when at least one
    sense carries no regional mark) and ``labelled_central`` (True when a
    sense is explicitly labelled Central).
    """
    section = _section(wikitext or '', edition)
    if section is None:
        return None
    senses = regional = 0
    labelled_central = False
    codes = []
    headword_codes = []
    for line in section.splitlines():
        stripped = line.strip()
        if stripped.startswith('=='):
            headword_codes = []  # a new part of speech
            continue
        if not stripped.startswith('#') and ('{{tlb|' in stripped or '{{term-label|' in stripped):
            headword_codes = _labels(stripped, edition)
            continue
        if not re.match(r'#(?![:*#])', stripped):
            continue  # examples, quotations, sub-items
        # A definition such as "feminine of fill" (filla) or "plural of" is
        # still a sense of the word, used everywhere unless it is labelled.
        senses += 1
        labels = headword_codes + _labels(stripped, edition)
        marked = [code for code in labels if code]
        if None in labels:
            labelled_central = True
        # A sense labelled both Central and regional is used in Central.
        if marked and None not in labels:
            regional += 1
            codes.extend(code for code in marked if code not in codes)
    return {
        'senses': senses,
        'regional': regional,
        'codes': codes,
        'central': senses == 0 or regional < senses,
        'labelled_central': labelled_central,
    }


def fetch_pages(titles, edition, opener=None, pause=1.0):
    """{title: wikitext} for up to BATCH_SIZE titles (missing pages omitted)."""
    params = {
        'action': 'query', 'prop': 'revisions', 'rvprop': 'content', 'rvslots': 'main',
        'format': 'json', 'formatversion': '2', 'redirects': '1', 'maxlag': '5',
        'titles': '|'.join(titles),
    }
    url = API[edition] + '?' + urllib.parse.urlencode(params)
    request = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
    opener = opener or urllib.request.urlopen
    for attempt in range(4):
        try:
            with opener(request, timeout=30) as response:
                payload = json.loads(response.read().decode('utf-8'))
            break
        except Exception:  # network hiccup or rate limit: back off and retry
            if attempt == 3:
                raise
            time.sleep(pause * (2 ** (attempt + 1)))
    if pause:
        time.sleep(pause)
    redirects = {r['to']: r['from'] for r in payload.get('query', {}).get('redirects', [])}
    pages = {}
    for page in payload.get('query', {}).get('pages', []):
        if page.get('missing') or not page.get('revisions'):
            continue
        title = redirects.get(page['title'], page['title'])
        pages[title] = page['revisions'][0]['slots']['main']['content']
    return pages


def check(terms, editions=('en', 'ca'), fetch=fetch_pages, progress=None):
    """Classify *terms* in each Wiktionary edition.

    Returns {term: {edition: classification or None}}.
    """
    results = {term: {} for term in terms}
    for edition in editions:
        for start in range(0, len(terms), BATCH_SIZE):
            batch = terms[start:start + BATCH_SIZE]
            pages = fetch(batch, edition)
            for term in batch:
                results[term][edition] = classify(pages.get(term), edition)
            if progress:
                progress(edition, min(start + BATCH_SIZE, len(terms)), len(terms))
    return results


def verdict(per_edition):
    """Combine the editions into (status, codes).

    - 'central': a sense is explicitly labelled Central, which is strong evidence;
    - 'regional': every edition that has the word marks every sense of it as
      regional or archaic (the editions must agree: one of them often lists a
      common meaning the other leaves out);
    - 'partial': some senses are marked regional, others are not;
    - 'unlabelled': the word is there without regional labels. That is NOT
      proof that it is Central (dictionaries often list Valencian or Balearic
      words as plain standard words), so existing marks are kept;
    - 'unknown': no edition has the word.
    """
    found = [result for result in per_edition.values() if result]
    if not found:
        return 'unknown', []
    codes = []
    for result in found:
        codes.extend(code for code in result['codes'] if code not in codes)
    if any(result['labelled_central'] for result in found):
        return 'central', codes
    with_senses = [result for result in found if result['senses']]
    if with_senses and all(r['regional'] == r['senses'] for r in with_senses):
        return 'regional', codes
    if codes:
        return 'partial', codes
    return 'unlabelled', []
