from typing import Dict


class ImageStoreActions:
    SET_IMAGE = 'SET_IMAGE'
    RESET_STATE = 'RESET_STATE'

    @staticmethod
    def set_image(file_path: str) -> Dict[str, str]:
        """
        Set image action

        :param file_path: Selected file

        :return: Action result
        """
        return {
            'type': ImageStoreActions.SET_IMAGE,
            'image': file_path
        }

    @staticmethod
    def reset_state() -> Dict[str, str]:
        """
        Reset state

        :return: Default state
        """
        return {
            'type': ImageStoreActions.RESET_STATE
        }
