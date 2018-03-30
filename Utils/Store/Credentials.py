from os import linesep
from pathlib import Path
from typing import Dict, Union

from pydux import create_store

from Utils.Debounce import debounce
from Utils.Singleton import Singleton
from Utils.Store.Actions.CredentialsStoreActions import CredentialsStoreActions


class CredentialStore(metaclass=Singleton):
    def __init__(self) -> None:
        self.credential_store = create_store(self.credentials)
        self.credential_store.subscribe(self.credentials_changed)
        self._time = None

    @debounce(0.25)
    def credentials_changed(self) -> None:
        """
        Debounced function when the config is changed

        :return: None
        """
        self.write_config_to_disk(
            CredentialStore.get_config_save_path("credentials"),
            self.credential_store.get_state()
        )

    @staticmethod
    def get_config_save_path(config: str) -> Path:
        """
        Get a path to save the config to

        :param config: Config name

        :return: Path to file
        """
        # Make config folder
        config_path = Path(__file__).parent.parent.parent.joinpath('Configs')
        Path.mkdir(Path(config_path), exist_ok=True)

        # Make config file
        config_file_path = Path(config_path.joinpath("{0}.cfg".format(config)))
        Path.touch(config_file_path, exist_ok=True)

        return config_file_path

    @staticmethod
    def write_config_to_disk(path: Path, config: Dict[str, str]) -> None:
        """
        Save the current config to a f7ile on the disk


        :param path: Path on the file
        :param config: Gonfig to save

        :return: None
        """
        with open(path, 'w') as file:
            file.writelines(
                linesep.join([str(x) + ":" + str(y)
                              for x, y in config.items()])
            )

    @staticmethod
    def read_config_from_disk(path: Path, defaults: Dict[str, str]) -> \
            Dict[str, str]:
        """
        Get the credentials from a file on the disk

        :param path: Path to the saved config
        :param defaults: Default values

        :return:
        """
        with open(path, 'r') as file:
            lines = {
                split_line[0]: ":".join(split_line[1::]) for split_line in
                [line.strip().split(':') for line in file.readlines()]
            }

        for key in defaults.keys():
            if key in lines:
                defaults[key] = lines[key]

        return defaults

    @property
    def time(self):
        """
        Get start time of the application

        :return: Starting time
        """
        return self._time

    @time.setter
    def time(self, time):
        """
        Set the start time of the application

        :param time: Current time

        :return: None
        """
        self._time = time

    @staticmethod
    def credentials(state: Dict[str, str],
                    action: Dict[str, Union[Dict[str, str], str]]) \
            -> Dict[str, str]:
        """
        Handle state changes

        :param state: State
        :param action: Action

        :return: Mutated state
        """
        if state is None:
            state = CredentialStore.read_config_from_disk(
                CredentialStore.get_config_save_path('credentials'),
                {
                    'name': '',
                    'location': '',
                    'case': ''
                }
            )

        if action.get('type') == CredentialsStoreActions.SET_CREDENTIALS:
            state = {
                'name': action.get('credentials').get('name'),
                'location': action.get('credentials').get('location'),
                'case': action.get('credentials').get('case'),
            }
        elif action.get('type') == CredentialsStoreActions.SET_LOCATION:
            state['location'] = action.get('location')
        elif action.get('type') == CredentialsStoreActions.SET_NAME:
            state['location'] = action.get('name')
        elif action.get('type') == CredentialsStoreActions.SET_CASE:
            state['case'] = action.get('case')
        elif action.get('type') == CredentialsStoreActions.SAVE_TO_DISK:
            CredentialStore.write_config_to_disk(
                CredentialStore.get_config_save_path("credentials"),
                state
            )
        return state
