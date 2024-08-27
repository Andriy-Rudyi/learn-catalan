from flask import render_template, request, Blueprint
from flaskblog.models import Post, Update, Announcement
from flaskblog.main.forms import SearchForm
from flaskblog.posts.forms import PostForm

main = Blueprint('main', __name__)


@main.route("/")
@main.route("/home")
def home():
    ProjectName = 'LearnCatalan'
    return render_template('home.html', ProjectName=ProjectName)

@main.route("/lessons")
def lessons():
    page = request.args.get('page', 1, type=int)
    #posts = Post.query.order_by(Post.date_posted.desc()).paginate(page=page, per_page=5)
    posts = Post.query.paginate(page=page, per_page=5)
    return render_template('lessons.html', title='Уроки', posts=posts)


@main.route("/faq")
def faq():
    ProjectName = 'LearnCatalan'
    return render_template('faq.html', title='FAQ', ProjectName=ProjectName)

@main.route("/announcements")
def announcements():
    announcements = Announcement.query.order_by(Announcement.date_posted.desc())
    return render_template('announcements.html', announcements=announcements, title='Announcements')

@main.route("/updates")
def updates():
    updates = Update.query.order_by(Update.date_posted.desc())
    return render_template('updates.html', updates=updates)

# # Pass Stuff To Navbar
# @main.context_processor
# def base():
# 	form = SearchForm()
# 	return dict(form=form)


# @main.route("/search", methods=['POST'])
# def search():
#     form = SearchForm()
#     posts = Post.query.get_or_404()
#     if form.validate_on_submit():
#         # Get data from submitted form
#         posts.searched = form.searched.data
#         # Query the Database
#         posts = posts.filter(Post.content.like('%' + posts.searched + '%'))
#         posts = posts.order_by(Post.title).all()    
            
#     return render_template("search.html", form=form, searched = posts.searched, posts = posts)