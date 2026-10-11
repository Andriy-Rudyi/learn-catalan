# flaskblog/tests/test_models.py

import os
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


class DatabaseUrlTests(unittest.TestCase):

    def _url(self, **env):
        from unittest import mock
        from flaskblog.config import database_url
        keys = ('DATABASE_PUBLIC_URL', 'DATABASE_URL')
        clean = {k: v for k, v in env.items() if k in keys}
        with mock.patch.dict('os.environ', clean, clear=False):
            for key in keys:
                if key not in clean:
                    os.environ.pop(key, None)
            return database_url()

    def test_public_url_wins(self):
        self.assertEqual('sqlite:///a.db', self._url(DATABASE_PUBLIC_URL='sqlite:///a.db',
                                                     DATABASE_URL='sqlite:///b.db'))

    def test_falls_back_to_database_url(self):
        self.assertEqual('sqlite:///b.db', self._url(DATABASE_URL='sqlite:///b.db'))

    def test_old_postgres_scheme_is_fixed(self):
        self.assertEqual('postgresql://u:p@h/db', self._url(DATABASE_URL='postgres://u:p@h/db'))
