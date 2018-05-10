from io import BytesIO
from exifread import process_file

from Interfaces.ModuleInterface import ModuleInterface
from Utils.ImageHandler import ImageHandler
from Utils.Logging.Logging import Logging
from Utils.XlsxWriter import XlsxWriter


class Photos(ModuleInterface):
    def __init__(self):
        # instancieer de debug logger
        self.logger = Logging(self.__class__.__name__).logger

    def run(self, *args):
        """
        Run the functions based on the user input

        :param args: args

        :return: None
        """
        files = self.get_files()[0]
        filtered = self.filter_files(files)
        hashed = self.hash(filtered)

        # print("\n".join(map(str,hashed)))
        self.data = hashed
        self.get_exif(hashed)

    def results(self):
        """
        Save the results of all the functions based on the user input

        :return: None
        """

        xlsx_writer = XlsxWriter('photos')
        xlsx_writer.add_worksheet("Photos")
        xlsx_writer.write_headers("Photos", ["Partite", "File", "File EXT",
                                             "File Type", "Create date",
                                             "Modify Date", "Change Date",
                                             "Size in kb",
                                             "File path", "Hash-waarde"])
        for row in self.data:
            # print(row[4])
            row[4] = str(row[4])
        xlsx_writer.write_items("Photos", self.data)

        """
        xlsx_writer.add_worksheet('Photos')
        xlsx_writer.write_headers(Photos,["Partitie","Naam bestand"])
        xlsx_writer.write_items(Photos, self.hashed)
        """
        xlsx_writer.close()

    @staticmethod
    def get_files():
        """
        Create a list of all files

        :return: None
        """
        return ImageHandler().files()

    @staticmethod
    def filter_files(files):
        lst = []

        for file in files:
            if file[2] == 'jpeg' and '._' not in file[1] or \
                    file[2] == 'jpg' and '._' not in file[1] or \
                    file[2] == 'png' and '._' not in file[1]:
                lst.append(file)

        return lst

    @staticmethod
    def hash(files):
        """
        Hash a single file

        :param files:List of all filtered files

        :return: Hash of the file
        """
        lst = []
        for file in files:
            sha_sum = ImageHandler().single_file(int(file[0][-1]),
                                                 ImageHandler.rreplace(
                                                     file[8],
                                                     file[1],
                                                     ''),
                                                 file[1],
                                                 True)

            file.append(sha_sum)
            lst.append(file)

        return lst

    @staticmethod
    def get_bytes(file):
        """
        Get the bytes of a single file

        :param file: Single file information

        :return: Bytes of a file
        """
        bts = ImageHandler().single_file(int(file[0][-1]),
                                         ImageHandler.rreplace(
                                             file[8],
                                             file[1],
                                             ''),
                                         file[1])

        return bts

    def get_exif(self, files):
        for file in files:
            fake_file = BytesIO(self.get_bytes(file))
            tags = process_file(fake_file)

            for _ in tags.keys():
                # if tag not in ('JPEGThumbnail', 'TIFFThumbnail', 'Filename',
                #                'EXIF MakerNote'):
                #     print("Key: %s, value %s" % (tag, tags[tag]))
                # verdelen van gegevens
                try:
                    for tag, value in files.items():
                        decoded = file.get(tag, tags)
                        if decoded == "Make":
                            return value
                except AttributeError:
                    continue
