from  flask import Flask, render_template, request, jsonify, Response
app = Flask(__name__)

import os, datetime
import models
import tasks

# Routes
@app.route('/')
def index():
    messages     = models.Message.query.all()
    messageCount = len(messages)
    return render_template('index.html', messages=messages, messageCount=messageCount, datetime=datetime.datetime.now())

@app.route('/messages')
def messages():
    messages     = models.Message.query.all()
    messageCount = len(messages)
    return render_template('messages.html', messages=messages, messageCount=messageCount, datetime=datetime.datetime.now())

@app.route('/_go')
def go():
    selectedMessages = request.args.get('selectedMessages', 0, type=str)[0:-1].split()
    urls             = request.args.get('urls',             0, type=str).split('\n')

    sleepTime        = request.args.get('sleepTime',        0, type=int)
    sleepAmt         = request.args.get('sleepAmt',         0, type=int)

    #tasks.autocraig.delay(selectedMessages, sleepTime, urls)

    return jsonify()

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



if __name__ == '__main__':
    # Bind to PORT if defined, otherwise default to 5000.
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)