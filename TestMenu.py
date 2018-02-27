from collections import defaultdict

from asciimatics.widgets import Frame, TextBox, Layout, Label, Divider, Text, \
    CheckBox, RadioButtons, Button, PopUpDialog, TimePicker, DatePicker, \
    Background
from asciimatics.scene import Scene
from asciimatics.screen import Screen
from asciimatics.exceptions import ResizeScreenError, NextScene, \
    StopApplication, \
    InvalidFields
import sys
import logging

from Utils.Store import Store
from Utils.FilePicker import FilepickerFrame

# Initial data for the form
form_data = {
    "PA": False,
    "FA": False,
    "FB": False,
    "FC": False,
    "IA": False
}

logging.basicConfig(filename="forms.log", level=logging.DEBUG)


class MenuFrame(Frame):
    def __init__(self, screen):
        self.store = Store().image_store
        self.image = self.store.get_state()

        super(MenuFrame, self).__init__(screen,
                                        screen.height - 2,
                                        screen.width - 2,
                                        data=form_data,
                                        has_shadow=True,
                                        has_border=True,
                                        can_scroll=False,
                                        name="IPFIT5")

        self.store.subscribe(lambda: self.set_image())

        self.palette = defaultdict(lambda: (
            Screen.COLOUR_WHITE, Screen.A_NORMAL, Screen.COLOUR_BLACK))

        self.palette['focus_field'] = (
            Screen.COLOUR_WHITE, Screen.A_NORMAL, Screen.COLOUR_BLACK)

        self.palette['focus_button'] = (
            Screen.COLOUR_BLACK, Screen.A_BOLD, Screen.COLOUR_WHITE)

        self.palette['selected_focus_field'] = (
            Screen.COLOUR_BLACK, Screen.A_BOLD, Screen.COLOUR_WHITE)

        header = Layout([1])
        self.add_layout(header)

        header.add_widget(
            Label(label="IPFIT5".center(screen.width - 4), height=1), 0)
        header.add_widget(Label(
            label="Virgil Bron | Owain van Brakel | Kasper van den Berg"
                .center(screen.width - 4), height=3), 0)

        layout = Layout([1, 50, 1])
        self.add_layout(layout)

        self.file_picker = RadioButtons([("Lorum ipsum", 1),
                                        ("Lorum ipsum", 2),
                                        (self.image, 3)],
                                        label="Image:",
                                        name="image",
                                        on_change=self._on_change)

        layout.add_widget(self.file_picker, 1)

        layout.add_widget(Divider(height=3), 1)

        layout.add_widget(Label("Photo's", height=2), 1)
        layout.add_widget(CheckBox("Lorum ipsum",
                                   label="",
                                   name="PA",
                                   on_change=self._on_change), 1)

        layout.add_widget(Divider(height=3), 1)

        layout.add_widget(Label("Files", height=2), 1)
        layout.add_widget(CheckBox("Hashing",
                                   label="",
                                   name="FA",
                                   on_change=self._on_change), 1)
        layout.add_widget(CheckBox("Create timeline",
                                   label="",
                                   name="FB",
                                   on_change=self._on_change), 1)
        layout.add_widget(CheckBox("Detect language",
                                   label="",
                                   name="FC",
                                   on_change=self._on_change), 1)

        layout.add_widget(Divider(height=3), 1)

        layout.add_widget(Label("IP", height=2), 1)
        layout.add_widget(CheckBox("Lorem ipsum",
                                   label="",
                                   name="IA",
                                   on_change=self._on_change), 1)

        layout.add_widget(Divider(height=3), 1)

        layout2 = Layout([1, 1])
        self.add_layout(layout2)

        layout2.add_widget(Button("View Data", self._view), 0)
        layout2.add_widget(Button("Quit", self._quit), 1)

        self.fix()

    def set_image(self):
        self.image = self.store.get_state()

        self.file_picker = RadioButtons([("Lorum ipsum", 1),
                      ("Lorum ipsum", 2),
                      (self.image, 3)],
                     label="Image:",
                     name="image",
                     on_change=self._on_change)

        print(self.image)

    def _on_change(self):
        self.save()
        for key, value in self.data.items():
            if key not in form_data or form_data[key] != value:
                if key == 'image' and value == 3:
                    raise NextScene()
                break

    def _reset(self):
        self.reset()
        raise NextScene()

    def _view(self):
        # Build result of this form and display it.
        try:
            self.save(validate=True)
            message = "Values entered are:\n\n"
            for key, value in self.data.items():
                message += "- {}: {}\n".format(key, value)

            message += "- Selected: {}\n".format(self.store.get_state())
        except InvalidFields as exc:
            message = "The following fields are invalid:\n\n"
            for field in exc.fields:
                message += "- {}\n".format(field)
        self._scene.add_effect(
            PopUpDialog(self._screen, message, ["OK"]))

    def _quit(self):
        self._scene.add_effect(
            PopUpDialog(self._screen,
                        "Are you sure?",
                        ["Yes", "No"],
                        on_close=self._quit_on_yes))

    @staticmethod
    def _quit_on_yes(selected):
        # Yes is the first button
        if selected == 0:
            raise StopApplication("User requested exit")


def menu(screen, scene):
    store = Store().image_store

    main_scene = Scene([Background(screen), MenuFrame(screen)], -1)
    file_picker_scene = Scene([Background(screen), FilepickerFrame(screen)], -1)

    screen.play(
        [main_scene, file_picker_scene],
        stop_on_resize=False,
        start_scene=scene
    )


def main():
    global global_store
    global_store = Store().image_store

    last_scene = None

    while True:
        try:
            Screen.wrapper(menu, catch_interrupt=False, arguments=[last_scene])
            sys.exit(0)
        except ResizeScreenError as e:
            last_scene = e.scene


if __name__ == '__main__':
    main()
