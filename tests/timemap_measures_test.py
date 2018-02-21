import os
import unittest
import shutil
import pprint

pp = pprint.PrettyPrinter(indent=4)

from offtopic import collectionmodel, compute_bytecount_across_TimeMap, \
    compute_wordcount_across_TimeMap, compute_jaccard_across_TimeMap, \
    compute_cosine_across_TimeMap, compute_sorensen_across_TimeMap, \
    compute_levenshtein_across_TimeMap, compute_nlevenshtein_across_TimeMap

import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

same_scores = {
    # "cosine": 1,
    "bytecount": 0,
    "wordcount": 0,
    # "tfintersection": 0,
    "jaccard": 0,
    "sorensen": 0,
    "levenshtein": 0,
    "nlevenshtein": 0
}

class TestingTimeMapMeasures(unittest.TestCase):

    def test_all_mementos_same(self):

        working_directory = "/tmp/test_all_mementos_same"

        if os.path.exists(working_directory):
            shutil.rmtree(working_directory)

        cm = collectionmodel.CollectionModel(working_directory=working_directory)

        headers = {
            "key1": "value1",
            "key2": "value2"
        }

        contents = []

        contents.append(b"<html><body>Content1 is wonderful</body></html>")
        contents.append(b"<html><body>Content2 is great</body></html>")

        timemap1_content ="""<original1>; rel="original",
<timemap1>; rel="self"; type="application/link-format"; from="Tue, 21 Mar 2016 15:45:06 GMT"; until="Tue, 21 Mar 2018 15:45:12 GMT",
<timegate1>; rel="timegate",
<memento11>; rel="first memento"; datetime="Tue, 21 Jan 2016 15:45:06 GMT",
<memento12>; rel="memento"; datetime="Tue, 21 Jan 2017 15:45:06 GMT",
<memento13>; rel="last memento"; datetime="Tue, 21 Jan 2018 15:45:12 GMT"
"""

        timemap2_content ="""<original1>; rel="original",
<timemap2>; rel="self"; type="application/link-format"; from="Tue, 21 Mar 2016 15:45:06 GMT"; until="Tue, 21 Mar 2018 15:45:12 GMT",
<timegate1>; rel="timegate",
<memento21>; rel="first memento"; datetime="Tue, 21 Mar 2016 15:45:06 GMT",
<memento22>; rel="memento"; datetime="Tue, 21 Mar 2017 15:45:06 GMT",
<memento23>; rel="last memento"; datetime="Tue, 21 Mar 2018 15:45:12 GMT"
"""

        cm.addTimeMap("timemap1", timemap1_content, headers)
        cm.addTimeMap("timemap2", timemap2_content, headers)

        urits = cm.getTimeMapURIList()

        for i in range(0, 2):

            timemap = cm.getTimeMap(urits[i])

            for memento in timemap["mementos"]["list"]:
            
                urim = memento["uri"]

                cm.addMemento(urim, contents[i], headers)

        scores = compute_bytecount_across_TimeMap(
            cm, scores=None, tokenize=False, stemming=False
        )

        scores = compute_wordcount_across_TimeMap(
            cm, scores=scores, stemming=True
        )

        scores = compute_jaccard_across_TimeMap(
            cm, scores=scores, tokenize=True, stemming=True
        )

        # scores = compute_cosine_across_TimeMap(
        #     cm, scores=scores, stemming=True
        # )

        scores = compute_sorensen_across_TimeMap(
            cm, scores=scores, tokenize=False, stemming=False
        )

        scores = compute_levenshtein_across_TimeMap(
            cm, scores=scores, tokenize=False, stemming=False
        )

        scores = compute_nlevenshtein_across_TimeMap(
            cm, scores=scores, tokenize=False, stemming=False
        )

        pp.pprint(scores)

        self.assertTrue( "timemap1" in scores["timemaps"] )
        self.assertTrue( "timemap2" in scores["timemaps"] )

        self.assertTrue( "memento11" in scores["timemaps"]["timemap1"] )
        self.assertTrue( "memento12" in scores["timemaps"]["timemap1"] )
        self.assertTrue( "memento13" in scores["timemaps"]["timemap1"] )

        self.assertTrue( "memento21" in scores["timemaps"]["timemap2"] )
        self.assertTrue( "memento22" in scores["timemaps"]["timemap2"] )
        self.assertTrue( "memento23" in scores["timemaps"]["timemap2"] )

        for urit in scores["timemaps"]:

            for urim in scores["timemaps"][urit]:

                self.assertTrue( "bytecount" in scores["timemaps"][urit][urim] )
                self.assertTrue( "wordcount" in scores["timemaps"][urit][urim] )
                self.assertTrue( "jaccard" in scores["timemaps"][urit][urim] )
                self.assertTrue( "sorensen" in scores["timemaps"][urit][urim] )
                self.assertTrue( "levenshtein" in scores["timemaps"][urit][urim] )
                self.assertTrue( "nlevenshtein" in scores["timemaps"][urit][urim] )

        for measure in same_scores:

            for urit in scores["timemaps"]:

                for urim in scores["timemaps"][urit]:

                    self.assertEqual(
                        scores["timemaps"][urit][urim][measure]["comparison score"],
                        same_scores[measure],
                        "measure {} does not compute the correct score "
                        "for document sameness"
                    )

        shutil.rmtree(working_directory)

    def test_one_memento(self):

        working_directory = "/tmp/test_all_mementos_same"

        if os.path.exists(working_directory):
            shutil.rmtree(working_directory)

        cm = collectionmodel.CollectionModel(working_directory=working_directory)

        headers = {
            "key1": "value1",
            "key2": "value2"
        }

        contents= b"<html><body>Content1 is wonderful</body></html>"

        timemap_content ="""<original1>; rel="original",
<timemap1>; rel="self"; type="application/link-format"; from="Tue, 21 Mar 2016 15:45:06 GMT"; until="Tue, 21 Mar 2018 15:45:12 GMT",
<timegate1>; rel="timegate",
<memento11>; rel="first last memento"; datetime="Tue, 21 Jan 2016 15:45:06 GMT"
"""

        cm.addTimeMap("timemap1", timemap_content, headers)

        urits = cm.getTimeMapURIList()

        timemap = cm.getTimeMap(urits[0])

        for memento in timemap["mementos"]["list"]:
        
            urim = memento["uri"]

            cm.addMemento(urim, contents, headers)

        scores = compute_bytecount_across_TimeMap(
            cm, scores=None, tokenize=False, stemming=False
        )

        scores = compute_wordcount_across_TimeMap(
            cm, scores=scores, stemming=True
        )

        scores = compute_jaccard_across_TimeMap(
            cm, scores=scores, tokenize=True, stemming=True
        )

        # scores = compute_cosine_across_TimeMap(
        #     cm, scores=scores, stemming=True
        # )

        scores = compute_sorensen_across_TimeMap(
            cm, scores=scores, tokenize=False, stemming=False
        )

        scores = compute_levenshtein_across_TimeMap(
            cm, scores=scores, tokenize=False, stemming=False
        )

        scores = compute_nlevenshtein_across_TimeMap(
            cm, scores=scores, tokenize=False, stemming=False
        )

        pp.pprint(scores)

        self.assertTrue( "timemap1" in scores["timemaps"] )

        self.assertTrue( "memento11" in scores["timemaps"]["timemap1"] )

        for urim in scores["timemaps"]["timemap1"]:

            self.assertTrue( "bytecount" in scores["timemaps"]["timemap1"][urim] )
            self.assertTrue( "wordcount" in scores["timemaps"]["timemap1"][urim] )
            self.assertTrue( "jaccard" in scores["timemaps"]["timemap1"][urim] )
            self.assertTrue( "sorensen" in scores["timemaps"]["timemap1"][urim] )
            self.assertTrue( "levenshtein" in scores["timemaps"]["timemap1"][urim] )
            self.assertTrue( "nlevenshtein" in scores["timemaps"]["timemap1"][urim] )

        for measure in same_scores:

            for urit in scores["timemaps"]:

                for urim in scores["timemaps"][urit]:

                    self.assertEqual(
                        scores["timemaps"][urit][urim][measure]["comparison score"],
                        same_scores[measure],
                        "measure {} does not compute the correct score "
                        "for document sameness"
                    )

        shutil.rmtree(working_directory)

    def test_all_mementos_different(self):
        pass