# -*- coding: utf-8 -*-

"""
otmt.input_types
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module exists to permit different ways of inseting data into 
a MeasureModel, including downloading from TimeMaps and collections.
"""

import sys
import logging
import json
import multiprocessing
import requests
import csv
import copy
import random
import pprint

from datetime import datetime
from datetime import date

from requests_futures.sessions import FuturesSession
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from requests.exceptions import ConnectionError, TooManyRedirects
from warcio.archiveiterator import ArchiveIterator
from aiu import ArchiveItCollection

from .collectionmodel import CollectionModel
# from .archiveit_collection import ArchiveItCollection
from .archive_information import generate_raw_urim

logger = logging.getLogger(__name__)

cpu_count = multiprocessing.cpu_count()

working_directory_default = "/tmp/otmt-working"

def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""

    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError ("Type %s not serializable" % type(obj))

def extract_urim_mdt_content_from_record(record):
    """This function extracts the URI-M, memento-datetime, headers and content
    from a WARC record object provided by warcio.
    """

    urir = None
    memento_datetime = None
    headers = None
    content = None

    if record.rec_type == 'response':

        uri = record.rec_headers.get_header('WARC-Target-URI')

        # WARCs keep track of DNS requests
        if uri.split(':')[0] != 'dns':

            headers = {}

            for line in record.http_headers.headers:
                key = line[0].lower()
                value = line[1]

                headers[key] = value

            if "content-type" in headers:

                if "text/html" in headers["content-type"]:

                    logger.debug("WARC-Entry-URI: {}".format(uri))

                    memento_datetime = datetime.strptime(
                        record.rec_headers.get_header('WARC-Date'),
                        '%Y-%m-%dT%H:%M:%SZ'
                    )

                    logger.debug("WARC-Entry-Memento-Datetime: {}".format(memento_datetime))
                    logger.debug("WARC-Entry-Headers: {}".format(headers))

                    status_code = record.http_headers.get_statuscode()

                    headers["http-status"] = status_code

                    content = record.raw_stream.read()

                    urir = uri

    return urir, memento_datetime, headers, content

def generate_timemap_from_timemap_data(urir, timemap_data):
    """This function generates a TimeMap for `urir` given `timemap_data`
    stored in a dictionary.
    """

    timemap_dict = {}

    timemap_dict["original_uri"] = urir
    timemap_dict["timegate_uri"] = "from-warc::timegate::{}".format(urir)
    timemap_dict["timemap_uri"] = {}
    timemap_dict["timemap_uri"]["json_format"] = \
        "from-warc::timemap::{}".format(urir)
    timemap_dict["mementos"] = {}
    timemap_dict["mementos"]["list"] = []

    memento_list = timemap_dict["mementos"]["list"]

    list_for_sorting = []

    for entry in timemap_data:

        mdt = entry["datetime"]
        uri = entry["uri"]

        memento_list.append(entry)

        list_for_sorting.append((mdt, uri))

    sorted_list_for_sorting = sorted(list_for_sorting)

    timemap_dict["mementos"]["first"] = {
        "datetime": sorted_list_for_sorting[0][0],
        "uri": sorted_list_for_sorting[0][1]
    }

    timemap_dict["mementos"]["last"] = {
        "datetime": sorted_list_for_sorting[-1][0],
        "uri": sorted_list_for_sorting[-1][1]
    }

    return timemap_dict

def get_collection_model_from_warc(warcfiles, working_directory):
    """This function takes the files specified in `warcfiles` and 
    fills a colleciton model with their headers and HTTP entities.
    """

    logger.warning("Only HTML entities are extracted from warcfiles")

    cm = CollectionModel(working_directory)

    timemaps_data = {}

    for warcfile in warcfiles:

        with open(warcfile, 'rb') as stream:

            for record in ArchiveIterator(stream):
                urir, memento_datetime, headers, content = \
                    extract_urim_mdt_content_from_record(record)

                if urir:

                    urim = "from-warc::{}::{}".format(
                        memento_datetime.strftime("%Y%m%d%H%M%S"), urir
                    )
                    cm.addMemento(urim, content, headers)

                    timemaps_data.setdefault(urir, []).append({
                        "datetime": memento_datetime,
                        "uri": urim
                    })

    for urir in timemaps_data:

        urit = "from-warc::timemap::{}".format(urir)

        timemap_data = timemaps_data[urir]

        timemap_json = json.dumps(
            generate_timemap_from_timemap_data(urir, timemap_data),
            default=json_serial
        )

        timemap_headers = {}

        cm.addTimeMap(urit, timemap_json, timemap_headers)

    return cm

