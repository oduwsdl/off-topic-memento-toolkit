import copy
import os
import hashlib
import json

from datetime import datetime
from datetime import date

from offtopic.timemap import convert_LinkTimeMap_to_dict

# Thanks https://stackoverflow.com/questions/11875770/how-to-overcome-datetime-datetime-not-json-serializable
def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""

    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError ("Type %s not serializable" % type(obj))

class CollectionModelException(Exception):
    pass

class CollectionModel:

    data_model = {}

    # TODO: add functions for metadata, for setting a collection id, name, etc.

    def __init__(self, working_directory=None):

        if working_directory:
            self.working_directory = working_directory
            self.timemap_directory = "{}/timemaps".format(working_directory)
            self.memento_directory = "{}/mementos".format(working_directory)
        else:
            # TODO: what if we don't supply a working directory?
            working_directory = None

        if not os.path.exists(working_directory):
            os.makedirs(self.working_directory)
            os.makedirs(self.timemap_directory)
            os.makedirs(self.memento_directory)
        else:
            # TODO: load data from the working directory if it already exists
            pass

    def addTimeMap(self, urit, content, headers):

        filename_digest = hashlib.sha3_256(bytes(urit, "utf8")).hexdigest()

        self.data_model.setdefault("timemaps", {})

        if type(content) == str:

            json_timemap = convert_LinkTimeMap_to_dict(content, skipErrors=True)

            self.data_model["timemaps"][urit] = json_timemap

            with open("{}/{}.json".format(
                self.timemap_directory, filename_digest), 'w') as out:
                json.dump(json_timemap, out, default=json_serial)

            with open("{}/{}.orig".format(
                self.timemap_directory, filename_digest), 'w') as out:
                out.write(content)

        else:
            raise CollectionModelException(
                "Unsupported TimeMap Type, must be str in link format"
                )

    def getTimeMap(self, urit):
        return copy.deepcopy( self.data_model["timemaps"][urit] )


    def addMemento(self, urim, content, headers):

        self.data_model.setdefault("mementos", {})

        filename = save_uri_to_disk(urim, content, headers, self.working_directory)

        self.data_model["mementos"][urim]["filecontent"]

    def save_uri_to_disk(self, content, headers):

        self.working_directory
