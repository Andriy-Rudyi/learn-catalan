import os


class Config:
    # SECRET_KEY = os.environ.get('SECRET_KEY') 
    # SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI')
    SECRET_KEY = os.getenv('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_PUBLIC_URI')

    #DB_URL = 'postgresql+psycopg2://{user}:{pw}@{url}/{db}'.format(user=POSTGRES_USER, pw=POSTGRES_PW, url=POSTGRES_URL, db=POSTGRES_DB)
    #SQLALCHEMY_DATABASE_URI = DB_URL


    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True

    #idk why, but import from .bash_profile , not from .profile
    MAIL_USERNAME = os.environ.get('EMAIL_USER') 
    MAIL_PASSWORD = os.environ.get('EMAIL_PASS')

# class TestConfig(Config):
#     TESTING = True