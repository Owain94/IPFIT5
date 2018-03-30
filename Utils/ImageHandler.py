from datetime import datetime
from hashlib import sha256
from os import sep
from pathlib import Path as PathlibPath
from pyewf import handle, glob
from pytsk3 import Img_Info, Volume_Info, FS_Info, Directory, File, \
    TSK_VS_PART_INFO, TSK_IMG_TYPE_EXTERNAL, TSK_FS_META_TYPE_DIR
from re import search, I
from sys import setrecursionlimit
from typing import List, Union, Tuple

from Utils.Logging.Logging import Logging
from Utils.Store.Image import ImageStore


class Ewf(Img_Info):
    def __init__(self, ewf_handle):
        self.ewf_handle = ewf_handle
        # noinspection PyArgumentList
        super(Ewf, self).__init__(url='',
                                  type=TSK_IMG_TYPE_EXTERNAL)

    def close(self):
        """
        Closes the ewf handle

        :return: None
        """
        self.ewf_handle.close()

    # noinspection PyUnusedLocal
    def read(self, offset, size, **kwargs):
        """
        Read the ewf file

        :param offset: Offset in bytes
        :param size: Size in bytes
        :param kwargs: Kwargs

        :return: File in bytes
        """
        self.ewf_handle.seek(offset)
        return self.ewf_handle.read(size)

    def get_size(self):
        """
        Get size of ewf

        :return: Size in bytes
        """
        return self.ewf_handle.get_media_size()


