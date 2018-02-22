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

    logger.info("Computing score across TimeMap, beginning TimeMap iteration...")

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

            mementos = timemap["mementos"]["list"]

            mementototal = len(mementos)
            logger.info("There are {} mementos in this TimeMap".format(mementototal))

            mementocounter = 1

            for memento in mementos:

                logger.info("Processing Memento {} of {}".format(mementocounter, mementototal))

                urim = memento["uri"]

                logger.debug("Accessing content of URI-M {} for calculations".format(urim))

                scores["timemaps"][urit].setdefault(urim, {})

                try:
                    memento_data = get_memento_data_for_measure(
                        urim, collectionmodel, tokenize=tokenize, 
                        stemming=stemming, 
                        remove_boilerplate=remove_boilerplate)
                        
                    scores["timemaps"][urit][urim].setdefault("timemap measures", {})
                    scores["timemaps"][urit][urim]["timemap measures"][measurename] = \
                        scoredistance_function(first_data, memento_data)

                except CollectionModelMementoErrorException:
                    logger.warning("Errors were recorded while attempting to "
                        "access URI-M {}, skipping {} calcualtions for this "
                        "URI-M".format(urim, measurename))
                
                mementocounter += 1

            uritcounter += 1

    return scores

def bytecount_scoredistance(first_data, memento_data, scorecache=None):

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

def wordcount_scoredistance(first_data, memento_data, scorecache=None):

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

def jaccard_scoredistance(first_data, memento_data, scorecache=None):

    scoredata = {}

    scoredata["comparison score"] = distance.jaccard(first_data, memento_data)

    return scoredata

def compute_jaccard_across_TimeMap(collectionmodel, scores=None, tokenize=True, stemming=True):

    scores = compute_score_across_TimeMap(collectionmodel, "jaccard", 
        jaccard_scoredistance, scores=scores, tokenize=tokenize, stemming=stemming,
        remove_boilerplate=True
    )

    return scores

def sorensen_scoredistance(first_data, memento_data, scorecache=None):

    scoredata = {}

    scoredata["comparison score"] = distance.sorensen(first_data, memento_data)

    return scoredata

def compute_sorensen_across_TimeMap(collectionmodel, scores=None, tokenize=True, stemming=True):
    
    scores = compute_score_across_TimeMap(collectionmodel, "sorensen", 
        sorensen_scoredistance, scores=scores, tokenize=tokenize, stemming=stemming,
        remove_boilerplate=True
    )

    return scores

def levenshtein_scoredistance(first_data, memento_data, scorecache=None):

    scoredata = {}

    scoredata["comparison score"] = distance.levenshtein(first_data, memento_data)

    return scoredata

def compute_levenshtein_across_TimeMap(collectionmodel, scores=None, tokenize=True, stemming=True):
    
    scores = compute_score_across_TimeMap(collectionmodel, "levenshtein", 
        levenshtein_scoredistance, scores=scores, tokenize=tokenize, stemming=stemming,
        remove_boilerplate=True
    )

    return scores

def nlevenshtein_scoredistance(first_data, memento_data, scorecache=None):

    scoredata = {}

    scoredata["comparison score"] = distance.nlevenshtein(first_data, memento_data)

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

def tfintersection_scoredistance(first_data, memento_data, scorecache=None):

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
    # remove_boilerplate = True

    logger.info("Computing score across TimeMap, beginning TimeMap iteration...")

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

            # first_data = get_memento_data_for_measure(
            #     first_urim, collectionmodel, tokenize=tokenize, stemming=stemming, 
            #     remove_boilerplate=remove_boilerplate)
            first_data = collectionmodel.getMementoContentWithoutBoilerplate(first_urim)

            mementos = timemap["mementos"]["list"]

            mementototal = len(mementos)
            logger.info("There are {} mementos in this TimeMap".format(mementototal))

            mementocounter = 1

            processed_urims = []
            documents = []

            processed_urims.append(first_urim)
            documents.append(first_data)

            for memento in mementos:

                logger.info("Processing Memento {} of {}".format(mementocounter, mementototal))

                urim = memento["uri"]

                logger.debug("Accessing content of URI-M {} for calculations".format(urim))

                scores["timemaps"][urit].setdefault(urim, {})

                try:
                    # memento_data = get_memento_data_for_measure(
                    #     urim, collectionmodel, tokenize=tokenize, 
                    #     stemming=stemming, 
                    #     remove_boilerplate=remove_boilerplate)
                    memento_data = collectionmodel.getMementoContentWithoutBoilerplate(urim)
                        
                    processed_urims.append(urim)
                    documents.append(memento_data)

                except CollectionModelMementoErrorException:
                    logger.warning("Errors were recorded while attempting to "
                        "access URI-M {}, skipping {} calcualtions for this "
                        "URI-M".format(urim, measurename))
                
                mementocounter += 1

            # our full_tokenize function handles stop words
            tfidf_vectorizer = TfidfVectorizer(tokenizer=full_tokenize, stop_words=None)
            tfidf_matrix = tfidf_vectorizer.fit_transform(documents)
            cscores = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix)

            for i in range(0, len(cscores[0])):
                urim = processed_urims[i]
                logger.debug("saving cosine scores for URI-M {}".format(urim))
                scores["timemaps"][urit][urim].setdefault("timemap measures", {})
                scores["timemaps"][urit][urim]["timemap measures"].setdefault(measurename, {})
                scores["timemaps"][urit][urim]["timemap measures"][measurename]["comparison score"] = cscores[0][i]

            uritcounter += 1

    return scores