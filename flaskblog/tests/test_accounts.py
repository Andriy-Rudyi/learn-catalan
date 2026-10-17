# flaskblog/tests/test_accounts.py

import unittest

from flaskblog.models import User
from flaskblog.permissions import admin_username
from flaskblog.tests.helpers import AppTestCase


class EditorOnlyTests(AppTestCase):
    """Only the site editor sees "New lesson" and may add lessons."""

    def _menu(self):
        body = self.client.get('/').data.decode()
        return body[body.index('<nav'):body.index('</nav>')]

    def test_visitors_and_other_users_have_no_new_lesson_button(self):
        self.assertNotIn('/lesson/new', self._menu())
        self.login_as(self.create_user('someone'))
        self.assertNotIn('/lesson/new', self._menu())
        response = self.client.get('/lesson/new')
        self.assertEqual(302, response.status_code)

    def test_a_similar_name_is_not_the_editor(self):
        self.login_as(self.create_user(admin_username().lower()))
        self.assertNotIn('/lesson/new', self._menu())

    def test_the_editor_has_the_button(self):
        self.login_as(self.create_admin())
        self.assertIn('/lesson/new', self._menu())
        self.assertEqual(200, self.client.get('/lesson/new').status_code)

    def test_the_editor_cannot_give_up_the_name(self):
        admin = self.create_admin()
        self.login_as(admin)
        self.client.post('/account', data={'username': 'renamed', 'email': admin.email})
        self.assertEqual(admin_username(), User.query.get(admin.id).username)

    def test_nobody_else_can_take_the_editor_name(self):
        user = self.create_user('someone')
        self.login_as(user)
        for name in (admin_username(), admin_username().upper()):
            self.client.post('/account', data={'username': name, 'email': user.email})
            self.assertEqual('someone', User.query.get(user.id).username)


class AccountPagesTests(AppTestCase):

    def test_login_and_signup_pages(self):
        for url in ('/login', '/register', '/reset_password'):
            body = self.client.get(url).data.decode()
            self.assertIn('auth-card', body, url)
        self.assertIn('autocomplete="current-password"', self.client.get('/login').data.decode())

    def test_account_shows_word_counts(self):
        self.login_as(self.create_user())
        body = self.client.get('/account').data.decode()
        self.assertIn('stat-tile', body)
        self.assertIn('/my-dictionary?status=known', body)

    def test_empty_personal_dictionary(self):
        self.login_as(self.create_user())
        body = self.client.get('/my-dictionary').data.decode()
        self.assertIn('empty-state', body)


if __name__ == '__main__':
    unittest.main()
