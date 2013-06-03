# Config
from  flask import Flask, render_template, request, jsonify, Response, url_for
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
    messages = models.Message.query.all()
    return render_template('index.html', messages=messages, messageCount=len(messages), datetime=datetime.datetime.now())

@app.route('/messages')
def messages():
    messages = models.Message.query.all()
    return render_template('messages.html', messages=messages, messageCount=len(messages), datetime=datetime.datetime.now())

@app.route('/reports')
def reports():
    messages = models.Message.query.all()

    conn    = models.connection['acw'].reports
    reports = list(conn.find())
    print reports
    return render_template('reports.html', reports=reports, messages=messages, messageCount=len(messages))

@app.route('/_go')
def go():
    selectedMessages = request.args.get('selectedMessages', 0, type=str)[0:-1].split(',')
    urls             = request.args.get('urls',             0, type=str).split('\n')

    sleepTime        = request.args.get('sleepTime',        0, type=int)
    sleepAmt         = request.args.get('sleepAmt',         0, type=int)

    if not selectedMessages:
        result = 0
    else:
        tasks.start_task.delay(selectedMessages, urls, sleepTime, sleepAmt)
        result = 1

    return jsonify(result=result)

@app.route('/_new_message', methods=['POST', 'GET'])
def new_message():
    fromAddress    = request.form['fromAddress']
    ccAddress      = request.form['ccAddress']
    subject        = request.form['subject']
    body           = request.form['body']
    reportsEnabled = request.form['reportsEnabled'] == 'on'

    attachments     = request.files.getlist('attachments')
    fromAddressList = request.files.get('fromAddressList')
    if fromAddressList:
        fromAddressList.stream.getvalue().split('\n')
    #print dir(fromAddressList)
    #with open(fromAddressList.stream, 'r') as listFile:
    #    print listFile

    basePath = os.path.dirname(os.path.realpath(__file__))
    
    try: # Save message in db
        message = models.Message(fromAddress, ccAddress, subject, body, reportsEnabled)
        models.db.session.add(message)
        models.db.session.commit()

        # Save uploads
        messageAttachmentsFolder = '{}/uploads/{}/attachments/'.format(basePath, message.id)
        make_dir(messageAttachmentsFolder)
        for attachment in attachments:
            savePath = '{}{}'.format(messageAttachmentsFolder, attachment.filename)
            attachment.save(savePath)

    except Exception, e:
        print e
        result = 0
    else:
        result = 1
    finally:
        return jsonify(result=result)



if __name__ == '__main__':
    # Bind to PORT if defined, otherwise default to 5000.
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)