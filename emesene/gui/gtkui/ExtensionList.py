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

import os
import gtk

import utils
import extension
import e3

class ExtensionListView(gtk.TreeView):
    def __init__(self, store, radio=False):
        gtk.TreeView.__init__(self, store)
        self.toggle_renderer = gtk.CellRendererToggle()
        self.toggle_renderer.set_radio(radio)
        self.append_column(gtk.TreeViewColumn(_('Status'), self.toggle_renderer, active=0, activatable=3, visible=4))
        self.append_column(gtk.TreeViewColumn(_('Name'), gtk.CellRendererText(), markup=1))
        self.set_rules_hint(True)

class ExtensionListStore(gtk.ListStore):
    def __init__(self):
        # running, pretty name and description, name
        gtk.ListStore.__init__(self, bool, str, str, bool, bool)

class ExtensionList(gtk.VBox):
    def __init__(self, session, on_toggled, on_cursor_changed, radio, type_):
        gtk.VBox.__init__(self)

        self.set_border_width(2)

        self.session = session
        self.session.config.get_or_set('l_active_plugins', [])

        self.list_store = ExtensionListStore()
        self.list_view = ExtensionListView(self.list_store, radio)
        self.list_view.toggle_renderer.connect("toggled", on_toggled, self.list_store, type_)
        self.list_view.connect("cursor_changed", on_cursor_changed, type_)
        self.extension_list = []
        self.extension_type = type_

        scroll = gtk.ScrolledWindow()
        scroll.add(self.list_view)
        scroll.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        scroll.set_shadow_type(gtk.SHADOW_IN)
        scroll.set_border_width(1)

        self.pack_start(scroll)

    def clear_all(self):
        '''clear the liststore'''
        self.list_store.clear()
        self.extension_list = []

    def append(self, is_active, label, name, sensitive=True, visible=True):
        '''append an item'''
        if not sensitive:
            label = '<span foreground="#696969">%s</span>' % label
        if name not in self.extension_list:
            self.list_store.append((is_active, label, name, sensitive, visible))
            self.extension_list.append(name)

class ExtensionListTab(gtk.VBox):
    def __init__(self, session, radio=False, use_tabs=False):
        gtk.VBox.__init__(self)

        self.session = session
        self.boxes = []
        self.extension_types = []
        if use_tabs:
            self.lists = gtk.Notebook()
        else:
            self.lists = gtk.HBox()
            self.append_list('plugin', radio)

            self.list_store = self.boxes[0].list_store
            self.list_view = self.boxes[0].list_view
            self.extension_list = self.boxes[0].extension_list
            self.append = self.boxes[0].append
            self.clear_all = self.boxes[0].clear_all

        self.buttonbox = gtk.HButtonBox()
        self.buttonbox.set_layout(gtk.BUTTONBOX_EDGE)
        self.buttonbox.set_border_width(2)

        self.pack_start(self.lists)
        self.pack_start(self.buttonbox, False)

    def _make_list(self, type_, radio):
        '''make a new extension list'''
        extension_list = ExtensionList(
            self.session, self.on_toggled, self.on_cursor_changed, radio, type_)
        self.boxes.append(extension_list)
        self.extension_types.append(type_)
        return extension_list

    def append_list(self, type_, radio=False):
        '''append an ExtensionList vbox'''
        extension_list = self._make_list(type_, radio)
        self.lists.pack_start(extension_list)

    def append_tab(self, name, type_, radio=False):
        '''append an ExtensionList tab'''
        extension_list = self._make_list(type_, radio)
        label = gtk.Label(name)
        self.lists.append_page(extension_list, label)
        return extension_list

    def on_toggled(self, *args):
        '''called when a checkbox is toggled'''
        pass

    def on_cursor_changed(self, *args):
        '''called when a row is selected'''
        pass

    def prettify_name(self, name, type_, description=''):
        '''return a prettier name for the plugin with its description in a new
        line, using Pango markup.
        '''
        name = name.replace('_', ' ')
        pretty_name = '<span><b>%s</b>\n<small>%s</small></span>'
        return pretty_name % (name[0].upper() + name[1:], description)

