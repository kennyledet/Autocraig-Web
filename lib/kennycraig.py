# Original Author : Alex Ksikes
# Modifications   : Kendrick Ledet


import re, urllib2, datetime, random, os
import models
from mailer import Mailer, Message
from bs4    import BeautifulSoup
from itertools import chain

class AutoProcess(object):
    def __init__(self, urls, messages):
        self.urls     = urls
        self.messages = messages
        self.reports  = models.connection.acw.reports
        self.tasks    = models.connection.acw.tasks
        self.dupes    = models.connection.acw.dupes

        self.uploadsBasePath = os.path.abspath(os.path.join(os.path.dirname( __file__ ), '..', 'uploads'))

    def start(self):
        # Scrape posts
        posts     = list(chain.from_iterable([self.scrape_posts(url) for url in self.urls]))
        tmpReport = {}

        print 'Using messages: {}'.format(self.messages)
        print 'Found posts: {}'.format(posts)

        for post in posts:
            # Check current task state
            state = self.tasks.find_one({'taskID': taskID})['state']
            if state == 0:  # quit
                break
            elif state == -1:  # pause
                while self.tasks.find_one({'taskID': taskID})['state'] == -1:
                    pass

            # Duplication prevention
            if post['id'] in [dupe['id'] for dupe in list(self.dupes.find())]:
                continue
            else:
                self.dupes.insert({'id': post['id']})

            message = random.choice(self.messages)

            if ', ' in message['fromAddress']:  # choose random from address from comma sep. list
                message['fromAddress'] = random.choice(message['fromAddress'].split(', '))

            #self.send_reply(message, post['toAddress'])

            if message['reportsEnabled']:
                # Add to task report
                tmpReport.update({post['url'].replace('.','*') : {'id': message['_id'], 'subject': message['subject'],
                    'body': message['body']}})

                # Report to report email


        # for testing
        ##self.dupes.remove()

        # Email digest to user
        #self.send_digest(self.messages[0]['from'], self.digest(posts))

        # Final report
        reportDict = {'created_at': datetime.datetime.now(), 'report': tmpReport}
        report     = self.reports.insert(reportDict)

        print reportDict, report

    def scrape_posts(self, url):
        mailPattern   = re.compile(r'[\w\-][\w\-\.]*@[\w\-][\w\-\.]+[a-zA-Z]{1,4}', re.I)
        postIdPattern = re.compile(r'Posting ID: (\d+)')

        baseUrl = url.split('/')[2] if not url.split('/')[1] else url.split('/')[0]
        posts   = []

        soup = BeautifulSoup(urllib2.urlopen(url).read())

        postsBlock = soup.find('blockquote',  id='toc_rows')
        postRows   = postsBlock.find_all('p', class_='row' )
        postLinks  = [row.contents[1]['href'] for row in postRows]

        for post in postLinks:
            print 'Scraping {}'.format(post)
            postUrl = 'http://{}{}'.format(baseUrl, post)
            html    = urllib2.urlopen(postUrl).read()

            postId  = re.findall(postIdPattern, html)[0]
            print 'Found {}'.format(postId)
            if not postId or postId in models.get_dupes(): 
                continue

            models.add_to_dupes(postId)

            soup      = BeautifulSoup(html)
            postTitle = soup.find('h2', class_='postingtitle').text
            postBody  = soup.find('section', id='postingbody').text

            emails    = re.findall(mailPattern, html)
            toAddress = emails[0]
            for email in emails:
                if 'craigslist' not in email: toAddress = email  # non-standard cl reply address, use this

            posts.append({'url': postUrl, 'id': postId, 'title': postTitle, 'body': postBody, 'toAddress': toAddress})

        return posts

    def digest(self, posts):
        html = ''
        for post in posts: html += '<a href="{}">{}</a>\n'.format(post['url'], post['id'])
        return html

    def send_reply(self, message, toAddress):
        sender = Mailer(host='mail.banglamafia.com', port=25, usr='bangla', pwd='Sn"IaaCi')
        email  = Message(From=message['fromAddress'], To=toAddress, Subject=message['subject'], CC=message['ccAddress'])
        email.Html = message.body

        messageUploads = '{}/{}/attachments/'.format(self.uploadsBasePath, message['_id'])

        for upload in os.listdir(messageUploads):
            email.attach('{}{}'.format(messageUploads, upload))

        print 'sending', message['subject'], ' to', toAddress
        
        sender.send(email)

    def send_digest(self, digestAddress, digest):
        sender = Mailer(host='mail.banglamafia.com', port=25, usr='bangla', pwd='Sn"IaaCi')
        email  = Message(From=digestAddress, To=digestAddress, Subject='craigslist-auto-{}'.format(datetime.datetime.now()))
        email.Html = digest

        sender.send(email)
