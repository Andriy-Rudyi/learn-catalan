# flaskblog/tests/test_forms.py

import unittest
from flaskblog import create_app, db
from flaskblog.users.forms import RegistrationForm

class FormTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing
        cls.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'  # Use an in-memory database for testing
        cls.app_context = cls.app.app_context()
        cls.app_context.push()
        db.create_all()  # Create all tables

    @classmethod
    def tearDownClass(cls):
        db.session.remove()
        db.drop_all()
        cls.app_context.pop()

    def test_registration_form(self):
        form = RegistrationForm(username='testuser', email='test@example.com', password='password', confirm_password='password')
        self.assertTrue(form.validate())

if __name__ == '__main__':
    unittest.main()


