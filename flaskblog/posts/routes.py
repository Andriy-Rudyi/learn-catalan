from flask import (render_template, url_for, flash,
                   redirect, request, abort, Blueprint)
from flask_login import current_user, login_required
from flaskblog import db
from flaskblog.models import Post, Comment
from flaskblog.posts.forms import PostForm

posts = Blueprint('posts', __name__)


@posts.route("/lesson/new", methods=['GET', 'POST'])
@login_required
def new_post():
    username = current_user.username
    if username == "Andriy":
        form = PostForm()
        if form.validate_on_submit():
            post = Post(title=form.title.data, content = form.content.data, author=current_user)
            db.session.add(post)
            db.session.commit()
            flash('Your post has been created!', 'success')
            return redirect(url_for('main.home'))
        return render_template('create_post.html', title='New Post', 
                            form=form, legend='New Post')
    else:
        flash('You do not have permission to do this!', 'danger')
        return redirect(url_for('main.home'))

@posts.route("/lesson/<int:post_id>")
def post(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template('post.html', title=post.title, post=post)


@posts.route("/lesson/<int:post_id>/update", methods=['GET', 'POST'])
@login_required
def update_post(post_id):
    username = current_user.username
    if username == "Andriy":
        post = Post.query.get_or_404(post_id)
        if post.author != current_user:
            abort(403)
        form = PostForm()
        if form.validate_on_submit():
            post.title = form.title.data
            post.content = form.content.data
            db.session.commit()
            flash('Your post has been updated!', 'success')
            return redirect(url_for('posts.post', post_id=post.id))
        elif request.method == 'GET':
            form.title.data = post.title
            form.content.data = post.content
        return render_template('create_post.html', title='Update Post',
                                form=form, legend='Update Post')
    else:
        flash('You do not have permission to do this!', 'danger')
        return redirect(url_for('main.home'))


@posts.route("/lesson/<int:post_id>/delete", methods=['POST'])
@login_required
def delete_post(post_id):
    username = current_user.username
    if username == "Andriy":    
        post = Post.query.get_or_404(post_id)
        if post.author != current_user:
            abort(403)
        db.session.delete(post)
        db.session.commit()
        flash('Your post has been deleted!', 'success')
        return redirect(url_for('main.home'))
    else:
        flash('You do not have permission to do this!', 'danger')
        return redirect(url_for('main.home'))
    
@posts.route("/create-comment/<int:post_id>", methods=['POST'])
@login_required
def create_comments(post_id):
    text = request.form.get('text')

    if not text:
        flash('Comment cannot be empty.', category='error')
    else:
        post = Post.query.get_or_404(post_id)
        if post:
            comment = Comment(text=text, author=current_user, post_id=post.id)
            db.session.add(comment)
            db.session.commit()
        else:
            flash('Post does not exist.', category='error')
        
    
    return redirect(url_for('posts.post', post_id=post_id))


@posts.route("/delete-comment/<int:comment_id>")
@login_required
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    post_id = comment.post.id
    if not comment:
        flash('Comment does not exist.', category='error')
        return redirect(url_for('main.home'))
    elif comment.author.id != current_user.id and comment.post.author.id != current_user.id:
        flash('You do not have permission to delete this comment.', category='error')
    else:
        db.session.delete(comment)
        db.session.commit()

    return redirect(url_for('posts.post', post_id=post_id))