import argparse
import json
from value_bot import ValueBot
from flask import Flask, request
from db.db import init_db

app = Flask(__name__)
app.config.from_pyfile('./config.py')

def trigger_list():
    hashtags = app.config["HASHTAGS"]
    triggers = {"valuebot"}

    for value in hashtags:
        for hashtag in hashtags[value]:
            triggers.add(hashtag)

    return ','.join(triggers)

def payload(text):
    return {
        "text": text,
        'link_names': 1
    }

value_bot = ValueBot(
    admins=app.config["ADMINS"],
    hashtags=app.config["HASHTAGS"],
    webhook_url=app.config["WEBHOOK_URL"])

@app.route('/', methods=['POST'])
def post():
    to_return = value_bot.handle_incoming_message(request.form)

    return json.dumps(payload(to_return))

def main():
    parser = argparse.ArgumentParser(description="ValueBot: a SlackBot for your company's values")
    parser.add_argument('-p', '--port', type=int, help='the port to run ValueBot on')
    args = parser.parse_args()

    port = args.port or 4567

    app.run(host='0.0.0.0', port=port, debug=True)

if __name__ == "__main__":
    main()