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

import e3

from pluginmanager import get_pluginmanager
from ExtensionList import ExtensionDownloadList

class PluginMainVBox(ExtensionDownloadList):
    def __init__(self, session, init_path):
        ExtensionDownloadList.__init__(
            self, session, 'plugins', init_path)

        self.config_dir = e3.common.ConfigDir('emesene2')

        self.config_button = gtk.Button(stock=gtk.STOCK_PREFERENCES)
        self.config_button.connect('clicked', self.on_config)
        self.no_button.set_property('no-show-all', True)

        self.buttonbox.pack_start(self.config_button, fill=False)
        self.on_cursor_changed(self.list_view)

    def show_update(self):
        '''called when the liststore need to be changed'''
        self.removable_list = {}
        self.removable_list['plugin'] = {}

        self.clear_all()
        self.append(False, _('Installed'), 'installed', True, False)

        pluginmanager = get_pluginmanager()

        for name, plugin in pluginmanager.get_plugins():
            is_active = pluginmanager.plugin_is_active(name)
            path = plugin.path
            if path.startswith(self.config_dir.base_dir) and not is_active:
                self.removable_list['plugin'][name] = path
            self.append(is_active, name, name, path=path,
                        description=pluginmanager.plugin_description(name))
        ExtensionDownloadList.show_update(self)

    def on_toggled(self, widget, path, model, type_):
        '''called when the toggle button in list view is pressed'''
        pluginmanager = get_pluginmanager()
        name = model[path][2]
        if not model[path][0]:
            self.on_start(name)
            self.removable_list[type_].pop(name, None)
        else:
            self.on_stop(name)
            if model[path][5].startswith(self.config_dir.base_dir):
                self.removable_list[type_][name] = model[path][5]
        model[path][0] = pluginmanager.plugin_is_active(name)

    def on_cursor_changed(self, list_view, type_='plugin'):
        '''called when a row is selected'''
        name = self.get_selected_name(self.list_view)
        pluginmanager = get_pluginmanager()
        self.config_button.set_sensitive(pluginmanager.plugin_configurable(name))

        ExtensionDownloadList.on_cursor_changed(self,
                                                list_view,
                                                type_,
                                                self.config_button)

    def on_start(self, name):
        '''start the selected plugin'''
        pluginmanager = get_pluginmanager()

        pluginmanager.plugin_start(name, self.session)
        if name not in self.session.config.l_active_plugins:
            self.session.config.l_active_plugins.append(name)

        self.on_cursor_changed(self.list_view)

    def on_stop(self, name):
        '''stop the selected plugin'''
        pluginmanager = get_pluginmanager()

        pluginmanager.plugin_stop(name)

        if name in self.session.config.l_active_plugins:
            self.session.config.l_active_plugins.remove(name)

        self.on_cursor_changed(self.list_view)

    def on_config(self, *args):
        '''Called when user hits the Preferences button'''
        pluginmanager = get_pluginmanager()
        name = self.get_selected_name(self.list_view)

        if name and pluginmanager.plugin_is_active(name):
                pluginmanager.plugin_config(name, self.session)

class PluginWindow(gtk.Window):
    def __init__(self, session):
        gtk.Window.__init__(self, gtk.WINDOW_TOPLEVEL)
        self.set_default_size(500, 300)
        self.set_title(_('Plugins'))
        self.set_position(gtk.WIN_POS_CENTER_ALWAYS)

        self.session = session
        config_dir = e3.common.ConfigDir('emesene2')

        self.main_vbox = PluginMainVBox(session, config_dir.join('plugins'))

        self.add(self.main_vbox)
        self.show_all()
