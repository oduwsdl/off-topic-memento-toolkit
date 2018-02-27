import logging

from simhash import Simhash

logger = logging.getLogger(__name__)

def save_Simhashes(collectionmodel, measuremodel):
    
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