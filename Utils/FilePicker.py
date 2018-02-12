import os

from collections import defaultdict

from asciimatics.event import KeyboardEvent
from asciimatics.widgets import Frame, Layout, FileBrowser, Widget, Label, \
    Divider
from asciimatics.scene import Scene
from asciimatics.screen import Screen
from asciimatics.exceptions import ResizeScreenError, StopApplication

from Utils.Logging.Logging import Logging

global_store = None


class FilepickerFrame(Frame):
    def __init__(self, screen, store):
        self.logger = Logging(self.__class__.__name__).logger

        super(FilepickerFrame, self).__init__(
            screen, screen.height, screen.width, has_border=False,
            name='Filepicker')

        self.store = store

        # Create the form layout...
        layout = Layout([1], fill_frame=True)
        self.add_layout(layout)

        # Now populate it with the widgets we want to use.
        self._list = FileBrowser(Widget.FILL_FRAME,
                                 os.path.abspath('.'),
                                 name='mc_list',
                                 on_select=self.selected)
        layout.add_widget(Label('Image file picker'))
        layout.add_widget(Divider())
        layout.add_widget(self._list)
        layout.add_widget(Divider())
        layout.add_widget(Label('Press Enter to select or `q` to return.'))

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
        self.logger.info('Image selected: {}'.format(self._list.value))
        raise StopApplication('Image selected')

    def process_event(self, event):
        # Do the key handling for this Frame.
        if isinstance(event, KeyboardEvent):
            if event.key_code in [ord('q'), ord('Q'), Screen.ctrl('c')]:
                self.logger.info('User exited file picker')
                raise StopApplication('User quit')

        # Now pass on to lower levels for normal handling of the event.
        return super(FilepickerFrame, self).process_event(event)


def filepicker(screen, old_scene):
    global global_store
    screen.play([Scene([FilepickerFrame(screen, global_store)], -1)],
                stop_on_resize=True, start_scene=old_scene)


def filepicker_main(store):
    global global_store
    global_store = store

    last_scene = None
    while True:
        try:
            Screen.wrapper(filepicker, catch_interrupt=False,
                           arguments=[last_scene])
            break
        except ResizeScreenError as e:
            last_scene = e.scene
