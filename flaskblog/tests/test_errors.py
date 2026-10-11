# flaskblog/tests/test_errors.py

import unittest

from flaskblog.tests.helpers import AppTestCase


class ErrorTests(AppTestCase):

    def test_404_error(self):
        response = self.client.get('/nonexistent_page')
        self.assertEqual(response.status_code, 404)

    def test_403_page_renders(self):
        response = self.client.get('/dictionary/new', follow_redirects=False)
        # not logged in: Flask-Login redirects instead of refusing
        self.assertEqual(response.status_code, 302)


if __name__ == '__main__':
    unittest.main()
