from ipwhois import IPWhois
import pyshark
import dpkt

import abc
import hashlib
import itertools
from os import stat
from enum import Enum
from pprint import pprint
from datetime import datetime
from functools import partial
from itertools import product
from multiprocessing import Pool, cpu_count
from typing import Iterable, Tuple, List, Set
from socket import inet_ntop, AF_INET, AF_INET6

import socket
from warnings import filterwarnings

filterwarnings(action="ignore")

class Reader(object, metaclass=abc.ABCMeta):

    @staticmethod
    @abc.abstractmethod
    def is_compatible(f: str) -> bool:
        """Checks if a given file can be read with this reader
            Args:
                file (str): The file that should be checked
            Returns:
                bool: True/False depending on if this reader can read the file
        """
        raise NotImplementedError(
            "This checks if the given file can be read using this reader.")

    @staticmethod
    @abc.abstractmethod
    def extract_ips(f: str) -> Iterable[Tuple[str, str]]:
        """Extracts the ip-addresses from a pcap file

            Args:
                file: the pcap to be read
            Returns:
                Generator: An iterable over the ip-addresses in the given
                pcap file
        """
        raise NotImplementedError(
            "Extracting of ip-addresses is one of the 2 things this class"
            "can do. This returns a generator that yields the IP's")

    @staticmethod
    @abc.abstractmethod
    def extract_all(f: str) -> Iterable[Tuple[str, str, str, datetime]]:
        """Extracts the ip-addresses, used protocoll, and timestamp
            Args:
                file: the pcap to be read
            Returns:
                Generator: An iterable over the ip-addresses,
                           protocolls and timestamp
        """
        raise NotImplementedError(
            "This returns a generator that yields tuples of (ip.src, ip.dst,"
            "protocoll, timestamp)")


class DPKTReader(Reader):

    @staticmethod
    def is_compatible(f: str) -> bool:
        with open(f, 'rb') as f:
            try:
                _ = dpkt.pcap.Reader(f)
                return True
            except Exception:
                return False

    @staticmethod
    def inet_to_str(inet) -> str:
        """Convert inet object to a string

            Args:
                inet (inet struct): inet network address
            Returns:
                str: Printable/readable IP address
        """
        return inet_ntop(AF_INET, inet)

    @staticmethod
    def to_protocoll(n: int) -> str:
        """Converts a given number to a protocoll.
            Returns 'unknown' if the number could not be found in the map

        Args:
            n: the number to be converted

        Returns:
            str: Printable/readble protocoll
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
    def is_compatible(f: str) -> bool:
        try:
            _ = pyshark.FileCapture(f, keep_packets=False)
            return True
        except Exception:
            return False

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
        """Hashes a given file
            Args:
                file (str): The file that needs to be hashes
            Returns:
                Tuple[str, str]: A tuple containing the filename,
                                 and the associated hash
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


'''
wrapper to automatically check if the PcapReader's instance
has self.pyshark_compatible and self.dpkt_compatibe set.
if not, sets them.
'''


def check_and_set_compatible(func):
    def wrapper(self, *args, **kwargs):
        if len(self.pyshark_compatible) == 0 and \
                len(self.dpkt_compatible) == 0:

            self.set_compatible()

        return func(self, *args, **kwargs)
    return wrapper


class PcapReader():

    def __init__(self, files):
        self.files = files
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

    @staticmethod
    def read(f: str, reader: Reader) -> Set[str]:
        return {ip for ip in reader.extract_ips(f)}

    @staticmethod
    def read_all(f: str, reader: Reader, compare: List[str]) \
            -> Set[Tuple[str, str, str, datetime]]:

        return {
            (src, dst, prot, stamp) for (src, dst, prot, stamp)
            in reader.extract_all(f)
            if any(ip in compare for ip in [src, dst])
        }

    def set_compatible(self):
        for f in self.files:
            if DPKTReader.is_compatible(f):
                self.dpkt_compatible.append(f)

            elif PysharkReader.is_compatible(f):
                self.pyshark_compatible.append(f)

            else:
                raise CompatibleException(
                    "None of the readers could read this pcapfile")

    def hash(self) -> List[Tuple[str, str]]:

        self.data["hashes"] = self.pool.map(Hasher.hash, self.files)

        return self.data["hashes"]

    @check_and_set_compatible
    def extract_ips(self) -> List[str]:
        """Extracts the ip-addresses using a Reader. Also set's the instance's
        ips to the ip-addresses found, so they can be used in other methods.

            Args:
                -
            Returns:
                List: A list of unique IP's found in all given pcap-files
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

    def in_common(self, other: str) -> List[str]:
        """Returns a list of all ip-addresses that both occure in the pcaps,
            and in the given file

            Args:
                other: The file to be compared with
            Returns:
                List of common ip-addresses
        """
        with open(other, 'r') as f:
            to_compare = {line.rstrip() for line in f.readlines()}

            self.data["similarities"] = self.data["ip-list"].intersection(
                to_compare)

        return list(self.data["similarities"])

    @check_and_set_compatible
    def generate_timeline(self) -> List[
            Tuple[str, str, str, datetime]]:
        """Generates a timeline of all ip-addresses
            in commen with the provided list

            Args:
                -
            Returns:
                Tuple[st, str, str, datetime]:
                    (src-ip, dst-ip, protocoll, timestamp)
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


def fancy_print():
    print("\n---------------------------------------------------------\n")


if __name__ == '__main__':
    pcapreader = PcapReader([
        r"E:\converted.pcap",
        r"E:\pcap_test.pcap",
        r"E:\pcap_test1.pcap",
        r"C:\Users\Kasper\Documents\HSL\Jaar 2\Periode 3\capture_test.pcapng"
    ])

    fancy_print()
    hashes = pcapreader.hash()
    for hash in hashes:
        print(hash)

    fancy_print()
    ips = pcapreader.extract_ips()
    for ip in ips:
        print(ip)
    fancy_print()

    common = pcapreader.in_common('testjes.txt')
    for c in common:
        print(c)

    fancy_print()
    timeline = pcapreader.generate_timeline()
    for line in timeline:
        print(line)

    fancy_print()
    whois = pcapreader.whoisinfo()
    for (ip, info) in whois:
        print(ip)
        pprint(info)
