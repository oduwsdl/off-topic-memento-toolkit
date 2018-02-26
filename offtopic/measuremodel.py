import json
import csv

class MeasureModelException(Exception):
    pass

class MeasureModelNoSuchMemento(MeasureModelException):
    pass

class MeasureModelNoSuchTimeMap(MeasureModelException):
    pass

class MeasureModelNoSuchMeasure(MeasureModelException):
    pass

class MeasureModelNoSuchMeasureType(MeasureModelException):
    pass

class MeasureModel:
    """
        This class exists because the data structure for keeping track
        of the scores and measures was getting too unwieldy. It seems
        awfully complex for its job, but I hadn't found an alternative yet.
    """

    def __init__(self):
        self.scoremodel = {}
        self.timemap_access_errormodel = {}
        self.memento_access_errormodel = {}
        self.memento_measure_errormodel = {}
        self.mementos_to_timemaps = {}
        self.measures = []

    def initialize_scoremodel_for_keys(self, urit, urim, measuretype, measure):
        self.scoremodel.setdefault(urit, {})
        self.scoremodel[urit].setdefault(urim, {})
        self.scoremodel[urit][urim].setdefault(measuretype, {})
        self.scoremodel[urit][urim][measuretype].setdefault(measure, {})
        self.scoremodel[urit][urim][measuretype][measure].setdefault(measure, {})
        self.scoremodel[urit][urim][measuretype][measure].setdefault("comparison score", None)
        self.scoremodel[urit][urim][measuretype][measure].setdefault("stemmed", None)
        self.scoremodel[urit][urim][measuretype][measure].setdefault("tokenized", None)
        self.scoremodel[urit][urim][measuretype][measure].setdefault("removed boilerplate", None)
        self.scoremodel[urit][urim][measuretype][measure].setdefault("topic status", None)

        self.scoremodel[urit][urim]["overall topic status"] = None

        self.timemap_access_errormodel[urit] = None

        self.memento_access_errormodel.setdefault(urit, {})
        self.memento_access_errormodel[urit].setdefault(urim, None)

        self.memento_measure_errormodel.setdefault(urit, {})
        self.memento_measure_errormodel[urit].setdefault(urim, {})
        self.memento_measure_errormodel[urit][urim].setdefault(measuretype, {})
        self.memento_measure_errormodel[urit][urim][measuretype].setdefault(measure, None)

        self.mementos_to_timemaps[urim] = urit

        if (measuretype, measure) not in self.measures:
            self.measures.append( (measuretype, measure) )

    def set_score(self, urit, urim, measuretype, measure, score):
        self.initialize_scoremodel_for_keys(urit, urim, measuretype, measure)
        self.scoremodel[urit][urim][measuretype][measure]["comparison score"] = score

    def handle_key_error(self, exception, urit, urim, measuretype, measure):
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
        score = None

        try: 
            score = self.scoremodel[urit][urim][measuretype][measure]["comparison score"]
        except KeyError as e:
            self.handle_key_error(e, urit, urim, measuretype, measure)

        return score

    def set_TimeMap_access_error(self, urit, errormsg):
        
        self.timemap_access_errormodel[urit] = errormsg

        # make sure there is an entry in the scoremodel for get_TimeMap_URIs
        self.scoremodel.setdefault(urit, {})

    def get_TimeMap_access_error_message(self, urit):
        return self.timemap_access_errormodel[urit]

    def set_Memento_access_error(self, urit, urim, errormsg):

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
        urit = self.mementos_to_timemaps[urim]
        return self.memento_access_errormodel[urit][urim]

    def set_Memento_measurement_error(self, urit, urim, measuretype, measurename, errormsg):

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

        urit = self.mementos_to_timemaps[urim]
        return self.memento_measure_errormodel[urit][urim][measuretype][measurename]

    def set_stemmed(self, urit, urim, measuretype, measure, stemmed):
        self.initialize_scoremodel_for_keys(urit, urim, measuretype, measure)
        self.scoremodel[urit][urim][measuretype][measure]["stemmed"] = stemmed

    def get_stemmed(self, urit, urim, measuretype, measure):

        stemmed = None

        try:
            stemmed = self.scoremodel[urit][urim][measuretype][measure]["stemmed"]
        except KeyError as e:
            self.handle_key_error(e, urit, urim, measuretype, measure)

        return stemmed

    def set_tokenized(self, urit, urim, measuretype, measure, tokenized):
        self.initialize_scoremodel_for_keys(urit, urim, measuretype, measure)
        self.scoremodel[urit][urim][measuretype][measure]["tokenized"] = tokenized

    def get_tokenized(self, urit, urim, measuretype, measure):

        tokenized = None

        try:
            tokenized = self.scoremodel[urit][urim][measuretype][measure]["tokenized"]
        except KeyError as e:
            self.handle_key_error(e, urit, urim, measuretype, measure)

        return tokenized

    def set_removed_boilerplate(self, urit, urim, measuretype, measure, removed_boilerplate):
        self.initialize_scoremodel_for_keys(urit, urim, measuretype, measure)
        self.scoremodel[urit][urim][measuretype][measure]["removed boilerplate"] = removed_boilerplate

    def get_removed_boilerplate(self, urit, urim, measuretype, measure):

        removed_boilerplate = None

        try:
            removed_boilerplate = self.scoremodel[urit][urim][measuretype][measure]["removed boilerplate"]
        except KeyError as e:
            self.handle_key_error(e, urit, urim, measuretype, measure)

        return removed_boilerplate
    
    def get_TimeMap_URIs(self):
        return list(self.scoremodel.keys())

    def get_Memento_URIs_in_TimeMap(self, urit):
        return list(self.scoremodel[urit].keys())
    
    def get_Measures(self):
        return list(self.measures)

    def get_off_topic_status_by_measure(self, urim, measuretype, measurename):
        urit = self.mementos_to_timemaps[urim]
        return self.scoremodel[urit][urim][measuretype][measurename]["topic status"]

    def get_overall_off_topic_status(self, urim):
        urit = self.mementos_to_timemaps[urim]
        return self.scoremodel[urit][urim]["overall topic status"]

    def calculate_offtopic_by_measure(self, measuretype, measurename, threshold, comparison):

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

        for urit in self.get_TimeMap_URIs():

            if self.get_TimeMap_access_error_message(urit):
                continue

            for urim in self.get_Memento_URIs_in_TimeMap(urit):

                if self.get_Memento_access_error_message(urim):
                    continue

                for measuretype, measurename in self.get_Measures():

                    topic_status = self.scoremodel[urit][urim][measuretype][measurename]["topic status"]

                    if topic_status == "off-topic":
                        self.scoremodel[urit][urim]["overall topic status"] = "off-topic"
                        break
                    
                    self.scoremodel[urit][urim]["overall topic status"] = topic_status

    def generate_dict(self):

        outputdata = {}

        for urit in self.get_TimeMap_URIs():

            outputdata.setdefault(urit, {})

            tm_a_err = self.get_TimeMap_access_error_message(urit)

            if tm_a_err:
                outputdata[urit]["access error"] = tm_a_err
            else:

                for urim in self.get_Memento_URIs_in_TimeMap(urit):

                    outputdata[urit].setdefault(urim, {})

                    m_a_err = self.get_Memento_access_error_message(urim)

                    if m_a_err:
                        outputdata[urit][urim]["access error"] = m_a_err
                    else:
                        
                        for measuretype, measurename in self.get_Measures():

                            outputdata[urit][urim].setdefault(measuretype, {})
                            outputdata[urit][urim][measuretype].setdefault(measurename, {})

                            m_m_err = self.get_Memento_measurement_error_message(urim, measuretype, measurename)

                            if m_m_err:
                                outputdata[urit][urim][measuretype][measurename]["measurement error"] = m_m_err

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
        
        outputdata = self.generate_dict()

        with open(filename, 'w') as outputjson:
            json.dump(outputdata, outputjson)

    def save_as_goldstandard(self, filename):

        outputdata = []

        for urit in self.get_TimeMap_URIs():

            tm_a_err = self.get_TimeMap_access_error_message(urit)

            if tm_a_err:
                outputdata[urit]["access error"] = tm_a_err

                outputdict = {}
                outputdict["URI-T"] = urit
                outputdict["Overall Topic Status"] = "ERROR"

            else:

                for urim in self.get_Memento_URIs_in_TimeMap(urit):

                    outputdict = {}
                    outputdict["URI-M"] = urim

                    fronturim = urim[:urim.find('/http')]

                    if fronturim[-3:] == 'id_':
                        fronturim = fronturim[:-3]

                    outputdict["Date"] = fronturim[fronturim.rfind('/') + 1:] 

                    m_a_err = self.get_Memento_access_error_message(urim)

                    if m_a_err:
                        outputdict["Overall Topic Status"] = "ERROR"
                    else:
                        
                        for measuretype, measurename in self.get_Measures():

                            m_m_err = self.get_Memento_measurement_error_message(urim, measuretype, measurename)

                            if m_m_err:
                                outputdict["Overall Topic Status"] = "ERROR"
                            else:

                                outputdict["Overall Topic Status"] = self.get_overall_off_topic_status(urim)

        with open(filename, 'wb') as csvfile:

            fieldnames = [
                'URI-T', 'Date', 'URI-M', 'Overall Topic Status'
            ]

            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for row in outputdata:
                writer.writerow(row)
    
    def save_as_CSV(self, filename):
        
        outputdata = []

        for urit in self.get_TimeMap_URIs():

            tm_a_err = self.get_TimeMap_access_error_message(urit)

            if tm_a_err:
                outputdata[urit]["access error"] = tm_a_err

                outputdict = {}
                outputdict["URI-T"] = urit
                outputdict["Error"] = "TimeMap Access Error"
                outputdict["Error Message"] = tm_a_err

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

        with open(filename, 'wb') as csvfile:

            fieldnames = [
                'URI-T', 'URI-M', 'Error', 'Error Message','Measurement Type', 'Measurement Name', 'Comparison Score',
                'Stemmed', 'Tokenized', 'Removed Boilerplate', 'Topic Status', 'Overall Topic Status'
            ]

            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for row in outputdata:
                writer.writerow(row)
            


