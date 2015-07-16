import requests
import json

class Slack(object):
    def __init__(self, webhook_url, api_token):
        self.webhook_url = webhook_url
        self.api_token = api_token
        self.username_cache = {}

    def get_user_name(self, user_id):
        if user_id in self.username_cache:
            return self.username_cache[user_id]

        data = {
            "token": self.api_token,
            "user": user_id
        }
        r = requests.post("https://slack.com/api/users.info", data=data)
        
        r.raise_for_status()

        try:
            response_data = r.json()
            user_name = response_data["user"]["name"]
            self.username_cache[user_id] = user_name

            return user_name
        except ValueError:
            return None
        else:
            return None

    def send_message(self, message):
        payload = {
            "channel": message.recipient,
            "text": message.text
        }
        data = { "payload": json.dumps(payload) }
        r = requests.post(self.webhook_url, data=data)

class SlackResponse(object):
    def __init__(self, text="", messages=[]):
        self.text = text
        self.messages = messages

    def json_payload(self):
        return json.dumps({
            "text": self.text,
            'link_names': 1
        })

    def is_empty(self):
        return self.text == "" and len(self.messages) == 0

class SlackMessage(object):
    def __init__(self, recipient, text):
        self.recipient = recipient
        self.text = text

class SlackPreformattedMessage(SlackMessage):
    def __init__(self, recipient, title, content):
        text = "*{}*\n```{}```".format(title, content)
        super(SlackPreformattedMessage, self).__init__(recipient, text)

class SlackPost(object):
    def __init__(self, msg_data):
        self.trigger = msg_data["trigger_word"]
        self.text = msg_data["text"]
        self.poster = msg_data["user_name"]
        self.timestamp = msg_data["timestamp"].replace(".", "")
        self.channel = msg_data["channel_name"]