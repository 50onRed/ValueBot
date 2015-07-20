import unittest
from slack import Slack, SlackResponse, SlackMessage, SlackReaction, SlackPost
from value_bot import ValueBot
from db import Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.post import Post

class DummySlack(Slack):
    def __init__(self):
        return

    def get_user_name(self, user_id):
        return user_id

    def get_channel_name(self, channel_id):
        return channel_id

    def private_message_channel(user_id):
        return "D{}".format(user_id)

class ValueBotTests(unittest.TestCase):
    def setUp(self):
        engine = create_engine("sqlite://")
        Session = sessionmaker(bind=engine)
        Base.metadata.create_all(engine)

        self.session = Session()

        slack = DummySlack()

        self.value_bot = ValueBot(
            slack=slack,
            admins={"testadmin"},
            hashtags={
                "testvalue": {"#testvalue"}
            }
        )

    def tearDown(self):
        self.session.close()

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
            'valuebot list leaders all',
            'valuebot list leaders all today',
            'valuebot list leaders all july',
            'valuebot list leaders all july 2014',
            'valuebot list leaders testvalue',
            'valuebot list leaders testvalue today',
            'valuebot list leaders testvalue july',
            'valuebot list leaders testvalue july 2014',
            '#testvalue <@someone> yes!'
            'whatever #testvalue <@someone> wahoooo',
            'some other thing for <@someone> #testvalue'
        ]

        for cmd in valids:
            post = SlackPost(
                text=cmd,
                poster="testadmin",
                timestamp="11111111",
                channel="#channel"
            )

            response = self.value_bot.handle_post(post, self.session)

            self.assertIsInstance(response, list)
            self.assertTrue(len(response) > 0, cmd)

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
            post = SlackPost(
                text=cmd,
                poster="testadmin",
                timestamp="11111111",
                channel="#channel"
            )

            response = self.value_bot.handle_post(post, self.session)

            self.assertIsInstance(response, list)
            self.assertTrue(len(response) == 0, cmd)

    def test_help(self):
        for cmd in ['valuebot help', 'valuebot man']:
            post = SlackPost(
                text=cmd,
                poster="testadmin",
                timestamp="11111111",
                channel="#channel"
            )

            response = self.value_bot.handle_post(post, self.session)

            self.assertIsInstance(response, list)
            self.assertTrue(len(response) == 1)
            self.assertIsInstance(response[0], SlackMessage)

            self.assertIn('testvalue', response[0].text)
            self.assertIn('#testvalue', response[0].text)

    def test_call_out(self):
        for cmd in ['valuebot #testvalue <@user>', '#testvalue <@user>']:
            num_posts = self.session.query(Post).count()

            post = SlackPost(
                text=cmd,
                poster="testadmin",
                timestamp="11111111",
                channel="#channel"
            )

            response = self.value_bot.handle_post(post, self.session)

            self.assertIsInstance(response, list)
            self.assertTrue(len(response) == 1)
            self.assertIsInstance(response[0], SlackReaction)

            self.assertEqual(self.session.query(Post).count(), num_posts + 1)

            most_recent = self.session.query(Post).order_by(Post.id.desc()).first()
            self.assertEqual(most_recent.user, "user")
            self.assertEqual(most_recent.poster, "testadmin")
            self.assertEqual(most_recent.value, "testvalue")
            self.assertEqual(most_recent.slack_channel, "#channel")

if __name__ == '__main__':
    unittest.main()
