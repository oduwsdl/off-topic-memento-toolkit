import distance
import string
import logging

from nltk import word_tokenize
from nltk.corpus import stopwords
from nltk.stem.porter import PorterStemmer

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .collectionmodel import CollectionModelMementoErrorException

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

def compute_score_across_TimeMap(collectionmodel, measurename,
    scoredistance_function=None, 
    scores=None, tokenize=True, stemming=True,
    remove_boilerplate=True):

    # TODO: raise an exception if the scoredistance_function is not set

    if scores == None:
        scores = {}
        scores["timemaps"] = {}

    logger.info("Computing {} score across TimeMap, "
        "beginning TimeMap iteration...".format(measurename))

    urits = collectionmodel.getTimeMapURIList()
    urittotal = len(urits)
    uritcounter = 1

    for urit in urits:

        logger.info("Processing TimeMap {} of {}".format(uritcounter, urittotal))
        logger.debug("Processing mementos from TimeMap at {}".format(urit))

        timemap = collectionmodel.getTimeMap(urit)

        scores["timemaps"].setdefault(urit, {})

        memento_list = timemap["mementos"]["list"]

        # some TimeMaps have no mementos
        # e.g., http://wayback.archive-it.org/3936/timemap/link/http://www.peacecorps.gov/shutdown/?from=hpb
        if len(memento_list) > 0:

            first_urim = timemap["mementos"]["first"]["uri"]

            logger.debug("Accessing content of first URI-M {} for calculations".format(first_urim))

            first_data = get_memento_data_for_measure(
                first_urim, collectionmodel, tokenize=tokenize, stemming=stemming, 
                remove_boilerplate=remove_boilerplate)

            # mementos = timemap["mementos"]["list"]

            mementototal = len(memento_list)
            logger.info("There are {} mementos in this TimeMap".format(mementototal))

            mementocounter = 1

            for memento in memento_list:

                logger.info("Processing Memento {} of {}".format(mementocounter, mementototal))

                urim = memento["uri"]

                logger.debug("Accessing content of URI-M {} for calculations".format(urim))

                scores["timemaps"][urit].setdefault(urim, {})
                scores["timemaps"][urit][urim].setdefault("timemap measures", {})

                try:
                    memento_data = get_memento_data_for_measure(
                        urim, collectionmodel, tokenize=tokenize, 
                        stemming=stemming, 
                        remove_boilerplate=remove_boilerplate)
                        
                    scores["timemaps"][urit][urim]["timemap measures"][measurename] = \
                        scoredistance_function(first_data, memento_data)
                    scores["timemaps"][urit][urim]["timemap measures"][measurename]["tokenized"] = tokenize
                    scores["timemaps"][urit][urim]["timemap measures"][measurename]["stemmed"] = stemming
                    scores["timemaps"][urit][urim]["timemap measures"][measurename]["boilerplate removal"] = remove_boilerplate

                except CollectionModelMementoErrorException:
                    errormsg = "Errors were recorded while attempting to " \
                        "access URI-M {}, skipping {} calcualtions for this " \
                        "URI-M".format(urim, measurename)
                    logger.warning(errormsg)
                    scores["timemaps"][urit][urim]["access error"] = errormsg
                
                mementocounter += 1

            uritcounter += 1

    return scores

def bytecount_scoredistance(first_data, memento_data):

    scoredata = {}

    if type(first_data) == type(memento_data):

        if type(first_data) == list:

            first_data = ''.join(first_data)
            memento_data = ''.join(memento_data)

    first_bytecount = len(first_data)
    memento_bytecount = len(memento_data)

    # TODO: score cache for individual scores
    scoredata["individual score"] = memento_bytecount
    
    # TODO: score cache for scores of both items
    if memento_bytecount == 0:

        if first_bytecount == 0:
            scoredata["comparison score"] = 0

        else:
            scoredata["comparison score"] = 1 -  (memento_bytecount / first_bytecount)

    else:
        scoredata["comparison score"] = 1 -  (memento_bytecount / first_bytecount)
    
    return scoredata

def compute_bytecount_across_TimeMap(collectionmodel, scores=None, tokenize=False, stemming=False):

    scores = compute_score_across_TimeMap(collectionmodel, "bytecount", 
        bytecount_scoredistance, scores=scores, tokenize=False, stemming=False,
        remove_boilerplate=False
    )

    return scores

def wordcount_scoredistance(first_data, memento_data):

    scoredata = {}

    first_wordcount = len(first_data)
    memento_wordcount = len(memento_data)

    scoredata["individual score"] = memento_wordcount

    if memento_wordcount == 0:

        if first_wordcount == 0:
            scoredata["comparison score"] = 0

        else:
            scoredata["comparison score"] = 1 -  (memento_wordcount / first_wordcount)

    else:
        scoredata["comparison score"] = 1 -  (memento_wordcount / first_wordcount)

    return scoredata

