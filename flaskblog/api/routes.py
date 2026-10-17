import threading
import time
from collections import defaultdict, deque

from flask import Blueprint, Response, current_app, jsonify, request, url_for
from werkzeug.exceptions import HTTPException

from flaskblog import db
from flaskblog.conjugation import get_service as get_conjugation_service
from flaskblog.conjugation.labels import MOOD_ORDER
from flaskblog.languages import LANGUAGES, SOURCE, is_known
from flaskblog.seo import site_url
from flaskblog.models import Word, WordTranslation
from flaskblog.vocabulary import service as vocabulary_service
from flaskblog.vocabulary import varieties
from flaskblog.vocabulary.constants import LEVELS, PARTS_OF_SPEECH, TOPICS

api = Blueprint('api', __name__, url_prefix='/api/v1')

VERSION = '1.0'
MAX_PER_PAGE = 100
DEFAULT_PER_PAGE = 20
CACHE_SECONDS = 3600

# Person keys for each mood's list of forms, in the order the forms come.
PERSONS = ('1s', '2s', '3s', '1p', '2p', '3p')
MOOD_PERSONS = {
    'imperatiu': ('2s', '3s', '1p', '2p', '3p'),
    'particip': ('ms', 'fs', 'mp', 'fp'),
    'infinitiu': (),
    'gerundi': (),
}

# Third-party material in the data, and what its licence asks for (README,
# "Data sources and licences").
SOURCES = [
    {
        'data': 'Regional labels (where a word is used instead of Central Catalan)',
        'source': 'Wiktionary, English and Catalan editions',
        'license': 'CC BY-SA 4.0',
        'url': 'https://www.wiktionary.org/',
    },
    {
        'data': 'Which words and verbs the dictionary includes (by frequency)',
        'source': 'FrequencyWords by Hermit Dave, from OpenSubtitles 2018 (OPUS)',
        'license': 'CC BY-SA 4.0',
        'url': 'https://github.com/hermitdave/FrequencyWords',
    },
    {
        'data': 'Synonyms on the /text page',
        'source': 'sinonims-cat thesaurus by Jaume Ortolà Font and contributors, Softcatalà',
        'license': 'CC BY 4.0',
        'url': 'https://github.com/Softcatala/sinonims-cat',
    },
    {
        'data': 'Verb conjugations',
        'source': 'verbecc (LGPL-3.0), with Catalan data from Verbiste and catverbs, '
                  'and this site\'s corrections to it',
        'license': 'GPL-2.0-or-later',
        'url': 'https://github.com/bretttolbert/verbecc',
    },
]

ERROR_MESSAGES = {
    'empty': 'No verb was given.',
    'too-long': 'The verb is too long.',
    'not-a-single-word': 'Give one verb in the infinitive, e.g. "parlar", not "jo parlo".',
    'not-catalan-letters': 'The verb contains characters that are not Catalan letters.',
    'unknown-verb': 'This is not a Catalan verb we know.',
    'internal': 'The verb could not be conjugated.',
}


def absolute(endpoint, **values):
    """A full link on the public site (https behind the hosting proxy)."""
    return site_url() + url_for(endpoint, **values)


# -- errors, CORS, caching, rate limit ----------------------------------------

def error(status, code, message, **extra):
    body = {'error': dict({'code': code, 'message': message}, **extra)}
    return jsonify(body), status


class RateLimiter(object):
    """At most *limit* requests per client in any 60 seconds (one process)."""

    def __init__(self):
        self.hits = defaultdict(deque)
        self.lock = threading.Lock()

    def allow(self, key, limit, now=None):
        now = time.time() if now is None else now
        with self.lock:
            hits = self.hits[key]
            while hits and hits[0] <= now - 60:
                hits.popleft()
            if len(hits) >= limit:
                return False, int(60 - (now - hits[0])) + 1
            hits.append(now)
            if len(self.hits) > 10000:  # forget idle clients
                for idle in [k for k, v in self.hits.items() if not v]:
                    del self.hits[idle]
            return True, 0


def client_ip():
    # Behind the hosting proxy the client is the last address it added.
    forwarded = request.headers.get('X-Forwarded-For', '')
    if forwarded:
        return forwarded.split(',')[-1].strip()
    return request.remote_addr or 'unknown'


