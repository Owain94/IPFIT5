import pydux

from Utils.Debounce import debounce
from Utils.Singleton import Singleton
from pathlib import Path
from os import linesep

from typing import Dict, Union


class CredentialStore(metaclass=Singleton):
    def __init__(self) -> None:
        self.credential_store = pydux.create_store(self.credential)
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

        for key, value in defaults.items():
            if key in lines:
                defaults[key] = lines[key]

        return defaults

    @staticmethod
    def credential(state: Dict[str, str],
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

        if action is None:
            return state
        elif action['type'] == 'set_credentials':
            state = {
                'name': action['credentials']['name'],
                'location': action['credentials']['location'],
                'case': action['credentials']['case'],
            }
        elif action['type'] == 'set_location':
            state['location'] = action['location']
        elif action['type'] == 'set_name':
            state['location'] = action['name']
        elif action['type'] == 'set_case':
            state['case'] = action['case']
        elif action['type'] == 'save_to_disk':
            CredentialStore.write_config_to_disk(
                CredentialStore.get_config_save_path("credentials"),
                state
            )
        return state
