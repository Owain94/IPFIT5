import unittest

from IP.capreader import PcapReader

class TestMethods(unittest.TestCase):
    
    def test_get_ips(self):
        """
        asserts that the ip of google is found in the given pcap
        """
        capreader = PcapReader(["/tests/test.pcap"], "/tests/check.txt")
        self.assertTrue('8.8.8.8' in capreader.extract_ips())
        self.assertEqual(capreader.hash(), "//fill this in with the hash of the file.")