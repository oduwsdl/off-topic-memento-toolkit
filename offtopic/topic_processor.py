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

from offtopic import CollectionModel

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

def convert_to_raw_uri(urim):

    if "/wayback.archive-it.org/" in urim:
        urim = urim.replace('/http', 'id_/http')

    return urim

def compute_scores_against_first_memento_in_TimeMap(
    scorefunction, distance_function, collection_model, scorename, scoredataname):

    scoring = {}
    scoring["scorename"] = scorename
    scoring["timemaps"] = {}

    for urit in collection_model.getTimeMapURIList():

        timemap = collection_model.getTimeMap(urit)

        scoring["timemaps"][urit] = {}

        # some TimeMaps have no mementos
        # e.g., http://wayback.archive-it.org/3936/timemap/link/http://www.peacecorps.gov/shutdown/?from=hpb
        if len(timemap["mementos"]["list"]) > 0:

            first_urim = convert_to_raw_uri(timemap["mementos"]["first"]["uri"])

            logger.info("extracting URI-M {} for calculations".format(first_urim))

            first_content = collection_model.getMementoContentWithoutBoilerplate(first_urim)
            first_tokens = tokenize(first_content)

            first_memento_score = scorefunction(first_tokens)

            for memento in timemap["mementos"]["list"]:

                urim = convert_to_raw_uri(memento["uri"])

                logger.info("extracting URI-M {} for calculations".format(urim))

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

    return scoring    

def compute_bytecount_score(tokens):
    
    return len(''.join(tokens))

def compute_bytecount_distance(first_memento_bytecount, memento_bytecount):
    
    return 1 - (first_memento_bytecount / memento_bytecount)

def calculate_bytecount_scores(collection_model):

    scoring = compute_scores_against_first_memento_in_TimeMap(
        compute_bytecount_score, compute_bytecount_distance, collection_model, 
        "bytecount", "bytes"
    )

    return scoring

def compute_wordcount_score(tokens):

    return len(tokens)

def compute_wordcount_distance(first_memento_wordcount, memento_wordcount):

    return 1 - (first_memento_wordcount / memento_wordcount)

def calculate_wordcount_scores(collection_model):

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

            first_urim = convert_to_raw_uri(timemap["mementos"]["first"]["uri"])

            first_content = collection_model.getMementoContentWithoutBoilerplate(
                first_urim
            )
            first_tokens = tokenize(first_content)
            
            for memento in timemap["mementos"]["list"]:

                urim = convert_to_raw_uri(memento["uri"])

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

                urim = convert_to_raw_uri(memento["uri"])

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