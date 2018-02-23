import os
import time
import hashlib
import contextlib

from mmap import mmap, ACCESS_READ
from multiprocessing import Pool, cpu_count

BLOCKSIZE = 65536


def flatten(iterable):
    iterator, sentinel, stack = iter(iterable), object(), []
    while True:
        value = next(iterator, sentinel)
        if value is sentinel:
            if not stack:
                break
            iterator = stack.pop()
        elif isinstance(value, str):
            yield value
        else:
            try:
                new_iterator = iter(value)
            except TypeError:
                yield value
            else:
                stack.append(iterator)
                iterator = new_iterator


def getSize(filename):
    st = os.stat(filename)
    return st.st_size


def hash_file(file):
    hasher = hashlib.sha256()
    s = getSize(file)
    if s <= 0 or s > 1000000000:
        return ''
    with open(file, 'rb') as f:

        with contextlib.closing(mmap(f.fileno(), 0, access=ACCESS_READ)) as m:
            buf = m.read(BLOCKSIZE)
            while len(buf) > 0:
                hasher.update(buf)
                buf = m.read(BLOCKSIZE)

    return hasher.hexdigest()


def hash_tree(files):
    P = Pool(cpu_count())

    hashed = P.map(hash_file, files)

    return hashed


def walk_dir():
    for root, _, files in os.walk('C:/Users/Kasper/Documents', topdown=False):
        for name in files:
            yield os.path.join(root, name)
    print('Done yielding things')


if __name__ == '__main__':
    n = 0
    for f in walk_dir():
        n += 1
    print(n)
    s = time.time()
    t = hash_tree([f for f in walk_dir()])

    print(time.time() - s)
