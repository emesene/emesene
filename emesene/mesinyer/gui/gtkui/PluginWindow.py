import gtk

import gui
import utils

from pluginmanager import get_pluginmanager

class PluginListView(gtk.TreeView):
    def __init__(self, store):
        gtk.TreeView.__init__(self, store)
        self.append_column(gtk.TreeViewColumn('Status', gtk.CellRendererToggle(), active=0))
        self.append_column(gtk.TreeViewColumn('Name', gtk.CellRendererText(), text=1))
        self.set_rules_hint(True)

class PluginListStore(gtk.ListStore):
    def __init__(self):
        gtk.ListStore.__init__(self, bool, str, str)

    def update_list(self):
        pluginmanager = get_pluginmanager()
        self.clear()

        for name in pluginmanager.get_plugins():
            self.append((pluginmanager.plugin_is_active(name),
                self.prettify_name(name), name))

    def prettify_name(self, name):
        '''return a prettier name for the plugin'''
        name = name.replace('_', ' ')
        return name[0].upper() + name[1:]

class PluginMainVBox(gtk.VBox):
    def __init__(self, session):
        gtk.VBox.__init__(self)

        self.set_border_width(2)

        self.session = session

        self.plugin_list_store = PluginListStore()
        self.plugin_list_store.update_list()
        self.plugin_list_view = PluginListView(self.plugin_list_store)

        scroll = gtk.ScrolledWindow()
        scroll.add(self.plugin_list_view)
        scroll.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        scroll.set_shadow_type(gtk.SHADOW_IN)
        scroll.set_border_width(1)

        button_hbox = gtk.HButtonBox()
        button_hbox.set_layout(gtk.BUTTONBOX_END)
        button_hbox.set_border_width(2)

        button_start = gtk.Button(stock=gtk.STOCK_EXECUTE)
        button_start.connect('clicked', self.on_start)

        button_stop = gtk.Button(stock=gtk.STOCK_STOP)
        button_stop.connect('clicked', self.on_stop)

        button_config = gtk.Button(stock=gtk.STOCK_PREFERENCES)
        button_config.connect('clicked', self.on_config)

        self.pack_start(scroll)
        button_hbox.pack_start(button_config, fill=False)
        button_hbox.pack_start(button_start, fill=False)
        button_hbox.pack_start(button_stop, fill=False)
        self.pack_start(button_hbox, False)

    def on_start(self, *args):
        '''start the selected plugin'''
        sel = self.plugin_list_view.get_selection()
        model, iter = sel.get_selected()
        if iter != None:
            name = model.get_value(iter, 2)
            pluginmanager = get_pluginmanager()
            pluginmanager.plugin_start(name, self.session)
            print pluginmanager.plugin_is_active(name), 'after start'
            model.set_value(iter, 0, bool(pluginmanager.plugin_is_active(name)))

    def on_stop(self, *args):
        '''stop the selected plugin'''
        sel = self.plugin_list_view.get_selection()
        model, iter = sel.get_selected()
        if iter != None:
            name = model.get_value(iter, 2)
            pluginmanager = get_pluginmanager()
            pluginmanager.plugin_stop(name)
            print pluginmanager.plugin_is_active(name), 'after stop'
            model.set_value(iter, 0, pluginmanager.plugin_is_active(name))

    def on_config(self, *args):
        '''stop the selected plugin'''
        sel = self.plugin_list_view.get_selection()
        model, iter = sel.get_selected()
        if iter != None:
            name = model.get_value(iter, 2)
            pluginmanager = get_pluginmanager()

            if pluginmanager.plugin_is_active(name):
                pluginmanager.plugin_config(name, self.session)

    def on_update(self):
        pass

class PluginWindow(gtk.Window):
    def __init__(self, session):
        gtk.Window.__init__(self, gtk.WINDOW_TOPLEVEL)
        self.set_default_size(500, 300)
        self.set_title('Plugins')
        self.set_position(gtk.WIN_POS_CENTER_ALWAYS)

        self.session = session

        if utils.file_readable(gui.theme.logo):
            self.set_icon(
                utils.safe_gtk_image_load(gui.theme.logo).get_pixbuf())

        self.main_vbox = PluginMainVBox(session)

        self.add(self.main_vbox)
        self.show_all()


