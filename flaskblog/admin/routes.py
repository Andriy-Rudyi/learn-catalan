from flask import Blueprint
from flask_admin import Admin
# from flask_admin.contrib.sqla import ModelView
from flaskblog.models import MyAdminIndexView

admin_bp = Blueprint('admin_routes', __name__)
admin = Admin(name='My Admin Panel', index_view=MyAdminIndexView(), template_mode='bootstrap4')

def init_admin(app):
    # Import inside the function to avoid circular imports
    from flaskblog import db
    from flaskblog.models import User, Post, UserView, PostView

    admin.add_view(UserView(User, db.session))
    admin.add_view(PostView(Post, db.session))
    admin.init_app(app)