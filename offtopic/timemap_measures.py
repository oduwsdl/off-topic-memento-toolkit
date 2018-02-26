import distance
import string
import logging

from nltk import word_tokenize
from nltk.corpus import stopwords
from nltk.stem.porter import PorterStemmer

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from simhash import Simhash

from .collectionmodel import CollectionModelMementoErrorException, \
    CollectionModelBoilerPlateRemovalFailureException

logger = logging.getLogger(__name__)

stemmer = PorterStemmer()

def stem_tokens(tokens):

    stemmed = []

    for item in tokens:
        stemmed.append( stemmer.stem(item) )

    return stemmed

def full_tokenize(text, stemming=True):

    stopset = stopwords.words("english") + list(string.punctuation)

    if type(text) == bytes:
        tokens = word_tokenize(text.decode("utf8"))
    else:
        tokens = word_tokenize(text)

    if stemming:
        stems = stem_tokens(tokens)

    return [ i for i in stems if i not in stopset ]

def get_memento_data_for_measure(urim, collection_model,
    tokenize=True, stemming=True, remove_boilerplate=True):

    data = None

    if remove_boilerplate:
        data = collection_model.getMementoContentWithoutBoilerplate(urim)
    else:
        data = collection_model.getMementoContent(urim)

    if tokenize:
        data = full_tokenize(data, stemming=stemming)

    return data

def apply_measurement_error_msg_to_all_mementos(urit, memento_list, 
    measuremodel, measurename, errormsg):

    for memento in memento_list:

        # we cannot compute any meeaningful measurements, so store
        # as errors for later output
        urim = memento["uri"]
        measuremodel.set_Memento_measurement_error(urit, urim, 
            "timemap measures", measurename, errormsg)   

    return measuremodel

