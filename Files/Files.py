from Utils.Logging.Logging import Logging
from Utils.Ewf import Ewf

from multiprocessing import Process, Manager

import csv


class Files:
    def __init__(self):
        self.logger = Logging(self.__class__.__name__).logger
        self.ewf = Ewf()
        self.data = []

    def get_files(self):
        data = self.ewf.files()
        self.write_csv(data, 'test.csv')

        return data

    def get_hash(self, file, shared_list):
        sha_sum = self.ewf.single_file(int(file[0][-1]),
                                       Ewf.rreplace(file[8], file[1], ''),
                                       file[1], True)

        file.append(sha_sum)
        shared_list.append(file)

    def get_hashes(self):
        data = self.get_files()

        self.write_csv(data, 'test.csv')

        with Manager() as manager:
            shared_list = manager.list()
            processes = []

            for i in data[0]:
                p = Process(target=self.get_hash, args=(i, shared_list))
                p.start()
                processes.append(p)

            for p in processes:
                p.join()

            lst = [x for x in shared_list]

        self.write_csv([lst], 'test.csv')

    @staticmethod
    def write_csv(data, output):
        if not data:
            return

        with open(output, 'w') as csvfile:
            csv_writer = csv.writer(csvfile)
            headers = ['Partition', 'File', 'File Ext', 'File Type',
                       'Create Date', 'Modify Date', 'Change Date', 'Size',
                       'File Path', 'Hash']
            csv_writer.writerow(headers)
            for result_list in data:
                csv_writer.writerows(result_list)
