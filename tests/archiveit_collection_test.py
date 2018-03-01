# -*- coding: utf-8 -*-

import unittest
import logging
import logging.config
import os
import shutil
import zipfile

from datetime import datetime

from otmt import ArchiveItCollection

class TestArchiveItCollection(unittest.TestCase):

    def test_nonexistent_collection(self):

        working_directory = "/tmp/archiveit_collection_test/testdata/archiveit_collection"

        if not os.path.exists(working_directory):
            os.makedirs(working_directory)

        testdatafile="{}/testdata/ac2.zip".format(
            os.path.dirname(os.path.realpath(__file__))
        )

        zipref = zipfile.ZipFile(testdatafile, 'r')
        zipref.extractall(working_directory)
        zipref.close()

        logger = logging.getLogger(__name__) 

        aic = ArchiveItCollection(2, working_directory=working_directory, use_cached=True)

        metadata = aic.return_collection_metadata_dict()

        self.assertFalse(metadata["exists"])
        self.assertEqual(metadata["id"], '2')

        logger.debug("testing for existence of working directory {}".format(
            working_directory))

        self.assertTrue(os.path.exists(working_directory))

        aic = ArchiveItCollection("2", working_directory=working_directory, use_cached=True)

        metadata = aic.return_collection_metadata_dict()

        self.assertFalse(metadata["exists"])
        self.assertEqual(metadata["id"], '2')

        self.assertFalse(aic.does_exist())

        shutil.rmtree(working_directory)

    def test_private_collection_12(self):

        working_directory = "/tmp/archiveit_collection_test/testdata/archiveit_collection"

        if not os.path.exists(working_directory):
            os.makedirs(working_directory)

        testdatafile="{}/testdata/ac12.zip".format(
            os.path.dirname(os.path.realpath(__file__))
        )

        zipref = zipfile.ZipFile(testdatafile, 'r')
        zipref.extractall(working_directory)
        zipref.close()

        aic = ArchiveItCollection(12, working_directory=working_directory, use_cached=True)

        metadata = aic.return_collection_metadata_dict()
        
        self.assertEqual(metadata["name"], "state minnesota sites")
        self.assertEqual(metadata["uri"], "https://archive-it.org/collections/12")
        self.assertEqual(metadata["collected_by"], "Demo Account #1")
        self.assertEqual(metadata["collected_by_uri"], "https://archive-it.org/organizations/3")
        self.assertEqual(metadata["description"], "No description.")

        self.assertEqual(metadata["subject"],
            [
                "historical"
            ]
        )

        self.assertEqual(metadata["archived_since"], "Sep, 2005")

        metadata_fields = aic.list_optional_metadata_fields()

        self.assertTrue("collector" in metadata_fields)

        self.assertEqual(aic.get_optional_metadata("collector"), [ "Demo Account #1" ])

        self.assertTrue(aic.is_private())
        self.assertTrue(aic.does_exist())

        seed_metadata = aic.return_seed_metadata_dict()

        self.assertEqual(seed_metadata["seed_metadata"], {})

        shutil.rmtree(working_directory)

    def test_public_collection_6820(self):

        working_directory = "/tmp/archiveit_collection_test/testdata/archiveit_collection"

        if not os.path.exists(working_directory):
            os.makedirs(working_directory)

        testdatafile="{}/testdata/ac6820.zip".format(
            os.path.dirname(os.path.realpath(__file__))
        )

        zipref = zipfile.ZipFile(testdatafile, 'r')
        zipref.extractall(working_directory)
        zipref.close()

        aic = ArchiveItCollection(6820, working_directory=working_directory, use_cached=True)

        metadata = aic.return_collection_metadata_dict()

        self.assertTrue(metadata["exists"])
        self.assertEqual(metadata["id"], '6820')

        self.assertEqual(metadata["name"], "Congressional Budget Office")
        self.assertEqual(metadata["uri"], "https://archive-it.org/collections/6820")
        self.assertEqual(metadata["collected_by"], "Federal Depository Library Program Web Archive")
        self.assertEqual(metadata["collected_by_uri"], "https://archive-it.org/organizations/593")
        self.assertEqual(metadata["description"],
            """Since 1975, CBO has produced independent analyses of budgetary and economic issues to support the Congressional budget process. Each year, the agency’s economists and budget analysts produce dozens of reports and hundreds of cost estimates for proposed legislation. CBO is strictly nonpartisan; conducts objective, impartial analysis; and hires its employees solely on the basis of professional competence without regard to political affiliation."""
            )

        self.assertEqual(metadata["subject"],
            [
                "Government - US Federal",
                "American History & Political Science",
                "Economics & Finance"
            ]
        )
        self.assertEqual(metadata["archived_since"], "Jan, 2016")

        metadata_fields = aic.list_optional_metadata_fields()

        self.assertTrue("language" in metadata_fields)
        self.assertTrue("collector" in metadata_fields)

        self.assertEqual(aic.get_optional_metadata("language"), [ "English" ])
        self.assertEqual(aic.get_optional_metadata("collector"), [ "U.S. Government Publishing Office" ])

        self.assertFalse(aic.is_private())
        self.assertTrue(aic.does_exist())

        shutil.rmtree(working_directory)

    def test_public_collection_7000(self):

        working_directory = "/tmp/archiveit_collection_test/testdata/archiveit_collection"

        if not os.path.exists(working_directory):
            os.makedirs(working_directory)

        testdatafile="{}/testdata/ac7000.zip".format(
            os.path.dirname(os.path.realpath(__file__))
        )

        zipref = zipfile.ZipFile(testdatafile, 'r')
        zipref.extractall(working_directory)
        zipref.close()

        aic = ArchiveItCollection(7000, working_directory=working_directory, use_cached=True)

        metadata = aic.return_collection_metadata_dict()

        self.assertTrue(metadata["exists"])
        self.assertEqual(metadata["id"], '7000')

        self.assertEqual(metadata["name"], "Sun Microsystems documents")
        self.assertEqual(metadata["uri"], "https://archive-it.org/collections/7000")
        self.assertEqual(metadata["collected_by"], "John Gilmore")
        self.assertEqual(metadata["collected_by_uri"], "https://archive-it.org/organizations/151")
        self.assertEqual(metadata["archived_since"], "Feb, 2016")
        self.assertEqual(metadata["description"],
            """A collection of technical documents that relate to the products of Sun Microsystems, Inc, a large computer company that existed between 1982 and 2010"""
            )

        self.assertEqual(metadata["subject"],
            [
                "Computers & Technology"
            ]
        )

        metadata_fields = aic.list_optional_metadata_fields()

        self.assertTrue("creator" in metadata_fields)
        self.assertTrue("source" in metadata_fields)
        self.assertTrue("coverage" in metadata_fields)
        self.assertTrue("type" in metadata_fields)
        self.assertTrue("date" in metadata_fields)
        self.assertTrue("language" in metadata_fields)
        self.assertTrue("contributor" in metadata_fields)
        self.assertTrue("collector" in metadata_fields)

        self.assertEqual(aic.get_optional_metadata("creator"), [ 
            "Sun Microsystems, Inc.",
            "http://sun.com",
            "John Gilmore"
        ])
        self.assertEqual(aic.get_optional_metadata("source"), [ "ftp://ftp.lvnet.lv/pub" ])
        self.assertEqual(aic.get_optional_metadata("coverage"), [ "between 1982 and 2010" ])

        self.assertEqual(aic.get_optional_metadata("type"), [ 
            "email messages",
            "PDF files",
            "white papers"
            ])

        self.assertEqual(aic.get_optional_metadata("date"), [ "2016" ])
        self.assertEqual(aic.get_optional_metadata("language"), [ "English" ])
        self.assertEqual(aic.get_optional_metadata("contributor"), [ "John Gilmore" ])
        self.assertEqual(aic.get_optional_metadata("collector"), [ "John Gilmore" ])

        self.assertEqual(metadata["optional"]["creator"], [ 
            "Sun Microsystems, Inc.",
            "http://sun.com",
            "John Gilmore"
        ])
        self.assertEqual(metadata["optional"]["source"], [ "ftp://ftp.lvnet.lv/pub" ])
        self.assertEqual(metadata["optional"]["coverage"], [ "between 1982 and 2010" ])

        self.assertEqual(metadata["optional"]["type"], [ 
            "email messages",
            "PDF files",
            "white papers"
            ])

        self.assertEqual(metadata["optional"]["date"], [ "2016" ])
        self.assertEqual(metadata["optional"]["language"], [ "English" ])
        self.assertEqual(metadata["optional"]["contributor"], [ "John Gilmore" ])
        self.assertEqual(metadata["optional"]["collector"], [ "John Gilmore" ])

        self.assertFalse(aic.is_private())
        self.assertTrue(aic.does_exist())

        shutil.rmtree(working_directory)

    def test_public_collection_5728(self):

        working_directory = "/tmp/archiveit_collection_test/testdata/archiveit_collection"

        if not os.path.exists(working_directory):
            os.makedirs(working_directory)

        testdatafile="{}/testdata/ac5728.zip".format(
            os.path.dirname(os.path.realpath(__file__))
        )

        zipref = zipfile.ZipFile(testdatafile, 'r')
        zipref.extractall(working_directory)
        zipref.close()

        aic = ArchiveItCollection(5728, working_directory=working_directory, use_cached=True)

        metadata = aic.return_collection_metadata_dict()

        self.assertTrue(metadata["exists"])
        self.assertEqual(metadata["id"], '5728')

        self.assertEqual(metadata["name"], "Social Media")
        self.assertEqual(metadata["uri"], "https://archive-it.org/collections/5728")
        self.assertEqual(metadata["collected_by"], "Willamette University")
        self.assertEqual(metadata["collected_by_uri"], "https://archive-it.org/organizations/958")
        self.assertEqual(metadata["archived_since"], "Apr, 2015")
        self.assertEqual(metadata["description"],
            "Social media content created by Willamette University."
            )

        self.assertEqual(metadata["subject"],
            [
                "Universities & Libraries",
                "Blogs & Social Media"
            ]
        )

        metadata_fields = aic.list_optional_metadata_fields()

        self.assertEqual(len(metadata_fields), 0)

        seed_metadata = aic.return_seed_metadata_dict() 

        self.assertEqual(seed_metadata["id"], "5728")

        # sample seeds, because I'm too lazy to put in data for all 101
        self.assertEqual(
            seed_metadata["seed_metadata"]["seeds"]["http://blog.willamette.edu/mba/"],
            {
                "collection_web_pages": [ {
                    "title": "Willamette MBA Blog",
                    "description": [
                    "Blog for the Willamette University Atkinson Graduate School of Management" 
                    ]
                } ],
                "seed_report": { 
                    "group": "",
                    "status": "False",
                    "frequency": "NONE",
                    "type": "normal",
                    "access": "True"
                }
            }
            )

        self.assertEqual(
            aic.get_seed_metadata("http://blog.willamette.edu/mba/"),
            seed_metadata["seed_metadata"]["seeds"]["http://blog.willamette.edu/mba/"]
            )

        self.assertEqual(
            seed_metadata["seed_metadata"]["seeds"]['http://blog.willamette.edu/worldnews/'],
            { 
                'collection_web_pages': [ {
                    'title': 'Willamette World News',
                    'description': ['Blog for International Education at Willamette University.'],
                    'videos': ['93 Videos Captured']
                    } ],
                'seed_report': {
                    'group': '',
                    'status': 'True',
                    'frequency': 'BIMONTHLY',
                    'type': 'normal',
                    'access': 'True'
                }
            }
        )

        self.assertEqual(
            aic.get_seed_metadata('http://blog.willamette.edu/worldnews/'),
            seed_metadata["seed_metadata"]["seeds"]['http://blog.willamette.edu/worldnews/']
        )

        self.assertEqual(
            seed_metadata["seed_metadata"]["seeds"]["http://www.facebook.com/WillametteAlumni/"],
            {
                'collection_web_pages': [ {
                    'title': 'Alumni Association Facebook',
                    'description': ["Facebook page for Willamette University's Alumni Association."],
                    'videos': ['859 Videos Captured'],
                    'group': ['Facebook'] } ],
                'seed_report': {
                    'group': 'Facebook',
                    'status': 'True',
                    'frequency': 'QUARTERLY',
                    'type': 'normal',
                    'access': 'True'}
             }
        )

        self.assertEqual(
            aic.get_seed_metadata("http://www.facebook.com/WillametteAlumni/"),
            seed_metadata["seed_metadata"]["seeds"]["http://www.facebook.com/WillametteAlumni/"]
        )

        self.assertFalse(aic.is_private())
        self.assertTrue(aic.does_exist())

        shutil.rmtree(working_directory)

# if __name__ == '__main__':

#     logging.config.fileConfig('logging.ini')
#     logger = logging.getLogger(__name__) 

#     logger.info("beginning unit tests")

#     unittest.main()
