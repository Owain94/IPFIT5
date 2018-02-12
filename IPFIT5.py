import curses

from os import sep

from FilePicker import filepicker_main as image_filepicker
from Store import Store

from Menu import Menu
from Files import FilesMenu
from IP import IpMenu
from Photos import PhotosMenu

global_stores = Store()


class MainApp(object):
    def __init__(self, stdscreen):
        global global_stores
        self.stores = global_stores
        self.image_picker = None
        self.image = None
        self.screen = stdscreen
        curses.curs_set(0)

        submenu_files = Menu(FilesMenu.FilesMenu.menu(), self.screen)
        submenu_ip = Menu(IpMenu.IpMenu.menu(), self.screen)
        submenu_photos = Menu(PhotosMenu.PhotosMenu.menu(), self.screen)

        if self.stores.image_store.get_state() == 'initial' or self.stores.image_store.get_state() is None:
            main_menu_items = [
                ('Load image', self.filepicker)
            ]
        else:
            main_menu_items = [
                ('Load image (Selected image: {})'.format(self.stores.image_store.get_state().split(sep)[-1]), self.filepicker),
                ('Files (Owain van Brakel)', submenu_files.display),
                ('IP (Kasper van den Berg)', submenu_ip.display),
                ('Photos (Virgil Bron)', submenu_photos.display)
            ]
        main_menu = Menu(main_menu_items, self.screen, sub=False)
        main_menu.display()

    def filepicker(self):
        image_filepicker(self.stores.image_store)
        curses.wrapper(MainApp)


if __name__ == '__main__':
    curses.wrapper(MainApp)
