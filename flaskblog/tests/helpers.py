"""Shared setup for the test suite."""

import unittest

from flaskblog import bcrypt, create_app, db
from flaskblog.config import TestConfig
from flaskblog.models import User
from flaskblog.permissions import admin_username


class AppTestCase(unittest.TestCase):
    """A test case with an application context and an empty database."""

    def setUp(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    # -- helpers -------------------------------------------------------
    def create_user(self, username='tester', email=None, password='secret'):
        user = User(
            username=username,
            email=email or '{}@example.com'.format(username),
            password=bcrypt.generate_password_hash(password).decode('utf-8'),
        )
        db.session.add(user)
        db.session.commit()
        return user

    def create_admin(self, password='secret'):
        return self.create_user(username=admin_username(), password=password)

    def login(self, email, password='secret'):
        return self.client.post(
            '/login',
            data={'email': email, 'password': password},
            follow_redirects=True,
        )

    def login_as(self, user, password='secret'):
        return self.login(user.email, password)
