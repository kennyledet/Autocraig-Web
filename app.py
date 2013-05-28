from flask import Flask, render_template, request, jsonify, Response
import os

app = Flask(__name__)

import models

# Routes
@app.route('/')
def index():
    messages = models.Message.query.all()
    return render_template('index.html', messages=messages)

@app.route('/messages')
def messages():
    return render_template('messages.html')

@app.route('/_go')
def go():
    urls = request.args.get('urls', 0, type=str)
    return jsonify()

@app.route('/_new_message')
def new_message():
    fromAddress = request.args.get('fromAddress', 0, type=str)
    print fromAddress
    subject     = request.args.get('subject',     0, type=str)
    body        = request.args.get('body',        0, type=str)
    reportsEnabled = True if request.args.get('reportsEnabled', 0, type=str) == 'on' else False

    try:
        message = models.Message(fromAddress, subject, body, reportsEnabled)
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