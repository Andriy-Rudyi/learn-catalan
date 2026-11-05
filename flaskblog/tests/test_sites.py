# flaskblog/tests/test_sites.py

import unittest

from flaskblog import create_app, db
from flaskblog.config import TestConfig
from flaskblog.tests.helpers import AppTestCase

BASE = 'langwave.test'


class DomainConfig(TestConfig):
    BASE_DOMAIN = BASE


class WithoutDomainTests(AppTestCase):
    """Without BASE_DOMAIN every host is the Catalan site, as before."""

    def test_any_host_is_the_catalan_site(self):
        for base_url in ('http://localhost', 'http://learn-catalan.onrender.com', 'http://' + BASE):
            response = self.client.get('/grammar', base_url=base_url)
            self.assertEqual(200, response.status_code, base_url)
        self.assertNotIn('LangWave', self.client.get('/', base_url='http://' + BASE).get_data(as_text=True))


class DomainTests(AppTestCase):

    def setUp(self):
        self.app = create_app(DomainConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.client = self.app.test_client()

    def get(self, host, path='/', **kwargs):
        return self.client.get(path, base_url='https://' + host, **kwargs)

    def test_root_is_the_language_picker(self):
        response = self.get(BASE)
        body = response.get_data(as_text=True)
        self.assertEqual(200, response.status_code)
        self.assertIn('LangWave', body)
        self.assertIn('href="https://catalan.{}/?lang=uk"'.format(BASE), body)
        self.assertIn('Català', body)
        # Registered but switched off: not shown.
        for slug in ('english', 'french', 'german'):
            self.assertNotIn('{}.{}'.format(slug, BASE), body)

    def test_picker_follows_the_interface_language(self):
        body = self.get(BASE, '/?lang=en').get_data(as_text=True)
        self.assertIn('Pick the language you want to learn', body)
        self.assertIn('href="https://catalan.{}/?lang=en"'.format(BASE), body)

    def test_root_pages_go_to_the_catalan_site(self):
        response = self.get(BASE, '/grammar?sort=topic')
        self.assertEqual(301, response.status_code)
        self.assertEqual('https://catalan.{}/grammar?sort=topic'.format(BASE), response.headers['Location'])

    def test_www_goes_to_the_root(self):
        response = self.get('www.' + BASE, '/dictionary')
        self.assertEqual(301, response.status_code)
        self.assertEqual('https://{}/dictionary'.format(BASE), response.headers['Location'])

    def test_catalan_site(self):
        response = self.get('catalan.' + BASE, '/grammar')
        self.assertEqual(200, response.status_code)
        self.assertIn('href="https://catalan.{}/grammar?lang=uk"'.format(BASE), response.get_data(as_text=True))

    def test_hidden_sites_are_not_found(self):
        for slug in ('english', 'french', 'german'):
            self.assertEqual(404, self.get('{}.{}'.format(slug, BASE)).status_code, slug)

    def test_unknown_subdomain_goes_to_the_picker(self):
        response = self.get('klingon.' + BASE, '/grammar')
        self.assertEqual(302, response.status_code)
        self.assertEqual('https://{}/'.format(BASE), response.headers['Location'])

    def test_old_address_goes_to_the_catalan_site(self):
        response = self.get('learn-catalan.onrender.com', '/conjugator?verb=anar')
        self.assertEqual(301, response.status_code)
        self.assertEqual('https://catalan.{}/conjugator?verb=anar'.format(BASE), response.headers['Location'])
        post = self.client.post('/login', base_url='https://learn-catalan.onrender.com')
        self.assertEqual(308, post.status_code)

    def test_localhost_is_served_for_development(self):
        self.assertEqual(200, self.client.get('/grammar', base_url='http://localhost:5000').status_code)

    def test_cookies_are_shared_by_all_sites(self):
        response = self.get('catalan.' + BASE, '/?lang=en')
        self.assertIn('Domain={}'.format(BASE), response.headers['Set-Cookie'])
        self.assertEqual(BASE, self.app.config['REMEMBER_COOKIE_DOMAIN'])
        user = self.create_user()
        response = self.client.post('/login', data={'email': user.email, 'password': 'secret'},
                                    base_url='https://catalan.' + BASE)
        cookies = response.headers.getlist('Set-Cookie')
        session = [c for c in cookies if c.startswith('session=')]
        self.assertTrue(session)
        self.assertIn('Domain={}'.format(BASE), session[0])
        # The same login is seen on the root domain's picker and other sites.
        self.assertEqual(200, self.get('catalan.' + BASE, '/account').status_code)

    def test_root_robots_and_sitemap(self):
        robots = self.get(BASE, '/robots.txt').get_data(as_text=True)
        self.assertIn('Sitemap: https://{}/sitemap.xml'.format(BASE), robots)
        sitemap = self.get(BASE, '/sitemap.xml').get_data(as_text=True)
        self.assertIn('<loc>https://{}/</loc>'.format(BASE), sitemap)
        self.assertIn('<loc>https://catalan.{}/</loc>'.format(BASE), sitemap)
        self.assertNotIn('english.', sitemap)
        catalan = self.get('catalan.' + BASE, '/robots.txt').get_data(as_text=True)
        self.assertIn('Sitemap: https://catalan.{}/sitemap.xml'.format(BASE), catalan)

    def test_static_files_on_the_root(self):
        self.assertEqual(200, self.get(BASE, '/static/main.css').status_code)
        self.assertEqual(200, self.get(BASE, '/favicon.ico').status_code)


if __name__ == '__main__':
    unittest.main()
