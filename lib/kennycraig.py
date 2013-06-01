# Original Author : Alex Ksikes
# Modifications   : Kendrick Ledet


import re, urllib2, datetime, random
import models
from mailer import Mailer, Message
from bs4    import BeautifulSoup
from itertools import chain

class AutoProcess(object):
    def __init__(self, urls, messages):
        self.urls     = urls
        self.messages = messages
        self.reports  = models.connection['acw'].reports

    def start(self):
        posts     = list(chain.from_iterable([self.scrape_posts(url) for url in self.urls]))
        tmpReport = {}

        print 'Using messages: '
        print self.messages
        print 'Found posts: '
        print posts

        for post in posts:
            models.add_to_dupes(post['id'])
            message = random.choice(self.messages)  # choose random message to send to this ad

            # Email ad poster
            # self.send_email(message.fromAddress, post['toAddress'], message.subject, message.body, message.ccAddress)

            # Insert into tmp report as craigslist id -> message sent
            tmpReport.update({str(post['id']) : message.id})

        # for testing
        models.connection['acw'].dupes.remove()

        # Email digest to user
        primaryFromAddress = self.messages[0].fromAddress
        self.send_email(primaryFromAddress, primaryFromAddress, 'craigslist-auto-%s' % datetime.datetime.now(), self.digest(posts), CC=None, HTML=True)

        # Print digest to stdout
        # print self.digest(self.posts)

        # Final report
        reportDict = {'created_at': datetime.datetime.now()}
        reportDict.update(tmpReport)

        print reportDict
        report     = self.reports.insert(reportDict)


    def scrape_posts(self, url):
        mailPattern   = re.compile(r'[\w\-][\w\-\.]*@[\w\-][\w\-\.]+[a-zA-Z]{1,4}', re.I)
        postIdPattern = re.compile(r'Posting ID: (\d+)')

        baseUrl = url.split('/')[2] if not url.split('/')[1] else url.split('/')[0]
        posts   = []

        soup = BeautifulSoup(urllib2.urlopen(url).read())

        postsBlock = soup.find('blockquote',  id='toc_rows')
        postRows   = postsBlock.find_all('p', class_='row' )
        postLinks  = [row.contents[1]['href'] for row in postRows]

        print postLinks

        for post in postLinks:
            print 'Scraping {}'.format(post)
            postUrl = 'http://{}{}'.format(baseUrl, post)
            html    = urllib2.urlopen(postUrl).read()
            soup    = BeautifulSoup(html)

            postId  = re.findall(postIdPattern, html)[0]
            if not postId or postId in models.get_dupes(): continue

            models.add_to_dupes(postId)

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
        for post in posts:
            html += '<a href="{}">{}</a>\n'.format(post['url'], post['id'])

        #print html
        return html


    def send_email(self, fromAddress, toAddress, subject, body, CC=None, HTML=False):
        sender  = Mailer(host='smtp.gmail.com', port=587, use_tls=True, usr='kendrickledet', pwd='yMHJ0e78gMbDtkV')
        message = Message(From=fromAddress, To=toAddress, Subject=subject, CC=CC, charset="utf-8")

        if HTML:
            message.Html = body
        else:
            message.Body = body

        #message.attach("kitty.jpg")
        sender.send(message)

    
def main():
    pass
      
if __name__ == '__main__':
    main()