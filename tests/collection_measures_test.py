import os
import unittest
import shutil
import pprint

pp = pprint.PrettyPrinter(indent=4)

from otmt import collectionmodel, MeasureModel, \
    compute_jaccard_accross_collection, \
    compute_sorensen_accross_collection

import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class TestingCollectionMeasures(unittest.TestCase):

    def test_all_measures_same(self):

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

        mm = compute_jaccard_accross_collection(cm, mm)

        mm = compute_sorensen_accross_collection(cm, mm)

        pp.pprint(mm.generate_dict())


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

        mm = compute_jaccard_accross_collection(cm, mm)

        mm = compute_sorensen_accross_collection(cm, mm)

        pp.pprint(mm.generate_dict())