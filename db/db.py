import sqlite3
import datetime
from calendar import monthrange
from contextlib import closing

def connect_db():
    return sqlite3.connect('./db/valuebot.sqlite3')

def init_db():
    with closing(connect_db()) as db:
        with file('./db/schema.sql') as f:
            db.cursor().executescript(f.read())
        db.commit()
        print "DB schema initialized."

class Post():
    def __init__(self, user, poster, value, text, slack_timestamp, posted_at=None):
        self.user = user
        self.poster = poster
        self.value = value
        self.text = text
        if posted_at:
            self.posted_at = posted_at
        else:
            self.posted_at = datetime.datetime.now()
        self.slack_timestamp = slack_timestamp

    def save(self):
        con = connect_db()

        with con:
            con.execute(
                "INSERT INTO posts(user, poster, value, text, posted_at, slack_timestamp) VALUES (?, ?, ?, ?, ?, ?)",
                (self.user, self.poster, self.value, self.text, self.posted_at, self.slack_timestamp))
            return True

    @property
    def postUrl(self):
        return "http://50onred.slack.com/archives/general/{}".format(self.slack_timestamp)

    @classmethod
    def getPostsByUser(cls, user, date, month, year):
        query = "SELECT * FROM posts WHERE user = ?"
        attrs = (user,)

        if date or month:
            query += " AND posted_at BETWEEN ? AND ?"
            attrs += cls.__getDateRange(date, month, year)

        con = connect_db()
        with con:
            res = con.execute(query, attrs)

            to_return = []
            for post in res:
                to_return.append(Post(post[1], post[2], post[3], post[4], post[6], posted_at=post[5]))

            return to_return

    @classmethod
    def getPostsByValue(cls, value, date, month, year):
        query = "SELECT * FROM posts"
        attrs = ()
        where_added = False

        if value and value != "all":
            where_added = True
            query += " WHERE value = ?"
            attrs += (value,)

        if date or month:
            if where_added:
                query += " AND"
            else:
                query += " WHERE"

            query += " posted_at BETWEEN ? AND ?"
            attrs += cls.__getDateRange(date, month, year)

        con = connect_db()
        with con:
            res = con.execute(query, attrs)

            to_return = []
            for post in res:
                p = Post(post[1], post[2], post[3], post[4], post[6], posted_at=post[5])
                to_return.append(p)
                print p.postUrl

            return to_return

    @classmethod
    def getLeadersByValue(cls, value, date, month, year):
        query = "SELECT user, COUNT(user) as user_occurence, posted_at FROM posts"
        attrs = ()
        where_added = False

        if value and value != "all":
            where_added = True
            query += " WHERE value = ?"
            attrs += (value,)

        if date or month:
            if where_added:
                query += " AND"
            else:
                query += " WHERE"

            query += " posted_at BETWEEN ? AND ?"
            attrs += cls.__getDateRange(date, month, year)

        query += " GROUP BY user ORDER BY user_occurence DESC"

        print query
        con = connect_db()
        with con:
            res = con.execute(query, attrs)

            to_return = []
            for user in res:
                to_return.append({ 'user': user[0], 'posts': user[1] })

            return to_return

    @classmethod
    def __getDateRange(cls, date, month, year):
        start, end = None, None

        if date:
            start = datetime.datetime(year, month, date)
            end = datetime.datetime(year, month, date, 23, 59, 59)
        else:
            start = datetime.datetime(year, month, 1)
            days_in_month = monthrange(year, month)[1]
            end = datetime.datetime(year, month, days_in_month, 23, 59, 59)

        return (start, end)