def generate_archiveit_urits(cid, seed_uris):
    """This function generates TimeMap URIs (URI-Ts) for a list of `seed_uris`
    from an Archive-It colleciton specified by `cid`.
    """

    urit_list = []

    for urir in seed_uris:
        urit = "http://wayback.archive-it.org/{}/timemap/link/{}".format(
            cid, urir
        )

        urit_list.append(urit)  

    return urit_list

def get_head_responses(session, uris):
    """This function creates a futures object for each URI-M in `uris,
    using an existing `session` object from requests-futures. Only HEAD
    requests are performed.
    """

    futures = {}

    for uri in uris:

        logger.debug("issuing HEAD on uri {}".format(uri))

        futures[uri] = session.head(uri, allow_redirects=True)

    return futures

def get_uri_responses(session, raw_uris):
    """This function creates a futures object for each URI-M in `raw_uris`,
    using an existing `session` object from requests-futures. Only GET
    requests are performed.
    """

    futures = {}

    for uri in raw_uris:

        logger.debug("issuing GET on uri {}".format(uri))

        futures[uri] = session.get(uri)

    return futures

def list_generator(input_list):
    """This function generates the next item in a list. It is useful for lists
    that have their items deleted while one is iterating through them.
    """

    logger.debug("list generator called")

    while len(input_list) > 0:
        for item in input_list:
            logger.debug("list now has {} items".format(len(input_list)))
            logger.debug("yielding {}".format(item))
            yield item

def get_collection_model_from_archiveit(archiveit_cid, working_directory):
    """This function takes an Archive-It Collection ID as `archiveit_cid` and
    fills a collection model with the contents of that collection.
    """

    archiveit_cid = archiveit_cid[0]

    logger.info("Acquiring Archive-It collection {}".format(
        archiveit_cid
    ))

    aic = ArchiveItCollection(archiveit_cid, logger=logger)

    logger.debug("creating collection model")

    cm = CollectionModel(working_directory)

    logger.debug("generating list of seed URIs")

    seed_uris = aic.list_seed_uris()

    logger.debug("seed URIs: {}".format(
        seed_uris
    ))

    urits = generate_archiveit_urits(archiveit_cid, seed_uris)

    retry_session = requests.Session()
    retry = Retry(
        total=10,
        read=10,
        connect=10,
        backoff_factor=0.3,
        status_forcelist=(500, 502, 504)
    )
    adapter = HTTPAdapter(max_retries=retry)
    retry_session.mount('http://', adapter)
    retry_session.mount('https://', adapter)  

    with FuturesSession(max_workers=cpu_count, session=retry_session) as session:
        futures = get_uri_responses(session, urits)

    working_uri_list = list(futures.keys())

    for urit in list_generator(working_uri_list):

        logging.debug("checking if URI-T {} is done downloading".format(urit))

        if futures[urit].done():

            logger.debug("URI-T {} is done, extracting content".format(urit))

            try:
                response = futures[urit].result()

                http_status = response.status_code

                if http_status == 200:

                    timemap_content = response.text
                    timemap_headers = dict(response.headers)
                    timemap_headers["http-status"] = http_status

                    logger.debug("adding TimeMap content for URI-T {}".format(urit))
                    logger.debug("Content: {}".format(timemap_content))
                    logger.debug("Headers: {}".format(
                        pprint.pformat(timemap_headers)
                        ))

                    cm.addTimeMap(urit, timemap_content, timemap_headers)

                # TODO: else store connection errors in CollectionModel
                working_uri_list.remove(urit)
            
            except ConnectionError:

                logger.warning("There was a connection error while attempting "
                    "to download URI-T {}".format(urit))

                # TODO: store connection errors in CollectionModel
                working_uri_list.remove(urit)

            except TooManyRedirects:

                logger.warning("There were too many redirects while attempting "
                    "to download URI-T {}".format(urit))

                # TODO: store connection errors in CollectionModel
                working_uri_list.remove(urit)

    urims = []

    for urit in cm.getTimeMapURIList():

        timemap = cm.getTimeMap(urit)

        try:
            for memento in timemap["mementos"]["list"]:
                # raw_urim = generate_raw_urim(memento["uri"])
                # urims.append(raw_urim)
                urims.append(memento["uri"])
        except KeyError as e:
            logger.exception("Skipping TimeMap at {} due to errors\nTimeMap Object: {}".format(urit, timemap))
        except Exception as e:
            logger.error("Error encountered processing TimeMap at {}".format(urit))
            logger.error("TimeMap Object: {}".format(timemap))
            raise e

    fetch_and_save_memento_content(urims, cm)
                
    return cm

