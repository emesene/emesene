import traceback

import gtk

import extension
from pluginmanager import get_pluginmanager

from debugger import warning

class PluginListView(gtk.TreeView):
    def __init__(self, store):
        gtk.TreeView.__init__(self, store)
        self.append_column(gtk.TreeViewColumn('Status', gtk.CellRendererToggle(), active=0))
        self.append_column(gtk.TreeViewColumn('Name', gtk.CellRendererText(), text=1))
        self.append_column(gtk.TreeViewColumn('Description', gtk.CellRendererText(), text=2))

class PluginListStore(gtk.ListStore):
    def __init__(self):
        gtk.ListStore.__init__(self, bool, str, str)

    def update_list(self):
        pluginmanager = get_pluginmanager()
        self.clear()
        for name in pluginmanager.get_plugins():
            self.append((pluginmanager.plugin_is_active(name), name, pluginmanager.get_info(name)['description']))

class PluginWindow(gtk.Window):
    def __init__(self):
        gtk.Window.__init__(self, gtk.WINDOW_TOPLEVEL)
        self.set_default_size(300, 200)
 
        main_vbox = gtk.VBox()
        main_vbox.set_border_width(2)
        self.plugin_list_store = PluginListStore()
        self.plugin_list_store.update_list()
        self.plugin_list_view = PluginListView(self.plugin_list_store)
        main_vbox.pack_start(self.plugin_list_view)
        button_hbox = gtk.HBox()
        button_hbox.set_border_width(2)
        button_start = gtk.Button(stock=gtk.STOCK_EXECUTE)
        button_start.connect('clicked', self.on_start)
        button_stop = gtk.Button(stock=gtk.STOCK_STOP)
        button_stop.connect('clicked', self.on_stop)
        button_hbox.pack_start(button_start, fill=False)
        button_hbox.pack_start(button_stop, fill=False)
        main_vbox.pack_start(button_hbox, False)
 
        self.add(main_vbox)
        self.show_all()

    def on_start(self, *args):
        '''start the selected plugin'''
        sel = self.plugin_list_view.get_selection()
        model, iter = sel.get_selected()
        name = model.get_value(iter, 1)
        pluginmanager = get_pluginmanager()
        pluginmanager.plugin_start(name)
        print pluginmanager.plugin_is_active(name), 'after start'
        model.set_value(iter, 0, bool(pluginmanager.plugin_is_active(name)))
 
    def on_stop(self, *args):
        '''stop the selected plugin'''
        sel = self.plugin_list_view.get_selection()
        model, iter = sel.get_selected()
        name = model.get_value(iter, 1)
        pluginmanager = get_pluginmanager()
        pluginmanager.plugin_stop(name)
        print pluginmanager.plugin_is_active(name), 'after stop'
        model.set_value(iter, 0, pluginmanager.plugin_is_active(name))

