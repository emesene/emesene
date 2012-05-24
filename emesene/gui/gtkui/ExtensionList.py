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
import re

import logging
log = logging.getLogger('gtkui.ExtensionList')

import utils
import extension
import e3
import gobject
import gui
import Info

from gui.gtkui import check_gtk3

if check_gtk3():
    import TinyButtonNew as TinyButton
else:
    import TinyButton

from pluginmanager import get_pluginmanager

class ExtensionListView(gtk.TreeView):
    def __init__(self, store, radio=False):
        gtk.TreeView.__init__(self, store)
        self.toggle_renderer = gtk.CellRendererToggle()
        self.toggle_renderer.set_radio(radio)
        self.append_column(gtk.TreeViewColumn(_('Status'),
                           self.toggle_renderer,
                           active=0,
                           activatable=3,
                           visible=4))

        self.append_column(gtk.TreeViewColumn(_('Name'),
                           gtk.CellRendererText(),
                           markup=1))
        self.set_rules_hint(True)

class ExtensionListStore(gtk.ListStore):
    def __init__(self):
        # running, pretty name and description, name
        gtk.ListStore.__init__(self, bool, str, str, bool, bool, str, str)

class ExtensionList(gtk.VBox):
    def __init__(self, session, on_toggled, on_cursor_changed, radio, type_):
        gtk.VBox.__init__(self)

        self.set_border_width(2)

        self.session = session
        self.session.config.get_or_set('l_active_plugins', [])

        self.list_store = ExtensionListStore()
        self.list_view = ExtensionListView(self.list_store, radio)
        self.list_view.toggle_renderer.connect("toggled",
                                               on_toggled,
                                               self.list_store,
                                               type_)

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

    def prettify_name(self, name, description):
        '''return a prettier name for the plugin with its description in a new
        line, using Pango markup.
        '''
        name = name.replace('_', ' ')
        if description:
            pretty_name = '<span><b>%s</b>\n<small>%s</small></span>' % \
                          (name.capitalize(), description)
        else:
            pretty_name = '<span><b>%s</b></span>' % name.capitalize()
        return pretty_name

    def append(self, is_active, label, name, sensitive=True, visible=True, path='', type_='', description=''):
        '''append an item'''
        pretty_name = self.prettify_name(label, description)
        if not sensitive:
            pretty_name = '<span foreground="#696969">%s</span>' % pretty_name
        if name not in self.extension_list:
            self.list_store.append((is_active, pretty_name, name, sensitive, visible, path, type_))
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

        #progressbar widgets
        self.progressbox = gtk.VBox()
        self.progressbox.set_border_width(2)
        box = gtk.HBox()
        box.set_border_width(2)
        self.progresslabel = gtk.Label()
        self.progressbar = gtk.ProgressBar()
        self.progress_cancel_button = TinyButton.TinyButton(gtk.STOCK_CANCEL)
        self.end_progress_handler = None

        box.pack_start(self.progresslabel, False, False, 0)
        box.pack_start(self.progressbar, False, False, 5)
        box.pack_start(self.progress_cancel_button, False, False, 0)

        separator = gtk.HSeparator()
        self.progressbox.pack_start(separator, False, False, 0)
        self.progressbox.pack_start(box, False, False, 2)

        self.pack_start(self.lists)
        self.pack_start(self.buttonbox, False)
        self.pack_start(self.progressbox, False)

    def set_action(self, action):
        '''called when the action changes'''
        self.progresslabel.set_text(action)
        self.progressbar.set_fraction(0)
        self.progressbar.set_text("0 %")

    def update_action(self, progress):
        '''called when the progress is updated'''
        self.progressbar.set_fraction(progress / 100.0)
        self.progressbar.set_text("%d %s" % (progress, "%"))

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

    def strip_name(self, name, *args):
        '''called to strip names when needed'''
        return name

    def on_toggled(self, *args):
        '''called when a checkbox is toggled'''
        pass

    def on_cursor_changed(self, *args):
        '''called when a row is selected'''
        pass

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

    def version_value(self, version):
        '''return an integer version value'''
        if isinstance(version, int):
            return version

        stripped_version = re.sub(r'[^\d.]+', '', version)
        split_version = stripped_version.split(".")
        split_version.reverse()
        value = 0
        for i, val in enumerate(split_version):
            value += (int(val) << (i * 8))

        return value


