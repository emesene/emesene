# -*- coding: utf-8 -*-

''' This module contains the PreseceCombo class'''


import PyKDE4.kdeui     as KdeGui
from PyKDE4.kdecore import i18n
import PyQt4.QtGui      as QtGui
import PyQt4.QtCore     as QtCore

import e3
import gui

#Maybe we need another class which makes status info more abstract?
#(a Qt Delegate?! Does KComboBox support them?)
#TODO: put inizialization out of constructor, add setstatusValues method.

class StatusCombo(KdeGui.KComboBox):
    '''A presence selection widget'''

    status_changed = QtCore.pyqtSignal(int)

    def __init__(self, parent=None):
        '''Constructor'''
        KdeGui.KComboBox.__init__(self, parent)

        self._status_strings = {}
        self._status_values = e3.status.ALL

        for status_key in self._status_values:
            self._status_strings[status_key] =  \
                    i18n( e3.status.STATUS[status_key].capitalize() )

        #status_key is of e3.status.ALL type
        #statusValue is a dict wich associates a e3.status with a string
        theme = gui.Theme()
        for status_key in self._status_values:
            icon_path = theme.status_icons[status_key]
            self.addItem(QtGui.QIcon(icon_path),
                         self._status_strings[status_key], status_key)

        self.set_status(e3.status.ONLINE)
        self.currentIndexChanged.connect(self._emit_status_changed)


    def set_status(self, status):
        """Sets the status in the StatusCombo.

        @type status: e3.status
        @param status: the status to set
        """
        if not status in e3.status.ALL:
            return
        KdeGui.KComboBox.setCurrentIndex(self,  self.findData(status))

    def status(self):
        '''Return the status selected'''
        #we don't say "get_status" to make it more Qt-Stylish
        return self.itemData( self.currentIndex() ).toPyObject()


    def _emit_status_changed(self, index=None):
        ''' emits a status_changed signal '''
        self.status_changed.emit( self.itemData(index).toPyObject() )


# -------------------- QT_OVERRIDE

    def setCurrentIndex(self, index):
        '''sets the status by the index'''
        # pylint: disable=C0103
        print "Oh, boy.... what an ugly way to set the displayed status!<br>\
                    Come on, use set_status() instead! :("
        #the personalinfoview holds a string... so this is necessary...
        #maybe this will be removed in the future... I hope...
        KdeGui.KComboBox.setCurrentIndex(self, index)




