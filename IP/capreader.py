from ipwhois import IPWhois
import pyshark
import dpkt

import abc
import hashlib
import itertools
from os import stat
from enum import Enum
from pprint import pprint
from itertools import chain
from datetime import datetime
from functools import partial
from itertools import product
from multiprocessing import Pool, cpu_count
from typing import Iterable, Tuple, List, Set
from socket import inet_ntop, AF_INET, AF_INET6

from warnings import filterwarnings

from Utils.XlsxWriter import XlsxWriter
from Utils.Logging.Logging import Logging
from Interfaces.ModuleInterface import ModuleInterface

filterwarnings(action="ignore")


def once(item):
    """
    used for Iterating once over any item.
    """
    yield item


class Reader(object, metaclass=abc.ABCMeta):

    @staticmethod
    @abc.abstractmethod
    def extract_ips(f: str) -> Iterable[Tuple[str, str]]:
        """
        Extracts the ip-addresses from a pcap file
        :param f: the pcap to be read
        :return: An iterable over the ip-addresses in the given pcap file
        """
        raise NotImplementedError(
            "Extracting of ip-addresses is one of the 2 things this class"
            "can do. This returns a generator that yields the IP's")

    @staticmethod
    @abc.abstractmethod
    def extract_all(f: str) -> Iterable[Tuple[str, str, str, datetime]]:
        """
        Extracts the ip-addresses, used protocoll, and timestamp
        :param f: the pcap to be read
        :return: An iterable over the ip-addresses, protocolls and timestamp
        """
        raise NotImplementedError(
            "This returns a generator that yields tuples of (ip.src, ip.dst,"
            "protocoll, timestamp)")

    @staticmethod
    def compatible(func=None, *, pyshark, dpkt):
        '''
        Decorator that wraps up the reading for 2 given pcap readers.
        `pyshark` and `dpkt` are both supposed to be lambda's, taking a file,
        and opening it. These lambda's are wrapped in @try_open,
        to check for failure or succes
        '''
        if func is None:
            return partial(Reader.compatible, pyshark=pyshark, dpkt=dpkt)

        @try_open
        def pysharkcompatible(f):
            return pyshark(f)

        @try_open
        def dpktcompatible(f):
            return dpkt(f)

        def wrapper(self, *args, **kwargs):
            return func(self, pyshark=pysharkcompatible, dpkt=dpktcompatible)
        return wrapper


def try_open(func):
    '''
    Decorator to try and read a pcap for any given reader.
    On succes, return 'true',
    on failure, return 'false'
    '''
    def wrapper(*args, **kwargs):
        f = args[0]
        try:
            with open(f, 'rb') as f:
                func(f, **kwargs)
                return True
        except Exception:
            return False
    return wrapper


