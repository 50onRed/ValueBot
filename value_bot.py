import re
import datetime
import requests
import json
from db.db import Post
from prettytable import PrettyTable

MONTHS=["january", "february", "march", "april", "may", "june",
        "july", "august", "september", "october", "november", "december"]

class ValueBot():
    def __init__(self, help_commands, list_commands, hashtags, webhook_url):
        self.help_commands = help_commands
        self.list_commands = list_commands
        self.valuesDict = self.__generateValuesDict(hashtags)
        self.values = hashtags.keys()
        self.webhook_url = webhook_url

    def handleIncomingMessage(self, msg):
        trigger = msg["trigger_word"]
        text = msg["text"]
        poster = msg["user_name"]

        if not trigger.startswith("#"):
            regex = re.compile(trigger + ':*\s*(.*)')
            text = regex.match(text).group(1) # only the text after the trigger command

            if text.lower() in self.help_commands:
                return "TODO: WRITE HELP MESSAGE"

            if text.startswith(tuple(self.list_commands)):
                # TODO: send this as a private message
                return self.__generateList(text, poster)

        return self.__handleCallOut(trigger, text, poster)

    def sendPrivateMessage(self, recipient, text):
        payload = {
            "channel": "@{}".format(recipient),
            "text": text
        }
        data = { "payload": json.dumps(payload) }
        r = requests.post(self.webhook_url, data=data)

        return "PM-ed!"

    def __handleCallOut(self, trigger, text, poster):
        value, user = None, None

        if trigger in self.valuesDict: # message started with hashtag
            value = self.valuesDict[trigger]
        else: # bot triggered by name
            hashtags = [tag.rstrip(".,!?:;") for tag in text.split() if tag.startswith("#")]
            for tag in hashtags:
                if tag in self.valuesDict:
                    value = self.valuesDict[tag]
                    break # only use the first hashtag that matches a value

        if value:
            mentioned_users = [name.strip("@.,!?:;") for name in text.split() if name.startswith("@")]
            if len(mentioned_users) >= 1:
                user = mentioned_users[0]

        if value and user:
            post = Post(user, poster, value, text)
            if post.save():
                return "Thanks, @{0}! I've recorded your call out under `{1}`.".format(poster, value)
            else:
                return "There was an error saving your call out, sorry!"

        return ''

    def __generateList(self, text, poster):
        tokens = [token.rstrip(".,!?:;").lower() for token in text.split()]
        del(tokens[0]) # get rid of 'list' token
        length = len(tokens)

        if length < 1:
            return ''

        leaders, user, value, date, month, year = False, None, None, None, None, None

        if tokens[0] == "leaders":
            leaders = True
            del(tokens[0])
            length -= 1
            if length < 1:
                return ''

        # TODO: check if user is admin

        subject = tokens[0]

        if subject == "me" and not leaders:
            user = poster
        elif subject.startswith("@") and not leaders:
            user = subject.lstrip("@")
        elif subject in self.values or subject == "all":
            value = subject
        elif subject in self.valuesDict:
            value = self.valuesDict[subject]
        elif not leaders:
            user = subject

        if length >= 2:
            now = datetime.datetime.now()

            date_token = tokens[1]
            if date_token == "today":
                date = now.day
                month = now.month
                year = now.year
            elif date_token == "all":
                date = None
            elif date_token in MONTHS:
                month = MONTHS.index(date_token) + 1

                if length >= 3:
                    year_token = tokens[2]

                    try:
                        year = int(year_token)
                    except ValueError:
                        return "Invalid year '{}'".format(year_token)
                else:
                    year = now.year

                    if now.month < date:
                        year -= 1

        print (leaders, user, value, date, month, year)

        if leaders and value:
            Post.getLeadersByValue(value, date, month, year)
        else:
            posts = None
            if user:
                posts = Post.getPostsByUser(user, date, month, year)
            elif value:
                posts = Post.getPostsByValue(value, date, month, year)

            if posts:
                table = newLeftAlignedTable(["User", "Poster", "Value", "Message", "Posted"])

                for post in posts:
                    table.add_row([post.user, post.poster, post.value, post.text, post.posted_at])
                return self.sendPrivateMessage(poster, "```{}```".format(table.get_string()))
            else:
                return self.sendPrivateMessage(poster, 'No posts found!')

        return ''

    # Flattens hashtag dictionary, for easy mapping from hashtags to corresponding values
    def __generateValuesDict(self, hashtags):
        valuesDict = {}

        for value in hashtags:
            for hashtag in hashtags[value]:
                valuesDict[hashtag] = value

        return valuesDict

def newLeftAlignedTable(attrs):
    t = PrettyTable(attrs)
    for a in attrs:
        t.align[a] = "l"
    return t