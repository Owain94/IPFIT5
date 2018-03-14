from Interfaces.ModuleInterface import ModuleInterface

from Utils.Logging.Logging import Logging
from Utils.ImageHandler import ImageHandler

from datetime import datetime
from multiprocessing import Process, Manager

from typing import List, Union, Dict


class Files(ModuleInterface):
    def __init__(self):
        self.logger = Logging(self.__class__.__name__).logger
        self.image_handler = ImageHandler()

        self.options = {}

        self.data = {
            'files': [],
            'hashing': [],
            'timeline': [],
            'language': [],
            'merged': []
        }

        self._progress = {
            'hashing': 0,
            'timeline': 0,
            'language': 0
        }

    def run(self, *args) -> None:
        self.options = {
            'hashing': args[0],
            'timeline': args[1],
            'language': args[2]
        }
        self.get_files()

    @property
    def progress(self) -> Dict[str, int]:
        d = {}

        if self.options['hashing']:
            d['hashing'] = self._progress['hashing']

        if self.options['timeline']:
            d['timeline'] = self._progress['timeline']

        if self.options['language']:
            d['language'] = self._progress['language']

        return d

    def results(self) -> None:
        pass

    def get_files(self) -> None:
        data = self.image_handler.files()

        self.data['files'] = data

    def timeline(self):
        pass

    def language(self):
        pass

    def get_hash(self, file: List[Union[str, datetime]], shared_list: List) \
            -> None:
        sha_sum = self.image_handler\
            .single_file(int(file[0][-1]),
                         ImageHandler.rreplace(file[8], file[1], ''),
                         file[1], True)

        file.append(sha_sum)
        shared_list.append(file)

    def get_hashes(self) -> None:
        progress = 0
        items = self.data['files'][0]

        with Manager() as manager:
            shared_list = manager.list()
            processes = []

            for i in items:
                p = Process(target=self.get_hash, args=(i, shared_list))
                p.start()
                processes.append(p)

            for p in processes:
                p.join()
                progress += 1
                self._progress['hashing'] = int(progress / len(items) * 100)

            lst = [x for x in shared_list]

        self.data['hashing'] = [lst]
