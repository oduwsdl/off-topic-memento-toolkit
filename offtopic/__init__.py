from .collectionmodel import CollectionModel, CollectionModelException, \
    CollectionModelMementoErrorException, CollectionModelTimeMapErrorException, \
    CollectionModelNoSuchMementoException, CollectionModelNoSuchTimeMapException
from .archiveit_collection import ArchiveItCollection, ArchiveItCollectionException
from .input_types import get_collection_model, supported_input_types, \
    discover_raw_urims, working_directory_default
from .argument_processing import process_similarity_measure_inputs, \
    process_input_types, get_logger, calculate_loglevel, process_output_types
from .topic_processor import supported_measures, evaluate_off_topic
from .output_types import supported_output_types
from .archive_information import generate_raw_urim, archive_mappings
from .timemap_measures import compute_bytecount_across_TimeMap, \
    compute_wordcount_across_TimeMap, compute_jaccard_across_TimeMap, \
    compute_cosine_across_TimeMap, compute_sorensen_across_TimeMap, \
    compute_levenshtein_across_TimeMap, compute_nlevenshtein_across_TimeMap

# __init__.py documentation: https://docs.python.org/3/tutorial/modules.html#packages
# file/folder info: https://www.python.org/dev/peps/pep-0008/#package-and-module-names

__all__ = ["CollectionModel", "CollectionModelException",
    "CollectionModelMementoErrorException", 
    "CollectionModelTimeMapErrorException", 
    "CollectionModelNoSuchMementoException",
    "ArchiveItCollection", "ArchiveItCollectionException",
    "get_collection_model", "process_similarity_measure_inputs",
    "process_input_types", "get_logger", "calculate_loglevel", 
    "supported_input_types", "supported_measures",
    "evaluate_off_topic", "supported_output_types",
    "generate_raw_urim", "archive_mappings",
    "working_directory_default", "process_output_types",
    "compute_bytecount_across_TimeMap",
    "compute_wordcount_across_TimeMap", "compute_jaccard_across_TimeMap",
    "compute_cosine_across_TimeMap", "compute_sorensen_across_TimeMap",
    "compute_levenshtein_across_TimeMap", "compute_nlevenshtein_across_TimeMap",
    ]

import logging
try:  # Python 2.7+
    from logging import NullHandler
except ImportError:
    class NullHandler(logging.Handler):
        def emit(self, record):
            pass

logging.getLogger(__name__).addHandler(NullHandler())