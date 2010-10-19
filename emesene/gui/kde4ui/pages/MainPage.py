# -*- coding: utf-8 -*-

'''This module contains classes to represent the main page.'''

import PyKDE4.kdeui     as KdeGui
from PyKDE4.kdecore import i18n
import PyQt4.QtGui      as QtGui
import PyQt4.QtCore     as QtCore
from PyQt4.QtCore   import Qt

import gui.kde4ui.widgets as Widgets


class MainPage (QtGui.QWidget):
    '''The main page (the one with the contact list)'''
    # pylint: disable=W0612
    NAME = 'MainPage'
    DESCRIPTION = 'The widget used to to dislay the main screen'
    AUTHOR = 'Gabriele Whisky Visconti'
    WEBSITE = ''
    # pylint: enable=W0612
    
    def __init__(self,  session, on_new_conversation, on_close,
                on_disconnect, parent=None):
        '''Constructor'''
        print "Main Page Constructor"
        QtGui.QWidget.__init__(self, parent)

        self._session = session
        print 'Session is: %s' % self._session
        # callbacks:
        self._on_new_conversation = on_new_conversation
        self._on_close = on_close
        self._on_disconnect = on_disconnect
        # a widget dic to avoid proliferation of instance variables:
        self._widget_dict = {}
        
        self._setup_ui()
        # emesene's
        self.contact_list = self._widget_dict['contact_list'].model() 
        print "End of MainPage Constructor"
        
        
    def _setup_ui(self):
        '''Instantiates the widgets, and sets the layout'''
        print "setup ui"
        widget_dict = self._widget_dict
        print "   0"
        widget_dict['nick_edit'] = Widgets.NickEdit()
        print "   1"
        widget_dict['psm_edit'] = Widgets.NickEdit(allow_empty=True, 
            empty_message=i18n(QtCore.QString(
                "<u>Click here to set a personal message...</u>")))
        print "   2"
        widget_dict['current_media'] = QtGui.QLabel()
        print "   3"
        widget_dict['status_combo'] = Widgets.StatusCombo()
        print "   4"
        widget_dict['display_pic'] = Widgets.DisplayPic(
                                        self._session.config_dir, None)
        print "   5"
        widget_dict['contact_list'] = Widgets.ContactList(self._session)
        print "   A"
        my_info_lay_left = QtGui.QVBoxLayout()
        my_info_lay_left.addWidget(widget_dict['nick_edit'])
        my_info_lay_left.addWidget(widget_dict['psm_edit'])
        my_info_lay_left.addWidget(widget_dict['current_media'])
        my_info_lay_left.addWidget(widget_dict['status_combo'])
        print "   B"
        my_info_lay = QtGui.QHBoxLayout()
        my_info_lay.addWidget(widget_dict['display_pic'])
        my_info_lay.addLayout(my_info_lay_left)
        print "   C"
        lay = QtGui.QVBoxLayout()
        lay.addLayout(my_info_lay)
        lay.addWidget(widget_dict['contact_list'])
        self.setLayout(lay)
        print "  signals"
        #widget_dict['nick_edit'].nickChanged.connect(
                                        #qcs per cambia  nick O_O)
        #widget_dict['psm_edit'].nickChanged.connect(
                                        #qualcosa O_O)
        #widget_dict['status_combo'].status_changed.connect(
        #                                contactListWindow.onNewPresenceSet)
        #widget_dict['display_pic'].clicked.connect(
        #                                self._on_display_pic_choose_request)
        print "End of setup ui"
        

    def onMyInfoUpdated(self, view):
        self.nick.setText(view.nick.to_HTML_string())
        #Think carefully: i think we can remove this  
        #(look at KPresenceComboBox.setText()'s implementation)
        if not QString(str(view.psm)).isEmpty(): 
            self.psm.setText(view.psm.to_HTML_string())
        if len(view.dp.imgs) > 0:
            _, path = view.dp.imgs[0]
            self.displayPic.setDisplayPic(path)
        self.currentMedia.setText(view.current_media.to_HTML_string())
        #TODO: view.presence holds a string.... 
        #shouldn't it hold a papyon.Presence?
        #this could be used when it will hold a papyon.Presence -->
        #self.presence_combo.setPresence(view.presence) 
        self.presenceCombo.setCurrentIndex(
                    self.presenceCombo.findText(view.presence.capitalize()))






