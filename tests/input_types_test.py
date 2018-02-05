import unittest
import shutil
import zipfile
import os

from offtopic import CollectionModel
from offtopic import get_collection_model


class InputTypeTest(unittest.TestCase):

    def test_dir_input(self):

        testdatafile="{}/testdata/test_loaddata.zip".format(
            os.path.dirname(os.path.realpath(__file__))
        )

        test_directory = "/tmp/inputtype_test"

        if not os.path.exists(test_directory):
            os.makedirs(test_directory)

        working_directory = "{}/test_loaddata".format(test_directory)

        zipref = zipfile.ZipFile(testdatafile, 'r')
        zipref.extractall(test_directory)
        zipref.close()

        cm = get_collection_model("dir", None, working_directory)

        testurim = "testing-storage:memento1"
        testurit = "testing-storage:timemap2"

        self.assertEqual([testurim], cm.getMementoURIList())

        self.assertEqual([testurit], cm.getTimeMapURIList())