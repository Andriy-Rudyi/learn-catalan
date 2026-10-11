# flaskblog/tests/test_routes.py

import unittest

from flaskblog import db
from flaskblog.models import Post
from flaskblog.tests.helpers import AppTestCase


class RouteTests(AppTestCase):

    def test_home_page(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Learn Catalan', response.data.decode())

    def test_lessons_page(self):
        response = self.client.get('/lessons')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Learn Catalan', response.data.decode())

    def test_faq_page(self):
        self.assertEqual(self.client.get('/faq').status_code, 200)

    def test_conjugator_page(self):
        self.assertEqual(self.client.get('/conjugator').status_code, 200)

    def test_dictionary_page(self):
        self.assertEqual(self.client.get('/dictionary').status_code, 200)

    def test_lesson_page_shows_a_post(self):
        user = self.create_user()
        post = Post(title='Primera lliçó', content='Hola!', author=user)
        db.session.add(post)
        db.session.commit()
        response = self.client.get('/lesson/{}'.format(post.slug))
        self.assertEqual(response.status_code, 200)
        self.assertIn('Primera lli', response.data.decode())

    def test_login_required_pages_redirect(self):
        for url in ('/account', '/lesson/new', '/my-dictionary'):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302, url)
            self.assertIn('/login', response.headers['Location'], url)


if __name__ == '__main__':
    unittest.main()
