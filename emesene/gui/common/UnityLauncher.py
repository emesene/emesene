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

import logging
log = logging.getLogger("gui.common.UnityLauncher")

import dbus, dbus.service
import gui

class UnityDBusController(dbus.service.Object):
    def __init__(self, app_uri):
        dbus.service.Object.__init__(self, dbus.SessionBus(), '/')
        self.properties = {}
        self.app_uri = app_uri
        self._update()
        self.set_property("count-visible", True)

    def set_property(self, property_, value):
        if property_ == "count":
            value = dbus.Int64(value)
        self.properties[property_] = value
        self._update()

    def _update(self):
        self.Update(self.app_uri, self.properties)

    @dbus.service.signal(dbus_interface='com.canonical.Unity.LauncherEntry',
                         signature=("sa{sv}"))
    def Update(self, app_uri, properties):
        pass

    @dbus.service.method(dbus_interface='com.canonical.Unity.LauncherEntry',
                         in_signature="sa{sv}", out_signature="")
    def Query(self, app_uri, properties):
        log.debug("DBus message. app_uri: %s, properties: %s" % (app_uri, properties))

class UnityLauncher(gui.BaseTray):
    ''' A widget that implements fancy unity launcher actions '''
    NAME = 'Unity Launcher'
    DESCRIPTION = 'Unity message count and quicklist'
    AUTHOR = 'Sven (Sbte)'
    WEBSITE = 'www.emesene.org'

    def __init__ (self):
        '''constructor'''
        gui.BaseTray.__init__(self)
        self.count = 0
        self.session = None
        self.launcher = UnityDBusController("application://emesene.desktop")

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
            self.launcher.set_property("count-visible", True)
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
            self.launcher.set_property("count-visible", False)
            self.launcher.set_property("urgent", False)

    def _close_session(self, menu_item, menu_object):
        self.session.close()