class DownloadListBase(ExtensionListTab):
    def __init__(self, session, radio=False, use_tabs=False):
        '''constructor'''
        ExtensionListTab.__init__(self, session, radio, use_tabs)
        self.updated_amount = 0
        self.default_action = _('Refresh extensions')
        self.progress = False


        self.config_dir = e3.common.ConfigDir('emesene2')

        self.list_types = ['plugins', 'themes']

        self.collections = \
        {
            'plugins':
            {
                'supported': extension.get_and_instantiate(
                                'supported plugins collection',
                                self.config_dir.join('plugins')),
                'community': extension.get_and_instantiate(
                                'community plugins collection',
                                self.config_dir.join('plugins'))
            },
            'themes':
            {
                'supported': extension.get_and_instantiate(
                                'supported themes collection',
                                self.config_dir.join('themes')),
                'community': extension.get_and_instantiate(
                                'community themes collection',
                                self.config_dir.join('themes'))
            }
        }

    def on_update(self, widget=None, refresh=False):
        '''called when the liststore need to be changed'''
        if self.progress:
            return

        self.progress = True
        self.set_action(self.default_action)
        self.progressbox.show_all()
        self.end_progress_handler = self.progress_cancel_button.connect('clicked', self._end_progress_cb)
        gobject.timeout_add_seconds(1, self.update_progress)
        utils.GtkRunner(self.show_update_callback, self.update, refresh)

    def update(self, refresh):
        '''update the collection data'''
        self.updated_amount = 0
        for list_type in self.list_types:
            for current_collection in self.collections[list_type].itervalues():
                current_collection.fetch(refresh)
                if self.progress is None:
                    return

                current_collection.fetch_all_metadata(refresh)
                if self.progress is None:
                    return

                self.updated_amount += 1

    def update_progress(self):
        if not self.progress:
            return False

        progress = self.updated_amount / (len(self.list_types) * 2.0)
        for collection in self.collections.itervalues():
            for current_collection in collection.itervalues():
                progress += current_collection.progress / (len(self.list_types) * 2.0)

        self.update_action(100.0 * progress)

        return True

    def show_update_callback(self, result=None):
        '''method used as callback, because both GtkRunner and buttons
        need the first argument on the on_update method'''
        if result is not None and not result[0]:
            log.error(str(result[1]))
        if not self.progress:
            return

        #hide progressbox
        self.progressbox.hide()
        self.progress_cancel_button.disconnect(self.end_progress_handler)
        self.progress = False
        self.show_update()

    def _end_progress_cb(self, *args):
        '''stops download of plugins'''
        for collection in self.collections.itervalues():
            for current_collection in collection.itervalues():
                current_collection.stop()
        self.show_update_callback()

