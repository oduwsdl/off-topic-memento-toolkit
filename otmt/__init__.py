from .collectionmodel import CollectionModel, CollectionModelException, \
    CollectionModelMementoErrorException, CollectionModelTimeMapErrorException, \
    CollectionModelNoSuchMementoException, CollectionModelNoSuchTimeMapException
from .input_types import get_collection_model, supported_input_types, \
    discover_raw_urims, working_directory_default
from .argument_processing import process_collection_similarity_measure_inputs, \
    process_timemap_similarity_measure_inputs, process_input_types, \
    get_logger, calculate_loglevel, process_output_types
from .output_types import supported_output_types
from .archive_information import generate_raw_urim, archive_mappings
from .timemap_measures import compute_bytecount_across_TimeMap, \
    compute_wordcount_across_TimeMap, compute_jaccard_across_TimeMap, \
    compute_cosine_across_TimeMap, compute_sorensen_across_TimeMap, \
    compute_levenshtein_across_TimeMap, compute_nlevenshtein_across_TimeMap, \
    compute_tfintersection_across_TimeMap, supported_timemap_measures, \
    compute_rawsimhash_across_TimeMap, compute_tfsimhash_across_TimeMap, \
    compute_gensim_lsi_across_TimeMap, compute_gensim_lda_across_TimeMap
from .collection_measures import compute_jaccard_accross_collection, \
    compute_sorensen_accross_collection, supported_collection_measures
from .measuremodel import MeasureModel, MeasureModelNoSuchMemento, \
    MeasureModelNoSuchTimeMap, MeasureModelNoSuchMeasure, MeasureModelNoSuchMeasureType
from .metadata_calcluations import compute_Simhashes, compute_raw_content_lengths, \
    detect_languages, extract_memento_datetimes

# __init__.py documentation: https://docs.python.org/3/tutorial/modules.html#packages
# file/folder info: https://www.python.org/dev/peps/pep-0008/#package-and-module-names

__all__ = ["CollectionModel", "CollectionModelException",
    "CollectionModelMementoErrorException", 
    "CollectionModelTimeMapErrorException", 
    "CollectionModelNoSuchMementoException",
    "get_collection_model", "process_collection_similarity_measure_inputs",
    "process_timemap_similarity_measure_inputs",
    "process_input_types", "get_logger", "calculate_loglevel", 
    "supported_input_types", "supported_output_types",
    "generate_raw_urim", "archive_mappings",
    "working_directory_default", "process_output_types",
    "compute_bytecount_across_TimeMap",
    "compute_wordcount_across_TimeMap", "compute_jaccard_across_TimeMap",
    "compute_cosine_across_TimeMap", "compute_sorensen_across_TimeMap",
    "compute_levenshtein_across_TimeMap", "compute_nlevenshtein_across_TimeMap",
    "compute_tfintersection_across_TimeMap", "supported_timemap_measures",
    "compute_rawsimhash_across_TimeMap", "compute_tfsimhash_across_TimeMap",
    "MeasureModel", "MeasureModelNoSuchMemento",
    "MeasureModelNoSuchTimeMap", "MeasureModelNoSuchMeasure",
    "compute_Simhashes", "compute_raw_content_lengths",
    "compute_jaccard_accross_collection", "compute_sorensen_accross_collection",
    "supported_collection_measures", "detect_languages", "extract_memento_datetimes"
    ]

import logging
try:  # Python 2.7+
    from logging import NullHandler
except ImportError:
    class NullHandler(logging.Handler):
        def emit(self, record):
            pass

logging.getLogger(__name__).addHandler(NullHandler())
