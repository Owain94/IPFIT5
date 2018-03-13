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
import socket
import datetime
from enum import Enum
from mmap import mmap, ACCESS_READ
from multiprocessing import Pool, cpu_count


class Reader(object, metaclass=abc.ABCMeta):

    @staticmethod
    @abc.abstractmethod
    def is_compatible(file):
        raise NotImplementedError(
            "This checks if the given file can be read using this reader.")

    @staticmethod
    @abc.abstractmethod
    def extract_ips(file):
        raise NotImplementedError(
            "Extracting of ip-addresses is one of the 2 things this class can do. This returns a generator that yields the IP's")

    @staticmethod
    @abc.abstractmethod
    def extract_all(file):
        raise NotImplementedError(
            "This returns a generator that yields tuples of (ip.src, ip.dst, protocoll, timestamp)")


class DPKTReader(Reader):

    @staticmethod
    def is_compatible(file):
        with open(file, 'rb') as f:
            try:
                _ = dpkt.pcap.Reader(f)
                return True
            except Exception:
                return False

    @staticmethod
    def inet_to_str(inet):
        """Convert inet object to a string

            Args:
                inet (inet struct): inet network address
            Returns:
                str: Printable/readable IP address
        """
        # First try ipv4 and then ipv6
        try:
            return socket.inet_ntop(socket.AF_INET, inet)
        except ValueError:
            return socket.inet_ntop(socket.AF_INET6, inet)

    @staticmethod
    def to_protocoll(n):
        """Converts a given number to a protocoll. Returns 'unknown' if the number could not be found in the map

        Args:
            n: the number to be converted

        Returns:
            str: Printable/readble protocoll
        """
        return {
            1: "ICMP",
            2: "IGMP",
            6: "TCP",
            17: "UDP",
        }.get(n, "Unknown")

    @staticmethod
    def extract_ips(file):
        """Extracts the ip-addresses from a pcap file

            Args:
                file: the pcap to be read
            Returns:
                Generator: An iterable over the ip-addresses in the given pcap file
        """
        with open(file, 'rb') as f:
            pcap = dpkt.pcap.Reader(f)

            for _, pkt in pcap:
                eth = dpkt.ethernet.Ethernet(pkt)

                if not isinstance(eth.data, dpkt.ip.IP):
                    continue

                ip = eth.data
                yield DPKTReader.inet_to_str(ip.src)
                yield DPKTReader.inet_to_str(ip.dst)

    @staticmethod
    def extract_all(file):
        """Extracts the ip-addresses, used protocoll, and timestamp
            Args:
                file: the pcap to be read
            Returns:
                Generator: An iterable over the ip-addresses, protocolls and timestampt
        """
        with open(file, 'rb') as f:
            pcap = dpkt.pcap.Reader(f)

            for ts, pkt in pcap:
                eth = dpkt.ethernet.Ethernet(pkt)

                if not isinstance(eth.data, dpkt.ip.IP):
                    continue

                ip = eth.data
                stamp = datetime.datetime.utcfromtimestamp(ts)
                prot = DPKTReader.to_protocoll(ip.p)

                src = DPKTReader.inet_to_str(ip.src)
                dst = DPKTReader.inet_to_str(ip.src)

                yield (src, dst, prot, stamp)


class PysharkReader(Reader):
    @staticmethod
    def is_compatible(file):
        try:
            _ = pyshark.FileCapture(file, keep_packets=False)
            return True
        except Exception:
            return False

    @staticmethod
    def extract_ips(file):
        cap = pyshark.FileCapture(file, keep_packets=False)

        for pkt in cap:
            try:
                yield pkt.ip.src
                yield pkt.ip.dst
            except Exception:
                continue

    @staticmethod
    def extract_all(file):
        cap = pyshark.FileCapture(file, keep_packets=False)

        for pkt in cap:
            try:
                stamp = pkt.sniff_time
                prot = pkt.transport_layer
                src = str(pkt.ip.src)
                dst = str(pkt.ip.dst)

                yield (src, dst, prot, stamp)

            except Exception:
                continue