class DownloadList(DownloadListBase):
    def __init__(self, session, list_type, init_path,
                 radio=False, use_tabs=False):
        '''constructor'''
        DownloadListBase.__init__(self, session, radio, use_tabs)

        self.list_types = [list_type]

        self.current_collection = self.collections[list_type]['supported']

        self.download_list = {}
        self.removable_list = {}

        refresh_button = gtk.Button(stock=gtk.STOCK_REFRESH)
        refresh_button.connect('clicked', self.on_update, True)

        self.download_button = gtk.Button(_('Download'))
        self.download_button.set_image(gtk.image_new_from_stock(
                                       gtk.STOCK_GO_DOWN, gtk.ICON_SIZE_MENU))
        self.download_button.connect('clicked', self.start_download)
        self.download_button.set_property('no-show-all', True)

        self.remove_button = gtk.Button(stock=gtk.STOCK_REMOVE)
        self.remove_button.connect('clicked', self.remove)
        self.remove_button.set_property('no-show-all', True)

        self.no_button = gtk.HBox()
        self.no_button2 = gtk.HBox()

        combo_store = gtk.ListStore(str, str)
        combo_store.append((_('Supported'), 'supported'))
        combo_store.append((_('Community'), 'community'))

        source_combo = gtk.ComboBox()
        source_combo.set_model(combo_store)

        cell = gtk.CellRendererText()
        source_combo.pack_start(cell, True)
        source_combo.add_attribute(cell, 'text', 0)
        source_combo.set_active(0)
        source_combo.connect('changed', self.on_change_source)

        self.buttonbox.pack_start(source_combo, fill=False)
        self.buttonbox.pack_start(refresh_button, fill=False)
        self.buttonbox.pack_start(self.no_button)
        self.buttonbox.pack_start(self.no_button2)
        self.buttonbox.pack_start(self.remove_button, fill=False)
        self.buttonbox.pack_start(self.download_button, fill=False)

    def on_cursor_changed(self, list_view, type_, extra_button=None):
        '''called when a row is selected'''
        if extra_button is None:
            extra_button = self.no_button

        value = self.get_selected_name(list_view)
        if value is not None:
            if value in self.download_list.get(type_, []):
                self.download_item = value
                self.download_button.show()
                extra_button.hide()
            else:
                self.download_button.hide()
                extra_button.show()
            if value in self.removable_list.get(type_, {}):
                self.remove_item = (type_, value)
                self.no_button2.hide()
                self.remove_button.show()
            else:
                self.remove_button.hide()
                self.no_button2.show()

    def get_selected_name(self, list_view):
        '''Gets the current selected name in the list view.'''
        selection = list_view.get_selection()
        if not selection is None:
            model, iter = selection.get_selected()
            if iter is not None:
                name = model.get_value(iter, 2)
                return name
        return None

    def on_change_source(self, combobox):
        '''called when the source is changed'''
        index = combobox.get_active()
        collection_type = combobox.get_model()[index][1]
        self.current_collection = self.collections[self.list_types[0]][collection_type]
        self.show_update()

    def start_download(self, widget=None):
        '''start the download of an extension'''
        if self.progress:
            return

        self.progress = True
        self.set_action(_('Downloading extensions'))
        self.progressbox.show_all()
        self.progress_cancel_button.connect('clicked', self._end_progress_cb)
        self.end_progress_handler = self.progress_cancel_button.connect('clicked',
                                        self._end_progress_cb)
        gobject.timeout_add_seconds(1, self.update_progress)
        utils.GtkRunner(self.show_update_callback, self.download)

    def download(self):
        '''download an extension'''
        self.updated_amount = 0
        self.current_collection.download(self.download_item)

    def remove(self, widget):
        '''remove an extension'''
        path = self.removable_list[self.remove_item[0]][self.remove_item[1]]
        self.current_collection.remove(path)
        self.removable_list[self.remove_item[0]].pop(self.remove_item[1])
        self.show_update()

    def fetch_metadata(self, type_, name):
        ''' fetch metadata '''
        meta = self.current_collection.fetch_metadata(type_, name)
        return meta

    def check_version(self, type_, name):
        meta = self.fetch_metadata(type_, name)
        if not meta or not meta.get('required emesene version'):
            return True

        if self.version_value(meta.get('required emesene version')) > \
           self.version_value(Info.EMESENE_VERSION):
            return False

        return True

    def show_update(self):
        '''show an update list of the set collection'''
        self.download_list = {}

        for box in self.boxes:
            if box.extension_type not in self.download_list:
                self.download_list[box.extension_type] = []

            element = self.current_collection.extensions_descs.get(box.extension_type, {})
            box.append(False, _('Available for download'),
                       'installable', visible=False)

            for label in element:
                if not self.check_version(box.extension_type, label):
                    continue
                if label not in box.extension_list:
                    self.download_list[box.extension_type].append(label)

                box.append(False, self.strip_name(label, box.extension_type),
                           label, False, description=self.fetch_metadata(
                                box.extension_type, label).get('description'))

