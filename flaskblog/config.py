import os


def database_url():
    """Database URL from the hosting environment.

    Railway exposes DATABASE_PUBLIC_URL; Render, Heroku and Fly use
    DATABASE_URL. Some of them still hand out the old ``postgres://``
    scheme, which SQLAlchemy no longer accepts.
    """
    url = os.getenv('DATABASE_PUBLIC_URL') or os.getenv('DATABASE_URL')
    if url and url.startswith('postgres://'):
        url = 'postgresql://' + url[len('postgres://'):]
    return url


class Config:
    # Local db (.bash_profile)
    # SECRET_KEY = os.environ.get('SECRET_KEY') 
    # SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI')

    # Production db
    SECRET_KEY = os.getenv('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = database_url()
    # Free hosted databases (Neon, Render) close idle connections; check each
    # pooled connection before use instead of failing the next request.
    SQLALCHEMY_ENGINE_OPTIONS = {'pool_pre_ping': True, 'pool_recycle': 280}

    #DB_URL = 'postgresql+psycopg2://{user}:{pw}@{url}/{db}'.format(user=POSTGRES_USER, pw=POSTGRES_PW, url=POSTGRES_URL, db=POSTGRES_DB)
    #SQLALCHEMY_DATABASE_URI = DB_URL


    # FAQ is hidden for now; set SHOW_FAQ=True to bring the page back.
    SHOW_FAQ = os.getenv('SHOW_FAQ') == 'True'

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
    SHOW_FAQ = False
