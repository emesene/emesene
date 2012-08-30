'''base implementation of a main window'''
# -*- coding: utf-8 -*-

#    This file is part of emesene.
#
#    emesene is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 3 of the License, or
#    (at your option) any later version.
#
#    emesene is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with emesene; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import extension

import Desktop
import webbrowser
import time
import logging
log = logging.getLogger('gui.base.MainWindowBase')


class MainWindowBase(object):
    '''a widget that contains all the components inside'''

    def __init__(self, session, on_new_conversation):
        '''class constructor'''

        self.session = session
        self.on_new_conversation = on_new_conversation

        self.session.signals.mail_count_changed.subscribe(self._on_mail_count_changed)
        self.session.signals.social_request.subscribe(self._on_social_request)
        self.session.signals.broken_profile.subscribe(self._on_broken_profile)

        self.session.config.subscribe(self._on_show_userpanel_changed,
            'b_show_userpanel')

        self.below_menu = extension.get_and_instantiate('below menu', self)
        self.below_panel = extension.get_and_instantiate('below panel', self)
        self.below_userlist = extension.get_and_instantiate('below userlist',
                                                            self)
        #extension changes
        extension.subscribe(self._on_below_userlist_changed, "below userlist")
        extension.subscribe(self._on_below_menu_changed, "below menu")
        extension.subscribe(self._on_below_panel_changed, "below panel")

    def _replace_widget(self, widget, new_extension, pos):
        '''replace widget with and instance of new_extension'''
        pass

    def _on_below_userlist_changed(self, new_extension):
        if type(self.below_userlist) != new_extension:
            self.below_userlist = self._replace_widget(
                    self.below_userlist, new_extension, 6)

    def _on_below_menu_changed(self, new_extension):
        if type(self.below_menu) != new_extension:
            self.below_menu = self._replace_widget(
                    self.below_menu, new_extension, 1)

    def _on_below_panel_changed(self, new_extension):
        if type(self.below_panel) != new_extension:
            self.below_panel = self._replace_widget(
                    self.below_panel, new_extension, 3)

    def on_mail_click(self):
        if self.session.config.b_open_mail_in_desktop:
            webbrowser.open("mailto:")
        else:
            Desktop.open(self.session.get_mail_url())

    def on_new_conversation_requested(self, account):
        '''Slot called when the user doubleclicks
        an entry in the contact list'''
        cid = time.time()
        self.on_new_conversation(cid, [account], False)
        #this calls the e3 Handler
        self.session.new_conversation(account, cid)

    def _on_mail_count_changed(self, count):
        '''update ui widget with new email count'''
        pass

    def _on_social_request(self, conn_url):
        pass

    def _on_broken_profile(self, profile_url):
        '''called when a person has a broken profile'''
        dialog = extension.get_default('dialog')
        dialog.broken_profile(self.session.close, profile_url)

    def _on_show_userpanel_changed(self, value):
        pass

    def unsubscribe_signals(self):
        '''callback called when the disconnect option is selected'''
        self.session.signals.mail_count_changed.unsubscribe(
            self._on_mail_count_changed)
        self.session.signals.broken_profile.unsubscribe(self._on_broken_profile)
        self.session.signals.social_request.unsubscribe(self._on_social_request)

        #extension changes
        extension.unsubscribe(self._on_below_userlist_changed, "below userlist")
        extension.unsubscribe(self._on_below_menu_changed, "below menu")
        extension.unsubscribe(self._on_below_panel_changed, "below panel")

        if self.below_userlist:
            self.below_userlist = None

        if self.below_menu:
            self.below_menu = None

        if self.below_panel:
            self.below_panel = None

        self.session.config.unsubscribe(self._on_show_userpanel_changed,
            'b_show_userpanel')
