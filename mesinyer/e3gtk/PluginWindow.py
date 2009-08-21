import gtk

import extension
from pluginmanager import get_pluginmanager

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
    DESCRIPTION_TPL = '{0[description]}\nAuthors:{1}'
    AUTHOR_TPL = '\n* <u>%s</u> %s'
    def __init__(self):
        gtk.Window.__init__(self, gtk.WINDOW_TOPLEVEL)

        main_vbox = gtk.VBox()
        self.plugin_list_store = PluginListStore()
        self.plugin_list_store.update_list()
        self.plugin_list_view = PluginListView(self.plugin_list_store)
        self.plugin_list_view.connect('cursor-changed', self.on_row_selected)
        main_vbox.pack_start(self.plugin_list_view)

        self.label_description = gtk.Label('') #this sits below
        self.frame_description = gtk.Frame('Description')
        self.frame_description.add(self.label_description)
        main_vbox.pack_start(self.frame_description)
        button_hbox = gtk.HBox()

        button_start = gtk.Button(stock=gtk.STOCK_EXECUTE)
        #it's clearly copy&pasted
        button_start.get_children()[0].get_children()[0].get_children()[1].set_label('Start')
        button_start.connect('clicked', self.on_start)

        button_stop = gtk.Button(stock=gtk.STOCK_STOP)
        #it's clearly copy&pasted
        button_stop.get_children()[0].get_children()[0].get_children()[1].set_label('Stop')
        button_stop.connect('clicked', self.on_stop)

        button_hbox.pack_start(button_start, fill=False)
        button_hbox.pack_start(button_stop, fill=False)

        main_vbox.pack_start(button_hbox, False)

        self.add(main_vbox)
        self.show_all()

    def on_start(self, *args):
        '''start the selected plugin'''
        sel = self.plugin_list_view.get_selection()
        (model, iter) = sel.get_selected()
        name = model.get_value(iter, 1)
        pluginmanager = get_pluginmanager()
        pluginmanager.plugin_start(name)
        model.set_value(iter,0,bool(pluginmanager.plugin_is_active(name)))
        extension.get_default('dialog').error('Error when starting plugin %s' % name)

    def on_stop(self, *args):
        '''stop the selected plugin'''
        sel = self.plugin_list_view.get_selection()
        (model, iter) = sel.get_selected()
        name = model.get_value(iter, 1)
        pluginmanager = get_pluginmanager()
        pluginmanager.plugin_stop(name)
        model.set_value(iter,0,pluginmanager.plugin_is_active(name))
        extension.get_default('dialog').error('Error when stopping plugin %s' % name)
    
    def on_row_selected(self, view):
        '''when user clicks on a different row. change description below'''
        sel = self.plugin_list_view.get_selection()
        (model, iter) = sel.get_selected()
        name = model.get_value(iter, 1)
        authors = ''
        for (aut,email) in get_pluginmanager().get_info(name)['authors'].items():
            email = email.replace(' ', '@', 1)
            email = email.replace(' ', '.', 1)
            authors+= self.AUTHOR_TPL % (aut,email)
        description = self.DESCRIPTION_TPL.format(get_pluginmanager().get_info(name), authors)
        self.label_description.set_markup(description)


if __name__ == '__main__':
    get_pluginmanager().scan_directory('plugins')
    window = PluginWindow()
    gtk.main()
