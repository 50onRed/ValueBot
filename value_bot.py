import re
import datetime
from slack import SlackResponse, SlackPreformattedMessage
from db.db import db
from db.post import Post
from prettytable import PrettyTable

MONTHS=["january", "february", "march", "april", "may", "june",
        "july", "august", "september", "october", "november", "december"]

class ValueBot():
    def __init__(self, slack, admins, hashtags):
        self.admins = admins
        self.slack = slack
        self.valuesDict = self._generate_values_dict(hashtags)
        self.values = hashtags.keys()
        self.hashtags = hashtags

    def handle_post(self, post):
        if not post.trigger.startswith("#"):
            regex = re.compile(post.trigger + ':*\s*(.*)')
            post.text = regex.match(post.text).group(1) # only the text after the trigger command

            if post.text.lower() in ["help", "man"]:
                return self._help_message()

            if post.text.startswith("list"):
                return self._generate_list(post.text, post.poster)

        return self._handle_call_out(post)

    def _help_message(self):
        to_return = "*ValueBot Usage*"
        to_return += "\nA call-out is a message that includes a team member you want to call out, and a hashtag of the value you want to call them out for."
        to_return += "\n\nThe list of values and hashtags are as follows:"

        for value in self.hashtags:
            to_return += "\n> *{}:* ".format(value.title())

            hashtags = map(lambda h: "`{}`".format(h), self.hashtags[value])
            to_return += ", ".join(hashtags)

        to_return += "\nTo get ValueBot to hear your call-out, start your message either with the hashtag, or with `valuebot`. For example:"
        to_return += "\n```valuebot @mary #got-shit-done yesterday!```"
        to_return += "\n```valuebot Thanks @jane for being so #curious```"
        to_return += "\n```#supportive Thanks @mike for your help on that thing this morning!```"

        return SlackResponse(to_return)

    def _handle_call_out(self, post):
        value, user = None, None

        if post.trigger in self.valuesDict: # message started with hashtag
            value = self.valuesDict[post.trigger]
        else: # bot triggered by name
            hashtags = [tag.rstrip(".,!?:;") for tag in post.text.split() if tag.startswith("#")]
            for tag in hashtags:
                if tag in self.valuesDict:
                    value = self.valuesDict[tag]
                    break # only use the first hashtag that matches a value

        mentioned_users = [name.strip("@.,!?:;<>") for name in post.text.split() if name.startswith("<@")]
        if len(mentioned_users) >= 1:
            user = self.slack.user_name_of_user_id(mentioned_users[0])

            if user == None:
                return SlackResponse("Error finding specified user.")

        if not value or not user:
            return SlackResponse()

        post_obj = Post(user, post.poster, value, post.text, post.timestamp, post.channel)
        db.session.add(post_obj)

        try:
            db.session.commit()
            text = "Thanks, @{0}! I've recorded your call out under `{1}`.".format(post.poster, value)
        except:
            text = "There was an error saving your call out, sorry!"

        return SlackResponse(text)

    def _generate_list(self, text, poster):
        tokens = [token.rstrip(".,!?:;").lower() for token in text.split()]
        del(tokens[0]) # get rid of 'list' token
        length = len(tokens)
        now = datetime.datetime.now()

        if length < 1:
            return SlackResponse()

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
            return SlackResponse("Admin-only!")

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
                        return SlackResponse("Invalid year '{}'".format(year_token))
                else:
                    year = now.year

                    if now.month < date:
                        year -= 1

        poster_username = "@{}".format(poster)

        if leaders and value:
            table = self.get_leaders_table(value, date, month, year)

            title = "Leaders in {}{}".format(value, date_clause(date, month, year))

            if table:
                content = table.get_string()
            else:
                content = "No leaders found"

            message = SlackPreformattedMessage(poster_username, title, content)
            return SlackResponse("Message sent!", [message])
        else:
            posts = None

            title = "Posts "
            if user:
                posts = Post.posts_by_user(user, date, month, year).all()
                title += "about @{}".format(user)
            elif value:
                posts = Post.posts_by_value(value, date, month, year).all()
                title += "in {}".format(value)

            title += date_clause(date, month, year)

            if posts:
                table = new_left_aligned_table(["User", "Poster", "Value", "Message", "Posted"])

                for post in posts:
                    table.add_row([post.user, post.poster, post.value, post.message_info_for_table, post.posted_at_formatted])
                content = table.get_string()
            else:
                content = "No posts found"

            message = SlackPreformattedMessage(poster_username, title, content)
            return SlackResponse("Message sent!", [message])

        return SlackResponse()

    def get_leaders_table(self, value, date, month, year):
        leaders = Post.leaders_by_value(value, date, month, year).all()

        if len(leaders) == 0:
            return None

        table = new_left_aligned_table(["User", "# Posts"])

        for user in leaders:
            table.add_row([user[0], user[1]])

        return table

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