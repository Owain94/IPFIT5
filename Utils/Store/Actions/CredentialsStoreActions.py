class CredentialsStoreActions:
    SET_CREDENTIALS = 'SET_CREDENTIALS'
    SET_NAME = 'SET_NAME'
    SET_LOCATION = 'SET_LOCATION'
    SET_CASE = 'SET_CASE'
    SAVE_TO_DISK = 'SAVE_TO_DISK'

    @staticmethod
    def set_credentials(name, location, case):
        return {
            'type': CredentialsStoreActions.SET_CREDENTIALS,
            'credentials': {
                'name': name,
                'location': location,
                'case': case,
            }
        }

    @staticmethod
    def set_name(name):
        return {
            'type': CredentialsStoreActions.SET_NAME,
            'name': name
        }

    @staticmethod
    def set_location(location):
        return {
            'type': CredentialsStoreActions.SET_LOCATION,
            'location': location
        }

    @staticmethod
    def set_case(case):
        return {
            'type': CredentialsStoreActions.SET_CASE,
            'case': case
        }

    @staticmethod
    def save_to_disk():
        return {
            'type': CredentialsStoreActions.SAVE_TO_DISK
        }
