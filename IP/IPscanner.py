import ipwhois
import pyshark
import dpkt

import abc

import os
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

class CapReader(object, metaclass=abc.ABCMeta):
    
    @abc.abstractmethod
    def hash(self):
        raise NotImplementedError("Hashing of pcaps is verry important, and should be implemented")

    @abc.abstractmethod
    def read_ips(self):
        raise NotImplementedError("Being able to read ip-addresses is the number one thing this reader should be able to do")
    
    @abc.abstractmethod
    def similarities(self, file):
        raise NotImplementedError("The found ip-addresses should be compared with a file for similarities")
    
    @abc.abstractmethod
    def timeline(self):
        raise NotImplementedError("A timeline of all ip-addresses should be created")

class DpktReader(CapReader):
    def __init__(self, pcaps):
        
        self.pcaps = pcaps
        self.ip_addresses = set()

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

    def __grab_ips_from_file(self, file):
        with open(file, 'rb') as f:
            pcap = dpkt.pcap.Reader(f)


    #returns a list of unique IP's found in ALL pcaps
    def read_ips(self):
        p = Pool(cpu_count())

        ips = p.map(self.__grab_ips_from_file, self.pcaps)

    def similarities(self, file):
        pass

    def timeline():
        pass



class IPReader(object):
    def __init__(self, pcaps):
        self.pcaps = pcaps
        self.ips = []
        self.overeenkomsten = []

    def read_ip(self, file):
        ips = []
        f = open(file, 'rb')

        
        try:
            cap = dpkt.pcap.Reader(f)
            for ts, buf in pcap:
                eth = dpkt.ethernet.Ethernet(buf)
                ip = eth.data
                print(ip)
                ips.append(ip) 
        except Exception as e:
            print("OH NOO {}".format(e))
        return ips
        '''
        with open(file, 'rb') as f:
            try:
                cap = dpkt.pcap.Reader(f)
                for ts, buf in pcap:
                        eth = dpkt.ethernet.Ethernet(buf)
                        ip = eth.data
                        print(ip)
                        ips.append(ip)
            except Exception as e:
                print(e)
        return ips
        '''
    def read_ips(self):
        p = Pool(cpu_count())

        ips = p.map(self.read_ip, self.pcaps)
        print(ips)


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

class Reader():
    def __init__(self, pcap):
        self.pcap = pcap
    
    def read(self, ips_only = True):
        cap = pyshark.FileCapture(self.pcap, keep_packets=False)
        print("Loaded {}".format(self.pcap))
        if ips_only:

            for pkt in cap:
                try:
                    yield (pkt.ip.src, pkt.ip.dst)
                except AttributeError as e:
                    print("something went wrong: {}".format(e))
        else:
            for pkt in cap:
                try:
                    yield (pkt.ip.src, pkt.ip.dst, pkt.transport_layer, pkt.sniff_time)
                except AttributeError as e:
                    print("something went wrong: {}".format(e))

        cap.close()
        if not cap.eventloop.is_closed():
            cap.eventloop.close()

        
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
        r = Reader(pcap)

        for (src, dst) in r.read(ips_only=True):
            yield src
            yield dst

    def grep_ips(self):
        self.ips = {ip for f in self.files for ip in self.grep_ips_from_file(f)}
        return list(self.ips)
        
    def sort(self):
        # Sort by time,
        pass

    def timeline(self):
        for pcap in self.files:
            r = Reader(pcap)
            for (src, dst, prot, time) in r.read(ips_only=False):

                if src in self.common or dst in self.common:
                    self.time_line.append([time, prot, src, dst])
                    print(type(prot))

        sorted(self.time_line, key=lambda pkt: pkt[0])
        return self.time_line

    # get out the protocolls
    def info(self):
        # get out whoami is and dns info.
        pass

def fancy_print():
    print("\n------------------------------------------\n")

if __name__ == '__main__':
    scanner = IPScanner([r"C:/Users/Kasper/Documents/HSL/Jaar 2/Periode 3/capture_test.pcapng",
                         r"C:/Users/Kasper/Documents/HSL/Jaar 2/Periode 3/capture_test1.pcapng",
                         r"C:/Users/Kasper/Documents/HSL/Jaar 2/Periode 3/capture_test2.pcapng",
    ])
    hashes = scanner.hash()
    print("[*] The hashes of the input files are: [*]")
    for hash in hashes:
        print(hash)

    fancy_print()

    timeline = scanner.timeline()
    print("[*] The timeline of the pcaps are: [*]")
    for pkt in timeline:
        print(pkt)

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
