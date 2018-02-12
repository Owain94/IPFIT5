import logging


class Logging:
    def __init__(self, name):
        logging.basicConfig(filename='IPFIT5.log',
                            format='%(asctime)s - %(name)s - %(levelname)s - '
                                   '%(message)s',
                            level=logging.DEBUG)

        self.logger = logging.getLogger(name)
