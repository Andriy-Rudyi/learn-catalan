import json
from verbecc import Conjugator
from verbecc.exceptions import VerbNotFoundError
from flask import render_template, request, Blueprint
from flaskblog.models import Post, Update, Announcement
from flaskblog.main.forms import SearchForm
from flaskblog.posts.forms import PostForm

main = Blueprint('main', __name__)


def printjson(c):
    print(json.dumps(c, indent=4, ensure_ascii=False))

@main.route("/")
@main.route("/home")
def home():
    ProjectName = 'LearnCatalan'
    return render_template('home.html', ProjectName=ProjectName)

@main.route("/lessons")
def lessons():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.date_posted).paginate(page=page, per_page=6)
    #posts = Post.query.paginate(page=page, per_page=5)
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

def format_conjugation_result(conjugation_result):
    # Create a new dictionary to hold modified results
    formatted_result = {}
    
    # Copy the verb data as is
    formatted_result['verb'] = conjugation_result.get('verb', {})

    # Process moods and tenses
    formatted_result['moods'] = {}
    for mood, tenses in conjugation_result.get('moods', {}).items():
        # Rename 'particip' mood to 'participi' if applicable
        new_mood = 'participi' if mood == 'particip' else mood
        formatted_result['moods'][new_mood] = {}
        
        for tense, forms in tenses.items():
            # Rename 'particip' tense to 'participi'
            new_tense = 'participi' if tense == 'particip' else tense
            formatted_result['moods'][new_mood][new_tense] = forms

    return formatted_result



@main.route('/conjugator', methods=['GET', 'POST'])
def conjugator():
    conjugation_result = None
    verb = request.form.get('verb')
    language = 'ca'  # Default to Catalan if not specified

    if request.method == 'POST':
        if verb:
            try:
                # Initialize Conjugator with the specified language
                cg = Conjugator(lang=language)
                conjugation_result = cg.conjugate(verb)
                conjugation_result = format_conjugation_result(conjugation_result)

                # Check if the result indicates an unknown verb
                if conjugation_result.get('verb') is None or conjugation_result['verb'].get('infinitive') == '':
                    conjugation_result = {'error': 'Unknown verb. Predicted conjugation: .'}
            except VerbNotFoundError:
                conjugation_result = {'error': 'Unknown verb. Predicted conjugation: .'}
            except Exception as e:
                # Handle any unexpected errors
                conjugation_result = {'error': f'An error occurred: {str(e)}'}

    return render_template('conjugator.html', verb=verb, conjugation_result=conjugation_result, language=language)




# @main.route("/conjugator")
# def conjugator():
#     return render_template('conjugator.html', title = 'Conjugator')

# @main.route("/conjugator/<str:verb>")
# def conjugate(verb):
#     cg = Conjugator(lang='ca')
#     cg.conjugate(verb)
#     return render_template('conjugator.html', title='Conjugator ()', verb=verb)


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