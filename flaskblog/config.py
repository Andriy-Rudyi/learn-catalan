import os
import secrets
import warnings


# Set by the hosting platforms; there a missing setting must be an error
# rather than a silent fallback.
HOSTED_MARKERS = ('RENDER', 'RAILWAY_ENVIRONMENT', 'DYNO', 'FLY_APP_NAME')

# Local development without any settings: the SQLite file in instance/.
LOCAL_DATABASE_URL = 'sqlite:///learn_catalan.db'


def is_hosted():
    return any(os.getenv(marker) for marker in HOSTED_MARKERS)


def database_url():
    """Database URL from the hosting environment.

    Railway exposes DATABASE_PUBLIC_URL; Render, Heroku and Fly use
    DATABASE_URL. Some of them still hand out the old ``postgres://``
    scheme, which SQLAlchemy no longer accepts. On a developer's machine
    with neither set, the local SQLite database is used.
    """
    url = os.getenv('DATABASE_PUBLIC_URL') or os.getenv('DATABASE_URL')
    if url and url.startswith('postgres://'):
        url = 'postgresql://' + url[len('postgres://'):]
    if not url and not is_hosted():
        url = LOCAL_DATABASE_URL
    return url


def secret_key():
    """SECRET_KEY from the environment.

    Without one, outside a known host, a random key is made for this run of
    the app: forms and logins work, but nobody can forge a session cookie,
    because the key is never written anywhere. (A fixed fallback key would
    be public, since the code is.) You are logged out when the app restarts.
    """
    key = os.getenv('SECRET_KEY')
    if key or is_hosted():
        return key
    warnings.warn('SECRET_KEY is not set: using a random key for this run only.')
    return secrets.token_hex(32)


class Config:
    # Local db (.bash_profile)
    # SECRET_KEY = os.environ.get('SECRET_KEY') 
    # SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI')

    # Production db
    SECRET_KEY = secret_key()
    SQLALCHEMY_DATABASE_URI = database_url()
    # Free hosted databases (Neon, Render) close idle connections; check each
    # pooled connection before use instead of failing the next request.
    SQLALCHEMY_ENGINE_OPTIONS = {'pool_pre_ping': True, 'pool_recycle': 280}

    #DB_URL = 'postgresql+psycopg2://{user}:{pw}@{url}/{db}'.format(user=POSTGRES_USER, pw=POSTGRES_PW, url=POSTGRES_URL, db=POSTGRES_DB)
    #SQLALCHEMY_DATABASE_URI = DB_URL


    # FAQ is shown in the menu; set SHOW_FAQ=False to hide the page.
    SHOW_FAQ = os.getenv('SHOW_FAQ', 'True') == 'True'

    # Look of the site for visitors who have not picked one in the menu:
    # 'modern' (rounded, with a pinned menu) or 'classic' (the earlier look).
    # DESIGN=classic rolls everybody back to the earlier look.
    DESIGN = os.getenv('DESIGN', 'modern')

    # Tags for search engines and link previews, /robots.txt and /sitemap.xml
    # (flaskblog/seo.py). SEO=False brings back the pages as they were before.
    SEO = os.getenv('SEO', 'True') == 'True'
    # Public address of the site for canonical links and the sitemap, e.g.
    # https://learn-catalan.com. Without it the address of the request is used.
    SITE_URL = os.getenv('SITE_URL')

    # Site language for visitors whose browser asks for none of the site's
    # languages (English, Ukrainian, French; Russian gets Ukrainian).
    DEFAULT_LANGUAGE = os.getenv('DEFAULT_LANGUAGE', 'en')

    # Dictionary words show their meanings one by one, each translated
    # (flaskblog/vocabulary/senses.py). SENSES=False shows one translation
    # line per language, as before; nothing in the database changes.
    SENSES = os.getenv('SENSES', 'True') == 'True'

    # Open API (/api/v1): requests a minute per client address; 0 = no limit.
    API_RATE_LIMIT = int(os.getenv('API_RATE_LIMIT', '120'))

    MAIL_SERVER = 'smtp-mail.outlook.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True

    #idk why, but import from .bash_profile , not from .profile
    MAIL_USERNAME = os.environ.get('EMAIL_USER') 
    MAIL_PASSWORD = os.environ.get('EMAIL_PASS')

class TestConfig(Config):
    """Configuration for the test suite.

    Uses an in-memory database so tests never touch the real one, and
    turns off CSRF and outgoing mail.
    """

    TESTING = True
    SECRET_KEY = 'test-secret-key'
    SQLALCHEMY_DATABASE_URI = os.getenv('TEST_DATABASE_URI', 'sqlite:///:memory:')
    WTF_CSRF_ENABLED = False
    MAIL_SUPPRESS_SEND = True
    SHOW_FAQ = True
    DESIGN = 'modern'
    SEO = True
    SENSES = True
    SITE_URL = None
    # The suite was written against the Ukrainian pages.
    DEFAULT_LANGUAGE = 'uk'
