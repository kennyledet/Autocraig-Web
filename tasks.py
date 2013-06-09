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

"""
TODO:
this task should poll an endpoint in the Flask webservice I set up
endpoint should tell us whether or not to *pause* the running task by calling time.sleep(1) (while isNecessary)?
isNecessary should be determined by frontend manipulating this endpoint through UI/UX
in order for this to work, we need task ids for the frontend to know what it's
working with 

OR another option could be to have the task set itself up to have itself run again,
and in theory the duplicates prevention would still be effective. We could also pass in report ids to update existing reports
