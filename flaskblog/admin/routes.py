from flask import Blueprint
from flask_admin import Admin

from flaskblog.models import MyAdminIndexView

admin_bp = Blueprint('admin_routes', __name__)


def init_admin(app):
    """Attach the admin panel to *app*.

    The Admin object and its views are built per application: a single
    module-level instance accumulated views and tried to register its
    blueprints again whenever a second application was created, which
    made the admin panel unusable outside the first one.
    """
    # Imported inside the function to avoid circular imports
    from flaskblog import db
    from flaskblog.models import (Announcement, AnnouncementView, Comment,
                                  CommentView, GrammarUnit, GrammarUnitView,
                                  Post, PostView, Translator, TranslatorView,
                                  Update, UpdateView, User,
                                  UserView, UserWord, UserWordView, Word,
                                  WordTranslation, WordTranslationView, WordView)

    admin = Admin(
        name='My Admin Panel',
        index_view=MyAdminIndexView(),
        template_mode='bootstrap4',
    )

    admin.add_view(UserView(User, db.session))
    admin.add_view(PostView(Post, db.session))
    admin.add_view(CommentView(Comment, db.session))
    admin.add_view(UpdateView(Update, db.session))
    admin.add_view(AnnouncementView(Announcement, db.session))
    admin.add_view(GrammarUnitView(GrammarUnit, db.session))
    admin.add_view(WordView(Word, db.session))
    admin.add_view(WordTranslationView(WordTranslation, db.session))
    admin.add_view(UserWordView(UserWord, db.session))
    admin.add_view(TranslatorView(Translator, db.session))
    admin.init_app(app)
    return admin