def compute_score_across_TimeMap(collectionmodel, measuremodel,
    measurename, scoredistance_function=None, 
    tokenize=True, stemming=True,
    remove_boilerplate=True):

    # TODO: raise an exception if the scoredistance_function is not set

    logger.info("Computing {} score across TimeMap, "
        "beginning TimeMap iteration...".format(measurename))

    urits = collectionmodel.getTimeMapURIList()
    urittotal = len(urits)
    uritcounter = 1

    for urit in urits:

        logger.info("Processing TimeMap {} of {}".format(uritcounter, urittotal))
        logger.debug("Processing mementos from TimeMap at {}".format(urit))

        timemap = collectionmodel.getTimeMap(urit)

        memento_list = timemap["mementos"]["list"]

        # some TimeMaps have no mementos
        # e.g., http://wayback.archive-it.org/3936/timemap/link/http://www.peacecorps.gov/shutdown/?from=hpb
        if len(memento_list) > 0:

            first_urim = timemap["mementos"]["first"]["uri"]

            logger.debug("Accessing content of first URI-M {} for calculations".format(first_urim))

            try:
                first_data = get_memento_data_for_measure(
                    first_urim, collectionmodel, tokenize=tokenize, stemming=stemming, 
                    remove_boilerplate=remove_boilerplate)

            except CollectionModelBoilerPlateRemovalFailureException as e:
                errormsg = "Boilerplate removal error with first memento in TimeMap, " \
                    "cannot effectively compare memento content"

                apply_measurement_error_msg_to_all_mementos(urit, memento_list,
                    measuremodel, measurename, errormsg)
                continue
            

            if len(first_data) == 0:

                errormsg = "After processing content, the first memento in TimeMap is now empty, cannot effectively compare memento content"
                logger.warning(errormsg)

                apply_measurement_error_msg_to_all_mementos(urit, memento_list,
                    measuremodel, measurename, errormsg)

                # move on to the next URI-T
                uritcounter += 1
                continue

            mementototal = len(memento_list)
            logger.info("There are {} mementos in this TimeMap".format(mementototal))

            mementocounter = 1

            for memento in memento_list:

                logger.debug("Processing Memento {} of {}".format(mementocounter, mementototal))

                urim = memento["uri"]

                logger.debug("Accessing content of URI-M {} for calculations".format(urim))

                try:

                    try:
                        memento_data = get_memento_data_for_measure(
                            urim, collectionmodel, tokenize=tokenize, 
                            stemming=stemming, 
                            remove_boilerplate=remove_boilerplate)

                        score = scoredistance_function(first_data, memento_data)
                        measuremodel.set_score(urit, urim, "timemap measures", measurename, score)
                        measuremodel.set_tokenized(urit, urim, "timemap measures", measurename, tokenize)
                        measuremodel.set_stemmed(urit, urim, "timemap measures", measurename, stemming)
                        measuremodel.set_removed_boilerplate(
                            urit, urim, "timemap measures", measurename, remove_boilerplate
                        )

                    except CollectionModelBoilerPlateRemovalFailureException as e:
                        errormsg = "Boilerplate could not be removed from " \
                            "memento at URI-M {}; details: {}".format(urim, repr(e))
                        logger.warning(errormsg)

                        measuremodel.set_Memento_measurement_error(
                            urit, urim, "timemap measures", measurename, repr(e)
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
                
                mementocounter += 1

            uritcounter += 1

    return measuremodel


def simhash_scoredistance(first_data, memento_data):

    if type(first_data) == type(memento_data):
        if type(first_data) == bytes:
            first_data = str(first_data)
            memento_data = str(memento_data)

    score = Simhash(first_data).distance(Simhash(memento_data))

    return score

def compute_rawsimhash_across_TimeMap(collectionmodel, measuremodel, tokenize=False, stemming=False):

    measuremodel = compute_score_across_TimeMap(collectionmodel, measuremodel, "raw_simhash", 
        simhash_scoredistance, tokenize=False, stemming=False,
        remove_boilerplate=False
    )

    return measuremodel

def compute_tfsimhash_across_TimeMap(collectionmodel, measuremodel, tokenize=True, stemming=True):

    measuremodel = compute_score_across_TimeMap(collectionmodel, measuremodel, "tf_simhash", 
        simhash_scoredistance, tokenize=True, stemming=True,
        remove_boilerplate=True
    )

    return measuremodel

def bytecount_scoredistance(first_data, memento_data):

    score = None

    if type(first_data) == type(memento_data):

        if type(first_data) == list:

            first_data = ''.join(first_data)
            memento_data = ''.join(memento_data)

    first_bytecount = len(first_data)
    memento_bytecount = len(memento_data)

    if memento_bytecount == 0:

        if first_bytecount == 0:
            score = 0

        else:
            score = 1 -  (memento_bytecount / first_bytecount)

    else:
        score = 1 -  (memento_bytecount / first_bytecount)
    
    return score

def compute_bytecount_across_TimeMap(collectionmodel, measuremodel, tokenize=False, stemming=False):

    measuremodel = compute_score_across_TimeMap(collectionmodel, measuremodel, "bytecount", 
        bytecount_scoredistance, tokenize=False, stemming=False,
        remove_boilerplate=False
    )

    return measuremodel

def wordcount_scoredistance(first_data, memento_data):

    score = None

    first_wordcount = len(first_data)
    memento_wordcount = len(memento_data)

    # scoredata["individual score"] = memento_wordcount

    if memento_wordcount == 0:

        if first_wordcount == 0:
            score = 0

        else:
            score = 1 -  (memento_wordcount / first_wordcount)

    else:
        score = 1 -  (memento_wordcount / first_wordcount)

    return score

def compute_wordcount_across_TimeMap(collectionmodel, measuremodel, tokenize=True, stemming=True):
    
    measuremodel = compute_score_across_TimeMap(collectionmodel, measuremodel, "wordcount", 
        wordcount_scoredistance, tokenize=True, stemming=stemming,
        remove_boilerplate=True
    )

    return measuremodel

def compute_scores_on_distance_measure(first_data, memento_data, distance_function):

    score = None

    if len(memento_data) == 0:

        if len(first_data) == 0:
            score = 0

        else:
            score = distance_function(first_data, memento_data)

    else:
        score = distance_function(first_data, memento_data)

    return score


def jaccard_scoredistance(first_data, memento_data):

    score = compute_scores_on_distance_measure(
        first_data, memento_data, distance.jaccard)

    return score

def compute_jaccard_across_TimeMap(collectionmodel, measuremodel, tokenize=True, stemming=True):

    scores = compute_score_across_TimeMap(collectionmodel, measuremodel, "jaccard", 
        jaccard_scoredistance, tokenize=tokenize, stemming=stemming,
        remove_boilerplate=True
    )

    return scores

def sorensen_scoredistance(first_data, memento_data):

    scoredata = {}

    scoredata = compute_scores_on_distance_measure(
        first_data, memento_data, distance.sorensen)

    return scoredata

def compute_sorensen_across_TimeMap(collectionmodel, measuremodel, tokenize=True, stemming=True):
    
    scores = compute_score_across_TimeMap(collectionmodel, measuremodel, "sorensen", 
        sorensen_scoredistance, tokenize=tokenize, stemming=stemming,
        remove_boilerplate=True
    )

    return scores

def levenshtein_scoredistance(first_data, memento_data):

    score = compute_scores_on_distance_measure(
        first_data, memento_data, distance.levenshtein)

    return score

def compute_levenshtein_across_TimeMap(collectionmodel, measuremodel, tokenize=True, stemming=True):
    
    scores = compute_score_across_TimeMap(collectionmodel, measuremodel, "levenshtein", 
        levenshtein_scoredistance, tokenize=tokenize, stemming=stemming,
        remove_boilerplate=True
    )

    return scores

def nlevenshtein_scoredistance(first_data, memento_data):

    score = compute_scores_on_distance_measure(
        first_data, memento_data, distance.nlevenshtein)

    return score

def compute_nlevenshtein_across_TimeMap(collectionmodel, measuremodel, tokenize=True, stemming=True):

    scores = compute_score_across_TimeMap(collectionmodel, measuremodel, "nlevenshtein", 
        nlevenshtein_scoredistance, tokenize=tokenize, stemming=stemming,
        remove_boilerplate=True
    )

    return scores

def calculate_term_frequencies(tokens):

    frequency_dict = {}

    for token in tokens:

        frequency_dict.setdefault(token, 0)
        frequency_dict[token] += 1

    tf = []

    for token, count in frequency_dict.items():
        tf.append( (count, token) )

    return sorted(tf, reverse=True)

def tfintersection_scoredistance(first_data, memento_data):

    score = None

    tf_first = calculate_term_frequencies(first_data)
    tf_memento = calculate_term_frequencies(memento_data)

    first_token_count = 20 if len(tf_first) > 20 else len(tf_first)
    memento_token_count = 20 if len(tf_memento) > 20 else len(tf_memento)

    top_20ish_first_tokens = []
    top_20ish_memento_tokens = []

    logger.debug("size of first memento data: {}".format(first_token_count))
    logger.debug("size of comparison memento data: {}".format(first_token_count))

    for i in range(0, first_token_count):
        top_20ish_first_tokens.append(tf_first[i][1])

    for i in range(0, memento_token_count):
        top_20ish_memento_tokens.append(tf_memento[i][1])

    logger.debug("top 20ish tokens in first memento data: {}".format(top_20ish_first_tokens))
    logger.debug("top 20ish tokens in comparison memento data: {}".format(top_20ish_memento_tokens))

    number_of_intersecting_terms = 0

    for token in top_20ish_first_tokens:
        
        if token in top_20ish_memento_tokens:
            number_of_intersecting_terms += 1

    logger.debug("number of intersecting terms: {}".format(number_of_intersecting_terms))

    score = len(top_20ish_first_tokens) - number_of_intersecting_terms

    return score

def compute_tfintersection_across_TimeMap(collectionmodel, measuremodel, tokenize=None, stemming=True):

    scores = compute_score_across_TimeMap(collectionmodel, measuremodel, "tfintersection",
        tfintersection_scoredistance, tokenize=True, stemming=stemming,
        remove_boilerplate=True
    )

    return scores

def compute_cosine_across_TimeMap(collectionmodel, measuremodel, tokenize=None, stemming=None):
    
    # TODO: alter compute_score_across_TimeMap so that much of this function can be replaced
    measurename = "cosine"

    tokenize = True
    remove_boilerplate = True
    stemming = True

    logger.info("Computing cosine score across TimeMap, beginning TimeMap iteration...")

    urits = collectionmodel.getTimeMapURIList()
    urittotal = len(urits)
    uritcounter = 1

    for urit in urits:

        logger.info("Processing TimeMap {} of {}".format(uritcounter, urittotal))
        logger.debug("Processing mementos from TimeMap at {}".format(urit))

        timemap = collectionmodel.getTimeMap(urit)

        memento_list = timemap["mementos"]["list"]

        # some TimeMaps have no mementos
        # e.g., http://wayback.archive-it.org/3936/timemap/link/http://www.peacecorps.gov/shutdown/?from=hpb
        if len(memento_list) > 0:

            first_urim = timemap["mementos"]["first"]["uri"]

            logger.debug("Accessing content of first URI-M {} for calculations".format(first_urim))

            try:
                first_data = collectionmodel.getMementoContentWithoutBoilerplate(first_urim)

            except CollectionModelBoilerPlateRemovalFailureException as e:
                errormsg = "Boilerplate removal error with first memento in TimeMap, " \
                    "cannot effectively compare memento content"

                apply_measurement_error_msg_to_all_mementos(urit, memento_list,
                    measuremodel, measurename, errormsg)
                continue

            if len(first_data) == 0:

                errormsg = "After processing content, the first memento in TimeMap is now empty, cannot effectively compare memento content"
                logger.warning(errormsg)

                apply_measurement_error_msg_to_all_mementos(urit, memento_list,
                    measuremodel, measurename, errormsg)

                # move on to the next URI-T
                uritcounter += 1
                continue

            mementototal = len(memento_list)
            logger.info("There are {} mementos in this TimeMap".format(mementototal))

            mementocounter = 1

            processed_urims = []
            error_urims = []
            documents = []

            # in case the mementos are not sorted in order of memento datetime
            # we save the first one for comparison
            processed_urims.append(first_urim)
            documents.append(first_data)

            for memento in memento_list:

                logger.debug("Processing Memento {} of {}".format(mementocounter, mementototal))

                urim = memento["uri"]

                logger.debug("Accessing content of URI-M {} for calculations".format(urim))

                try:

                    # in case the mementos are not sorted in order of memento datetime
                    # we ignore the first one for comparison because we already saved it
                    if urim != first_urim:
                        try:
                            memento_data = collectionmodel.getMementoContentWithoutBoilerplate(urim)
                                
                            processed_urims.append(urim)
                            documents.append(memento_data)

                        except CollectionModelBoilerPlateRemovalFailureException as e:
                            errormsg = "Boilerplate could not be removed from " \
                                "memento at URI-M {}; details: {}".format(urim, repr(e))
                            logger.warning(errormsg)

                            measuremodel.set_Memento_measurement_error(
                                urit, urim, "timemap measures", measurename, repr(e)
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
                    error_urims.append(urim)
                
                mementocounter += 1

            # our full_tokenize function handles stop words
            tfidf_vectorizer = TfidfVectorizer(tokenizer=full_tokenize, stop_words=None)
            tfidf_matrix = tfidf_vectorizer.fit_transform(documents)
            cscores = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix)

            for i in range(0, len(cscores[0])):
                urim = processed_urims[i]
                logger.debug("saving cosine scores for URI-M {}".format(urim))

                measuremodel.set_score(urit, urim, "timemap measures", measurename, cscores[0][i])
                measuremodel.set_tokenized(urit, urim, "timemap measures", measurename, tokenize)
                measuremodel.set_stemmed(urit, urim, "timemap measures", measurename, stemming)
                measuremodel.set_removed_boilerplate(
                    urit, urim, "timemap measures", measurename, remove_boilerplate
                )                        

            uritcounter += 1

    return measuremodel

supported_timemap_measures = {
    "cosine": {
        "name": "Cosine Similarity",
        "function": compute_cosine_across_TimeMap,
        "comparison direction": "<",
        "default threshold": 0.15
    },
    "bytecount": {
        "name": "Byte Count",
        "function": compute_bytecount_across_TimeMap,
        "comparison direction": "<",
        "default threshold": -0.65
    },
    "wordcount": {
        "name": "Word Count",
        "function": compute_wordcount_across_TimeMap,
        "comparison direction": "<",
        "default threshold": -0.85
    },
    "tfintersection": {
        "name": "TF-Intersection",
        "function": compute_tfintersection_across_TimeMap,
        "comparison direction": "!=",
        "default threshold": 0.0
    },
    "jaccard": {
        "name": "Jaccard Distance",
        "function": compute_jaccard_across_TimeMap,
        "comparison direction": ">",
        "default threshold": 0.05
    },
    "sorensen": {
        "name": "Sørensen-Dice Distance",
        "function": compute_sorensen_across_TimeMap,
        "comparison direction": ">",
        "default threshold": 0.05
    },
    "raw_simhash": {
        "name": "Simhash on raw memento content",
        "function": compute_rawsimhash_across_TimeMap,
        "comparison direction": ">",
        "default threshold": 0
    },
    "tf_simhash": {
        "name": "Simhash on term frequencies in memento",
        "function": compute_tfsimhash_across_TimeMap,
        "comparison direction": ">",
        "default threshold": 0
    }
    # Note: these took way too long to execute
    # ,
    # "levenshtein": {
    #     "name": "Levenshtein Distance",
    #     "function": compute_levenshtein_across_TimeMap,
    #     "comparison direction": ">",
    #     "default threshold": 0.05
    # },
    # "nlevenshtein": {
    #     "name": "Normalized Levenshtein Distance",
    #     "function": compute_nlevenshtein_across_TimeMap,
    #     "comparison direction": ">",
    #     "default threshold": 0.05
    # }
}