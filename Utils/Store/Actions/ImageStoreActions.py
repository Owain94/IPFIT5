from typing import Dict


class ImageStoreActions:
    SET_IMAGE = 'SET_IMAGE'
    RESET_STATE = 'RESET_STATE'

    @staticmethod
    def set_image(file_path: str) -> Dict[str, str]:
        return {
            'type': ImageStoreActions.SET_IMAGE,
            'image': file_path
        }

    @staticmethod
    def reset_state() -> Dict[str, str]:
        return {
            'type': ImageStoreActions.RESET_STATE
        }
