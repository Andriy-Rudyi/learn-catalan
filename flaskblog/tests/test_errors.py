# flaskblog/tests/test_errors.py

import unittest
from flaskblog import create_app, db

class ErrorTests(unittest.TestCase):

    def setUp(self):
        self.app = create_app('TestConfig')
        self.client = self.app.test_client()
        with self.app.app_context():
            db.create_all()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_404_error(self):
        response = self.client.get('/nonexistent_page')
        self.assertEqual(response.status_code, 404)
        self.assertIn(b'Page Not Found', response.data)

if __name__ == '__main__':
    unittest.main()
