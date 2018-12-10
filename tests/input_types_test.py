import unittest
import shutil
import zipfile
import os

from datetime import datetime

from requests.exceptions import ConnectionError, TooManyRedirects

from otmt import CollectionModel
from otmt import get_collection_model
from otmt import discover_raw_urims

import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

futures_mementoinfo = {
    "https://wayback.archive-it.org/web/19700101000000/http://goodmemento": {
        "headers": {
            "key1": "value1",
            "key2": "value2",
            "memento-datetime": "some date"
        },
        "content": "<html><body>Archive stuff<br />Good Memento</body></html>",
        "errorinfo": None,
        "status": 200,
        "history": [],
        "url": "https://wayback.archive-it.org/web/19700101000000/http://goodmemento"
    },
    "https://wayback.archive-it.org/web/19700101000000/http://connectionerror": {
        "headers": None,
        "content": None,
        "errorinfo": "ConnectionError('connectionerror',)",
        "status": None,
        "history": []
    },
    "https://wayback.archive-it.org/web/19700101000000/http://toomanyredirects": {
        "headers": None,
        "content": None,
        "errorinfo": "TooManyRedirects('toomanyredirects',)",
        "status": None,
        "history": []
    },
    "https://wayback.archive-it.org/web/19700101000000/http://goodmementowithredirectstart": {
        "headers": {
            "key1": "value1",
            "key2": "value2",
            "memento-datetime": "some date"
        },
        "content": "<html><body>Archive stuff<br />Good Memento</body></html>",
        "errorinfo": None,
        "status": 200,
        "history": [],
        "url": "https://wayback.archive-it.org/web/19700101000000/http://goodmementowithredirectend"
    },
    "https://wayback.archive-it.org/web/19700101000000/http://goodmementowithredirectmid": {
        "headers": {
            "key1": "value1",
            "key2": "value2"
        },
        "content": "",
        "errorinfo": None,
        "status": 302,
        "history": []
    },
    "https://wayback.archive-it.org/web/19700101000000/http://goodmementowithredirectend": {
        "headers": {
            "key1": "value1",
            "key2": "value2",
            "memento-datetime": "some date"
        },
        "content": "",
        "errorinfo": None,
        "status": 302,
        "history": []      
    }
}

class MockResponse():

    def __init__(self, uri):
        self.uri = uri
        self.status_code = futures_mementoinfo[self.uri]["status"]
        self.text = futures_mementoinfo[self.uri]["content"]
        self.headers = futures_mementoinfo[self.uri]["headers"]
        self.history = futures_mementoinfo[self.uri]["history"]
        self.url = ""

