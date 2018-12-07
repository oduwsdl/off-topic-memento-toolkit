# -*- coding: utf-8 -*-

"""
otmt.collectionmodel
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module exists to store the results of the different input types. Its
classes are designed to allow access to the data needed for measurement
calculations.

Note: The CollectionModel class also exists so that it can be subclassed
in the future. There is no reason that one should be limited to storing 
the input data as files and folders as I have here. A subclass that stores
the data as a WARC, or to a database is also possible, and such a 
subclass can be used with the measurement functions of timemap_measures,
provided that such a subclass has the same methods and parameters.
"""

import copy
import os
import hashlib
import json
import csv
import logging

import lxml.etree

from datetime import datetime
from datetime import date

from justext import justext, get_stoplist

from .timemap import convert_LinkTimeMap_to_dict

logger = logging.getLogger(__name__)

# Disabled this pylint rule because of too many false positives
# Ref: http://pylint-messages.wikidot.com/messages:e1101
# pylint: disable=no-member

# Thanks https://stackoverflow.com/questions/11875770/how-to-overcome-datetime-datetime-not-json-serializable
def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""

    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError ("Type %s not serializable" % type(obj))

class CollectionModelException(Exception):
    """An exception class to be used by the functions in this file so that the
    source of error can be detected.
    """
    pass

class CollectionModelMementoErrorException(CollectionModelException):
    """An exception indicating an error with accessing the given memento.
    """
    pass

class CollectionModelTimeMapErrorException(CollectionModelException):
    """An exception indicating an error with accessing the given TimeMap.
    """
    pass

class CollectionModelNoSuchMementoException(CollectionModelException):
    """An exception indicating that a given memento is not stored in 
    this object.
    """
    pass

class CollectionModelNoSuchTimeMapException(CollectionModelException):
    """An exception indicating that a given TimeMap is not stored in 
    this object.
    """
    pass

class CollectionModelBoilerPlateRemovalFailureException(CollectionModelException):
    """An exception indicating that boilerplate removal failed for a given memento.
    """
    pass

