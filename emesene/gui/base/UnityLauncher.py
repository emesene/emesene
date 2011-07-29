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

from gi.repository import Unity, Dbusmenu
from BaseTray import BaseTray

class UnityLauncher(BaseTray):
    ''' A widget that implements fancy unity launcher actions '''
    NAME = 'Unity Launcher'
    DESCRIPTION = 'Unity message count and quicklist'
    AUTHOR = 'Sven (Sbte)'
    WEBSITE = 'www.emesene.org'

    def __init__ (self, close_session):
        '''constructor'''
        BaseTray.__init__(self)
        self.count = 0
        self.session = None
        self.close_session = close_session

        self.launcher = Unity.LauncherEntry.get_for_desktop_id('emesene.desktop')
        self.launcher.set_property("count", self.count)

        # Also add a quicklist
        ql = Dbusmenu.Menuitem.new()
        ql_quit = Dbusmenu.Menuitem.new()
        ql_quit.property_set(Dbusmenu.MENUITEM_PROP_LABEL, _('Quit'))
        ql_quit.connect('item-activated', self._close_session)
        ql.child_append(ql_quit)
        self.launcher.set_property("quicklist", ql)
        self.icid_dict = {}

    def set_session(self, session):
        ''' Method called upon login '''
        self.session = session
        self.session.signals.conv_message.subscribe(
            self._on_message)
        self.session.signals.conv_ended.subscribe(
            self._on_conv_ended)
        self.session.signals.message_read.subscribe(
            self._on_message_read)

    def remove_session(self):
        if self.session is not None:
            self.session.signals.conv_message.unsubscribe(
                self._on_message)
            self.session.signals.conv_ended.unsubscribe(
                self._on_conv_ended)
            self.session.signals.message_read.unsubscribe(
                self._on_message_read)
            self.session = None

    def _on_message(self, cid, account, msgobj, cedict=None):
        ''' This is fired when a new message arrives '''
        conv = self._get_conversation(cid, account)
        if conv:
            icid = conv.icid
            if icid in self.icid_dict.keys():
                self.icid_dict[icid] += 1
            else:
                conv_manager = self._get_conversation_manager(cid, account)
                if not conv_manager:
                    return
                if conv_manager.is_active():
                    return
                self.icid_dict[icid] = 1
            self.count += 1
            self.launcher.set_property("count", self.count)
            self.launcher.set_property("count_visible", True)
            self.launcher.set_property("urgent", True)

    def _on_message_read(self, conv):
        ''' This is called when the user read the message '''
        if conv:
            self._hide_count(conv.icid)

    def _on_conv_ended(self, cid):
        ''' This is called when the conversation is closed '''
        conv = self._get_conversation(cid)
        if conv:
            self._hide_count(conv.icid)

    def _hide_count(self, icid):
        ''' Hide the message count if nessecary '''
        if icid in self.icid_dict.keys():
            self.count -= self.icid_dict[icid]
            del self.icid_dict[icid]
        self.launcher.set_property("count", self.count)
        if self.icid_dict == {}:
            self.count = 0
        if self.count == 0:
            self.launcher.set_property("count_visible", False)
            self.launcher.set_property("urgent", False)

    def _close_session(self, menu_item, menu_object):
        self.close_session()

