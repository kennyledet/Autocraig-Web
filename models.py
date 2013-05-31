import datetime
import itertools
from flask.ext.sqlalchemy import SQLAlchemy
from mongokit import Connection, Document
from app      import app

# Database config and init
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/data.db'
db  = SQLAlchemy(app)

MONGODB_HOST = 'localhost'
MONGODB_PORT = 27017

connection = Connection()

# Models
class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created_at  = db.Column(db.DateTime())

    fromAddress = db.Column(db.String(255))
    subject     = db.Column(db.String(255))
    body        = db.Column(db.String(255))
    ccAddress   = db.Column(db.String(255))

    reportsEnabled = db.Column(db.Boolean())

    def __init__(self, fromAddress, ccAddress, subject, body, reportsEnabled):
        self.created_at  = datetime.datetime.now()
        self.fromAddress = fromAddress
        self.ccAddress   = ccAddress
        self.subject     = subject
        self.body        = body
        self.reportsEnabled = reportsEnabled

    def __repr__(self):
        return '<Subject %r>' % self.subject

def new_report(messages, ads):  # messages are Message ids, ads are craigslist posting ids
    collection = connection['acw'].reports
    collection.insert({'created_at': datetime.datetime.now(), 'messages': messages, 'ads': ads})

def add_to_dupes(craigslist_id):
    collection = connection['acw'].dupes
    collection.insert({'craigslist_id': craigslist_id})

def get_dupes():
    collection = connection['acw'].dupes
    dupes = [dupe['craigslist_id'] for dupe in list(collection.find())]

    return dupes
