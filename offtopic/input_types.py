import logging
import json

from datetime import datetime
from datetime import date

from warcio.archiveiterator import ArchiveIterator

from offtopic import CollectionModel

def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""

    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError ("Type %s not serializable" % type(obj))

def extract_urim_mdt_content_from_record(record):

    logger = logging.getLogger(__name__)

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
        "from-warc::timegate::{}".format(urir)
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

    timemap_dict["mementos"]["first"] = sorted_list_for_sorting[0]
    timemap_dict["mementos"]["last"] = sorted_list_for_sorting[-1]

    return timemap_dict


def get_collection_model_from_warc(warcfiles, working_directory):

    logger = logging.getLogger(__name__)

    logger.warn("Only HTML entities are extracted from warcfiles")

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

def get_collection_model_from_archiveit(archiveit_cid, working_directory):



    pass

def get_collection_model_from_timemap(urit, working_directory):
    pass

def get_collection_model_from_datafile(datafile, working_directory):
    pass

def get_collection_model_from_directory(working_directory):
    
    cm = CollectionModel(working_directory)

    return cm
    
supported_input_types = {
    'warc': get_collection_model_from_warc,
    'archiveit': get_collection_model_from_archiveit,
    'timemap': get_collection_model_from_timemap,
    'datafile': get_collection_model_from_datafile,
    'dir': get_collection_model_from_directory
}

def get_collection_model(input_type, arguments, directory):
    
    logger = logging.getLogger(__name__)    

    logger.info("Using input type {}".format(input_type))
    logger.debug("input type arguments: {}".format(arguments))
    logger.debug("using supported input type {}".format(
        supported_input_types[input_type]))

    if input_type == "dir":
        return supported_input_types[input_type](directory)
    else:
        return supported_input_types[input_type](arguments, directory)
