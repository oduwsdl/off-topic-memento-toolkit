# -*- coding: utf-8 -*-

"""
otmt.timemap
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module allows one to parse a link-format TimeMap.
"""

import requests
from copy import deepcopy

from datetime import datetime

class MalformedLinkFormatTimeMap(Exception):
    """
        This class exists to indicate errors while processing TimeMaps in
        link format.
    """
    pass

def convert_LinkTimeMap_to_dict(timemap_text, skipErrors=False):
    """
        A function to convert the link format TimeMap text into a Python 
        dictionary that closely resembles the JSON specified at:
        http://mementoweb.org/guide/timemap-json/

        There is one difference: the value of the datetime attribute is
        an actual Python datetime object.

        One can set skipErrors to True in order to skip errors in processing
        the TimeMap, but use with caution as it can lead to unpredictable
        behavior.
    """

    def process_local_dict(local_dict, working_dict):

        first = False
        last = False

        for uri in local_dict:

            relation = local_dict[uri]["rel"]

            if relation == "original":
                working_dict["original_uri"] = uri

            elif relation == "timegate":
                working_dict["timegate_uri"] = uri

            elif relation == "self":
                working_dict["timemap_uri"] = {}
                working_dict["timemap_uri"]["link_format"] = uri

            elif "memento" in relation:
                working_dict.setdefault("mementos", {})

                if "first" in relation:
                    working_dict["mementos"]["first"] = {}
                    working_dict["mementos"]["first"]["uri"] = uri
                    first = True

                if "last" in relation:
                    working_dict["mementos"]["last"] = {}
                    working_dict["mementos"]["last"]["uri"] = uri
                    last = True

                working_dict["mementos"].setdefault("list", [])

                local_memento_dict = {
                    "datetime": None,
                    "uri": uri
                }

            if "datetime" in local_dict[uri]:

                mdt = datetime.strptime(local_dict[uri]["datetime"],
                    "%a, %d %b %Y %H:%M:%S GMT")

                local_memento_dict["datetime"] = mdt

                working_dict["mementos"]["list"].append(local_memento_dict)

                if first:
                    working_dict["mementos"]["first"]["datetime"] = mdt

                if last:
                    working_dict["mementos"]["last"]["datetime"] = mdt
                
        return working_dict


    dict_timemap = {}

    # current_char = ""
    uri = ""
    key = ""
    value = ""
    local_dict = {}
    state = 0
    charcount = 0

    for character in timemap_text:
        charcount += 1

        if state == 0:

            local_dict = {}
            uri = ""

            if character == '<':
                state = 1
            elif character.isspace():
                pass
            else:
                if not skipErrors:
                    raise MalformedLinkFormatTimeMap(
                        "issue at character {} while looking for next URI"
                        .format(charcount))

        elif state == 1:

            if character == '>':
                # URI should be saved by this point
                state = 2
                uri = uri.strip()
                local_dict[uri] = {}
            else:
                uri += character

        elif state == 2:

            if character == ';':
                state = 3

            elif character.isspace():
                pass

            else:
                if not skipErrors:
                    raise MalformedLinkFormatTimeMap(
                        "issue at character {} while looking for relation"
                        .format(charcount))

        elif state == 3:

            if character == '=':
                state = 4
            else:
                key += character

        elif state == 4:

            if character == ';':
                state = 3
            elif character == ',':
                state = 0

                process_local_dict(local_dict, dict_timemap)

            elif character == '"':
                state = 5
            elif character.isspace():
                pass
            else:
                if not skipErrors:
                    raise MalformedLinkFormatTimeMap(
                        "issue at character {} while looking for value"
                        .format(charcount))

        elif state == 5:

            if character == '"':
                state = 4

                key = key.strip()
                value = value.strip()
                local_dict[uri][key] = value
                key = ""
                value = ""

            else:
                value += character

        else:
            
            if not skipErrors:
                raise MalformedLinkFormatTimeMap(
                    "discovered unknown state while processing TimeMap")

    process_local_dict(local_dict, dict_timemap)

    return dict_timemap