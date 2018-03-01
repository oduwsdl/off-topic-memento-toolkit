import unittest
import os
import json
import pprint

pp = pprint.PrettyPrinter(indent=4)

from otmt import MeasureModel, MeasureModelNoSuchMemento, \
    MeasureModelNoSuchTimeMap, MeasureModelNoSuchMeasure, \
    MeasureModelNoSuchMeasureType

class TestingMeasureModel(unittest.TestCase):

    def test_measuremodel_storage_happy_path(self):

        working_directory = "/tmp/test_measuremodel_storage_happy_path"

        if not os.path.exists(working_directory):
            os.makedirs(working_directory)

        mm = MeasureModel()

        mm.set_score("timemap1", "http://examplearchive.org/19700101000000/http://memento1", "measuretype1", "measure1", 539)

        self.assertEqual(
            mm.get_score("timemap1", "http://examplearchive.org/19700101000000/http://memento1", "measuretype1", "measure1"),
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

        mm.set_Memento_access_error("timemap4", "http://examplearchive.org/19700101000000/http://memento2", "this is a memento error message for http://examplearchive.org/19700101000000/http://memento2")

        self.assertEqual(
            mm.get_Memento_access_error_message("http://examplearchive.org/19700101000000/http://memento2"),
            "this is a memento error message for http://examplearchive.org/19700101000000/http://memento2"
        )

        mm.set_Memento_measurement_error("timemap5", "http://examplearchive.org/19700101000000/http://memento3", 
            "measuretype1", "measure1", "this is a memento error message for http://examplearchive.org/19700101000000/http://memento3")

        self.assertEqual(
            mm.get_Memento_measurement_error_message("http://examplearchive.org/19700101000000/http://memento3", "measuretype1", "measure1"),
            "this is a memento error message for http://examplearchive.org/19700101000000/http://memento3"
        )

        self.assertEqual(
            mm.get_stemmed("timemap1", "http://examplearchive.org/19700101000000/http://memento1", "measuretype1", "measure1"),
            None
        )

        mm.set_stemmed("timemap1", "http://examplearchive.org/19700101000000/http://memento1", "measuretype1", "measure1", True)

        self.assertEqual(
            mm.get_stemmed("timemap1", "http://examplearchive.org/19700101000000/http://memento1", "measuretype1", "measure1"),
            True
        )

        self.assertEqual(
            mm.get_tokenized("timemap1", "http://examplearchive.org/19700101000000/http://memento1", "measuretype1", "measure1"),
            None
        )

        mm.set_tokenized("timemap1", "http://examplearchive.org/19700101000000/http://memento1", "measuretype1", "measure1", True)

        self.assertEqual(
            mm.get_tokenized("timemap1", "http://examplearchive.org/19700101000000/http://memento1", "measuretype1", "measure1"),
            True
        )

        self.assertEqual(
            mm.get_removed_boilerplate("timemap1", "http://examplearchive.org/19700101000000/http://memento1", "measuretype1", "measure1"),
            None
        )

        mm.set_removed_boilerplate("timemap1", "http://examplearchive.org/19700101000000/http://memento1", "measuretype1", "measure1", True)

        self.assertEqual(
            mm.get_removed_boilerplate("timemap1", "http://examplearchive.org/19700101000000/http://memento1", "measuretype1", "measure1"),
            True
        )

        self.assertEqual(
            mm.get_TimeMap_URIs(),
            ["timemap1", "timemap2", "timemap4", "timemap5"]
        )

        self.assertEqual(
            mm.get_Memento_URIs_in_TimeMap("timemap1"),
            ["http://examplearchive.org/19700101000000/http://memento1"]
        )

        self.assertEqual(
            mm.get_Measures(),
            [("measuretype1", "measure1")]
        )

        mm.set_score("timemap1", "http://examplearchive.org/19700101000000/http://memento4", "measuretype1", "measure1", 550)

        mm.calculate_offtopic_by_measure("measuretype1", "measure1", 540, ">")
        mm.calculate_overall_offtopic_status()

        self.assertEqual(
            mm.get_off_topic_status_by_measure(
                "http://examplearchive.org/19700101000000/http://memento1",
                "measuretype1", "measure1"),
            "on-topic"
        )

        self.assertEqual(
            mm.get_off_topic_status_by_measure(
                "http://examplearchive.org/19700101000000/http://memento4",
                "measuretype1", "measure1"),
            "off-topic"
        )

        jsonfilename = "{}/test_measuremodel_storage_happy_path.json".format(working_directory)

        mm.save_as_JSON(jsonfilename)

        with open(jsonfilename) as jsonfile:
            jsondata = json.load(jsonfile)

        pp.pprint(jsondata)

        expectedjsondata = {
            "timemap1": {
                "http://examplearchive.org/19700101000000/http://memento1":{
                     "measuretype1": {
                         "measure1" : {
                            "stemmed": True,
                            "tokenized": True,
                            "removed boilerplate": True,
                            "comparison score": 539,
                            "topic status": "on-topic"
                         }
                     },
                     "overall topic status": "on-topic"
                },
                "http://examplearchive.org/19700101000000/http://memento4": {
                    "measuretype1": {
                        "measure1": {
                            "stemmed": None,
                            "tokenized": None,
                            "removed boilerplate": None,
                            "comparison score": 550,
                            "topic status": "off-topic"
                        }
                    },
                    "overall topic status": "off-topic"
                }
            },
            "timemap2": {
                "access error": "this is an error message for timemap2"
            },
            "timemap4": {
                "http://examplearchive.org/19700101000000/http://memento2": {
                    "access error": "this is a memento error message for http://examplearchive.org/19700101000000/http://memento2"
                }
            },
            "timemap5": {
                "http://examplearchive.org/19700101000000/http://memento3": {
                    "measuretype1": {
                        "measure1": {
                            "measurement error": "this is a memento error message for http://examplearchive.org/19700101000000/http://memento3"
                        }
                    }
                }
            }
        }

        self.maxDiff = None

        self.assertEqual(expectedjsondata, jsondata)

        csvfilename = "{}/test_measuremodel_storage_happy_path.csv".format(working_directory)

        mm.save_as_CSV(csvfilename)

        with open(csvfilename) as csvfile:
            csvdata = csvfile.read()

        expectedcsvdata ="""URI-T,URI-M,Error,Error Message,Content Length,Simhash,Measurement Type,Measurement Name,Comparison Score,Stemmed,Tokenized,Removed Boilerplate,Topic Status,Overall Topic Status
timemap1,http://examplearchive.org/19700101000000/http://memento1,,,,,measuretype1,measure1,539,True,True,True,on-topic,on-topic
timemap1,http://examplearchive.org/19700101000000/http://memento4,,,,,measuretype1,measure1,550,,,,off-topic,off-topic
timemap2,,TimeMap Access Error,this is an error message for timemap2,,,,,,,,,,
timemap4,http://examplearchive.org/19700101000000/http://memento2,Memento Access Error,this is a memento error message for http://examplearchive.org/19700101000000/http://memento2,,,,,,,,,,
timemap5,http://examplearchive.org/19700101000000/http://memento3,Memento Measurement Error,this is a memento error message for http://examplearchive.org/19700101000000/http://memento3,,,measuretype1,measure1,,,,,,
"""

        self.assertEqual(expectedcsvdata, csvdata)

        gsfilename = "{}/test_measuremodel_storage_happy_path.tsv".format(working_directory)

        mm.save_as_goldstandard(gsfilename)

        expectedgsdata = """id	date	URI	label
1	19700101000000	http://examplearchive.org/19700101000000/http://memento1	1
1	19700101000000	http://examplearchive.org/19700101000000/http://memento4	0
2			ERROR
3	19700101000000	http://examplearchive.org/19700101000000/http://memento2	ERROR
4	19700101000000	http://examplearchive.org/19700101000000/http://memento3	ERROR
"""

        with open(gsfilename) as gsfile:
            gsdata = gsfile.read()

        self.assertEqual(expectedgsdata, gsdata)

    def test_measuremodel_storage_sad_path(self):

        mm = MeasureModel()

        with self.assertRaises(MeasureModelNoSuchTimeMap):
            mm.get_score("timemap1", "http://examplearchive.org/19700101000000/http://memento1", "measuretype1", "measure1")

        with self.assertRaises(MeasureModelNoSuchTimeMap):
            mm.get_stemmed("timemap1", "http://examplearchive.org/19700101000000/http://memento1", "measuretype1", "measure1")

        with self.assertRaises(MeasureModelNoSuchTimeMap):
            mm.get_tokenized("timemap1", "http://examplearchive.org/19700101000000/http://memento1", "measuretype1", "measure1")

        with self.assertRaises(MeasureModelNoSuchTimeMap):
            mm.get_removed_boilerplate("timemap1", "http://examplearchive.org/19700101000000/http://memento1", "measuretype1", "measure1")

        mm.scoremodel["timemap1"] = {}

        with self.assertRaises(MeasureModelNoSuchMemento):
            mm.get_score("timemap1", "http://examplearchive.org/19700101000000/http://memento1", "measuretype1", "measure1")

        with self.assertRaises(MeasureModelNoSuchMemento):
            mm.get_stemmed("timemap1", "http://examplearchive.org/19700101000000/http://memento1", "measuretype1", "measure1")

        with self.assertRaises(MeasureModelNoSuchMemento):
            mm.get_tokenized("timemap1", "http://examplearchive.org/19700101000000/http://memento1", "measuretype1", "measure1")

        with self.assertRaises(MeasureModelNoSuchMemento):
            mm.get_removed_boilerplate("timemap1", "http://examplearchive.org/19700101000000/http://memento1", "measuretype1", "measure1")

        mm.scoremodel["timemap1"]["http://examplearchive.org/19700101000000/http://memento1"] = {}

        with self.assertRaises(MeasureModelNoSuchMeasureType):    
            mm.get_score("timemap1", "http://examplearchive.org/19700101000000/http://memento1", "measuretype1", "measure1")

        with self.assertRaises(MeasureModelNoSuchMeasureType):
            mm.get_stemmed("timemap1", "http://examplearchive.org/19700101000000/http://memento1", "measuretype1", "measure1")

        with self.assertRaises(MeasureModelNoSuchMeasureType):
            mm.get_tokenized("timemap1", "http://examplearchive.org/19700101000000/http://memento1", "measuretype1", "measure1")

        with self.assertRaises(MeasureModelNoSuchMeasureType):
            mm.get_removed_boilerplate("timemap1", "http://examplearchive.org/19700101000000/http://memento1", "measuretype1", "measure1")

        mm.scoremodel["timemap1"]["http://examplearchive.org/19700101000000/http://memento1"]["measuretype1"] = {}

        with self.assertRaises(MeasureModelNoSuchMeasure):
            mm.get_score("timemap1", "http://examplearchive.org/19700101000000/http://memento1", "measuretype1", "measure1")

        with self.assertRaises(MeasureModelNoSuchMeasure):
            mm.get_stemmed("timemap1", "http://examplearchive.org/19700101000000/http://memento1", "measuretype1", "measure1")

        with self.assertRaises(MeasureModelNoSuchMeasure):
            mm.get_tokenized("timemap1", "http://examplearchive.org/19700101000000/http://memento1", "measuretype1", "measure1")

        with self.assertRaises(MeasureModelNoSuchMeasure):
            mm.get_removed_boilerplate("timemap1", "http://examplearchive.org/19700101000000/http://memento1", "measuretype1", "measure1")