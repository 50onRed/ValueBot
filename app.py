import json
from value_bot import ValueBot
from flask import Flask, request

app = Flask(__name__)
app.config.from_pyfile('./config/options.py')

def payload(text):
    return {
        "text": text,
        'link_names': 1
    }

value_bot = ValueBot(
    help_commands=app.config["HELP_COMMANDS"],
    hashtags=app.config['HASHTAGS'])

@app.route('/', methods=['POST'])
def post():
    to_return = value_bot.handleIncomingMessage(request.form)

    return json.dumps(payload(to_return))

def main():
    app.run(host='0.0.0.0', port=4567, debug=True)

if __name__ == "__main__":
    main()