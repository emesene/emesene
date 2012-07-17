# -*- coding: utf-8 -*-

'''This module contains classes to represent the main page.'''

import PyQt4.QtGui      as QtGui
import PyQt4.QtCore     as QtCore

from gui.qt4ui.Utils import tr
from gui.qt4ui import widgets

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
        self.session.config.subscribe(self._on_show_userpanel_changed,
            'b_show_userpanel')
        self._on_show_userpanel_changed(self.session.config.b_show_userpanel)

    def _setup_ui(self):
        '''Instantiates the widgets, and sets the layout'''
        widget_dict = self._widget_dict
        contact_list_cls = extension.get_default('contact list')
        user_panel_cls = extension.get_default('user panel')

        widget_dict['user_panel'] = user_panel_cls(self.session, self)
        self.contact_list = contact_list_cls(self.session)
        widget_dict['search_entry'] = widgets.SearchEntry()
        widget_dict['search_entry'].setVisible(False)
        widget_dict['search_entry'].textChanged.connect(
                                    self._on_search_changed)
        widget_dict['user_panel'].search.clicked.connect(
                                    self._on_search_click)

        lay = QtGui.QVBoxLayout()
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(widget_dict['user_panel'])
        lay.addWidget(widget_dict['search_entry'])
        lay.addWidget(self.contact_list)
        self.setLayout(lay)
        self.contact_list.new_conversation_requested.connect(
                                        self.on_new_conversation_requested)

    def _on_search_click(self, status):
        self._widget_dict['search_entry'].setVisible(status)
        self.contact_list.is_searching = status
        if not status:
            #clean search entry when search is disabled
            self._widget_dict['search_entry'].clear()
            self._on_search_changed(QtCore.QString(''))

    def _on_search_changed(self, new_text):
        self.contact_list.filter_text = new_text.toLower()
        if new_text != '':
            self.contact_list.expand_groups()
            self.contact_list.select_top_contact()
        else:
            self.contact_list.un_expand_groups()

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
