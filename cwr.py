import itertools
import requests
import random
import os

from datamodel import DataModel

from threading import Thread
from bs4 import BeautifulSoup
from difflib import SequenceMatcher
from abc import abstractmethod
from collections import namedtuple, defaultdict
from highlightinterface import HighlightWebView, HighlightBox

from PyQt4 import QtGui
from PyQt4 import QtWebKit
from PyQt4 import QtCore
from PyQt4.Qt import QUrl, QCheckBox

from testcollection.mqt import MQTTopic, MQTDocument, MQTRelevanceJudgment, MQT

class CWR(QtGui.QWidget):
    
    def __init__(self):
        self._dm = DataModel()              # Primary data model.

        self._topics    = []                # All topics for which judgments have been loaded.
        self._documents = []                # Documents for which we have a judgment for the
                                            # currently selected topic.

        self._selected_topic    = None      # Currently selected topic.
        self._selected_document = None      # Currently selected document.
        self._rationales        = []        # Rationales for the currently selected document.

        self._display_text = None           # Text of document being manipulated.

        super(CWR, self).__init__()

        self.init_UI()

        # For testing WebView.
        ''' 
        test_url = 'https://en.wikipedia.org/wiki/The_Beatles'
        content  = requests.get(test_url).text        
        content
        test_text = BeautifulSoup(content, "html.parser").get_text()
        self._display_text = test_text
        '''
        
    def init_UI(self):        
        grid = QtGui.QGridLayout()
        grid.setSpacing(10)
            
        #####################################
        # Summary of UI Elements            #
        #####################################
        # These are UI elements that are updated after creation.
        self._confusion_matrix = None       # String form of confusion matrix for current view.


        #####################################
        # Topic View                        #
        #####################################
        # Contains Topic List.
        topic_view = QtGui.QGroupBox("Topics")
        topic_layout = QtGui.QVBoxLayout()
        topic_view.setLayout(topic_layout)
        grid.addWidget(topic_view, 0, 0)

        # Topic List
        self._topic_list = QtGui.QListWidget()
        self._topic_list.setSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Minimum)
        self._topic_list.itemClicked.connect(self._topic_selected)
        topic_layout.addWidget(self._topic_list)
        

        #####################################
        # Document View                     #
        #####################################
        # Contains Document List.
        document_view = QtGui.QGroupBox("Documents")
        document_layout = QtGui.QVBoxLayout()
        document_view.setLayout(document_layout)
        grid.addWidget(document_view, 0, 1)

        # Document List
        self._document_list = QtGui.QListWidget()
        self._document_list.setSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self._document_list.itemClicked.connect(self._document_selected)
        document_layout.addWidget(self._document_list)


        #####################################
        # Statistics View                   #
        #####################################
        # Below rationale view. Contains the confusion matrix, list of
        # rationales, gold standard values, and user judgments.
        stat_label = QtGui.QLabel()
        stat_label.setText("<B>Statistics</B>")
        #stat_layout        = QtGui.QVBoxLayout()
        document_layout.addWidget(stat_label)
        #self._stat_display.setLayout(stat_layout)
        #self._stat_display.setSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Minimum)

        # Confusion Matrix for current Topic or Topic-Document Pair
        confusion_matrix_label = QtGui.QLabel()
        confusion_matrix_label.setText("Confusion Matrix")
        document_layout.addWidget(confusion_matrix_label)
        confusion_matrix       = QtGui.QLabel()
        confusion_matrix.setText("  -    -    -    -   \n"
                                 "  -    -    -    -   \n"
                                 "  -    -    -    -   \n")
        document_layout.addWidget(confusion_matrix)

        # Gold Standard for current Topic-Document.
        gold_standard_view = QtGui.QLabel()
        gold_standard_view.setText("Gold Standard: N/A")
        document_layout.addWidget(gold_standard_view)

        # Degree 1 Agreement
        d1_agreement_view = QtGui.QLabel()
        d1_agreement_view.setText("D1 Agreement: N/A")
        document_layout.addWidget(d1_agreement_view)

        # Give pointers to updateable elements.
        self._confusion_matrix   = confusion_matrix
        self._gold_standard_view = gold_standard_view
        self._d1_agreement_view  = d1_agreement_view

   
        #####################################
        # Rationale View                    #
        #####################################
        # Contains the rationale check boxes, text display, and statistics.
        rationale_view = QtGui.QGridLayout()
        grid.addLayout(rationale_view, 0, 2)
        
        # Rationale Display
        display = HighlightWebView()
        display.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        display.load(QUrl('https://en.wikipedia.org/wiki/The_Beatles'))
        display.show()
        self._rationale_display = display
        rationale_view.addWidget(self._rationale_display, 2, 0)
        
        # Rationale Selection
        selection_view = QtGui.QGroupBox("Selection")
        self._selection_layout = QtGui.QHBoxLayout()
        selection_view.setLayout(self._selection_layout)
        rationale_view.addWidget(selection_view, 1, 0)


        #####################################
        # Worker View                       #
        #####################################
        # Below rationale view. Contains pure text of worker rationales,
        # judgments, and the gold standard.
        self._worker_display = QtGui.QGroupBox("Workers")
        worker_layout        = QtGui.QVBoxLayout()
        grid.addLayout(worker_layout, 0, 3)
        #self._worker_display.setLayout(worker_layout)


        # Worker Rationales for current Topic-Document.
        worker_rationale_list_label = QtGui.QLabel()
        worker_rationale_list_label.setText("Worker Rationales")
        worker_layout.addWidget(worker_rationale_list_label)
        worker_rationale_list = QtGui.QTextEdit()
        worker_rationale_list.setText("Initial Text.")
        worker_layout.addWidget(worker_rationale_list)

        # Worker Judgments for current Topic-Document.
        worker_judgment_list_label = QtGui.QLabel()
        worker_judgment_list_label.setText("Worker Judgments")
        worker_layout.addWidget(worker_judgment_list_label)
        worker_judgment_list = QtGui.QTextEdit()
        worker_judgment_list.setText("Initial Text.")
        worker_layout.addWidget(worker_judgment_list)

        # Give pointers to updateable elements.
        self._worker_judgments   = worker_judgment_list
        self._worker_rationales  = worker_rationale_list
        

        #####################################
        # Main Application Properties       #
        #####################################
        self.setLayout(grid)
        self.setGeometry(300, 300, 1000, 1000)
        self.setWindowTitle("The Crowdworker's Rationale")
        self.show()
        
    def load(self, directory):
        '''
        Loads rationale data from the specified file.
        '''
        dm = self._dm
        for dirpath, _, filenames in os.walk(directory):
            for f in filenames:
                if f.endswith(".csv"): 
                    absolute_path = os.path.abspath(os.path.join(dirpath, f))
                    dm.load(absolute_path)
        self.update_topic_list(dm.judged_topics())
        self.update_document_list([])

