import curses
import sys

from curses import panel


class Menu(object):
    def __init__(self, items, stdscreen, sub: bool = True):
        self.window = stdscreen.subwin(0, 0)
        self.window.keypad(1)
        self.panel = panel.new_panel(self.window)
        self.panel.hide()
        panel.update_panels()

        self.position = 0
        self.items = items
        if sub:
            self.items.append(('Return', 'return'))

        # Start colors in curses
        curses.start_color()
        curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_WHITE)

    def navigate(self, n):
        self.position += n
        if self.position < 0:
            self.position = 0
        elif self.position >= len(self.items):
            self.position = len(self.items) - 1

    def display(self):
        self.panel.top()
        self.panel.show()
        self.window.clear()

        while True:
            height, width = self.window.getmaxyx()

            # Declaration of strings
            title = "IPFIT5"[:width - 1]
            subtitle = "Owain van Brakel | Kasper van den Berg | Virgil Bron"[:width - 1]
            statusbarstr = "Press 'q' to exit"

            # Centering calculations
            start_x_title = int((width // 2) - (len(title) // 2) - len(title) % 2)
            start_x_subtitle = int((width // 2) - (len(subtitle) // 2) - len(subtitle) % 2)

            # Render status bar
            self.window.attron(curses.color_pair(3))
            self.window.addstr(height - 1, 0, statusbarstr)
            self.window.addstr(height - 1, len(statusbarstr), " " * (width - len(statusbarstr) - 1))
            self.window.attroff(curses.color_pair(3))

            # Turning on attributes for title
            self.window.attron(curses.color_pair(2))
            self.window.attron(curses.A_BOLD)

            # Rendering title
            self.window.addstr(0, start_x_title, title)

            # Turning off attributes for title
            self.window.attroff(curses.color_pair(2))
            self.window.attroff(curses.A_BOLD)

            # Print rest of text
            self.window.addstr(1, start_x_subtitle, subtitle)

            # Refresh the screen
            self.window.refresh()

            self.window.refresh()
            curses.doupdate()
            for index, item in enumerate(self.items):
                if index == self.position:
                    mode = curses.A_REVERSE
                else:
                    mode = curses.A_NORMAL

                msg = '%d. %s' % (index, item[0])

                if item[1] == 'return':
                    index = index + 4
                else:
                    index = index + 3

                self.window.addstr(index, 1, msg, mode)

            key = self.window.getch()

            if key in [curses.KEY_ENTER, ord('\n')]:
                if (self.items[self.position][1]) == 'return':
                    break
                else:
                    self.items[self.position][1]()

            elif key == curses.KEY_UP:
                self.navigate(-1)

            elif key == curses.KEY_DOWN:
                self.navigate(1)

            if key == ord('q') or key == ord('Q'):
                sys.exit('User exited')

        self.window.clear()
        self.panel.hide()
        panel.update_panels()
        curses.doupdate()