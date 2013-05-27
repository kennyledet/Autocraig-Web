from flask import Flask, render_template, request, jsonify, Response
from flask.ext.sqlalchemy import SQLAlchemy

import datetime
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/data.db'
db  = SQLAlchemy(app)

# Models
class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created_at  = db.Column(db.DateTime())

    toAddress   = db.Column(db.String(255))
    fromAddress = db.Column(db.String(255))
    subject     = db.Column(db.String(255))
    body        = db.Column(db.Text())

    reportsEnabled = db.Column(db.Boolean())

    def __init__(self, toAddress, fromAddress, subject, body, reportsEnabled):
    	self.created_at  = datetime.datetime.now()
        self.toAddress   = toAddress
        self.fromAddress = fromAddress
        self.subject     = subject
        self.body 		 = body
        self.reportsEnabled = reportsEnabled

    def __repr__(self):
        return '<Subject %r>' % self.subject

# Routes
@app.route('/')
def index():
	return render_template('index.html')

@app.route('/go')
def go():
	urls = request.args.get('urls', 0, type=str)
	#print urls.split('\n')

	return jsonify(result=1)

@app.route('/messages')
def messages():
	return render_template('messages.html')

@app.route('/_new_message')
def new_message():
	toAddress   = request.args.get('toAddress',   0, type=str)
	fromAddress = request.args.get('fromAddress', 0, type=str)
	subject     = request.args.get('subject',     0, type=str)
	body        = request.args.get('body', 		  0, type=str)
	reportsEnabled = request.args.get('reportsEnabled', 0, type=str)



	return jsonify(result=result)



if __name__ == '__main__':
    # Bind to PORT if defined, otherwise default to 5000.
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)