class ThemeList(DownloadList):
    def __init__(self, session):
        self.config_dir = e3.common.ConfigDir('emesene2')
        DownloadList.__init__(
            self, session, 'themes',
            self.config_dir.join('themes'), True, True)

        self.default_action = _('Refresh themes')

        self.themes = {}
        self.theme_configs = {}
        self.callbacks = {}

    def on_toggled(self, widget, path, model, type_):
        '''called when the toggle button in list view is pressed'''
        for row in model:
            if row[0]:
                if model[path][5].startswith(self.config_dir.base_dir):
                    self.removable_list[type_][row[2]] = row[5]
                row[0] = False
        model[path][0] = True
        self.removable_list[type_].pop(model[path][2], None)
        self.callbacks[type_](self.theme_configs[type_], model[path][2])

    def set_theme(self, property_name, value):
        self.set_attr(property_name, value)

    def show_update(self):
        '''called when the liststore need to be changed'''
        self.removable_list = {}

        for box in self.boxes:
            if box.extension_type not in self.removable_list:
                self.removable_list[box.extension_type] = {}
            box.clear_all()
            box.append(False, _('Installed'),
                       'installed', visible=False)

            current = self.get_attr(self.theme_configs[box.extension_type])
            for path in self.themes[box.extension_type].list():
                label = self.themes[box.extension_type].get_name_from_path(path)
                name = os.path.basename(path)
                is_current = name == current or label == current
                if path.startswith(self.config_dir.base_dir) and not is_current:
                    self.removable_list[box.extension_type][name] = path
                box.append(is_current, label, name, path=path)
        DownloadList.show_update(self)

    def strip_name(self, name, type_):
        '''return a stripped version of theme name.'''
        name = name.replace('_', ' ')
        name = self.themes[type_].pattern.sub('', name)
        return '%s' % name

    def append_theme_tab(self, name, theme_type, theme, theme_config,
                         callback=None):
        self.themes[theme_type] = theme
        self.theme_configs[theme_type] = theme_config
        if callback:
            self.callbacks[theme_type] = callback
        else:
            self.callbacks[theme_type] = self.set_theme
        box = self.append_tab(name, theme_type, True)
        return box

