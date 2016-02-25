from testcollection.mqt import MQTTopic, MQTDocument, MQTRelevanceJudgment, MQT
from sets import Set

class DataModel(object):
    '''
    Abstraction for the CWR data model. Eventually, this
    would ideally be a shim layer for relational db calls.
    '''

    def __init__(self):
        # All data is captured by test collection.
        self.test_collection = MQT.load('2009.mqt')
        
        # Loaded AMT runs.
        self.judged_data = []
        
    def load(self, filename):
        '''
        Loads AMT data into the test collection.
        '''
        try:
            tc = self.test_collection
            self.judged_data.extend(tc.import_amt_results(filename))
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
        return list(set([j.topic for j in self.judged_data]))        

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

    def judged_documents_by_topic(self, topic_id):
        '''
        Returns all documents for which judgments have been loaded with
        the specified topic.
        
        Arguments:
        topic_id -- string id of topic
        '''
        return list(Set([j.document for j in self.judged_data if j.topic.id == topic_id]))
        
    def judgments(self, topic_id, document_id):
        return list(Set([j for j in self.judged_data if 
                         j.topic.id == topic_id and 
                         j.document.id == document_id]))
    def all_gs(self):
        '''
        Returns all gold standard judgments.
        '''
        return self.test_collection.gold_standard()

    def gold_standard(self, topic_id, document_id):
        '''
        Returns the gold standard judgment for a Topic-Document pair.
        '''
        gs = self.test_collection.find_gold_standard(topic_id, document_id)
        return gs.value

    def confusion_matrix(self, topic=None, document=None):
        '''
        Computes and returns a confusion matrix for the list of judgments.
        
        Cell[r][c] of the confusion matrix holds the probability that,
        given that an annotator selected r for a document, another 
        selected c for that same document.
        '''
        # Filter data.
        filtered = self.judged_data
        if topic:
            filtered = [j for j in filtered if j.topic.id == topic]
        if document:
            filtered = [j for j in filtered if j.document.id == document]
            
        # Compute.
        cm, _ = self.test_collection.compute_agreement_matrix(filtered)
        return self._confusion_matrix_string(cm)

    def _confusion_matrix_string(self, cm):
        as_string = ''
        for r in range(len(cm)):
            for c in range(len(cm[r])):
                as_string += ('%f ' % cm[r][c])
            as_string += '\n'
        return as_string

        

    
    
