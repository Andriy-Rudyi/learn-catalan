from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_mail import Mail
from flask_ckeditor import CKEditor
from flaskblog.config import Config
from flask_migrate import Migrate




db = SQLAlchemy()
#app._context().push()
bcrypt = Bcrypt()
login_manager = LoginManager()
login_manager.login_view = 'users.login'
login_manager.login_message_category = 'info'

mail = Mail()
ckeditor = CKEditor()
migrate = Migrate()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    #app._context().push()
    bcrypt.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    ckeditor.init_app(app)
    migrate.init_app(app, db)
    
    from flaskblog.admin.routes import admin_bp, init_admin
    init_admin(app)
    # with app.app_context():
    #     # Create database tables if they do not exist
    #     db.create_all()

    from flaskblog.users.routes import users
    from flaskblog.posts.routes import posts
    from flaskblog.main.routes import main
    from flaskblog.errors.handler import errors
    from flaskblog.grammar.routes import grammar
    from flaskblog.phonetics.routes import phonetics
    from flaskblog.vocabulary.routes import vocabulary
    app.register_blueprint(users)
    app.register_blueprint(posts)
    app.register_blueprint(main)
    app.register_blueprint(errors)
    app.register_blueprint(admin_bp)
    app.register_blueprint(vocabulary)
    app.register_blueprint(grammar)
    app.register_blueprint(phonetics)

    from flaskblog.conjugation.cli import conjugation_cli
    from flaskblog.grammar.cli import grammar_cli
    from flaskblog.vocabulary.cli import vocabulary_cli
    app.cli.add_command(conjugation_cli)
    app.cli.add_command(grammar_cli)
    app.cli.add_command(vocabulary_cli)

    return app