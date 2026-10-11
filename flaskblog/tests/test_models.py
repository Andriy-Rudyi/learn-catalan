# flaskblog/tests/test_models.py

import unittest

from flaskblog import db
from flaskblog.models import Comment, Post, User
from flaskblog.tests.helpers import AppTestCase


class ModelTests(AppTestCase):

    def test_user_model(self):
        self.create_user(username='testuser', email='test@example.com')
        self.assertEqual(User.query.count(), 1)
        self.assertEqual(User.query.first().username, 'testuser')

    def test_post_gets_a_slug_from_its_title(self):
        user = self.create_user()
        post = Post(title='Bon dia', content='Hola', author=user)
        db.session.add(post)
        db.session.commit()
        self.assertEqual('bon-dia', post.slug)

    def test_reset_token_round_trip(self):
        user = self.create_user()
        self.assertEqual(user, User.verify_reset_token(user.get_reset_token()))

    def test_invalid_reset_token(self):
        self.assertIsNone(User.verify_reset_token('not-a-token'))

    def test_deleting_a_user_deletes_their_posts_and_comments(self):
        user = self.create_user()
        post = Post(title='Lliçó', content='Hola', author=user)
        db.session.add(post)
        db.session.commit()
        db.session.add(Comment(text='Bé!', author=user, post_id=post.id))
        db.session.commit()

        db.session.delete(user)
        db.session.commit()
        self.assertEqual(0, Post.query.count())
        self.assertEqual(0, Comment.query.count())


if __name__ == '__main__':
    unittest.main()
