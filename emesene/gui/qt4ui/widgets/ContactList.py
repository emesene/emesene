# -*- coding: utf-8 -*-

'''This module contains the ContactList class'''
                            
import PyQt4.QtGui      as QtGui
import PyQt4.QtCore     as QtCore

import extension
import gui

# pylint: disable=W0403
import ContactListDelegate
import ContactListModel
from   ContactListModel import Role


class ContactList (gui.ContactList, QtGui.QTreeView):
    '''A Contactlist Widget'''
    new_conversation_requested = QtCore.pyqtSignal(basestring)
    
    def __init__(self, session, parent=None):
        QtGui.QTreeView.__init__(self, parent)
        dialog = extension.get_default('dialog')
        # We need a model *before* callig gui.ContactList's costructor!!
        self._model = ContactListModel.ContactListModel(self)
        gui.ContactList.__init__(self, session, dialog)
            
        self.setModel(self._model)
        self.setItemDelegate(ContactListDelegate.ContactListDelegate(self))
        self.setAnimated(True)
        self.setHeaderHidden(True)
        self.setVerticalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)
        self.setSortingEnabled(True)
        self.viewport().setStyleSheet( "QWidget{                    \
            background-attachment: fixed;           \
            background-origin: content;             \
            background-position: bottom left;       \
            background-repeat: no-repeat;           \
            background-clip: content;               \
            background-color: rgb(178, 216, 255);   \
            background-image: url(amsn2/ui/front_ends/kde4/background.png);}" )
        #self.verticalScrollBar().setStyleSheet("QScrollBar:vertical{}")
        #self.setIndentation(0)
        self.doubleClicked.connect(self._on_item_double_clicked)


    def edit(self, index, trigger, event):
        '''Returning False disables editing on the View'''
        return False
    
    # [START] -------------------- GUI.CONTACTLIST_OVERRIDE
    
    def add_contact(self, contact, group=None):
        '''Add a contact to the view. Resent to model.'''
        self._model.add_contact(contact, group)
        
    def update_contact(self, contact):
        '''Update a contact in the view. Resent to model'''
        self._model.update_contact(contact)
        
    def add_group(self, group):
        '''Add a group to the view. Resent to model.'''
        self._model.add_group(group)
    
    def fill(self, clear=True): # emesene's
        '''Fill the contact list. Resent to model'''
        print "redirecting to base's fill"
        gui.ContactList.fill(self, clear)
    
    def clear(self):
        '''Clears the contact list. Resent to model.'''
        self._model.clear()
        return True
        
    
        
    # [END] -------------------- GUI.CONTACTLIST_OVERRIDE
        

    def _on_item_double_clicked(self, item):
        '''Slot called when the user double clicks a contact. requests
        a new conversation'''
        contact = self._model.data(item, Role.DataRole).toPyObject()
        self.new_conversation_requested.emit(str(contact.account))






