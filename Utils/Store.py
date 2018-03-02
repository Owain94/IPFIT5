import pydux
from Utils.Singleton import Singleton


class Store(metaclass=Singleton):
    def __init__(self):
        self.image_store = pydux.create_store(self.image)
        self.credential_store = pydux.create_store(self.credential)

    @staticmethod
    def credential(state: str, action: [str, str]) -> str:
        if state is None:
            state = {
                'name': '',
                'location': '',
                'case': ''
            }
        if action is None:
            return state
        elif action == 'set_credentials':
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
        return state

    @staticmethod
    def image(state, action):
        if state is None:
            state = 'initial'
        if action is None:
            return state
        elif action['type'] == 'set_image':
            state = action['image']
        return state
