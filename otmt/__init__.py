import os
import time
import random
import getpass
import logging
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ---------------------------------------------------------------------------
# Global Network Layer Patch: Dynamic WS-DL User-Agent & Jitter
# ---------------------------------------------------------------------------
# Allows custom email override via OTMT_USER_EMAIL, otherwise uses current_user@odu.edu
DEFAULT_EMAIL = f"{getpass.getuser()}@odu.edu"
USER_EMAIL = os.environ.get("OTMT_USER_EMAIL", DEFAULT_EMAIL)
USER_AGENT = f"ODU WS-DL Research ({USER_EMAIL})"

os.environ["HTTP_USER_AGENT"] = USER_AGENT

class RetryNon200(Retry):
    """Custom retry logic that forces retries on ANY status code other than 200 OK."""
    def is_retry(self, method, status_code, has_retry_after=False):
        if status_code != 200:
            return True
        return super().is_retry(method, status_code, has_retry_after=has_retry_after)

class JitteryAdapter(HTTPAdapter):
    def send(self, request, **kwargs):
        time.sleep(random.uniform(3.0, 7.0))
        return super().send(request, **kwargs)

retry_strategy = RetryNon200(
    total=5,
    backoff_factor=2,
    raise_on_status=False
)

adapter = JitteryAdapter(max_retries=retry_strategy)

orig_session_init = requests.Session.__init__

def patched_session_init(self, *args, **kwargs):
    orig_session_init(self, *args, **kwargs)
    self.headers.update({
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5"
    })
    self.mount("https://", adapter)
    self.mount("http://", adapter)

requests.Session.__init__ = patched_session_init
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------

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

__all__ = [
    "CollectionModel", "CollectionModelException",
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

try:  # Python 2.7+
    from logging import NullHandler
except ImportError:
    class NullHandler(logging.Handler):
        def emit(self, record):
            pass

logging.getLogger(__name__).addHandler(NullHandler())
