import hashlib
import time
from splinter import Browser

def hash_pass(password):
    return hashlib.sha224(password).hexdigest()

def make_dir(dirname):
    if not os.path.exists(dirname):
        return os.makedirs(dirname, mode=0777)
    else:
        return None

def rbl_check(ip):
    """ Check an IP against multiple RBLs """
    with Browser(driver_name='chrome') as b:
        b.visit('https://rblwatcher.com/')
        b.fill('ip', ip)
        b.find_by_id('btn_checkip').click()

        time.sleep(7)

        blacklist = b.find_by_css('div[class="blacklisted"]')
        whitelist = b.find_by_css('div[class="nblacklisted"]')

        blacklisted, whitelisted = len(blacklist), len(whitelist)

        ratio = float(blacklisted) / float(whitelisted + blacklisted)
        
        return 1 if ratio < 0.10 else 0