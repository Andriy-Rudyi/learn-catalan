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

    def test_faq_is_hidden_by_default(self):
        self.assertEqual(self.client.get('/faq').status_code, 404)
        self.assertNotIn('FAQ', self._navbar('/'))

    def test_faq_can_be_switched_back_on(self):
        self.app.config['SHOW_FAQ'] = True
        self.assertEqual(self.client.get('/faq').status_code, 200)
        self.assertIn('FAQ', self._navbar('/'))

    def _navbar(self, url):
        body = self.client.get(url).data.decode()
        return body[body.index('<nav'):body.index('</nav>')]

    def test_menu_has_the_current_sections_only(self):
        for url in ('/', '/conjugator'):
            navbar = self._navbar(url)
            for present in ('Дієвідміна', 'Словник', 'Граматика'):
                self.assertIn(present, navbar, url)
            for absent in ('Уроки', 'Оголошення', 'Оновлення', 'FAQ'):
                self.assertNotIn(absent, navbar, url)

    def test_menu_order_is_grammar_dictionary_conjugator(self):
        navbar = self._navbar('/')
        positions = [navbar.index(name) for name in ('Граматика', 'Словник', 'Дієвідміна')]
        self.assertEqual(sorted(positions), positions)

    def test_current_section_is_highlighted(self):
        navbar = self._navbar('/grammar')
        grammar_link = navbar[:navbar.index('Граматика')]
        self.assertIn('active', grammar_link[grammar_link.rindex('<a'):])
        conjugator = self._navbar('/conjugator')
        self.assertNotIn('active', conjugator[:conjugator.index('Словник')].split('<a')[-1])

    def test_theme_toggle_and_mobile_viewport(self):
        body = self.client.get('/').data.decode()
        self.assertIn('id="themeToggle"', body)
        self.assertIn('data-bs-theme', body)
        self.assertIn('name="viewport"', body)
        self.assertIn('bootstrap.bundle.min.js', body)

    def test_home_page_starts_with_the_grammar_course(self):
        self.assertIn('/grammar', self.client.get('/').data.decode())

    def test_login_lands_on_the_home_page(self):
        user = self.create_user()
        response = self.client.post(
            '/login', data={'email': user.email, 'password': 'secret'}
        )
        self.assertEqual(302, response.status_code)
        self.assertTrue(response.headers['Location'].endswith('/home'))

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
