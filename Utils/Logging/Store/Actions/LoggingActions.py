from datetime import datetime

from typing import Dict, Union


class LoggingStoreActions:
    ADD_LOG = 'ADD_LOG'
    SAVE_TO_DISK = 'SAVE_TO_DISK'

    @staticmethod
    def add_log(what: str,
                why: str,
                how: str,
                result: str) -> \
            Dict[str, Union[str, Dict[str, Union[datetime, str]]]]:
        """
        Add log action

        :param what: What
        :param why: Why
        :param how: How
        :param result: Result

        :return: Action result
        """
        return {
            'type': LoggingStoreActions.ADD_LOG,
            'log': {
                'why': why,
                'what': what,
                'how': how,
                'result': result
            }
        }

    @staticmethod
    def save_to_disk():
        """
        Save to disk action

        :return: Action result
        """
        return {
            'type': LoggingStoreActions.SAVE_TO_DISK
        }
