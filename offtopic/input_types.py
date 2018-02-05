import logging

from offtopic import CollectionModel

def get_collection_model_from_warc(warcfiles, working_directory):
    pass

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
