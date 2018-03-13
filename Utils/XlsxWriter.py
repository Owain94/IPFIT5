from Utils.Store.Credentials import CredentialStore

from xlsxwriter import Workbook

from pathlib import Path

from typing import List


class XlsxWriter:
    def __init__(self, name: str) -> None:
        self.workbook = Workbook(self.get_save_path(name))
        self.worksheets = []

    @staticmethod
    def get_save_path(name) -> str:
        # Make output folder
        config_path = Path(__file__).parent.parent.joinpath('Output')
        Path.mkdir(Path(config_path), exist_ok=True)

        credentials = CredentialStore()
        case = credentials.credential_store.get_state().get('case')

        # Make case folder
        case_path = Path(config_path.joinpath(case))
        Path.mkdir(Path(case_path), exist_ok=True)

        return str(
            case_path.joinpath('{} - {}.xlsx'.format(
                credentials.time,
                name
            ))
        )

    def add_worksheet(self) -> None:
        self.worksheets.append(self.workbook.add_worksheet())

    def write_headers(self, worksheet: int, headers: List[str]) -> None:
        bold = self.workbook.add_format({'bold': True})
        bold.set_center_across()

        for i, header in enumerate(headers):
            self.worksheets[worksheet].write(0, i, header, bold)

    def write_items(self, worksheet: int, items: List[List[str]]) -> None:
        for i, item_list in enumerate(items):
            for j, item in enumerate(item_list):
                self.worksheets[worksheet].write(i + 2, j, item)

        self.set_width(0, self.get_width(items))

    @staticmethod
    def get_width(items: List[List[str]]) -> List[int]:
        width = [0 for _ in items[0]]

        for item_list in items:
            for j, item in enumerate(item_list):
                if width[j] < len(item):
                    width[j] = len(item)

        return width

    def set_width(self, worksheet: int, width: List[int]) -> None:
        for i, w in enumerate(width):
            self.worksheets[worksheet].set_column(i, i, w + 1)
