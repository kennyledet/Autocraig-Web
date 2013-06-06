import os, time
import models
from celery import Celery
from lib.kennycraig import AutoProcess

BROKER_URL = 'sqla+sqlite:///celerydb.sqlite'
celery     = Celery('tasks', broker=BROKER_URL)

@celery.task
def start_task(selectedMessages, urls, sleepTime, sleepAmt):
    iter = 0
    while iter <= int(sleepAmt):
        messages = []
        for messageId in map(int, selectedMessages):
            messages.append(models.Message.query.filter_by(id=messageId).first())

        process = AutoProcess(urls, messages)
        process.start()

        time.sleep(int(sleepTime))

        iter += 1
