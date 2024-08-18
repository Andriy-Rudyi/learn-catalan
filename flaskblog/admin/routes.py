from flask import Blueprint
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView

admin_bp = Blueprint('admin_routes', __name__)
admin = Admin(name='My Admin Panel', template_mode='bootstrap4')

def init_admin(app):
    # Import inside the function to avoid circular imports
    from flaskblog import db
    from flaskblog.models import User, Post, PostView

    admin.add_view(ModelView(User, db.session))
    admin.add_view(PostView(Post, db.session))
    admin.init_app(app)