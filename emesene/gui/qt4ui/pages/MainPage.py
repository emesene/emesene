# -*- coding: utf-8 -*-

'''This module contains classes to represent the main page.'''

import time

import PyQt4.QtGui      as QtGui
import PyQt4.QtCore     as QtCore

import extension


class MainPage (QtGui.QWidget):
    '''The main page (the one with the contact list)'''
    # pylint: disable=W0612
    NAME = 'MainPage'
    DESCRIPTION = 'The widget used to to dislay the main screen'
    AUTHOR = 'Gabriele "Whisky" Visconti'
    WEBSITE = ''
    # pylint: enable=W0612
    
    def __init__(self,  session, on_new_conversation, on_close,
                on_disconnect, set_menu_bar_cb, parent=None):
        '''Constructor'''
        QtGui.QWidget.__init__(self, parent)

        self._session = session
        # callbacks:
        print on_new_conversation
        self._on_new_conversation = on_new_conversation
        self._on_close = on_close
        self._on_disconnect = on_disconnect
        self._set_menu_bar_cb = set_menu_bar_cb
        
        # menu objects:
        self._main_menu = None
        self._contact_menu = None
        self._group_menu = None

        
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
        
        nick_edit_cls       = extension.get_default('nick edit')
        status_combo_cls    = extension.get_default('status combo')
        avatar_cls          = extension.get_default('avatar')
        contact_list_cls    = extension.get_default('contact list')
        
        widget_dict['nick_edit'] = nick_edit_cls()
        widget_dict['psm_edit'] = nick_edit_cls(allow_empty=True, 
            empty_message=QtCore.QString(
                "<u>Click here to set a personal message...</u>"))
        widget_dict['current_media'] = QtGui.QLabel()
        widget_dict['status_combo'] = status_combo_cls()
        widget_dict['display_pic'] = avatar_cls(self._session)
        widget_dict['contact_list'] = contact_list_cls(self._session)
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
        widget_dict['display_pic'].clicked.connect(
                                        self._on_display_pic_clicked)
        widget_dict['contact_list'].new_conversation_requested.connect(
                                        self._on_new_conversation_requested)
                                        
    
        

    def _on_ss_profile_get_succeed(self, nick, psm):
        '''This method sets the displayed account's info,
        retrieving data from "_session" object'''
        if nick == '':
            nick = self._session.contacts.me.display_name
        if psm == '':
            psm = self._session.contacts.me.message
        status = self._session.contacts.me.status    
        
        widget_dict = self._widget_dict
        widget_dict['nick_edit'].set_text(nick)
        widget_dict['psm_edit'].set_text(psm)
        widget_dict['status_combo'].set_status(status)
        #print "display pic path: %s" % display_pic_path
        # investigate display pic...
        widget_dict['display_pic'].set_display_pic_of_account()
        
    def _on_new_conversation_requested(self, account):
        '''Slot called when the user doubleclicks 
        an entry in the contact list'''
        print account
        conv_id = time.time()
        self._on_new_conversation(conv_id, [account], False) 
        # TODO: shouldn't this go somewhere else?!
        # calls the e3 handler
        self._session.new_conversation(account, conv_id)
    
    
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
        
    def _on_display_pic_clicked(self):
        '''Slot called when the user clicks the display pic. It shows
        the AvatarChooser'''
        chooser_cls = extension.get_default('avatar chooser')
        chooser = chooser_cls(self._session)
        chooser.exec_()

        
        