class ExtensionDownloadList(ExtensionListTab):
    def __init__(self, session, list_type,
                 collection_class, init_path, radio=False, use_tabs=False):
        '''constructor'''
        ExtensionListTab.__init__(self, session, radio, use_tabs)
        self.first = True

        self.thc_com = {}
        self.thc_cur_name = 'Supported'

        self.list_type = list_type

        self.thc_com['Community'] = collection_class('emesene-community-'+self.list_type, init_path)
        self.thc_com['Supported'] = collection_class('emesene-supported-'+self.list_type, init_path)

        self.download_list = {}

        refresh_button = gtk.Button(stock=gtk.STOCK_REFRESH)
        refresh_button.connect('clicked', self.on_update, True)

        self.download_button = gtk.Button(_('Download'))
        self.download_button.set_image(gtk.image_new_from_stock(
                                       gtk.STOCK_GO_DOWN, gtk.ICON_SIZE_MENU))
        self.download_button.connect('clicked', self.start_download)
        self.download_button.set_property('no-show-all', True)

        self.no_button = gtk.HBox()

        source_combo = gtk.ComboBox()
        cmb_model_sources = gtk.ListStore(str)

        iter_ = cmb_model_sources.append()
        cmb_model_sources.set_value(iter_, 0, "Supported")
        iter_ = cmb_model_sources.append()
        cmb_model_sources.set_value(iter_, 0, "Community")

        source_combo.set_model(cmb_model_sources)
        cell = gtk.CellRendererText()

        source_combo.pack_start(cell, True)
        source_combo.add_attribute(cell, 'text', 0)
        source_combo.set_active(0)
        hbox = gtk.HBox()

        source_combo.connect('changed', self.on_change_source)
        self.buttonbox.pack_start(source_combo, fill=False)
        self.buttonbox.pack_start(refresh_button, fill=False)
        self.buttonbox.pack_start(hbox)
        self.buttonbox.pack_start(self.download_button, fill=False)
        self.buttonbox.pack_start(self.no_button)

    def on_cursor_changed(self, list_view, type_):
        '''called when a row is selected'''
        model, iter_ = list_view.get_selection().get_selected()
        if iter_ is not None:
            value = model.get_value(iter_, 2)
            if value in self.download_list[type_]:
                self.download_item = value
                self.download_button.show()
                self.no_button.hide()
            else:
                self.download_button.hide()
                self.no_button.show()

    def on_change_source(self, combobox):
        '''called when the source is changed'''
        self.thc_cur_name = combobox.get_active_text()
        self.on_update(clear=True)

    def on_update(self, widget=None, download=False, clear=False):
        '''called when the liststore need to be changed'''
        if self.first or download:
            dialog = extension.get_default('dialog')
            self.progress = dialog.progress_window(
                            _('Refresh extensions'), self._end_progress_cb)
            self.progress.set_action(_("Refreshing extensions"))
            self.progress.show_all()
            utils.GtkRunner(self.show_update, self.update)

            self.first = False
        elif clear:
            self.show_update()

    def start_download(self, widget=None):
        '''start the download of an extension'''
        thc_cur = self.thc_com[self.thc_cur_name]
        thc_cur.download(self.download_item)
        self.on_update(clear=True)

    def update(self):
        '''update the collections'''
        for k in self.thc_com:
            self.thc_com[k].fetch()

    def show_update(self, result=True):
        '''show an update list of the set collection'''
        self.progress.update(100.0)
        self.progress.destroy()
        self.download_list = {}

        thc_cur = self.thc_com[self.thc_cur_name]

        for box in self.boxes:
            self.download_list[box.extension_type] = []
            element = thc_cur.extensions_descs.get(box.extension_type, {})
            box.append(False, '<b>Available for download</b>', 'installable', visible=False)
            for label in element:
                if label not in box.extension_list:
                    self.download_list[box.extension_type].append(label)
                box.append(False, self.prettify_name(label, box.extension_type), label, False)

    def _end_progress_cb(self, event, response=None):
        '''close refresh'''
        pass

class ThemeList(ExtensionDownloadList):
    def __init__(self, session):
        config_dir = e3.common.ConfigDir('emesene2')
        ExtensionDownloadList.__init__(
            self, session, 'themes', e3.common.Collections.ThemesCollection,
            config_dir.join('themes'), True, True)

        self.themes = {}
        self.theme_configs = {}
        self.callbacks = {}

    def on_toggled(self, widget, path, model, type_):
        '''called when the toggle button in list view is pressed'''
        for row in model:
            row[0] = False
        model[path][0] = True
        self.callbacks[type_](self.theme_configs[type_], model[path][2])

    def get_attr(self, name):
        """return the value of an attribute, if it has dots, then
        get the values until the last
        """

        obj = self
        for attr in name.split('.'):
            obj = getattr(obj, attr)

        return obj

    def set_attr(self, name, value):
        """set the value of an attribute, if it has dots, then
        get the values until the last
        """

        obj = self
        terms = name.split('.')

        for attr in terms[:-1]:
            obj = getattr(obj, attr)

        setattr(obj, terms[-1], value)
        return obj

    def set_theme(self, property_name, value):
        self.set_attr(property_name, value)

    def on_update(self, widget=None, download=False, clear=False):
        if not (self.first or download or clear):
            return
        for box in self.boxes:
            box.clear_all()
            box.append(False, '<b>Installed</b>', 'installed', visible=False)
            current = self.get_attr(self.theme_configs[box.extension_type])
            for path in self.themes[box.extension_type].list():
                label = self.themes[box.extension_type].get_name_from_path(path)
                name = os.path.basename(path)
                box.append(name == current or label == current, label, name)
            ExtensionDownloadList.on_update(self, widget, download, clear)

    def prettify_name(self, name, type_):
        '''return a prettier name using Pango markup.
        '''
        name = name.replace('_', ' ')
        name = self.themes[type_].pattern.sub('', name)
        return '%s' % name

    def append_theme_tab(self, name, theme_type, theme, theme_config, callback=None):
        self.themes[theme_type] = theme
        self.theme_configs[theme_type] = theme_config
        if callback:
            self.callbacks[theme_type] = callback
        else:
            self.callbacks[theme_type] = self.set_theme
        box = self.append_tab(name, theme_type, True)
        return box
