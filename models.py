import datetime
from app import db

class Message(db.Document):
    created_at  = db.DateTimeField(default=datetime.datetime.now, required=True)
    toAddress   = db.StringField(max_length=255)
    fromAddress = db.StringField(max_length=255)
    subject     = db.StringField()
    body        = db.StringField()

    def __unicode__(self):
        return self.subject

    meta = {
        'allow_inheritance': True,
        'indexes': ['-created_at', 'slug'],
        'ordering': ['-created_at']
    }
