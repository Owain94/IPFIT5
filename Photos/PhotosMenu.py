import curses


class PhotosMenu(object):
    @staticmethod
    def menu():
        menu_items = [
            ('Placeholder', curses.beep)
        ]

        return menu_items
