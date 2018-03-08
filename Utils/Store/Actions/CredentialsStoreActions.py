from typing import Dict, Union


class CredentialsStoreActions:
    SET_CREDENTIALS = 'SET_CREDENTIALS'
    SET_NAME = 'SET_NAME'
    SET_LOCATION = 'SET_LOCATION'
    SET_CASE = 'SET_CASE'
    SAVE_TO_DISK = 'SAVE_TO_DISK'

    @staticmethod
    def set_credentials(name: str, location: str, case: str) -> \
            Dict[str, Union[str, Dict[str, str]]]:
        return {
            'type': CredentialsStoreActions.SET_CREDENTIALS,
            'credentials': {
                'name': name,
                'location': location,
                'case': case,
            }
        }

    @staticmethod
    def set_name(name: str) -> Dict[str, str]:
        return {
            'type': CredentialsStoreActions.SET_NAME,
            'name': name
        }

    @staticmethod
    def set_location(location: str) -> Dict[str, str]:
        return {
            'type': CredentialsStoreActions.SET_LOCATION,
            'location': location
        }

    @staticmethod
    def set_case(case: str) -> Dict[str, str]:
        return {
            'type': CredentialsStoreActions.SET_CASE,
            'case': case
        }

    @staticmethod
    def save_to_disk() -> Dict[str, str]:
        return {
            'type': CredentialsStoreActions.SAVE_TO_DISK
        }
