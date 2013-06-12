# Config
from  flask import Flask, render_template, redirect, request, jsonify, Response, url_for
app = Flask(__name__)

import os, datetime, time
import StringIO
import models
import tasks

# Helper functions
def make_dir(dirname):
    if not os.path.exists(dirname):
        return os.makedirs(dirname, mode=0777)
    else:
        return None

# Routes
@app.route('/')
def index():
    messages = list(models.connection.acw.messages.find({}))
    return render_template('index.html', messages=messages, messageCount=len(messages), datetime=datetime.datetime.now())

@app.route('/messages')
def messages():
    messages = list(models.connection.acw.messages.find({}))
    return render_template('messages.html', messages=messages, messageCount=len(messages), datetime=datetime.datetime.now())

@app.route('/reports')
def reports():
    messages = list(models.connection.acw.messages.find({}))
    reports  = list(models.connection.acw.reports.find({}))
    return render_template('reports.html', reports=reports, messages=messages, messageCount=len(messages))

@app.route('/_update_task')
def update_task():
    ''' Set running Celery task to a new state '''
    taskID = request.args.get('taskID', 0, type=str)
    state  = request.args.get('state', 0, type=int)

    models.connection.acw.tasks.update({'taskID': taskID}, {'$set': {'state': state}})

    return jsonify(result=1)

@app.route('/_start')
def start():
    ''' Start new task '''
    selectedMessages = request.args.get('selectedMessages', 0, type=str)[0:-1].split(',')
    urls             = request.args.get('urls',             0, type=str).split('\n')
    sleepTime        = request.args.get('sleepTime',        0, type=int)
    sleepAmt         = request.args.get('sleepAmt',         0, type=int)

    if not selectedMessages or not urls:
        result = 0
        taskID = None
    else:
        result = 1
        taskID = str(time.time())  # record taskID as timestamp
        tasks.start_task.delay(selectedMessages, urls, sleepTime, sleepAmt, taskID)

    return jsonify(result=result, taskID=taskID)

@app.route('/_new_message', methods=['POST', 'GET'])
def new_message():
    fromAddress    = request.form['fromAddress']
    ccAddress      = request.form['ccAddress']
    subject        = request.form['subject']
    body           = request.form['body']
    reportsEnabled = request.form['reportsEnabled'] == 'on'
    reportAddress  = request.form['reportAddress']

    # Parse .txt file of from addresses if uploaded
    fromAddrList   = request.files.get('fromAddressList')
    if fromAddrList.stream.getvalue():
        fromAddrList = fromAddrList.stream.getvalue().split('\n')
        if '' in fromAddrList: fromAddrList.remove('')
        fromAddress  = ', '.join(fromAddrList)

    try: # Save message in db
        models.connection.acw.messages.insert({'created_at': datetime.datetime.now(), 'fromAddress': fromAddress, 'ccAddress': ccAddress,
            'subject': subject, 'body': body, 'reportsEnabled': reportsEnabled, 'reportAddress': reportAddress })

        # Save uploads in message attachments folder
        basePath = os.path.dirname(os.path.realpath(__file__))
        messageAttachmentsFolder = '{}/uploads/{}/attachments/'.format(basePath, message.id)
        make_dir(messageAttachmentsFolder)

        for attachment in request.files.getlist('attachments'):
            savePath = '{}{}'.format(messageAttachmentsFolder, attachment.filename)
            attachment.save(savePath)

    except Exception, e:
        print e        
    finally:
        return redirect(url_for('messages'))



if __name__ == '__main__':
    # Bind to PORT if defined, otherwise default to 5000.
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)