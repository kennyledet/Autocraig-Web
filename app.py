from flask import Flask, render_template, request, jsonify, Response
#from flask.ext.security.datastore.mongoengine import MongoEngineUserDatastore
#from models import *
import os

app = Flask(__name__)
app.config["MONGODB_SETTINGS"] = {'DB': "autocraig"}
app.config["SECRET_KEY"] = "k3l432l3lj"

#db = MongoEngine(app)

@app.route('/')
def index():
	return render_template('index.html')

@app.route('/go')
def go():
	urls = request.args.get('urls', 0, type=str)
	print urls
	print urls.split('\n')

	return jsonify(result=1)

@app.route('/messages')
def messages():
	return render_template('messages.html')

@app.route('/_new_message')
def new_message():
	fromAddress = request.args.get('fromAddress', 0, type=str)
	print fromAddress

	return jsonify(t=fromAddress)

if __name__ == '__main__':
    # Bind to PORT if defined, otherwise default to 5000.
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)