import curses

from Utils.Logging.Logging import Logging

from Files.Files import Files


class FilesMenu(object):
    def __init__(self, store):
        self.logger = Logging(self.__class__.__name__).logger
        self.store = store
        self.files = Files(store)

    def menu(self):
        menu_items = [
            ('Files', self.files.get_files),
            ('Search', self.files.search),
            ('Hashes', self.files.get_hashes)
        ]

        return menu_items
