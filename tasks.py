import os
import models
from   celery import Celery

BROKER_URL = 'redis://localhost:6379/0'
celery     = Celery('tasks', broker=BROKER_URL)

@celery.task
def autocraig(selectedMessages, sleepTime, sleepAmt, urls):
    for url in urls:
        print 'Scraping and sending to postings in {}..'.format(url)
        for messageId in selectedMessages:
            print 'Sending message {}'.format(messageId)
            message = models.Message.query.filter_by(id=messageId).first()
            ## start automation
