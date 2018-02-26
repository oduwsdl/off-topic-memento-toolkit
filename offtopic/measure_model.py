
class MeasureModel:

    scoremodel = {}
    errormodel = {}
    measures = []

    def set_score(self, urit, urim, measuretype, measure, score):
        self.scoremodel.setdefault(urit, {})
        self.scoremodel[urit].setdefault(urim, {})
        self.scoremodel[urit][urim].setdefault(measuretype, {})
        self.scoremodel[urit][urim][measuretype].setdefault(measure, {})
        self.scoremodel[urit][urim][measuretype][measure]["comparison score"] = score
        self.measures.append((measuretype, measure))

    def get_score(self, urit, urim, measuretype, measure):
        return self.scoremodel[urit][urim][measuretype][measure]

    def set_errormsg(self, uri, errormsg):
        self.errormodel[uri] = errormsg

    def get_errormsg(self, uri):
        return self.errormodel[uri]

    def set_score_feature(self, urit, urim, measuretype, measure, featurename, value):
        self.scoremodel[urit][urim][measuretype][measure][featurename] = value

    def get_score_feature(self, urit, urim, measuretype, measure, featurename):
        return self.scoremodel[urit][urim][measuretype][measure][featurename]

    def get_TimeMap_URIs(self):
        return list(self.scoremodel.keys())

    # def get_Memento_URIs(self, urit);
    #     return list(self.scoremodel[urit].keys())

    def get_Measures(self):
        return self.measures


    
