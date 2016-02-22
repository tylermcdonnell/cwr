from MQT import MQTTopic, MQTDocument, MQTRelevanceJudgment, MQT
from sets import Set

class DataModel(object):
    '''
    Abstraction for the CWR data model. Eventually, this
    would ideally be a shim layer for relational db calls.
    '''

    def __init__(self):
        # All data is captured by test collection.
        self.test_collection = None
        
        # Loaded AMT runs.
        self.judged_data = None
        
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
        '''
        Returns all topics.
        '''
        return self.test_collection.topics()

    def judged_topics(self):
        '''
        Returns all topics for which judgments have been loaded.
        '''
        return list(Set([j.topic for j in self.judged_data]))        

    def all_documents(self):
        '''
        Returns all documents.
        '''
        return self.test_collection.documents()

    def judged_documents(self):
        '''
        Returns all documents for which judgments have been loaded.
        '''
        return list(Set([j.document for j in self.judged_data]))

    def judged_documents_by_topic(self, topic):
        '''
        Returns all documents for which judgments have been loaded with
        the specified topic.
        '''
        return list(Set([j.document for j in self.judged_data if j.topic == topic]))

    def all_gs(self):
        '''
        Returns all gold standard judgments.
        '''
        return self.test_collection.gold_standard()

    def confusion_matrix(self, topic):
        '''
        Computes and returns a confusion matrix for the list of judgments.
        
        Cell[r][c] of the confusion matrix holds the probability that,
        given that an annotator selected r for a document, another 
        selected c for that same document.
        '''
        pass
        

    
    
