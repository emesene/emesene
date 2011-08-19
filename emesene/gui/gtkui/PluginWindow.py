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

from pluginmanager import get_pluginmanager

class PluginListView(gtk.TreeView):
    def __init__(self, store, toggle_func=None):
        gtk.TreeView.__init__(self, store)
        self.toggle_renderer = gtk.CellRendererToggle()
        self.append_column(gtk.TreeViewColumn(_('Status'), self.toggle_renderer, active=0))
        self.append_column(gtk.TreeViewColumn(_('Name'), gtk.CellRendererText(), markup=1))
        self.set_rules_hint(True)
        if toggle_func:
            self.toggle_renderer.connect("toggled", toggle_func)

class PluginListStore(gtk.ListStore):
    def __init__(self):
        # running, pretty name and description, name
        gtk.ListStore.__init__(self, bool, str, str)

    def update_list(self):
        pluginmanager = get_pluginmanager()
        self.clear()

        for name in pluginmanager.get_plugins():
            self.append((pluginmanager.plugin_is_active(name),
                self.prettify_name(name, pluginmanager.plugin_description(name)),
                name))

    def prettify_name(self, name, description):
        '''return a prettier name for the plugin with its description in a new
        line, using Pango markup.
        '''
        name = name.replace('_', ' ')
        pretty_name = '<span><b>%s</b>\n<small>%s</small></span>'
        return pretty_name % (name[0].upper() + name[1:], description)

class PluginMainVBox(gtk.VBox):
    def __init__(self, session):
        gtk.VBox.__init__(self)

        self.set_border_width(2)

        self.session = session
        self.session.config.get_or_set('l_active_plugins', [])

        self.plugin_list_store = PluginListStore()
        self.plugin_list_store.update_list()
        self.plugin_list_view = PluginListView(self.plugin_list_store, self.toggle_func)
        self.plugin_list_view.connect("cursor_changed", self.on_cursor_changed)

        scroll = gtk.ScrolledWindow()
        scroll.add(self.plugin_list_view)
        scroll.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        scroll.set_shadow_type(gtk.SHADOW_IN)
        scroll.set_border_width(1)

        button_hbox = gtk.HButtonBox()
        button_hbox.set_layout(gtk.BUTTONBOX_END)
        button_hbox.set_border_width(2)

        self.button_start = gtk.Button(stock=gtk.STOCK_EXECUTE)
        self.button_start.connect('clicked', self.on_start)

        self.button_stop = gtk.Button(stock=gtk.STOCK_STOP)
        self.button_stop.connect('clicked', self.on_stop)
        self.button_stop.hide()

        button_config = gtk.Button(stock=gtk.STOCK_PREFERENCES)
        button_config.connect('clicked', self.on_config)

        self.pack_start(scroll)
        button_hbox.pack_start(button_config, fill=False)
        button_hbox.pack_start(self.button_start, fill=False)
        button_hbox.pack_start(self.button_stop, fill=False)
        self.pack_start(button_hbox, False)
        self.on_cursor_changed(self.plugin_list_view)

    def toggle_func(self, toggle, path):
        '''called when the toggle button in list view is pressed'''
        sel = self.plugin_list_view.get_selection()
        sel.select_path(path)
        if not toggle.get_active():
            self.on_start()
        else:
            self.on_stop()

    def on_start(self, *args):
        '''start the selected plugin'''
        sel = self.plugin_list_view.get_selection()
        model, iter = sel.get_selected()
        if iter is not None:
            name = model.get_value(iter, 2)
            pluginmanager = get_pluginmanager()
            pluginmanager.plugin_start(name, self.session)

            if name not in self.session.config.l_active_plugins:
                self.session.config.l_active_plugins.append(name)

            model.set_value(iter, 0, bool(pluginmanager.plugin_is_active(name)))
        self.on_cursor_changed(self.plugin_list_view)

    def on_stop(self, *args):
        '''stop the selected plugin'''
        sel = self.plugin_list_view.get_selection()
        model, iter = sel.get_selected()
        if iter is not None:
            name = model.get_value(iter, 2)
            pluginmanager = get_pluginmanager()
            pluginmanager.plugin_stop(name)

            if name in self.session.config.l_active_plugins:
                self.session.config.l_active_plugins.remove(name)

            model.set_value(iter, 0, pluginmanager.plugin_is_active(name))
        self.on_cursor_changed(self.plugin_list_view)

    def on_config(self, *args):
        '''stop the selected plugin'''
        sel = self.plugin_list_view.get_selection()
        model, iter = sel.get_selected()
        if iter is not None:
            name = model.get_value(iter, 2)
            pluginmanager = get_pluginmanager()

            if pluginmanager.plugin_is_active(name):
                pluginmanager.plugin_config(name, self.session)

    def on_update(self):
        pass

    def on_cursor_changed(self, plugin_list_view):
        model, iter = plugin_list_view.get_selection().get_selected()
        if iter is not None:
          value = model.get_value(iter,0)
          if value:
              self.button_stop.show()
              self.button_start.hide()
          else:
              self.button_stop.hide()
              self.button_start.show()

class PluginWindow(gtk.Window):
    def __init__(self, session):
        gtk.Window.__init__(self, gtk.WINDOW_TOPLEVEL)
        self.set_default_size(500, 300)
        self.set_title(_('Plugins'))
        self.set_position(gtk.WIN_POS_CENTER_ALWAYS)

        self.session = session

        self.main_vbox = PluginMainVBox(session)

        self.add(self.main_vbox)
        self.show_all()
