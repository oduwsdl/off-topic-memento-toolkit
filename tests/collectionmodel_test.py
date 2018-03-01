import unittest
import sys
import os
import hashlib
import shutil
import zipfile

import pprint

pp = pprint.PrettyPrinter(indent=4)

from datetime import datetime

import lxml.etree

from otmt import collectionmodel

# Disabled this pylint rule because of too many false positives
# Ref: http://pylint-messages.wikidot.com/messages:e1101
# pylint: disable=no-member

import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

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
        """
            The following should not happen:

            TypeError: write() argument must be str, not bytes

            so our input is bytes and our output is bytes to conform to the 
            libraries that will use CollectionModel.
        """

        working_directory="/tmp/collectionmodel_test/test_mementos"
        memento_directory = "{}/mementos/".format(working_directory)
       
        cm = collectionmodel.CollectionModel(working_directory=working_directory)

        self.assertIsNotNone(cm, "CollectionModel failed to instantiate")

        testmemheaders = {
            "header1": "value1",
            "header2": "value2",
            "memento-datetime": "value3"
        }

        testmemcontent = b"<html><body>mementotext</body></html>"

        testurim1 = "testing-storage:memento1"

        cm.addMemento(testurim1, testmemcontent, testmemheaders )

        self.assertEqual(cm.getMementoContent(testurim1), testmemcontent)

        self.assertEqual(cm.getMementoContentWithoutBoilerplate(testurim1), b"mementotext\n")

        filename_digest = hashlib.sha3_256(bytes(testurim1, "utf8")).hexdigest()

        files_to_check = [
            "{}/{}_headers.json".format( memento_directory, filename_digest ),
            "{}/{}.orig".format( memento_directory, filename_digest )
        ]

        self.check_fileobjects_exist(files_to_check)

        shutil.rmtree(working_directory)

    def test_memento_error_path(self):

        working_directory="/tmp/collectionmodel_test/test_memento_errors"
        memento_error_directory = "{}/memento_errors".format(working_directory)

        uri = "testing-storage:bad-memento1"

        filename_digest = hashlib.sha3_256(bytes(uri, "utf8")).hexdigest()

        cm = collectionmodel.CollectionModel(working_directory=working_directory)

        headers = {
            "key1": "value1",
            "key2": "value2"
        }

        content = b"<html><body>404 Not Found</body></html>"

        errorinformation = b"ERROR MESSAGE"

        cm.addMementoError(uri, content, headers, errorinformation)

        files_to_check = [
            "{}/{}_error_info.txt".format( memento_error_directory, filename_digest ),
            "{}/{}_headers.json".format( memento_error_directory, filename_digest ),
            "{}/{}.orig".format( memento_error_directory, filename_digest )
        ]

        self.assertRaises( collectionmodel.CollectionModelMementoErrorException,
            cm.getMementoContent, uri )

        self.assertRaises( collectionmodel.CollectionModelMementoErrorException, 
            cm.getMementoHeaders, uri )

        self.assertEqual( cm.getMementoErrorInformation(uri), errorinformation )

        # logger.debug("hi there...")
        # logger.debug(cm.getMementoErrorInformation(uri))

        uri = "testing-storage:good-memento1"
        content = b"<html><body>It works!</body></html>"

        cm.addMemento(uri, content, headers)

        self.assertEquals( cm.getMementoErrorInformation(uri), None )

        self.check_fileobjects_exist(files_to_check)

        shutil.rmtree(working_directory)

    def test_string_not_bytes_memento(self):


        working_directory="/tmp/collectionmodel_test/test_mementos"
        memento_directory = "{}/mementos/".format(working_directory)
       
        cm = collectionmodel.CollectionModel(working_directory=working_directory)

        self.assertIsNotNone(cm, "CollectionModel failed to instantiate")

        testmemheaders = {
            "header1": "value1",
            "header2": "value2",
            "memento-datetime": "value3"
        }

        testmemcontent = b"<html><body>mementotext</body></html>"

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

        self.assertRaises( collectionmodel.CollectionModelNoSuchMementoException,
            cm.getMementoContent, "testing-storage:bad-memento" )

        shutil.rmtree(working_directory)

    def test_single_memento(self):

        working_directory="/tmp/collectionmodel_test/test_single_memento"

        if os.path.exists(working_directory):
            shutil.rmtree(working_directory)

        cm = collectionmodel.CollectionModel(working_directory=working_directory)

        headers = {
            "key1": "value1",
            "key2": "value2"
        }

        timemap_content ="""<original1>; rel="original",
<timemap1>; rel="self"; type="application/link-format"; from="Tue, 21 Mar 2016 15:45:06 GMT"; until="Tue, 21 Mar 2018 15:45:12 GMT",
<timegate1>; rel="timegate",
<memento11>; rel="first last memento"; datetime="Tue, 21 Jan 2016 15:45:06 GMT"
"""

        cm.addTimeMap("timemap1", timemap_content, headers)

        pp.pprint(cm.getTimeMapURIList())

        self.assertEqual( len(cm.getTimeMapURIList()), 1)

        self.assertTrue( "timemap1" in cm.getTimeMapURIList() )

        timemap = cm.getTimeMap("timemap1")

        self.assertEqual( "memento11", timemap["mementos"]["first"]["uri"] )
        self.assertEqual( "memento11", timemap["mementos"]["last"]["uri"] )

        self.assertEqual( len(timemap["mementos"]["list"]), 1)

        self.assertEqual( timemap["mementos"]["list"][0]["uri"], "memento11" )

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

        badurim = "testing-storage:bad-memento1"

        # badurim_headers = {
        #     "key1": "value1",
        #     "key2": "value2"
        # }

        # badurim_content = b"<html><body>404 Not Found</body></html>"

        errorinformation = b"ERROR MESSAGE"

        testurim = "testing-storage:memento1"

        testmemheaders = {
            "header1": "value1",
            "header2": "value2",
            "memento-datetime": "value3"
        }

        testmemcontent = b"<html><body>mementotext</body></html>"

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

        self.assertEqual(testmemheaders, cm.getMementoHeaders(testurim))

        self.assertEqual([testurim], cm.getMementoURIList())

        self.maxDiff = None

        self.assertEqual(testtimemapdict, cm.getTimeMap(testurit))

        self.assertEqual(testtimemapheaders, cm.getTimeMapHeaders(testurit))

        self.assertEqual([testurit], cm.getTimeMapURIList())

        self.assertEqual( cm.getMementoErrorInformation(badurim), errorinformation )

        shutil.rmtree(test_directory)

    def test_problematic_timemap(self):

        timemapcontent="""<http://digitalinnovations.ucla.edu/>; rel="original",
<http://wayback.archive-it.org/7877/timemap/link/http://digitalinnovations.ucla.edu/>; rel="self"; type="application/link-format"; from="Tue, 21 Mar 2017 15:45:06 GMT"; until="Tue, 21 Mar 2017 15:45:12 GMT",
<http://wayback.archive-it.org/7877/http://digitalinnovations.ucla.edu/>; rel="timegate",
<http://wayback.archive-it.org/7877/20170321154506/http://digitalinnovations.ucla.edu/>; rel="first memento"; datetime="Tue, 21 Mar 2017 15:45:06 GMT",
<http://wayback.archive-it.org/7877/20170321154512/http://digitalinnovations.ucla.edu/>; rel="last memento"; datetime="Tue, 21 Mar 2017 15:45:12 GMT"
"""

        expectedtimemapdict = {
            "original_uri": "http://digitalinnovations.ucla.edu/",
            "timegate_uri": "http://wayback.archive-it.org/7877/http://digitalinnovations.ucla.edu/",
            "timemap_uri": {
                "link_format": "http://wayback.archive-it.org/7877/timemap/link/http://digitalinnovations.ucla.edu/"
            },
            "mementos": {
                "first": {
                    "datetime": datetime(2017, 3, 21, 15, 45, 6),
                    "uri": "http://wayback.archive-it.org/7877/20170321154506/http://digitalinnovations.ucla.edu/"
                },
                "last": {
                    "datetime": datetime(2017, 3, 21, 15, 45, 12),
                    "uri": "http://wayback.archive-it.org/7877/20170321154512/http://digitalinnovations.ucla.edu/"
                },
                "list": [
                    {
                        "datetime": datetime(2017, 3, 21, 15, 45, 6),
                        "uri": "http://wayback.archive-it.org/7877/20170321154506/http://digitalinnovations.ucla.edu/"
                    },
                    {
                        "datetime": datetime(2017, 3, 21, 15, 45, 12),
                        "uri": "http://wayback.archive-it.org/7877/20170321154512/http://digitalinnovations.ucla.edu/"
                    }
                ]
            }
        }

        test_directory = "/tmp/collectionmodel_test"

        if not os.path.exists(test_directory):
            os.makedirs(test_directory)

        working_directory = "{}/test_problematic_timemap".format(test_directory)

        cm = collectionmodel.CollectionModel(working_directory=working_directory)

        urit = "testing1"

        testtimemapheaders = {
            "header1": "value1",
            "header2": "value2"
        }

        cm.addTimeMap(urit, timemapcontent, testtimemapheaders)

        self.assertEqual(
            expectedtimemapdict,
            cm.getTimeMap(urit)
        )

        shutil.rmtree(test_directory)

    def test_boilerplate_problem(self):

        working_directory = "/tmp/collectionmodel_test/test_boilerplate_problem"
       
        cm = collectionmodel.CollectionModel(working_directory=working_directory)

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
        
        testheaders = {
            "header1": "value1",
            "header2": "value2"
        }

        testurit2 = "testing-storage:timemap2"

        cm.addTimeMap(testurit2, testtimemap2, testheaders )

        testcontent = b"<html><body>hi</body></html>"

        cm.addMemento("http://arxiv.example.net/web/20000620180259/http://a.example.org",
            testcontent, testheaders)

        cm.addMemento("http://arxiv.example.net/web/20091027204954/http://a.example.org",
            testcontent, testheaders)

        cm.addMemento("http://arxiv.example.net/web/20000621011731/http://a.example.org",
            testcontent, testheaders)

        cm.addMemento("http://arxiv.example.net/web/20000621044156/http://a.example.org",
            b"", testheaders)

        self.assertEqual(
            cm.getMementoContentWithoutBoilerplate(
                "http://arxiv.example.net/web/20000620180259/http://a.example.org"),
           b"hi\n"
        )

        with self.assertRaises(collectionmodel.CollectionModelBoilerPlateRemovalFailureException):
            data = cm.getMementoContentWithoutBoilerplate(
                "http://arxiv.example.net/web/20000621044156/http://a.example.org")
            data # here to shut up pylint

        shutil.rmtree(working_directory)