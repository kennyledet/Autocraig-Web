# Config
from  flask import Flask, render_template, request, jsonify, Response, url_for
app = Flask(__name__)

import os, datetime, time
import models
import tasks


# Routes
@app.route('/')
def index():
    messages = models.Message.query.all()
    return render_template('index.html', messages=messages, messageCount=len(messages), datetime=datetime.datetime.now())

@app.route('/messages')
def messages():
    messages = models.Message.query.all()
    return render_template('messages.html', messages=messages, messageCount=len(messages), datetime=datetime.datetime.now())

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

@app.route('/_new_message')
def new_message():
    fromAddress    = request.args.get('fromAddress', 0, type=str)
    ccAddress      = request.args.get('ccAddress',   0, type=str)
    subject        = request.args.get('subject',     0, type=str)
    body           = request.args.get('body',        0, type=str)
    reportsEnabled = request.args.get('reportsEnabled', 0, type=str) == 'on'

    try:
        message = models.Message(fromAddress, ccAddress, subject, body, reportsEnabled)
        models.db.session.add(message)
        models.db.session.commit()
    except Exception, e:
        result = 0
    else:
        result = 1
    finally:
        return jsonify(result=result)

"""
@app.route('/_upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'GET':
        # return a list of dicts with info about already available files:
        filesInfo = []
        for fileName in os.listdir('uploads'):
            fileURL  = url_for('uploads', filename=fileName)
            fileSize = os.path.getsize('uploads/{}'.format(fileName))
            fileInfo.append({name: fileName, size: fileSize, url: fileURL})
        return jsonify(files=filesInfo)
    else:
        data     = request.files.get('data_file')
        fileName = data.filename

        save_file(data, fileName)

        fileSize = os.path.getsize('uploads/{}'.format(fileName))
        fileURL  = url_for('uploads', filename=fileName)
        return jsonify(name=fileName, size=fileSize, url=fileURL)
"""

if __name__ == '__main__':
    # Bind to PORT if defined, otherwise default to 5000.
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)