#########################################################################################
# Updateable UI Elements                                                                #
#########################################################################################

    def update_topic_list(self, topics):
        '''
        Updates the topics displayed in Topic View.
        '''
        self._topics = topics
        self._topic_list.clear()
        self._topic_list.addItems([t.id for t in topics])
        self._topic_list.sortItems()   
        
    def update_document_list(self, documents):
        '''
        Updates the documents displayed in Document View.
        '''
        self._document_list.clear()
        self._document_list.addItems(documents)
        self._document_list.sortItems() 

    def update_rationale_selection(self, rationales):
        '''
        Regenerates data structures and display logic for rationale selection.
        '''
        # Compact holder for all rationale logic.
        container = namedtuple('RationaleContainer', ['rationale', 'color', 'display'])

        # Friendly display colors used to highlight rationales in source texts.
        colors = [QtGui.QColor(102, 255, 102), # Light Green
                  QtGui.QColor(255, 102, 102), # Light Red 
                  QtGui.QColor(102, 201, 255), # Electric Blue
                  QtGui.QColor(102, 178, 255), # Baby Blue
                  QtGui.QColor(178, 102, 255), # Light Purple
                  QtGui.QColor(255, 205, 255), # Light Magenta
                  QtGui.QColor(255, 102, 178), # Light Pink
                  QtGui.QColor(192, 192, 192)] # Light Grey

        # Remove old rationale widgets.
        layout = self._selection_layout
        for i in reversed(range(layout.count())): 
            layout.itemAt(i).widget().setParent(None)

        # Re-generate rationale data structures.
        self._rationales = []
        for i in range(len(rationales)):
            r = rationales[i]
            c = colors[min(i, len(colors) - 1)]
            d = QCheckBox(r.label)
            d.stateChanged.connect(self._rationale_selection_changed)
            self._rationales.append(container(rationale = r, color = c, display = d))
            self._selection_layout.addWidget(d)

    def update_rationale_display(self):
        '''
        Recomputes rationale overlap and updates display. Expensive.
        '''
        print ("Updating rationale display...")
        
        # Disable rationale selection while updating.
        for this_rationale in self._rationales:
            this_rationale.display.setEnabled(False)
        
        # Locate selected rationales.
        selected = []
        for this_rationale in self._rationales:
            if this_rationale.display.isChecked():
                selected.extend([r for r in self._rationales if this_rationale.display.text() == r.rationale.label])
        print (selected)

        # Gather text.
        text = self._rationale_display.get_text()

        # Compute overlap.
        just_rationales = [r.rationale for r in selected]
        result = Rationale.compute_overlap(text, just_rationales)

        # Update display with rationale matches.
        display = self._rationale_display
        display.clear()
        
        # If more than one rationale is selected, highlight overlap.
        '''
        if result.overlap:
            for string in result.overlap:
                print ("Highlighted string: %s" % string)
                display.highlight(string)
        # Else, highlight single rationale
        elif result.matches:
            strings = [QtCore.QString(s) for s in itertools.chain(*[s for s in result.matches.values()])]
            for string in strings:
                print ("Highlighting string: %s" % string)
                display.highlight(string)
        '''

        for r in just_rationales:
            display.highlight(r.rationale.rationale)
            
        # This is code exclusively for a multi-color highlight interface.
        '''
        for rationale, matches in result.matches.items():
            # Map back to container to find correct color.
            color = [c.color for c in selected if c.rationale is rationale][0]
            
            # Highlight in display.
            for match in matches:
                display.highlight(match, color)

        overlap_color = QtGui.QColor(255, 255, 102) # Light Yellow
        for string in result.overlap:
            display.highlight(string, overlap_color)
        '''

        # Re-enable rationale selection.
        for this_rationale in self._rationales:
            this_rationale.display.setEnabled(True)

    def update_statistics(self, topic=None, document=None):
        self.update_gold_standard_view(topic, document)
        self.update_rationale_list()
        self.update_judgment_list()
        self.update_confusion_matrix(topic, document)
        self.update_d1_agreement(topic, document)

    def update_confusion_matrix(self, topic=None, document=None):
        cm = self._dm.confusion_matrix(topic, document)
        self._confusion_matrix.setText(cm)

    def update_gold_standard_view(self, topic, document):
        '''
        Updates the current gold standard view.
        '''
        if topic and document:
            value = self._dm.gold_standard(topic, document)
            self._gold_standard_view.setText("Gold Standard: %s" % value)

    def update_d1_agreement(self, topic, document):
        '''
        Computes and updates the agreement for currently selected Topic or Document.
        '''
        agreement = self._dm.agreement(topic, document)
        self._d1_agreement_view.setText("D1 Agreement: %f" % agreement)

    def update_rationale_list(self):
        '''
        Updates the worker rationale list. If one or more worker IDs is 
        selected, this will display only the rationales by the selected 
        workers. Otherwise, this will display all rationales for the 
        selected Topic and Document.
        '''
        display_text = ''
        selected = [r for r in self._rationales if r.display.isChecked()]
        # If none are selected, display all.
        selected = selected if selected else self._rationales
        for r in selected:
            display_text += ('%s\n\n%s\n\n' % (r.rationale.label, r.rationale.rationale.rationale))
        self._worker_rationales.setText(display_text)

    def update_judgment_list(self, topic=None, document=None):
        '''
        Updates the worker judgment list. If one or more worker IDs is
        selected, this will display only the judgments of those selected
        workers. Otherwise, this will display the judgments from all workers.
        '''
        display_text = ''
        selected = [r for r in self._rationales if r.display.isChecked()]
        # If none are selected, display all.
        selected = selected if selected else self._rationales
        for r in selected:
            display_text += ('%s: %s\n' % (r.rationale.label, r.rationale.rationale.value))
        self._worker_judgments.setText(display_text)
        
    def update_rationale_text(self, text):
        '''
        This updates the text in the rationale display.
        '''
        self._rationale_display.set_text(text)
    
    def highlight_rationale(self, text):
        self._rationale_display.highlight(text)

    def load_document(self, url):
        self._rationale_display.load(QUrl(url))
        

