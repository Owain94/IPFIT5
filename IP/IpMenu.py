import curses

from Utils.Logging.Logging import Logging


class IpMenu(object):
    def __init__(self):
        self.logger = Logging(self.__class__.__name__).logger

    @staticmethod
    def menu():
        menu_items = [
            ('Placeholder', curses.beep),
            ('Placeholder', curses.flash)
        ]

        return menu_items
