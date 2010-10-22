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
        QtGui.QWidget.__init__(self, parent)

        self._session = session
        # callbacks:
        self._on_new_conversation = on_new_conversation
        self._on_close = on_close
        self._on_disconnect = on_disconnect
        
        # a widget dic to avoid proliferation of instance variables:
        self._widget_dict = {}
        
        self._setup_ui()
        # emesene's
        self.contact_list = self._widget_dict['contact_list']
        
        # Session's Signals: [Remember to unsubscribe! O_O]
        session.signals.profile_get_succeed.subscribe(
                                self._on_ss_profile_get_succeed)
        
        
        
    def _setup_ui(self):
        '''Instantiates the widgets, and sets the layout'''
        widget_dict = self._widget_dict

        widget_dict['nick_edit'] = Widgets.NickEdit()
        widget_dict['psm_edit'] = Widgets.NickEdit(allow_empty=True, 
            empty_message=i18n(QtCore.QString(
                "<u>Click here to set a personal message...</u>")))
        widget_dict['current_media'] = QtGui.QLabel()
        widget_dict['status_combo'] = Widgets.StatusCombo()
        widget_dict['display_pic'] = Widgets.DisplayPic(
                                        self._session.config_dir, None)
        widget_dict['contact_list'] = Widgets.ContactList(self._session)
        my_info_lay_left = QtGui.QVBoxLayout()
        my_info_lay_left.addWidget(widget_dict['nick_edit'])
        my_info_lay_left.addWidget(widget_dict['psm_edit'])
        my_info_lay_left.addWidget(widget_dict['current_media'])
        my_info_lay_left.addWidget(widget_dict['status_combo'])
        
        my_info_lay = QtGui.QHBoxLayout()
        my_info_lay.addWidget(widget_dict['display_pic'])
        my_info_lay.addLayout(my_info_lay_left)

        lay = QtGui.QVBoxLayout()
        lay.addLayout(my_info_lay)
        lay.addWidget(widget_dict['contact_list'])
        self.setLayout(lay)
        
        # First fill of personal Infos:
        self._on_ss_profile_get_succeed('','')

        widget_dict['nick_edit'].nick_changed.connect(
                                        self._on_set_new_nick)
        widget_dict['psm_edit'].nick_changed.connect(
                                        self._on_set_new_psm)
        widget_dict['status_combo'].status_changed.connect(
                                        self._on_set_new_status)
        #widget_dict['display_pic'].clicked.connect(
        #                                self._on_display_pic_choose_request)

        

    def _on_ss_profile_get_succeed(self, nick, psm):
        '''This method sets the displayed account's info,
        retrieving data from "_session" object'''
        if nick == '':
            nick = self._session.contacts.me.display_name
        if psm == '':
            psm = self._session.contacts.me.message
        status = self._session.contacts.me.status    
        display_pic_path = self._session.config_dir.get_path('last_avatar')
        
        widget_dict = self._widget_dict
        widget_dict['nick_edit'].set_text(nick)
        widget_dict['psm_edit'].set_text(psm)
        widget_dict['status_combo'].set_status(status)
        #print "display pic path: %s" % display_pic_path
        # investigate display pic...
        widget_dict['display_pic']._set_display_pic(display_pic_path)
    
    
    def _on_set_new_nick(self, nick):
        '''Slot called when user tries to se a new nick'''
        self._session.set_nick(nick)
        # to be completed handling the subsequent signal from e3
        
    def _on_set_new_psm(self, psm):
        '''Slot called when the user tries to set a new psm'''
        self._session.set_message(psm)
        # to be completed handling the subsequent signal from e3
        
    def _on_set_new_status(self, status):
        '''Slot called when the user tries to set a new status'''
        self._session.set_status(status)
        # to be completed handling the subsequent signal from e3

        
        