def discover_raw_urims(urimlist, futures=None):
    """This function checks that the URI-Ms in `urimlist` are valid mementos,
    following all redirects and checking for a Memento-Datetime header.
    """

    raw_urimdata = {}
    errordata = {}

    if futures == None:

        retry_session = requests.Session()
        retry = Retry(
            total=10,
            read=10,
            connect=10,
            backoff_factor=0.3,
            status_forcelist=(500, 502, 504)
        )
        adapter = HTTPAdapter(max_retries=retry)
        retry_session.mount('http://', adapter)
        retry_session.mount('https://', adapter)  

        with FuturesSession(max_workers=cpu_count) as session:
            futures = get_head_responses(session, urimlist)

    working_uri_list = list(futures.keys())

    completed_urims = []

    # for urim in list_generator(working_uri_list):
    while len(completed_urims) < len(list(working_uri_list)):

        urim = random.choice(
            list(set(working_uri_list) - set(completed_urims))
        )

        logger.debug("checking if URI-M {} is done downloading".format(urim))

        if futures[urim].done():

            logger.debug("searching for raw version of URI-M {}".format(urim))

            try:

                response = futures[urim].result()

                if "memento-datetime" in response.headers:

                    if len(response.history) == 0:
                        raw_urimdata[urim] = generate_raw_urim(urim)
                    else:
                        raw_urimdata[urim] = generate_raw_urim(response.url)

                    logger.debug("added raw URI-M {} associated with URI-M {}"
                        " to the list to be downloaded".format(raw_urimdata[urim], urim))

                else:

                    warn_msg = "No Memento-Datetime in Response Headers for " \
                        "URI-M {}".format(urim)

                    logger.warning(warn_msg)
                    errordata[urim] = warn_msg

            except ConnectionError as e:
                logger.warning("While acquiring memento at {} there was an error of {}, "
                    "this event is being recorded".format(urim, repr(e)))
                errordata[urim] = repr(e)

            except TooManyRedirects as e:
                logger.warning("While acquiring memento at {} there was an error of {},"
                    "this event is being recorded".format(urim, repr(e)))
                errordata[urim] = repr(e)

            finally:
                logger.debug("Removing URI-M {} from the processing list".format(urim))
                completed_urims.append(urim)

    return raw_urimdata, errordata

def fetch_and_save_memento_content(urimlist, collectionmodel):
    """This function takes a `urimlist` and saves the raw memento content in 
    `collectionmodel`.
    """

    logger.info("Discovering raw mementos")
    raw_urimdata, errordata = discover_raw_urims(urimlist)

    logger.debug("Storing error data in collection model")

    invert_raw_urimdata_mapping = {}
    raw_urims = []

    for urim in raw_urimdata:
        raw_urim = raw_urimdata[urim]
        invert_raw_urimdata_mapping.setdefault(raw_urim, []).append( urim )
        raw_urims.append(raw_urim)

    logger.info("Issuing requests for {} raw mementos".format(len(raw_urims)))

    retry_session = requests.Session()
    retry = Retry(
        total=10,
        read=10,
        connect=10,
        backoff_factor=0.3,
        status_forcelist=(500, 502, 504)
    )
    adapter = HTTPAdapter(max_retries=retry)
    retry_session.mount('http://', adapter)
    retry_session.mount('https://', adapter)  

    with FuturesSession(max_workers=cpu_count) as session:
        futures = get_uri_responses(session, raw_urims)

    completed_raw_urims = []
    leftovers = list(set(raw_urims) - set(completed_raw_urims))

    # for raw_urim in list_generator(raw_urims_copy):
    while len(leftovers) > 0:

        raw_urim = random.choice(leftovers)

        logger.debug("Processing raw URI-M {} associated with URI-M {}".format(
            raw_urim, invert_raw_urimdata_mapping[raw_urim]))

        if futures[raw_urim].done():

            logger.debug("Raw URI-M {} is done".format(raw_urim))

            try:

                response = futures[raw_urim].result()

                http_status = response.status_code
                memento_content = bytes(response.text, 'utf8')
                memento_headers = dict(response.headers)    
                memento_headers["http-status"] = http_status

                # sometimes, via redirects, the different URI-Ms end up at the 
                # same raw URI-M
                logger.debug("There are {} URI-Ms leading to raw URI-M {}".format(
                    len(invert_raw_urimdata_mapping[raw_urim]), raw_urim
                ))
                for urim in invert_raw_urimdata_mapping[raw_urim]:
                    collectionmodel.addMemento(urim, memento_content, memento_headers)

                logger.debug("Removing raw URI-M {} from processing list".format(raw_urim))

            except ConnectionError as e:
                urim = invert_raw_urimdata_mapping[raw_urim]
                logger.warning("While acquiring memento at {} there was an error of {}, "
                    "this event is being recorded".format(urim, repr(e)))
                

                try:
                    errordata[urim] = repr(e)
                except TypeError as e:
                    logger.debug("errordata type: {}".format(type(errordata)))
                    logger.debug("e type: {}".format(type(e)))
                    logger.debug("repr(e): {}".format(repr(e)))
                    logger.warning("failed to record error for URI-M {}".format(urim))

            except TooManyRedirects as e:
                urim = invert_raw_urimdata_mapping[raw_urim]
                logger.warning("While acquiring memento at {} there was an error of {},"
                    "this event is being recorded".format(urim, repr(e)))
                errordata[urim] = repr(e)

            finally:
                logger.debug("Removing URI-M {} from the processing list".format(urim))
                completed_raw_urims.append(raw_urim)

        leftovers = list(set(raw_urims) - set(completed_raw_urims))

    for urim in errordata:
        errormsg = errordata[urim]
        collectionmodel.addMementoError(
            urim, b"", {}, bytes(errormsg, "utf8")
        )

    return collectionmodel

