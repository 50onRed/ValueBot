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

    def get_user_name(self, user_id):
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

    def test_valid_syntax(self):
        valids = [
            'valuebot help',
            'valuebot man',
            'valuebot #testvalue <@someone>',
            'valuebot <@somebody> #testvalue',
            'valuebot list all',
            'valuebot list all today',
            'valuebot list all july',
            'valuebot list all july 2014'
            'valuebot list testvalue',
            'valuebot list testvalue today',
            'valuebot list testvalue july',
            'valuebot list testvalue july 2014',
            'valuebot list someone',
            'valuebot list someone today',
            'valuebot list someone july',
            'valuebot list someone july 2014',
            '#testvalue <@someone> yes!'
        ]

        for cmd in valids:
            post = SlackPost({
                "trigger_word": cmd.split()[0],
                "text": cmd,
                "user_name": "testadmin",
                "timestamp": "11111111",
                "channel_name": "#channel"
            })

            response = self.value_bot.handle_post(post)

            self.assertIsInstance(response, SlackResponse)
            self.assertFalse(response.is_empty(), cmd)

    def test_invalid_syntax(self):
        invalids = [
            'valuebot helpme',
            'valuebot #avaluewedontknowabout <@someone>',
            'valuebot #testvalue @someone',
            '#testvalue @someone',
            '#testvalue hi',
            '#somevalue <@someone>'
        ]

        for cmd in invalids:
            post = SlackPost({
                "trigger_word": cmd.split()[0],
                "text": cmd,
                "user_name": "testadmin",
                "timestamp": "11111111",
                "channel_name": "#channel"
            })

            response = self.value_bot.handle_post(post)

            self.assertIsInstance(response, SlackResponse)
            self.assertTrue(response.is_empty(), cmd)

    def test_help(self):
        for cmd in ['valuebot help', 'valuebot man']:
            post = SlackPost({
                "trigger_word": "valuebot",
                "text": cmd,
                "user_name": "testadmin",
                "timestamp": "11111111",
                "channel_name": "#channel"
            })

            response = self.value_bot.handle_post(post)

            self.assertIsInstance(response, SlackResponse)
            self.assertTrue(len(response.messages) == 0)

            self.assertIn('testvalue', response.text)
            self.assertIn('#testvalue', response.text)

    def test_help_only_with_valuebot(self):
        for cmd in ['#testvalue help', '#testvalue man']:
            post = SlackPost({
                "trigger_word": "#testvalue",
                "text": cmd,
                "user_name": "testadmin",
                "timestamp": "11111111",
                "channel_name": "#channel"
            })

            response = self.value_bot.handle_post(post)

            self.assertIsInstance(response, SlackResponse)
            self.assertTrue(len(response.messages) == 0)

            self.assertEqual('', response.text)

    def test_call_out(self):
        for cmd in ['valuebot #testvalue <@user>', '#testvalue <@user>']:
            num_posts = Post.query.count()

            post = SlackPost({
                "trigger_word": cmd.split()[0],
                "text": cmd,
                "user_name": "testadmin",
                "timestamp": "11111111",
                "channel_name": "#channel"
            })

            response = self.value_bot.handle_post(post)

            self.assertIsInstance(response, SlackResponse)
            self.assertTrue(len(response.messages) == 0)

            self.assertNotEqual('', response.text)
            self.assertNotIn('Error', response.text)

            self.assertEqual(Post.query.count(), num_posts + 1)

            most_recent = Post.query.order_by(Post.id.desc()).first()
            self.assertEqual(most_recent.user, "user")
            self.assertEqual(most_recent.poster, "testadmin")
            self.assertEqual(most_recent.value, "testvalue")
            self.assertEqual(most_recent.slack_channel, "#channel")

if __name__ == '__main__':
    unittest.main()