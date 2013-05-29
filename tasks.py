import os
from celery import Celery
import models
BROKER_URL = 'redis://localhost:6379/0'
celery     = Celery('tasks', broker=BROKER_URL)

@celery.task
def autocraig(selectedMessages, sleepTime, urls):
    for url in urls:
        print 'Scraping and sending to postings in {}..'.format(url)
        for messageId in selectedMessages:
            print 'Sending message {}'.format(messageId)
            message = models.Message.query.filter_by(id=messageId).first()
            ## start automation
