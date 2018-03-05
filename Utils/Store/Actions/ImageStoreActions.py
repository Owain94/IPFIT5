class ImageStoreActions:
    SET_IMAGE = 'SET_IMAGE'
    RESET_STATE = 'RESET_STATE'

    @staticmethod
    def set_image(file_path):
        return {
            'type': ImageStoreActions.SET_IMAGE,
            'image': file_path
        }
