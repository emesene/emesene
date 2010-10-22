# -*- coding: utf-8 -*-

'''This module contains the NickEdit class'''

import PyKDE4.kdeui     as KdeGui
import PyKDE4.kdecore   as KdeCore
from PyKDE4.kdecore import i18n
import PyQt4.QtGui      as QtGui
import PyQt4.QtCore     as QtCore
from PyQt4.QtCore   import Qt


class NickEdit(QtGui.QStackedWidget):
    '''A Nice nick / psm editor'''
    nick_changed = QtCore.pyqtSignal(basestring)
    def __init__(self, allow_empty=False, 
                 empty_message=i18n(QtCore.QString("Click here to write")),
                 parent=None):
        print "Nick Edit Consctructor"
        QtGui.QStackedWidget.__init__(self, parent)
        print "   0"
        self._allow_empty = allow_empty
        self._empty_message = QtCore.QString("<u>") + \
                              empty_message + \
                              QtCore.QString("</u>")
        self._is_empty_message_displayed = False
        print "   1"
        self.line_edit = KdeGui.KLineEdit()
        print "   1.2"
        self.label = QLabelEmph(i18n(QtCore.QString("If you see this, " \
                            "please invoke setText on KNickEdit.")))
        print "   1.3"
        self.set_text(QtCore.QString())
        print "   2"
        self.addWidget(self.line_edit)
        self.addWidget(self.label)
        self.setCurrentWidget(self.label)
        self.setSizePolicy(QtGui.QSizePolicy.Expanding, 
                           QtGui.QSizePolicy.Fixed)
        print "   3"
        self.label.clicked.connect(self._on_label_clicked)
        self.line_edit.editingFinished.connect(self._on_line_edited)
        print "End of nick edit constructor"
        
        
    def text(self):
        '''Returns the displayed text'''
        if self._is_empty_message_displayed:
            return QtCore.QString()
        return self.label.text()
        
        
    def set_text(self, text):
        '''Displays the given text'''
        #NOTE: do we have to set also the KLineEdit's text? 
        #<-> method could be called while the KLEdit is active? 
        text = QtCore.QString(text) 
        if not text.isEmpty():
            self._is_empty_message_displayed = False
            self.label.setText(text)
        elif self._allow_empty:
            self._is_empty_message_displayed = True
            self.label.setText(self._empty_message)


    def _on_label_clicked(self):
        '''Slot called when the user clicks on the label of 
        this widget'''
        if self._is_empty_message_displayed:
            text = QtCore.QString()
        else:
            text = self.label.text()
        self.line_edit.setText(text)
        self.setCurrentWidget(self.line_edit)
        self.line_edit.setFocus(Qt.MouseFocusReason)
    
    
    def _on_line_edited(self):
        '''Slot called when the user finishes editing the nick'''
        text = self.line_edit.text()
        self.set_text(text)
        #if the text is empty, and it is not allowed 
        # to be so, the label remains unchanged
        self.setCurrentWidget(self.label)
        self.nick_changed.emit(str(text))




class QLabelEmph(QtGui.QLabel):
    '''Convenience class for a more interestin QLabel behaviour'''
    _LE = QtCore.QString("<u><em>")
    _RI = QtCore.QString("</em></u>")
    
    clicked = QtCore.pyqtSignal()
    def __init__(self, text=QtCore.QString(), parent = None):
        '''Constructor'''
        QtGui.QLabel.__init__(self)
        self._text = QtCore.QString()
        self.setText(text)
        
# -------------------- QT_OVERRIDE
    
    #you can pass either a pythonic string or a QString
    def setText(self, text): 
        # pylint: disable=C0103
        '''sets the text'''
        text = QtCore.QString(text)
        self._text = QtCore.QString(text) 
        QtGui.QLabel.setText(self, text)

    #returns a QString
    def text(self): 
        # pylint: disable=C0103
        '''Returns the text'''
        return self._text
        
    def mousePressEvent(self, event):
        # pylint: disable=C0103
        '''Handles mouse presses'''
        QtGui.QLabel.mousePressEvent(self, event)
        if event.button() == Qt.LeftButton:
            self.clicked.emit()    
            
    #received even if mouse tracking not explicitly enabled
    def enterEvent(self, event): 
        # pylint: disable=C0103
        '''Handles mouse-in events'''
        QtGui.QLabel.setText(self, QLabelEmph._LE + self._text + QLabelEmph._RI)
        
    #received even if mouse tracking not explicitly enabled
    def leaveEvent(self, event): 
        # pylint: disable=C0103
        '''Handles mouse-out events'''
        QtGui.QLabel.setText(self, self._text)
        

