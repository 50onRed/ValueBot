import datetime
from sqlalchemy import Column, Integer, String, DateTime, func, desc
from calendar import monthrange
from .db import db, Base

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

    @property
    def post_url(self):
        return "https://50onred.slack.com/archives/{}/p{}".format(self.slack_channel, self.slack_timestamp)

    @property
    def message_info_for_table(self):
        return "{}\n{}".format(self.text, self.post_url)

    @property
    def posted_at_formatted(self):
        return self.posted_at.strftime('%B %d %Y %I:%M %p')

    @classmethod
    def posts_by_user(cls, user, date, month, year):
        query = cls.query.filter(Post.user == user)

        if date or month:
            dates = _get_date_range(date, month, year)
            query = query.filter(Post.posted_at >= dates[0], Post.posted_at <= dates[1])

        return query

    @classmethod
    def posts_by_value(cls, value, date, month, year):
        query = cls.query

        if (value and value != "all"):
            query = query.filter(Post.value == value)

        if date or month:
            dates = _get_date_range(date, month, year)
            query = query.filter(Post.posted_at >= dates[0], Post.posted_at <= dates[1])

        return query

    @classmethod
    def leaders_by_value(cls, value, date, month, year):
        query = db.session.query(Post.user, func.count(Post.id).label('user_occurence')
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