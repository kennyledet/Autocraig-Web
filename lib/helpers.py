import hashlib

def hash_pass(password):
    return hashlib.sha224(password).hexdigest()

def make_dir(dirname):
    if not os.path.exists(dirname):
        return os.makedirs(dirname, mode=0777)
    else:
        return None
