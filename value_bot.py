import datetime
from slack import SlackResponse, SlackPreformattedMessage
from db.post import Post
from prettytable import PrettyTable, ALL, NONE

MONTHS=["january", "february", "march", "april", "may", "june",
        "july", "august", "september", "october", "november", "december"]

POSTS_PER_TABLE = 25

class ValueBot():
    def __init__(self, slack, admins, hashtags):
        self.admins = admins
        self.slack = slack
        self.valuesDict = self._generate_values_dict(hashtags)
        self.values = hashtags.keys()
        self.hashtags = hashtags

    def handle_post(self, post, session):
        if post.text.lower() in ["valuebot help", "valuebot man"]:
            response = self._help_message(post)
        elif post.text.startswith("valuebot list"):
            response = self._generate_list(post, session)
        else:
            response = self._handle_call_out(post, session)

        if not response:
            response = []

        if not isinstance(response, list):
            response = [response]

        return response

    def _help_message(self, post):
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

        return post.respond(to_return)

    def _handle_call_out(self, post, session):
        value, user = None, None

        hashtags = [tag.rstrip(".,!?:;") for tag in post.text.split() if tag.startswith("#")]
        for tag in hashtags:
            if tag in self.valuesDict:
                value = self.valuesDict[tag]
                break # only use the first hashtag that matches a value

        mentioned_users = [name.strip("@.,!?:;<>") for name in post.text.split() if name.startswith("<@")]
        if len(mentioned_users) >= 1:
            user = self.slack.get_user_name(mentioned_users[0])

            if user == None:
                return post.respond("Error finding specified user.")

        if not value or not user:
            return None

        poster_username = self.slack.get_user_name(post.poster)

        post_obj = Post(user, poster_username, value, post.text, post.timestamp, post.channel)
        session.add(post_obj)

        return post.react("white_check_mark")

    def _generate_list(self, post, session):
        tokens = [token.rstrip(".,!?:;").lower() for token in post.text.split()]

        if (tokens[0].startswith("valuebot")):
            del(tokens[0])

        del(tokens[0]) # get rid of 'list' token
        length = len(tokens)
        now = datetime.datetime.now()

        if length < 1:
            return None

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

        if not self.is_admin(post.poster) and subject != "me":
            return post.react("x")

        if subject == "me" and not leaders:
            user = post.poster
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
                        return post.respond("Invalid year '{}'".format(year_token))
                else:
                    year = now.year

                    if now.month < date:
                        year -= 1

        reaction = post.react("ok_hand")

        if leaders and value:
            table = self.get_leaders_table(session, value, date, month, year)

            title = "Leaders in {}{}".format(value, date_clause(date, month, year))

            if table:
                content = table.get_string()
            else:
                content = "No leaders found"

            message = SlackPreformattedMessage(post.poster, content, title)
            return [reaction, message]
        else:
            posts = None

            title = "Posts "
            if user:
                posts = Post.posts_by_user(session, user, date, month, year).all()
                title += "about @{}".format(user)
            elif value:
                posts = Post.posts_by_value(session, value, date, month, year).all()
                title += "in {}".format(value)

            title += date_clause(date, month, year)
            response = [reaction]

            if posts:
                table = new_left_aligned_table(["Info", "Message", "Date"])
                num_in_table = 0
                num_posts = len(posts)
                first_table = True

                for idx, p in enumerate(posts):
                    table.add_row([
                        p.users_value_info_for_table,
                        p.message_info_for_table(self.slack),
                        p.posted_at_formatted])

                    num_in_table += 1

                    if num_in_table == POSTS_PER_TABLE or idx == num_posts - 1:
                        if first_table:
                            msg = SlackPreformattedMessage(post.poster, table.get_string(), title)
                            first_table = False
                        else:
                            msg = SlackPreformattedMessage(post.poster, table.get_string())

                        response.append(msg)

                        table = new_left_aligned_table(["Info", "Message", "Date"], False)
                        num_in_table = 0
            else:
                message = SlackPreformattedMessage(post.poster, "No posts found", title)
                response.append(message)

            return response

        return None

    def get_leaders_table(self, session, value, date, month, year):
        leaders = Post.leaders_by_value(session, value, date, month, year).all()

        if len(leaders) == 0:
            return None

        table = new_left_aligned_table(["User", "# Posts"])

        for user in leaders:
            table.add_row([user[0], user[1]])

        return table

    def is_admin(self, user_id):
        username = self.slack.get_user_name(user_id)
        return username in self.admins

    # Flattens hashtag dictionary, for easy mapping from hashtags to corresponding values
    def _generate_values_dict(self, hashtags):
        valuesDict = {}

        for value in hashtags:
            for hashtag in hashtags[value]:
                valuesDict[hashtag] = value

        return valuesDict

def new_left_aligned_table(attrs, header=True):
    if header:
        t = PrettyTable(attrs)
    else:
        t = PrettyTable(attrs)
        t.header = False

    t.align = "l"
    t.hrules = ALL
    t.horizontal_char = " "
    t.vrules = NONE
    t.header_style = "upper"
    t.padding_width = 1
    t.left_padding_width = 0
    t.right_padding_width = 0
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