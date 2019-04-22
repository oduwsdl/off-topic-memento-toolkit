# -*- coding: utf-8 -*-

"""
otmt.measuremodel
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module exists to store the results of the different measures. Its classes
also handle output of those measures to different output types.

Note: The MeasureModel class also exists so that it can be subclassed
in the future. There is no reason that one should be limited to storing 
the input data as a dictionary as I have here. A subclass that stores
the data as a WARC, or to a database is also possible, and such a 
subclass can be used with the measurement functions of timemap_measures,
provided that such a subclass has the same methods and parameters.
"""

import json
import csv

class MeasureModelException(Exception):
    """An exception class to be used by the functions in this file so that the
    source of error can be detected.
    """
    pass

class MeasureModelNoSuchMemento(MeasureModelException):
    """An exception class to be used when the requested Memento is not stored
    by an instance of `MeasureModel`.
    """
    pass

class MeasureModelNoSuchTimeMap(MeasureModelException):
    """An exception class to be used when the requested TimeMap is not stored
    by an instance of `MeasureModel`.
    """
    pass

class MeasureModelNoSuchMeasure(MeasureModelException):
    """An exception class to be used when the requested measure is not stored
    by an instance of `MeasureModel`.
    """
    pass

class MeasureModelNoSuchMeasureType(MeasureModelException):
    """An exception class to be used when the requested measure type is not
    stored by an instance of `MeasureModel`.
    """
    pass