class CollectionModel:
    """
        This class exists because the dict for keeping track of
        the mementos and timemaps was getting too unweildy and often 
        required that certain calling functions occur in order.

        This class can also be subclassed to store memento data in
        another way, such as a database or WARC.
    """

    # TODO: add functions for storing metadata, like for saving a collection id, name, etc.

    def __init__(self, working_directory):

        self.working_directory = working_directory
        self.timemap_directory = "{}/timemaps".format(working_directory)
        self.timemap_errors_directory = "{}/timemap_errors".format(working_directory)

        self.memento_directory = "{}/mementos".format(working_directory)
        self.memento_errors_directory = "{}/memento_errors".format(working_directory)

        self.collection_timemaps = {}

        self.urimap = {
            "timemaps": {},
            "mementos": {},
            "memento-errors": {}
        }

        if not os.path.exists(working_directory):
            os.makedirs(self.working_directory)
            os.makedirs(self.timemap_directory)
            os.makedirs(self.memento_directory)
            os.makedirs(self.memento_errors_directory)
        else:
            self.load_data_from_directory()

        self.timemap_metadatafile = open("{}/metadata.csv".format(
            self.timemap_directory
        ), 'a')

        self.timemap_csvwriter = csv.writer(self.timemap_metadatafile)

        self.memento_metadatafile = open("{}/metadata.csv".format(
            self.memento_directory
        ), 'a')

        self.memento_csvwriter = csv.writer(self.memento_metadatafile)

        self.memento_errors_metadatafile = open("{}/metadata.csv".format(
            self.memento_errors_directory
        ), 'a')

        self.memento_errors_csvwriter = csv.writer(self.memento_errors_metadatafile)

    def __del__(self):

        self.timemap_metadatafile.close()
        self.memento_metadatafile.close()
        self.memento_errors_metadatafile.close()

    def load_data_from_directory(self):
        """
            Loads data from a previous run of this class.
        """

        logger.info("loading data from directory {}".format(self.timemap_directory))

        timemap_metadatafile = open("{}/metadata.csv".format(
            self.timemap_directory
        ))

        memento_metadatafile = open("{}/metadata.csv".format(
            self.memento_directory
        ))

        memento_errors_metadatafile = open("{}/metadata.csv".format(
            self.memento_errors_directory
        ))

        logger.debug("acquiring data using {}".format(timemap_metadatafile))

        timemap_reader = csv.reader(timemap_metadatafile)
        memento_reader = csv.reader(memento_metadatafile)
        memento_error_reader = csv.reader(memento_errors_metadatafile)

        for row in timemap_reader:

            logger.debug("reading TimeMap data row {}".format(row))

            urit = row[0]
            filename_digest = row[1]

            self.urimap["timemaps"][urit] = filename_digest

            with open("{}/timemaps/{}.json".format(
                self.working_directory, filename_digest)) as jsonin:

                tmdata = json.load(jsonin)

                try:
                    mdt = tmdata['mementos']['first']['datetime']
                except KeyError:
                    logger.exception("failed to read TimeMap for URI-T {}, skipping...".format(urit))
                    continue
                
                tmdata['mementos']['first']['datetime'] = datetime.strptime(
                    mdt, "%Y-%m-%dT%H:%M:%S"
                )

                mdt = tmdata['mementos']['last']['datetime']

                tmdata['mementos']['last']['datetime'] = datetime.strptime(
                    mdt, "%Y-%m-%dT%H:%M:%S"
                )

                mementolist = copy.deepcopy(tmdata['mementos']['list'])

                tmdata['mementos']['list'] = []

                for entry in mementolist:

                    tmdata['mementos']['list'].append(
                        {
                        "uri": entry['uri'],
                        "datetime": datetime.strptime( entry['datetime'], "%Y-%m-%dT%H:%M:%S" )
                        }
                    )

                self.collection_timemaps[urit] = tmdata

        for row in memento_reader:
            urim = row[0]
            filename_digest = row[1]

            self.urimap["mementos"][urim] = filename_digest

        for row in memento_error_reader:
            urim = row[0]
            filename_digest = row[1]

            self.urimap["memento-errors"][urim] = filename_digest

        timemap_metadatafile.close()
        memento_metadatafile.close()
        memento_errors_metadatafile.close()

    def addTimeMap(self, urit, content, headers):
        """Adds a TimeMap to the object, parsing it if it is in link-format
        and then stores the TimeMap as a dict in memory and JSON on disk.

        If JSON is given as `content`, then it is just converted to a dict.
        """

        filename_digest = hashlib.sha3_256(bytes(urit, "utf8")).hexdigest()

        if type(content) == str:

            try:
                json_timemap = json.loads(content)
                fdt = datetime.strptime(
                    json_timemap["mementos"]["first"]["datetime"],
                    "%Y-%m-%dT%H:%M:%S"
                )
                ldt = datetime.strptime(
                    json_timemap["mementos"]["last"]["datetime"],
                    "%Y-%m-%dT%H:%M:%S"
                )

                json_timemap["mementos"]["first"]["datetime"] = fdt
                json_timemap["mementos"]["last"]["datetime"] = ldt

                updated_memlist = []

                for mem in json_timemap["mementos"]["list"]:
                    mdt = datetime.strptime(
                        mem["datetime"],
                        "%Y-%m-%dT%H:%M:%S"
                    )

                    uri = mem["uri"]
                    updated_memlist.append({
                        "datetime": mdt,
                        "uri": uri
                    })

                json_timemap["mementos"]["list"] = updated_memlist

            except json.JSONDecodeError:
                json_timemap = convert_LinkTimeMap_to_dict(content, skipErrors=True)

            self.collection_timemaps[urit] = json_timemap

            with open("{}/{}_headers.json".format(
                self.timemap_directory, filename_digest), 'w') as out:
                json.dump(headers, out, default=json_serial, indent=4)
                
            with open("{}/{}.json".format(
                self.timemap_directory, filename_digest), 'w') as out:
                json.dump(json_timemap, out, default=json_serial, indent=4)

            with open("{}/{}.orig".format(
                self.timemap_directory, filename_digest), 'w') as out:
                out.write(content)

            self.urimap["timemaps"][urit] = filename_digest

            self.timemap_csvwriter.writerow([urit, filename_digest])

        else:
            raise CollectionModelException(
                "Unsupported TimeMap Type, must be str in link format"
                )

    def getTimeMap(self, urit):
        """
            Returns the dict form of TimeMap at `urit` provided that it
            was previously stored via `addTimeMap`.
        """

        # TODO: there may be too much data for low memory systems
        return copy.deepcopy( self.collection_timemaps[urit] )

    def addMemento(self, urim, content, headers):
        """Adds Memento `content` specified by `urim` to the object, along 
        with its headers.
        """

        filename_digest = hashlib.sha3_256(bytes(urim, "utf8")).hexdigest()

        with open("{}/{}_headers.json".format(
            self.memento_directory, filename_digest), 'w') as out:
            json.dump(headers, out, default=json_serial)

        with open("{}/{}.orig".format(
            self.memento_directory, filename_digest), 'wb') as out:
            out.write(content)

        self.urimap["mementos"][urim] = filename_digest

        self.memento_csvwriter.writerow([urim, filename_digest])

    def addMementoError(self, urim, content, headers, errorinformation):
        """Associates `errorinformation` with memento specified by `urim` to
        the object, `content` and `headers` can also be stored from the given
        input transaction. If there are no headers or content, use content=""
        and headers={}.
        """

        filename_digest = hashlib.sha3_256(bytes(urim, "utf8")).hexdigest()

        with open("{}/{}_headers.json".format(
            self.memento_errors_directory, filename_digest), 'w') as out:
            json.dump(headers, out, default=json_serial, indent=4)

        with open("{}/{}.orig".format(
            self.memento_errors_directory, filename_digest), 'wb') as out:
            out.write(content)

        with open("{}/{}_error_info.txt".format(
            self.memento_errors_directory, filename_digest), 'wb') as out:
            out.write(errorinformation)

        self.urimap["memento-errors"][urim] = filename_digest

        self.memento_errors_csvwriter.writerow([urim, filename_digest])

    def getMementoContent(self, urim):
        """Returns the HTTP entity of memento at `urim` provided that it
        was previously stored via `addMemento`.

        If no data was stored via `addMemento` for `urim`, then
        `CollectionModelNoSuchMementoException` is thrown.

        If data was stored via `addMementoError` for `urim`, then
        `CollectionModelMementoErrorException` is thrown.
        """

        if urim in self.urimap["memento-errors"]:
            raise CollectionModelMementoErrorException

        try:

            filename_digest = self.urimap["mementos"][urim]

            with open("{}/{}.orig".format(
                self.memento_directory, filename_digest), 'rb') as fileinput:
                data = fileinput.read()

        except KeyError:
            err_msg = "The URI-M [{}] is not saved in this " \
                "collection model".format(urim)

            logger.error(err_msg)

            raise CollectionModelNoSuchMementoException(err_msg)

        return data

    def getMementoErrorInformation(self, urim):
        """Returns the error information associated with `urim`, provided that
        it was previously stored via `addMementoError`.

        If no data was stored via `addMemento` for `urim`, then
        `CollectionModelNoSuchMementoException` is thrown.
        """

        if urim in self.urimap["memento-errors"]:

            filename_digest = self.urimap["memento-errors"][urim]

            with open("{}/{}_error_info.txt".format(
                self.memento_errors_directory, filename_digest), 'rb') as fileinput:
                data = fileinput.read()

        else:

            if urim in self.urimap["mementos"]:
                return None
            else:
                err_msg = "The URI-M [{}] is not saved in this " \
                    "collection model".format(urim)

                logger.error(err_msg)

                raise CollectionModelNoSuchMementoException(err_msg)

        return data

    def getMementoContentWithoutBoilerplate(self, urim):
        """Returns the HTTP entity of memento at `urim` with all boilerplate
        removed, provided that it was previously stored via `addMemento`.

        If no data was stored via `addMemento` for `urim`, then
        `CollectionModelNoSuchMementoException` is thrown.

        If data was stored via `addMementoError` for `urim`, then
        `CollectionModelMementoErrorException` is thrown.

        If the boilerplate removal process produces an error for `urim`,
        then CollectionModelBoilerPlateRemovalFailureException is thrown.
        """

        if urim in self.urimap["memento-errors"]:
            raise CollectionModelMementoErrorException(
                "Errors were recorded for URI-M {}".format(urim))

        content_without_boilerplate = None

        logger.debug("Acquiring memento content without boilerplate for {}".format(urim))

        try:

            filename_digest = self.urimap["mementos"][urim]

            boilerplate_filename = "{}/{}.orig.noboilerplate".format(
                self.memento_directory, filename_digest)

            if not os.path.exists(boilerplate_filename):

                logger.debug("Boilerplate content has not yet been "
                    "generated, generating...")

                with open("{}/{}.orig".format(
                    self.memento_directory, filename_digest), 'rb') as fileinput:
                    data = fileinput.read()

                try:
                    paragraphs = justext(data, get_stoplist('English'))


                    with open(boilerplate_filename, 'wb') as bpfile:
                        
                        for paragraph in paragraphs:
                            bpfile.write(bytes("{}\n".format(paragraph.text), "utf8"))

                except (lxml.etree.ParserError, lxml.etree.XMLSyntaxError) as e:
                    raise CollectionModelBoilerPlateRemovalFailureException(repr(e))

            with open(boilerplate_filename, 'rb') as bpfile:
                content_without_boilerplate = bpfile.read()
                    
        except KeyError:

            # logger.debug("urimap['mementos']: {}".format(self.urimap["mementos"]))

            logger.error("The URI-M [{}] is not saved in this collection model".format(
                    urim))

            raise CollectionModelNoSuchMementoException(
                "The URI-M [{}] is not saved in this collection model".format(
                    urim))

        return content_without_boilerplate

    def getHeaders(self, objecttype, uri):
        """Returns the headers associated with URI `uri`.
        `objecttype` must be set to timemaps if headers
        for a TimeMap are desired.
        """

        if objecttype == "timemaps":
            directory = self.timemap_directory
        else:
            directory = self.memento_directory

        try:

            filename_digest = self.urimap[objecttype][uri]

            with open("{}/{}_headers.json".format(
                directory, filename_digest)) as fileinput:
                data = json.load(fileinput)

        except KeyError:
            raise CollectionModelException(
                "The URI [{}] headers are not saved "
                "in this collection model".format(
                    uri))

        return data

    def getMementoHeaders(self, urim):
        """Returns the headers associated with memento at `urim`.
        """

        if urim in self.urimap["memento-errors"]:
            raise CollectionModelMementoErrorException

        return self.getHeaders("mementos", urim)

    def getTimeMapHeaders(self, urit):
        """Returns the headers associated with TimeMap at `urit`.
        """

        return self.getHeaders("timemaps", urit)

    def getMementoURIList(self):
        """Returns a list of all URI-Ms stored in this object."""

        return copy.deepcopy(
            list(self.urimap["mementos"].keys())
        )

    def getTimeMapURIList(self):
        """Returns a list of all URI-Ts stored in this object."""

        return copy.deepcopy(
            list(self.urimap["timemaps"].keys())
        )
