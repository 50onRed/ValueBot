import sqlite3
import datetime
from calendar import monthrange
from contextlib import closing
from flask import current_app as app

def connect_db():
    return sqlite3.connect('./db/valuebot.sqlite3')

def init_db():
    # TODO: FIX THIS
    with app.app_context():
        with closing(connect_db()) as db:
            with app.open_resource('./db/schema.sql', mode='r') as f:
                db.cursor().executescript(f.read())
            db.commit()

class Post():
    def __init__(self, user, poster, value, text):
        self.user = user
        self.poster = poster
        self.value = value
        self.text = text
        self.posted_at = datetime.datetime.now()

    def save(self):
        con = connect_db()

        with con:
            con.execute(
                "INSERT INTO POSTS(user, poster, value, text, posted_at) VALUES (?, ?, ?, ?, ?)",
                (self.user, self.poster, self.value, self.text, self.posted_at))
            return True

    @classmethod
    def getPostsByUser(cls, user, date, month, year):
        query = "SELECT * FROM POSTS WHERE user = ?"
        attrs = (user,)

        if date or month:
            query += " AND posted_at BETWEEN ? AND ?"
            attrs += cls.__getDateRange(date, month, year)

        con = connect_db()
        with con:
            res = con.execute(query, attrs)

            to_return = []
            for post in res:
                to_return.append(Post(post[1], post[2], post[3], post[4]))

            return to_return

    @classmethod
    def getPostsByValue(cls, value, date, month, year):
        query = "SELECT * FROM POSTS"
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
                to_return.append(Post(post[1], post[2], post[3], post[4]))

            return to_return

    @classmethod
    def getLeadersByValue(cls, value, date, month, year):
        print "getting leaders"

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