@api.before_request
def rate_limit():
    if request.method == 'OPTIONS':
        return None
    limit = current_app.config.get('API_RATE_LIMIT', 120)
    if not limit:
        return None
    allowed, retry_after = current_app.extensions['api_rate_limiter'].allow(client_ip(), limit)
    if not allowed:
        response, status = error(429, 'rate-limited',
                                 'Too many requests: at most {} a minute.'.format(limit))
        response.headers['Retry-After'] = str(retry_after)
        return response, status
    return None


@api.after_request
def open_to_everyone(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Accept, Content-Type'
    response.headers.setdefault('Cache-Control', 'public, max-age={}'.format(CACHE_SECONDS))
    response.headers['X-API-Version'] = VERSION
    return response


@api.errorhandler(HTTPException)
def http_error(exc):
    return error(exc.code or 500, exc.name.lower().replace(' ', '-'), exc.description)


# -- serialisers ----------------------------------------------------------------

def requested_languages():
    """Codes from ?lang=fr,uk, or None for all."""
    raw = request.args.get('lang', '').strip()
    if not raw:
        return None
    codes = [code.strip() for code in raw.split(',') if code.strip()]
    unknown = [code for code in codes if not is_known(code)]
    if unknown:
        return unknown, None
    return None, codes


def word_json(word, languages=None):
    translations = {
        lang: {'translation': entry.translation, 'example': entry.example, 'notes': entry.notes,
               'reviewed': entry.reviewed}
        for lang, entry in sorted(word.translations.items())
        if entry.translation and (languages is None or lang in languages)
    }
    data = {
        'term': word.term,
        'slug': word.slug,
        'language': SOURCE,
        'part_of_speech': word.part_of_speech,
        'gender': word.gender,
        'pronunciation': word.pronunciation,
        'topic': word.topic,
        'level': word.level,
        'example': word.example_ca,
        'regional': list(word.variety_codes),
        'central_alternative': word.central_alternative if word.variety_codes else None,
        'translations': translations,
        'conjugation': (absolute('api.conjugation', verb=word.term)
                        if word.is_verb else None),
        'url': absolute('vocabulary.word', slug=word.slug),
        'api_url': absolute('api.word', slug=word.slug),
    }
    if current_app.config.get('SENSES'):
        # The same translations, meaning by meaning (English decides the meanings).
        data['senses'] = [
            {
                'position': sense.position,
                'translations': {
                    lang: {'text': entry.text, 'reviewed': entry.reviewed}
                    for lang, entry in sorted(sense.translations.items())
                    if entry.text and (languages is None or lang in languages)
                },
            }
            for sense in word.senses
        ]
    return data


def conjugation_json(result):
    moods = {}
    for mood in [m for m in MOOD_ORDER if m in result.moods] + \
            [m for m in result.moods if m not in MOOD_ORDER]:
        persons = MOOD_PERSONS.get(mood, PERSONS)
        tenses = {}
        for tense, forms in result.moods[mood].items():
            if persons:
                tenses[tense] = [
                    {'person': persons[i] if i < len(persons) else None, 'form': form}
                    for i, form in enumerate(forms)
                ]
            else:
                tenses[tense] = [{'person': None, 'form': form} for form in forms]
        moods[mood] = tenses
    return {
        'query': result.query,
        'infinitive': result.display_infinitive,
        'base_infinitive': result.infinitive,
        'pronominal': result.is_pronominal,
        'model': result.template,
        'verified': result.verified,
        'moods': moods,
        'url': absolute('main.conjugator', verb=result.display_infinitive),
    }


# -- endpoints ------------------------------------------------------------------

@api.route('')
@api.route('/')
def index():
    return jsonify({
        'name': 'Learn Catalan open API',
        'version': VERSION,
        'documentation': absolute('api_docs.developers'),
        'openapi': absolute('api.openapi'),
        'endpoints': {
            'languages': absolute('api.languages'),
            'words': absolute('api.words'),
            'word': absolute('api.word', slug='anar'),
            'conjugation': absolute('api.conjugation', verb='anar'),
            'verbs': absolute('api.verbs', q='par'),
            'dictionary_csv': absolute('api.dictionary_csv'),
        },
        'sources': SOURCES,
    })


@api.route('/languages')
def languages():
    counts = dict(
        db.session.query(WordTranslation.lang, db.func.count(WordTranslation.id))
        .filter(WordTranslation.translation != '')
        .group_by(WordTranslation.lang)
        .all()
    )
    return jsonify({
        'source': SOURCE,
        'data': [
            {'code': lang.code, 'name': lang.name, 'native_name': lang.native,
             'rtl': lang.rtl, 'words': counts.get(lang.code, 0)}
            for lang in LANGUAGES.values()
        ],
    })


@api.route('/words')
def words():
    unknown, languages = requested_languages() or (None, None)
    if unknown:
        return error(400, 'unknown-language', 'Unknown language: {}.'.format(', '.join(unknown)),
                     languages=list(LANGUAGES))
    page = request.args.get('page', 1, type=int) or 1
    per_page = min(max(request.args.get('per_page', DEFAULT_PER_PAGE, type=int) or 1, 1), MAX_PER_PAGE)
    query = vocabulary_service.search(
        query_text=(request.args.get('q') or '').strip()[:100] or None,
        topic=request.args.get('topic') or None,
        level=request.args.get('level') or None,
        part_of_speech=request.args.get('part_of_speech') or None,
        variety=request.args.get('variety') or None,
    )
    if languages:
        query = query.filter(Word.translations.any(WordTranslation.lang.in_(languages)))
    result = query.paginate(page=max(page, 1), per_page=per_page, error_out=False)

    def page_url(number):
        args = dict(request.args.to_dict(), page=number, per_page=per_page)
        return absolute('api.words', **args)

    return jsonify({
        'data': [word_json(word, languages) for word in result.items],
        'meta': {'page': result.page, 'per_page': per_page, 'total': result.total, 'pages': result.pages},
        'links': {
            'next': page_url(result.page + 1) if result.has_next else None,
            'prev': page_url(result.page - 1) if result.has_prev else None,
        },
    })


@api.route('/words/<string:slug>')
def word(slug):
    unknown, languages = requested_languages() or (None, None)
    if unknown:
        return error(400, 'unknown-language', 'Unknown language: {}.'.format(', '.join(unknown)),
                     languages=list(LANGUAGES))
    entry = Word.query.filter_by(slug=slug).first()
    if entry is None:
        entry = Word.query.filter(db.func.lower(Word.term) == slug.lower()).first()
    if entry is None:
        return error(404, 'not-found', 'No dictionary word with this slug or term.')
    return jsonify({'data': word_json(entry, languages)})


@api.route('/conjugations/<path:verb>')
def conjugation(verb):
    result = get_conjugation_service().conjugate(verb[:60])
    if not result.ok:
        status = 404 if result.error == 'unknown-verb' else 400
        return error(status, result.error or 'invalid', ERROR_MESSAGES.get(result.error, 'Invalid verb.'),
                     suggestions=result.suggestions)
    return jsonify({'data': conjugation_json(result)})


@api.route('/verbs')
def verbs():
    prefix = (request.args.get('q') or '').strip()[:60]
    limit = min(max(request.args.get('limit', 10, type=int) or 10, 1), 50)
    found = get_conjugation_service().autocomplete(prefix, limit=limit) if prefix else []
    return jsonify({'data': found})


@api.route('/dictionary.csv')
def dictionary_csv():
    """The whole dictionary in every language, in the import format."""
    response = Response(vocabulary_service.export_csv(), mimetype='text/csv')
    response.headers['Content-Disposition'] = 'attachment; filename=learn-catalan-dictionary.csv'
    return response


@api.route('/openapi.json')
def openapi():
    from flaskblog.api.spec import spec
    return jsonify(spec(
        server=absolute('api.index').rstrip('/'),
        topics=[code for code, _ in TOPICS],
        levels=[code for code, _ in LEVELS],
        parts_of_speech=[code for code, _ in PARTS_OF_SPEECH],
        languages=list(LANGUAGES),
        regions=list(varieties.CODES),
    ))


def wants_json():
    return request.path.startswith(api.url_prefix + '/') or request.path == api.url_prefix


def init_app(app):
    from flaskblog.api.docs import api_docs

    app.config.setdefault('API_RATE_LIMIT', 120)
    app.extensions['api_rate_limiter'] = RateLimiter()
    app.json.sort_keys = False  # keep fields in a readable order
    app.register_blueprint(api)
    app.register_blueprint(api_docs)
