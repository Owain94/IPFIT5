from pydux import create_store

from pathlib import Path
from os import linesep

from Utils.Debounce import debounce
from Utils.Singleton import Singleton
from Utils.Store.Actions.CredentialsStoreActions import CredentialsStoreActions

from typing import Dict, Union


class CredentialStore(metaclass=Singleton):
    def __init__(self) -> None:
        self.credential_store = create_store(self.credentials)
        self.credential_store.subscribe(self.credentials_changed)

    @debounce(0.25)
    def credentials_changed(self) -> None:
        self.write_config_to_disk(
            CredentialStore.get_config_save_path("credentials"),
            self.credential_store.get_state()
        )

    @staticmethod
    def get_config_save_path(config: str) -> Path:
        # Make config folder
        config_path = Path(__file__).parent.parent.parent.joinpath('Configs')
        Path.mkdir(Path(config_path), exist_ok=True)

        # Make config file
        config_file_path = Path(config_path.joinpath("{0}.cfg".format(config)))
        Path.touch(config_file_path, exist_ok=True)

        return config_file_path

    @staticmethod
    def write_config_to_disk(path: Path, config: Dict[str, str]) -> None:
        with open(path, 'w') as file:
            file.writelines(
                linesep.join([str(x) + ":" + str(y)
                              for x, y in config.items()])
            )

    @staticmethod
    def read_config_from_disk(path: Path, defaults: Dict[str, str]) -> \
            Dict[str, str]:
        with open(path, 'r') as file:
            lines = {
                split_line[0]: ":".join(split_line[1::]) for split_line in
                [line.strip().split(':') for line in file.readlines()]
            }

        for key in defaults.keys():
            if key in lines:
                defaults[key] = lines[key]

        return defaults

    @staticmethod
    def credentials(state: Dict[str, str],
                    action: Dict[str, Union[Dict[str, str], str]]) \
            -> Dict[str, str]:
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
