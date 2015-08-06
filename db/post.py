import datetime, textwrap
from sqlalchemy import Column, Integer, String, DateTime, func, desc, ForeignKey
from sqlalchemy.orm import relationship
from calendar import monthrange
from . import Base

MAX_INFO_LENGTH = 45
MAX_MSG_LENGTH = 65

class Post(Base):
    __tablename__ = 'posts'

    id = Column(Integer, primary_key=True)
    users = relationship('PostUser', back_populates='post')
    values = relationship('PostValue', back_populates='post')
    poster = Column(String(64), nullable=False)
    text = Column(String(500), nullable=False)
    posted_at = Column(DateTime, nullable=False)
    slack_timestamp = Column(String(64), nullable=False)
    slack_channel = Column(String(64), nullable=False)

    def __init__(self, poster, text, slack_timestamp, slack_channel, posted_at=None):
        self.poster = poster
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
            return "(Private Message or Group)"

    @property
    def users_value_info_for_table(self):
        users = map(lambda u: u.formatted_name, self.users)
        users = ", ".join(users)

        values = map(lambda v: v.value, self.values)
        values = ", ".join(values)

        text = "@{} -> {} for {}".format(self.poster, users, values)
        return textwrap.fill(text, MAX_INFO_LENGTH)

    def message_info_for_table(self, slack):
        if not isinstance(self.text, unicode):
            text = unicode(self.text, "ISO-8859-1")
        else:
            text = self.text

        def replace_usernames(token):
            if token.startswith("<@"):
                last_chars = token[12:0]
                user_id = token[:12].strip("@<>")
                user_name = slack.get_user_name(user_id)
                token = u"@{}{}".format(user_name, last_chars)

            return token

        text_tokens = map(replace_usernames, text.split())
        text = textwrap.fill(u" ".join(text_tokens), MAX_MSG_LENGTH)
        return u"{}\n{}".format(text, self.post_url(slack))

    @property
    def posted_at_formatted(self):
        return self.posted_at.strftime('%B %d %Y %I:%M %p')

    @classmethod
    def posts_by_user(cls, session, user, date, month, year):
        query = session.query(Post).join(Post.users).filter(PostUser.user == user)

        if date or month:
            dates = _get_date_range(date, month, year)
            query = query.filter(Post.posted_at >= dates[0], Post.posted_at <= dates[1])

        return query

    @classmethod
    def posts_by_value(cls, session, value, date, month, year):
        query = session.query(cls)

        if (value and value != "all"):
            query = query.join(Post.values).filter(PostValue.value == value)

        if date or month:
            dates = _get_date_range(date, month, year)
            query = query.filter(Post.posted_at >= dates[0], Post.posted_at <= dates[1])

        return query

    @classmethod
    def leaders_by_value(cls, session, value, date, month, year):
        query = session.query(PostUser.user, func.count(PostUser.id).label('user_occurence')
            ).group_by(PostUser.user
            ).order_by(desc('user_occurence'))

        if value and value != "all":
            query = query.join("post").join(Post.values).filter(PostValue.value == value)

        if date or month:
            dates = _get_date_range(date, month, year)
            query = query.filter(Post.posted_at >= dates[0], Post.posted_at <= dates[1])

        return query

class PostUser(Base):
    __tablename__ = 'post_users'

    id = Column(Integer, primary_key=True)
    user = Column(String, nullable=False)
    post_id = Column(Integer, ForeignKey('posts.id'))

    post = relationship('Post', back_populates='users')

    def __init__(self, user):
        self.user = user

    @property
    def formatted_name(self):
        return "@{}".format(self.user)

class PostValue(Base):
    __tablename__ = 'post_values'

    id = Column(Integer, primary_key=True)
    value = Column(String, nullable=False)
    post_id = Column(Integer, ForeignKey('posts.id'))

    post = relationship('Post', back_populates='values')

    def __init__(self, value):
        self.value = value

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
