from typing import Dict

from pydux import create_store

from Utils.Singleton import Singleton
from Utils.Store.Actions.ImageStoreActions import ImageStoreActions


class ImageStore(metaclass=Singleton):
    def __init__(self) -> None:
        self.image_store = create_store(self.image)

    @staticmethod
    def image(state: str, action: Dict[str, str]) -> str:
        """
        Handle state changes

        :param state: State
        :param action: Action

        :return: Mutated state
        """
        if state is None:
            state = 'initial'
        elif action.get('type') == ImageStoreActions.SET_IMAGE:
            state = action.get('image')
        elif action.get('type') == ImageStoreActions.RESET_STATE:
            state = 'initial'
        return state