class MockFuture():

    def __init__(self, uri):
        self.uri = uri

    def done(self):
        return True

    def result(self):

        if self.uri == "https://wayback.archive-it.org/web/19700101000000/http://connectionerror":
            raise ConnectionError("connectionerror")

        if self.uri == "https://wayback.archive-it.org/web/19700101000000/http://toomanyredirects":
            raise TooManyRedirects("toomanyredirects")

        if self.uri == "https://wayback.archive-it.org/web/19700101000000/http://goodmemento":
            mr = MockResponse(self.uri)
            mr.url = self.uri
            return mr

        if self.uri == "https://wayback.archive-it.org/web/19700101000000/http://goodmementowithredirectstart":

            mr = MockResponse(self.uri)

            mr.history = [
                MockResponse("https://wayback.archive-it.org/web/19700101000000/http://goodmementowithredirectstart"),
                MockResponse("https://wayback.archive-it.org/web/19700101000000/http://goodmementowithredirectend")
            ]

            mr.url = "https://wayback.archive-it.org/web/19700101000000/http://goodmementowithredirectend"

            return mr


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

        cm = get_collection_model("dir", [working_directory], working_directory)

        testurim = "testing-storage:memento1"
        testurit = "testing-storage:timemap2"

        self.assertEqual([testurim], cm.getMementoURIList())

        self.assertEqual([testurit], cm.getTimeMapURIList())

        shutil.rmtree(working_directory)

    def test_warc_input(self):

        warcfile="{}/testdata/testwarc.warc.gz".format(
            os.path.dirname(os.path.realpath(__file__))
        )

        test_directory = "/tmp/inputtype_test"

        if not os.path.exists(test_directory):
            os.makedirs(test_directory)

        working_directory = "{}/test_warc_input".format(test_directory)

        cm = get_collection_model("warc", [warcfile], working_directory)

        testurims = [
            "from-warc::20110201020507::http://crowdvoice.org/emergency-law-and-police-brutality-in-egypt/contents/4012/vote/down",
            "from-warc::20110201020505::http://www.enduringamerica.com/home/2010/11/30/egypt-watch-latest-on-the-parliamentary-elections.html",
            "from-warc::20110201020320::http://abcnews.go.com/video/playlistPane?id=2808979&videoID=12787224&tabID=9482931&sectionID=2808950&playlistID=2808979&page=8&pageSize=5"
        ]

        testmemcontent = b"""

<div class="pane">
	<div class="video">
				<a class="pta" href="/Politics/video/kennedy-townsend-calls-tighter-gun-laws-12734504&amp;tab=9482931&amp;section=2808950&amp;playlist=2808979">
<img src="http://a.abcnews.com/images/Politics/ABC_KENNEDY_TOWNSEND_GUNS_110121_wc.jpg" width="100" height="56" style="margin-left:0px;margin-top:0px" border="0" alt="VIDEO: Kennedy Townsend Calls For Tighter Gun Laws" title=""/></a> <div class="ptc"> 
					<h2>Kennedy Townsend Calls For Tighter Gun Laws</h2>
					Kathleen Kennedy Townsend gives remarks to DOJ on the Arizona shooting.
				   </div>
				  </div> 
				
	<div style="clear:both"><!-- empty --></div>
</div>
"""

        mementos_in_collection = cm.getMementoURIList()

        for testurim in testurims:

            self.assertIn(testurim, mementos_in_collection)

        self.assertEqual(testmemcontent, cm.getMementoContent(
            "from-warc::20110201020320::http://abcnews.go.com/video/playlistPane?id=2808979&videoID=12787224&tabID=9482931&sectionID=2808950&playlistID=2808979&page=8&pageSize=5"
        ))

        testtmcontent = {
            "original_uri": "http://crowdvoice.org/emergency-law-and-police-brutality-in-egypt/contents/4012/vote/down",
            "timegate_uri": "from-warc::timegate::http://crowdvoice.org/emergency-law-and-police-brutality-in-egypt/contents/4012/vote/down",
            "timemap_uri": {
                "json_format": "from-warc::timemap::http://crowdvoice.org/emergency-law-and-police-brutality-in-egypt/contents/4012/vote/down"
            },
            "mementos": {
                "list": [
                    {
                        "datetime": datetime(2011, 2, 1, 2, 5, 7),
                        "uri": "from-warc::20110201020507::http://crowdvoice.org/emergency-law-and-police-brutality-in-egypt/contents/4012/vote/down"
                    }
                ],
                "first": {
                    "datetime": datetime(2011, 2, 1, 2, 5, 7),
                    "uri": "from-warc::20110201020507::http://crowdvoice.org/emergency-law-and-police-brutality-in-egypt/contents/4012/vote/down"
                },
                "last": {
                    "datetime": datetime(2011, 2, 1, 2, 5, 7),
                    "uri": "from-warc::20110201020507::http://crowdvoice.org/emergency-law-and-police-brutality-in-egypt/contents/4012/vote/down"
                }
            }
        }

        self.maxDiff = None

        self.assertEqual(
            testtmcontent,
            cm.getTimeMap("from-warc::timemap::http://crowdvoice.org/emergency-law-and-police-brutality-in-egypt/contents/4012/vote/down")
        )

        shutil.rmtree(working_directory)

    def test_discover_raw_urims(self):

        working_directory = "/tmp/test-fetch-mementos"

        # clean up from potential prior failed run
        if os.path.exists(working_directory):
            shutil.rmtree(working_directory)

        mock_futures = {}

        urimlist = [
            "https://wayback.archive-it.org/web/19700101000000/http://goodmemento",
            "https://wayback.archive-it.org/web/19700101000000/http://connectionerror",
            "https://wayback.archive-it.org/web/19700101000000/http://goodmementowithredirectstart",
            "https://wayback.archive-it.org/web/19700101000000/http://toomanyredirects"
        ]

        for urim in urimlist:
            mock_futures[urim] = MockFuture(urim)

        raw_urimdata, errordata = discover_raw_urims(urimlist, futures=mock_futures)

        self.assertEqual( len(raw_urimdata), 2 )

        self.assertEqual(
            raw_urimdata["https://wayback.archive-it.org/web/19700101000000/http://goodmemento"],
            "https://wayback.archive-it.org/web/19700101000000id_/http://goodmemento"
        )

        self.assertEqual(
            raw_urimdata["https://wayback.archive-it.org/web/19700101000000/http://goodmementowithredirectstart"],
            "https://wayback.archive-it.org/web/19700101000000id_/http://goodmementowithredirectend"
        )

        self.assertEqual( len(errordata), 2 )

        self.assertEqual(
            errordata["https://wayback.archive-it.org/web/19700101000000/http://connectionerror"],
            "ConnectionError('connectionerror')"
        )

        self.assertEqual(
            errordata["https://wayback.archive-it.org/web/19700101000000/http://toomanyredirects"],
            "TooManyRedirects('toomanyredirects')"
        )

        
