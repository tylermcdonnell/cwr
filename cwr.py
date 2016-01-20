import itertools
import requests

from bs4 import BeautifulSoup
from difflib import SequenceMatcher
from abc import abstractmethod
from collections import namedtuple, defaultdict

from PyQt4 import QtGui
from PyQt4 import QtWebKit
from PyQt4.Qt import QUrl, QCheckBox



class CWR(QtGui.QWidget):
    
    def __init__(self):
        super(CWR, self).__init__()
        
        self.init_UI()
        
    def init_UI(self):

        test_rationales = { '0000001' : "The Beatles were an English rock band, formed in Liverpool in 1960. With members John Lennon, Paul McCartney, George Harrison and Ringo Starr, they became widely regarded as the foremost and most influential act of the rock era.", 
                            '0000002' : "The Beatles were an English rock band, formed in Liverpool in 1960 they came to be perceived as an embodiment of the ideals shared by the counterculture of the 1960s",
                            '0000003' : "The Beatles were an English rock band The Beatles built their reputation playing clubs in Liverpool and Hamburg over a three-year period from 1960" }
        #test_text = "The Beatles were an English rock band, formed in Liverpool in 1960. With members John Lennon, Paul McCartney, George Harrison and Ringo Starr, they became widely regarded as the foremost and most influential act of the rock era.[1] Rooted in skiffle, beat, and 1950s rock and roll, the Beatles later experimented with several genres, ranging from pop ballads and Indian music to psychedelia and hard rock, often incorporating classical elements in innovative ways. In the early 1960s, their enormous popularity first emerged as Beatlemania, but as the group's music grew in sophistication, led by primary songwriters Lennon and McCartney, they came to be perceived as an embodiment of the ideals shared by the counterculture of the 1960s. The Beatles built their reputation playing clubs in Liverpool and Hamburg over a three-year period from 1960, with Stuart Sutcliffe initially serving as bass player. The core of Lennon, McCartney and Harrison went through a succession of drummers, most notably Pete Best, before asking Starr to join them. Manager Brian Epstein moulded them into a professional act and producer George Martin enhanced their musical potential. They gained popularity in the United Kingdom after their first hit, Love Me Do, in late 1962. They acquired the nickname the Fab Four as Beatlemania grew in Britain over the following year, and by early 1964 they had become international stars, leading the British Invasion of the United States pop market. From 1965 onwards, the Beatles produced what many consider their finest material, including the innovative and widely influential albums Rubber Soul (1965), Revolver (1966), Sgt. Pepper's Lonely Hearts Club Band (1967), The Beatles (commonly known as the White Album, 1968) and Abbey Road (1969). After their break-up in 1970, they each enjoyed successful musical careers of varying lengths. McCartney and Starr, the surviving members, remain musically active. Lennon was shot and killed in December 1980, and Harrison died of lung cancer in November 2001. According to the RIAA, the Beatles are the best-selling music artists in the United States, with 178 million certified units. They have had more number-one albums on the British charts and sold more singles in the UK than any other act. In 2008, the group topped Billboard magazine's list of the all-time most successful Hot 100 artists; as of 2015, they hold the record for most number-one hits on the Hot 100 chart with twenty. They have received ten Grammy Awards, an Academy Award for Best Original Song Score and fifteen Ivor Novello Awards. Collectively included in Time magazine's compilation of the twentieth century's 100 most influential people, they are the best-selling band in history, with estimated sales of over 600 million records worldwide.[2][3] The group was inducted into the Rock and Roll Hall of Fame in 1988, with all four being inducted individually as well from 1994 to 2015."

        test_url = 'https://en.wikipedia.org/wiki/The_Beatles'
        content  = requests.get(test_url).text        
        content
        test_text = BeautifulSoup(content, "html.parser").get_text()
      
        grid = QtGui.QGridLayout()
        grid.setSpacing(10)
            
        # Topic View - contains topic list.
        topic_view = QtGui.QGroupBox("Topics")
        topic_layout = QtGui.QVBoxLayout()
        topic_view.setLayout(topic_layout)
        grid.addWidget(topic_view, 0, 0)
        
        # Topic List
        self._topic_list = QtGui.QListWidget()
        self._topic_list.setSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Minimum)
        self._topic_list.itemClicked.connect(self.topic_selected)
        topic_layout.addWidget(self._topic_list)
        
        # Document View - contains document list.
        document_view = QtGui.QGroupBox("Documents")
        document_layout = QtGui.QVBoxLayout()
        document_view.setLayout(document_layout)
        grid.addWidget(document_view, 0, 1)
        
        # Document List
        self._document_list = QtGui.QListWidget()
        self._document_list.setSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Minimum)
        self._document_list.itemClicked.connect(self.document_selected)
        document_layout.addWidget(self._document_list)
        
        # Rationale View - Contains the rationale check boxes, text display, and statistics.
        rationale_view = QtGui.QGridLayout()
        grid.addLayout(rationale_view, 0, 2)
        
        # Rationale Display
        self._rationale_display = HighlightBox()
        rationale_view.addWidget(self._rationale_display, 2, 0)
        self._rationale_display.set_text(test_text)
        
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
        
        self.setLayout(grid)
        self.setGeometry(300, 300, 1000, 1000)
        self.setWindowTitle("The Crowdworker's Rationale")
        self.show()

    def load_rationales(self, rationales):
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
            self._rationales.append(container(rationale = r, color = c, display = d))
            self._selection_layout.addWidget(d)

    def rationale_selection_changed(self, state):
        '''
        Handler function called when a user selects or deselects a rationale
        check box. Inititates an expensive rationale overlap computation.
        '''
        # Locate selected rationales.
        selected = []
        for box in self._rationale_boxes:
            if box.isChecked:
                selected.extend([r for r in self._rationales if box.text == r.label])

        # Compute overlap.
        result = Rationale.compute_overlap(self._text, selected)

        # Update display.
        for match in result.matches:
            # Highlight with assigned color for rationale.
            pass
        for overlap in result.matches:
            # Highlight with overlap color.
            pass
    
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
        
    def topic_selected(self, item):
        '''
        Handler function called when a user selects a topic in the
        Topic View.
        '''
        print (item.text())
        
    def document_selected(self, item):
        '''
        Handler function called when a user select a doicment in the
        Document View.
        '''
        print (item.text())
        
    def update_rationale_text(self, text):
        self._rationale_display.set_text(text)
    
    def highlight_rationale(self, text):
        self._rationale_display.highlight(text)
    