#########################################################################################
# Signals                                                                               #
#########################################################################################

    def _topic_selected(self, item):
        '''
        Handler function - user selects a topic in the Topic View.
        
        Refreshes the list of documents in the Document View with 
        all documents for which a worker judgment has been loaded
        for that topic. Computes statistics across that topic.
        '''
        topic_id = item.text()

        # Update control selection.
        self._selected_topic = topic_id

        # Update statistics view.
        self.update_statistics(topic=str(topic_id))

        print ("Loading documents for topic %s" % topic_id)
        documents = self._dm.judged_documents_by_topic(topic_id)
        self.update_document_list([d.id for d in documents])

    def _document_selected(self, item):
        '''
        Handler function - user select a document in the Document View.
        
        Loads the text from that document into the rationale display
        and computes statistics for that document.
        '''
        document_id       = item.text()
        
        # Update control selection.
        self._selected_document = document_id

        # Grab control selections.
        selected_topic    = self._selected_topic
        selected_document = self._selected_document

        print ("Loading rationales for document %s, topic %s" % (selected_document, selected_topic))
        rationales = self._dm.judgments(selected_topic, selected_document)
        rationales = [Rationale(str(random.randint(1,10000)), r) for r in rationales]
        self.update_rationale_selection(rationales)

        # Update statistics view.
        self.update_statistics(str(selected_topic), str(selected_document))

        # Load document.
        document = next((d for d in self._dm.judged_documents() if d.id == selected_document), None)
        self.load_document(document.url)
        
    def _rationale_selection_changed(self, state):
        '''
        Handler function called when a user selects or deselects a rationale
        check box.
        '''
        worker = Thread(target=self.update_rationale_display)
        worker.start()
    
    
