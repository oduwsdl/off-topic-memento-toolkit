import unittest
import os
import json
import pprint

pp = pprint.PrettyPrinter(indent=4)

from offtopic import MeasureModel, MeasureModelNoSuchMemento, \
    MeasureModelNoSuchTimeMap, MeasureModelNoSuchMeasure, \
    MeasureModelNoSuchMeasureType

class TestingMeasureModel(unittest.TestCase):

    def test_measuremodel_storage_happy_path(self):

        mm = MeasureModel()

        mm.set_score("timemap1", "memento1", "measuretype1", "measure1", 539)

        self.assertEqual(
            mm.get_score("timemap1", "memento1", "measuretype1", "measure1"),
            539
        )

        mm.set_TimeMap_access_error("timemap2", "this is an error message for timemap2")

        self.assertEqual(
            mm.get_TimeMap_access_error_message("timemap2"),
            "this is an error message for timemap2"
        )

        # mm.set_TimeMap_measurement_error("timemap3", "this is an error message for timemap3")

        # self.assertEqual(
        #     mm.get_TimeMap_measurement_error_message("timemap3"),
        #     "this is an error message for timemap3"
        # )

        mm.set_Memento_access_error("timemap4", "memento2", "this is a memento error message for memento2")

        self.assertEqual(
            mm.get_Memento_access_error_message("memento2"),
            "this is a memento error message for memento2"
        )

        mm.set_Memento_measurement_error("timemap5", "memento3", 
            "measuretype1", "measure1", "this is a memento error message for memento3")

        self.assertEqual(
            mm.get_Memento_measurement_error_message("memento3", "measuretype1", "measure1"),
            "this is a memento error message for memento3"
        )

        self.assertEqual(
            mm.get_stemmed("timemap1", "memento1", "measuretype1", "measure1"),
            None
        )

        mm.set_stemmed("timemap1", "memento1", "measuretype1", "measure1", True)

        self.assertEqual(
            mm.get_stemmed("timemap1", "memento1", "measuretype1", "measure1"),
            True
        )

        self.assertEqual(
            mm.get_tokenized("timemap1", "memento1", "measuretype1", "measure1"),
            None
        )

        mm.set_tokenized("timemap1", "memento1", "measuretype1", "measure1", True)

        self.assertEqual(
            mm.get_tokenized("timemap1", "memento1", "measuretype1", "measure1"),
            True
        )

        self.assertEqual(
            mm.get_removed_boilerplate("timemap1", "memento1", "measuretype1", "measure1"),
            None
        )

        mm.set_removed_boilerplate("timemap1", "memento1", "measuretype1", "measure1", True)

        self.assertEqual(
            mm.get_removed_boilerplate("timemap1", "memento1", "measuretype1", "measure1"),
            True
        )

        self.assertEqual(
            mm.get_TimeMap_URIs(),
            ["timemap1", "timemap2", "timemap4", "timemap5"]
        )

        self.assertEqual(
            mm.get_Memento_URIs_in_TimeMap("timemap1"),
            ["memento1"]
        )

        self.assertEqual(
            mm.get_Measures(),
            [("measuretype1", "measure1")]
        )

        jsonfilename = "/tmp/test_measuremodel_storage_happy_path.json"

        mm.set_score("timemap1", "memento4", "measuretype1", "measure1", 550)

        mm.save_as_JSON(jsonfilename)

        with open(jsonfilename) as jsonfile:
            jsondata = json.load(jsonfile)

        pp.pprint(jsondata)

        expectedjsondata = {
            "timemap1": {
                "memento1":{
                     "measuretype1": {
                         "measure1" : {
                            "stemmed": True,
                            "tokenized": True,
                            "removed boilerplate": True,
                            "comparison score": 539,
                            "topic status": None
                         }
                     },
                     "overall topic status": None
                },
                "memento4": {
                    "measuretype1": {
                        "measure1": {
                            "stemmed": None,
                            "tokenized": None,
                            "removed boilerplate": None,
                            "comparison score": 550,
                            "topic status": None
                        }
                    },
                    "overall topic status": None
                }
            },
            "timemap2": {
                "access error": "this is an error message for timemap2"
            },
            "timemap4": {
                "memento2": {
                    "access error": "this is a memento error message for memento2"
                }
            },
            "timemap5": {
                "memento3": {
                    "measuretype1": {
                        "measure1": {
                            "measurement error": "this is a memento error message for memento3"
                        }
                    }
                }
            }
        }

        self.maxDiff = None

        self.assertEqual(expectedjsondata, jsondata)

    def test_measuremodel_storage_sad_path(self):

        mm = MeasureModel()

        with self.assertRaises(MeasureModelNoSuchTimeMap):
            mm.get_score("timemap1", "memento1", "measuretype1", "measure1")

        with self.assertRaises(MeasureModelNoSuchTimeMap):
            mm.get_stemmed("timemap1", "memento1", "measuretype1", "measure1")

        with self.assertRaises(MeasureModelNoSuchTimeMap):
            mm.get_tokenized("timemap1", "memento1", "measuretype1", "measure1")

        with self.assertRaises(MeasureModelNoSuchTimeMap):
            mm.get_removed_boilerplate("timemap1", "memento1", "measuretype1", "measure1")

        mm.scoremodel["timemap1"] = {}

        with self.assertRaises(MeasureModelNoSuchMemento):
            mm.get_score("timemap1", "memento1", "measuretype1", "measure1")

        with self.assertRaises(MeasureModelNoSuchMemento):
            mm.get_stemmed("timemap1", "memento1", "measuretype1", "measure1")

        with self.assertRaises(MeasureModelNoSuchMemento):
            mm.get_tokenized("timemap1", "memento1", "measuretype1", "measure1")

        with self.assertRaises(MeasureModelNoSuchMemento):
            mm.get_removed_boilerplate("timemap1", "memento1", "measuretype1", "measure1")

        mm.scoremodel["timemap1"]["memento1"] = {}

        with self.assertRaises(MeasureModelNoSuchMeasureType):    
            mm.get_score("timemap1", "memento1", "measuretype1", "measure1")

        with self.assertRaises(MeasureModelNoSuchMeasureType):
            mm.get_stemmed("timemap1", "memento1", "measuretype1", "measure1")

        with self.assertRaises(MeasureModelNoSuchMeasureType):
            mm.get_tokenized("timemap1", "memento1", "measuretype1", "measure1")

        with self.assertRaises(MeasureModelNoSuchMeasureType):
            mm.get_removed_boilerplate("timemap1", "memento1", "measuretype1", "measure1")

        mm.scoremodel["timemap1"]["memento1"]["measuretype1"] = {}

        with self.assertRaises(MeasureModelNoSuchMeasure):
            mm.get_score("timemap1", "memento1", "measuretype1", "measure1")

        with self.assertRaises(MeasureModelNoSuchMeasure):
            mm.get_stemmed("timemap1", "memento1", "measuretype1", "measure1")

        with self.assertRaises(MeasureModelNoSuchMeasure):
            mm.get_tokenized("timemap1", "memento1", "measuretype1", "measure1")

        with self.assertRaises(MeasureModelNoSuchMeasure):
            mm.get_removed_boilerplate("timemap1", "memento1", "measuretype1", "measure1")

    # TODO:
    def test_measuremodel_offtopic_by_measure(self):
        pass

    # TODO:
    def test_measuremodel_offtopic_overall(self):
        pass

    # TODO:
    def test_CSV_output(self):
        pass

    # TODO:
    def test_goldstandard_output(self):
        pass