class Rationale(object):
    '''
    Provides various utilities for analyzing similarity of rationales
    with respect to each and a source text.
    '''

    def __init__(self, label, rationale):
        self.label     = label
        self.rationale = rationale

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
        
        matches -- Dictionary of key-[string] pairs, where the list of strings 
                   for a key are substrings found between the string provided 
                   for that key and the source text.
        overlap -- List of strings that are common to two or more rationales.
        '''
        result = namedtuple('RationaleComputation', ['matches', 'overlap'])
        
        # Compute matches
        matches  = defaultdict(list)
        for rationale in rationales:
            for match in SequenceMatcher(None, text, rationale).get_matching_blocks():
                start  = match[0]
                length = match[2]
                matches.append({ key : text[start : start + length] })
                
        # Compute overlap in rationales.
        overlap = []
        for pair in itertools.combinations(rationales, 2):
            for match in SequenceMatcher(None, pair[0], pair[1]).get_matching_blocks():
                start  = match[0]
                length = match[2]
                overlap.append(pair[0][start : start + length])
                
        return result(matches = matches, overlap = overlap)
                 
class HighlightInterface(object):
    '''
    '''
    
    @abstractmethod
    def highlight(self, string, color):
        '''
        '''
        pass
    
    @abstractmethod
    def clear(self):
        '''
        '''
        pass    
    
class HighlightWebView(QtWebKit.QWebView, HighlightInterface):
    '''
    A special viewer for web URLs which provides highlight functionality.
    '''

    def highlight(self, string, color):
        '''
        '''
        pass

    def clear(self):
        '''
        '''
        pass
    
class HighlightBox(QtGui.QTextEdit, HighlightInterface):
    '''
    A special text viewer which provides highlight functionality.
    '''
    def __init__(self, parent=None):
        super(HighlightBox, self).__init__(parent)
        
        # Setup the text editor
        self.format = QtGui.QTextCharFormat()
        
        # The raw display text.
        self._text = None
        self.set_text("Select a topic and document to view.")

    def _set_color(self, color):
        self.format.setBackground(QtGui.QBrush(color))
        
    def _highlight(self, start, length, color):
        self._set_color(color)
        cursor = self.textCursor()
        cursor.setPosition(start)
        cursor.movePosition(QtGui.QTextCursor.Right, 1, n = length)
        cursor.mergeCharFormat(self.format)
        
    def set_text(self, text):
        self._text = text
        self.setText(text)
    
    def highlight(self, string, color):
        '''
        Highlights specified text in display.

        Arguments:

        color -- QColor used for highlighting.
        '''
        for match in SequenceMatcher(None, self._text, string).get_matching_blocks():
            start  = match[0]
            length = match[2]
            self._highlight(start, length, color)
            
    def clear(self):
        '''
        Clears all highlights.
        '''
        self._highlight(0, len(self._text), QtGui.QColor("white"))
        


        
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