class DPKTReader(Reader):

    @staticmethod
    def inet_to_str(inet) -> str:
        """
        convers inet object to a string
        :param inet: inet object
        :return: printable/readable Ip address
        """
        return inet_ntop(AF_INET, inet)

    @staticmethod
    def to_protocoll(n: int) -> str:
        """
        converts a given number to a protocoll
        :param n: int to be converted
        :return: the protocoll
        """
        return {
            1: "ICMP",
            2: "IGMP",
            3: "GGP",
            4: "IPIP",
            5: "ST",
            6: "TCP",
            7: "CBT",
            8: "EGP",
            9: "IGP",
            10: "BBNRCC",
            11: "NVP",
            12: "PUP",
            13: "ARGUS",
            14: "EMCON",
            15: "XNET",
            16: "CHAOS",
            17: "UDP",
            18: "MUX",
            19: "DCNMEAS",
            20: "HMP",
            21: "PRM",
            22: "IDP",
            23: "TRUNK1",
            24: "TRUNK2",
            25: "LEAF1",
            26: "LEAF2",
            27: "RDP",
            28: "IRTP",
            29: "TP",
            30: "NETBLT",
            31: "MFPNSP",
            32: "MERITINP",
            33: "SEP",
            34: "3PC",
            35: "IDPR",
            36: "XTP",
            37: "DDP",
            38: "CMTP",
            39: "TPPP",
            40: "IL",
            41: "IP6",
            42: "SDRP",
            43: "ROUTING",
            44: "FRAGMENT",
            46: "RSVP",
            47: "GRE",
            48: "MHRP",
            49: "ENA",
            50: "ESP",
            51: "AH",
            52: "INLSP",
            53: "SWIPE",
            54: "NARP",
            55: "MOBILE",
            56: "TLSP",
            57: "SKIP",
            58: "ICMP6",
            59: "NONE",
            60: "DSTOPTS",
            61: "ANYHOST",
            62: "CFTP",
            63: "ANYNET",
            64: "EXPAK",
            65: "KRYPTOLAN",
            66: "RVD",
            67: "IPPC",
            68: "DISTFS",
            69: "SATMON",
            70: "VISA",
            71: "IPCV",
            72: "CPNX",
            73: "CPHB",
            74: "WSN",
            75: "PVP",
            76: "BRSATMON",
            77: "SUNND",
            78: "WBMON",
            79: "WBEXPAK",
            80: "EON",
            81: "VMTP",
            82: "SVMTP",
            83: "VINES",
            84: "TTP",
            85: "NSFIGP",
            86: "DGP",
            87: "TCF",
            88: "EIGRP",
            89: "OSPF",
            90: "SPRITERPC",
            91: "LARP",
            92: "MTP",
            93: "AX25",
            94: "IPIPENCAP",
            95: "MICP",
            96: "SCCSP",
            97: "ETHERIP",
            98: "ENCAP",
            99: "ANYENC",
            100: "GMTP",
            101: "IFMP",
            102: "PNNI",
            103: "PIM",
            104: "ARIS",
            105: "SCPS",
            106: "QNX",
            107: "AN",
            108: "IPCOMP",
            109: "SNP",
            110: "COMPAQPEER",
            111: "IPXIP",
            112: "VRRP",
            113: "PGM",
            114: "ANY0HOP",
            115: "L2TP",
            116: "DDX",
            117: "IATP",
            118: "STP",
            119: "SRP",
            120: "UTI",
            121: "SMP",
            122: "SM",
            123: "PTP",
            124: "ISIS",
            125: "FIRE",
            126: "CRTP",
            127: "CRUDP",
            128: "SSCOPMCE",
            129: "IPLT",
            130: "SPS",
            131: "PIPE",
            132: "SCTP",
            133: "FC",
            134: "RSVPIGN",
        }.get(n, "Unknown")

    @staticmethod
    def extract_ips(f: str) -> Iterable[Tuple[str, str]]:

        with open(f, 'rb') as f:
            pcap = dpkt.pcap.Reader(f)

            for _, pkt in pcap:
                eth = dpkt.ethernet.Ethernet(pkt)

                if not isinstance(eth.data, dpkt.ip.IP):
                    continue

                ip = eth.data
                yield DPKTReader.inet_to_str(ip.src)
                yield DPKTReader.inet_to_str(ip.dst)

    @staticmethod
    def extract_all(f: str) -> Iterable[Tuple[str, str, str, datetime]]:

        with open(f, 'rb') as f:
            pcap = dpkt.pcap.Reader(f)

            for ts, pkt in pcap:
                eth = dpkt.ethernet.Ethernet(pkt)

                if not isinstance(eth.data, dpkt.ip.IP):
                    continue

                ip = eth.data
                stamp = datetime.utcfromtimestamp(ts)
                prot = DPKTReader.to_protocoll(ip.p)

                src = DPKTReader.inet_to_str(ip.src)
                dst = DPKTReader.inet_to_str(ip.dst)

                yield (src, dst, prot, stamp)


