import re
import datetime
import requests
import json
from db.db import Post
from prettytable import PrettyTable

MONTHS=["january", "february", "march", "april", "may", "june",
        "july", "august", "september", "october", "november", "december"]

class ValueBot():
    def __init__(self, admins, hashtags, webhook_url):
        self.admins = admins
        self.valuesDict = self._generate_values_dict(hashtags)
        self.values = hashtags.keys()
        self.webhook_url = webhook_url

    def handle_incoming_message(self, msg):
        trigger = msg["trigger_word"]
        text = msg["text"]
        poster = msg["user_name"]
        timestamp = msg["timestamp"].replace(".", "")
        channel = msg["channel_name"]

        if not trigger.startswith("#"):
            regex = re.compile(trigger + ':*\s*(.*)')
            text = regex.match(text).group(1) # only the text after the trigger command

            if text.lower() in ["help", "man"]:
                return "TODO: WRITE HELP MESSAGE"

            if text.startswith("list"):
                return self._generate_list(text, poster)

        return self._handle_call_out(trigger, text, poster, timestamp, channel)

    def send_private_message(self, recipient, title, table_text=None):
        text = "*{}*".format(title)

        if table_text:
            text += "\n```{}```".format(table_text)

        payload = {
            "channel": "@{}".format(recipient),
            "text": text
        }
        data = { "payload": json.dumps(payload) }
        r = requests.post(self.webhook_url, data=data)

        return "PM-ed!"

    def _handle_call_out(self, trigger, text, poster, timestamp, channel):
        value, user = None, None

        if trigger in self.valuesDict: # message started with hashtag
            value = self.valuesDict[trigger]
        else: # bot triggered by name
            hashtags = [tag.rstrip(".,!?:;") for tag in text.split() if tag.startswith("#")]
            for tag in hashtags:
                if tag in self.valuesDict:
                    value = self.valuesDict[tag]
                    break # only use the first hashtag that matches a value

        mentioned_users = [name.strip("@.,!?:;") for name in text.split() if name.startswith("@")]
        if len(mentioned_users) >= 1:
            user = mentioned_users[0]

        if not value or not user:
            return ''

        post = Post(user, poster, value, text, timestamp, channel)
        if post.save():
            return "Thanks, @{0}! I've recorded your call out under `{1}`.".format(poster, value)
        else:
            return "There was an error saving your call out, sorry!"

    def _generate_list(self, text, poster):
        tokens = [token.rstrip(".,!?:;").lower() for token in text.split()]
        del(tokens[0]) # get rid of 'list' token
        length = len(tokens)
        now = datetime.datetime.now()

        if length < 1:
            return ''

        leaders, user, value, date, month, year = False, None, None, None, None, None

        subject = None

        if tokens[0] == "leaders":
            leaders = True
            del(tokens[0])
            length -= 1
            if length < 1:
                # default to this month
                month = now.month
                year = now.year
                subject = "all"

        if not subject:
            subject = tokens[0]

        if not poster in self.admins and subject != "me":
            return "Admin-only!"

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

        if leaders and value:
            leaders = Post.get_leaders_by_value(value, date, month, year)

            title = "Leaders in {}{}".format(value, date_clause(date, month, year))

            if leaders:
                table = new_left_aligned_table(["User", "# Posts"])

                for user in leaders:
                    table.add_row([user['user'], user['posts']])

                return self.send_private_message(poster, title, table.get_string())
            else:
                return self.send_private_message(poster, title, 'No leaders found')
        else:
            posts = None

            title = "Posts "
            if user:
                posts = Post.get_posts_by_user(user, date, month, year)
                title += "about @{}".format(user)
            elif value:
                posts = Post.get_posts_by_value(value, date, month, year)
                title += "in {}".format(value)

            title += date_clause(date, month, year)

            if posts:
                table = new_left_aligned_table(["User", "Poster", "Value", "Message", "Posted"])

                for post in posts:
                    table.add_row([post.user, post.poster, post.value, post.message_info_for_table, post.posted_at_formatted])
                return self.send_private_message(poster, title, table.get_string())
            else:
                return self.send_private_message(poster, title, 'No posts found!')

        return ''

    # Flattens hashtag dictionary, for easy mapping from hashtags to corresponding values
    def _generate_values_dict(self, hashtags):
        valuesDict = {}

        for value in hashtags:
            for hashtag in hashtags[value]:
                valuesDict[hashtag] = value

        return valuesDict

def new_left_aligned_table(attrs):
    t = PrettyTable(attrs)
    for a in attrs:
        t.align[a] = "l"
    return t

def date_clause(date, month, year):
    clause = ""

    if (date or month):
        if date:
            clause += ", on {}".format(date)
        else:
            clause += ", in"

        clause += " {} {}".format(MONTHS[month-1].capitalize(), year)

    return clause