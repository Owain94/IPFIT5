from copy import copy, deepcopy
from datetime import datetime
from gzip import GzipFile
from hashlib import sha256
from io import BytesIO
from multiprocessing import Pool, cpu_count
from os import SEEK_END
from tarfile import TarFile
from time import sleep
from typing import List, Union
from zipfile import ZipFile, BadZipFile
from zlib import error as zlib_error

from langdetect import detect_langs

from Interfaces.ModuleInterface import ModuleInterface
from Utils.ImageHandler import ImageHandler
from Utils.Logging.Logging import Logging
from Utils.XlsxWriter import XlsxWriter

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

    @staticmethod
    def zipped_sha_hash(file):
        sha256_sum = sha256()

        buf = file.read()
        sha256_sum.update(buf)

        return sha256_sum.hexdigest()

    @staticmethod
    def zipped_language(file, raw=False):
        languages_string = ''
        text = file.readlines()
        decoded = ''
        if raw:
            decoded = file
        else:
            for i in text:
                try:
                    decoded += i.decode('utf-8')
                except UnicodeDecodeError:
                    try:
                        decoded += i.decode('utf-8')
                    except UnicodeDecodeError:
                        pass

        languages = detect_langs(decoded)

        if languages is not None:
            languages_string = ', '.join(
                ['{:.2f}% {}'.format(
                    float(str(lang)[3:]) * 100,
                    lang_dict[str(lang)[:2]]
                ) for lang in languages])

        return languages_string

    def zip_file(self, file, partition, _, path):
        lst = []

        try:
            with ZipFile(file) as zf:
                for file_info in zf.infolist():
                    try:
                        filename = file_info.filename.split('/')[-1] \
                            if '.' in file_info.filename else \
                            file_info.filename.replace('/', '')

                        extension = file_info.filename.split('.')[-1].lower() \
                            if '.' in file_info.filename else ''

                        fd = 'FILE' \
                            if file_info.compress_size != 0 \
                               and file_info.file_size != 0 \
                            else 'DIR'

                        size = '{} / {}'.format(file_info.compress_size,
                                                file_info.file_size) \
                            if file_info.compress_size != 0 \
                               and file_info.file_size != 0 \
                            else ''

                        file_path = '{}/{}'.format(path, file_info.filename)

                        item = [
                            partition,
                            filename,
                            extension,
                            fd,
                            '',
                            datetime(*file_info.date_time),
                            '',
                            size,
                            file_path
                        ]

                        if fd == 'FILE':
                            file = BytesIO(zf.read(file_info))
                            item.append(self.zipped_sha_hash(file))
                        else:
                            item.append('')

                        if extension == 'txt':
                            item.append(
                                self.zipped_language(
                                    BytesIO(zf.read(file_info.filename))))
                        else:
                            item.append('')

                        lst.append(item)
                    except zlib_error:
                        continue
                    except BadZipFile:
                        continue
        except BadZipFile:
            pass

        return lst

    def tar_file(self, file, partition, _, path):
        lst = []

        with TarFile(fileobj=file) as zf:
            for member in zf.getnames():
                if '._' not in member:
                    f = zf.extractfile(member)

                    filename = member.split('/')[-1] if '.' in member else \
                        member.replace('/', '')

                    extension = member.split('.')[-1].lower() \
                        if '.' in member else ''

                    f.seek(0, SEEK_END)

                    item = [
                        partition,
                        filename,
                        extension,
                        'FILE',
                        '',
                        '',
                        '',
                        f.tell(),
                        '{}/{}'.format(path, member),
                        self.zipped_sha_hash(f)
                    ]

                    if extension == 'txt':
                        item.append(self.zipped_language(f.read()))
                    else:
                        item.append('')

                    lst.append(item)

        return lst

    def gzip_file(self, file, partition, filename, path):
        lst = []
        with GzipFile(fileobj=file) as zf:
            file_content = BytesIO(zf.read())

            name = ImageHandler().rreplace(filename, '.gz', '')

            extension = name.split('.')[-1].lower() \
                if '.' in name else ''

            item = [
                partition,
                name,
                extension,
                'FILE',
                '',
                '',
                '',
                len(file_content.getbuffer()),
                '{}/{}'.format(path, name),
                self.zipped_sha_hash(file_content)
            ]

            if extension == 'txt':
                item.append(self.zipped_language(file_content))
            else:
                item.append('')

            lst.append(item)

            if extension == 'tar':
                tar = self.tar_file(file_content, partition, filename, path)

                for item in tar:
                    lst.append(item)

        return lst

    def compressed_files(self, file):
        stream = ImageHandler().single_file(int(file[0][-1]),
                                            ImageHandler.rreplace(
                                                file[8],
                                                file[1],
                                                ''),
                                            file[1])

        return {
            'zip': self.zip_file,
            'gz': self.gzip_file
        }.get(file[2], 'pass')(BytesIO(stream), file[0], file[1], file[8])

    def get_files(self) -> None:
        data = ImageHandler().files()

        lst = []
        count = 0
        for item in data[0]:
            item[0:0] = [count]
            count += 1
            lst.append(item)
            if any(ext == item[3] for ext in ['zip', 'gz']) \
                    and not item[2].startswith('._'):
                for i in self.compressed_files(item[1:]):
                    i[0:0] = [count]
                    count += 1
                    lst.append(i)

        # file_list = []
        #
        # for i, f in enumerate(data[0]):
        #     f[0:0] = [i]
        #     file_list.append(f)

        self.data['files'] = lst

    # noinspection PyUnresolvedReferences
    def timeline(self):
        results = []

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
            key=lambda x: x[5] if isinstance(x[5], datetime) else datetime.min)

        self.data['timeline'] = results

    @staticmethod
    def detect_language(file: List[Union[str, datetime]]) \
            -> List[Union[str, datetime]]:
        if len(file) > 10:
            return file

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
        if len(file) > 10:
            return file

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

        self.data['hashing'] = [x for x in results if x[10] != '']

    def format_items(self, part: str) -> List[Union[str, int]]:
        items = []

        if part == 'hashing' or part == 'language':
            data = sorted(self.data[part])
        elif part == 'combined':
            data = self.combined_data()
        else:
            data = deepcopy(self.data[part])

        for item in data:
            item.pop(0)
            if part == 'files' or part == 'timeline':
                if len(item) > 9:
                    del item[9:11]
            if part == 'hashing':
                if len(item) > 10:
                    item.pop(10)
            if part == 'language':
                if len(item) > 10:
                    item.pop(9)

            item[4] = item[4].strftime('%d-%m-%Y %H:%M:%S') if \
                isinstance(item[4], datetime) else ''
            item[5] = item[5].strftime('%d-%m-%Y %H:%M:%S') if \
                isinstance(item[5], datetime) else ''
            item[6] = item[6].strftime('%d-%m-%Y %H:%M:%S') if \
                isinstance(item[6], datetime) else ''
            item[7] = str(item[7])

            items.append(item)

        return items

    def combined_data(self):
        if self.options['timeline']:
            data = deepcopy(self.data['timeline'])
        else:
            data = deepcopy(self.data['files'])

        lst = []

        for item in data:
            if len(item) > 10:
                if not self.options['hashing']:
                    item.pop(10)

                if not self.options['language'] and not \
                        self.options['hashing']:
                    item.pop(10)
                elif not self.options['language']:
                    item.pop(11)
            else:
                if self.options['hashing']:
                    y = [i for i in self.data['hashing'] if i[0] == item[0]]
                    if y:
                        item.append(y[0][10])
                    else:
                        item.append('')

                if self.options['language']:
                    y = [i for i in self.data['language'] if i[0] == item[0]]
                    if y:
                        item.append(y[0][10])
                    else:
                        item.append('')

            lst.append(item)

        return lst

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
        xlsx_writer.write_items('Combined', self.format_items('combined'))

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
