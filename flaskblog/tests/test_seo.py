# flaskblog/tests/test_seo.py

import json
import re
import unittest

from flaskblog import db
from flaskblog.grammar import service as grammar_service
from flaskblog.models import GrammarUnit, Word
from flaskblog.tests.helpers import AppTestCase
from flaskblog.vocabulary import service as vocabulary_service


class SeoTests(AppTestCase):

    def setUp(self):
        super().setUp()
        grammar_service.seed()
        vocabulary_service.import_seed()
        db.session.commit()

    def _head(self, url):
        body = self.client.get(url).data.decode()
        return body[:body.index('</head>')]

    def test_title_description_and_previews(self):
        head = self._head('/grammar')
        self.assertIn('<title>Граматика — Learn Catalan</title>', head)
        self.assertRegex(head, r'<meta name="description" content="[^"]{40,}">')
        self.assertIn('property="og:title"', head)
        self.assertIn('og-image.png', head)
        self.assertIn('<title>anar: дієвідміна дієслова — Learn Catalan</title>', self._head('/conjugator?verb=anar'))

    def test_canonical_and_language_versions(self):
        head = self._head('/grammar?sort=topic')
        self.assertIn('<link rel="canonical" href="http://localhost/grammar?lang=uk">', head)
        self.assertIn('hreflang="en" href="http://localhost/grammar?lang=en"', head)
        self.assertIn('hreflang="x-default" href="http://localhost/grammar"', head)
        self.assertIn('href="http://localhost/grammar?lang=en"', self._head('/grammar?lang=en'))

    def test_site_url_setting(self):
        self.app.config['SITE_URL'] = 'https://learn-catalan.com/'
        self.assertIn('href="https://learn-catalan.com/phonetics?lang=uk"', self._head('/phonetics'))

    def test_private_pages_and_search_results_are_not_indexed(self):
        for url in ('/login', '/register', '/dictionary?q=casa', '/no-such-page'):
            self.assertIn('name="robots" content="noindex', self._head(url), url)
        for url in ('/', '/grammar', '/dictionary', '/faq', '/conjugator?verb=anar'):
            self.assertNotIn('name="robots"', self._head(url), url)
        self.assertIn('noindex', self._head('/conjugator?verb=xyzzyq'))

    def test_unit_by_number_points_to_the_unit_page(self):
        unit = GrammarUnit.query.filter_by(number=7).first()
        head = self._head('/grammar/unit/7')
        self.assertIn('rel="canonical" href="http://localhost/grammar/{}?lang=uk"'.format(unit.slug), head)

    def test_structured_data(self):
        home = self._head('/')
        data = json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>', home).group(1))
        self.assertEqual('WebSite', data['@type'])
        faq = self._head('/faq')
        data = json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>', faq).group(1))
        self.assertEqual('FAQPage', data['@type'])
        self.assertTrue(any('звук' in q['name'] for q in data['mainEntity']))

    def test_robots_txt_and_sitemap(self):
        robots = self.client.get('/robots.txt').data.decode()
        self.assertIn('Sitemap: http://localhost/sitemap.xml', robots)
        self.assertIn('Disallow: /account', robots)
        response = self.client.get('/sitemap.xml')
        self.assertEqual('application/xml', response.mimetype)
        sitemap = response.data.decode()
        word = Word.query.filter_by(term='anar').first()
        self.assertIn('<loc>http://localhost/dictionary/{}?lang=uk</loc>'.format(word.slug), sitemap)
        self.assertIn('<loc>http://localhost/conjugator?verb=anar&amp;lang=en</loc>', sitemap)
        self.assertIn('hreflang="x-default"', sitemap)
        self.assertNotIn('/login', sitemap)

    def test_everything_can_be_switched_off(self):
        self.app.config['SEO'] = False
        head = self._head('/grammar')
        self.assertIn('<title>Learn Catalan - Граматика</title>', head)
        for absent in ('rel="canonical"', 'og:title', 'name="description"', 'hreflang'):
            self.assertNotIn(absent, head)
        self.assertEqual(404, self.client.get('/robots.txt').status_code)
        self.assertEqual(404, self.client.get('/sitemap.xml').status_code)


if __name__ == '__main__':
    unittest.main()
