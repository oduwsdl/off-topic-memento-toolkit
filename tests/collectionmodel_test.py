import unittest
import os
import hashlib
import shutil
import zipfile

from datetime import datetime

from offtopic import collectionmodel

class TestingCollectionModel(unittest.TestCase):

    def check_fileobjects_exist(self, files_to_check):

        for filename in files_to_check:

            if not os.path.exists(filename):

                self.fail("Expected file not created: {}".format(filename))

    def test_directory_creation_happy_path(self):

        working_directory="/tmp/collectionmodel_test/test_directory_creation"

        collectionmodel.CollectionModel(working_directory=working_directory)

        files_to_check = [
            working_directory,
            "{}/timemaps".format(working_directory),
            "{}/mementos".format(working_directory),
            "{}/timemaps/metadata.csv".format(working_directory),
            "{}/mementos/metadata.csv".format(working_directory)
        ]

        self.check_fileobjects_exist(files_to_check)

        shutil.rmtree(working_directory)

    def test_timemaps_happy_path(self):

        working_directory = "/tmp/collectionmodel_test/test_timemaps"
        timemap_directory = "{}/timemaps/".format(working_directory)
       
        cm = collectionmodel.CollectionModel(working_directory=working_directory)

        self.assertIsNotNone(cm, "CollectionModel failed to instantiate")

        testtimemapheaders = {
            "header1": "value1",
            "header2": "value2"
        }

        testtimemap2 = """<http://a.example.org>;rel="original",
        <http://arxiv.example.net/timemap/http://a.example.org>
        ; rel="self";type="application/link-format"
        ; from="Tue, 20 Jun 2000 18:02:59 GMT"
        ; until="Wed, 09 Apr 2008 20:30:51 GMT",
        <http://arxiv.example.net/timegate/http://a.example.org>
        ; rel="timegate",
        <http://arxiv.example.net/web/20000620180259/http://a.example.org>
        ; rel="first memento";datetime="Tue, 20 Jun 2000 18:02:59 GMT"
        ; license="http://creativecommons.org/publicdomain/zero/1.0/",
        <http://arxiv.example.net/web/20091027204954/http://a.example.org>
        ; rel="last memento";datetime="Tue, 27 Oct 2009 20:49:54 GMT"
        ; license="http://creativecommons.org/publicdomain/zero/1.0/",
        <http://arxiv.example.net/web/20000621011731/http://a.example.org>
        ; rel="memento";datetime="Wed, 21 Jun 2000 01:17:31 GMT"
        ; license="http://creativecommons.org/publicdomain/zero/1.0/",
        <http://arxiv.example.net/web/20000621044156/http://a.example.org>
        ; rel="memento";datetime="Wed, 21 Jun 2000 04:41:56 GMT"
        ; license="http://creativecommons.org/publicdomain/zero/1.0/",
        """

        testtimemap2dict = {
            "original_uri": "http://a.example.org",
            "timegate_uri": "http://arxiv.example.net/timegate/http://a.example.org",
            "timemap_uri": {
                "link_format": "http://arxiv.example.net/timemap/http://a.example.org"
            },
            "mementos": {
                "first": {
                    "datetime": datetime(2000, 6, 20, 18, 2, 59),
                    "uri": "http://arxiv.example.net/web/20000620180259/http://a.example.org"
                },
                "last": {
                    "datetime": datetime(2009, 10, 27, 20, 49, 54),
                    "uri": "http://arxiv.example.net/web/20091027204954/http://a.example.org"
                },
                "list": [
                    {
                        "datetime": datetime(2000, 6, 20, 18, 2, 59),
                        "uri": "http://arxiv.example.net/web/20000620180259/http://a.example.org"
                    },
                    {
                        "datetime": datetime(2009, 10, 27, 20, 49, 54),
                        "uri": "http://arxiv.example.net/web/20091027204954/http://a.example.org"                        
                    },
                    {
                        "datetime": datetime(2000, 6, 21, 1, 17, 31),
                        "uri": "http://arxiv.example.net/web/20000621011731/http://a.example.org"
                    },
                    {
                        "datetime": datetime(2000, 6, 21, 4, 41, 56),
                        "uri": "http://arxiv.example.net/web/20000621044156/http://a.example.org"
                    }
                ]
            }
        }

        testurit2 = "testing-storage:timemap2"
        testurit2filename_digest = hashlib.sha3_256(bytes(testurit2, "utf8")).hexdigest()

        files_to_check = [
            "{}/{}_headers.json".format( timemap_directory, testurit2filename_digest ),
            "{}/{}.json".format( timemap_directory, testurit2filename_digest ),
            "{}/{}.orig".format( timemap_directory, testurit2filename_digest )
        ]

        cm.addTimeMap(testurit2, testtimemap2, testtimemapheaders )

        self.assertEqual(cm.getTimeMap(testurit2), testtimemap2dict)

        self.check_fileobjects_exist(files_to_check)

        shutil.rmtree(working_directory)

    def test_mementos_happy_path(self):

        working_directory="/tmp/collectionmodel_test/test_mementos"
        memento_directory = "{}/mementos/".format(working_directory)
       
        cm = collectionmodel.CollectionModel(working_directory=working_directory)

        self.assertIsNotNone(cm, "CollectionModel failed to instantiate")

        testmemheaders = {
            "header1": "value1",
            "header2": "value2",
            "memento-datetime": "value3"
        }

        testmemcontent = "<html><body>mementotext</body></html>"

        testurim1 = "testing-storage:memento1"

        cm.addMemento(testurim1, testmemcontent, testmemheaders )

        self.assertEqual(cm.getMementoContent(testurim1), testmemcontent)

        filename_digest = hashlib.sha3_256(bytes(testurim1, "utf8")).hexdigest()

        files_to_check = [
            "{}/{}_headers.json".format( memento_directory, filename_digest ),
            "{}/{}.orig".format( memento_directory, filename_digest )
        ]

        self.check_fileobjects_exist(files_to_check)

        shutil.rmtree(working_directory)

    def test_missing_memento(self):

        working_directory="/tmp/collectionmodel_test/test_missing_memento"
       
        cm = collectionmodel.CollectionModel(working_directory=working_directory)

        self.assertRaises( collectionmodel.CollectionModelException,
            cm.getMementoContent, "testing-storage:bad-memento" )

        shutil.rmtree(working_directory)

    #def test_missing_timemap
    def test_data_load(self):

        # working_directory="{}/testdata/test_loaddata".format(
        #     os.path.dirname(os.path.realpath(__file__))
        # )

        testdatafile="{}/testdata/test_loaddata.zip".format(
            os.path.dirname(os.path.realpath(__file__))
        )

        test_directory = "/tmp/collectionmodel_test"

        if not os.path.exists(test_directory):
            os.makedirs(test_directory)

        working_directory = "{}/test_loaddata".format(test_directory)

        zipref = zipfile.ZipFile(testdatafile, 'r')
        zipref.extractall(test_directory)
        zipref.close()

        testurim = "testing-storage:memento1"

        testmemheaders = {
            "header1": "value1",
            "header2": "value2",
            "memento-datetime": "value3"
        }

        testmemcontent = "<html><body>mementotext</body></html>"

        testtimemapheaders = {
            "header1": "value1",
            "header2": "value2"
        }

        testurit = "testing-storage:timemap2"

        testtimemapdict = {
            "original_uri": "http://a.example.org",
            "timegate_uri": "http://arxiv.example.net/timegate/http://a.example.org",
            "timemap_uri": {
                "link_format": "http://arxiv.example.net/timemap/http://a.example.org"
            },
            "mementos": {
                "first": {
                    "datetime": datetime(2000, 6, 20, 18, 2, 59),
                    "uri": "http://arxiv.example.net/web/20000620180259/http://a.example.org"
                },
                "last": {
                    "datetime": datetime(2009, 10, 27, 20, 49, 54),
                    "uri": "http://arxiv.example.net/web/20091027204954/http://a.example.org"
                },
                "list": [
                    {
                        "datetime": datetime(2000, 6, 20, 18, 2, 59),
                        "uri": "http://arxiv.example.net/web/20000620180259/http://a.example.org"
                    },
                    {
                        "datetime": datetime(2009, 10, 27, 20, 49, 54),
                        "uri": "http://arxiv.example.net/web/20091027204954/http://a.example.org"                        
                    },
                    {
                        "datetime": datetime(2000, 6, 21, 1, 17, 31),
                        "uri": "http://arxiv.example.net/web/20000621011731/http://a.example.org"
                    },
                    {
                        "datetime": datetime(2000, 6, 21, 4, 41, 56),
                        "uri": "http://arxiv.example.net/web/20000621044156/http://a.example.org"
                    }
                ]
            }
        }

        cm = collectionmodel.CollectionModel(working_directory=working_directory)

        self.assertEqual(testmemcontent, cm.getMementoContent(testurim))

        self.maxDiff = None

        self.assertEqual(testtimemapdict, cm.getTimeMap(testurit))

        shutil.rmtree(test_directory)
