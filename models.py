import datetime
from flask.ext.sqlalchemy import SQLAlchemy

# Database config and init
from app import app
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/data.db'
db  = SQLAlchemy(app)

# Models
class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created_at  = db.Column(db.DateTime())

    toAddress   = db.Column(db.String(255))
    fromAddress = db.Column(db.String(255))
    subject     = db.Column(db.String(255))
    body        = db.Column(db.Integer)

    reportsEnabled = db.Column(db.Boolean())

    def __init__(self, toAddress, fromAddress, subject, body, reportsEnabled):
        self.created_at  = datetime.datetime.now()
        self.toAddress   = toAddress
        self.fromAddress = fromAddress
        self.subject     = subject
        self.body        = body
        self.reportsEnabled = reportsEnabled

    def __repr__(self):
        return '<Subject %r>' % self.subject
