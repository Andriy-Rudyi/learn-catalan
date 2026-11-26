# flaskblog/tests/test_security.py

import unittest

from flaskblog import security
from flaskblog.tests.helpers import AppTestCase


class HeaderTests(AppTestCase):

    def test_every_page_has_the_security_headers(self):
        for url in ('/', '/grammar', '/dictionary', '/ukrainian/', '/api/v1/', '/no-such-page'):
            headers = self.client.get(url).headers
            self.assertEqual('nosniff', headers['X-Content-Type-Options'], url)
            self.assertEqual('SAMEORIGIN', headers['X-Frame-Options'], url)
            self.assertEqual('strict-origin-when-cross-origin', headers['Referrer-Policy'], url)
            self.assertIn("frame-ancestors 'self'", headers['Content-Security-Policy'], url)
            self.assertIn('microphone=(self)', headers['Permissions-Policy'], url)

    def test_hsts_only_over_https(self):
        self.assertNotIn('Strict-Transport-Security', self.client.get('/').headers)
        headers = self.client.get('/', headers={'X-Forwarded-Proto': 'https'}).headers
        self.assertIn('max-age=31536000', headers['Strict-Transport-Security'])

    def test_cookies(self):
        self.assertTrue(self.app.config['SESSION_COOKIE_HTTPONLY'])
        self.assertEqual('Lax', self.app.config['SESSION_COOKIE_SAMESITE'])
        self.assertEqual('Lax', self.app.config['REMEMBER_COOKIE_SAMESITE'])
        self.assertFalse(self.app.config.get('SESSION_COOKIE_SECURE'))  # not hosted
        response = self.client.get('/?lang=en')
        self.assertIn('SameSite=Lax', ' '.join(response.headers.getlist('Set-Cookie')) or 'SameSite=Lax')


class LoginAttemptTests(AppTestCase):

    def setUp(self):
        super().setUp()
        self.user = self.create_user()

    def post(self, password):
        return self.client.post('/login', data={'email': self.user.email, 'password': password})

    def test_blocked_after_five_failures(self):
        for _ in range(5):
            self.assertEqual(200, self.post('wrong').status_code)
        response = self.post('secret')  # even the right password waits
        self.assertEqual(429, response.status_code)
        self.assertIn('Забагато невдалих спроб', response.get_data(as_text=True))

    def test_success_resets_the_count(self):
        for _ in range(4):
            self.post('wrong')
        self.assertEqual(302, self.post('secret').status_code)
        self.client.get('/logout')
        for _ in range(4):
            self.assertEqual(200, self.post('wrong').status_code)

    def test_window(self):
        self.app.config['LOGIN_WINDOW'] = 0
        for _ in range(6):
            self.post('wrong')
        self.assertEqual(302, self.post('secret').status_code)

    def test_next_stays_on_the_site(self):
        response = self.client.post('/login?next=https://evil.example/x',
                                    data={'email': self.user.email, 'password': 'secret'})
        self.assertEqual(302, response.status_code)
        self.assertNotIn('evil.example', response.headers['Location'])
        self.client.get('/logout')
        response = self.client.post('/login?next=/grammar',
                                    data={'email': self.user.email, 'password': 'secret'})
        self.assertTrue(response.headers['Location'].endswith('/grammar'))


class SafeNextTests(unittest.TestCase):

    def test_safe_next(self):
        self.assertEqual('/grammar?x=1', security.safe_next('/grammar?x=1'))
        for bad in ('https://evil.example', '//evil.example', '/\\evil.example', 'javascript:alert(1)',
                    'evil.example', '', None):
            self.assertIsNone(security.safe_next(bad), bad)


if __name__ == '__main__':
    unittest.main()
