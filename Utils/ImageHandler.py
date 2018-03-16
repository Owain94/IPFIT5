import pyewf
import pytsk3

from os import sep
from re import search, I
from hashlib import sha256
from sys import setrecursionlimit
from pathlib import Path as PathlibPath
from datetime import datetime

from Utils.Singleton import Singleton
from Utils.Store.Image import ImageStore
from Utils.Logging.Logging import Logging

from typing import List, Union, Tuple


class Ewf(pytsk3.Img_Info, metaclass=Singleton):
    def __init__(self, ewf_handle):
        self.ewf_handle = ewf_handle
        # noinspection PyArgumentList
        super(Ewf, self).__init__(url='',
                                  type=pytsk3.TSK_IMG_TYPE_EXTERNAL)

    def close(self):
        self.ewf_handle.close()

    def read(self, offset, size, **kwargs):
        self.ewf_handle.seek(offset)
        return self.ewf_handle.read(size)

    def get_size(self):
        return self.ewf_handle.get_media_size()


class ImageHandler(metaclass=Singleton):
    def __init__(self) -> None:
        self.logger = Logging(self.__class__.__name__).logger
        self.store = ImageStore().image_store

        setrecursionlimit(100000)

        self.image_handle = None

        self.ext = PathlibPath(self.store.get_state()).suffix.lower()[1:]
        self.search_result = None
        self.logger.debug('Extension: ' + self.ext)

        if self.store.get_state() != 'initial':
            if self.encase_image(self.ext):
                self.ewf_handle = pyewf.handle()
                self.ewf_handle.open(pyewf.glob(self.store.get_state()))
                self.logger.debug('EWF handle opened')
                self.logger.info('{} loaded with EWF'.format(
                    self.store.get_state().split(sep)[-1])
                )

                self.image_handle = Ewf(self.ewf_handle)
            else:
                self.image_handle = pytsk3.Img_Info(self.store.get_state())

    def check_file_path(self) -> bool:
        image_path = PathlibPath(self.store.get_state())
        return image_path.is_file()

    def check_file(self) -> bool:
        try:
            self.info()
        except OSError:
            return False
        return True

    def info(self):
        try:
            return pytsk3.Volume_Info(self.image_handle)
        except RuntimeError:
            return None

    def encase_metadata(self) -> Union[List, List[Union[str, str]]]:
        if not self.encase_image(self.ext):
            return []

        handle = self.ewf_handle

        metadata = [
            'EWF Acquisition Metadata',
            ''
        ]

        headers = handle.get_header_values()
        hashes = handle.get_hash_values()

        for k in headers:
            metadata.append("- {}: {}".format(k.replace('_', ' ').capitalize(),
                                              headers[k]))
        metadata.append('')

        for h in hashes:
            metadata.append("- {}: {}".format(h, hashes[h]))
        metadata.append(
            "- Bytes per Sector: {}".format(handle.bytes_per_sector))
        metadata.append(
            "- Number of Sectors: {}".format(handle.get_number_of_sectors()))
        metadata.append("- Total Size: {}".format(handle.get_media_size()))

        return metadata

    def volume_info(self) -> List[Union[str, str]]:
        volume = self.info()

        volume_info = [
            'Volume information',
            '',
            '- Amount of partitions: {}'.format(volume.info.part_count)
        ]

        for part in volume:
            volume_info.append('')
            volume_info.append('- Partition address: {}'.format(part.addr))
            volume_info.append('- Partition start: {}'.format(part.start))
            volume_info.append(
                '- Partition length (relative): {}'.format(
                    part.start + part.len - 1))
            volume_info.append('- Partition length: {}'.format(part.len))
            volume_info.append(
                '- Partition description: {}'.format(
                    part.desc.decode('UTF-8')))

        return volume_info

    @staticmethod
    def encase_image(ext: str) -> bool:
        return ext == 'e01' or ext == 's01' or ext == 'ex01' \
            or ext == 'l01' or ext == 'lx01'

    @staticmethod
    def rreplace(s: str, old: str, new: str) -> str:
        return (s[::-1].replace(old[::-1], new[::-1], 1))[::-1]

    @staticmethod
    def partition_check(part: pytsk3.TSK_VS_PART_INFO) -> bool:
        tables_to_ignore = ['Unallocated', 'Extended', 'Primary Table']
        decoded = part.desc.decode('UTF-8')

        return part.len > 2048 and not any(
            table for
            table in tables_to_ignore
            if table in decoded
        )

    def get_handle(self) -> Tuple[pytsk3.Volume_Info, pytsk3.Img_Info]:
        return self.info(), self.image_handle

    @staticmethod
    def open_fs_single_vol(img: pytsk3.Img_Info, path: str) -> \
            Union[Tuple[pytsk3.FS_Info, pytsk3.Directory], Tuple[None, None]]:
        try:
            fs = pytsk3.FS_Info(img)
            # noinspection PyArgumentList
            root = fs.open_dir(path=path)

            return fs, root
        except IOError:
            pass

            return None, None
        except RuntimeError:
            pass

            return None, None

    @staticmethod
    def open_fs(img: pytsk3.Img_Info, vol: pytsk3.Volume_Info, path: str,
                part: pytsk3.Volume_Info) -> \
            Union[Tuple[pytsk3.FS_Info, pytsk3.Directory], Tuple[None, None]]:
        try:
            fs = pytsk3.FS_Info(
                img, offset=part.start * vol.info.block_size)
            # noinspection PyArgumentList
            root = fs.open_dir(path=path)

            return fs, root
        except IOError:
            pass

            return None, None
        except RuntimeError:
            return None, None

    @staticmethod
    def nameless_dir(fs_object: pytsk3.File) -> bool:
        return not hasattr(fs_object, 'info') \
            or not hasattr(fs_object.info, 'name') or not hasattr(
            fs_object.info.name, 'name') or \
            fs_object.info.name.name.decode('UTF-8') in ['.', '..']

    def single_file(self, partition: int, path: str, filename: str,
                    hashing: bool = False) -> Union[str, bytes, None]:
        vol, img = self.get_handle()
        fs, root = None, None

        if vol is not None:
            all_partitions = [x for x in vol]
            part = all_partitions[partition]
            if self.partition_check(part):
                fs, root = self.open_fs(img, vol, path, part)
        else:
            fs, root = self.open_fs_single_vol(img, path)

        if fs is not None and root is not None:
            try:
                for fs_object in root:
                    if self.nameless_dir(fs_object):
                        continue

                    try:
                        file_name = fs_object.info.name.name.decode('UTF-8')

                        if file_name.lower() == filename.lower():
                            return self.hash_file(fs_object) if hashing else \
                                self.read_file(fs_object)
                    except IOError:
                        pass
            except RuntimeError:
                pass

        return '' if hashing else None

    def files(self, search_str: str = None) -> \
            List[List[Union[str, datetime]]]:
        vol, img = self.get_handle()
        recursed_data = []

        # Open FS and Recurse
        if vol is not None:
            for part in vol:
                if self.partition_check(part):
                    fs, root = self.open_fs(img, vol, '/', part)
                    if fs is not None and root is not None:
                        data = self.recurse_files(part.addr, fs, root, [],
                                                  [], [''], search_str)
                        recursed_data.append(data)
        else:
            fs, root = self.open_fs_single_vol(img, '/')
            if fs is not None and root is not None:
                data = self.recurse_files(1, fs, root, [], [], [''],
                                          search_str)
                recursed_data.append(data)

        return recursed_data

    def recurse_files(self, part: int, fs: pytsk3.FS_Info,
                      root_dir: pytsk3.Directory, dirs: List[pytsk3.Directory],
                      data: List[List[Union[str, datetime]]],
                      parent: List[str], search_str: str = None) -> \
            List[List[Union[str, datetime]]]:
        # print('Recurse')
        dirs.append(root_dir.info.fs_file.meta.addr)
        for fs_object in root_dir:
            # Skip '.', '..' or directory entries without a name.
            if self.nameless_dir(fs_object):
                continue
            try:
                file_name = fs_object.info.name.name.decode('UTF-8')
                file_path = '{}/{}'.format(
                    '/'.join(parent),
                    fs_object.info.name.name.decode('UTF-8'))
                try:
                    if fs_object.info.meta.type == \
                            pytsk3.TSK_FS_META_TYPE_DIR:
                        f_type = 'DIR'
                        file_ext = ''
                    else:
                        f_type = 'FILE'
                        file_ext = file_name.rsplit('.')[-1].lower() \
                            if '.' in file_name else ''
                except AttributeError:
                    continue

                if search_str is None or search(search_str,
                                                file_name,
                                                I) is not None:
                    size = fs_object.info.meta.size
                    create = self.convert_time(fs_object.info.meta.crtime)
                    change = self.convert_time(fs_object.info.meta.ctime)
                    modify = self.convert_time(fs_object.info.meta.mtime)

                    data.append(
                        ['PARTITION {}'.format(part), file_name, file_ext,
                         f_type, create, change, modify, size, file_path])

                if f_type == 'DIR':
                    parent.append(fs_object.info.name.name.decode('UTF-8'))
                    sub_directory = fs_object.as_directory()
                    inode = fs_object.info.meta.addr

                    # This ensures that we don't recurse into a directory
                    # above the current level and thus avoid circular loops.
                    if inode not in dirs:
                        self.recurse_files(part, fs, sub_directory,
                                           dirs, data, parent, search_str)
                    parent.pop(-1)

            except IOError:
                pass
        dirs.pop(-1)
        return data

    @staticmethod
    def read_file(fs_object: pytsk3.File) -> bytes:
        offset = 0
        size = getattr(fs_object.info.meta, "size", 0)

        return fs_object.read_random(offset, size)

    @staticmethod
    def hash_file(fs_object: pytsk3.File) -> str:
        offset = 0
        buff_size = 1024 * 1024
        size = getattr(fs_object.info.meta, "size", 0)

        sha256_sum = sha256()
        while offset < size:
            available_to_read = min(buff_size, size - offset)
            data = fs_object.read_random(offset, available_to_read)
            if not data:
                break

            offset += len(data)
            sha256_sum.update(data)
        return sha256_sum.hexdigest()

    @staticmethod
    def convert_time(ts: float) -> Union[str, datetime]:
        return '' if str(ts) == '0' else datetime.utcfromtimestamp(ts)
