import os
import models
from celery import Celery
from lib.kennycraig import AutoProcess

BROKER_URL = 'redis://localhost:6379/0'
celery     = Celery('tasks', broker=BROKER_URL)

@celery.task
def start_task(selectedMessages, urls, sleepTime, sleepAmt):
    messages = []
    for messageId in map(int, selectedMessages):
        print messageId
        messages.append(models.Message.query.filter_by(id=messageId).first())

    print 'Using messages: '
    print messages

    process = AutoProcess(urls, messages)
    process.start()


