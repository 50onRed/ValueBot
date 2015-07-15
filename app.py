import json
import datetime
from slack import Slack, SlackPost, SlackMessage, SlackPreformattedMessage
from value_bot import ValueBot
from flask import Flask, request
from flask.ext.script import Manager
from flask.ext.migrate import Migrate, MigrateCommand
from db.db import db

def payload(text):
    return {
        "text": text,
        'link_names': 1
    }

def create_app():
    app = Flask(__name__)
    app.config.from_pyfile('./config.py')

    db.init_app(app)
    migrate = Migrate(app, db)

    @app.route('/', methods=['POST'])
    def post():
        post = SlackPost(request.form)
        to_return = value_bot.handle_post(post)

        for msg in to_return.messages:
            slack.send_message(msg)

        return to_return.json_payload()

    return app

app = create_app()

slack = Slack(
    webhook_url=app.config["WEBHOOK_URL"],
    api_token=app.config["SLACK_TOKEN"])

value_bot = ValueBot(
    slack=slack,
    admins=app.config["ADMINS"],
    hashtags=app.config["HASHTAGS"])

manager = Manager(app)
manager.add_command('db', MigrateCommand)

@manager.command
def send_yesterday_leaders(channel):
    now = datetime.datetime.now()
    yesterday = now - datetime.timedelta(days=1)

    with app.app_context():
        table = value_bot.get_leaders_table("all", yesterday.day, yesterday.month, yesterday.year)

        if table:
            content = table.get_string()
        else:
            content = "No leaders found"

        message = SlackPreformattedMessage(channel, "Yesterday's leaders", content)
        slack.send_message(message)

@manager.command
def send_callout_reminder(channel):
    message = SlackMessage(channel, "*Daily reminder to call out team members for embodying the core values today!*")
    slack.send_message(message)

@manager.command
def trigger_list():
    hashtags = app.config["HASHTAGS"]
    triggers = {"valuebot"}

    for value in hashtags:
        for hashtag in hashtags[value]:
            triggers.add(hashtag)

    print ','.join(triggers)

if __name__ == "__main__":
    manager.run()