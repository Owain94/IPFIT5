from collections import defaultdict

from asciimatics.widgets import Frame, Text, TextBox, Layout, Label, Divider, \
    CheckBox, Button, PopUpDialog
from asciimatics.scene import Scene
from asciimatics.screen import Screen
from asciimatics.exceptions import ResizeScreenError, NextScene, \
    StopApplication
from sys import exit as exit_application

from pathlib import Path
from Utils.Store import Store
from Utils.FilePicker import FilepickerFrame

from Utils.Ewf import Ewf

from Files.Files import Files


class MenuFrame(Frame):
    def __init__(self, screen):
        self.form_data = {
            'DA': None,
            'DB': None,
            'DC': None,
            'IA': None,
            'PA': False,
            'FA': False,
            'FB': False,
            'FC': False,
            'IB': False
        }

        self.store = Store().image_store
        self.image = self.store.get_state()

        settings = self.get_settings()

        if settings is not None:
            try:
                self.form_data['DA'] = settings[0]
                self.form_data['DB'] = settings[1]
                self.form_data['DC'] = settings[2]
            except IndexError:
                pass

        super(MenuFrame, self).__init__(screen,
                                        screen.height - 2,
                                        screen.width - 2,
                                        data=self.form_data,
                                        has_shadow=True,
                                        has_border=True,
                                        can_scroll=False,
                                        name='IPFIT5')

        self.store.subscribe(lambda: self.set_image())

        self.palette = defaultdict(lambda: (
            Screen.COLOUR_WHITE, Screen.A_NORMAL, Screen.COLOUR_BLACK))

        self.palette['focus_field'] = (
            Screen.COLOUR_WHITE, Screen.A_NORMAL, Screen.COLOUR_BLACK)

        self.palette['focus_button'] = (
            Screen.COLOUR_BLACK, Screen.A_BOLD, Screen.COLOUR_WHITE)

        self.palette['selected_focus_field'] = (
            Screen.COLOUR_WHITE, Screen.A_BOLD, Screen.COLOUR_BLACK)

        self.palette['disabled'] = (
            Screen.COLOUR_BLACK, Screen.A_BOLD, Screen.COLOUR_BLACK)

        self.image_label = TextBox(height=2,
                                   as_string=True,
                                   label='Image:',
                                   name='IA')
        self.image_label.disabled = True
        self.image_label.custom_colour = 'label'

        self.image_info_button = Button('Image info', self.file_info)
        self.image_info_button.disabled = True

        self.draw_menu()

    def draw_menu(self):
        header = Layout([1])
        self.add_layout(header)

        header.add_widget(
            Label(label='IPFIT5'.center(self.screen.width - 4), height=1), 0)
        header.add_widget(Label(
            label='Virgil Bron | Owain van Brakel | Kasper van den Berg'
            .center(self.screen.width - 4), height=1), 0)

        details_layout = Layout([1, 50, 1])
        self.add_layout(details_layout)

        details_layout.add_widget(Divider(height=3), 1)

        details_layout.add_widget(Label(label='Settings', height=2), 1)
        details_layout.add_widget(Text(label='Name:',
                                       name='DA',
                                       on_change=self.on_change), 1)
        details_layout.add_widget(Text(label='Location:',
                                       name='DB',
                                       on_change=self.on_change), 1)
        details_layout.add_widget(Text(label='Case:',
                                       name='DC',
                                       on_change=self.on_change), 1)

        details_save_layout = Layout([1, 50, 1])
        self.add_layout(details_save_layout)

        details_save_layout.add_widget(Button('Save', self.save_details), 1)

        image_layout = Layout([1, 50, 1])
        self.add_layout(image_layout)

        image_layout.add_widget(Divider(height=3), 1)

        image_layout.add_widget(self.image_label, 1)

        image_buttons_layout = Layout([1, 25, 25, 1])
        self.add_layout(image_buttons_layout)

        image_buttons_layout.add_widget(
            Button('Select image', self.file_picker), 1)
        image_buttons_layout.add_widget(self.image_info_button, 2)
        image_buttons_layout.add_widget(Divider(height=3), 1)
        image_buttons_layout.add_widget(Divider(height=3), 2)

        photos_layout = Layout([1, 50, 1])
        self.add_layout(photos_layout)

        photos_layout.add_widget(Label('Photo\'s', height=2), 1)
        photos_layout.add_widget(CheckBox('Lorum ipsum',
                                          label='',
                                          name='PA',
                                          on_change=self.on_change), 1)
        photos_layout.add_widget(Divider(height=3), 1)

        files_layout = Layout([1, 50, 1])
        self.add_layout(files_layout)

        files_layout.add_widget(Label('Files', height=2), 1)
        files_layout.add_widget(CheckBox('Hashing',
                                         label='',
                                         name='FA',
                                         on_change=self.on_change), 1)
        files_layout.add_widget(CheckBox('Create timeline',
                                         label='',
                                         name='FB',
                                         on_change=self.on_change), 1)
        files_layout.add_widget(CheckBox('Detect language',
                                         label='',
                                         name='FC',
                                         on_change=self.on_change), 1)
        files_layout.add_widget(Divider(height=3), 1)

        ip_layout = Layout([1, 50, 1])
        self.add_layout(ip_layout)

        ip_layout.add_widget(Label(label='IP', height=2), 1)
        ip_layout.add_widget(CheckBox('Lorem ipsum',
                                      label='',
                                      name='IB',
                                      on_change=self.on_change), 1)
        ip_layout.add_widget(Divider(height=3), 1)

        buttons_layout = Layout([1, 1])
        self.add_layout(buttons_layout)

        buttons_layout.add_widget(Button('Run', self.run), 0)
        buttons_layout.add_widget(Button('Quit', self.quit), 1)

        self.fix()

    def set_image(self):
        self.form_data['IA'] = self.store.get_state()
        self.image_info_button.disabled = False
        self.save()

    def on_change(self):
        self.save()
        self.image_info_button.disabled = self.store.get_state() == 'initial'

    def file_picker(self):
        raise NextScene()

    def file_info(self):
        ewf = Ewf()
        metadata = ewf.encase_metadata()
        volume_information = ewf.volume_info()

        if len(metadata) > 0:
            metadata.append('')

        self._scene.add_effect(
            PopUpDialog(self._screen,
                        '\n'.join([*metadata, *volume_information]), ['OK']))

    def save_details(self):
        data = [
            self.data.get('DA'),
            self.data.get('DB'),
            self.data.get('DC')
        ]
        self.save_settings(data)

        self._scene.add_effect(
            PopUpDialog(self._screen, 'Settings saved!', ['OK']))

    def view(self):
        self._scene.add_effect(
            PopUpDialog(self._screen, str(self.store.get_state()), ['OK']))

    def quit(self):
        self._scene.add_effect(
            PopUpDialog(self._screen,
                        'Are you sure?',
                        ['Yes', 'No'],
                        on_close=self.quit_on_yes))

    def run(self):
        name = self.data.get('DA', None)
        location = self.data.get('DB', None)
        case = self.data.get('DC', None)
        image = self.data.get('IA', None)

        msg = []

        if name is None or len(name[0]) is 0:
            msg.append('Name can not be empty')

        if location is None or len(location[0]) is 0:
            msg.append('Location can not be empty')

        if case is None or len(case[0]) is 0:
            msg.append('Case can not be empty')

        if image is None or len(case[0]) is 0:
            msg.append('No image selected')

        if len(msg) > 0:
            self._scene.add_effect(
                PopUpDialog(self._screen, '\n'.join(msg), ['OK']))
            return

        self.exec()

    def exec(self):
        # Files -- hashing
        if self.data.get('FA', None):
            Files().get_hashes()

    @staticmethod
    def get_settings():
        if not Path('settings').is_file():
            return None

        data = []

        with open('settings') as f:
            for line in f.readlines():
                data.append(line.strip('\n'))

        return data

    @staticmethod
    def save_settings(data):
        write_data = []
        for item in data:
            if item is not None:
                write_data.append(item)
            else:
                write_data.append('')

        with open('settings', 'w') as f:
            f.write('\n'.join(write_data))

    @staticmethod
    def quit_on_yes(selected):
        # Yes is the first button
        if selected == 0:
            raise StopApplication('User requested exit')


def menu(screen, scene):
    main_scene = \
        Scene([MenuFrame(screen)], -1)
    file_picker_scene = \
        Scene([FilepickerFrame(screen)], -1)

    screen.play(
        [main_scene, file_picker_scene],
        stop_on_resize=True,
        start_scene=scene
    )


def main():
    last_scene = None

    while True:
        try:
            Screen.wrapper(menu, catch_interrupt=False, arguments=[last_scene])
            exit_application(0)
        except ResizeScreenError as e:
            last_scene = e.scene


if __name__ == '__main__':
    main()
