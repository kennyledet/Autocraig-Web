import os, time
import models
from celery import Celery
from lib.kennycraig import AutoProcess

BROKER_URL = 'sqla+sqlite:///celerydb.sqlite'
celery     = Celery('tasks', broker=BROKER_URL)

@celery.task
def start_task(selectedMessages, urls, sleepTime, sleepAmt, taskID):
    # Register task and mark as running
    db   = models.connection.acw.tasks
    task = db.insert({'taskID': taskID, 'state': 1})
    iter = 0
    while True:
        # check state
        state = db.find_one({'taskID': taskID})['state']
        if state == 1:  # run
            if iteration <= sleepAmt:
                messages = [models.Message.query.filter_by(id=messageId) for messageId in map(int, selectedMessages)]
                process  = AutoProcess(urls, messages)
                process.start()
                time.sleep(sleepTime)
                iteration += 1
            else:
                db.update({'taskID': taskID}, {'$set': {'state': 0}})
        elif state == 0:  # quit
            return
        elif state == -1:  # pause
            while db.find_one({'taskID': taskID})['state'] == -1:
                pass