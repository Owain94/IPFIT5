import os
import pyshark
import hashlib
import itertools
import contextlib
import sys
import inspect
from mmap import mmap, ACCESS_READ
from multiprocessing import Pool, cpu_count

DEBUG = False
# FIXME
#------------------------------------------------
currentdir = os.path.dirname(os.path.abspath(
    inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)
#---------------------------------------------
from Utils.Logging import Logging


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


class Hasher():
    BLOCKSIZE = 65536

    def __init__(self, filename):
        self.filename = filename

    def getSize(self):
        st = os.stat(self.filename)

        return st.st_size

    def hash(self):
        hasher = hashlib.sha256()
        s = self.getSize()

        # On 0 bit files, it doesnt make sense to hash it.
        if s == 0:
            return ""

        with open(self.filename, 'rb') as f:
            buf = f.read(self.BLOCKSIZE)
            while len(buf) > 0:
                hasher.update(buf)
                buf = f.read(self.BLOCKSIZE)

        return hasher.hexdigest()


def hash_file(file):
    hasher = Hasher(file)
    return (file, hasher.hash())


class IPScanner():
    def __init__(self, files):
        #self.logger = Logging(self.__class__.__name__).logger
        self.hashes = []
        self.common = set()
        self.ips = set()
        self.time_line = []
        self.files = files

    #@FIXME: Logging
    def hash(self):
        p = Pool(cpu_count())
        try:
            self.hashes = p.map(hash_file, self.files)
        except Exception as e:
            if DEBUG:
                print("An error occured in the hash function: {}".format(e))
        return self.hashes

    def compare(self, other):
        with open(other, 'r') as f:
            other = set(line.rstrip() for line in f.readlines())
        self.common = self.ips.intersection(other)
        return self.common

    def grep_ips_from_file(self, pcap):
        ips = []
        cap = pyshark.FileCapture(pcap)
        for pkt in cap:
            try:
                yield pkt.ip.src
                yield pkt.ip.dst
            except Exception as e:
                if DEBUG:
                    print(
                        "An error occured in the grep_ips_from_file function: {}".format(e))
        cap.close()
        return ips

    def grep_ips(self):
        self.ips = set(itertools.chain.from_iterable(
            (self.grep_ips_from_file(f) for f in self.files)))
        return list(self.ips)

    def sort(self):
        # Sort by time,
        pass

    def try_read(self, pcap):
        cap = pyshark.FileCapture(pcap)
        for pkt in cap:
            try:
                yield (pkt.sniff_time, pkt.transport_layer, pkt.ip.src, pkt.ip.dst)
            except Exception as e:
                if DEBUG:
                    print("An error occured in the try_read function: {}".format(e))
        cap.close()

    def timeline(self):
        for pcap in self.files:
            for (time, prot, src, dst) in self.try_read(pcap):
                if src in self.common or dst in self.common:
                    self.time_line.append([time, prot, src, dst])

        sorted(self.time_line, key=lambda pkt: pkt[0])
        return self.time_line

    # get out the protocolls
    def info(self):
        # get out whoami is and dns info.
        pass


def fancy_print():
    print()
    print("------------------------------------------")
    print()


if __name__ == '__main__':
    scanner = IPScanner([r"C:/Users/Kasper/Documents/HSL/Jaar 2/Periode 3/capture_test.pcapng",
                         r"C:/Users/Kasper/Documents/HSL/Jaar 2/Periode 3/capture_test1.pcapng"])

    hashes = scanner.hash()
    print("[*] The hashes of the input files are: [*]")
    for hash in hashes:
        print(hash)

    fancy_print()

    ips = scanner.grep_ips()
    print("[*] all the Ip's in the pcaps are: [*]")
    for ip in ips:
        print(ip)

    fancy_print()

    f = input("welk bestand wil je comparen?:")

    common = scanner.compare(f)
    print("[*] The IP-addresses that occur in both the pcaps and the given file are: [*]")
    for c in common:
        print(c)

    fancy_print()

    timeline = scanner.timeline()
    print("[*] The timeline of the pcaps are: [*]")
    for pkt in timeline:
        print(pkt)

    fancy_print()
