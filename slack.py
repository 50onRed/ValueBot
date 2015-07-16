import websocket
import requests
import json

class Slack(object):
    def __init__(self, api_token):
        self.api_token = api_token
        self.username_cache = {}

    def start(self, handlers):
        self.handlers = handlers
        websocket.enableTrace(True)

        data = {
            "token": self.api_token
        }
        r = requests.post("https://slack.com/api/rtm.start", data=data)
        r.raise_for_status()

        try:
            response_data = r.json()
            print response_data
            print response_data["url"]

            ws = websocket.WebSocketApp(response_data["url"],
                                        on_message = self._on_message,
                                        on_error = self._on_error,
                                        on_close = self._on_close)
            ws.run_forever()
        except ValueError:
            print "lmaoerror"

    def _on_message(self, ws, message):
        print message
        message = json.loads(message)

        is_deleted = "subtype" in message and message["subtype"] == "message_deleted"
        if message["type"] == "message" and not is_deleted:
            post = SlackPost(
                text=message["text"],
                poster=message["user"],
                timestamp=message["ts"],
                channel=message["channel"])

            if "post" in self.handlers:
                self.handlers["post"](post)

    def _on_error(self, ws, error):
        print error

    def _on_close(self, ws):
        print "### WebSocket connection closed ###"

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
    def __init__(self, text, poster, timestamp, channel):
        self.text = text
        self.poster = poster
        self.timestamp = timestamp
        self.channel = channel