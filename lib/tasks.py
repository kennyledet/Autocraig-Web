import os, time
import models
from celery import Celery
from kennycraig import AutoProcess
from bson.objectid  import ObjectId

BROKER_URL = 'sqla+sqlite:///celerydb.sqlite'
celery     = Celery('tasks', broker=BROKER_URL)

@celery.task
def start_task(selectedMessages, urls, sleepTime, sleepAmt, taskID, userID):
    # Register task and mark as running
    if not len(selectedMessages):  # Do not run if no messages are selected
        return

    db   = models.connection.acw.tasks
    task = db.insert({'taskID': taskID, 'state': 1})
    iteration = 0
    while True:
        # check state
        state = db.find_one({'taskID': taskID})['state']
        if state == 1:  # run
            if iteration <= sleepAmt:
                messages = [models.connection.acw.messages.find_one({u'_id': ObjectId(message_id)}) 
                            for message_id in selectedMessages]
                process  = AutoProcess(urls, messages, userID)
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