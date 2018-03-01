# -*- coding: utf-8 -*-

"""
offtopic.metadata_calculations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This contains functions for producing calculations on mementos outside of the
timemap_measures model.
"""

import logging

from simhash import Simhash

logger = logging.getLogger(__name__)

def save_Simhashes(collectionmodel, measuremodel):
    """Iterates through all TimeMaps and mementos in `collectionmodel` and 
    computes the Simhash on their raw content, storing the results in
    `measuremodel`.
    """
    
    urits = collectionmodel.getTimeMapURIList()
    urittotal = len(urits)
    uritcount = 1

    for urit in urits:

        logger.info("calculating Simhash for mementos in TimeMap {} of {}".format(
            uritcount, urittotal
        ))

        timemap = collectionmodel.getTimeMap(urit)

        memento_list = timemap["mementos"]["list"]

        if len(memento_list) > 0:

            for memento in memento_list:

                urim = memento["uri"]

                if collectionmodel.getMementoErrorInformation(urim):
                    shash = "No Simhash due to error"

                else:
                    shash = Simhash( 
                        str(collectionmodel.getMementoContent(urim))
                        ).value

                measuremodel.set_simhash(urit, urim, shash)

        uritcount += 1

    return measuremodel


def save_raw_content_lengths(collectionmodel, measuremodel):
    """Iterates through all TimeMaps and mementos in `collectionmodel` and 
    computes the content length, storing the results in
    `measuremodel`.
    """

    urits = collectionmodel.getTimeMapURIList()
    urittotal = len(urits)
    uritcount = 1

    for urit in urits:

        logger.info("calculating content lengths on mementos in TimeMap {} of {}".format(
            uritcount, urittotal
        ))

        timemap = collectionmodel.getTimeMap(urit)

        memento_list = timemap["mementos"]["list"]

        if len(memento_list) > 0:

            for memento in memento_list:

                urim = memento["uri"]

                if collectionmodel.getMementoErrorInformation(urim):
                    length = "No length due to error"

                else:
                    length = len(collectionmodel.getMementoContent(urim))

                measuremodel.set_content_length(urit, urim, length)

        uritcount += 1 

    return measuremodel