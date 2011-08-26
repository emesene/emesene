import gtk
import extension
from gui.gtkui.Preferences import BaseTable
from gui.gtkui.Dialog import ProgressWindow
from gui.gtkui.utils import GtkRunner

class ExtensionsListView(gtk.TreeView):

    def __init__(self, store):
        gtk.TreeView.__init__(self, store)
        self.crt = gtk.CellRendererToggle()
        self.append_column(gtk.TreeViewColumn(_('Status'), self.crt, active = 0))
        self.append_column(gtk.TreeViewColumn(_('Name'), gtk.CellRendererText(), text=1))
        self.set_rules_hint(True)


class ExtensionsListStore(gtk.ListStore):

    def __init__(self):
        gtk.ListStore.__init__(self, bool, str, str)


class ExtensionMainVBox(gtk.VBox):

    def __init__(self, session):
        gtk.VBox.__init__(self)

        self.set_border_width(2)

        self.session = session
        self.session.config.get_or_set('l_active_plugins', [])

        self.ext_list_store = ExtensionsListStore()
        self.ext_list_view = ExtensionsListView(self.ext_list_store)
        self.ext_list_view.crt.connect('toggled', self._cell_toggled, self.ext_list_store)

        scroll = gtk.ScrolledWindow()
        scroll.add(self.ext_list_view)
        scroll.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        scroll.set_shadow_type(gtk.SHADOW_IN)
        scroll.set_border_width(1)

        button_hbox = gtk.HButtonBox()
        button_hbox.set_layout(gtk.BUTTONBOX_END)
        button_hbox.set_border_width(2)

        self.pack_start(scroll)
        self.pack_start(button_hbox, False)
        self.on_cursor_changed(self.ext_list_view)


    def set_element_to_fetch(self, element):
        self.__element = element


    def _cell_toggled(self, widget, path, model):
        model[path][0] = not model[path][0]
        self.__element[model[path][2]].todownload = model[path][0]


    def append_element(self, label):
        self.ext_list_store.append((self.__element[label].todownload, label, label))


    def clearAll(self):
        self.ext_list_store.clear()


    def on_cursor_changed(self, ext_list_view):
        model, iter = ext_list_view.get_selection().get_selected()
        if iter is not None:
          value = model.get_value(iter,0)
          if value:
              self.button_stop.show()
              self.button_refresh.hide()
          else:
              self.button_stop.hide()
              self.button_refresh.show()


class DownloadExtension(BaseTable):
    """the panel to download extensions
    """

    def __init__(self, session, community_name, supported_name, n_boxes, collection_class):
        """constructor
        """
        BaseTable.__init__(self, 4, 1)
        self.first = False
        self.n_boxes = n_boxes
        self.set_border_width(5)
        self.session = session
        self.main_vboxes = range(self.n_boxes)

        for i in range(self.n_boxes):
            self.main_vboxes[i] = ExtensionMainVBox(session)

        self.thc_com = {}
        self.thc_cur_name = 'Supported'

        self.thc_com['Community'] = collection_class(community_name)
        self.thc_com['Supported'] = collection_class(supported_name)

        self.exts_hbox = gtk.VBox()

        for i in range(self.n_boxes):
            self.exts_hbox.pack_start(self.main_vboxes[i])

        button_hbox = gtk.HButtonBox()
        button_hbox.set_layout(gtk.BUTTONBOX_END)
        button_hbox.set_border_width(2)

        self.button_download = gtk.Button("Download")
        self.button_download.connect('clicked', self.start_download)

        self.button_refresh = gtk.Button("Refresh")
        self.button_refresh.connect('clicked', self.start_update)

        self.cmb_source = gtk.ComboBox()
        cmb_model_sources = gtk.ListStore(str)

        iter=cmb_model_sources.append()
        cmb_model_sources.set_value(iter, 0, "Supported")
        iter=cmb_model_sources.append()
        cmb_model_sources.set_value(iter, 0, "Community")
        
        self.cmb_source.set_model(cmb_model_sources)
        cell = gtk.CellRendererText()

        self.cmb_source.pack_start(cell, True)
        self.cmb_source.add_attribute(cell, 'text',0)
        self.cmb_source.set_active(0)

        self.cmb_source.connect('changed', self.on_change_theme_source)
        button_hbox.pack_start(self.cmb_source, fill = False)
        button_hbox.pack_start(self.button_download, fill = False)
        button_hbox.pack_start(self.button_refresh, fill = False)

        self.exts_hbox.pack_start(button_hbox)

        self.add(self.exts_hbox)
        self.show_all()


    def on_change_theme_source(self, combobox):
        self.thc_cur_name = combobox.get_active_text()
        self.show_update()


    def on_update(self):
        if not self.first:
            self.start_update()
            self.first = True


    def start_update(self, widget = None):
        self.progress = ProgressWindow(_('Refresh extensions'), self._end_progress_cb)
        self.progress.set_action(_("Refreshing extensions"))
        self.progress.show_all()
        GtkRunner(self.show_update, self.update)


    def start_download(self, widget = None):
        print "FILES TO DOWNLOAD"
        thc_cur = self.thc_com[self.thc_cur_name]
        for key in thc_cur.extensions_descs:
            element = thc_cur.extensions_descs[key]
            for label in element:
                if element[label].todownload:
                    print element[label].files


    def update(self):
        for k in self.thc_com:
            self.thc_com[k].fetch()


    def show_update(self, result = True):

        self.progress.update(100.0)
        self.progress.destroy()

        for i in range(self.n_boxes):
            self.main_vboxes[i].clearAll()

        thc_cur = self.thc_com[self.thc_cur_name]

        n_box = 0

        for key in thc_cur.extensions_descs:
            element = thc_cur.extensions_descs[key]
            self.main_vboxes[n_box].set_element_to_fetch(element)

            for label in element:
                self.main_vboxes[n_box].append_element(label)

            n_box += 1


    def _end_progress_cb(self, event, response = None):
        '''close refresh'''
        pass

