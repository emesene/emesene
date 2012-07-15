# -*- coding: utf-8 -*-

'''This module contains classes to represent the main page.'''

import PyQt4.QtGui      as QtGui
import PyQt4.QtCore     as QtCore

from gui.qt4ui.Utils import tr

import extension
import gui

class MainPage (QtGui.QWidget, gui.MainWindowBase):
    '''The main page (the one with the contact list)'''
    # pylint: disable=W0612
    NAME = 'MainPage'
    DESCRIPTION = 'The widget used to to dislay the main screen'
    AUTHOR = 'Gabriele "Whisky" Visconti'
    WEBSITE = ''
    # pylint: enable=W0612

    def __init__(self, session, on_new_conversation, set_menu_bar_cb, parent=None):
        '''Constructor'''
        QtGui.QWidget.__init__(self, parent)
        gui.MainWindowBase.__init__(self, session, on_new_conversation)
        # callbacks:
        self._set_menu_bar_cb = set_menu_bar_cb

        # menu objects:
        self._main_menu = None
        self._contact_menu = None
        self._group_menu = None
        self.session = session

        # a widget dic to avoid proliferation of instance variables:
        self._widget_dict = {}
        self._setup_ui()

        # emesene's
        self.contact_list = self._widget_dict['contact_list']
        self.session.config.subscribe(self._on_show_userpanel_changed,
            'b_show_userpanel')
        self._on_show_userpanel_changed(self.session.config.b_show_userpanel)

    def _setup_ui(self):
        '''Instantiates the widgets, and sets the layout'''
        widget_dict = self._widget_dict

        nick_edit_cls = extension.get_default('nick edit')
        avatar_cls = extension.get_default('avatar')
        contact_list_cls = extension.get_default('contact list')
        user_panel_cls = extension.get_default('user panel')

        widget_dict['user_panel'] = user_panel_cls(self.session, self)
        widget_dict['contact_list'] = contact_list_cls(self.session)

        lay = QtGui.QVBoxLayout()
        lay.setContentsMargins (0,0,0,0)
        lay.addWidget(widget_dict['user_panel'])
        lay.addWidget(widget_dict['contact_list'])
        self.setLayout(lay)

        widget_dict['contact_list'].new_conversation_requested.connect(
                                        self.on_new_conversation_requested)

    def _on_show_userpanel_changed(self, value):
        '''callback called when config.b_show_userpanel changes'''
        self._widget_dict['user_panel'].setVisible(value)

    def _on_new_conversation_requested(self, account, on_close):
        '''Slot called when the user doubleclicks
        an entry in the contact list'''
        self.on_new_conversation_requested(account)

    def _on_mail_count_changed(self, count):
        self._widget_dict['user_panel'].set_mail_count(count)

    def replace_extensions(self):
        #FIXME: add extension support
        #below_userlist, below_menu, below_panel
        #we can only import qt extensions
        pass
