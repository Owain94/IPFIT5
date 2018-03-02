import pyewf
import pytsk3

from os import sep
from re import search, I
from hashlib import sha256
from sys import setrecursionlimit, exc_info
from pathlib import Path as PathlibPath
from datetime import datetime

from Utils.Store import Store
from Utils.Logging.Logging import Logging


class Ewf(pytsk3.Img_Info):
    def __init__(self, ):
        self.logger = Logging(self.__class__.__name__).logger
        self.store = Store().image_store

        setrecursionlimit(100000)

        self.image_handle = None

        self.ext = PathlibPath(self.store.get_state()).suffix.lower()[1:]
        self.search_result = None
        self.logger.debug('Extension: ' + self.ext)

        if self.encase_image(self.ext):
            self.ewf_handle = pyewf.handle()
            self.ewf_handle.open(pyewf.glob(self.store.get_state()))
            self.logger.debug('EWF handle opened')
            self.logger.info('{} loaded with EWF'.format(
                self.store.get_state().split(sep)[-1]))
            super(Ewf, self).__init__(url='',
                                      type=pytsk3.TSK_IMG_TYPE_EXTERNAL)

    def close(self):
        self.logger.debug('EWF handle closed')
        self.ewf_handle.close()

    def read(self, offset, size):
        self.ewf_handle.seek(offset)
        return self.ewf_handle.read(size)

    def check_file_path(self):
        my_file = PathlibPath(self.store.get_state())
        return my_file.is_file()

    def check_file(self):
        try:
            self.info()
        except OSError:
            return False
        return True

    def get_size(self):
        return self.ewf_handle.get_media_size()

    def info(self):
        if self.encase_image(self.ext):
            volume = pytsk3.Volume_Info(self)
        else:
            self.image_handle = pytsk3.Img_Info(url=self.store.get_state())
            volume = pytsk3.Volume_Info(self.image_handle)

        return volume

    def encase_metadata(self):
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

    def volume_info(self):
        volume = self.info()

        volume_info = [
            'Volume information',
            '',
            '- Amount of partitions: {}'.format(volume.info.part_count),
            ''
        ]

        for part in volume:
            volume_info.append('- Partition address: {}'.format(part.addr))
            volume_info.append('- Partition start: {}'.format(part.start))
            volume_info.append(
                '- Partition length (relative): {}'.format(
                    part.start + part.len - 1))
            volume_info.append('- Partition length: {}'.format(part.len))
            volume_info.append(
                '- Partition description: {}'.format(
                    part.desc.decode('UTF-8')))
            volume_info.append('')

        return volume_info[:-1]

    @staticmethod
    def encase_image(ext):
        return ext == 'e01' or ext == 's01' or ext == 'ex01' \
               or ext == 'l01' or ext == 'lx01'

    @staticmethod
    def rreplace(s, old, new):
        return (s[::-1].replace(old[::-1], new[::-1], 1))[::-1]

    @staticmethod
    def partition_check(part):
        tables_to_ignore = ['Unallocated', 'Extended', 'Primary Table']
        decoded = part.desc.decode('UTF-8')

        return part.len > 2048 and not any(
            table for
            table in tables_to_ignore
            if table in decoded
        )

    def get_handle(self):
        vol = self.info()
        if self.encase_image(self.ext):
            img = self
        else:
            img = self.image_handle

        return vol, img

    @staticmethod
    def open_fs_single_vol(img, path):
        try:
            fs = pytsk3.FS_Info(img)
            root = fs.open_dir(path=path)

            return fs, root
        except IOError:
            _, e, _ = exc_info()
            print('[-] Unable to open FS:\n {}'.format(e))

            return None, None

    @staticmethod
    def open_fs(img, vol, path, part):
        try:
            fs = pytsk3.FS_Info(
                img, offset=part.start * vol.info.block_size)
            root = fs.open_dir(path=path)

            return fs, root
        except IOError:
            _, e, _ = exc_info()
            print('[-] Unable to open FS:\n {}'.format(e))

            return None, None

    @staticmethod
    def nameless_dir(fs_object):
        return not hasattr(fs_object, 'info') \
               or not hasattr(fs_object.info, 'name') or not hasattr(
            fs_object.info.name, 'name') or \
               fs_object.info.name.name.decode('UTF-8') in ['.', '..']

    def single_file(self, partition, path, filename, hashing=False):
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
            for fs_object in root:
                if self.nameless_dir(fs_object):
                    continue

                try:
                    file_name = fs_object.info.name.name.decode('UTF-8')

                    if file_name.lower() == filename.lower():
                        if hashing:
                            return self.hash_file(fs_object)
                        else:
                            return fs_object

                except IOError:
                    pass

        return None

    def files(self, search_str=None):
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

    def recurse_files(self, part, fs, root_dir, dirs, data, parent,
                      search_str=None):
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
                        if '.' in file_name:
                            file_ext = file_name.rsplit('.')[-1].lower()
                        else:
                            file_ext = ''
                except AttributeError:
                    continue

                if search_str is None or search(search_str, file_name,
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
    def hash_file(fs_object):
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
    def convert_time(ts):
        if str(ts) == '0':
            return ''
        return datetime.utcfromtimestamp(ts)
