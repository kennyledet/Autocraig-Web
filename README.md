Autocraig-Web
=============
Automated Craigslist Reply Tool

This tool allows for the scraping and replying to of Craigslist postings based on listings URLs (such as searches).

It started out as an extension of [autocraig](https://github.com/alexksikes/autocraig to provide a web interface), but I quickly realized that this core script had many flaws and didn't even work fully, so I rewrote it as kennycraig.

Installation Instructions
--------------------------
This is a Python web app built with the amazing Flask framework. You'll need Python and Flask installed.
It also has some additional Python module requirements are contained in the docs/requirements.txt.

You can easily install ALL requirements, including Flask, with pip by running

    pip install -r requirements.txt

To install pip, see: http://www.pip-installer.org/en/latest/installing.html

This web app uses MongoDB as the primary database. Please run a Mongo server on port 27017 or change the port setting in lib/models.py

To install MongoDB, see: http://docs.mongodb.org/manual/tutorial/install-mongodb-on-red-hat-centos-or-fedora-linux/

The other database is used for running a Celery queue, is handled by sqlite3, and is automatically created.

Now, set your mail server settings in lib/settings.py

Now, to run the script effectively you will need to start 2 servers

The first is the Flask server. It should be running on port 5000 by default

    python app.py -b 0.0.0.0

The second is a Celery server. Celery handles the email sending tasks.
By running the pip command above you already have everything necessary to run it.
Run the Celery server with

    celery -A lib.tasks worker --loglevel=info

Usage Instructions
==================

Control Panel - New Task
------------------------
Use this page to start new automation tasks

Messages: The left panel is a clickable list of Messages containing some basic info about each one.
Click all messages you want to use for the task, then click Start to begin.

Scrape URLS: Paste in your craigslist urls here. the script will get all posts from them
Here you can also tell the script to run every x seconds, x times. Leave both at 0 to have the script only run once.
Once a task is started, you may Pause, Continue or Stop it. Once it is stopped it cannot be paused/continued, only started again
as a new task.


Control Panel - Messages
------------------------
Use this page to view, edit and create messages to send to craigslist ad posters.

You can upload a list of From addresses which the script will randomly choose from each time the message is used
, one per line, or separate a list of From addresses by comma and space..you can also simply choose a single address

Each message in the list view has an Edit button beneath the message content. Click this to edit the message details.

