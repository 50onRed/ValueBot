import datetime
import config
from lib.slack import Slack, SlackPost, SlackMessage, SlackPreformattedMessage
from value_bot import ValueBot
from manager import Manager
from contextlib import contextmanager
from db import session_scope

slack = Slack(config.SLACK_BOT_TOKEN)

value_bot = ValueBot(
    slack=slack,
    admins=config.ADMINS,
    hashtags=config.HASHTAGS)

manager = Manager()

@manager.command
def run():
    def handle_post(post):
        with session_scope() as session:
            responses = value_bot.handle_post(post, session)

        for res in responses:
            res.send(slack)

    slack.start({
        "post": handle_post
    })

@manager.command
def send_yesterday_leaders(channel):
    now = datetime.datetime.now()
    yesterday = now - datetime.timedelta(days=1)

    with session_scope() as session:
        table = value_bot.get_leaders_table(session, "all", yesterday.day, yesterday.month, yesterday.year)

    if table:
        content = table.get_string()
    else:
        content = "No leaders found"

    channel_id = slack.get_channel_id(channel)
    if channel_id:
        message = SlackPreformattedMessage(channel_id, content, "Yesterday's Leaders")
        message.send(slack)

@manager.command
def send_callout_reminder(channel):
    channel_id = slack.get_channel_id(channel)
    if channel_id:
        message = SlackMessage(channel_id, "*Daily reminder to call out team members for embodying the core values today!*")
        message.send(slack)

if __name__ == "__main__":
    manager.main()
