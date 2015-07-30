import datetime
from sqlalchemy import Column, Integer, String, DateTime, func, desc
from calendar import monthrange
from . import Base

MAX_LINE_LENGTH = 65

class Post(Base):
    __tablename__ = 'posts'

    id = Column(Integer, primary_key=True)
    user = Column(String, nullable=False)
    poster = Column(String, nullable=False)
    value = Column(String, nullable=False)
    text = Column(String, nullable=False)
    posted_at = Column(DateTime, nullable=False)
    slack_timestamp = Column(String, nullable=False)
    slack_channel = Column(String, nullable=False)

    def __init__(self, user, poster, value, text, slack_timestamp, slack_channel, posted_at=None):
        self.user = user
        self.poster = poster
        self.value = value
        self.text = text
        self.posted_at = posted_at or datetime.datetime.now()
        self.slack_timestamp = slack_timestamp
        self.slack_channel = slack_channel

    def post_url(self, slack):
        channel = slack.get_channel_name(self.slack_channel)

        if channel:
            ts = self.slack_timestamp.replace(".", "")
            return "https://50onred.slack.com/archives/{}/p{}".format(channel, ts)
        else:
            return "(Private message)"

    @property
    def users_value_info_for_table(self):
        return "@{} -> @{} for `{}`".format(self.poster, self.user, self.value)

    def message_info_for_table(self, slack):
        if not isinstance(self.text, unicode):
            text = unicode(self.text, "ISO-8859-1")
        else:
            text = self.text

        text_tokens = text.split()

        lines = []
        curr_line = []
        curr_line_length = 0

        for token in text_tokens:
            if token.startswith("<@"):
                last_chars = token[12:0]
                user_id = token[:12].strip("@<>")
                user_name = slack.get_user_name(user_id)
                token = u"@{}{}".format(user_name, last_chars)

            curr_line_length += 1 + len(token)

            if curr_line_length > MAX_LINE_LENGTH:
                line = " ".join(curr_line)
                lines.append(line)
                curr_line = [token]
                curr_line_length = 0
            else:
                curr_line.append(token)

        lines.append(" ".join(curr_line))

        text = u"\n".join(lines)
        return u"{}\n{}".format(text, self.post_url(slack))

    @property
    def posted_at_formatted(self):
        return self.posted_at.strftime('%B %d %Y %I:%M %p')

    @classmethod
    def posts_by_user(cls, session, user, date, month, year):
        query = session.query(cls).filter(Post.user == user)

        if date or month:
            dates = _get_date_range(date, month, year)
            query = query.filter(Post.posted_at >= dates[0], Post.posted_at <= dates[1])

        return query

    @classmethod
    def posts_by_value(cls, session, value, date, month, year):
        query = session.query(cls)

        if (value and value != "all"):
            query = query.filter(Post.value == value)

        if date or month:
            dates = _get_date_range(date, month, year)
            query = query.filter(Post.posted_at >= dates[0], Post.posted_at <= dates[1])

        return query

    @classmethod
    def leaders_by_value(cls, session, value, date, month, year):
        query = session.query(Post.user, func.count(Post.id).label('user_occurence')
            ).group_by(Post.user
            ).order_by(desc('user_occurence'))

        if value and value != "all":
            query = query.filter(Post.value == value)

        if date or month:
            dates = _get_date_range(date, month, year)
            query = query.filter(Post.posted_at >= dates[0], Post.posted_at <= dates[1])

        return query

def _get_date_range(date, month, year):
    start, end = None, None

    if date:
        start = datetime.datetime(year, month, date)
        end = datetime.datetime(year, month, date, 23, 59, 59)
    else:
        start = datetime.datetime(year, month, 1)
        days_in_month = monthrange(year, month)[1]
        end = datetime.datetime(year, month, days_in_month, 23, 59, 59)

    return (start, end)
