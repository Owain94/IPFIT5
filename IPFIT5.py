import curses

from os import sep

from Utils.Store import Store
from Utils.Logging.Logging import Logging
from Utils.FilePicker import filepicker_main as image_filepicker

from Utils.Ewf import Ewf, EwfInfoMenu

from Utils.Menu import Menu
from Files import FilesMenu
from IP import IpMenu
from Photos import PhotosMenu

global_stores = Store()


class MainApp(object):
    def __init__(self, stdscreen):
        self.logger = Logging(self.__class__.__name__).logger

        global global_stores
        self.stores = global_stores
        self.image_picker = None
        self.image = None
        self.screen = stdscreen
        curses.curs_set(0)

        self.submenu_files = Menu(FilesMenu.FilesMenu.menu(), self.screen)
        self.submenu_ip = Menu(IpMenu.IpMenu.menu(), self.screen)
        self.submenu_photos = Menu(PhotosMenu.PhotosMenu.menu(), self.screen)

        if self.stores.image_store.get_state() == 'initial' or \
                self.stores.image_store.get_state() is None:
            main_menu_items = [
                ('Load image', self.filepicker)
            ]
        else:
            self.submenu_file_info = Menu(
                EwfInfoMenu.menu(self.stores.image_store), self.screen,
                info=True)

            main_menu_items = [
                ('Load image (Selected image: {})'.format(
                    self.stores.image_store.get_state().split(sep)[-1]),
                 self.filepicker),
                ('Image information', self.fileinfo),
                ('Files (Owain van Brakel)', self.menu_files),
                ('IP (Kasper van den Berg)', self.menu_ip),
                ('Photos (Virgil Bron)', self.menu_photos)
            ]
        main_menu = Menu(main_menu_items, self.screen, sub=False)
        main_menu.display()

    def filepicker(self):
        image_filepicker(self.stores.image_store)
        curses.wrapper(MainApp)

    def fileinfo(self):
        self.logger.debug('File info menu opened')
        self.submenu_file_info.display()

    def menu_files(self):
        self.logger.debug('Files menu opened')
        self.submenu_files.display()

    def menu_ip(self):
        self.logger.debug('Ip menu opened')
        self.submenu_ip.display()

    def menu_photos(self):
        self.logger.debug('Photos menu opened')
        self.submenu_photos.display()


if __name__ == '__main__':
    Logging(__name__).logger.info('Application start')
    curses.wrapper(MainApp)
