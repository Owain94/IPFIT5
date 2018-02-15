import pyewf
import pytsk3

from os import sep
from re import match
from hashlib import sha256
from sys import setrecursionlimit, exc_info
from pathlib import Path as PathlibPath
from datetime import datetime

from Utils.Logging.Logging import Logging


class Ewf(pytsk3.Img_Info):
    def __init__(self, store):
        self.logger = Logging(self.__class__.__name__).logger
        self.store = store

        setrecursionlimit(100000)

        self.image_handle = None

        self.ext = PathlibPath(store.get_state()).suffix.lower()[1:]
        self.block_size = 0
        self.search_result = None
        self.logger.debug('Extension: ' + self.ext)

        if self.ext == 'e01' or self.ext == 's01' or self.ext == 'ex01' or \
                self.ext == 'l01' or self.ext == 'lx01':
            self.ewf_handle = pyewf.handle()
            self.ewf_handle.open(pyewf.glob(store.get_state()))
            self.logger.debug('EWF handle opened')
            self.logger.info('{} loaded with EWF'.format(
                store.get_state().split(sep)[-1]))
            super(Ewf, self).__init__(url='',
                                      type=pytsk3.TSK_IMG_TYPE_EXTERNAL)

    def close(self):
        self.logger.debug('EWF handle closed')
        self.ewf_handle.close()

    def read(self, offset, size):
        self.ewf_handle.seek(offset)
        return self.ewf_handle.read(size)

    def get_size(self):
        return self.ewf_handle.get_media_size()

    def info(self):
        if self.ext == 'e01' or self.ext == 's01' or self.ext == 'ex01' or \
                self.ext == 'l01' or self.ext == 'lx01':
            volume = pytsk3.Volume_Info(self)
        else:
            self.image_handle = pytsk3.Img_Info(url=self.store.get_state())
            volume = pytsk3.Volume_Info(self.image_handle)

        self.block_size = volume.info.block_size
        return volume

    def hash_file(self, path, filename):
        return self.file(path, filename, True)

    def search_file(self, search):
        self.files(search)
        search_result = self.search_result
        self.search_result = None
        return search_result

    def file(self, path, filename, hash=False):
        vol = self.info()
        if self.ext == 'e01' or self.ext == 's01' or self.ext == 'ex01' or \
                self.ext == 'l01' or self.ext == 'lx01':
            img = self
        else:
            img = self.image_handle
        fs = None
        root = None
        # Open FS and Recurse
        if vol is not None:
            for part in vol:
                if part.len > 2048 and "Unallocated" not in part.desc.decode(
                        'UTF-8') and "Extended" not in part.desc.decode(
                        'UTF-8') and "Primary Table" not in part.desc.decode(
                        'UTF-8'):
                    try:
                        fs = pytsk3.FS_Info(
                            img, offset=part.start * vol.info.block_size)
                    except IOError:
                        _, e, _ = exc_info()
                        # print("[-] Unable to open FS:\n {}".format(e))
                    root = fs.open_dir(path=path)
        else:
            try:
                fs = pytsk3.FS_Info(img)
            except IOError:
                _, e, _ = exc_info()
                # print("[-] Unable to open FS:\n {}".format(e))
            root = fs.open_dir(path=path)

        for fs_object in root:
            if not hasattr(fs_object, "info") \
                    or not hasattr(fs_object.info, "name") or not hasattr(
                    fs_object.info.name, "name") or \
                    fs_object.info.name.name.decode('UTF-8') in [".", ".."]:
                continue
            try:
                if fs_object.info.name.name.decode('UTF-8') == filename:
                    if not hash:
                        return fs_object
                    else:
                        offset = 0
                        size = fs_object.info.meta.size
                        buff_size = 1024 * 1024

                        sha256_sum = sha256()
                        while offset < size:
                            available_to_read = min(buff_size, size - offset)
                            data = fs_object.read_random(
                                offset, available_to_read)
                            if not data:
                                break

                            offset += len(data)
                            sha256_sum.update(data)
                        return sha256_sum.hexdigest()
            except IOError:
                pass

        return None

    def files(self, search=None):
        vol = self.info()
        if self.ext == 'e01' or self.ext == 's01' or self.ext == 'ex01' or \
                self.ext == 'l01' or self.ext == 'lx01':
            img = self
        else:
            img = self.image_handle
        # print("[+] Recursing through files..")
        recursed_data = []
        fs = None
        # Open FS and Recurse
        if vol is not None:
            for part in vol:
                if part.len > 2048 and "Unallocated" not in part.desc.decode(
                        'UTF-8') and "Extended" not in part.desc.decode(
                        'UTF-8') and "Primary Table" not in part.desc.decode(
                        'UTF-8'):
                    try:
                        fs = pytsk3.FS_Info(
                            img, offset=part.start * vol.info.block_size)
                    except IOError:
                        _, e, _ = exc_info()
                        # print("[-] Unable to open FS:\n {}".format(e))
                    root = fs.open_dir(path="/")
                    data = self.recurse_files(part.addr, fs, root, [], [],
                                              [""], search)
                    recursed_data.append(data)

        else:
            try:
                fs = pytsk3.FS_Info(img)
            except IOError:
                _, e, _ = exc_info()
                # print("[-] Unable to open FS:\n {}".format(e))
            root = fs.open_dir(path="/")
            data = self.recurse_files(1, fs, root, [], [], [""], search)
            recursed_data.append(data)

        return recursed_data

    def recurse_files(self, part, fs, root_dir, dirs, data, parent,
                      search=None):
        # print('Recurse')
        dirs.append(root_dir.info.fs_file.meta.addr)
        for fs_object in root_dir:
            # Skip ".", ".." or directory entries without a name.
            if not hasattr(fs_object, "info") \
                    or not hasattr(fs_object.info, "name") or not hasattr(
                fs_object.info.name, "name") or \
                    fs_object.info.name.name.decode('UTF-8') in [".", ".."]:
                continue
            try:
                file_name = fs_object.info.name.name.decode('UTF-8')
                if search or True:
                    search_result = match('autoexec', file_name)
                    print(search_result, file_name)
                    if search_result:
                        self.search_result = fs_object
                        return

                file_path = "{}/{}".format(
                    "/".join(parent),
                    fs_object.info.name.name.decode('UTF-8'))
                try:
                    if fs_object.info.meta.type == \
                            pytsk3.TSK_FS_META_TYPE_DIR:
                        f_type = "DIR"
                        file_ext = ""
                    else:
                        f_type = "FILE"
                        if "." in file_name:
                            file_ext = file_name.rsplit(".")[-1].lower()
                        else:
                            file_ext = ""
                except AttributeError:
                    continue

                size = fs_object.info.meta.size
                create = self.convert_time(fs_object.info.meta.crtime)
                change = self.convert_time(fs_object.info.meta.ctime)
                modify = self.convert_time(fs_object.info.meta.mtime)
                data.append(
                    ["PARTITION {}".format(part), file_name, file_ext, f_type,
                     create, change, modify, size, file_path])

                if f_type == "DIR":
                    parent.append(fs_object.info.name.name.decode('UTF-8'))
                    sub_directory = fs_object.as_directory()
                    inode = fs_object.info.meta.addr

                    # This ensures that we don't recurse into a directory
                    # above the current level and thus avoid circular loops.
                    if inode not in dirs:
                        self.recurse_files(part, fs, sub_directory, dirs,
                                           data, parent, search)
                    parent.pop(-1)

            except IOError:
                pass
        dirs.pop(-1)
        return data

    @staticmethod
    def convert_time(ts):
        if str(ts) == "0":
            return ""
        return datetime.utcfromtimestamp(ts)


class EwfInfoMenu(object):
    def __init__(self):
        self.logger = Logging(self.__class__.__name__).logger

    @staticmethod
    def menu(store):
        ewf = Ewf(store)
        volume = ewf.info()

        menu_items = [
            ('Amount of partitions: {}'.format(volume.info.part_count), ''),
            ('', '')]

        for part in volume:
            menu_items.append(('Partition address: {}'.format(part.addr), ''))
            menu_items.append(('Partition start: {}'.format(part.start), ''))
            menu_items.append(('Partition length (relative): {}'.format(
                part.start + part.len - 1), ''))
            menu_items.append(('Partition length: {}'.format(part.len), ''))
            menu_items.append(('Partition description: {}'.format(
                part.desc.decode('UTF-8')), ''))

            menu_items.append(('', ''))

        return menu_items
