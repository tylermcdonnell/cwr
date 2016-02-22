import itertools
import requests

from datamodel import DataModel

from threading import Thread
from bs4 import BeautifulSoup
from difflib import SequenceMatcher
from abc import abstractmethod
from collections import namedtuple, defaultdict
from highlightinterface import HighlightWebView, HighlightBox

from PyQt4 import QtGui
from PyQt4 import QtWebKit
from PyQt4.Qt import QUrl, QCheckBox

class CWR(QtGui.QWidget):
    
    def __init__(self):
        super(CWR, self).__init__()

        self._dm = DataModel()              # Primary data model.

        self._topics    = []                # All topics for which judgments have been loaded.
        self._documents = []                # Documents for which we have a judgment for the
                                            # currently selected topic.

        self._selected_topic    = None      # Currently selected topic.
        self._selected_document = None      # Currently selected document.
        self._rationales        = None      # Rationales for the currently selected document.

        self._display_text = None           # Text of document being manipulated.

        # For testing WebView.
        ''' 
        test_url = 'https://en.wikipedia.org/wiki/The_Beatles'
        content  = requests.get(test_url).text        
        content
        test_text = BeautifulSoup(content, "html.parser").get_text()
        self._display_text = test_text
        '''
        
        self.init_UI()
        
    def init_UI(self):        
        grid = QtGui.QGridLayout()
        grid.setSpacing(10)
            
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
        self._topic_list.itemClicked.connect(self.topic_selected)
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
        self._document_list.setSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Minimum)
        self._document_list.itemClicked.connect(self._document_selected)
        document_layout.addWidget(self._document_list)
        
        #####################################
        # Rationale View                    #
        #####################################
        # Contains the rationale check boxes, text display, and statistics.
        rationale_view = QtGui.QGridLayout()
        grid.addLayout(rationale_view, 0, 2)
        
        # Rationale Display
        web = HighlightWebView()
        web.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        web.load(QUrl('https://en.wikipedia.org/wiki/The_Beatles'))
        web.show()
        self._rationale_display = web
        #self._rationale_display = HighlightBox()
        rationale_view.addWidget(self._rationale_display, 2, 0)
        #self._rationale_display.set_text(test_text)
        
        # Rationale Selection
        selection_view = QtGui.QGroupBox("Selection")
        self._selection_layout = QtGui.QHBoxLayout()
        selection_view.setLayout(self._selection_layout)
        rationale_view.addWidget(selection_view, 1, 0)
        rationales = []
        for label, rationale in test_rationales.items():
            rationales.append(Rationale(label, rationale))
        self.load_rationales(rationales)
        
        # Statistics View
        self._stat_display = QtGui.QGroupBox("Statistics")
        stat_layout = QtGui.QVBoxLayout()
        stat_label1 = QtGui.QLabel()
        stat_label1.setText("Here is where statistics will be displayed.")
        stat_layout.addWidget(stat_label1)
        self._stat_display.setLayout(stat_layout)
        rationale_view.addWidget(self._stat_display, 3, 0)
        
        #####################################
        # Main Application Properties       #
        #####################################
        self.setLayout(grid)
        self.setGeometry(300, 300, 1000, 1000)
        self.setWindowTitle("The Crowdworker's Rationale")
        self.show()

    def _load_rationales(self, rationales):
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

        # Re-generate rationale data structures.
        self._rationales = []
        for i in range(len(rationales)):
            r = rationales[i]
            c = colors[min(i, len(colors) - 1)]
            d = QCheckBox(r.label)
            d.stateChanged.connect(self._rationale_selection_changed)
            self._rationales.append(container(rationale = r, color = c, display = d))
            self._selection_layout.addWidget(d)

#########################################################################################
# Updateable UI Elements                                                                #
#########################################################################################

    def update_topic_list(self, topics):
        '''
        Updates the topics displayed in Topic View.
        '''
        self._topic_list.clear()
        self._topic_list.addItems(topics)
        self._topic_list.sortItems()   
        
    def update_document_list(self, documents):
        '''
        Updates the documents displayed in Document View.
        '''
        self._document_list.clear()
        self._document_list.addItems(documents)
        self._document_list.sortItems() 

    def _update_rationale_display(self):
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
                
        # Compute overlap.
        just_rationales = [r.rationale for r in selected]
        result = Rationale.compute_overlap(self._text, just_rationales)

        # Update display with rationale matches.
        display = self._rationale_display
        display.clear()
        for rationale, matches in result.matches.items():
            # Map back to container to find correct color.
            color = [c.color for c in selected if c.rationale is rationale][0]
            
            # Highlight in display.
            for match in matches:
                display.highlight(match, color)
            
        # Update display with overlap between rationales.
        overlap_color = QtGui.QColor(255, 255, 102) # Light Yellow
        for string in result.overlap:
            display.highlight(string, overlap_color)

        # Re-enable rationale selection.
        for this_rationale in self._rationales:
            this_rationale.display.setEnabled(True)

        print ("Finished updating rationale display.")
        
    def update_rationale_text(self, text):
        self._rationale_display.set_text(text)
    
    def highlight_rationale(self, text):
        self._rationale_display.highlight(text)

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
        documents = self._dm.judged_documents_by_topic(item)
        update_document_list(documents)

    def _document_selected(self, item):
        '''
        Handler function - user select a document in the Document View.
        
        Loads the text from that document into the rationale display
        and computes statistics for that document.
        '''
        print (item.text())

    def _rationale_selection_changed(self, state):
        '''
        Handler function called when a user selects or deselects a rationale
        check box.
        '''
        worker = Thread(target=self._update_rationale_display)
        worker.start()
    
    
class Rationale(object):
    '''
    Provides various utilities for analyzing similarity of rationales
    with respect to each and a source text.
    '''

    def __init__(self, label, rationale):
        self.label = label
        self.text  = rationale

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
        result = namedtuple('RationaleComputation', ['matches', 'overlap'])
        
        # Compute matches
        matches  = defaultdict(list)
        for rationale in rationales:
            for match in SequenceMatcher(None, text, rationale.text).get_matching_blocks():
                start  = match[0]
                length = match[2]
                matches[rationale].append(text[start : start + length])
                
        # Compute overlap in rationales.
        overlap = []
        for pair in itertools.combinations(rationales, 2):
            string1 = pair[0].text
            string2 = pair[1].text
            for match in SequenceMatcher(None, string1, string2).get_matching_blocks():
                start  = match[0]
                length = match[2]
                overlap.append(string1[start : start + length])
                
        return result(matches = matches, overlap = overlap)
                 


        
if __name__ == "__main__":
    import sys
    a = QtGui.QApplication(sys.argv)
    
    #t = MyHighlighter()
    #t.show()
    
    window = CWR()
    window.update_topic_list(["978", "1067", "1065"])
    window.update_document_list(["https://en.wikipedia.org/wiki/Taylor_Swift", "https://en.wikipedia.org/wiki/The_Beatles"])
    
    '''
    web = QtWebKit.QWebView()
    web.load(QUrl('https://en.wikipedia.org/wiki/The_Beatles'))
    web.show()
    '''
    
    sys.exit(a.exec_())