def get_collection_model_from_timemap(urits, working_directory):
    """This function fills a collection model using one or more TimeMaps
    stored in `urits`.
    """

    cm = CollectionModel(working_directory=working_directory)

    for urit in urits:

        logger.info("Acquiring collection model from TimeMap at [{}]".format(urit))

        r = requests.get(urit)

        http_status = r.status_code

        if http_status == 200:

            content = r.text
            headers = dict(r.headers)
            headers["http-status"] = http_status
            cm.addTimeMap(urit, content, headers)

            timemap = cm.getTimeMap(urit)

            urims = []

            for memento in timemap["mementos"]["list"]:
                urims.append(memento["uri"])

            fetch_and_save_memento_content(urims, cm)

        else:
            # TODO: Make an exception specific to this module for this case
            raise Exception("No TimeMap was acquired from URI-T {}".format(urit))

    return cm

def get_collection_model_from_datafile(datafile, working_directory):
    """This function generates a collection, including TimeMaps from a gold
    standard testing data file. It is used mainly for testing.
    """

    datafile = datafile[0]

    logger.info("building collection data from datafile {}".format(datafile))

    cm = CollectionModel(working_directory=working_directory)

    with open(datafile) as tsvfile:

        reader = csv.DictReader(tsvfile, delimiter='\t')
        timemaps_data = {}

        for row in reader:

            urir = "datafile-{}".format(row["id"])
            mdt = datetime.strptime(row["date"], "%Y%m%d%H%M%S")
            urim = row["URI"]

            # urim = generate_raw_urim(urim)

            # ontopic = row["label"]
            timemaps_data.setdefault(urir, []).append({
                "datetime": mdt,
                "uri": urim
            })

    for urir in timemaps_data:

        urit = "from-datafile::timemap::{}".format(urir)
        timemap_data = timemaps_data[urir]
        
        timemap_json = json.dumps(
            generate_timemap_from_timemap_data(urir, timemap_data),
            default=json_serial         
        )

        timemap_headers = {}
        cm.addTimeMap(urit, timemap_json, timemap_headers)

    urims = []

    for urit in cm.getTimeMapURIList():

        timemap = cm.getTimeMap(urit)

        for memento in timemap["mementos"]["list"]:
            # raw_urim = generate_raw_urim(memento["uri"])
            # urims.append(raw_urim)
            urims.append(memento["uri"])

    fetch_and_save_memento_content(urims, cm)

    return cm

def get_collection_model_from_directory(working_directory):
    """This function just loads a colleciton model from an existing
    directory. It is used mainly for testing.
    """
    
    cm = CollectionModel(working_directory)

    return cm
    
supported_input_types = {
    'warc': get_collection_model_from_warc,
    'archiveit': get_collection_model_from_archiveit,
    'timemap': get_collection_model_from_timemap,
    'goldtest': get_collection_model_from_datafile,
    'dir': get_collection_model_from_directory
}

def get_collection_model(input_type, arguments, working_directory):
    """This factory method takes `input_type` along with `arguments` and uses
    `supported_input_types` to run the correct function for producing
    the collection model filled via the different input methods,
    such as Archive-It collection ID or TimeMap.
    """

    logger.info("Using input type {}".format(input_type))
    logger.debug("input type arguments: {}".format(arguments))
    logger.debug("using supported input type {}".format(
        supported_input_types[input_type]))

    if input_type == "dir":

        input_dir = arguments[0]

        logger.info("Input directory {} has been chosen, using it instead of the "
            "working directory value of {}".format(input_dir, working_directory))

        return supported_input_types[input_type](input_dir)
    else:
        logger.info("Working directory {} will be used".format(working_directory))

        return supported_input_types[input_type](arguments, working_directory)
