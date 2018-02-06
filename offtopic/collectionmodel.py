import copy
import os
import hashlib
import json
import csv
import logging

from datetime import datetime
from datetime import date

from offtopic.timemap import convert_LinkTimeMap_to_dict

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
    pass

class CollectionModel:

    # TODO: add functions for metadata, for setting a collection id, name, etc.

    def __init__(self, working_directory):

        self.working_directory = working_directory
        self.timemap_directory = "{}/timemaps".format(working_directory)
        self.memento_directory = "{}/mementos".format(working_directory)

        self.collection_timemaps = {}

        self.urimap = {
            "timemaps": {},
            "mementos": {}
        }

        if not os.path.exists(working_directory):
            os.makedirs(self.working_directory)
            os.makedirs(self.timemap_directory)
            os.makedirs(self.memento_directory)
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

    def __del__(self):

        self.timemap_metadatafile.close()
        self.memento_metadatafile.close()

    def load_data_from_directory(self):

        logger = logging.getLogger(__name__)

        logger.info("loading data from directory {}".format(self.timemap_directory))

        timemap_metadatafile = open("{}/metadata.csv".format(
            self.timemap_directory
        ))

        memento_metadatafile = open("{}/metadata.csv".format(
            self.memento_directory
        ))

        timemap_reader = csv.reader(timemap_metadatafile)
        memento_reader = csv.reader(memento_metadatafile)

        for row in timemap_reader:
            urit = row[0]
            filename_digest = row[1]

            self.urimap["timemaps"][urit] = filename_digest

            with open("{}/timemaps/{}.json".format(
                self.working_directory, filename_digest)) as jsonin:

                tmdata = json.load(jsonin)

                mdt = tmdata['mementos']['first']['datetime']
                
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

    def addTimeMap(self, urit, content, headers):

        filename_digest = hashlib.sha3_256(bytes(urit, "utf8")).hexdigest()

        if type(content) == str:

            json_timemap = convert_LinkTimeMap_to_dict(content, skipErrors=True)

            self.collection_timemaps[urit] = json_timemap

            with open("{}/{}_headers.json".format(
                self.timemap_directory, filename_digest), 'w') as out:
                json.dump(headers, out, default=json_serial)
                
            with open("{}/{}.json".format(
                self.timemap_directory, filename_digest), 'w') as out:
                json.dump(json_timemap, out, default=json_serial)

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
        # TODO: there may be too much data for low memory systems
        return copy.deepcopy( self.collection_timemaps[urit] )

    def addMemento(self, urim, content, headers):

        filename_digest = hashlib.sha3_256(bytes(urim, "utf8")).hexdigest()

        with open("{}/{}_headers.json".format(
            self.memento_directory, filename_digest), 'w') as out:
            json.dump(headers, out, default=json_serial)

        with open("{}/{}.orig".format(
            self.memento_directory, filename_digest), 'wb') as out:
            out.write(content)

        self.urimap["mementos"][urim] = filename_digest

        self.memento_csvwriter.writerow([urim, filename_digest])

    def getMementoContent(self, urim):

        try:

            filename_digest = self.urimap["mementos"][urim]

            with open("{}/{}.orig".format(
                self.memento_directory, filename_digest), 'rb') as fileinput:
                data = fileinput.read()

        except KeyError:
            raise CollectionModelException(
                "The URI-M [{}] is not saved in this collection model".format(
                    urim))

        return data

    def getHeaders(self, objecttype, uri):

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

        return self.getHeaders("mementos", urim)

    def getTimeMapHeaders(self, urit):

        return self.getHeaders("timemaps", urit)

    def getMementoURIList(self):

        return copy.deepcopy(
            list(self.urimap["mementos"].keys())
        )

    def getTimeMapURIList(self):

        return copy.deepcopy(
            list(self.urimap["timemaps"].keys())
        )