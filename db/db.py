import sqlite3
import datetime
from contextlib import closing
from flask import current_app as app

def connect_db():
    return sqlite3.connect('./db/valuebot.sqlite3')

def init_db():
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

        try:
            with con:
                con.execute(
                    "insert into posts(user, poster, value, text, posted_at) values (?, ?, ?, ?, ?)",
                    (self.user, self.poster, self.value, self.text, self.posted_at))
                return True
        except:
            return False

    @classmethod
    def getPostsByUser(cls, user, date, year):
        print "getting posts"

    @classmethod
    def getPostsByValue(cls, value, date, year):
        print "getting posts"

    @classmethod
    def getLeadersByValue(cls, value, date, year):
        print "getting leaders"