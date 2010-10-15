# -*- coding: utf-8 -*-

''' This module contains the PreseceCombo class'''


import PyKDE4.kdeui     as KdeGui
from PyKDE4.kdecore import i18n
import PyQt4.QtGui      as QtGui
import PyQt4.QtCore     as QtCore

import e3
import gui

#Maybe we need another class which makes presence info more abstract?
#(a Qt Delegate?! Does KComboBox support them?)
#TODO: put inizialization out of constructor, add setPresenceValues method.

class PresenceCombo(KdeGui.KComboBox):
    '''A presence selection widget'''

    #papyon.Presence is an enumeration of strings
    presence_changed = QtCore.pyqtSignal(int)

    def __init__(self, parent=None):
        '''Constructor'''
        KdeGui.KComboBox.__init__(self, parent)

        self._presence_strings = {}
        self._presence_values = e3.status.ALL

        for presence_key in self._presence_values:
            self._presence_strings[presence_key] =  \
                    i18n( e3.status.STATUS[presence_key].capitalize() )

        #presence_key is of e3.status.ALL type
        #presenceValue is a dict wich associates a e3.status with a string
        theme = gui.Theme()
        for presence_key in self._presence_values:
            icon_path = theme.status_icons[presence_key]
            self.addItem(QtGui.QIcon(icon_path),
                         self._presence_strings[presence_key], presence_key)

        self.set_presence(e3.status.ONLINE)
        self.currentIndexChanged.connect(self._emit_presence_changed)


    def set_presence(self, presence):
        """Sets the presence in the PresenceCombo.

        @type presence: e3.status
        @param presence: the presence to set
        """
        if not presence in e3.status.ALL:
            return
        KdeGui.KComboBox.setCurrentIndex(self,  self.findData(presence))

    def presence(self):
        '''Return the presence selected'''
        #we don't say "getPresence" to make it more Qt-Stylish
        return self.itemData( self.currentIndex() ).toPyObject()


    def _emit_presence_changed(self, index=None):
        ''' emits a presence_changes signal '''
        self.presence_changed.emit( self.itemData(index).toPyObject() )


# -------------------- QT_OVERRIDE

    def setCurrentIndex(self, index):
        '''sets the presence by the index'''
        # pylint: disable=C0103
        print "Oh, boy.... what an ugly way to set the displayed presence!<br>\
                    Come on, use set_presence() instead! :("
        #the personalinfoview holds a string... so this is necessary...
        #maybe this will be removed in the future... I hope...
        KdeGui.KComboBox.setCurrentIndex(self, index)




