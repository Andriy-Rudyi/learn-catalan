import os


class Config:
    # SECRET_KEY = os.environ.get('SECRET_KEY') 
    # SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI')
    SECRET_KEY = os.getenv('SECRET_KEY')
    # SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL') 
    # SQLALCHEMY_DATABASE_URI = os.getenv('SQLALCHEMY_DATABASE_URI')
    # SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_PUBLIC_URI')
    
    #POSTGRES_URL = os.getenv('DATABASE_URL')
    POSTGRES_URL = 'viaduct.proxy.rlwy.net:29772'
    POSTGRES_USER = os.getenv('PGUSER')
    POSTGRES_PW = os.getenv('PGPASSWORD')
    #POSTGRES_PW = 'RJrEpGqHzyAKKrxAeIYugcyFeSTeAxJy'
    POSTGRES_DB = os.getenv('POSTGRES_DB')
    #DB_URL = 'postgresql+psycopg2://{user}:{pw}@{url}/{db}'.format(user=POSTGRES_USER, pw=POSTGRES_PW, url=POSTGRES_URL, db=POSTGRES_DB)
    DB_URL = 'postgresql://postgres:RJrEpGqHzyAKKrxAeIYugcyFeSTeAxJy@viaduct.proxy.rlwy.net:29772/railway'
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')


    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True

    #idk why, but import from .bash_profile , not from .profile
    MAIL_USERNAME = os.environ.get('EMAIL_USER') 
    MAIL_PASSWORD = os.environ.get('EMAIL_PASS')

# class TestConfig(Config):
#     TESTING = True