class PysharkReader(Reader):
    @staticmethod
    def extract_ips(f: str) -> Iterable[Tuple[str, str]]:
        cap = pyshark.FileCapture(f, keep_packets=False)

        for pkt in cap:
            try:
                yield pkt.ip.src
                yield pkt.ip.dst
            except Exception:
                continue

        # This prevents getting an Overlapping Future error.
        PysharkReader.close_cap(cap)

    @staticmethod
    def extract_all(f: str) -> Iterable[Tuple[str, str, str, datetime]]:
        cap = pyshark.FileCapture(f)

        for pkt in cap:
            try:
                stamp = pkt.sniff_time
                prot = pkt.transport_layer
                src = str(pkt.ip.src)
                dst = str(pkt.ip.dst)

                yield (src, dst, prot, stamp)

            except Exception:
                continue

        # This prevents getting an Overlapping Future error.
        PysharkReader.close_cap(cap)

    @staticmethod
    def close_cap(cap):
        cap.close()
        if not cap.eventloop.is_closed():
            cap.eventloop.close()


class Hasher():
    BLOCKSIZE = 65536

    @staticmethod
    def getSize(f: str) -> int:

        return stat(f).st_size

    @staticmethod
    def hash(fi: str) -> Tuple[str, str]:
        """
        hashes a given file
        :param fi: the file to be hashed
        :return: tuple containing the filename, and the hash
        """
        hasher = hashlib.sha256()
        s = Hasher.getSize(fi)

        # On 0 bit files, it doesnt make sense to hash it.
        if s == 0:
            return (fi, "")

        with open(fi, 'rb') as f:
            buf = f.read(Hasher.BLOCKSIZE)
            while len(buf) > 0:
                hasher.update(buf)
                buf = f.read(Hasher.BLOCKSIZE)

        return (fi, hasher.hexdigest())


class CompatibleException(Exception):
    pass


def check_and_set_compatible(func):
    """
    wrapper to automatically check if the PcapReader's instance
    has self.pyshark_compatible and self.dpkt_compatibe set.
    if not, sets them.
    """

    def wrapper(self, *args, **kwargs):
        if len(self.pyshark_compatible) == 0 and \
                len(self.dpkt_compatible) == 0:

            self.set_compatible()

        return func(self, *args, **kwargs)
    return wrapper


