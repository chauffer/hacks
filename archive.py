import time
import os
import shutil
import re

SECONDS_IN_DAY = 24 * 60 * 60
src = '.'


now = time.time()
before = now - SECONDS_IN_DAY

def get_appropriate_folder(filename):
    return time.strftime('%Y-%m', time.gmtime(os.path.getmtime(filename)))


for fname in os.listdir(src):

    if fname == 'archive.py' or re.match('^[0-9]{4}-[0-9]{2}$', fname):
        continue
    print('Processing ', fname)
    src_fname = os.path.join(src, fname)
    folder = get_appropriate_folder(src_fname)
    os.makedirs(folder, exist_ok=True)

    shutil.move(src_fname, folder)
    print('Moved {fname} to {folder}'.format(fname=fname, folder=folder))
