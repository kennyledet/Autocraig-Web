# Original Author : Alex Ksikes
# Modifications   : Kendrick Ledet
# - Gets the same job done in about 50 (nonredundant) less lines of code
# - Replaces Alex K's send_mail.py with mailer module
# requires 
# - send_mail.py
# - html2text.py

import re, urllib, urlparse, datetime
import html2text

from mailer import Mailer, Message


class MainProc(object):
    """Main process for running kennycraig"""
    def __init__(self, config={
                            'FROM_EMAIL'  : '',
                            'REPLY_EMAIL' : '',
                            'TO_EMAIL' : '',
                            'CC_EMAIL' : '',
                            'REPORTS_ENABLED': True}):

        self.config = config
        self.config.update({'NUM_DAYS'  : 3,
                            'NUM_PAGES' : 3,
                            'DEEP'  : 1,
                            'VALID' : 15,
                            'SIMILARITY' : 0.9})
        self.duplicates_file = 'autocraig.duplicates'
    
    def start(self, search_url, msg, quiet=False):
        duplicates = self.load_duplicates()
        posts      = self.get_all_posts(search_url, duplicates)

        self.add_to_duplicates(posts)

        # report an hrml if needed
        if self.config['REPORTS_ENABLED']:
            print 1
            self.email_digest(posts)
        # email all authors
        self.email_authors(posts, msg)
        # output result to stdout
        if not quiet:
            print self.report(posts),


    def load_duplicates(self):
        duplicates = {}
        data = open(self.duplicates_file).read().split('@#@#@')
        for (craig_id, text) in zip(data[0::2], data[1::2]):
            duplicates[craig_id] = text
        return duplicates


    def add_to_duplicates(self, posts):
        o = open(self.duplicates_file, 'a')
        for post in posts:
            if not post: continue
            o.write(post['craig_id'] + '@#@#@' + post['description_text'] + '@#@#@')
        o.close()


    def get_all_posts(self, search_url, duplicates):
        posts = []
        for u in self.get_post_urls(search_url):
            post = self.get_post(urlparse.urljoin(search_url, u))
            if not post: continue
            if (not duplicates or not self.is_duplicates(duplicates, post)):
                posts.append(post)
        return posts


    def get_post_urls(self, search_url):
        html = urllib.urlopen(search_url).read()
        return re.compile('\s\-.*?<a\shref="(.*?)">.*?</a>').findall(html)


    def get_post(self, post_url):
        print post_url

        p_post = {'reply' : re.compile('mailto:(.*?)\?', re.I), 
                  'description_html' : re.compile('(<h2>.*?postingid:\s[0-9]+)<br>', re.I|re.S)}
        post, html = {}, urllib.urlopen(post_url).read()
        post['url'] = post_url
        m = re.findall('/([0-9]+)\.html', post_url)
        post['craig_id'] = m[0] if m else False

        print post['craig_id']
        if not post['craig_id']:
            return None
        for type, p in p_post.items():
            txt = p.findall(html)
            if txt:
                txt = txt[0]
            else:
                txt = ''
            post[type] = txt
        try:
            post['description_text'] = html2text.html2text(post['description_html']).encode('utf-8')
        except:
            post['description_text'] = ''
        post['phone'], post['email_alternative'] = self.analyze(post['description_text'])
        return post


    def email_authors(self, posts, msg):
        for post in posts:
            print 'emailing {}'.format(post)
            self.send_email(self.config['FROM_EMAIL'], post['reply'], 'Regarding your listing', msg, CC=self.config['CC_EMAIL'])
            """
            send_mail(to_addrs=post['reply'], from_addrs=self.config['FROM_EMAIL'], 
                      cc_addrs=self.config['CC_EMAIL'].split(','), message=msg, subject=post['title'])
            """


    def email_digest(self, posts):
        if not posts: return
        self.send_email(self.config['FROM_EMAIL'], self.config['TO_EMAIL'], 'craigslist-auto-%s' % datetime.datetime.now(), self.report(posts, html=True), CC=self.config['CC_EMAIL'], HTML=True)
        """
        send_mail(to_addrs=self.config['TO_EMAIL'].split(','), cc_addrs=self.config['CC_EMAIL'].split(','), 
                  message=self.report(posts, html=True), from_addr=self.config['FROM_EMAIL'],
                  content_type='text/html', subject='craigslist-auto-%s' % datetime.datetime.now())
        """
          

    def report(self, posts, html=False):
        s = ''
        for post in posts:
            if html:
                info = '<a href="%s">source</a>' % post['url']
                sep  = '<hr>\n'
                desc = 'description_html'
            else:
                info = 'source : ' + post['url']
                sep  = 50 * '#' + '\n'
                desc = 'description_text'
            info += post['phone'] + post['email_alternative']
            s += sep + info + post[desc] + '\n'
        return s[:-1]


    def analyze(self, description_text):
        phonePattern = re.compile(r'''
                        # don't match beginning of string, number can start anywhere
            (\d{3})     # area code is 3 digits (e.g. '800')
            \D*         # optional separator is any number of non-digits
            (\d{3})     # trunk is 3 digits (e.g. '555')
            \D*         # optional separator
            (\d{4})     # rest of number is 4 digits (e.g. '1212')
            \D*         # optional separator
            (\d*)       # extension is optional and can be any number of digits
            $           # end of string
            ''', re.I)

        mailPattern = re.compile(r'[\w\-][\w\-\.]*@[\w\-][\w\-\.]+[a-zA-Z]{1,4}', re.I)
        phone = phonePattern.findall(description_text)
        if not phone:
            phone = ['']
        email = mailPattern.findall(description_text)
        if not email:
            email = ['']
        return (phone[0], email[0])

    
    def is_duplicates(self, duplicates, post):
        if duplicates.has_key(post['craig_id']):
            return True
        for text in duplicates.values():
            if dot(text, post['description_text']) >= self.config['SIMILARITY']:
                return True
        return False


    def get_bag(self, s):
        v = {}
        for w in s.split():
            v[w] = v.get(w, 0) + 1
        return v


    def dot(self, s1, s2):
        v1, v2 = self.get_bag(s1), self.get_bag(s2)
        score = 0
        for w, val in v1.items():
            if v2.has_key(w):
                score += v2[w] * val
        norm = max(len(s1.split()), len(s2.split()))
        if norm == 0:
            norm  = 1
            score = 0
        return 1.0 * score / norm

    def send_email(self, fromAddress, toAddress, subject, body, CC=None, HTML=False):
        sender  = Mailer(host='smtp.gmail.com', port=587, use_tls=True, usr='kendrickledet@gmail', pwd='yMHJ0e78gMbDtkV')
        message = Message(From=fromAddress, To=toAddress, Subject=subject, Body=body, CC=CC, charset="utf-8")
        message.Subject = subject
        # TODO below: check if html, attachment support
        #message.Body = body
        #message.Html = 'This is an <strong>HTML</strong> email!'
        #message.attach("kitty.jpg")

    
def main():
    # they see me hardcooooooodiiiiiin', they haaaaatin
    search_url = 'http://dallas.craigslist.org/search/?areaID=21&subAreaID=&query=BOOTY&catAbb=sss'
    msg        = """Hi there, I am interested in your posting. \n
                    Please get back to me if it's still available."""

    proc = MainProc({'FROM_EMAIL'  : 'kendrickledet@gmail.com',
                    'REPLY_EMAIL' : 'kendrickledet@gmail.com',
                    'TO_EMAIL' : 'kendrickledet@gmail.com',
                    'CC_EMAIL' : 'kendrickledet@gmail.com',
                    'REPORTS_ENABLED': True})

    proc.start(search_url, msg)
      
if __name__ == '__main__':
    main()