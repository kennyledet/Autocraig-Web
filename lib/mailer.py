#coding: UTF8
"""
mailer module

Simple front end to the smtplib and email modules,
to simplify sending email.

A lot of this code was taken from the online examples in the
email module documentation:
http://docs.python.org/library/email-examples.html

Released under MIT license.

Version 0.5 is based on a patch by Douglas Mayle

Sample code:

    import mailer

    message = mailer.Message()
    message.From = "me@example.com"
    message.To = "you@example.com"
    message.Subject = "My Vacation"
    message.Body = open("letter.txt", "rb").read()
    message.attach("picture.jpg")

    sender = mailer.Mailer('mail.example.com')
    sender.send(message)
__version__ = "0.7"
__author__ = "Ryan Ginstrom"
__license__ = "MIT"
__description__ = "A module to send email simply in Python"
"""
import smtplib
import socket
import threading
import Queue
import uuid

# this is to support name changes
# from version 2.4 to version 2.5
try:
    from email import encoders
    from email.header import make_header
    from email.message import Message
    from email.mime.audio import MIMEAudio
    from email.mime.base import MIMEBase
    from email.mime.image import MIMEImage
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
except ImportError:
    from email import Encoders as encoders
    from email.Header import make_header
    from email.MIMEMessage import Message
    from email.MIMEAudio import MIMEAudio
    from email.MIMEBase import MIMEBase
    from email.MIMEImage import MIMEImage
    from email.MIMEMultipart import MIMEMultipart
    from email.MIMEText import MIMEText

# For guessing MIME type based on file name extension
import mimetypes
import time

from os import path

import models
import urllib2

def recvline(sock):
    stop = 0
    line = ''
    while True:
        i = sock.recv(1)
        if i == 'n': stop = 1
        line += i
        if stop == 1:
            break
    return line
 
def load_proxies():
    try:
        proxies = urllib2.urlopen('http://spamvilla.com/sock_proxy.txt').read()
    except:
        return None
    else:
        return proxies.split('\n')


class ProxSMTP( smtplib.SMTP ):
 
    def __init__(self, host='', port=0, p_address='',p_port=0, local_hostname=None,
             timeout=socket._GLOBAL_DEFAULT_TIMEOUT):
        """Initialize a new instance.
 
        If specified, `host' is the name of the remote host to which to
        connect.  If specified, `port' specifies the port to which to connect.
        By default, smtplib.SMTP_PORT is used.  An SMTPConnectError is raised
        if the specified `host' doesn't respond correctly.  If specified,
        `local_hostname` is used as the FQDN of the local host.  By default,
        the local hostname is found using socket.getfqdn().
 
        """
        self.p_address = p_address
        self.p_port = p_port
 
        self.timeout = timeout
        self.esmtp_features = {}
        self.default_port = smtplib.SMTP_PORT
        if host:
            (code, msg) = self.connect(host, port)
            if code != 220:
                raise SMTPConnectError(code, msg)
        if local_hostname is not None:
            self.local_hostname = local_hostname
        else:
            # RFC 2821 says we should use the fqdn in the EHLO/HELO verb, and
            # if that can't be calculated, that we should use a domain literal
            # instead (essentially an encoded IP address like [A.B.C.D]).
            fqdn = socket.getfqdn()
            if '.' in fqdn:
                self.local_hostname = fqdn
            else:
                # We can't find an fqdn hostname, so use a domain literal
                addr = '127.0.0.1'
                try:
                    addr = socket.gethostbyname(socket.gethostname())
                except socket.gaierror:
                    pass
                self.local_hostname = '[%s]' % addr
        smtplib.SMTP.__init__(self)
 
    def _get_socket(self, port, host, timeout):
        # This makes it simpler for SMTP_SSL to use the SMTP connect code
        # and just alter the socket connection bit.
        if self.debuglevel > 0: print>>stderr, 'connect:', (host, port)
        new_socket = socket.create_connection((self.p_address,self.p_port), timeout)
        new_socket.sendall("CONNECT {0}:{1} HTTP/1.1rnrn".format(port,host))
        for x in xrange(2): recvline(new_socket)
        return new_socket


