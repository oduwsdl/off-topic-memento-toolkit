import json

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

    def save_as_JSON(self, filename):
        
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
                                    "comparison score": self.get_score(urit, urim, measuretype, measurename)
                                }

        with open(filename, 'w') as outputjson:
            json.dump(outputdata, outputjson)

    def save_as_goldstandard(self, filename):
        pass
    
    def save_as_CSV(self, filename):
        pass