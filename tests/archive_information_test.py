import unittest

from offtopic import generate_raw_urim

class TestingArchiveInformation(unittest.TestCase):

    def generate_raw_urim_archiveit_happy_path(self):

        urim = "http://wayback.archive-it.org/1068/20110317183254/http://www.amnistia.org.mx/"

        raw_urim = "http://wayback.archive-it.org/1068/20110317183254id_/http://www.amnistia.org.mx/"

        self.assertEquals(
            raw_urim, generate_raw_urim(urim)
        )

    def generate_raw_urim_archiveit_raw_already(self):

        raw_urim = "http://wayback.archive-it.org/1068/20110317183254id_/http://www.amnistia.org.mx/"

        self.assertEquals(
            raw_urim, generate_raw_urim(raw_urim)
        )

    def generate_raw_urim_archiveorg_happy_path(self):

        urim = "https://web.archive.org/web/20070207050545/http://www.cnn.com:80/"

        raw_urim = "https://web.archive.org/web/20070207050545id_/http://www.cnn.com:80/"

        self.assertEquals(
            raw_urim, generate_raw_urim(urim)
        )
    
    def generate_raw_urim_archiveorg_raw_already(self):

        raw_urim = "https://web.archive.org/web/20070207050545id_/http://www.cnn.com:80/"

        self.assertEquals(
            raw_urim, generate_raw_urim(raw_urim)
        )