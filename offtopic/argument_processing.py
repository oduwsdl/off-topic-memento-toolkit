import argparse
import sys
import logging
import logging.config

from .topic_processor import supported_measures
from .input_types import supported_input_types
from .output_types import supported_output_types

def process_similarity_measure_inputs(input_argument):
    
    input_measures = input_argument.split(',')

    measures_used = {}

    for measure in input_measures:

        try:
            if '=' in measure:
                measure_name, threshold = measure.split('=')
                
                if measure_name not in supported_measures:
                    raise argparse.ArgumentTypeError(
                        "measure '{}' is not supported at this time".format(
                            measure_name)
                            )

                measures_used[measure_name] = threshold

            else:
                measures_used[measure] = \
                    supported_measures[measure]['default_threshold']
        except KeyError:
            raise argparse.ArgumentTypeError(
                "measure '{}' is not supported at this time".format(
                    measure
                    )
                )

    return measures_used

def process_output_types(input_argument):

    output_type = input_argument

    if output_type in supported_output_types:
        return output_type
    else:
        raise argparse.ArgumentTypeError(
            "{} is not a supported output type, supported output types are "
            "{}".format(output_type, list(supported_output_types.keys()))
        )

def process_input_types(input_argument):

    if '=' not in input_argument:
        raise argparse.ArgumentTypeError(
            "no required argument supplied for input type {}\n\n"
            "Examples:\n"
            "for an Archive-It collection use something like\n"
            "-i archiveit=3639\n\n"
            "for [EXPERIMENTAL] WARCs use (separate with commas, but no spaces)\n"
            "-i warc=myfile.warc.gz,myfile2.warc.gz\n\n"
            "for a TimeMap use (separate with commas, but not spaces)\n"
            "-i timemap=http://archive.example.org/timemap/http://example.com"
            .format(input_argument)
            )

    input_type, argument = input_argument.split('=') 

    if input_type not in supported_input_types:
        raise argparse.ArgumentTypeError(
            "{} is not a supported input type, supported types are {}".format(
                input_type, list(supported_input_types.keys())
                )
            )

    if ',' in argument:
        arguments = argument.split(',')
    else:
        arguments = [ argument ]

    return input_type, arguments

def get_logger(appname, loglevel, logfile):

    logger = logging.getLogger(appname)

    if logfile == sys.stdout:
        logging.basicConfig( 
            format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            level=loglevel)
    else:
        logging.basicConfig( 
            format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            level=loglevel,
            filename=logfile)

    return logger

def calculate_loglevel(verbose):
  
    if verbose:
        return logging.DEBUG
    else:
        return logging.INFO