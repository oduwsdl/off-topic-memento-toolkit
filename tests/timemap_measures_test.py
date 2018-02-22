import os
import string
import random
import unittest
import shutil
import pprint

pp = pprint.PrettyPrinter(indent=4)

from offtopic import collectionmodel, compute_bytecount_across_TimeMap, \
    compute_wordcount_across_TimeMap, compute_jaccard_across_TimeMap, \
    compute_cosine_across_TimeMap, compute_sorensen_across_TimeMap, \
    compute_levenshtein_across_TimeMap, compute_nlevenshtein_across_TimeMap, \
    compute_tfintersection_across_TimeMap

import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

same_scores = {
    "cosine": 1.0,
    "bytecount": 0,
    "wordcount": 0,
    "tfintersection": 0,
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
            cm, scores=scores, tokenize=True, stemming=True
        )

        scores = compute_jaccard_across_TimeMap(
            cm, scores=scores, tokenize=True, stemming=True
        )

        scores = compute_cosine_across_TimeMap(
            cm, scores=scores, tokenize=True, stemming=True
        )

        scores = compute_sorensen_across_TimeMap(
            cm, scores=scores, tokenize=True, stemming=True
        )

        scores = compute_levenshtein_across_TimeMap(
            cm, scores=scores, tokenize=True, stemming=True
        )

        scores = compute_nlevenshtein_across_TimeMap(
            cm, scores=scores, tokenize=True, stemming=True
        )

        scores = compute_tfintersection_across_TimeMap(
            cm, scores=scores, tokenize=True, stemming=True
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

                self.assertTrue( "bytecount" in scores["timemaps"][urit][urim]["timemap measures"] )
                self.assertTrue( "wordcount" in scores["timemaps"][urit][urim]["timemap measures"] )
                self.assertTrue( "jaccard" in scores["timemaps"][urit][urim]["timemap measures"] )
                self.assertTrue( "sorensen" in scores["timemaps"][urit][urim]["timemap measures"] )
                self.assertTrue( "levenshtein" in scores["timemaps"][urit][urim]["timemap measures"] )
                self.assertTrue( "nlevenshtein" in scores["timemaps"][urit][urim]["timemap measures"] )
                self.assertTrue( "tfintersection" in scores["timemaps"][urit][urim]["timemap measures"] )
                self.assertTrue( "cosine" in scores["timemaps"][urit][urim]["timemap measures"] )

        for measure in same_scores:

            for urit in scores["timemaps"]:

                for urim in scores["timemaps"][urit]:

                    self.assertAlmostEqual(
                        scores["timemaps"][urit][urim]["timemap measures"][measure]["comparison score"],
                        same_scores[measure],
                        msg="measure {} does not compute the correct score "
                        "for document sameness with URI-M {}".format(measure, urim)
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
            cm, scores=scores, tokenize=True, stemming=True
        )

        scores = compute_jaccard_across_TimeMap(
            cm, scores=scores, tokenize=True, stemming=True
        )

        scores = compute_cosine_across_TimeMap(
            cm, scores=scores, stemming=True
        )

        scores = compute_sorensen_across_TimeMap(
            cm, scores=scores, tokenize=True, stemming=True
        )

        scores = compute_levenshtein_across_TimeMap(
            cm, scores=scores, tokenize=True, stemming=True
        )

        scores = compute_nlevenshtein_across_TimeMap(
            cm, scores=scores, tokenize=True, stemming=True
        )

        scores = compute_tfintersection_across_TimeMap(
            cm, scores=scores, tokenize=True, stemming=True
        )

        pp.pprint(scores)

        self.assertTrue( "timemap1" in scores["timemaps"] )

        self.assertTrue( "memento11" in scores["timemaps"]["timemap1"] )

        urit = "timemap1"

        for urim in scores["timemaps"]["timemap1"]:

            self.assertTrue( "bytecount" in scores["timemaps"][urit][urim]["timemap measures"] )
            self.assertTrue( "wordcount" in scores["timemaps"][urit][urim]["timemap measures"] )
            self.assertTrue( "jaccard" in scores["timemaps"][urit][urim]["timemap measures"] )
            self.assertTrue( "sorensen" in scores["timemaps"][urit][urim]["timemap measures"] )
            self.assertTrue( "levenshtein" in scores["timemaps"][urit][urim]["timemap measures"] )
            self.assertTrue( "nlevenshtein" in scores["timemaps"][urit][urim]["timemap measures"] )
            self.assertTrue( "tfintersection" in scores["timemaps"][urit][urim]["timemap measures"] )
            self.assertTrue( "cosine" in scores["timemaps"][urit][urim]["timemap measures"] )

        for measure in same_scores:

            for urit in scores["timemaps"]:

                for urim in scores["timemaps"][urit]:

                    self.assertAlmostEqual(
                        scores["timemaps"][urit][urim]["timemap measures"][measure]["comparison score"],
                        same_scores[measure],
                        msg="measure {} does not compute the correct score "
                        "for document sameness for URI-M {}".format(measure, urim)
                    )

        shutil.rmtree(working_directory)

    def test_all_mementos_different(self):

        working_directory = "/tmp/test_all_mementos_different"

        if os.path.exists(working_directory):
            shutil.rmtree(working_directory)

        cm = collectionmodel.CollectionModel(working_directory=working_directory)

        headers = {
            "key1": "value1",
            "key2": "value2"
        }

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

        # see: https://en.wikipedia.org/wiki/Pangram
        full_sentence = ['The', 'quick', 'brown', 'fox', 'jumps', 'over', 
            'the', 'lazy', 'dog', 'etaoin', 'shrdlu', 'Now','is', 'the', 
            'time', 'for', 'all', 'good', 'men', 'to', 'come', 'to', 'the', 
            'aid', 'of', 'their', 'country',
            'Jived', 'fox', 'nymph', 'grabs', 'quick', 'waltz',
            'Glib', 'jocks', 'quiz', 'nymph', 'to', 'vex', 'dwarf',
            'Sphinx', 'of', 'black', 'quartz,', 'judge', 'my', 'vow',
            'How', 'vexingly', 'quick', 'daft', 'zebras', 'jump',
            'The', 'five', 'boxing', 'wizards', 'jump', 'quickly',
            'Pack', 'my', 'box', 'with', 'five', 'dozen', 'liquor', 'jugs'
            ]

        for i in range(0, 2):

            timemap = cm.getTimeMap(urits[i])
            index = i + 1

            for memento in timemap["mementos"]["list"]:

                index += 1
            
                urim = memento["uri"]
                mdt = memento["datetime"]

                innercontent = urim

                for j in range(0, index):
                    innercontent += "\n" + " ".join(full_sentence[(i + j + index):]) + " "

                innercontent += "\n" + str(mdt)

                content = "<html><body>{}</body></html>".format(innercontent)

                cm.addMemento(urim, bytes(content, "utf8"), headers)

        scores = compute_bytecount_across_TimeMap(
            cm, scores=None, tokenize=False, stemming=False
        )

        scores = compute_wordcount_across_TimeMap(
            cm, scores=scores, tokenize=True, stemming=True
        )

        scores = compute_jaccard_across_TimeMap(
            cm, scores=scores, tokenize=True, stemming=True
        )

        # scores = compute_cosine_across_TimeMap(
        #     cm, scores=scores, stemming=True
        # )

        scores = compute_sorensen_across_TimeMap(
            cm, scores=scores, tokenize=True, stemming=True
        )

        scores = compute_levenshtein_across_TimeMap(
            cm, scores=scores, tokenize=True, stemming=True
        )

        scores = compute_nlevenshtein_across_TimeMap(
            cm, scores=scores, tokenize=True, stemming=True
        )

        # scores = compute_tfintersection_across_TimeMap(
        #     cm, scores=scores, tokenize=True, stemming=True
        # )

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

                self.assertTrue( "bytecount" in scores["timemaps"][urit][urim]["timemap measures"] )
                self.assertTrue( "wordcount" in scores["timemaps"][urit][urim]["timemap measures"] )
                self.assertTrue( "jaccard" in scores["timemaps"][urit][urim]["timemap measures"] )
                self.assertTrue( "sorensen" in scores["timemaps"][urit][urim]["timemap measures"] )
                self.assertTrue( "levenshtein" in scores["timemaps"][urit][urim]["timemap measures"] )
                self.assertTrue( "nlevenshtein" in scores["timemaps"][urit][urim]["timemap measures"] )

        expected_scores = {   'timemaps': {   'timemap1': {   'memento11': {   'timemap measures': {   'bytecount': {   'comparison score': 0.0,
                                                                                              'individual score': 723},
                                                                             'jaccard': {   'comparison score': 0.0},
                                                                             'levenshtein': {   'comparison score': 0},
                                                                             'nlevenshtein': {   'comparison score': 0.0},
                                                                             'sorensen': {   'comparison score': 0.0},
                                                                             'wordcount': {   'comparison score': 0.0,
                                                                                              'individual score': 94}}},
                                    'memento12': {   'timemap measures': {   'bytecount': {   'comparison score': -0.43015214384508993,
                                                                                              'individual score': 1034},
                                                                             'jaccard': {   'comparison score': 0.11363636363636365},
                                                                             'levenshtein': {   'comparison score': 45},
                                                                             'nlevenshtein': {   'comparison score': 0.3333333333333333},
                                                                             'sorensen': {   'comparison score': 0.06024096385542166},
                                                                             'wordcount': {   'comparison score': -0.43617021276595747,
                                                                                              'individual score': 135}}},
                                    'memento13': {   'timemap measures': {   'bytecount': {   'comparison score': -0.8409405255878284,
                                                                                              'individual score': 1331},
                                                                             'jaccard': {   'comparison score': 0.15555555555555556},
                                                                             'levenshtein': {   'comparison score': 86},
                                                                             'nlevenshtein': {   'comparison score': 0.48863636363636365},
                                                                             'sorensen': {   'comparison score': 0.08433734939759041},
                                                                             'wordcount': {   'comparison score': -0.8723404255319149,
                                                                                              'individual score': 176}}}},
                    'timemap2': {   'memento21': {   'timemap measures': {   'bytecount': {   'comparison score': 0.0,
                                                                                              'individual score': 1019},
                                                                             'jaccard': {   'comparison score': 0.0},
                                                                             'levenshtein': {   'comparison score': 0},
                                                                             'nlevenshtein': {   'comparison score': 0.0},
                                                                             'sorensen': {   'comparison score': 0.0},
                                                                             'wordcount': {   'comparison score': 0.0,
                                                                                              'individual score': 133}}},
                                    'memento22': {   'timemap measures': {   'bytecount': {   'comparison score': -0.28655544651619236,
                                                                                              'individual score': 1311},
                                                                             'jaccard': {   'comparison score': 0.09302325581395354},
                                                                             'levenshtein': {   'comparison score': 45},
                                                                             'nlevenshtein': {   'comparison score': 0.25862068965517243},
                                                                             'sorensen': {   'comparison score': 0.04878048780487809},
                                                                             'wordcount': {   'comparison score': -0.30827067669172936,
                                                                                              'individual score': 174}}},
                                    'memento23': {   'timemap measures': {   'bytecount': {   'comparison score': -0.5593719332679097,
                                                                                              'individual score': 1589},
                                                                             'jaccard': {   'comparison score': 0.13636363636363635},
                                                                             'levenshtein': {   'comparison score': 86},
                                                                             'nlevenshtein': {   'comparison score': 0.4056603773584906},
                                                                             'sorensen': {   'comparison score': 0.07317073170731703},
                                                                             'wordcount': {   'comparison score': -0.593984962406015,
                                                                                              'individual score': 212}}}}}}

        for measure in same_scores:

            # we'll have to test TF intersection separately,
            # the way that I build the sentences does not
            # have enough different words
            if measure == "tfintersection" or measure == "cosine":
                continue

            for urit in scores["timemaps"]:

                for urim in scores["timemaps"][urit]:

                    # comparisons with themselves should match
                    if urim == "memento11" or urim == "memento21":
                        self.assertEqual(
                            scores["timemaps"][urit][urim]["timemap measures"][measure]["comparison score"],
                            same_scores[measure],
                            "measure {} does not compute the correct score "
                            "for document sameness".format(measure)
                        )
                    else:
                        self.assertNotEqual(
                            scores["timemaps"][urit][urim]["timemap measures"][measure]["comparison score"],
                            same_scores[measure],
                            "measure {} does not compute the correct score "
                            "for document differentness for URI-M {}".format(
                                measure, urim)
                        )

                    # for regression
                    self.assertAlmostEqual(
                            scores["timemaps"][urit][urim]["timemap measures"][measure]["comparison score"],
                            expected_scores["timemaps"][urit][urim]["timemap measures"][measure]["comparison score"],
                            msg="measure {} does not compute the expected score "
                            "for URI-M {}".format(measure, urim)
                    )

        shutil.rmtree(working_directory)

    def test_tf_intersection(self):

        working_directory = "/tmp/test_tf_intersection"

        if os.path.exists(working_directory):
            shutil.rmtree(working_directory)

        cm = collectionmodel.CollectionModel(working_directory=working_directory)

        headers = {
            "key1": "value1",
            "key2": "value2"
        }

        full_sentence = ['The', 'quick', 'brown', 'fox', 'jumps', 'over', 
            'the', 'lazy', 'dog', 'etaoin', 'shrdlu', 'Now','is', 'the', 
            'time', 'for', 'all', 'good', 'men', 'to', 'come', 'to', 'the', 
            'aid', 'of', 'their', 'country',
            'Jived', 'fox', 'nymph', 'grabs', 'quick', 'waltz',
            'Glib', 'jocks', 'quiz', 'nymph', 'to', 'vex', 'dwarf',
            'Sphinx', 'of', 'black', 'quartz,', 'judge', 'my', 'vow',
            'How', 'vexingly', 'quick', 'daft', 'zebras', 'jump',
            'The', 'five', 'boxing', 'wizards', 'jump', 'quickly',
            'Pack', 'my', 'box', 'with', 'five', 'dozen', 'liquor', 'jugs'
            ]

        memcontent1 = bytes("<html><body>{}</body></html>".format(" ".join(full_sentence[0:20])), "utf8")
        memcontent2 = bytes("<html><body>{}</body></html>".format(" ".join(full_sentence[20:-1])), "utf8")

        timemap_content ="""<original1>; rel="original",
<timemap1>; rel="self"; type="application/link-format"; from="Tue, 21 Mar 2016 15:45:06 GMT"; until="Tue, 21 Mar 2018 15:45:12 GMT",
<timegate1>; rel="timegate",
<memento11>; rel="first memento"; datetime="Tue, 21 Jan 2016 15:45:06 GMT",
<memento12>; rel="last memento"; datetime="Tue, 21 Jan 2018 15:45:12 GMT"
"""

        cm.addTimeMap("timemap1", timemap_content, headers)
        cm.addMemento("memento11", memcontent1, headers)
        cm.addMemento("memento12", memcontent2, headers)

        scores = compute_tfintersection_across_TimeMap(cm, scores=None, tokenize=None, stemming=True)

        pp.pprint(scores)

        self.assertNotEqual(
            same_scores['tfintersection'],
            scores['timemaps']['timemap1']['memento12']['timemap measures']['tfintersection']['comparison score']
        )

        # after removing stop words, the first document consists of 11 words
        # the comparison document consists of more than 20 words
        # the terms 'quick' and 'jump' overlap, giving 2 overlapping terms
        # 11 - 2 = 9, hence the comparison score of 9
        expected_scores = {   'timemaps': {   'timemap1': {   'memento11': {   'timemap measures': {   'tfintersection': {   'comparison score': 0}}},
                                    'memento12': {   'timemap measures': {   'tfintersection': {   'comparison score': 9}}}}}}

        # for regression
        self.assertAlmostEqual(
            expected_scores['timemaps']['timemap1']['memento12']['timemap measures']['tfintersection']['comparison score'],
            scores['timemaps']['timemap1']['memento12']['timemap measures']['tfintersection']['comparison score']
        )

        shutil.rmtree(working_directory)

    def test_cosine(self):

        working_directory = "/tmp/test_tf_intersection"

        if os.path.exists(working_directory):
            shutil.rmtree(working_directory)

        cm = collectionmodel.CollectionModel(working_directory=working_directory)

        headers = {
            "key1": "value1",
            "key2": "value2"
        }

        full_sentence = ['The', 'quick', 'brown', 'fox', 'jumps', 'over', 
            'the', 'lazy', 'dog', 'etaoin', 'shrdlu', 'Now','is', 'the', 
            'time', 'for', 'all', 'good', 'men', 'to', 'come', 'to', 'the', 
            'aid', 'of', 'their', 'country',
            'Jived', 'fox', 'nymph', 'grabs', 'quick', 'waltz',
            'Glib', 'jocks', 'quiz', 'nymph', 'to', 'vex', 'dwarf',
            'Sphinx', 'of', 'black', 'quartz,', 'judge', 'my', 'vow',
            'How', 'vexingly', 'quick', 'daft', 'zebras', 'jump',
            'The', 'five', 'boxing', 'wizards', 'jump', 'quickly',
            'Pack', 'my', 'box', 'with', 'five', 'dozen', 'liquor', 'jugs'
            ]

        memcontent1 = bytes("<html><body>{}</body></html>".format(" ".join(full_sentence[0:20])), "utf8")
        memcontent2 = bytes("<html><body>{}</body></html>".format(" ".join(full_sentence[20:-1])), "utf8")

        timemap_content ="""<original1>; rel="original",
<timemap1>; rel="self"; type="application/link-format"; from="Tue, 21 Mar 2016 15:45:06 GMT"; until="Tue, 21 Mar 2018 15:45:12 GMT",
<timegate1>; rel="timegate",
<memento11>; rel="first memento"; datetime="Tue, 21 Jan 2016 15:45:06 GMT",
<memento12>; rel="last memento"; datetime="Tue, 21 Jan 2018 15:45:12 GMT"
"""

        cm.addTimeMap("timemap1", timemap_content, headers)
        cm.addMemento("memento11", memcontent1, headers)
        cm.addMemento("memento12", memcontent2, headers)

        scores = compute_cosine_across_TimeMap(cm, scores=None, tokenize=None, stemming=True)

        pp.pprint(scores)

        self.assertNotEqual(
            same_scores['cosine'],
            scores['timemaps']['timemap1']['memento12']['timemap measures']['cosine']['comparison score']
        )

        # after removing stop words, the first document consists of 11 words
        # the comparison document consists of more than 20 words
        # the terms 'quick' and 'jump' overlap, giving 2 overlapping terms
        # 11 - 2 = 9, hence the comparison score of 9
        expected_scores = {   'timemaps': {   'timemap1': {   'memento11': {   'timemap measures': {   'cosine': {   'comparison score': 1.0000000000000002}}},
                                    'memento12': {   'timemap measures': {   'cosine': {   'comparison score': 0.117041776804418}}}}}}

        # for regression
        self.assertAlmostEqual(
            expected_scores['timemaps']['timemap1']['memento12']['timemap measures']['cosine']['comparison score'],
            scores['timemaps']['timemap1']['memento12']['timemap measures']['cosine']['comparison score']
        )

        shutil.rmtree(working_directory)