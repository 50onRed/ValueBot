import unittest
from flask.ext.testing import TestCase
from app import create_app
from slack import Slack, SlackResponse, SlackMessage, SlackPost
from value_bot import ValueBot
from db.db import db
from db.post import Post

class DummySlack(Slack):
    def __init__(self):
        return

    def user_name_of_user_id(self, user_id):
        return user_id

    def send_message(self, message):
        print "Sending message: {}".format(message)

class ValueBotTests(TestCase):
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    TESTING = True

    def create_app(self):
        return create_app()

    def setUp(self):
        db.create_all()

        slack = DummySlack()

        self.value_bot = ValueBot(
            slack=slack,
            admins={"testadmin"},
            hashtags={
                "testvalue": {"#testvalue"}
            }
        )

    def tearDown(self):
        db.session.remove()
        db.drop_all()

if __name__ == '__main__':
    unittest.main()