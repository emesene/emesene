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

import gtk

import gui
import utils
import e3

from pluginmanager import get_pluginmanager
from ExtensionList import ExtensionDownloadList

class PluginMainVBox(ExtensionDownloadList):
    def __init__(self, session, init_path):
        ExtensionDownloadList.__init__(
            self, session, 'emesene-community-plugins',
            'emesene-supported-plugins', 1,
            e3.common.Collections.PluginsCollection, init_path)

        self.config_button = gtk.Button(stock=gtk.STOCK_PREFERENCES)
        self.config_button.connect('clicked', self.on_config)

        self.buttonbox.pack_start(self.config_button, fill=False)
        self.on_cursor_changed(self.list_view)

    def on_update(self, widget=None, download=False, clear=False):
        if self.first or download or clear:
            self.clear_all()
            self.append(False, '<b>Installed</b>', 'installed', True, False)
            pluginmanager = get_pluginmanager()

            for name in pluginmanager.get_plugins():
                self.append(pluginmanager.plugin_is_active(name),
                    self.list_store.prettify_name(name, pluginmanager.plugin_description(name)),
                    name)
            ExtensionDownloadList.on_update(self, widget, download, clear)

    def on_toggled(self, widget, path, model):
        '''called when the toggle button in list view is pressed'''
        sel = self.list_view.get_selection()
        sel.select_path(path)
        if not widget.get_active():
            self.on_start()
        else:
            self.on_stop()

    def on_cursor_changed(self, list_view):
        '''called when a row is selected'''
        model, iter_ = list_view.get_selection().get_selected()
        if iter_ is not None:
            value = model.get_value(iter_, 2)
            if value in self.download_list:
                self.download_item = value
                self.config_button.hide()
                self.download_button.show()
            else:
                self.download_button.hide()
                self.config_button.show()

    def on_start(self, *args):
        '''start the selected plugin'''
        sel = self.list_view.get_selection()
        model, iter = sel.get_selected()
        if iter is not None:
            name = model.get_value(iter, 2)
            pluginmanager = get_pluginmanager()
            pluginmanager.plugin_start(name, self.session)

            if name not in self.session.config.l_active_plugins:
                self.session.config.l_active_plugins.append(name)

            model.set_value(iter, 0, bool(pluginmanager.plugin_is_active(name)))
        self.on_cursor_changed(self.list_view)

    def on_stop(self, *args):
        '''stop the selected plugin'''
        sel = self.list_view.get_selection()
        model, iter = sel.get_selected()
        if iter is not None:
            name = model.get_value(iter, 2)
            pluginmanager = get_pluginmanager()
            pluginmanager.plugin_stop(name)

            if name in self.session.config.l_active_plugins:
                self.session.config.l_active_plugins.remove(name)

            model.set_value(iter, 0, pluginmanager.plugin_is_active(name))
        self.on_cursor_changed(self.list_view)

    def on_config(self, *args):
        '''stop the selected plugin'''
        sel = self.list_view.get_selection()
        model, iter = sel.get_selected()
        if iter is not None:
            name = model.get_value(iter, 2)
            pluginmanager = get_pluginmanager()

            if pluginmanager.plugin_is_active(name):
                pluginmanager.plugin_config(name, self.session)

class PluginWindow(gtk.Window):
    def __init__(self, session):
        gtk.Window.__init__(self, gtk.WINDOW_TOPLEVEL)
        self.set_default_size(500, 300)
        self.set_title(_('Plugins'))
        self.set_position(gtk.WIN_POS_CENTER_ALWAYS)

        self.session = session

        self.main_vbox = PluginMainVBox(session, os.path.join(os.getcwd(), "plugins"))

        self.add(self.main_vbox)
        self.show_all()
