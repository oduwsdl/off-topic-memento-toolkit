import unittest
import os
import hashlib

from datetime import datetime

from offtopic import collectionmodel

class TestingCollectionModel(unittest.TestCase):

    def test_timemaps(self):

        working_directory = "/tmp/collectionmodel_test/test_timemaps"
       
        cm = collectionmodel.CollectionModel(working_directory=working_directory)

        if not os.path.exists(working_directory):
            self.fail("Collection working directory not created")

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
        testurit2filename_json = "{}.json".format( testurit2filename_digest )
        testurit2filename_orig = "{}.orig".format( testurit2filename_digest )

        cm.addTimeMap(testurit2, testtimemap2, testtimemapheaders )

        self.assertEqual(cm.getTimeMap(testurit2), testtimemap2dict)

        if not os.path.exists("{}/timemaps/{}".format(working_directory, testurit2filename_json)):
            self.fail("TimeMap not saved to {}/timemaps/{}".format(working_directory, testurit2filename_json))

        if not os.path.exists("{}/timemaps/{}".format(working_directory, testurit2filename_orig)):
            self.fail("TimeMap not saved to {}/timemaps/{}".format(working_directory, testurit2filename_orig))

        # os.removedirs(working_directory)