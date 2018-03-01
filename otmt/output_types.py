# -*- coding: utf-8 -*-

"""
otmt.timemap_measures
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module supplies the functions for exporting to different output types.
"""

import json
import csv
import logging

def output_json(outputfile, measuremodel, collectionmodel):
    measuremodel.save_as_JSON(outputfile)

def output_datafile(outputfile, measuremodel, collectionmodel):
    measuremodel.save_as_goldstandard(outputfile)

def output_csv(outputfile, measuremodel, collectionmodel):
    measuremodel.save_as_CSV(outputfile)

supported_output_types = {
    'json': output_json,
    'golddatafile': output_datafile,
    'csv': output_csv
}