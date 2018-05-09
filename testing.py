from IP import capreader

def fancy_print():
    print("\n---------------------------------------------------------\n")


if __name__ == '__main__':
    pcapreader = capreader.PcapReader([
        r"F:\converted.pcap",
        r"F:\pcap_test.pcap",
        r"F:\pcap_test1.pcap",
        r"F:\filtered03.pcap",
        r"F:\filtered05.pcap"
    ], "testjes.txt")

    pcapreader.run()
    pcapreader.results()