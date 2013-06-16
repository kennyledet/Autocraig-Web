import hashlib

def hash_pass(password):
    return hashlib.sha224(password).hexdigest()
