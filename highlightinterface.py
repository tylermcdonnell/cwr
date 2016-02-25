from abc import abstractmethod

from PyQt4 import QtCore
from PyQt4 import QtGui
from PyQt4 import QtWebKit
from PyQt4.Qt import QUrl, QCheckBox


class HighlightInterface(object):
    
    @abstractmethod
    def highlight(self, string, color=None):
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
    
    def __init__(self, parent=None):
        super(HighlightWebView, self).__init__(parent)
        
        # The raw display text.
        self._text = None
        
    def show_html(self):
        html = BeautifulSoup(self.page().mainFrame().toHtml(), "html.parser")
        print (html.encode('utf-8'))
        print (html.get_text().encode('utf-8'))

    def load(self, URL):
        '''
        Loads the specified URL and stores its text for computations.
        '''
        super(HighlightWebView, self).load(URL)
        #print (self.page().mainFrame().toHtml())

    def get_text(self):
        return self.page().mainFrame().toHtml().toUtf8()

    def highlight(self, string, color=None):
        '''
        Highlight all occurrences of specified string.
        '''
        string = QtCore.QString(string)
        print ("Highlighting: %s" % string)
        return self.findText(string, QtWebKit.QWebPage.HighlightAllOccurrences)

    def clear(self):
        '''
        Clears highlights.
        '''
        print ("Clearing highlights.")
        return self.findText('', QtWebKit.QWebPage.HighlightAllOccurrences)
    
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