class ImageHandler:
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
                self.ewf_handle = handle()
                self.ewf_handle.open(glob(self.store.get_state()))
                self.logger.debug('EWF handle opened')
                self.logger.info('{} loaded with EWF'.format(
                    self.store.get_state().split(sep)[-1])
                )

                self.image_handle = Ewf(self.ewf_handle)
            else:
                self.image_handle = Img_Info(self.store.get_state())

    def check_file_path(self) -> bool:
        """
        Check if the given file exists on the computer

        :return: Whether the file exists or not
        """
        image_path = PathlibPath(self.store.get_state())
        return image_path.is_file()

    def check_file(self) -> bool:
        """
        Check if the file could be read

        :return: Whether file could be read or not
        """
        try:
            self.info()
        except OSError:
            return False
        return True

    def info(self) -> Union[Volume_Info, None]:
        """
        Get volume info from image

        :return: Volume info object
        """
        try:
            return Volume_Info(self.image_handle)
        except RuntimeError:
            return None

    def encase_metadata(self) -> Union[List, List[Union[str, str]]]:
        """
        Get all metadata from an ewf file

        :return: All ewf metadata
        """
        if not self.encase_image(self.ext):
            return []

        ewf_handle = self.ewf_handle

        metadata = [
            'EWF Acquisition Metadata',
            ''
        ]

        headers = ewf_handle.get_header_values()
        hashes = ewf_handle.get_hash_values()

        for k in headers:
            metadata.append("- {}: {}".format(k.replace('_', ' ').capitalize(),
                                              headers[k]))
        metadata.append('')

        for h in hashes:
            metadata.append("- {}: {}".format(h, hashes[h]))
        metadata.append(
            "- Bytes per Sector: {}".format(ewf_handle.bytes_per_sector))
        metadata.append(
            "- Number of Sectors: {}".format(
                ewf_handle.get_number_of_sectors()))
        metadata.append("- Total Size: {}".format(ewf_handle.get_media_size()))

        return metadata

    def volume_info(self) -> List[Union[str, str]]:
        """
        Get all volume info from an image

        :return: All volumes
        """
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
        """
        Check if a file is an ewf file based on the extension

        :param ext: Extension to check

        :return: Whether the file is an ewf image or not
        """
        return ext == 'e01' or ext == 's01' or ext == 'ex01' \
            or ext == 'l01' or ext == 'lx01'

    @staticmethod
    def rreplace(s: str, old: str, new: str) -> str:
        """
        Right replace text in string

        :param s: String to replace a word in
        :param old: The word that will be replaced
        :param new: The world that will replace the old word

        :return: String with te right replaced word
        """
        return (s[::-1].replace(old[::-1], new[::-1], 1))[::-1]

    @staticmethod
    def partition_check(part: TSK_VS_PART_INFO) -> bool:
        """
        Check if the partition is valid

        :param part: Partition object

        :return: Whether the partition is valid or not
        """
        tables_to_ignore = ['Unallocated', 'Extended', 'Primary Table']
        decoded = part.desc.decode('UTF-8')

        return part.len > 2048 and not any(
            table for
            table in tables_to_ignore
            if table in decoded
        )

    def get_handle(self) -> Tuple[Volume_Info, Img_Info]:
        """
        Get the volume info object and the current image handle

        :return: Volume info object and the handle
        """
        return self.info(), self.image_handle

    @staticmethod
    def open_fs_single_vol(img: Img_Info, path: str) -> \
            Union[Tuple[FS_Info, Directory], Tuple[None, None]]:
        """
        Open a single file system

        :param img: Current image handle
        :param path: Path to open on the filesystem

        :return: Filesystem object and the selected directory
        """
        try:
            fs = FS_Info(img)
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
    def open_fs(img: Img_Info, vol: Volume_Info, path: str,
                part: Volume_Info) -> \
            Union[Tuple[FS_Info, Directory], Tuple[None, None]]:
        """
        Open file system

        :param img: Current image handle
        :param vol: Volume in the image
        :param path: Path to open on the filesystem
        :param part: Partition in the image

        :return: Filesystem object and the selected directory
        """
        try:
            fs = FS_Info(
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
    def nameless_dir(fs_object: File) -> bool:
        """
        Check if the directory isn't a current dir or top dir navigation
        symlink

        :param fs_object: file object

        :return: Whether the dir is a navigation symlink
        """
        return not hasattr(fs_object, 'info') \
            or not hasattr(fs_object.info, 'name') or not hasattr(
            fs_object.info.name, 'name') or \
            fs_object.info.name.name.decode('UTF-8') in ['.', '..']

    def single_file(self, partition: int, path: str, filename: str,
                    hashing: bool = False) -> Union[str, bytes, None]:
        """
        Get a single file from an image

        :param partition: Partition in the image to open
        :param path: Path to the file
        :param filename: Filename
        :param hashing: Whether te return the hash of the file or not

        :return: The hash of the file or the tho file as bytes
        """
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
        """
        Get all files in an image

        :param search_str: Search for a specific regex match

        :return: Files in the image
        """
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

    def recurse_files(self, part: int, fs: FS_Info,
                      root_dir: Directory, dirs: List[Directory],
                      data: List[List[Union[str, datetime]]],
                      parent: List[str], search_str: str = None) -> \
            List[List[Union[str, datetime]]]:
        """
        Recurse over all the folder in the image

        :param part: Partition in the image
        :param fs: Filesystem
        :param root_dir: Current directory
        :param dirs: All directories in the current directory
        :param data: All files and directories in the current directory
        :param parent: Parent directory
        :param search_str: Search for a specific regex match

        :return: All recursed data
        """
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
                    if fs_object.info.meta.type == TSK_FS_META_TYPE_DIR:
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
    def read_file(fs_object: File) -> bytes:
        """
        Read the bytes from an fs_object file

        :param fs_object: fs_oject from the image

        :return: Bytes of the fs_object file
        """
        offset = 0
        size = getattr(fs_object.info.meta, "size", 0)

        return fs_object.read_random(offset, size)

    @staticmethod
    def hash_file(fs_object: File) -> str:
        """
        Hash an fs_object from the image

        :param fs_object: fs_oject from the image

        :return: Sha256 of the fs_object file
        """
        if fs_object.info.meta.type == TSK_FS_META_TYPE_DIR:
            return ''

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
        """
        Covert a date time to an UTC timestamp

        :param ts: date time object

        :return: UTC timestamp
        """
        return '' if str(ts) == '0' else datetime.utcfromtimestamp(ts)
