import unittest
import shutil
import zipfile
import os

from offtopic import CollectionModel
from offtopic import get_collection_model

import logging
logging.basicConfig(level=logging.DEBUG)

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

        shutil.rmtree(working_directory)
