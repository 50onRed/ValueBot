import websocket
import requests
import json

class Slack(object):
    def __init__(self, api_token):
        self.api_token = api_token
        self.username_cache = {}
        self.channels_by_id = {}

    def start(self, handlers):
        self.handlers = handlers
        websocket.enableTrace(True)

        response = self.make_api_request("rtm.start")
        self.bot_user_id = response["self"]["id"]

        for user in response["users"]:
            self.username_cache[user["id"]] = user["name"]

        for channel in response["channels"]:
            self.channels_by_id[channel["id"]] = channel["name"]

        ws = websocket.WebSocketApp(response["url"],
                                    on_message = self._on_message,
                                    on_error = self._on_error,
                                    on_close = self._on_close)
        ws.run_forever()

    def _on_message(self, ws, message):
        print message
        message = json.loads(message)

        is_deleted = "subtype" in message and message["subtype"] == "message_deleted"
        is_message_confirmation = "ok" in message and message["ok"] == True
        is_real_user = "user" in message
        is_self = "user" in message and message["user"] == self.bot_user_id
        if (message["type"] == "message"
            and not is_deleted
            and not is_message_confirmation
            and is_real_user
            and not is_self):
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
        if user_id not in self.username_cache:
            user_info = self.make_api_request("users.info", { "user": user_id })

            user_name = user_info["user"]["name"]
            self.username_cache[user_id] = user_name

        return self.username_cache[user_id]

    def get_channel_name(self, channel_id):
        if channel_id in self.channels_by_id.values(): # old-style channels in database
            return channel_id

        if channel_id not in self.channels_by_id:
            channel_info = self.make_api_request("channels.info", { "channel": channel_id })

            if channel_info["ok"]:
                channel_name = channel_info["channel"]["name"]
            else:
                channel_name = None # private message or something

            self.channels_by_id[channel_id] = channel_name

        return self.channels_by_id[channel_id]

    def get_channel_id(self, channel_name):
        response = self.make_api_request("channels.list")

        if not response['ok']:
            print "ERROR: {}".format(response['error'])
            return None

        for channel in response["channels"]:
            if channel["name"] == channel_name:
                return channel["id"]

        return None

    def private_message_channel(self, user_id):
        response = self.make_api_request("im.open", { "user": user_id })

        return response["channel"]["id"]

    def make_api_request(self, method, data={}):
        data["token"] = self.api_token

        r = requests.post("https://slack.com/api/{}".format(method), data=data)
        r.raise_for_status()

        try:
            response_data = r.json()
            return response_data
        except ValueError:
            return None

class SlackResponse(object):
    def send(self, slack):
        pass

class SlackMessage(SlackResponse):
    def __init__(self, channel, text):
        self.channel = channel
        self.text = text

    def send(self, slack):
        if self.channel.startswith("U"):
            channel = slack.private_message_channel(self.channel)
        else:
            channel = self.channel

        payload = {
            "channel": channel,
            "text": self.text,
            "link_names": 1,
            "unfurl_links": False,
            "as_user": True
        }

        res = slack.make_api_request("chat.postMessage", payload)
        print res

class SlackPreformattedMessage(SlackMessage):
    def __init__(self, channel, content, title=None):
        if title:
            text = "*{}*\n```{}```".format(title, content)
        else:
            text = "```{}```".format(content)

        super(SlackPreformattedMessage, self).__init__(channel, text)

class SlackReaction(SlackResponse):
    def __init__(self, channel, timestamp, name):
        self.channel = channel
        self.timestamp = timestamp
        self.name = name

    def send(self, slack):
        payload = {
            "channel": self.channel,
            "timestamp": self.timestamp,
            "name": self.name
        }

        res = slack.make_api_request("reactions.add", payload)
        print res

class SlackPost(object):
    def __init__(self, text, poster, timestamp, channel):
        self.text = text
        self.poster = poster
        self.timestamp = timestamp
        self.channel = channel

    def respond(self, text):
        return SlackMessage(
            channel=self.channel,
            text=text
        )

    def react(self, emoji):
        return SlackReaction(
            channel=self.channel,
            timestamp=self.timestamp,
            name=emoji
        )
