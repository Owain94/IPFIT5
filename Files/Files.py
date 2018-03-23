from Interfaces.ModuleInterface import ModuleInterface

from Utils.Logging.Logging import Logging
from Utils.ImageHandler import ImageHandler

from Utils.XlsxWriter import XlsxWriter

from time import sleep
from copy import copy, deepcopy
from datetime import datetime
from multiprocessing import Pool, cpu_count

from langdetect import detect_langs

from typing import List, Union

lang_dict = {
    'af': 'Afrikaans',
    'ar': 'Arabic',
    'bg': 'Bulgarian',
    'bn': 'Bengali',
    'ca': 'Catalan',
    'cs': 'Czech',
    'cy': 'Welsh',
    'da': 'Danish',
    'de': 'German',
    'el': 'Greek',
    'en': 'English',
    'es': 'Spanish',
    'et': 'Estonian',
    'fa': 'Persian',
    'fi': 'Finnish',
    'fr': 'French',
    'gu': 'Gujarati',
    'he': 'Hebrew',
    'hi': 'Hindi',
    'hr': 'Croatian',
    'hu': 'Hungarian',
    'id': 'Indonesian',
    'it': 'Italian',
    'ja': 'Japanese',
    'kn': 'Kannada',
    'ko': 'Korean',
    'lt': 'Lithuanian',
    'lv': 'Latvian',
    'mk': 'Macedonian',
    'ml': 'Malayalam',
    'mr': 'Marathi',
    'ne': 'Nepali',
    'nl': 'Dutch',
    'no': 'Norwegian',
    'pa': 'Panjabi',
    'pl': 'Polish',
    'pt': 'Portuguese',
    'ro': 'Romanian',
    'ru': 'Russian',
    'sk': 'Slovak',
    'sl': 'Slovenian',
    'so': 'Somali',
    'sq': 'Albanian',
    'sv': 'Swedish',
    'sw': 'Swahili',
    'ta': 'Tamil',
    'te': 'Telugu',
    'th': 'Thai',
    'tl': 'Tigrinya',
    'tr': 'Turkish',
    'uk': 'Ukrainian',
    'ur': 'Urdu',
    'vi': 'Vietnamese',
    'zh-cn': 'Simplified Chinese',
    'zh-tw': 'Taiwanese Mandarin'
}


