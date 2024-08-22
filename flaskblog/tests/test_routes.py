# flaskblog/tests/test_routes.py

import unittest

from flaskblog import create_app, db
from flaskblog.models import Post, User


class RouteTests(unittest.TestCase):

    def setUp(self):
        self.app = create_app('TestConfig')
        self.client = self.app.test_client()
        with self.app.app_context():
            db.create_all()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_lessons_page(self):
        response = self.client.get('/lessons')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Learn Catalan', response.data)

    def test_about_page(self):
        response = self.client.get('/about')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'About Page', response.data)


if __name__ == '__main__':
    unittest.main()
