# Config
import os, datetime, time, StringIO
import tasks, models
import lib
from   lib import helpers

from flask import Flask, render_template, redirect, request, jsonify, Response, url_for, session
from bson.objectid   import ObjectId
from flask.ext.login import LoginManager

app = Flask(__name__)
app.secret_key = 'WT3SDz0RBvffB0s'

# Routes
@app.route('/')
def index():
    #print session
    ''' Index is Login/Registration page '''
    if session['logged_in']:
        return redirect(url_for('new_task'))
    return render_template('index.html', datetime=datetime.datetime.now())


@app.route('/login', methods=['POST'])
def login():
    e = None
    email, password = request.form['email'], request.form['password']
    print email

    user = models.connection.acw.users.find_one({'email': email})
    if not user:
        session['logged_in'] = False
        session['user'] = None
        e = 'No user with this email'
        return redirect('/')
    if helpers.hash_pass(password) == user['password']:  # Authenticated
        session['logged_in'] = True
        session['user'] = user['_id']
        return redirect('/new_task')
    else:
        session['logged_in'] = False
        session['user'] = None
        e = 'Password incorrect'
        return redirect('/')
    
    return redirect('/new_task')


@app.route('/logout', methods=['GET'])
def logout():
    session['logged_in'] = False
    session['user']      = None    
    return redirect('/')


@app.route('/register', methods=['POST'])
def register():
    models.connection.acw.users.insert({'email': request.form['email'], 'password': helpers.hash_pass(request.form['password']), 
        'role': 'member'})
    return redirect('/')


@app.route('/new_task')
def new_task():
    if not session['logged_in']:
        return redirect('/')

    messages = list(models.connection.acw.messages.find({'user': session['user']}))
    return render_template('new_task.html', messages=messages, messageCount=len(messages), datetime=datetime.datetime.now())


@app.route('/messages')
def messages():
    if not session['logged_in']:
        return redirect('/')

    messages = list(models.connection.acw.messages.find({'user': session['user']}))
    return render_template('messages.html', messages=messages, messageCount=len(messages), datetime=datetime.datetime.now())


@app.route('/reports')
def reports():
    if not session['logged_in']:
        return redirect('/')

    messages = list(models.connection.acw.messages.find({'user': session['user']}))
    reports  = list(models.connection.acw.reports.find({'user': session['user']}))
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
        tasks.start_task.delay(selectedMessages, urls, sleepTime, sleepAmt, taskID, session['user'])

    return jsonify(result=result, taskID=taskID)


@app.route('/_new_message', methods=['POST', 'GET'])
def new_message():
    fromAddress    = request.form['fromAddress']
    ccAddress      = request.form['ccAddress']
    subject        = request.form['subject']
    body           = request.form['body']
    reportsEnabled = True if request.form.get('reportsEnabled') else False
    reportAddress  = request.form['reportAddress']

    # Parse .txt file of from addresses if uploaded
    fromAddrList   = request.files.get('fromAddressList')
    if fromAddrList.stream.getvalue():
        fromAddrList = fromAddrList.stream.getvalue().split('\n')
        if '' in fromAddrList: fromAddrList.remove('')
        fromAddress  = ', '.join(fromAddrList)

    try: # Save message in db
        models.connection.acw.messages.insert({'created_at': datetime.datetime.now(), 'fromAddress': fromAddress, 'ccAddress': ccAddress,
            'subject': subject, 'body': body, 'reportsEnabled': reportsEnabled, 'reportAddress': reportAddress, 'user': session['user'] })

        # Save uploads in message attachments folder
        basePath = os.path.dirname(os.path.realpath(__file__))
        messageAttachmentsFolder = '{}/uploads/{}/attachments/'.format(basePath, message['_id'])
        helpers.make_dir(messageAttachmentsFolder)

        for attachment in request.files.getlist('attachments'):
            savePath = '{}{}'.format(messageAttachmentsFolder, attachment.filename)
            attachment.save(savePath)

    except Exception, e:
        print e        
    finally:
        return redirect(url_for('messages'))


@app.route('/_edit_message', methods=['POST'])
@app.route('/_edit_message/<_id>', methods=['GET'])
def edit_message(_id=None):
    if request.method != 'POST':
        messages = list(models.connection.acw.messages.find({'user':session['user']}))
        message  = models.connection.acw.messages.find_one({u'_id': ObjectId(_id)})
        return render_template('edit_message.html', messages=messages, message=message, messageCount=len(messages), datetime=datetime.datetime.now())
    else:
        fromAddress    = request.form['fromAddress']
        ccAddress      = request.form['ccAddress']
        subject        = request.form['subject']
        body           = request.form['body']
        reportsEnabled = True if request.form.get('reportsEnabled') else False
        reportAddress  = request.form['reportAddress']
        _id = request.form['_id']

        # Parse .txt file of from addresses if uploaded
        fromAddrList   = request.files.get('fromAddressList')
        if fromAddrList.stream.getvalue():
            fromAddrList = fromAddrList.stream.getvalue().split('\n')
            if '' in fromAddrList: fromAddrList.remove('')
            fromAddress  = ', '.join(fromAddrList)

        try: # Save message in db
            db = models.connection.acw.messages
            db.update({'_id': ObjectId(_id)}, {'$set': {'fromAddress': fromAddress, 'ccAddress': ccAddress,
                'subject': subject, 'body': body, 'reportsEnabled': reportsEnabled, 'reportAddress': reportAddress }})

            # Save uploads in message attachments folder
            basePath = os.path.dirname(os.path.realpath(__file__))
            messageAttachmentsFolder = '{}/uploads/{}/attachments/'.format(basePath, message['_id'])
            helpers.make_dir(messageAttachmentsFolder)

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