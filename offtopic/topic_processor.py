import sys
import nltk
import string
import logging
import logging.config
import distance

from nltk.corpus import stopwords
from nltk.stem.porter import PorterStemmer
from gensim import corpora, models, similarities
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer

from .collectionmodel import CollectionModel, CollectionModelMementoErrorException
from .archive_information import generate_raw_urim

logger = logging.getLogger(__name__)

stemmer = PorterStemmer()

def stem_tokens(tokens):

    stemmed = []

    for item in tokens:
        stemmed.append( stemmer.stem(item) )

    return stemmed

def tokenize(text):

    stopset = stopwords.words("english") + list(string.punctuation)

    tokens = nltk.word_tokenize(text.decode("utf8"))
    stems = stem_tokens(tokens)

    return [ i for i in stems if i not in stopset ]

def compute_scores_against_first_memento_in_TimeMap(
    scorefunction, distance_function, collection_model, scorename, scoredataname):

    scoring = {}
    scoring["scorename"] = scorename
    scoring["timemaps"] = {}

    logger.info("beginning TimeMap iteration")

    # logger.debug("timemap URI list: {}".format(collection_model.getTimeMapURIList()))

    urits = collection_model.getTimeMapURIList()
    urittotal = len(urits)

    logger.info("There are {} TimeMaps in this collection".format(urittotal))
    uritcounter = 1

    for urit in urits:

        logger.info("Processing TimeMap {} of {}".format(uritcounter, urittotal))
        logger.debug("processing memementos from TimeMap {}".format(urit))

        timemap = collection_model.getTimeMap(urit)

        scoring["timemaps"][urit] = {}

        # some TimeMaps have no mementos
        # e.g., http://wayback.archive-it.org/3936/timemap/link/http://www.peacecorps.gov/shutdown/?from=hpb
        if len(timemap["mementos"]["list"]) > 0:

            # first_urim = generate_raw_urim(timemap["mementos"]["first"]["uri"])
            first_urim = timemap["mementos"]["first"]["uri"]

            logger.debug("Accessing content of first URI-M {} for calculations".format(first_urim))

            first_content = collection_model.getMementoContentWithoutBoilerplate(first_urim)
            first_tokens = tokenize(first_content)

            first_memento_score = scorefunction(first_tokens)

            mementos = timemap["mementos"]["list"]
            mementototal = len(mementos)

            logger.info("There are {} mementos in this TimeMap".format(mementototal))
            mementocounter = 1

            for memento in mementos:

                logger.info("Processing Memento {} of {}".format(mementocounter, mementototal))

                # urim = generate_raw_urim(memento["uri"])
                urim = memento["uri"]

                logger.debug("Accessing content of URI-M {} for calculations".format(urim))

                try:
                    memento_content = collection_model.getMementoContentWithoutBoilerplate(urim)
                    memento_tokens = tokenize(memento_content)

                    memento_score = scorefunction(memento_tokens)

                    scoring["timemaps"][urit].setdefault(urim, {})
                    scoring["timemaps"][urit][urim].setdefault(scoredataname, {})
                    scoring["timemaps"][urit][urim].setdefault("score", {})
                    scoring["timemaps"][urit][urim][scoredataname] = memento_score
                    scoring["timemaps"][urit][urim]["score"] = distance_function(
                        first_memento_score, memento_score
                    )
                except CollectionModelMementoErrorException:
                    logger.warning("Errors were recorded while attempting to "
                        "access URI-M {}, skipping calcualtions for this "
                        "URI-M".format(urim))

                mementocounter += 1
            
            uritcounter += 1

    return scoring    

def compute_bytecount_score(tokens):
    
    return len(''.join(tokens))

def compute_bytecount_distance(first_memento_bytecount, memento_bytecount):

    if memento_bytecount == 0:

        if first_memento_bytecount == 0:
            return 0
        else:
            return 1 - (memento_bytecount / first_memento_bytecount)

    else:
        return 1 - (first_memento_bytecount / memento_bytecount)

def calculate_bytecount_scores(collection_model):

    logger.info("calculating bytecount scores for mementos")

    scoring = compute_scores_against_first_memento_in_TimeMap(
        compute_bytecount_score, compute_bytecount_distance, collection_model, 
        "bytecount", "bytes"
    )

    return scoring

def compute_wordcount_score(tokens):

    return len(tokens)

def compute_wordcount_distance(first_memento_wordcount, memento_wordcount):

    if memento_wordcount == 0:
        if first_memento_wordcount == 0:
            return 0
        else:
            return 1 - (memento_wordcount / first_memento_wordcount)
    else:
        return 1 - (first_memento_wordcount / memento_wordcount)
    
def calculate_wordcount_scores(collection_model):

    logger.info("calculating wordcount scores for mementos")

    scoring = compute_scores_against_first_memento_in_TimeMap(
        compute_wordcount_score, compute_wordcount_distance, collection_model, 
        "wordcount", "words"
    )                  

    return scoring

def evaluate_off_topic(scoring, threshold):

    for urit in scoring["timemaps"]:

        for urim in scoring["timemaps"][urit]:

            scoring["timemaps"][urit][urim]["on-topic"] = False

            if scoring["timemaps"][urit][urim]["score"] > threshold:
                scoring["timemaps"][urit][urim]["on-topic"] = True

    return scoring