class Mailer(object):
    """
    Represents an SMTP connection.

    Use login() to log in with a username and password.
    """

    def __init__(self, host="localhost", port=0, use_tls=False, usr=None, pwd=None):
        self.host = host
        self.port = port
        self.use_tls = use_tls
        self._usr = usr
        self._pwd = pwd

    def login(self, usr, pwd):
        self._usr = usr
        self._pwd = pwd

    def send(self, msg):
        """
        Send one message or a sequence of messages.

        Every time you call send, the mailer creates a new
        connection, so if you have several emails to send, pass
        them as a list:
        mailer.send([msg1, msg2, msg3])
        """
        '''Proxy override'''
        proxies = []
        try:
            proxies_from_db = list(models.connection.acw.proxies.find({}))[0]['proxies']
        except:
            proxies_from_db = []

        proxies_from_url = load_proxies()
        proxies.extend(proxies_from_db)
        proxies.extend(proxies_from_url)

        if len(proxies):
            import random
            from lib.helpers import rbl_check
            proxy, proxy_port = random.choice(proxies).split(':') # get random proxy
            while not rbl_check(proxy):
                proxy, proxy_port = random.choice(proxies).split(':')
        else:
            proxy, proxy_port = '', 0
            
        server = ProxSMTP(self.host, self.port, proxy, proxy_port)

        if self._usr and self._pwd:
            if self.use_tls is True:
                server.ehlo()
                server.starttls()
                server.ehlo()

            server.login(self._usr, self._pwd)

        try:
            num_msgs = len(msg)
            for m in msg:
                self._send(server, m)
        except TypeError:
            self._send(server, msg)

        server.quit()

    def _send(self, server, msg):
        """
        Sends a single message using the server
        we created in send()
        """
        me = msg.From
        if isinstance(msg.To, basestring):
            to = [msg.To]
        else:
            to = list(msg.To)

        cc = []
        if msg.CC:
            if isinstance(msg.CC, basestring):
                cc = [msg.CC]
            else:
                cc = list(msg.CC)

        bcc = []
        if msg.BCC:
            if isinstance(msg.BCC, basestring):
                bcc = [msg.BCC]
            else:
                bcc = list(msg.BCC)

        you = to + cc + bcc
        server.sendmail(me, you, msg.as_string())

