import os
import string
import random
import unittest
import shutil
import pprint

pp = pprint.PrettyPrinter(indent=4)

from otmt import collectionmodel, compute_bytecount_across_TimeMap, \
    compute_wordcount_across_TimeMap, compute_jaccard_across_TimeMap, \
    compute_cosine_across_TimeMap, compute_sorensen_across_TimeMap, \
    compute_levenshtein_across_TimeMap, compute_nlevenshtein_across_TimeMap, \
    compute_tfintersection_across_TimeMap, compute_tfsimhash_across_TimeMap, \
    compute_rawsimhash_across_TimeMap, MeasureModel

import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

same_scores = {
    "cosine": 1.0,
    "bytecount": 0,
    "wordcount": 0,
    "tfintersection": 0,
    "jaccard": 0.0,
    "sorensen": 0,
    "levenshtein": 0,
    "nlevenshtein": 0,
    "raw_simhash": 0,
    "tf_simhash": 0
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

        mm = MeasureModel()

        mm = compute_bytecount_across_TimeMap(
            cm, mm, tokenize=False, stemming=False
        )

        mm = compute_wordcount_across_TimeMap(
            cm, mm, tokenize=True, stemming=True
        )

        mm = compute_jaccard_across_TimeMap(
            cm, mm, tokenize=True, stemming=True
        )

        mm = compute_cosine_across_TimeMap(
            cm, mm, tokenize=True, stemming=True
        )

        mm = compute_sorensen_across_TimeMap(
            cm, mm, tokenize=True, stemming=True
        )

        mm = compute_levenshtein_across_TimeMap(
            cm, mm, tokenize=True, stemming=True
        )

        mm = compute_nlevenshtein_across_TimeMap(
            cm, mm, tokenize=True, stemming=True
        )

        mm = compute_tfintersection_across_TimeMap(
            cm, mm, tokenize=True, stemming=True
        )

        mm = compute_rawsimhash_across_TimeMap(
            cm, mm, tokenize=False, stemming=False
        )

        mm = compute_tfsimhash_across_TimeMap(
            cm, mm, tokenize=True, stemming=True
        )

        self.assertTrue( "timemap1" in mm.get_TimeMap_URIs() )
        self.assertTrue( "timemap2" in mm.get_TimeMap_URIs() )

        self.assertTrue( "memento11" in mm.get_Memento_URIs_in_TimeMap("timemap1") )
        self.assertTrue( "memento12" in mm.get_Memento_URIs_in_TimeMap("timemap1") )
        self.assertTrue( "memento13" in mm.get_Memento_URIs_in_TimeMap("timemap1") )

        self.assertTrue( "memento21" in mm.get_Memento_URIs_in_TimeMap("timemap2") )
        self.assertTrue( "memento22" in mm.get_Memento_URIs_in_TimeMap("timemap2") )
        self.assertTrue( "memento23" in mm.get_Memento_URIs_in_TimeMap("timemap2") )

        for measure in same_scores:

            print("evaluating measure {}".format(measure))

            for urit in mm.get_TimeMap_URIs():

                for urim in mm.get_Memento_URIs_in_TimeMap(urit):

                    self.assertAlmostEqual(
                        mm.get_score(urit, urim, "timemap measures", measure),
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

        mm = MeasureModel()

        mm = compute_bytecount_across_TimeMap(
            cm, mm, tokenize=False, stemming=False
        )

        mm = compute_wordcount_across_TimeMap(
            cm, mm, tokenize=True, stemming=True
        )

        mm = compute_jaccard_across_TimeMap(
            cm, mm, tokenize=True, stemming=True
        )

        mm = compute_cosine_across_TimeMap(
            cm, mm, stemming=True
        )

        mm = compute_sorensen_across_TimeMap(
            cm, mm, tokenize=True, stemming=True
        )

        mm = compute_levenshtein_across_TimeMap(
            cm, mm, tokenize=True, stemming=True
        )

        mm = compute_nlevenshtein_across_TimeMap(
            cm, mm, tokenize=True, stemming=True
        )

        mm = compute_tfintersection_across_TimeMap(
            cm, mm, tokenize=True, stemming=True
        )

        mm = compute_rawsimhash_across_TimeMap(
            cm, mm, tokenize=False, stemming=False
        )

        mm = compute_tfsimhash_across_TimeMap(
            cm, mm, tokenize=True, stemming=True
        )

        self.assertTrue( "timemap1" in mm.get_TimeMap_URIs() )

        self.assertTrue( "memento11" in mm.get_Memento_URIs_in_TimeMap("timemap1") )

        urit = "timemap1"

        for measure in same_scores:

            for urit in mm.get_TimeMap_URIs():

                for urim in mm.get_Memento_URIs_in_TimeMap("timemap1"):

                    self.assertAlmostEqual(
                        mm.get_score(urit, urim, "timemap measures", measure),
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

        mm = MeasureModel()

        mm = compute_bytecount_across_TimeMap(
            cm, mm, tokenize=False, stemming=False
        )

        mm = compute_wordcount_across_TimeMap(
            cm, mm, tokenize=True, stemming=True
        )

        mm = compute_jaccard_across_TimeMap(
            cm, mm, tokenize=True, stemming=True
        )

        # mm = compute_cosine_across_TimeMap(
        #     cm, scores=scores, stemming=True
        # )

        mm = compute_sorensen_across_TimeMap(
            cm, mm, tokenize=True, stemming=True
        )

        mm = compute_levenshtein_across_TimeMap(
            cm, mm, tokenize=True, stemming=True
        )

        mm = compute_nlevenshtein_across_TimeMap(
            cm, mm, tokenize=True, stemming=True
        )

        # mm = compute_tfintersection_across_TimeMap(
        #     cm, scores=scores, tokenize=True, stemming=True
        # )

        # mm = compute_rawsimhash_across_TimeMap(
        #     cm, mm, tokenize=False, stemming=False
        # )

        self.assertTrue( "timemap1" in mm.get_TimeMap_URIs() )
        self.assertTrue( "timemap2" in mm.get_TimeMap_URIs() )

        self.assertTrue( "memento11" in mm.get_Memento_URIs_in_TimeMap("timemap1") )
        self.assertTrue( "memento12" in mm.get_Memento_URIs_in_TimeMap("timemap1") )
        self.assertTrue( "memento13" in mm.get_Memento_URIs_in_TimeMap("timemap1") )

        self.assertTrue( "memento21" in mm.get_Memento_URIs_in_TimeMap("timemap2") )
        self.assertTrue( "memento22" in mm.get_Memento_URIs_in_TimeMap("timemap2") )
        self.assertTrue( "memento23" in mm.get_Memento_URIs_in_TimeMap("timemap2") )

        expected_scores = {   'timemaps': {   'timemap1': {   'memento11': {   'timemap measures': {   'bytecount': {   'comparison score': 0.0,
                                                                                              'individual score': 723},
                                                                             'jaccard': {   'comparison score': 0.0},
                                                                             'levenshtein': {   'comparison score': 0},
                                                                             'nlevenshtein': {   'comparison score': 0.0},
                                                                             'sorensen': {   'comparison score': 0.0},
                                                                             'wordcount': {   'comparison score': 0.0,
                                                                                              'individual score': 94}}},
                                                                             
                                    'memento12': {   'timemap measures': {   'bytecount': {   'comparison score': 0.43015214384508993,
                                                                                              'individual score': 1034},
                                                                             'jaccard': {   'comparison score': 0.11363636363636365},
                                                                             'levenshtein': {   'comparison score': 45},
                                                                             'nlevenshtein': {   'comparison score': 0.3333333333333333},
                                                                             'sorensen': {   'comparison score': 0.06024096385542166},
                                                                             'wordcount': {   'comparison score': 0.43617021276595747,
                                                                                              'individual score': 135}}},
                                    'memento13': {   'timemap measures': {   'bytecount': {   'comparison score': 0.8409405255878284,
                                                                                              'individual score': 1331},
                                                                             'jaccard': {   'comparison score': 0.15555555555555556},
                                                                             'levenshtein': {   'comparison score': 86},
                                                                             'nlevenshtein': {   'comparison score': 0.48863636363636365},
                                                                             'sorensen': {   'comparison score': 0.08433734939759041},
                                                                             'wordcount': {   'comparison score': 0.8723404255319149,
                                                                                              'individual score': 176}}}},
                    'timemap2': {   'memento21': {   'timemap measures': {   'bytecount': {   'comparison score': 0.0,
                                                                                              'individual score': 1019},
                                                                             'jaccard': {   'comparison score': 0.0},
                                                                             'levenshtein': {   'comparison score': 0},
                                                                             'nlevenshtein': {   'comparison score': 0.0},
                                                                             'sorensen': {   'comparison score': 0.0},
                                                                             'wordcount': {   'comparison score': 0.0,
                                                                                              'individual score': 133}}},
                                    'memento22': {   'timemap measures': {   'bytecount': {   'comparison score': 0.28655544651619236,
                                                                                              'individual score': 1311},
                                                                             'jaccard': {   'comparison score': 0.09302325581395354},
                                                                             'levenshtein': {   'comparison score': 45},
                                                                             'nlevenshtein': {   'comparison score': 0.25862068965517243},
                                                                             'sorensen': {   'comparison score': 0.04878048780487809},
                                                                             'wordcount': {   'comparison score': 0.30827067669172936,
                                                                                              'individual score': 174}}},
                                    'memento23': {   'timemap measures': {   'bytecount': {   'comparison score': 0.5593719332679097,
                                                                                              'individual score': 1589},
                                                                             'jaccard': {   'comparison score': 0.13636363636363635},
                                                                             'levenshtein': {   'comparison score': 86},
                                                                             'nlevenshtein': {   'comparison score': 0.4056603773584906},
                                                                             'sorensen': {   'comparison score': 0.07317073170731703},
                                                                             'wordcount': {   'comparison score': 0.593984962406015,
                                                                                              'individual score': 212}}}}}}

        for measure in same_scores:

            # we'll have to test TF intersection separately,
            # the way that I build the sentences does not
            # have enough different words
            if measure == "tfintersection" or measure == "cosine" or \
                measure == "raw_simhash" or measure == "tf_simhash":
                continue

            for urit in mm.get_TimeMap_URIs():

                for urim in mm.get_Memento_URIs_in_TimeMap(urit):

                    # comparisons with themselves should match
                    if urim == "memento11" or urim == "memento21":
                        self.assertEqual(
                            mm.get_score(urit, urim, "timemap measures", measure),
                            same_scores[measure],
                            "measure {} does not compute the correct score "
                            "for document sameness".format(measure)
                        )
                    else:
                        self.assertNotEqual(
                            mm.get_score(urit, urim, "timemap measures", measure),
                            same_scores[measure],
                            "measure {} does not compute the correct score "
                            "for document differentness for URI-M {}".format(
                                measure, urim)
                        )

                    # for regression
                    self.assertAlmostEqual(
                            mm.get_score(urit, urim, "timemap measures", measure),
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

        mm = MeasureModel()

        mm = compute_tfintersection_across_TimeMap(cm, mm, tokenize=None, stemming=True)

        self.assertNotEqual(
            same_scores['tfintersection'],
            mm.get_score("timemap1", "memento12", "timemap measures", "tfintersection")
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
            mm.get_score("timemap1", "memento12", "timemap measures", "tfintersection")
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

        mm = MeasureModel()       

        mm = compute_cosine_across_TimeMap(cm, mm, tokenize=None, stemming=True)

        self.assertNotEqual(
            same_scores['cosine'],
            mm.get_score("timemap1", "memento12", "timemap measures", "cosine")
        )

        # after removing stop words, the first document consists of 11 words
        # the comparison document consists of more than 20 words
        # the terms 'quick' and 'jump' overlap, giving 2 overlapping terms
        # 11 - 2 = 9, hence the comparison score of 9
        expected_scores = {   'timemaps': {   'timemap1': {   'memento11': {   'timemap measures': {   'cosine': {   'comparison score': 1.0}}},
                                    'memento12': {   'timemap measures': {   'cosine': {   'comparison score': 0.12882843018556128}}}}}}

        # for regression
        self.assertAlmostEqual(
            expected_scores['timemaps']['timemap1']['memento12']['timemap measures']['cosine']['comparison score'],
            mm.get_score("timemap1", "memento12", "timemap measures", "cosine")
        )

        shutil.rmtree(working_directory)

    def test_empty_documents(self):

        working_directory = "/tmp/test_empty_documents"

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
<memento11>; rel="first memento"; datetime="Tue, 21 Jan 2016 15:45:06 GMT",
<memento12>; rel="memento"; datetime="Tue, 21 Jan 2017 15:45:06 GMT",
<memento13>; rel="last memento"; datetime="Tue, 21 Jan 2018 15:45:12 GMT"
"""

        empty_html_document = b"<html><body></body></html>"

        # if the first document is empty and all subsequent docs are empty, 
        # then we are still on-topic, but this is to be debated
        cm.addTimeMap("timemap1", timemap_content, headers)
        cm.addMemento("memento11", empty_html_document, headers)
        cm.addMemento("memento12", empty_html_document, headers)
        cm.addMemento("memento13", empty_html_document, headers)

        mm = MeasureModel()

        mm = compute_jaccard_across_TimeMap(
            cm, mm, tokenize=None, stemming=True)

        mm = compute_cosine_across_TimeMap(
            cm, mm, tokenize=None, stemming=True)
        
        for urit in mm.get_TimeMap_URIs():

            for urim in mm.get_Memento_URIs_in_TimeMap(urit):

                for measurename in ["cosine", "jaccard"]:

                    self.assertEquals(
                        mm.get_Memento_measurement_error_message(urim, "timemap measures", measurename),
                        "After processing content, the first memento in TimeMap is now empty, cannot effectively compare memento content"
                    )

        shutil.rmtree(working_directory)

    def test_empty_document_in_middle(self):

        working_directory = "/tmp/test_empty_documents"

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
<memento11>; rel="first memento"; datetime="Tue, 21 Jan 2016 15:45:06 GMT",
<memento12>; rel="memento"; datetime="Tue, 21 Jan 2017 15:45:06 GMT",
<memento13>; rel="last memento"; datetime="Tue, 21 Jan 2018 15:45:12 GMT"
"""

        full_html_document = b"<html>The quick brown fox jumps over the lazy dog<body></html>"
        empty_html_document = b"<html><body></body></html>"

        cm.addTimeMap("timemap1", timemap_content, headers)
        cm.addMemento("memento11", full_html_document, headers)
        cm.addMemento("memento12", empty_html_document, headers)
        cm.addMemento("memento13", full_html_document, headers)

        mm = MeasureModel()

        mm = compute_jaccard_across_TimeMap(
            cm, mm, tokenize=None, stemming=True)

        # Rather than dealing with empty documents, this throws
        # ValueError: empty vocabulary; perhaps the documents only contain stop words
        # it should handle the error gracefully
        mm = compute_cosine_across_TimeMap(
            cm, mm, tokenize=None, stemming=True)

        self.assertAlmostEqual(
            mm.get_score("timemap1", "memento11", "timemap measures", "cosine"),
            1.0
        )

        self.assertAlmostEqual(
            mm.get_score("timemap1", "memento12", "timemap measures", "cosine"),
            0.0
        )

        self.assertAlmostEqual(
            mm.get_score("timemap1", "memento13", "timemap measures", "cosine"),
            1.0
        )

        shutil.rmtree(working_directory)

    def test_first_document_is_empty_otherwise_filled(self):

        working_directory = "/tmp/test_empty_documents"

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
<memento11>; rel="first memento"; datetime="Tue, 21 Jan 2016 15:45:06 GMT",
<memento12>; rel="memento"; datetime="Tue, 21 Jan 2017 15:45:06 GMT",
<memento13>; rel="last memento"; datetime="Tue, 21 Jan 2018 15:45:12 GMT"
"""

        full_html_document = b"<html>The quick brown fox jumps over the lazy dog<body></html>"
        empty_html_document = b"<html><body></body></html>"

        cm.addTimeMap("timemap1", timemap_content, headers)
        cm.addMemento("memento11", empty_html_document, headers)
        cm.addMemento("memento12", full_html_document, headers)
        cm.addMemento("memento13", full_html_document, headers)

        mm = MeasureModel()

        mm = compute_jaccard_across_TimeMap(
            cm, mm, tokenize=None, stemming=True)

        mm = compute_cosine_across_TimeMap(
            cm, mm, tokenize=None, stemming=True)

        for urit in mm.get_TimeMap_URIs():

            for urim in mm.get_Memento_URIs_in_TimeMap(urit):

                for measurename in ["cosine", "jaccard"]:

                    self.assertEquals(
                        mm.get_Memento_measurement_error_message(urim, "timemap measures", measurename),
                        "After processing content, the first memento in TimeMap is now empty, cannot effectively compare memento content"
                    )

        shutil.rmtree(working_directory)

    def test_handle_boilerplateremoval_error_due_to_empty_document(self):

        working_directory = "/tmp/test_handle_boilerplateremoval_error"

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
<memento11>; rel="first memento"; datetime="Tue, 21 Jan 2016 15:45:06 GMT",
<memento12>; rel="memento"; datetime="Tue, 21 Jan 2017 15:45:06 GMT",
<memento13>; rel="last memento"; datetime="Tue, 21 Jan 2018 15:45:12 GMT"
"""

        full_html_document = b"<html>The quick brown fox jumps over the lazy dog<body></html>"
        really_empty_document = b""

        cm.addTimeMap("timemap1", timemap_content, headers)
        cm.addMemento("memento11", full_html_document, headers)
        cm.addMemento("memento12", really_empty_document, headers)
        cm.addMemento("memento13", full_html_document, headers)

        # TODO: how to handle the empty document?

        mm = MeasureModel()

        mm = compute_jaccard_across_TimeMap(
            cm, mm, tokenize=None, stemming=True)

        pp.pprint(mm.scoremodel)

        self.assertEqual(
            mm.get_Memento_measurement_error_message("memento12", "timemap measures", "jaccard"),
            "CollectionModelBoilerPlateRemovalFailureException(\"ParserError('Document is empty',)\",)"
        )

        mm = compute_cosine_across_TimeMap(
            cm, mm, tokenize=None, stemming=True)

        self.assertEqual(
            mm.get_Memento_measurement_error_message("memento12", "timemap measures", "cosine"),
            "CollectionModelBoilerPlateRemovalFailureException(\"ParserError('Document is empty',)\",)"
        )


        shutil.rmtree(working_directory)

    def test_handle_boilerplateremoval_error_due_to_empty_first_document(self):

        working_directory = "/tmp/test_handle_boilerplateremoval_error"

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
<memento11>; rel="first memento"; datetime="Tue, 21 Jan 2016 15:45:06 GMT",
<memento12>; rel="memento"; datetime="Tue, 21 Jan 2017 15:45:06 GMT",
<memento13>; rel="last memento"; datetime="Tue, 21 Jan 2018 15:45:12 GMT"
"""

        full_html_document = b"<html>The quick brown fox jumps over the lazy dog<body></html>"
        really_empty_document = b""

        cm.addTimeMap("timemap1", timemap_content, headers)
        cm.addMemento("memento11", really_empty_document, headers)
        cm.addMemento("memento12", full_html_document, headers)
        cm.addMemento("memento13", full_html_document, headers)

        # TODO: how to handle the empty document?

        mm = MeasureModel()

        mm = compute_jaccard_across_TimeMap(
            cm, mm, tokenize=None, stemming=True)

        pp.pprint(mm.scoremodel)

        self.assertEqual(
            mm.get_Memento_measurement_error_message("memento11", "timemap measures", "jaccard"),
            "Boilerplate removal error with first memento in TimeMap, cannot effectively compare memento content"
        )

        self.assertEqual(
            mm.get_Memento_measurement_error_message("memento12", "timemap measures", "jaccard"),
            "Boilerplate removal error with first memento in TimeMap, cannot effectively compare memento content"
        )

        self.assertEqual(
            mm.get_Memento_measurement_error_message("memento13", "timemap measures", "jaccard"),
            "Boilerplate removal error with first memento in TimeMap, cannot effectively compare memento content"
        )

        mm = compute_cosine_across_TimeMap(
            cm, mm, tokenize=None, stemming=True)

        self.assertEqual(
            mm.get_Memento_measurement_error_message("memento11", "timemap measures", "cosine"),
            "Boilerplate removal error with first memento in TimeMap, cannot effectively compare memento content"
        )

        self.assertEqual(
            mm.get_Memento_measurement_error_message("memento12", "timemap measures", "cosine"),
            "Boilerplate removal error with first memento in TimeMap, cannot effectively compare memento content"
        )

        self.assertEqual(
            mm.get_Memento_measurement_error_message("memento13", "timemap measures", "cosine"),
            "Boilerplate removal error with first memento in TimeMap, cannot effectively compare memento content"
        )


        shutil.rmtree(working_directory)

    def test_raw_simhash(self):

        working_directory = "/tmp/test_raw_simhash"

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

        mm = MeasureModel()

        mm = compute_rawsimhash_across_TimeMap(cm, mm, tokenize=None, stemming=True)

        self.assertNotEqual(
            same_scores['raw_simhash'],
            mm.get_score("timemap1", "memento12", "timemap measures", "raw_simhash")
        )

        # after removing stop words, the first document consists of 11 words
        # the comparison document consists of more than 20 words
        # the terms 'quick' and 'jump' overlap, giving 2 overlapping terms
        # 11 - 2 = 9, hence the comparison score of 9
        expected_scores = {   'timemaps': {   'timemap1': {   'memento11': {   'timemap measures': {   'raw_simhash': {   'comparison score': 0}}},
                                    'memento12': {   'timemap measures': {   'raw_simhash': {   'comparison score': 36}}}}}}

        # for regression
        self.assertAlmostEqual(
            expected_scores['timemaps']['timemap1']['memento12']['timemap measures']['raw_simhash']['comparison score'],
            mm.get_score("timemap1", "memento12", "timemap measures", "raw_simhash")
        )

        shutil.rmtree(working_directory)

    def test_tf_simhash(self):

        working_directory = "/tmp/test_tf_simhash"

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

        mm = MeasureModel()

        mm = compute_tfsimhash_across_TimeMap(cm, mm, tokenize=None, stemming=True)

        self.assertNotEqual(
            same_scores['raw_simhash'],
            mm.get_score("timemap1", "memento12", "timemap measures", "tf_simhash")
        )

        # after removing stop words, the first document consists of 11 words
        # the comparison document consists of more than 20 words
        # the terms 'quick' and 'jump' overlap, giving 2 overlapping terms
        # 11 - 2 = 9, hence the comparison score of 9
        expected_scores = {   'timemaps': {   'timemap1': {   'memento11': {   'timemap measures': {   'tf_simhash': {   'comparison score': 0}}},
                                    'memento12': {   'timemap measures': {   'tf_simhash': {   'comparison score': 24}}}}}}

        # for regression
        self.assertAlmostEqual(
            expected_scores['timemaps']['timemap1']['memento12']['timemap measures']['tf_simhash']['comparison score'],
            mm.get_score("timemap1", "memento12", "timemap measures", "tf_simhash")
        )

        shutil.rmtree(working_directory)