# flaskblog/tests/test_forms.py

import unittest

from werkzeug.datastructures import MultiDict

from flaskblog.tests.helpers import AppTestCase
from flaskblog.users.forms import RegistrationForm
from flaskblog.vocabulary.forms import UserWordForm, WordForm


class FormTests(AppTestCase):

    def test_registration_form(self):
        form = RegistrationForm(
            username='testuser',
            email='test@example.com',
            password='password',
            confirm_password='password',
        )
        self.assertTrue(form.validate())

    def test_registration_form_rejects_a_taken_username(self):
        self.create_user(username='taken', email='taken@example.com')
        form = RegistrationForm(
            username='taken',
            email='other@example.com',
            password='password',
            confirm_password='password',
        )
        self.assertFalse(form.validate())

    def test_word_form_requires_term_and_translation(self):
        self.assertFalse(WordForm(term='', translation='').validate())
        self.assertTrue(WordForm(term='poma', translation='яблуко').validate())

    def test_word_form_rejects_an_unknown_topic(self):
        # Choice validation applies to submitted data, so build the form
        # the way a request would.
        form = WordForm(
            formdata=MultiDict(
                {'term': 'poma', 'translation': 'яблуко', 'topic': 'no-such-topic'}
            )
        )
        self.assertFalse(form.validate())
        self.assertIn('topic', form.errors)

    def test_user_word_form(self):
        self.assertTrue(UserWordForm(term='poma', translation='яблуко').validate())
        self.assertFalse(UserWordForm(term='poma', translation='').validate())


if __name__ == '__main__':
    unittest.main()
