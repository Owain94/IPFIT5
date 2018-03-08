from pydux import create_store

from datetime import datetime

from Utils.Singleton import Singleton
from Utils.Logging.Store.Actions.LoggingActions import LoggingStoreActions

from typing import Dict, Union


class LoggingStore(metaclass=Singleton):
    def __init__(self) -> None:
        self.logging_store = create_store(self.logging)
        self.logging_store.subscribe(self.log_added)

        self.log = []

    def log_added(self) -> None:
        log = self.logging_store.get_state()
        self.log.append([
            log.get('when'),
            log.get('why'),
            log.get('what'),
            log.get('how'),
            log.get('result')
        ])

    def logging(self, state: Dict[str, str],
                action: Dict[str, Union[Dict[str, str], str]]) \
            -> Dict[str, str]:
        if action.get('type') == LoggingStoreActions.ADD_LOG:
            state = {
                'when': datetime.now(),
                'why': action.get('log').get('why'),
                'what': action.get('log').get('what'),
                'how': action.get('log').get('how'),
                'result': action.get('log').get('result')
            }
        if action.get('type') == LoggingStoreActions.SAVE_TO_DISK:
            print(self.log)
        return state
