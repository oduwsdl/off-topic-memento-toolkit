import sys
import logging
import json
import multiprocessing
import requests
import csv

from datetime import datetime
from datetime import date

from requests_futures.sessions import FuturesSession
from requests.exceptions import ConnectionError, TooManyRedirects
from warcio.archiveiterator import ArchiveIterator

from offtopic import CollectionModel
from offtopic import ArchiveItCollection

logger = logging.getLogger(__name__)

cpu_count = multiprocessing.cpu_count()

def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""

    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError ("Type %s not serializable" % type(obj))

def extract_urim_mdt_content_from_record(record):

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

    urit_list = []

    for urir in seed_uris:
        urit = "http://wayback.archive-it.org/{}/timemap/link/{}".format(
            cid, urir
        )

        urit_list.append(urit)  

    return urit_list

def get_uri_responses(session, uris):

    futures = {}

    for uri in uris:

        logger.debug("fetching uri {}".format(uri))

        futures[uri] = session.get(uri)

    return futures

def list_generator(input_list):

    while len(input_list) > 0:
        for item in input_list:
            yield item

def get_collection_model_from_archiveit(archiveit_cid, working_directory):

    archiveit_cid = archiveit_cid[0]

    logger.info("Acquiring Archive-It collection {}".format(
        archiveit_cid
    ))

    # logger.setLevel(logging.INFO)

    logger.error("log level is set to {} == {}".format(logger.level, logging.INFO))
    logger.debug("acquiring metadata about Archive-It colleciton {}".format(
        archiveit_cid
    ))

    aic = ArchiveItCollection(archiveit_cid, working_directory=working_directory,
        logger=logger)

    logger.debug("creating collection model")

    cm = CollectionModel(working_directory)

    logger.debug("generating list of seed URIs")

    seed_uris = aic.list_seed_uris()

    logger.debug("seed URIs: {}".format(
        seed_uris
    ))

    urits = generate_archiveit_urits(archiveit_cid, seed_uris)

    with FuturesSession(max_workers=cpu_count) as session:
        futures = get_uri_responses(session, urits)

    working_uri_list = list(futures.keys())

    for urit in list_generator(working_uri_list):

        logging.debug("checking if URI {} is done downloading".format(urit))

        if futures[urit].done():

            logger.debug("URI {} is done, extracting content".format(urit))

            try:
                response = futures[urit].result()

                http_status = response.status_code

                if http_status == 200:

                    timemap_content = response.text
                    timemap_headers = dict(response.headers)
                    timemap_headers["http-status"] = http_status

                    cm.addTimeMap(urit, timemap_content, timemap_headers)

                # TODO: else store connection errors in CollectionModel
                working_uri_list.remove(urit)
            
            except ConnectionError:
                # TODO: store connection errors in CollectionModel
                working_uri_list.remove(urit)

            except TooManyRedirects:
                # TODO: store connection errors in CollectionModel
                working_uri_list.remove(urit)

    urims = []

    for urit in cm.getTimeMapURIList():

        timemap = cm.getTimeMap(urit)
        for memento in timemap["mementos"]["list"]:
            raw_urim = memento["uri"].replace('/http', 'id_/http')
            urims.append(raw_urim)

    fetch_mementos(urims, cm)
                
    return cm

def fetch_mementos(urimlist, collectionmodel):

    with FuturesSession(max_workers=cpu_count) as session:
        futures = get_uri_responses(session, urimlist)

    working_uri_list = list(futures.keys())

    for urim in list_generator(working_uri_list):

        if futures[urim].done():

            try:
                response = futures[urim].result()

                http_status = response.status_code

                if http_status == 200:

                    memento_content = bytes(response.text, 'utf8')
                    memento_headers = dict(response.headers)
                    memento_headers["http-status"] = http_status

                    collectionmodel.addMemento(
                        urim, memento_content, memento_headers)

                # TODO: else store connection errors in CollectionModel
                working_uri_list.remove(urim)
            
            except ConnectionError:
                # TODO: store connection errors in CollectionModel
                working_uri_list.remove(urim)

            except TooManyRedirects:
                # TODO: store connection errors in CollectionModel
                working_uri_list.remove(urim)

def get_collection_model_from_timemap(urit, working_directory):
    
    cm = CollectionModel(working_directory=working_directory)

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

        fetch_mementos(urims, cm)

    else:
        # TODO: Make an exception specific to this module for this case
        raise Exception("No TimeMap was acquired from URI-T {}".format(urit))

def get_collection_model_from_datafile(datafile, working_directory):

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
            urims.append(memento["uri"])

    fetch_mementos(urims, cm)

    return cm


def get_collection_model_from_directory(working_directory):
    
    cm = CollectionModel(working_directory)

    return cm
    
supported_input_types = {
    'warc': get_collection_model_from_warc,
    'archiveit': get_collection_model_from_archiveit,
    'timemap': get_collection_model_from_timemap,
    'goldtest': get_collection_model_from_datafile,
    'dir': get_collection_model_from_directory
}

def get_collection_model(input_type, arguments, directory):

    logger.info("Using input type {}".format(input_type))
    logger.debug("input type arguments: {}".format(arguments))
    logger.debug("using supported input type {}".format(
        supported_input_types[input_type]))

    if input_type == "dir":
        return supported_input_types[input_type](directory)
    else:
        return supported_input_types[input_type](arguments, directory)
