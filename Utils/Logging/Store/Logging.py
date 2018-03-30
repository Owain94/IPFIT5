from datetime import datetime
from typing import Dict, Union

from pydux import create_store

from Utils.Logging.Store.Actions.LoggingActions import LoggingStoreActions
from Utils.Singleton import Singleton
from Utils.Store.Credentials import CredentialStore
from Utils.XlsxWriter import XlsxWriter


class LoggingStore(metaclass=Singleton):
    def __init__(self) -> None:
        self.logging_store = create_store(self.logging)
        self.logging_store.subscribe(self.log_added)

        self.log = []

    def log_added(self) -> None:
        """
        Add a log the all logs

        :return: None
        """
        log = self.logging_store.get_state()
        self.log.append([
            log.get('when'),
            log.get('why'),
            log.get('what'),
            log.get('how'),
            log.get('result')
        ])

    def format_logs(self):
        """
        Format the log items

        :return: Formatted logs
        """
        credentials = CredentialStore().credential_store.get_state()

        log = []

        for item in self.log:
            log.append([
                credentials.get('name'),
                item[0].strftime("%d-%m-%Y %H:%M:%S"),
                credentials.get('location'),
                item[2],
                item[1],
                item[3],
                'IPFIT5.py',
                item[4]
            ])

        return log

    def save_log(self) -> None:
        """
        Save the logs to a XLSX workbook

        :return:  None
        """
        logs = self.format_logs()

        headers = [
            'Who',
            'When',
            'Where',
            'What',
            'Why',
            'How',
            'With',
            'Result'
        ]

        xlsx_writer = XlsxWriter('logbook')
        xlsx_writer.add_worksheet('Logging')
        xlsx_writer.write_headers('Logging', headers)
        xlsx_writer.write_items('Logging', logs)
        xlsx_writer.close()

    def logging(self, state: Dict[str, str],
                action: Dict[str, Union[Dict[str, str], str]]) \
            -> Dict[str, str]:
        """
        Handle state changes

        :param state: State
        :param action: Action

        :return: Mutated state
        """
        if action.get('type') == LoggingStoreActions.ADD_LOG:
            state = {
                'when': datetime.now(),
                'why': action.get('log').get('why'),
                'what': action.get('log').get('what'),
                'how': action.get('log').get('how'),
                'result': action.get('log').get('result')
            }
        if action.get('type') == LoggingStoreActions.SAVE_TO_DISK:
            self.save_log()
        return state
