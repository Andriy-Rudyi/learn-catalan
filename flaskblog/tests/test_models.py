# flaskblog/tests/test_models.py

import unittest
from flaskblog import create_app, db
from flaskblog.models import User

class ModelTests(unittest.TestCase):

    def setUp(self):
        self.app = create_app('TestConfig')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_user_model(self):
        user = User(username='testuser', email='test@example.com', password='password')
        db.session.add(user)
        db.session.commit()
        self.assertEqual(User.query.count(), 1)
        self.assertEqual(User.query.first().username, 'testuser')

if __name__ == '__main__':
    unittest.main()
