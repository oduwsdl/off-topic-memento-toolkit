import logging
import distance

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .collectionmodel import CollectionModelBoilerPlateRemovalFailureException, \
    CollectionModelMementoErrorException

from .timemap_measures import stem_tokens, full_tokenize, get_memento_data_for_measure

logger = logging.getLogger(__name__)

# def compute_cosine_across_collection(collectionmodel, measuremodel):

#     measuretype = "collection measures"
#     measurename = "cosine"

#     logger.info("Computing {} across the whole collection".format(measurename))

#     urits = collectionmodel.getTimeMapURIList()
#     urittotal = len(urits)
#     uritcounter = 1

#     documents = []
#     processed_urims = []

#     tokenize = True
#     remove_boilerplate = True
#     stemming = True

#     for urit in urits:

#         logger.info("Processing TimeMap {} of {}".format(uritcounter, urittotal))
#         logger.debug("Processing mementos from TimeMap at {}".format(urit))

#         timemap = collectionmodel.getTimeMap(urit)

#         memento_list = timemap["mementos"]["list"]

#         # some TimeMaps have no mementos
#         # e.g., http://wayback.archive-it.org/3936/timemap/link/http://www.peacecorps.gov/shutdown/?from=hpb
#         if len(memento_list) > 0:

#             for memento in memento_list:

#                 urim = memento["uri"]

#                 try:
#                     memento_data = collectionmodel.getMementoContentWithoutBoilerplate(urim)

#                     processed_urims.append(urim)
#                     documents.append(memento_data)

#                 except CollectionModelBoilerPlateRemovalFailureException as e:
#                     errormsg = "Boilerplate could not be removed from " \
#                         "memento at URI-M {}; details: {}".format(urim, repr(e))
#                     logger.warning(errormsg)

#                     measuremodel.set_Memento_measurement_error(
#                         urit, urim, measuretype, measurename, repr(e)
#                     )

#                 except CollectionModelMementoErrorException:
#                     errormsg = "Errors were recorded while attempting to " \
#                         "access URI-M {}, skipping {} calcualtions for this " \
#                         "URI-M".format(urim, measurename)
#                     logger.warning(errormsg)

#                     errorinfo = collectionmodel.getMementoErrorInformation(urim)

#                     measuremodel.set_Memento_access_error(
#                         urit, urim, errorinfo
#                     )

#         uritcounter += 1

#     tfidf_vectorizer = TfidfVectorizer(tokenizer=full_tokenize, stop_words=None)
#     tfidf_matrix = tfidf_vectorizer.fit_transform(documents)
#     cscores = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix)

#     for i in range(0, len(cscores[0])):
#         urim = processed_urims[i]
#         logger.debug("saving cosine scores for URI-M {}".format(urim))

#         measuremodel.set_score(urit, urim, "timemap measures", measurename, cscores[0][i])
#         measuremodel.set_tokenized(urit, urim, "timemap measures", measurename, tokenize)
#         measuremodel.set_stemmed(urit, urim, "timemap measures", measurename, stemming)
#         measuremodel.set_removed_boilerplate(
#             urit, urim, "timemap measures", measurename, remove_boilerplate
#         )              

#     return measuremodel


def compute_distance_score_across_collection(collectionmodel, measuremodel, measurename, distance_function):

    measuretype = "collection measures"

    logger.info("Computing {} across the whole collection".format(measurename))

    urits = collectionmodel.getTimeMapURIList()
    urittotal = len(urits)
    uritcounter = 1

    tokens = []
    processed_urims = []

    tokenize = True
    remove_boilerplate = True
    stemming = True

    for urit in urits:

        logger.info("Processing TimeMap {} of {}".format(uritcounter, urittotal))
        logger.debug("Processing mementos from TimeMap at {}".format(urit))

        timemap = collectionmodel.getTimeMap(urit)

        memento_list = timemap["mementos"]["list"]

        # some TimeMaps have no mementos
        # e.g., http://wayback.archive-it.org/3936/timemap/link/http://www.peacecorps.gov/shutdown/?from=hpb
        if len(memento_list) > 0:

            for memento in memento_list:

                urim = memento["uri"]

                try:
                    memento_data = get_memento_data_for_measure(
                        urim, collectionmodel, tokenize=tokenize, 
                        stemming=stemming, 
                        remove_boilerplate=remove_boilerplate)

                    processed_urims.append(urim)

                    for token in memento_data:
                        tokens.append(token)

                except CollectionModelBoilerPlateRemovalFailureException as e:
                    errormsg = "Boilerplate could not be removed from " \
                        "memento at URI-M {}; details: {}".format(urim, repr(e))
                    logger.warning(errormsg)

                    measuremodel.set_Memento_measurement_error(
                        urit, urim, measuretype, measurename, repr(e)
                    )

                except CollectionModelMementoErrorException:
                    errormsg = "Errors were recorded while attempting to " \
                        "access URI-M {}, skipping {} calcualtions for this " \
                        "URI-M".format(urim, measurename)
                    logger.warning(errormsg)

                    errorinfo = collectionmodel.getMementoErrorInformation(urim)

                    measuremodel.set_Memento_access_error(
                        urit, urim, errorinfo
                    )

        uritcounter += 1

    for urim in processed_urims:
        memento_data = get_memento_data_for_measure(
            urim, collectionmodel, tokenize=tokenize, 
            stemming=stemming, 
            remove_boilerplate=remove_boilerplate)

        score = distance_function(tokens, memento_data)

        measuremodel.set_score(urit, urim, measuretype, measurename, score)
        measuremodel.set_tokenized(urit, urim, measuretype, measurename, tokenize)
        measuremodel.set_stemmed(urit, urim, measuretype, measurename, stemming)
        measuremodel.set_removed_boilerplate(
            urit, urim, measuretype, measurename, remove_boilerplate
        )

    return measuremodel

def compute_jaccard_accross_collection(collectionmodel, measuremodel):

    score = compute_distance_score_across_collection(collectionmodel, 
        measuremodel, "jaccard", distance.jaccard)

    return score

def compute_sorensen_accross_collection(collectionmodel, measuremodel):

    score = compute_distance_score_across_collection(collectionmodel, 
        measuremodel, "sorensen", distance.sorensen)

    return score

supported_collection_measures = {
    # "cosine": {
    #     "name": "Cosine Similarity",
    #     "function": compute_cosine_across_collection,
    #     "comparison direction": "<",
    #     "default threshold": 0.12
    # },
    "jaccard": {
        "name": "Jaccard Distance",
        "function": compute_jaccard_accross_collection,
        "comparison direction": ">",
        "default threshold": 0.96
    },
    "sorensen": {
        "name": "Sørensen-Dice Distance",
        "function": compute_sorensen_accross_collection,
        "comparison direction": ">",
        "default threshold": 0.96
    }
}