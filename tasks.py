import os, time
import models
from celery import Celery
from lib.kennycraig import AutoProcess

BROKER_URL = 'sqla+sqlite:///celerydb.sqlite'
celery     = Celery('tasks', broker=BROKER_URL)

@celery.task
def start_task(selectedMessages, urls, sleepTime, sleepAmt, taskID):
    # Register taskID in MongoDB collection and mark as running
    conn  = models.connection['acw'].tasks  
    tasks = list(conn.find())
    conn.insert({'taskID': taskID, 'running': True})

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
start_task should poll the MongoDB collection directly
this polling should tell us whether or not to *pause* the running task by calling time.sleep(1) (while isNecessary)?
isNecessary should be determined by frontend manipulating this endpoint through UI/UX

The frontend needs a way to update the collection via endpoint
"""