class MeasureModel:
    """
        This class exists because the data structure for keeping track
        of the scores and measures was getting too unwieldy. It seems
        awfully complex for its job, but I hadn't found an alternative yet.

        One could conceivably replace it with a dict, but then everything
        managed here would need to be managed in the calling code, making
        them more tightly coupled than I wanted.
    """

    def __init__(self):
        self.scoremodel = {}
        self.timemap_access_errormodel = {}
        self.memento_access_errormodel = {}
        self.memento_measure_errormodel = {}
        self.mementos_to_timemaps = {}
        self.measures = []

    def initialize_scoremodel_for_urit_urim(self, urit, urim):
        """Sets up the data structure for scores of URI-Ts and URI-Ms."""

        self.scoremodel.setdefault(urit, {})
        self.scoremodel[urit].setdefault(urim, {})

        self.scoremodel[urit][urim].setdefault("raw simhash value", None)
        self.scoremodel[urit][urim].setdefault("content length", None)

        self.mementos_to_timemaps[urim] = urit
        self.timemap_access_errormodel[urit] = None

        self.memento_access_errormodel.setdefault(urit, {})
        self.memento_access_errormodel[urit].setdefault(urim, None)

    def initialize_scoremodel_for_keys(self, urit, urim, measuretype, measure):
        """Sets up the data structure for scores and errors of
         URI-Ts and URI-Ms."""
        self.initialize_scoremodel_for_urit_urim(urit, urim)

        self.scoremodel[urit][urim].setdefault(measuretype, {})
        self.scoremodel[urit][urim][measuretype].setdefault(measure, {})
        self.scoremodel[urit][urim][measuretype][measure].setdefault(measure, {})
        self.scoremodel[urit][urim][measuretype][measure].setdefault("comparison score", None)
        self.scoremodel[urit][urim][measuretype][measure].setdefault("stemmed", None)
        self.scoremodel[urit][urim][measuretype][measure].setdefault("tokenized", None)
        self.scoremodel[urit][urim][measuretype][measure].setdefault("removed boilerplate", None)
        self.scoremodel[urit][urim][measuretype][measure].setdefault("topic status", None)

        self.scoremodel[urit][urim]["overall topic status"] = None

        self.memento_measure_errormodel.setdefault(urit, {})
        self.memento_measure_errormodel[urit].setdefault(urim, {})
        self.memento_measure_errormodel[urit][urim].setdefault(measuretype, {})
        self.memento_measure_errormodel[urit][urim][measuretype].setdefault(measure, None)

        if (measuretype, measure) not in self.measures:
            self.measures.append( (measuretype, measure) )

    def set_score(self, urit, urim, measuretype, measure, score):
        """Sets the `score` for a given `urim`, belonging to a given `urit`, 
        associated with a given `measuretype` and `measure`.
        """

        self.initialize_scoremodel_for_keys(urit, urim, measuretype, measure)
        self.scoremodel[urit][urim][measuretype][measure]["comparison score"] = score

    def handle_key_error(self, exception, urit, urim, measuretype, measure):
        """Handles the different types of KeyError issues that result from
        mistakes in calling the methods of this class.
        """
        key = str(exception).strip("'")

        if key == urit:
            raise MeasureModelNoSuchTimeMap(urit)
        elif key == urim:
            raise MeasureModelNoSuchMemento(urim)
        elif key == measuretype:
            raise MeasureModelNoSuchMeasureType(measuretype)
        elif key == measure:
            raise MeasureModelNoSuchMeasure(measure)
        else:
            raise exception

    def get_score(self, urit, urim, measuretype, measure):
        """Gets the `score` for a given `urim`, belonging to a given `urit`, 
        associated with a given `measuretype` and `measure`.
        """

        score = None

        try: 
            score = self.scoremodel[urit][urim][measuretype][measure]["comparison score"]
        except KeyError as e:
            self.handle_key_error(e, urit, urim, measuretype, measure)

        return score

    def set_content_length(self, urit, urim, content_length):
        """Sets the `content_length` for a given `urim`, belonging to a given
        `urit`.
        """

        self.initialize_scoremodel_for_urit_urim(urit, urim)
        self.scoremodel[urit][urim]["content length"] = content_length

    def get_content_length(self, urit, urim):
        """Gets the content length for a given `urim`, belonging to a given
        `urit`.
        """

        content_length = None

        try:
            if "content length" in self.scoremodel[urit][urim]:
                content_length = self.scoremodel[urit][urim]["content length"]
            else:
                content_length = None
        except KeyError as e:
            self.handle_key_error(e, urit, urim, None, None)

        return content_length

    def set_simhash(self, urit, urim, simhash_value):
        """Sets the `simhash_value` for a given `urim`, belonging to a given
        `urit`.
        """

        self.initialize_scoremodel_for_urit_urim(urit, urim)
        self.scoremodel[urit][urim]["raw simhash value"] = simhash_value

    def set_memento_datetime(self, urit, urim, memento_datetime):
        """Sets the `memento-datetime` value for a given `urim`, belonging to
        a given `urit`.
        """
        self.initialize_scoremodel_for_urit_urim(urit, urim)
        self.scoremodel[urit][urim]["memento-datetime"] = memento_datetime

    def set_language(self, urit, urim, language):
        """Sets the `language` for a given `urim`, belonging to a given
        `urit`.
        """

        self.initialize_scoremodel_for_urit_urim(urit, urim)
        self.scoremodel[urit][urim]["language"] = language

    def get_simhash(self, urit, urim):
        """Gets the simhash value for a given `urim`, belonging to a given
        `urit`.
        """

        simhash_value = None

        try:
            if "raw simhash value" in self.scoremodel[urit][urim]:
                simhash_value = self.scoremodel[urit][urim]["raw simhash value"]
            else:
                simhash_value = None
        except KeyError as e:
            self.handle_key_error(e, urit, urim, None, None)

        return simhash_value

    def get_language(self, urit, urim):
        """Gets the language value for a given `urim`, belonging to a given
        `urit`.
        """

        language_value = None

        try:
            if "language" in self.scoremodel[urit][urim]:
                language_value = self.scoremodel[urit][urim]["language"]
            else:
                language_value = None
        except KeyError as e:
            self.handle_key_error(e, urit, urim, None, None)

        return language_value

    def get_memento_datetime(self, urit, urim):
        """Gets the memento-datetime for a given `urim`, belonging to a given
        `urit`.
        """

        memento_datetime = None

        try:
            if "memento-datetime" in self.scoremodel[urit][urim]:
                memento_datetime = self.scoremodel[urit][urim]["memento-datetime"]
            else:
                memento_datetime = None
        except KeyError as e:
            self.handle_key_error(e, urit, urim, None, None)

        return memento_datetime

    def set_TimeMap_access_error(self, urit, errormsg):
        """Associates `errormsg` with a given `urit` when the error involves
        failure to access (i.e., download) a TimeMap.
        """
        
        self.timemap_access_errormodel[urit] = errormsg

        # make sure there is an entry in the scoremodel for get_TimeMap_URIs
        self.scoremodel.setdefault(urit, {})

    def get_TimeMap_access_error_message(self, urit):
        """Gets the error message associated with a given `urit` when the
        error involves failure to access (i.e., download) a TimeMap.

        Returns None if no error association exists.
        """

        return self.timemap_access_errormodel[urit]

    def set_Memento_access_error(self, urit, urim, errormsg):
        """Associates `errormsg` with a given `urit` and `urim` when the 
        error involves failure to access (i.e., download) a memento.
        """

        self.memento_access_errormodel.setdefault(urit, {})
        self.memento_access_errormodel[urit][urim] = errormsg

        # make sure there is an entry in the scoremodel for get_TimeMap_URIs
        self.scoremodel.setdefault(urit, {})
        self.scoremodel[urit].setdefault(urim, {})
        
        # there can be an access error or a measurement error, not both
        self.memento_measure_errormodel.setdefault(urit, {})
        self.memento_measure_errormodel[urit][urim] = None

        # convenience so that we can search for memento errors
        # using a single urim instead of having to know the urit
        self.mementos_to_timemaps[urim] = urit

        # because we set an error on the memento,
        # there cannot be errors on the timemap
        self.timemap_access_errormodel[urit] = None

    def get_Memento_access_error_message(self, urim):
        """Gets the error message associated with a given `urim` when the
        error involves failure to access (i.e., download) a memento.

        Returns None if no error association exists.
        """

        urit = self.mementos_to_timemaps[urim]
        return self.memento_access_errormodel[urit][urim]

    def set_Memento_measurement_error(self, urit, urim, measuretype, measurename, errormsg):
        """Associates `errormsg` with a given `urim`, `measuretype`,
        and `measurename` when the error involves failure of one of the 
        measures when processing a memento.
        """

        self.memento_measure_errormodel.setdefault(urit, {})
        self.memento_measure_errormodel[urit].setdefault(urim, {})
        self.memento_measure_errormodel[urit][urim].setdefault(measuretype, {})
        self.memento_measure_errormodel[urit][urim][measuretype][measurename] = errormsg

        # make sure there is an entry in the scoremodel for get_TimeMap_URIs
        self.scoremodel.setdefault(urit, {})
        self.scoremodel[urit].setdefault(urim, {})

        # there can be an access error or a measurement error, not both
        self.memento_access_errormodel.setdefault(urit, {})
        self.memento_access_errormodel[urit][urim] = None

        # convenience so that we can search for memento errors
        # using a single urim instead of having to know the urit
        self.mementos_to_timemaps[urim] = urit

        # because we set an error on the memento,
        # there cannot be errors on the timemap
        self.timemap_access_errormodel[urit] = None

    def get_Memento_measurement_error_message(self, urim, measuretype, measurename):
        """Gets the error message associated with a given `urim`, `measuretype`,
        and `measurename` when the error involves failure of one of the 
        measures when processing a memento.

        Returns None if no error association exists.
        """

        urit = self.mementos_to_timemaps[urim]
        return self.memento_measure_errormodel[urit][urim][measuretype][measurename]

    def set_stemmed(self, urit, urim, measuretype, measure, stemmed):
        """Sets that a given `urit`, `urim` was `stemmed` while using
        `measuretype` and `measure`.
        """
        
        self.initialize_scoremodel_for_keys(urit, urim, measuretype, measure)
        self.scoremodel[urit][urim][measuretype][measure]["stemmed"] = stemmed

    def get_stemmed(self, urit, urim, measuretype, measure):
        """Gets that a given `urit`, `urim` was `stemmed` while using
        `measuretype` and `measure`.

        Returns None if not set.
        """

        stemmed = None

        try:
            stemmed = self.scoremodel[urit][urim][measuretype][measure]["stemmed"]
        except KeyError as e:
            self.handle_key_error(e, urit, urim, measuretype, measure)

        return stemmed

    def set_tokenized(self, urit, urim, measuretype, measure, tokenized):
        """Sets that a given `urit`, `urim` was `tokenized` while using
        `measuretype` and `measure`.
        """

        self.initialize_scoremodel_for_keys(urit, urim, measuretype, measure)
        self.scoremodel[urit][urim][measuretype][measure]["tokenized"] = tokenized

    def get_tokenized(self, urit, urim, measuretype, measure):
        """Gets that a given `urit`, `urim` was `stemmed` while using
        `measuretype` and `measure`.

        Returns None if not set.
        """

        tokenized = None

        try:
            tokenized = self.scoremodel[urit][urim][measuretype][measure]["tokenized"]
        except KeyError as e:
            self.handle_key_error(e, urit, urim, measuretype, measure)

        return tokenized

    def set_removed_boilerplate(self, urit, urim, measuretype, measure, removed_boilerplate):
        """Sets that a given `urit`, `urim` was had its boilerplate removed
        while using `measuretype` and `measure`.
        """
        
        self.initialize_scoremodel_for_keys(urit, urim, measuretype, measure)
        self.scoremodel[urit][urim][measuretype][measure]["removed boilerplate"] = removed_boilerplate

    def get_removed_boilerplate(self, urit, urim, measuretype, measure):
        """Gets that a given `urit`, `urim` was had its boilerplate removed
        while using `measuretype` and `measure`.

        Returns None if not set.
        """

        removed_boilerplate = None

        try:
            removed_boilerplate = self.scoremodel[urit][urim][measuretype][measure]["removed boilerplate"]
        except KeyError as e:
            self.handle_key_error(e, urit, urim, measuretype, measure)

        return removed_boilerplate

    def get_TimeMap_URIs(self):
        """Returns the list of TimeMap URIs (URI-Ts) that have been stored 
        in this object.
        """

        return list(self.scoremodel.keys())

    def get_Memento_URIs_in_TimeMap(self, urit):
        """Returns the list of memento URIs (URI-Ms) that have been stored
        in this object and associated with TimeMap `urit`.
        """

        return list(self.scoremodel[urit].keys())
    
    def get_Measures(self):
        """Returns the list of measure stored in this object.
        """

        return list(self.measures)

    def get_off_topic_status_by_measure(self, urim, measuretype, measurename):
        """Returns the off-topic status of `urim` for `measuretype` and
        `measurename`.

        Returns None if no off-topic status has been associated.
        """

        status = None

        try:
            urit = self.mementos_to_timemaps[urim]
            status = self.scoremodel[urit][urim][measuretype][measurename]["topic status"]
        except KeyError as e:
            self.handle_key_error(e, urit, urim, measuretype, measurename)

        return status

    def get_overall_off_topic_status(self, urim):
        """Returns the off-topic status of `urim` for all measures.

        Returns None if no off-topic status has been associated.
        """

        urit = self.mementos_to_timemaps[urim]
        return self.scoremodel[urit][urim]["overall topic status"]

    def calculate_offtopic_by_measure(self, measuretype, measurename, threshold, comparison):
        """Iterates through all TimeMaps and mementos, deteremining if the 
        resulting scores for `measuretype` and `measurename` exceed the 
        numeric value stored in `threshold` as indicated by `comparison`.

        Valid values of `comparison` are <, >, ==, or !=.
        """

        for urit in self.get_TimeMap_URIs():

            if self.get_TimeMap_access_error_message(urit):
                continue

            for urim in self.get_Memento_URIs_in_TimeMap(urit):

                if self.get_Memento_access_error_message(urim):
                    continue

                if self.get_Memento_measurement_error_message(urim, measuretype, measurename):
                    continue

                score = self.get_score(urit, urim, measuretype, measurename)

                # TODO: fix this if/elif block
                # I know I can use eval, but also know its use has security implications
                if comparison == ">":
                    if score > threshold:
                        self.scoremodel[urit][urim][measuretype][measurename]["topic status"] = "off-topic"
                    else:
                        self.scoremodel[urit][urim][measuretype][measurename]["topic status"] = "on-topic"
                elif comparison == "==":
                    if score == threshold:
                        self.scoremodel[urit][urim][measuretype][measurename]["topic status"] = "off-topic"
                    else:
                        self.scoremodel[urit][urim][measuretype][measurename]["topic status"] = "on-topic"
                elif comparison == "<":
                    if score < threshold:
                        self.scoremodel[urit][urim][measuretype][measurename]["topic status"] = "off-topic"
                    else:
                        self.scoremodel[urit][urim][measuretype][measurename]["topic status"] = "on-topic"
                elif comparison == "!=":
                    if score != threshold:
                        self.scoremodel[urit][urim][measuretype][measurename]["topic status"] = "off-topic"
                    else:
                        self.scoremodel[urit][urim][measuretype][measurename]["topic status"] = "on-topic"
                else:
                    raise MeasureModelException("Unsupported comparison type {}".format(comparison))

    def calculate_overall_offtopic_status(self):
        """Iterates through all TimeMaps and mementos, determining if a memento
        was marked off-topic in any of its measures.
        """

        for urit in self.get_TimeMap_URIs():

            if self.get_TimeMap_access_error_message(urit):
                continue

            for urim in self.get_Memento_URIs_in_TimeMap(urit):

                if self.get_Memento_access_error_message(urim):
                    continue

                for measuretype, measurename in self.get_Measures():

                    if self.get_Memento_measurement_error_message(urim, measuretype, measurename):
                        continue

                    topic_status = self.scoremodel[urit][urim][measuretype][measurename]["topic status"]

                    if topic_status == "off-topic":
                        self.scoremodel[urit][urim]["overall topic status"] = "off-topic"
                        break
                    
                    self.scoremodel[urit][urim]["overall topic status"] = topic_status

    def generate_dict(self):
        """Generates a dictionary of the content within this object."""

        outputdata = {}

        for urit in self.get_TimeMap_URIs():

            outputdata.setdefault(urit, {})

            tm_a_err = self.get_TimeMap_access_error_message(urit)

            if tm_a_err:
                outputdata[urit]["access error"] = str(tm_a_err)
            else:

                for urim in self.get_Memento_URIs_in_TimeMap(urit):

                    outputdata[urit].setdefault(urim, {})

                    m_a_err = self.get_Memento_access_error_message(urim)

                    if m_a_err:
                        outputdata[urit][urim]["access error"] = str(m_a_err)
                    else:

                        if self.get_simhash(urit, urim):
                            outputdata[urit][urim]["raw memento simhash value"] = \
                                self.get_simhash(urit, urim)

                        if self.get_content_length(urit,urim):
                            outputdata[urit][urim]["content length"] = \
                                self.get_content_length(urit, urim)

                        if self.get_language(urit, urim):
                            outputdata[urit][urim]["language"] = \
                                self.get_language(urit, urim)

                        if self.get_memento_datetime(urit, urim):
                            outputdata[urit][urim]["memento-datetime"] = \
                                self.get_memento_datetime(urit, urim).strftime(
                                    "%Y/%m/%d %H:%M:%S GMT"
                                )

                        for measuretype, measurename in self.get_Measures():

                            outputdata[urit][urim].setdefault(measuretype, {})
                            outputdata[urit][urim][measuretype].setdefault(measurename, {})

                            m_m_err = self.get_Memento_measurement_error_message(urim, measuretype, measurename)

                            if m_m_err:
                                outputdata[urit][urim][measuretype][measurename]["measurement error"] = str(m_m_err)

                            else:
                                outputdata[urit][urim][measuretype][measurename] = {
                                    "stemmed": self.get_stemmed(urit, urim, measuretype, measurename),
                                    "tokenized": self.get_tokenized(urit, urim, measuretype, measurename),
                                    "removed boilerplate": self.get_removed_boilerplate(urit, urim, measuretype, measurename),
                                    "comparison score": self.get_score(urit, urim, measuretype, measurename),
                                    "topic status": self.get_off_topic_status_by_measure(urim, measuretype, measurename)
                                }

                                outputdata[urit][urim]["overall topic status"] = self.get_overall_off_topic_status(urim)

        return outputdata

    def save_as_JSON(self, filename):
        """Saves the content of this object as JSON."""
        
        outputdata = self.generate_dict()

        with open(filename, 'w') as outputjson:
            json.dump(outputdata, outputjson, indent=4)

    def save_as_goldstandard(self, filename):
        """Saves the content of this object as the tab-delimited gold
        standard data used in AlNoamany's work.
        """

        outputdata = []
        uritcounter = 1

        for urit in self.get_TimeMap_URIs():

            tm_a_err = self.get_TimeMap_access_error_message(urit)

            if tm_a_err:
                outputdict = {}
                outputdict["id"] = uritcounter
                outputdict["label"] = "ERROR"
                outputdata.append(outputdict)

            else:

                for urim in self.get_Memento_URIs_in_TimeMap(urit):

                    outputdict = {}
                    outputdict["id"] = uritcounter
                    outputdict["URI"] = urim

                    fronturim = urim[:urim.find('/http')]

                    if fronturim[-3:] == 'id_':
                        fronturim = fronturim[:-3]

                    outputdict["date"] = fronturim[fronturim.rfind('/') + 1:] 

                    m_a_err = self.get_Memento_access_error_message(urim)

                    if m_a_err:
                        outputdict["label"] = "ERROR"
                    else:
                        
                        for measuretype, measurename in self.get_Measures():

                            m_m_err = self.get_Memento_measurement_error_message(urim, measuretype, measurename)

                            if m_m_err:
                                outputdict["label"] = "ERROR"
                            else:

                                if self.get_overall_off_topic_status(urim) == "on-topic":
                                    outputdict["label"] = "1"
                                elif self.get_overall_off_topic_status(urim) == "off-topic":
                                    outputdict["label"] = "0"

                    outputdata.append(outputdict)

            uritcounter += 1

        with open(filename, 'w') as tsvfile:

            fieldnames = [
                'id', 'date', 'URI', 'label'
            ]

            writer = csv.DictWriter(tsvfile, fieldnames=fieldnames, delimiter='\t')
            writer.writeheader()

            for row in outputdata:
                writer.writerow(row)
    
    def save_as_CSV(self, filename):
        """Saves the content of this object as a CSV."""
        
        outputdata = []

        for urit in self.get_TimeMap_URIs():

            tm_a_err = self.get_TimeMap_access_error_message(urit)

            if tm_a_err:

                outputdict = {}
                outputdict["URI-T"] = urit
                outputdict["Error"] = "TimeMap Access Error"
                outputdict["Error Message"] = tm_a_err
                outputdata.append(outputdict)

            else:

                for urim in self.get_Memento_URIs_in_TimeMap(urit):

                    outputdict = {}
                    outputdict["URI-T"] = urit
                    outputdict["URI-M"] = urim

                    m_a_err = self.get_Memento_access_error_message(urim)

                    if m_a_err:
                        outputdict["Error"] = "Memento Access Error"
                        outputdict["Error Message"] = m_a_err
                    else:
                        
                        for measuretype, measurename in self.get_Measures():

                            m_m_err = self.get_Memento_measurement_error_message(urim, measuretype, measurename)

                            outputdict["Measurement Type"] = measuretype
                            outputdict["Measurement Name"] = measurename

                            if m_m_err:
                                outputdict["Error"] = "Memento Measurement Error"
                                outputdict["Error Message"] = m_m_err

                            else:

                                outputdict["Comparison Score"] = self.get_score(urit, urim, measuretype, measurename)
                                outputdict["Stemmed"] = self.get_stemmed(urit, urim, measuretype, measurename)
                                outputdict["Tokenized"] = self.get_tokenized(urit, urim, measuretype, measurename)
                                outputdict["Removed Boilerplate"] = self.get_removed_boilerplate(urit, urim, measuretype, measurename)
                                outputdict["Topic Status"] = self.get_off_topic_status_by_measure(urim, measuretype, measurename)
                                outputdict["Overall Topic Status"] = self.get_overall_off_topic_status(urim)
                                outputdict["Simhash"] = self.get_simhash(urit, urim)
                                outputdict["Content Length"] = self.get_content_length(urit, urim)

                    outputdata.append(outputdict)

        with open(filename, 'w') as csvfile:

            fieldnames = [
                'URI-T', 'URI-M', 'Error', 'Error Message', 'Content Length', 'Simhash',
                'Measurement Type', 'Measurement Name', 'Comparison Score',
                'Stemmed', 'Tokenized', 'Removed Boilerplate', 'Topic Status', 'Overall Topic Status'
            ]

            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for row in outputdata:
                writer.writerow(row)
            