class PcapReader(ModuleInterface):

    def __init__(self, files, to_check):
        self.logger = Logging(self.__class__.__name__).logger
        self.files = files
        self.to_check = to_check
        self.dpkt_compatible = []
        self.pyshark_compatible = []
        self.pool = Pool(cpu_count())

        self.data = {
            "hashes": [],
            "timeline": [],
            "whois-info": [],
            "ip-list": set(),
            "similarities": set(),
        }

    def run(self, *args):
        self.hash()
        self.extract_ips()
        self.in_common()
        self.generate_timeline()
        self.whoisinfo()

    def results(self):
        xlsx_writer = XlsxWriter('ips')

        # write the hashes
        self.write_xls(xlsx_writer, "Hashes", [
                       "Filename", "Sha256-hash"], self.data["hashes"])

        # write the unique ip's found
        self.write_xls(xlsx_writer, "Unique-ips",
                       ["IPS"], [[ip] for ip in self.data["ip-list"]])

        # write the ip's in commons with the provided file
        self.write_xls(xlsx_writer, "Commons", ["Common"], [
                       [ip] for ip in self.data["similarities"]])

        # write the timeline
        self.write_xls(xlsx_writer, "Timeline", [
                       "ip-src", "ip-dst", "protocoll", "time"], self.data["timeline"])

        def has_dict(item): return type(item[1]) == dict
        # write whoisinfo.
        self.write_xls(xlsx_writer, "Whoisinfo",
                       list(next(
                           chain(once("Ip"), item[1].keys())
                           for item in self.data["whois-info"] if has_dict(item)
                       )),
                       [[str(v) for v in chain(once(item[0]), item[1].values())]
                        for item in self.data["whois-info"] if has_dict(item)]
                       )
        xlsx_writer.close()

    def write_xls(self, xlsxwriter, worksheetname, headers, data):
        xlsxwriter.add_worksheet(worksheetname)
        xlsxwriter.write_headers(worksheetname, headers)
        xlsxwriter.write_items(worksheetname, [*data])

    @staticmethod
    def read(f: str, reader: Reader) -> Set[str]:
        """
        extracts all ip's from a given pcap, with a given reader
        :param f: pcap to be read
        :reader: the reader to be read with
        :return: set of unique ip's in the pcap
        """
        return {ip for ip in reader.extract_ips(f)}

    @staticmethod
    def read_all(f: str, reader: Reader, compare: List[str]) \
            -> Set[Tuple[str, str, str, datetime]]:
        """
        extract the src, dst, prot, stamp from a given pcap
        :param f: the pcap-file
        :param reader: the reader to be read with
        :param compare: list to compare the ip's with
        :return: set of (src, dst, prot stamp)
        """

        return {
            (src, dst, prot, stamp) for (src, dst, prot, stamp)
            in reader.extract_all(f)
            if any(ip in compare for ip in [src, dst])
        }

    @Reader.compatible(dpkt=lambda f: dpkt.pcap.Reader(f),
                       pyshark=lambda f: pyshark.FileCapture(f,
                                                             keep_packets=False))
    def set_compatible(self, pyshark, dpkt):
        """
        sets self.dpkt_compatible and self.pyshark_compatible
        :param pyshark: lambda for trying to read the pcap with pyshark
        :param dpkt: lambda for trying to read the pcap with dpkt
        :return: none
        """
        for f in self.files:
            if dpkt(f):
                self.dpkt_compatible.append(f)

            elif pyshark(f):
                self.pyshark_compatible.append(f)

            else:
                raise CompatibleException(
                    "None of the readers could read this pcapfile")

    def hash(self) -> List[Tuple[str, str]]:
        """
        Hashes all files of self
        :return: list of tuples, containg the filename and the hash
        """

        self.data["hashes"] = self.pool.map(Hasher.hash, self.files)

        return self.data["hashes"]

    @check_and_set_compatible
    def extract_ips(self) -> List[str]:
        """
        extracts the ip's from every file in self.files
        :return: list of unique ip's
        """
        # DPKT
        extracted_sets = self.pool.map(
            partial(PcapReader.read, reader=DPKTReader), self.dpkt_compatible)

        self.data["ip-list"].update({ip for s in extracted_sets for ip in s})

        # Pyshark
        self.data["ip-list"].update({
            ip for f in self.pyshark_compatible for ip in
            PcapReader.read(f, reader=PysharkReader)})

        return list(self.data["ip-list"])

    def in_common(self) -> List[str]:
        """
        Check ip's found in the given file for similarities with it's own list
        :param other: file to be read
        :return: list of similarities
        """
        with open(self.to_check, 'r') as f:
            to_compare = {line.rstrip() for line in f.readlines()}

            self.data["similarities"] = self.data["ip-list"].intersection(
                to_compare)

        return list(self.data["similarities"])

    @check_and_set_compatible
    def generate_timeline(self) -> List[
            Tuple[str, str, str, datetime]]:
        """
        generates a timeline of all ip-addresses
        :return: List of Tuples containing src, dst, prot, stamp
        """

        # DPKT
        extracted_sets = self.pool.map(partial(
            PcapReader.read_all,
            reader=DPKTReader,
            compare=self.data["similarities"]), self.dpkt_compatible)

        tmp_timeline = [line for s in extracted_sets for line in s]

        # Pyshark
        tmp_timeline.extend(
            [line for f in self.pyshark_compatible for line in
                PcapReader.read_all(
                    f,
                    reader=PysharkReader,
                    compare=self.data["similarities"])])

        self.data["timeline"] = sorted(tmp_timeline, key=lambda line: line[3])

        # Check if there's a better way to convert datatime's to str ...there should be?
        self.data["timeline"] = [(*stuff, str(stamp))
                                 for (*stuff, stamp) in self.data["timeline"]]
        return self.data["timeline"]

    @staticmethod
    def whois_info_ip(ip: str) -> Tuple[str, IPWhois]:
        try:
            whois = IPWhois(ip)
            results = whois.lookup_whois()

            return (ip, results)
        except Exception:
            return ("", "")

    def whoisinfo(self) -> List[Tuple[str, IPWhois]]:

        self.data["whois-info"] = self.pool.map(
            PcapReader.whois_info_ip, self.data["similarities"])
        return self.data["whois-info"]