def compute_wordcount_across_TimeMap(collectionmodel, scores=None, tokenize=True, stemming=True):
    
    scores = compute_score_across_TimeMap(collectionmodel, "wordcount", 
        wordcount_scoredistance, scores=scores, tokenize=True, stemming=stemming,
        remove_boilerplate=True
    )

    return scores

def compute_scores_on_distance_measure(first_data, memento_data, distance_function):

    scoredata = {}

    if len(memento_data) == 0:

        if len(first_data) == 0:
            scoredata["comparison score"] = 0

        else:
            scoredata["comparison score"] = distance_function(first_data, memento_data)

    else:
        scoredata["comparison score"] = distance_function(first_data, memento_data)

    return scoredata


def jaccard_scoredistance(first_data, memento_data):

    scoredata = {}

    scoredata = compute_scores_on_distance_measure(
        first_data, memento_data, distance.jaccard)

    return scoredata

def compute_jaccard_across_TimeMap(collectionmodel, scores=None, tokenize=True, stemming=True):

    scores = compute_score_across_TimeMap(collectionmodel, "jaccard", 
        jaccard_scoredistance, scores=scores, tokenize=tokenize, stemming=stemming,
        remove_boilerplate=True
    )

    return scores

def sorensen_scoredistance(first_data, memento_data):

    scoredata = {}

    scoredata = compute_scores_on_distance_measure(
        first_data, memento_data, distance.sorensen)

    return scoredata

def compute_sorensen_across_TimeMap(collectionmodel, scores=None, tokenize=True, stemming=True):
    
    scores = compute_score_across_TimeMap(collectionmodel, "sorensen", 
        sorensen_scoredistance, scores=scores, tokenize=tokenize, stemming=stemming,
        remove_boilerplate=True
    )

    return scores

def levenshtein_scoredistance(first_data, memento_data):

    scoredata = {}

    scoredata = compute_scores_on_distance_measure(
        first_data, memento_data, distance.levenshtein)

    return scoredata

def compute_levenshtein_across_TimeMap(collectionmodel, scores=None, tokenize=True, stemming=True):
    
    scores = compute_score_across_TimeMap(collectionmodel, "levenshtein", 
        levenshtein_scoredistance, scores=scores, tokenize=tokenize, stemming=stemming,
        remove_boilerplate=True
    )

    return scores

def nlevenshtein_scoredistance(first_data, memento_data):

    scoredata = {}

    scoredata = compute_scores_on_distance_measure(
        first_data, memento_data, distance.nlevenshtein)

    return scoredata

def compute_nlevenshtein_across_TimeMap(collectionmodel, scores=None, tokenize=True, stemming=True):

    scores = compute_score_across_TimeMap(collectionmodel, "nlevenshtein", 
        nlevenshtein_scoredistance, scores=scores, tokenize=tokenize, stemming=stemming,
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

    scoredata = {}

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

    scoredata["comparison score"] = len(top_20ish_first_tokens) - number_of_intersecting_terms

    return scoredata

def compute_tfintersection_across_TimeMap(collectionmodel, scores=None, tokenize=None, stemming=True):

    scores = compute_score_across_TimeMap(collectionmodel, "tfintersection",
        tfintersection_scoredistance, scores=scores, tokenize=True, stemming=stemming,
        remove_boilerplate=True
    )

    return scores

def compute_cosine_across_TimeMap(collectionmodel, scores=None, tokenize=None, stemming=None):
    
    # TODO: alter compute_score_across_TimeMap so that much of this function can be replaced
    if scores == None:
        scores = {}
        scores["timemaps"] = {}
    
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

        scores["timemaps"].setdefault(urit, {})

        memento_list = timemap["mementos"]["list"]

        # some TimeMaps have no mementos
        # e.g., http://wayback.archive-it.org/3936/timemap/link/http://www.peacecorps.gov/shutdown/?from=hpb
        if len(memento_list) > 0:

            first_urim = timemap["mementos"]["first"]["uri"]

            logger.debug("Accessing content of first URI-M {} for calculations".format(first_urim))

            first_data = collectionmodel.getMementoContentWithoutBoilerplate(first_urim)

            if len(first_data) == 0:
                errormsg = "The first memento of the TimeMap at {} has no content" \
                    " after removing boilerplate, skipping this timemap for" \
                    " processing...".format(urit)
                logger.warning(errormsg)
                scores["timemaps"][urit]["measure calculation error"] = errormsg
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

                logger.info("Processing Memento {} of {}".format(mementocounter, mementototal))

                urim = memento["uri"]

                logger.debug("Accessing content of URI-M {} for calculations".format(urim))

                scores["timemaps"][urit].setdefault(urim, {})
                scores["timemaps"][urit][urim].setdefault("timemap measures", {})
                scores["timemaps"][urit][urim]["timemap measures"].setdefault(measurename, {})

                try:

                    # in case the mementos are not sorted in order of memento datetime
                    # we ignore the first one for comparison because we already saved it
                    if urim != first_urim:
                        memento_data = collectionmodel.getMementoContentWithoutBoilerplate(urim)
                            
                        processed_urims.append(urim)
                        documents.append(memento_data)

                except CollectionModelMementoErrorException:
                    errormsg = "Errors were recorded while attempting to " \
                        "access URI-M {}, skipping {} calcualtions for this " \
                        "URI-M".format(urim, measurename)
                    logger.warning(errormsg)
                    error_urims.append(urim)
                    errorinfo = collectionmodel.getMementoErrorInformation(urim)
                    scores["timemaps"][urit][urim]["access error"] = str(errorinfo)
                
                mementocounter += 1

            # our full_tokenize function handles stop words
            tfidf_vectorizer = TfidfVectorizer(tokenizer=full_tokenize, stop_words=None)

            errormsg = None

            try:
                tfidf_matrix = tfidf_vectorizer.fit_transform(documents)
                cscores = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix)
                logger.info("Successful processing of cosine similarity scores")
            except ValueError as e:
                errormsg = repr(e)
                logger.warn(errormsg)
                cscores = [[]]

                for i in range(0, len(documents)):
                    if len(documents[0]) == 0:
                        if len(documents[i]) == 0:
                            cscores[0].append(1.0)

            for i in range(0, len(cscores[0])):
                urim = processed_urims[i]
                logger.debug("saving cosine scores for URI-M {}".format(urim))

                scores["timemaps"][urit][urim]["timemap measures"][measurename]["comparison score"] = cscores[0][i]
                scores["timemaps"][urit][urim]["timemap measures"][measurename]["tokenized"] = tokenize
                scores["timemaps"][urit][urim]["timemap measures"][measurename]["stemmed"] = stemming
                scores["timemaps"][urit][urim]["timemap measures"][measurename]["boilerplate removal"] = remove_boilerplate

                if errormsg:
                    scores["timemaps"][urit][urim]["timemap measures"][measurename]["measure calculation error"] = \
                        errormsg

            uritcounter += 1

    return scores

