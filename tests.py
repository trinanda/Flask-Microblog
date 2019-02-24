from datetime import datetime, timedelta
import unittest
from app import create_app, db
from app.models import User, Post
from config import Config


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite://'


class UserModelCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_password_hashing(self):
        u = User(username='tri')
        u.set_password('cat')
        self.assertFalse(u.check_password('dog'))
        self.assertTrue(u.check_password('cat'))

    def test_avatar(self):
        u = User(username='sri', email='sri@example.com')
        self.assertEqual(u.avatar(128), ('https://www.gravatar.com/avatar/'
                                         '1439a2054d7d9d044132f9e145704079'
                                         '?d=identicon&s=128'))

    def test_follow(self):
        u1 = User(username='tri', email='tri@example.com')
        u2 = User(username='sri', email='sri@example.com')
        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()
        self.assertEqual(u1.followed.all(), [])
        self.assertEqual(u1.followers.all(), [])

        u1.follow(u2)
        db.session.commit()
        self.assertTrue(u1.is_following(u2))
        self.assertEqual(u1.followed.count(), 1)
        self.assertEqual(u1.followed.first().username, 'sri')
        self.assertEqual(u2.followers.count(), 1)
        self.assertEqual(u2.followers.first().username, 'tri')

        u1.unfollow(u2)
        db.session.commit()
        self.assertFalse(u1.is_following(u2))
        self.assertEqual(u1.followed.count(), 0)
        self.assertEqual(u2.followers.count(), 0)

    def test_follow_posts(self):
        # create four users
        u1 = User(username='tri', email='tri@example.com')
        u2 = User(username='sri', email='sri@example.com')
        u3 = User(username='ari', email='ari@example.com')
        u4 = User(username='fuad', email='fuad@example.com')
        db.session.add_all([u1, u2, u3, u4])

        # create four posts
        now = datetime.utcnow()
        p1 = Post(body="post from tri", author=u1, timestamp=now + timedelta(seconds=1))
        p2 = Post(body="post from sri", author=u2, timestamp=now + timedelta(seconds=4))
        p3 = Post(body="post from ari", author=u3, timestamp=now + timedelta(seconds=3))
        p4 = Post(body="post from fuad", author=u4, timestamp=now + timedelta(seconds=2))
        db.session.add_all([p1, p2, p3, p4])
        db.session.commit()

        # setup the followers
        u1.follow(u2)   # tri follows sri
        u1.follow(u3)   # tri follows ari
        u2.follow(u1)   # sri follows tri
        u4.follow(u3)   # fuad follows ari
        db.session.commit()

        # check the followed posts of each user
        f1 = u1.followed_posts().all()
        f2 = u2.followed_posts().all()
        f3 = u3.followed_posts().all()
        f4 = u4.followed_posts().all()
        self.assertEqual(f1, [p2, p3, p1])
        self.assertEqual(f2, [p2, p1])
        self.assertEqual(f3, [p3])
        self.assertEqual(f4, [p3, p4])


if __name__ == "__main__":
    unittest.main(verbosity=2)