class Hasher():
    BLOCKSIZE = 65536

    @staticmethod
    def getSize(file):
        return os.stat(file).st_size

    @staticmethod
    def hash(file):
        hasher = hashlib.sha256()
        s = Hasher.getSize(file)

        # On 0 bit files, it doesnt make sense to hash it.
        if s == 0:
            return ""

        with open(file, 'rb') as f:
            buf = f.read(Hasher.BLOCKSIZE)
            while len(buf) > 0:
                hasher.update(buf)
                buf = f.read(Hasher.BLOCKSIZE)

        return (file, hasher.hexdigest())


class CompatibleException(Exception):
    pass


class ReadPreference(Enum):
    DPKT = 1
    PYSHARK = 2
    UNKNOWN = 3


class PcapReader():

    def __init__(self, files):
        self.files = files
        self.dpkt_compatible = []
        self.pyshark_compatible = []
        self.hashes = []
        self.ips = set()

    @staticmethod
    def read_dpkt(file):
        return {ip for ip in DPKTReader.extract_ips(file)}

    @staticmethod
    def read_pyshark(file):
        return {ip for ip in PysharkReader.extract_ips(file)}

    def set_compatible(self):
        for file in self.files:
            if DPKTReader.is_compatible(file):
                self.dpkt_compatible.append(file)

            elif PysharkReader.is_compatible(file):
                self.pyshark_compatible.push(file)

            else:
                raise CompatibleException(
                    "None of the readers could read this pcapfile")

    def hash(self):
        p = Pool(cpu_count())

        self.hashes = p.map(Hasher.hash, self.files)

        return self.hashes

    def all_dpkt_compatible(self):
        return len(self.files) == len(self.dpkt_compatible)

    def all_pyshark_compatible(self):
        return len(self.files) == len(self.pyshark_compatible)

    def extract_ips(self, preference=ReadPreference.UNKNOWN):
        """Extracts the ip-addresses using a Reader. Also set's the instance's ips to the ip-addresses found,
            so they can be used in other methods.

            Args:
                preference: with the preference it is possible to preference one of the readers, by default
                it's UNKNOWN.
            Returns:
                List: A list of unique IP's found in all given pcap-files
        """
        DPKT = False
        PYSHARK = False

        if self.all_dpkt_compatible() and (preference == ReadPreference.UNKNOWN or preference == ReadPreference.DPKT):
            DPKT = True
            Pyshark = False

        else:
            DPKT = False
            PYSHARK = True

        if DPKT:  # self.all_dpkt_compatible() or preference == ReadPreference.DPKT:

            print("Using DPKT")
            p = Pool(cpu_count())
            tmp = p.map(PcapReader.read_dpkt, self.files)
            self.ips = {ip for set in tmp for ip in set}

            print(len(list(self.ips)))
            return list(self.ips)

        elif PYSHARK:  # self.all_pyshark_compatible() or preference == ReadPreference.PYSHARK:

            print("Using Pyshark")

            self.ips = {
                ip for file in self.files for ip in PcapReader.read_pyshark(file)}
            print(len(list(self.ips)))
            return list(self.ips)

        else:
            raise CompatibleException("This is not supported YET")


if __name__ == '__main__':
    import time

    pcapreader = PcapReader([r"E:\converted.pcap"])
    pcapreader.set_compatible()

    hashes = pcapreader.hash()

    for hash in hashes:
        print(hash)
    ips = pcapreader.extract_ips()

    for ip in ips:
        print(ip)
    '''
    n = 0

    s = time.time()
    test_end = None
    for (src, dst, prot, stamp) in PysharkReader.extract_all(r"E:\converted.pcap"):
        n += 1
        test_end = stamp

    print("Finished with {} items in {} seconds".format(n, time.time() - s))

    m = 0
    t = time.time()
    test_start = None
    for (src, dst, prot, stamp) in DPKTReader.extract_all(r"E:\converted.pcap"):
        if m == 0:
            test_start = stamp
        m += 1
    print("Finished with {} items in {} seconds".format(m, time.time() - t))

    print("{}: {}\t{}".format(test_end > test_start, test_end, test_start))
    '''
