import os

from collections import defaultdict

from asciimatics.widgets import Frame, Layout, FileBrowser, Widget, Label, \
    Divider
from asciimatics.screen import Screen
from asciimatics.exceptions import NextScene

from Utils.Store.Image import ImageStore
from Utils.Logging.Logging import Logging


class FilepickerFrame(Frame):
    def __init__(self, screen):
        self.logger = Logging(self.__class__.__name__).logger

        super(FilepickerFrame, self).__init__(screen,
                                              screen.height - 2,
                                              screen.width - 2,
                                              has_shadow=True,
                                              has_border=True,
                                              can_scroll=False,
                                              name='Filepicker')

        self.store = ImageStore().image_store

        header = Layout([1])
        self.add_layout(header)

        header.add_widget(
            Label(label="IPFIT5".center(screen.width - 4), height=1), 0)
        header.add_widget(
            Label(
                label="Virgil Bron | Owain van Brakel | ""Kasper van den Berg"
                .center(screen.width - 4), height=3), 0)

        # Create the form layout...
        layout = Layout([1, 50, 1], fill_frame=True)
        self.add_layout(layout)

        # Now populate it with the widgets we want to use.
        self._list = FileBrowser(Widget.FILL_FRAME, os.path.abspath(
            '.'), name='mc_list', on_select=self.selected)
        layout.add_widget(Label('Image file picker'), 1)
        layout.add_widget(Divider(), 1)
        layout.add_widget(self._list, 1)
        layout.add_widget(Divider(), 1)
        layout.add_widget(Label('Press Enter to select.'), 1)

        # Prepare the Frame for use.
        self.fix()

        self.palette = defaultdict(lambda: (
            Screen.COLOUR_WHITE, Screen.A_NORMAL, Screen.COLOUR_BLACK))
        self.palette['focus_field'] = (
            Screen.COLOUR_WHITE, Screen.A_NORMAL, Screen.COLOUR_BLACK)
        self.palette['selected_focus_field'] = (
            Screen.COLOUR_WHITE, Screen.A_BOLD, Screen.COLOUR_CYAN)

        self.logger.debug('File picker opened')

    def selected(self):
        # Just confirm whenever the user actually selects something.
        self.store.dispatch({'type': 'set_image', 'image': self._list.value})
        # self.logger.info('Image selected: {}'.format(self._list.value))
        raise NextScene()
