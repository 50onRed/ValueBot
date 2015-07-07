import json
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

    value_bot = ValueBot(
        admins=app.config["ADMINS"],
        hashtags=app.config["HASHTAGS"],
        webhook_url=app.config["WEBHOOK_URL"])

    @app.route('/', methods=['POST'])
    def post():
        to_return = value_bot.handle_incoming_message(request.form)

        return json.dumps(payload(to_return))

    return app

app = create_app()
manager = Manager(app)

manager.add_command('db', MigrateCommand)

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