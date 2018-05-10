from collections import defaultdict
from datetime import datetime
from multiprocessing import Process
from sys import exit as exit_application

from asciimatics.exceptions import ResizeScreenError, NextScene, \
    StopApplication
from asciimatics.scene import Scene
from asciimatics.screen import Screen
from asciimatics.widgets import Frame, Text, TextBox, Layout, Label, Divider, \
    CheckBox, Button, PopUpDialog

from Files.Files import Files
from Photos import Photo
from IP import capreader

from os import path, listdir

from Utils.FilePicker import FilepickerFrame
from Utils.ImageHandler import ImageHandler
from Utils.Logging.Store.Logging import LoggingStore
from Utils.Logging.Store.Logging import LoggingStoreActions
from Utils.Store.Actions.CredentialsStoreActions import CredentialsStoreActions
from Utils.Store.Credentials import CredentialStore
from Utils.Store.Image import ImageStore


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

        self.image_handler = None
        self.image_store = ImageStore().image_store
        credentials = CredentialStore()
        self.credentials_store = credentials.credential_store
        self.logging_store = LoggingStore()

        credentials.time = datetime.now().strftime("%d-%m-%Y-%H%M%S")

        self.logging_store.logging_store.dispatch(
            LoggingStoreActions.add_log(
                why='Image analyzing',
                what='Started IPFIT5.py',
                how='Terminal',
                result='Application started'
            )
        )

        self.get_settings()

        # noinspection PyArgumentList
        super(MenuFrame, self).__init__(screen,
                                        screen.height - 2,
                                        screen.width - 2,
                                        data=self.form_data,
                                        has_shadow=True,
                                        has_border=True,
                                        can_scroll=False,
                                        name='IPFIT5')

        self._screen = screen

        self.image_store.subscribe(lambda: self.set_image())

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

        self.photos_btn = CheckBox('Analyze photo\'s',
                                   label='',
                                   name='PA',
                                   on_change=self.on_change)
        self.photos_btn.disabled = True

        self.files_one_btn = CheckBox('Hashing',
                                      label='',
                                      name='FA',
                                      on_change=self.on_change)
        self.files_one_btn.disabled = True
        self.files_two_btn = CheckBox('Create timeline',
                                      label='',
                                      name='FB',
                                      on_change=self.on_change)
        self.files_two_btn.disabled = True
        self.files_three_btn = CheckBox('Detect language',
                                        label='',
                                        name='FC',
                                        on_change=self.on_change)
        self.files_three_btn.disabled = True

        self.pcap_btn = CheckBox('Analyze PCAPs',
                                 label='',
                                 name='IB',
                                 on_change=self.on_change)
        self.pcap_btn.disabled = True

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

        image_layout = Layout([1, 50, 1])
        self.add_layout(image_layout)

        image_layout.add_widget(Divider(height=3), 1)

        image_layout.add_widget(self.image_label, 1)

        image_buttons_layout = Layout([1, 25, 25, 1])
        self.add_layout(image_buttons_layout)

        image_buttons_layout.add_widget(
            Button('Select image/PCAP', self.file_picker), 1)
        image_buttons_layout.add_widget(self.image_info_button, 2)
        image_buttons_layout.add_widget(Divider(height=3), 1)
        image_buttons_layout.add_widget(Divider(height=3), 2)

        photos_layout = Layout([1, 50, 1])
        self.add_layout(photos_layout)

        photos_layout.add_widget(Label('Photo\'s', height=2), 1)
        photos_layout.add_widget(self.photos_btn, 1)
        photos_layout.add_widget(Divider(height=3), 1)

        files_layout = Layout([1, 50, 1])
        self.add_layout(files_layout)

        files_layout.add_widget(Label('Files', height=2), 1)
        files_layout.add_widget(self.files_one_btn, 1)
        files_layout.add_widget(self.files_two_btn, 1)
        files_layout.add_widget(self.files_three_btn, 1)
        files_layout.add_widget(Divider(height=3), 1)

        ip_layout = Layout([1, 50, 1])
        self.add_layout(ip_layout)

        ip_layout.add_widget(Label(label='IP', height=2), 1)
        ip_layout.add_widget(self.pcap_btn, 1)
        ip_layout.add_widget(Divider(height=3), 1)

        buttons_layout = Layout([1, 1])
        self.add_layout(buttons_layout)

        buttons_layout.add_widget(Button('Run', self.run), 0)
        buttons_layout.add_widget(Button('Quit', self.quit), 1)

        self.fix()

    def set_image(self):
        if self.image_store.get_state() == 'initial':
            return

        self.image_handler = ImageHandler()

        if self.image_handler.check_file():
            self.form_data['IA'] = self.image_store.get_state()
            self.image_info_button.disabled = False

            self.photos_btn.disabled = False
            self.files_one_btn.disabled = False
            self.files_two_btn.disabled = False
            self.files_three_btn.disabled = False
            self.pcap_btn.disabled = True
        else:
            self.image_info_button.disabled = True
            self.photos_btn.disabled = True
            self.files_one_btn.disabled = True
            self.files_two_btn.disabled = True
            self.files_three_btn.disabled = True
            self.pcap_btn.disabled = False


        self.save()

    def on_change(self):
        self.save()
        self.image_info_button.disabled = \
            self.image_store.get_state() == 'initial'

        cred_state = self.credentials_store.get_state()

        if self.data.get('DA') != cred_state['name'] or \
                self.data.get('DB') != cred_state['location'] or \
                self.data.get('DC') != cred_state['case']:
            self.credentials_store.dispatch(
                CredentialsStoreActions.set_credentials(
                    self.data.get('DA'),
                    self.data.get('DB'),
                    self.data.get('DC')
                )
            )

    def file_picker(self):
        raise NextScene('FilePicker')

    def file_info(self):
        metadata = self.image_handler.encase_metadata()
        volume_information = self.image_handler.volume_info()

        if len(metadata) > 0:
            metadata.append('')

        self._scene.add_effect(
            PopUpDialog(self._screen,
                        '\n'.join([*metadata, *volume_information]), ['OK']))

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

        if image is None or self.image_store.get_state() == 'initial':
            msg.append('No image selected')

        if len(msg) > 0:
            self._scene.add_effect(
                PopUpDialog(self._screen, '\n'.join(msg), ['OK']))
        else:
            self.exec()

    @staticmethod
    def exec_photos(photos: Photo.Photos):
        photos.run()
        photos.results()

    def exec_files(self, files: Files):
        files.run(
            self.data.get('FA', False),
            self.data.get('FB', False),
            self.data.get('FC', False)
        )
        files.results()

    @staticmethod
    def exec_ip(ip: capreader.PcapReader):
        ip.run()
        ip.results()

    def exec(self):
        photos = Photo.Photos()
        files = Files()

        pth = path.dirname(self.image_store.get_state())

        onlyfiles = [f for f in listdir(pth)
                     if path.isfile(path.join(pth, f))]

        fls = []

        for i in onlyfiles:
            ext = path.splitext(i)[1][1:]

            if ext.lower() == 'pcap' or ext.lower() == 'pcapng':
                if '._' not in i:
                    fls.append(path.join(pth, i))

        ip = capreader.PcapReader(fls)

        execute_list = []

        if self.data.get('PA', False):
            execute_list.append(
                Process(target=self.exec_photos, args=(photos,))
            )

        if self.data.get('FA', False) or \
                self.data.get('FB', False) or \
                self.data.get('FC', False):
            execute_list.append(
                Process(target=self.exec_files, args=(files,))
            )

        if self.data.get('IB', False):

            self.exec_ip(ip)

        processes = []
        for p in execute_list:
            p.start()
            processes.append(p)

        for p in processes:
            p.join()

        self._scene.add_effect(
            PopUpDialog(self._screen, 'All jobs have finished!', ['OK'],
                        on_close=self.quit_on_yes))

    def get_settings(self):
        settings = self.credentials_store.get_state()

        self.form_data['DA'] = settings['name']
        self.form_data['DB'] = settings['location']
        self.form_data['DC'] = settings['case']

    @staticmethod
    def quit_on_yes(selected):
        if selected == 0:
            raise StopApplication('User requested exit')


def menu(screen, scene):
    main_scene = \
        Scene([MenuFrame(screen)], -1, name='Main')
    file_picker_scene = \
        Scene([FilepickerFrame(screen)], -1, name='FilePicker')

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
