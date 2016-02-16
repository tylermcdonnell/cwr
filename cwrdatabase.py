from MQT import MQTTopic, MQTDocument, MQTRelevanceJudgment, MQT
from sets import Set

class CWRData(object):
    '''
    Abstraction for the CWR data model. Eventually, this
    would ideally be a shim layer for relational db calls.
    '''

    def __init__(self):
        # All data is captured by test collection.
        self.test_collection = None
        
        # Loaded AMT runs.
        self.empirical_data = None
        
    def load(self, filename):
        '''
        Loads AMT data into the test collection.
        '''
        try:
            tc = self.test_collection
            self.empirical_data.extend(tc.import_amt_results(filename))
        except:
            # TODO: Pass error upstream.
            print ("Error while loading AMT results.")

    def all_topics(self):
        return self.test_collection.topics()

    def judged_topics(self):
        return list(Set([j.topic for j in self.empirical_data]))        

    def all_documents(self):
        return self.test_collection.documents()

    def judged_documents(self):
        return list(Set([j.document for j in self.empirical_data]))

    def judged_documents_by_topic(self, topic):
        return list(Set([j.document for j in self.empirical_data if j.topic == topic]))

    def all_gs(self):
        return self.test_collection.gold_standard()
        

    
    