class Files(ModuleInterface):
    def __init__(self):
        self.logger = Logging(self.__class__.__name__).logger

        self.options = {}

        self.data = {
            'files': [],
            'hashing': [],
            'timeline': [],
            'language': [],
            'merged': []
        }

        self.headers = [
            'Partition',
            'File',
            'File Ext',
            'File Type',
            'Create Date',
            'Modify Date',
            'Change Date',
            'Size',
            'File Path'
        ]

    def run(self, *args) -> None:
        self.options = {
            'hashing': args[0],
            'timeline': args[1],
            'language': args[2]
        }

        self.get_files()

        if self.options['hashing']:
            self.hashes()

        if self.options['timeline']:
            self.timeline()

        if self.options['language']:
            self.language()

    def results(self) -> None:
        xlsx_writer = None
        count = int(self.options['hashing'])
        count += int(self.options['timeline'])
        count += int(self.options['language'])

        if count > 0:
            xlsx_writer = XlsxWriter('files')

        if count > 1:
            self.save_merged(xlsx_writer)

        if count > 0:
            self.save_files(xlsx_writer)

        if self.options['hashing']:
            self.save_hashes(xlsx_writer)

        if self.options['timeline']:
            self.save_timeline(xlsx_writer)

        if self.options['language']:
            self.save_language(xlsx_writer)

        if count > 0:
            xlsx_writer.close()

    def get_files(self) -> None:
        data = ImageHandler().files()
        file_list = []

        for i, f in enumerate(data[0]):
            f[0:0] = [i]
            file_list.append(f)

        self.data['files'] = file_list

    # noinspection PyUnresolvedReferences
    def timeline(self):
        results = []

        total = len(self.data['files']) + 2

        for item in self.data['files']:
            create = item[5].strftime('%d-%m-%Y %H:%M:%S') if \
                isinstance(item[5], datetime) else None
            modify = item[6].strftime('%d-%m-%Y %H:%M:%S') if \
                isinstance(item[6], datetime) else None
            change = item[7].strftime('%d-%m-%Y %H:%M:%S') if \
                isinstance(item[7], datetime) else None

            results.append(item)

            if all(x is not None for x in [create, modify, change]):
                if create != modify:
                    results.append(copy(item))

                if (create != change and change != modify) or \
                        (modify != change and change != create):
                    results.append(copy(item))

            elif sum(x is not None for x in [create, modify, change]) == 2:
                values = [x for x in [create, modify, change] if x is not None]

                if values[0] != values[1]:
                    results.append(copy(item))

        results.sort(
            key=lambda x: x[7] if isinstance(x[7], datetime) else datetime.min)
        results.sort(
            key=lambda x: x[6] if isinstance(x[6], datetime) else datetime.min)
        results.sort(
            key=lambda x: x[5] if isinstance(x[8], datetime) else datetime.min)

        self.data['timeline'] = results

    @staticmethod
    def detect_language(file: List[Union[str, datetime]]) \
            -> List[Union[str, datetime]]:
        languages = None
        languages_string = ''
        if file[3].lower() == 'txt':
            text = ImageHandler().single_file(int(file[1][-1]),
                                              ImageHandler.rreplace(
                                                  file[9],
                                                  file[2],
                                                  ''),
                                              file[2])
            try:
                languages = detect_langs(text.decode('utf-8'))
            except UnicodeDecodeError:
                try:
                    languages = detect_langs(text.decode('utf-16'))
                except UnicodeDecodeError:
                    pass

            if languages is not None:
                languages_string = ', '.join(['{:.2f}% {}'.format(
                    float(str(lang)[3:]) * 100,
                    lang_dict[str(lang)[:2]]
                ) for lang in languages])

        file.append(languages_string)

        return file

    def language(self) -> None:
        data = [x for x in self.data['files'] if x[3] == 'txt']
        with Pool(processes=cpu_count()) as pool:
            results = []
            [
                pool.apply_async(self.detect_language,
                                 (x,),
                                 callback=results.append)
                for x in data
            ]

            while len(data) != len(results):
                sleep(0.05)

        self.data['language'] = results

    @staticmethod
    def hash(file: List[Union[str, datetime]]) -> List[Union[str, datetime]]:
        sha_sum = ImageHandler().single_file(int(file[1][-1]),
                                             ImageHandler.rreplace(
                                                 file[9],
                                                 file[2],
                                                 ''),
                                             file[2],
                                             True)

        file.append(sha_sum)

        return file

    def hashes(self) -> None:
        with Pool(processes=cpu_count()) as pool:
            results = []
            [
                pool.apply_async(self.hash, (x,), callback=results.append)
                for x in self.data['files']
            ]

            while len(self.data['files']) != len(results):
                sleep(0.05)

        self.data['hashing'] = results

    def format_items(self, part: str) -> List[Union[str, int]]:
        items = []

        if part == 'hashing' or part == 'language':
            data = sorted(self.data[part])
        else:
            data = deepcopy(self.data[part])

        for item in data:
            item.pop(0)
            item[4] = item[4].strftime('%d-%m-%Y %H:%M:%S') if \
                isinstance(item[4], datetime) else ''
            item[5] = item[5].strftime('%d-%m-%Y %H:%M:%S') if \
                isinstance(item[5], datetime) else ''
            item[6] = item[6].strftime('%d-%m-%Y %H:%M:%S') if \
                isinstance(item[6], datetime) else ''

            items.append(item)

        return items

    def save_merged(self, xlsx_writer) -> None:
        lst = []

        if self.options['hashing']:
            lst.append('SHA256 hash')

        if self.options['language']:
            lst.append('Language')

        xlsx_writer.add_worksheet('Combined')
        xlsx_writer.write_headers('Combined', [
            *self.headers,
            *lst
        ])

    def save_files(self, xlsx_writer) -> None:
        xlsx_writer.add_worksheet('Files')
        xlsx_writer.write_headers('Files', self.headers)
        xlsx_writer.write_items('Files', self.format_items('files'))

    def save_hashes(self, xlsx_writer) -> None:
        xlsx_writer.add_worksheet('Hashes')
        xlsx_writer.write_headers('Hashes', [
            *self.headers,
            *['SHA256 hash']
        ])
        xlsx_writer.write_items('Hashes', self.format_items('hashing'))

    def save_timeline(self, xlsx_writer) -> None:
        xlsx_writer.add_worksheet('Timeline')
        xlsx_writer.write_headers('Timeline', self.headers)
        xlsx_writer.write_items('Timeline', self.format_items('timeline'))

    def save_language(self, xlsx_writer) -> None:
        xlsx_writer.add_worksheet('Language')
        xlsx_writer.write_headers('Language', [
            *self.headers,
            *['Language']
        ])
        xlsx_writer.write_items('Language', self.format_items('language'))