def calculate_jaccard_scores(collection_model):

    scoring = {}
    scoring["timemaps"] = {}

    for urit in collection_model.getTimeMapURIList():

        timemap = collection_model.getTimeMap(urit)

        scoring["timemaps"][urit] = {}

        if len(timemap["mementos"]["list"]) > 0:

            first_urim = generate_raw_urim(timemap["mementos"]["first"]["uri"])

            first_content = collection_model.getMementoContentWithoutBoilerplate(
                first_urim
            )
            first_tokens = tokenize(first_content)
            
            for memento in timemap["mementos"]["list"]:

                urim = generate_raw_urim(memento["uri"])

                memento_content = collection_model.getMementoContentWithoutBoilerplate(
                    urim
                )
                memento_tokens = tokenize(memento_content)
                
                scoring["timemaps"][urit].setdefault(urim, {})
                scoring["timemaps"][urit][urim]["score"] = distance.jaccard(
                    first_tokens, memento_tokens
                )

    return scoring

def calculate_cosinesimilarity_scores(collection_model):

    scoring = {}
    scoring["timemaps"] = {}

    for urit in collection_model.getTimeMapURIList():

        timemap = collection_model.getTimeMap(urit)
        tfidf_vectorizer = TfidfVectorizer()

        scoring["timemaps"][urit] = {}

        if len(timemap["mementos"]["list"]) > 0:

            documents = []
            urims = []
            
            for memento in timemap["mementos"]["list"]:

                urim = generate_raw_urim(memento["uri"])

                memento_content = collection_model.getMementoContentWithoutBoilerplate(
                    urim
                )

                documents.append(memento_content)
                urims.append(urim)

            tfidf_matrix = tfidf_vectorizer.fit_transform(documents)
            cscores = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix)

            for index in range(0, len(cscores)):
                urim = urims[index]
                scoring["timemaps"][urit].setdefault(urim, {})
                scoring["timemaps"][urit][urim]["score"] = cscores[index]

    return scoring

def calculate_term_frequencies(tokens):

    term_frequency = {}

    for token in tokens:

        term_frequency[token] += 1

    return term_frequency

# def calculate_tfintersection_scores(collection_model):

#     scoring = {}
#     scoring["timemaps"] = {}

#     for urit in collection_model.getTimeMapURIList():

#         timemap = collection_model.getTimeMap(urit)

#         scoring["timemaps"][urit] = {}

#         if len(timemap["mementos"]["list"]) > 0:

#             first_urim = convert_to_raw_uri(timemap["mementos"]["first"]["uri"])

#             first_content = collection_model.getMementoContentWithoutBoilerplate(first_urim)
#             first_tokens = tokenize(first_content)
#             first_term_freq = calculate_term_frequencies(first_tokens)

#             for memento in timemap["mementos"]["list"]:

#                 urim = convert_to_raw_uri(memento["uri"])

#                 memento_content = collection_model.getMementoContentWithoutBoilerplate(urim)
#                 memento_tokens = tokenize(memento_content)
#                 memento_term_freq = calculate_term_frequencies(memento_tokens)

#                 for term in first_term_freq

                




# def calculate_gensimlda_scores(collection_model):

#     scoring = {}
#     scoring["timemaps"] = {}

#     for urit in collection_model.getTimeMapURIList():

#         timemap = collection_model.getTimeMap(urit)

#         scoring["timemaps"][urit] = {}

#         # some TimeMaps have no mementos
#         # e.g., http://wayback.archive-it.org/3936/timemap/link/http://www.peacecorps.gov/shutdown/?from=hpb
#         if len(timemap["mementos"]["list"]) > 0:

#             texts = []

#             for memento in timemap["mementos"]["list"]:

#                 urim = convert_to_raw_uri(memento["uri"])

#                 memento_content = collection_model.getMementoContentWithoutBoilerplate(urim)
#                 memento_tokens = tokenize(memento_content)

#                 texts.append(memento_tokens)

#             # TODO: don't do this in memory
#             dictionary = corpora.Dictionary(texts)
#             corpus = [dictionary.doc2bow(text) for text in texts]
#             tfidf = models.TfidfModel(corpus)
#             corpus_tfidf = tfidf[corpus]

#             # TODO: how many topics do we need?
#             lsi = models.LsiModel(corpus_tfidf, id2word=dictionary, num_topics=2)



            



supported_measures = {
    # "tfintersection": {
    #     "name": "TF-Intersection",
    #     "default_threshold": 0,
    #     "function": None
    # },
    "cosine": {
        "name": "Cosine Similarity",
        "default_threshold": 0.15,
        "function": calculate_cosinesimilarity_scores
    },
    "jaccard": {
        "name": "Jaccard Distance",
        "default_threshold": 0.05,
        "function": calculate_jaccard_scores
    },
    # "gensim-lda": {
    #     "name": "Gensim using LDA",
    #     "default_threshold": 0,
    #     "function": calculate_gensimlda_scores
    # },
    "wordcount": {
        "name": "Word Count",
        "default_threshold": -0.85,
        "function": calculate_wordcount_scores
    },
    "bytecount": {
        "name": "Byte Count",
        "default_threshold": -0.65,
        "function": calculate_bytecount_scores
    }
}