class Rationale(object):
    '''
    Provides various utilities for analyzing similarity of rationales
    with respect to each and a source text.
    '''

    def __init__(self, label, rationale):
        self.label      = label
        self.rationale  = rationale 

    @staticmethod
    def compute_overlap(text, rationales):
        '''
        Stores the key-string tuple and, for every tuple stored, computes the 
        overlap of the string with the source text. Additionally, separately
        computes overlapping portions of the text common to more than one triple.
        
        Arguments:
        
        text       -- Source text to compare rationales against.
        rationales -- Rationales to use for computation. 
        
        Returns namedtuple with fields:
        
        matches -- Dictionary of rationale-[string] pairs, where the list of strings 
                   mapped to a rationale are substrings found in the text.
        overlap -- List of strings that are common to two or more rationales.
        '''
        minimum_match_length = 5
        result = namedtuple('RationaleComputation', ['matches', 'overlap'])
        
        # Compute matches
        matches  = defaultdict(list)
        for rationale in rationales:
            # Yes, this is stupid naming by me.
            rationale_text = rationale.rationale.rationale
            for match in SequenceMatcher(None, text, rationale_text).get_matching_blocks():
                start  = match[0]
                length = match[2]
                if length > minimum_match_length:
                    matches[rationale].append(text[start : start + length])
     
        # Compute overlap in rationales.
        overlap = []
        for pair in itertools.combinations(rationales, 2):
            string1 = pair[0].rationale.rationale
            string2 = pair[1].rationale.rationale
            for match in SequenceMatcher(None, string1, string2).get_matching_blocks():
                start  = match[0]
                length = match[2]
                if length > minimum_match_length:
                    overlap.append(string1[start : start + length])
                
        return result(matches = matches, overlap = overlap)



        
if __name__ == "__main__":
    import sys
    a = QtGui.QApplication(sys.argv)
    
    #t = MyHighlighter()
    #t.show()
    
    window = CWR()
    window.load('data')
#    window.update_topic_list(["978", "1067", "1065"])
#    window.update_document_list(["https://en.wikipedia.org/wiki/Taylor_Swift", "https://en.wikipedia.org/wiki/The_Beatles"])
    
    '''
    web = QtWebKit.QWebView()
    web.load(QUrl('https://en.wikipedia.org/wiki/The_Beatles'))
    web.show()
    '''
    
    sys.exit(a.exec_())
