import json
import sqlite3
from value_bot import ValueBot
from flask import Flask, request
from contextlib import closing

app = Flask(__name__)
app.config.from_pyfile('./config/hashtags.py')

def connect_db():
    return sqlite3.connect('./db/valuebot.sqlite3')

def init_db():
    with closing(connect_db()) as db:
        with app.open_resource('./db/schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

value_bot = ValueBot(db=connect_db(), hashtags=app.config['HASHTAGS'])

@app.route('/', methods=['POST'])
def post():
    print "yo"

    command = request.form['text'].strip()
    user = request.form['user_name']
    value_bot.handleIncomingMessage(request.form)
    return json.dumps({
        # "channel": "#valuebot-testing",
        # "username": "ValueBot",
        "text": "Hello, " + user
    })

def main():
    app.run(host='0.0.0.0', port=4567, debug=True)

if __name__ == "__main__":
    main()