class UpdateList(DownloadListBase):
    def __init__(self, session):
        DownloadListBase.__init__(self, session)
        self.update_list = {'plugins': {}, 'themes': {}}

        self.update_amount = 0

        self.themes = {}
        self.theme_names = {}
        self.theme_configs = {}

        self.download_button = gtk.Button(_('Update'))
        self.download_button.set_image(gtk.image_new_from_stock(
                                       gtk.STOCK_REFRESH, gtk.ICON_SIZE_MENU))
        self.download_button.connect('clicked', self.start_download)

        self.buttonbox.set_layout(gtk.BUTTONBOX_END)
        self.buttonbox.pack_start(self.download_button, fill=False)

    def on_toggled(self, widget, path, model, type_):
        '''remove from or add to the update_list'''
        model[path][0] = not model[path][0]
        if model[path][6] == 'plugin':
            item = self.update_list['plugins'][model[path][6]]
        else:
            item = self.update_list['themes'][model[path][6]]
        if model[path][0]:
            item[model[path][2]] = model[path][5]
        else:
            del item[model[path][2]]

    def download(self, name, current_extension):
        '''download an extension'''
        current_extension.download(name)

    def remove(self, path, current_extension):
        '''remove an extension'''
        current_extension.remove(path)

    def get_collection(self, collection, type_, name):
        if self.collections[collection]['supported'].has_item(type_, name):
            return self.collections[collection]['supported']
        elif self.collections[collection]['community'].has_item(type_, name):
            return self.collections[collection]['community']

    def start_download(self, widget=None):
        '''start the download of an extension'''
        if self.progress:
            return

        self.progress = True
        self.set_action(_('Updating extensions'))
        self.progressbox.show_all()
        self.end_progress_handler = self.progress_cancel_button.connect('clicked',
                                        self._end_progress_cb)
        gobject.timeout_add_seconds(1, self.update_download_progress)
        utils.GtkRunner(self.show_update_callback, self.download_updates)

    def download_updates(self):
        self.updated_amount = 0
        for collection_name, items in self.update_list.iteritems():
            for ext_type, ext_list in items.iteritems():
                for ext, path in ext_list.iteritems():
                    if self.progress is None:
                        return

                    current_extension = self.get_collection(collection_name, ext_type, ext)
                    self.download(ext, current_extension)
                    self.updated_amount += 1
                ext_list = {}
        self.show_update()

    def update_download_progress(self):
        if not self.progress:
            return False

        if not self.update_amount:
            progress = 1.0
        else:
            progress = self.updated_amount / float(self.update_amount)
            for collection in self.collections.itervalues():
                for current_collection in collection.itervalues():
                    progress += current_collection.progress / float(self.update_amount)

        self.update_action(100.0 * progress)

        return True

    def fetch_metadata(self, collection, type_, name):
        meta = self.collections[collection]['supported'].fetch_metadata(type_, name)
        if not meta:
            meta = self.collections[collection]['community'].fetch_metadata(type_, name)
        return meta

    def check_updates(self, collection, type_, path, instance=None):
        '''check whether updates are available'''
        name = os.path.basename(path)
        meta = self.fetch_metadata(collection, type_, name)
        if not meta or not meta.get('version') or not meta.get('required emesene version'):
            return False

        local_meta = e3.common.MetaData.get_metadata_from_path(path)
        if not local_meta or not local_meta.get('required emesene version'):
            return True

        if self.version_value(meta.get('required emesene version')) > \
           self.version_value(Info.EMESENE_VERSION):
            return False

        if not local_meta.get('version'):
            return True

        if self.version_value(meta.get('version')) > self.version_value(local_meta.get('version')):
            return True

        return False

    def show_update(self):
        '''called when the liststore need to be changed'''
        self.clear_all()
        self.update_amount = 0

        for theme_type in self.themes.iterkeys():
            first = True
            if theme_type not in self.update_list['themes']:
                self.update_list['themes'][theme_type] = {}

            for path in self.themes[theme_type].list():
                if not self.check_updates('themes', theme_type, path):
                    continue
                if first:
                    self.append(False, self.theme_names[theme_type], theme_type, visible=False)
                    first = False
                name = os.path.basename(path)
                label = self.themes[theme_type].get_name_from_path(path)
                self.update_list['themes'][theme_type][name] = path
                self.update_amount += 1
                self.append(True, label, name, path=path, type_=theme_type)

        pluginmanager = get_pluginmanager()

        first = True
        if 'plugin' not in self.update_list['plugins']:
            self.update_list['plugins']['plugin'] = {}

        for name, plugin in pluginmanager.get_plugins():
            path = plugin.path
            if not self.check_updates('plugins', 'plugin', path, plugin):
                continue
            if first:
                self.append(False, _('Plugins'), 'installed', True, False)
                first = False
            self.update_list['plugins']['plugin'][name] = path
            self.update_amount += 1
            self.append(True, name, name, path=path, type_='plugin',
                        description=pluginmanager.plugin_description(name))

    def append_theme(self, name, theme_type, theme, theme_config):
        self.themes[theme_type] = theme
        self.theme_configs[theme_type] = theme_config
        self.theme_names[theme_type] = name