class Message(object):
    """
    Represents an email message.

    Set the To, From, Subject, and Body attributes as plain-text strings.
    Optionally, set the Html attribute to send an HTML email, or use the
    attach() method to attach files.

    Use the charset property to send messages using other than us-ascii

    If you specify an attachments argument, it should be a list of
    attachment filenames: ["file1.txt", "file2.txt"]

    `To` should be a string for a single address, and a sequence
    of strings for multiple recipients (castable to list)

    Send using the Mailer class.
    """

    def __init__(self, To=None, From=None, CC=None, BCC=None, Subject=None, Body=None, Html=None,
                 Date=None, attachments=None, charset=None):
        self.attachments = []
        if attachments:
            for attachment in attachments:
                if isinstance(attachment, basestring):
                    self.attachments.append((attachment, None, None))
                else:
                    try:
                        filename, cid = attachment
                    except (TypeError, IndexError):
                        self.attachments.append((attachment, None, None))
                    else:
                        self.attachments.append((filename, cid, None))
        self.To = To
        self.CC = CC
        self.BCC = BCC
        """string or iterable"""
        self.From = From
        """string"""
        self.Subject = Subject
        self.Body = Body
        self.Html = Html
        self.Date = Date or time.strftime("%a, %d %b %Y %H:%M:%S %z", time.gmtime())
        self.charset = charset or 'us-ascii'

        self.message_id = self.make_key()

    def make_key(self):
        return str(uuid.uuid4())

    def as_string(self):
        """Get the email as a string to send in the mailer"""

        if not self.attachments:
            return self._plaintext()
        else:
            return self._multipart()

    def _plaintext(self):
        """Plain text email with no attachments"""

        if not self.Html:
            msg = MIMEText(self.Body, 'plain', self.charset)
        else:
            msg  = self._with_html()

        self._set_info(msg)
        return msg.as_string()

    def _with_html(self):
        """There's an html part"""

        outer = MIMEMultipart('alternative')

        part1 = MIMEText(self.Body, 'plain', self.charset)
        part2 = MIMEText(self.Html, 'html', self.charset)

        outer.attach(part1)
        outer.attach(part2)

        return outer

    def _set_info(self, msg):
        if self.charset == 'us-ascii':
            msg['Subject'] = self.Subject
        else:
            subject = unicode(self.Subject, self.charset)
            msg['Subject'] = str(make_header([(subject, self.charset)]))

        msg['From'] = self.From
        
        if isinstance(self.To, basestring):
            msg['To'] = self.To
        else:
            self.To = list(self.To)
            msg['To'] = ", ".join(self.To)

        if self.CC:
            if isinstance(self.CC, basestring):
                msg['CC'] = self.CC
            else:
                self.CC = list(self.CC)
                msg['CC'] = ", ".join(self.CC)

        msg['Date'] = self.Date

    def _multipart(self):
        """The email has attachments"""

        msg = MIMEMultipart('related')

        if self.Html:
            outer = MIMEMultipart('alternative')

            part1 = MIMEText(self.Body, 'plain', self.charset)
            part1.add_header('Content-Disposition', 'inline')

            part2 = MIMEText(self.Html, 'html', self.charset)
            part2.add_header('Content-Disposition', 'inline')

            outer.attach(part1)
            outer.attach(part2)
            msg.attach(outer)
        else:
            msg.attach(MIMEText(self.Body, 'plain', self.charset))

        self._set_info(msg)
        msg.preamble = self.Subject

        for filename, cid, mimetype in self.attachments:
            self._add_attachment(msg, filename, cid, mimetype)

        return msg.as_string()

    def _add_attachment(self, outer, filename, cid, mimetype):
        """
        If mimetype is None, it will try to guess the mimetype
        """
        if mimetype:
            ctype = mimetype
            encoding = None
        else:
            ctype, encoding = mimetypes.guess_type(filename)
        if ctype is None or encoding is not None:
            # No guess could be made, or the file is encoded (compressed), so
            # use a generic bag-of-bits type.
            ctype = 'application/octet-stream'
        maintype, subtype = ctype.split('/', 1)
        fp = open(filename, 'rb')
        if maintype == 'text':
            # Note: we should handle calculating the charset
            msg = MIMEText(fp.read(), _subtype=subtype)
        elif maintype == 'image':
            msg = MIMEImage(fp.read(), _subtype=subtype)
        elif maintype == 'audio':
            msg = MIMEAudio(fp.read(), _subtype=subtype)
        else:
            msg = MIMEBase(maintype, subtype)
            msg.set_payload(fp.read())
            # Encode the payload using Base64
            encoders.encode_base64(msg)
        fp.close()

        # Set the content-ID header
        if cid:
            msg.add_header('Content-ID', '<%s>' % cid)
            msg.add_header('Content-Disposition', 'inline')
        else:
            # Set the filename parameter
            msg.add_header('Content-Disposition', 'attachment', filename=path.basename(filename))
        outer.attach(msg)

    def attach(self, filename, cid=None, mimetype=None):
        """
        Attach a file to the email. Specify the name of the file;
        Message will figure out the MIME type and load the file.

        Specify mimetype to set the MIME type manually.
        """

        self.attachments.append((filename, cid, mimetype))


class Manager(threading.Thread):
    """
    Manages the sending of email in the background

    you can supply it with an instance of class Mailler or pass in the same
    parameters that you would have used to create an instance of Mailler

    if a message was succesfully sent, self.results[msg.message_id] returns a 3
    element tuple (True/False, err_code, err_message)
    """

    def __init__(self, mailer=None, callback=None, **kwargs):
        threading.Thread.__init__(self)

        self.queue = Queue.Queue()
        self.mailer = mailer
        self.abort = False
        self.callback = callback
        self._results = {}
        self._result_lock = threading.RLock()

        if self.mailer is None:
            self.mailer = Mailer(
                host=kwargs.get('host', 'localhost'),
                port=kwargs.get('port', 25),
                use_tls=kwargs.get('use_tls', False),
                usr=kwargs.get('usr', None),
                pwd=kwargs.get('pwd', None),
            )

    def __getattr__(self, name):
        if name == 'results':
            with self._result_lock:
                return self._results
        else:
            return None

    def run(self):

        while self.abort is False:
            msg = self.queue.get(block=True)
            if msg is None:
                break

            try:
                num_msgs = len(msg)
            except TypeError:
                num_msgs = 1
                msg = [msg]

            for m in msg:
                try:
                    self.results[m.message_id] = (False, -1, '')
                    self.mailer.send(m)
                    self.results[m.message_id] = (True, 0, '')

                except Exception as e:
                    args = e.args
                    if len(args) < 2:
                        args = (-1, e.args[0])

                    self.results[m.message_id] = (False, args[0], args[1])

                if self.callback:
                    try:
                        self.callback(m.message_id)
                    except:
                        pass

            # endfor

            self.queue.task_done()

    def send(self, msg):
        self.queue.put(msg)
