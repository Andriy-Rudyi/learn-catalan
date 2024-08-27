from flask import (Blueprint, abort, flash, redirect, render_template, request,
                   url_for)
from flask_login import current_user, login_required

from flaskblog import db
from flaskblog.models import Comment, Post
from flaskblog.posts.forms import PostForm
import re

posts = Blueprint('posts', __name__)


def generate_unique_slug(slug):
    """
    Generate a unique slug by appending a number to the end if it already exists.
    """
    original_slug = slug
    counter = 1

    # Check if the slug exists and keep incrementing the counter until a unique slug is found
    while Post.query.filter_by(slug=slug).first() is not None:
        slug = f"{original_slug}-{counter}"
        counter += 1

    return slug


@posts.route("/lesson/new", methods=['GET', 'POST'])
@login_required
def new_post():
    username = current_user.username
    if username == "Andriy":
        form = PostForm()
        if form.validate_on_submit():

            # Generate a slug from the title
            slug = re.sub(r'\W+', '-', form.title.data).lower()
            slug = generate_unique_slug(slug)

            post = Post(
                title=form.title.data,
                content=form.content.data,
                slug=slug, 
                author=current_user)
            
            db.session.add(post)
            db.session.commit()
            flash('Your post has been created!', 'success')
            return redirect(url_for('main.lessons'))
        return render_template('create_post.html', title='New Post',
                               form=form, legend='New Post')
    else:
        flash('You do not have permission to do this!', 'danger')
        return redirect(url_for('main.lessons'))


@posts.route("/lesson/<string:slug>")
def post(slug):
    post = Post.query.filter_by(slug=slug).first_or_404()
    return render_template('post.html', title=post.title, post=post)


@posts.route("/lesson/<string:slug>/update", methods=['GET', 'POST'])
@login_required
def update_post(slug):
    username = current_user.username
    if username == "Andriy":
        post = Post.query.filter_by(slug=slug).first_or_404()
        if post.author != current_user:
            abort(403)

        form = PostForm()
        if form.validate_on_submit():
            post.title = form.title.data
            post.content = form.content.data

            # post.slug = generate_unique_slug(re.sub(r'\W+', '-', form.title.data).lower())
            
            db.session.commit()
            flash('Your post has been updated!', 'success')
            return redirect(url_for('posts.post', slug=post.slug))
        
        elif request.method == 'GET':
            form.title.data = post.title
            form.content.data = post.content
        return render_template('create_post.html', title='Update Post',
                               form=form, legend='Update Post')
    else:
        flash('You do not have permission to do this!', 'danger')
        return redirect(url_for('main.lessons'))


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
        return redirect(url_for('main.lessons'))
    else:
        flash('You do not have permission to do this!', 'danger')
        return redirect(url_for('main.lessons'))


@posts.route("/create-comment/<string:slug>", methods=['POST'])
@login_required
def create_comments(slug):
    text = request.form.get('text')

    if not text:
        flash('Comment cannot be empty.', category='error')
    else:
        post = Post.query.filter_by(slug=slug).first_or_404()
        if post:
            comment = Comment(text=text, author=current_user, post_id=post.id)
            db.session.add(comment)
            db.session.commit()
        else:
            flash('Post does not exist.', category='error')

    return redirect(url_for('posts.post', slug=slug))


@posts.route("/delete-comment/<int:comment_id>")
@login_required
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    slug = comment.post.slug
    if not comment:
        flash('Comment does not exist.', category='error')
        return redirect(url_for('main.lessons'))
    elif comment.author.id != current_user.id and comment.post.author.id != current_user.id:
        flash('You do not have permission to delete this comment.', category='error')
    else:
        db.session.delete(comment)
        db.session.commit()

    return redirect(url_for('posts.post', slug=slug))