# TODO: rename to evaluate_off_topic_single_measure
def evaluate_off_topic(scoring, threshold, measurename, comparison_direction):

    for urit in scoring["timemaps"]:

        if "measure calculation error" not in scoring["timemaps"][urit]:

            for urim in scoring["timemaps"][urit]:

                # try:

                # if there was an access error, we can't say if it was off-topic or not
                if "access error" not in scoring["timemaps"][urit][urim]:

                    scoring["timemaps"][urit][urim]["timemap measures"][measurename]["topic status"] = "on-topic"

                    # TODO: fix this if/elif block
                    # I know I can use eval, but also know its use has security implications
                    if comparison_direction == ">":
                        if scoring["timemaps"][urit][urim]["timemap measures"][measurename]["comparison score"] > threshold:
                            scoring["timemaps"][urit][urim]["timemap measures"][measurename]["topic status"] = "off-topic"
                    elif comparison_direction == "==":
                        if scoring["timemaps"][urit][urim]["timemap measures"][measurename]["comparison score"] == threshold:
                            scoring["timemaps"][urit][urim]["timemap measures"][measurename]["topic status"] = "off-topic"
                    elif comparison_direction == "<":
                        if scoring["timemaps"][urit][urim]["timemap measures"][measurename]["comparison score"] < threshold:
                            scoring["timemaps"][urit][urim]["timemap measures"][measurename]["topic status"] = "off-topic"
                    elif comparison_direction == "!=":
                        if scoring["timemaps"][urit][urim]["timemap measures"][measurename]["comparison score"] != threshold:
                            scoring["timemaps"][urit][urim]["timemap measures"][measurename]["topic status"] = "off-topic"

                else:
                    scoring["timemaps"][urit][urim]["timemap measures"][measurename]["topic status"] = "no data for calculation"

                # except KeyError as e:
                #     logger.error("While determining if off-topic, it was discovered that"
                #         " a key is missing in the calculations data structure for URI-T {} and URI-M {}".format(
                #         urit, urim
                #     ))
                #     scoring["timemaps"][urit][urim]["per measure threshold calculation error"] = repr(e)

    return scoring

def evaluate_all_off_topic(scoring):

    for urit in scoring["timemaps"]:

        for urim in scoring["timemaps"][urit]:

            memento_data = scoring["timemaps"][urit][urim]
            memento_data["overall topic status"] = "on-topic"

            for measurename in memento_data["timemap measures"]:

                measure_data = memento_data["timemap measures"][measurename]

                if measure_data["topic status"] == "off-topic":

                    memento_data["overall topic status"] = "off-topic"
                    break

    return scoring


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
    "levenshtein": {
        "name": "Levenshtein Distance",
        "function": compute_levenshtein_across_TimeMap,
        "comparison direction": ">",
        "default threshold": 0.05
    },
    "nlevenshtein": {
        "name": "Normalized Levenshtein Distance",
        "function": compute_nlevenshtein_across_TimeMap,
        "comparison direction": ">",
        "default threshold": 0.05
    }
}