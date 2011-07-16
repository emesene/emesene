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
import webbrowser

import e3.common
import gui
import utils
import extension

from gui.base import MarkupParser

import PluginWindow

import logging
log = logging.getLogger('gtkui.Preferences')

try:
    from enchant_dicts import list_dicts
except:
    def list_dicts():
        return []

# TODO: consider moving to nicer icons than stock ones.
LIST = [
    {'stock_id' : gtk.STOCK_FULLSCREEN,'text' : _('Interface')},
    {'stock_id' : gtk.STOCK_FLOPPY,'text' : _('Desktop')},
    {'stock_id' : gtk.STOCK_MEDIA_NEXT,'text' : _('Sounds')},
    {'stock_id' : gtk.STOCK_LEAVE_FULLSCREEN,'text' : _('Notifications')},
    {'stock_id' : gtk.STOCK_SELECT_COLOR,'text' : _('Theme')},
    {'stock_id' : gtk.STOCK_DIALOG_WARNING,'text' : _('Extensions')},
    {'stock_id' : gtk.STOCK_DISCONNECT,'text' : _('Plugins')},
]

class Preferences(gtk.Window):
    """A window to display/modify the preferences
    """

    def __init__(self, session):
        """constructor
        """
        gtk.Window.__init__(self)
        self.set_border_width(2)
        self.set_title(_("Preferences"))
        self.session = session

        self.set_default_size(600, 400)
        self.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_DIALOG)

        ''' TREE VIEW STUFF '''
        # Create the list store model for the treeview.
        self.listStore = gtk.ListStore(gtk.gdk.Pixbuf, str)



        # Create the TreeView
        treeView = gtk.TreeView(self.listStore)

        # Create the renders
        cellText = gtk.CellRendererText()
        cellPix = gtk.CellRendererPixbuf()

        # Create the single Tree Column
        treeViewColumn = gtk.TreeViewColumn(_('Categories'))

        treeViewColumn.pack_start(cellPix, expand=False)
        treeViewColumn.add_attribute(cellPix, 'pixbuf',0)
        treeViewColumn.pack_start(cellText, expand=True)
        treeViewColumn.set_attributes(cellText, text=1)

        treeView.append_column(treeViewColumn)
        treeView.set_headers_visible(False)
        treeView.connect('cursor-changed', self._on_row_activated)
        self.treeview = treeView

        self.notebook = gtk.Notebook()
        self.notebook.set_show_tabs(False)
        self.notebook.set_resize_mode(gtk.RESIZE_QUEUE)
        self.notebook.set_scrollable(True)

        ''' PACK TREEVIEW, FRAME AND HBOX '''
        vbox = gtk.VBox()

        vbox.set_spacing(4)
        hbox = gtk.HBox(homogeneous=False, spacing=5)
        hbox.pack_start(treeView, True,True) # False, True
        hbox.pack_start(self.notebook, True, True)
        vbox.pack_start(hbox, True,True) # hbox, True, True

        self.interface = Interface(session)
        self.desktop = DesktopTab(session)
        self.sound = Sound(session)
        self.notification = Notification(session)
        self.theme = Theme(session)
        self.extension = Extension(session)
        self.plugins = PluginWindow.PluginMainVBox(session)

        self.buttons = gtk.HButtonBox()
        self.buttons.set_border_width(2)
        self.buttons.set_layout(gtk.BUTTONBOX_END)
        self.close = gtk.Button(stock=gtk.STOCK_CLOSE)
        self.close.connect('clicked', lambda *args: self.hide())
        self.buttons.pack_start(self.close)

        vbox.pack_start(self.buttons, False, False)

        # Create a dict that stores each page
        self.page_dict = []

        # Keep local copies of the objects
        self.interface_page = self.interface
        self.desktop_page = self.desktop
        self.sound_page = self.sound
        self.notifications_page = self.notification
        self.theme_page = self.theme
        self.extensions_page = self.extension
        self.plugins_page = self.plugins

        self.__init_list()

        self.connect('delete_event', self.hide_on_delete)
        self.add(vbox)
        vbox.show_all()

    def remove_subscriptions(self):
        self.interface.remove_subscriptions()
        self.sound.remove_subscriptions()
        self.theme.remove_subscriptions()

    def remove_from_list(self, icon, text, page):

        LIST.remove({'stock_id' : icon,'text' : text})
        self.page_dict.remove(page)
        num = self.notebook.page_num(page)
        self.notebook.remove_page(num)
        self.__refresh_list()    

    def add_to_list(self, icon, text, page):

        LIST.append({'stock_id' : icon,'text' : text})
        self.page_dict.append(page)
        self.notebook.append_page(page)
        self.__refresh_list()

    def __init_list(self):

        # Whack the pages into a dict for future reference

        self.page_dict.append(self.interface_page)
        self.page_dict.append(self.desktop_page)
        self.page_dict.append(self.sound_page)
        self.page_dict.append(self.notifications_page)
        self.page_dict.append(self.theme_page)
        self.page_dict.append(self.extensions_page)
        self.page_dict.append(self.plugins_page)

        for i in LIST:
            # we should use always the same icon size,
            # we can remove that field in LIST
            self.listStore.append([self.render_icon(i['stock_id'],
                             gtk.ICON_SIZE_LARGE_TOOLBAR), i['text']])

        if 'msn' in self.session.SERVICES: # only when session is papylib.
            LIST.append({'stock_id' : gtk.STOCK_NETWORK,'text' : _('Live Messenger')})
            self.listStore.append([self.render_icon(gtk.STOCK_NETWORK,
                             gtk.ICON_SIZE_LARGE_TOOLBAR), _('Live Messenger')])
            self.msn_papylib = MSNPapylib(self.session)
            self.msn_papylib_page = self.msn_papylib
            self.page_dict.append(self.msn_papylib_page)

        for i in range(len(self.page_dict)):
           self.notebook.append_page(self.page_dict[i])

    def __refresh_list(self):

        self.listStore.clear()

        for i in LIST:
            # we should use always the same icon size,
            # we can remove that field in LIST
            self.listStore.append([self.render_icon(i['stock_id'],
                             gtk.ICON_SIZE_LARGE_TOOLBAR), i['text']])

    def _on_row_activated(self,treeview):
        # Get information about the row that has been selected
        cursor, obj = treeview.get_cursor()
        self.showPage(cursor[0])

    def showPage(self, index):
        self.notebook.set_current_page(index)
        self.current_page = index
        self.page_dict[index].on_update()

class BaseTable(gtk.Table):
    """a base table to display preferences
    """
    def __init__(self, rows, columns, homogeneous=False):
        """constructor
        """
        gtk.Table.__init__(self, rows, columns, homogeneous)
        self.rows = rows
        self.columns = columns
        self.set_row_spacings(4)
        self.set_col_spacings(4)

        self.current_row = 0

    def add_text(self, text, column, row, align_left=False, line_wrap=True):
        """add a label with thext to row and column, align the text left if
        align_left is True
        """
        label = gtk.Label(text)
        self.add_label(label, column, row, align_left)

    def add_label(self, label, column, row, align_left=False, line_wrap=True):
        """add a label with thext to row and column, align the text left if
        align_left is True
        """
        if align_left:
            label.set_alignment(0.0, 0.5)

        label.set_line_wrap(line_wrap)
        self.attach(label, column, column + 1, row, row + 1, yoptions=0)

    def add_button(self, text, column, row, on_click, xoptions=gtk.EXPAND|gtk.FILL, yoptions=gtk.EXPAND|gtk.FILL):
        """add a button with text to the row and column, connect the clicked
        event to on_click"""
        button = gtk.Button(text)
        button.connect('clicked', on_click)
        self.attach(button, column, column + 1, row, row + 1, xoptions,
                yoptions)

    def append_row(self, widget, row=None):
        """append a row to the table
        """
        increment_current_row = False
        if row == None:
            row = self.current_row
            increment_current_row = True

        self.attach(widget, 0, self.columns, row, row + 1, yoptions=gtk.SHRINK)

        if increment_current_row:
            self.current_row += 1

    def append_entry_default(self, text, format_type, property_name, default):
        """append a row with a label and a entry, set the value to the
        value of property_name if exists, if not set it to default.
         Add a reset button that sets the value to the default"""

        def on_reset_clicked(button, entry, default):
            """called when the reset button is clicked, set
            entry text to default"""
            entry.set_text(default)

        def on_entry_changed(entry, property_name):
            """called when the content of an entry changes,
            set the value of the property to the new value"""
            self.set_attr(property_name, entry.get_text())

        def on_help_clicked(button, format_type):
            """called when the help button is clicked"""
            extension.get_default('dialog').contactlist_format_help(format_type)

        hbox = gtk.HBox(spacing=4)
        label = gtk.Label(text)
        label.set_alignment(0.0, 0.5)
        text = self.get_attr(property_name)

        entry = gtk.Entry()
        entry.set_text(text)

        reset = gtk.Button()
        entry_help = gtk.Button()

        hbox.pack_start(label)
        hbox.pack_start(entry, False)
        hbox.pack_start(reset, False)
        hbox.pack_start(entry_help, False)

        reset_image = gtk.image_new_from_stock(gtk.STOCK_CLEAR,
                                               gtk.ICON_SIZE_MENU)
        reset.set_label(_('Reset'))
        reset.set_image(reset_image)
        reset.connect('clicked', on_reset_clicked, entry, default)
        entry.connect('changed', on_entry_changed, property_name)

        help_image = gtk.image_new_from_stock(gtk.STOCK_HELP,
                                              gtk.ICON_SIZE_MENU)
        entry_help.set_image(help_image)
        entry_help.connect('clicked', on_help_clicked, format_type)

        self.append_row(hbox, None)

    def create_check(self, text, property_name):
        """create a CheckButton and
        set the check state with default
        """
        default = self.get_attr(property_name)
        widget = gtk.CheckButton(text)
        widget.set_active(default)
        widget.connect('toggled', self.on_toggled, property_name)
        return widget

    def append_check(self, text, property_name, row=None):
        """append a row with a check box with text as label and
        set the check state with default
        """
        widget = self.create_check(text, property_name)
        self.append_row(widget, row)
        return widget

    def append_range(self, text, property_name, min_val, max_val,is_int=True):
        """append a row with a scale to select an integer value between
        min and max
        """
        hbox = gtk.HBox()
        hbox.set_homogeneous(True)
        label = gtk.Label(text)
        label.set_alignment(0.0, 0.5)
        default = self.get_attr(property_name)

        if default is None:
            default = min_val

        scale = gtk.HScale()
        scale.set_range(min_val, max_val)
        scale.set_value(default)

        if is_int:
            scale.set_digits(0)

        hbox.pack_start(label, True, True)
        hbox.pack_start(scale, False)

        scale.connect('button_release_event', self.on_range_changed, property_name,
                is_int)

        self.append_row(hbox, None)

    def fill_combo(self, combo, getter, property_name, values=None):
        if values:
            default = getter()[values.index(self.get_attr(property_name))]
        else:
            default = self.get_attr(property_name)
        count = 0
        default_count = 0
        for item in getter():
            combo.append_text(item)
            if item == default:
                default_count = count

            count += 1

        combo.set_active(default_count)

    def create_combo (self, getter, property_name, values=None, changed_cb = None):
        combo = gtk.combo_box_new_text()
        self.fill_combo(combo, getter, property_name, values)
        if changed_cb:
            combo.connect('changed', changed_cb, property_name, values)
        else:
            combo.connect('changed', self.on_combo_changed, property_name, values)
        return combo

    def create_combo_with_label(self, text, getter, property_name,values=None, changed_cb = None):
        """creates and return a new ComboBox with a label and append values to the combo
        """
        hbox = gtk.HBox()
        hbox.set_homogeneous(True)
        label = gtk.Label(text)
        label.set_alignment(0.0, 0.5)
        combo = self.create_combo(getter, property_name, values, changed_cb)

        hbox.pack_start(label, True, True)
        hbox.pack_start(combo, False)

        return hbox

    def append_combo(self, text, getter, property_name,values=None):
        """append a label and a combo and adds values to it
        """
        hbox = self.create_combo_with_label(text, getter, property_name,values)
        self.append_row(hbox, None)

    def append_markup(self, text):
        """append a label
        """
        hbox = gtk.HBox()
        hbox.set_homogeneous(True)
        label = gtk.Label()
        label.set_alignment(0.0, 0.5)
        label.set_markup(text)

        hbox.pack_start(label, True, True)

        self.append_row(hbox, None)

    def on_combo_changed(self, combo, property_name, values=None):
        """callback called when the selection of the combo changed
        """
        if not(values):
            self.set_attr(property_name, combo.get_active_text())
        else:
            self.set_attr(property_name, values[combo.get_active()])

    def on_range_changed(self, scale, widget, property_name, is_int):
        """callback called when the selection of the combo changed
        """
        value = scale.get_value()

        if is_int:
            value = int(value)

        self.set_attr(property_name, value)

    def on_toggled(self, checkbutton, property_name):
        """default callback for a cehckbutton, set property_name
        to the status of the checkbutton
        """
        self.set_attr(property_name, checkbutton.get_active())

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

    def get_attr_or_default(self, obj, name, default=None):
        """try to get the value of the attribute 'name' from obj, if it
        doesn't exist return default"""
        if not hasattr(obj, name):
            return default

        return getattr(obj, name)

    def on_update(self):
        pass

    def on_redraw_main_screen(self, button):
        """called when the Redraw main screen button is clicked"""
        self.session.save_config()
        self.session.signals.login_succeed.emit()
        self.session.signals.contact_list_ready.emit()

    def on_synch_emesene1(self, button):
        """called when the Synch test button is clicked"""
        syn = extension.get_default('synch tool')
        user = self.session.account.account
        current_service = self.session.config.service
        syn = syn(self.session, current_service)
        syn.show(True)

class Interface(BaseTable):
    """the panel to display/modify the config related to the gui
    """

    def __init__(self, session):
        """constructor
        """
        BaseTable.__init__(self, 17, 2)
        self.set_border_width(5)
        self.session = session

        langs = list_dicts()

        self.spell_lang = self.session.config.get_or_set("spell_lang", "en")
        self.lang_menu = gtk.combo_box_new_text()
        self.lang_menu.connect("changed", self._on_lang_combo_change)

        index = 0
        for lang in langs:
            self.lang_menu.append_text(lang)
            if lang == self.spell_lang:
                self.lang_menu.set_active(index)
            index += 1

        self.session.config.get_or_set('i_tab_position', 0)
        self.tab_pos_cb = self.create_combo_with_label(_('Tab position'), self.get_tab_positions,
                'session.config.i_tab_position',range(4))

        self.append_markup('<b>'+_('Main window:')+'</b>')
        self.append_check(_('Show user panel'),
            'session.config.b_show_userpanel')
        self.append_markup('<b>'+_('Conversation window:')+'</b>')
        self.session.config.get_or_set('b_avatar_on_left', False)
        self.session.config.get_or_set('b_toolbar_small', False)
        self.session.config.get_or_set('b_conversation_tabs', True)
        self.append_check(_('Tabbed Conversations'),
                'session.config.b_conversation_tabs')
        self.append_row(self.tab_pos_cb)
        self.session.config.get_or_set('b_show_avatar_in_taskbar', True)
        self.append_check(_('Start minimized/iconified'), 'session.config.b_conv_minimized')
        self.append_check(_('Show emoticons'), 'session.config.b_show_emoticons')
        self.append_check(_('Show conversation header'),
            'session.config.b_show_header')
        self.append_check(_('Show conversation side panel'),
            'session.config.b_show_info')
        self.append_check(_('Show conversation toolbar'),
            'session.config.b_show_toolbar')
        # small-toolbar sensitivity depends on conversation toolbar visibility
        self.cb_small_toolbar = self.create_check(_('Small conversation toolbar'), 
            'session.config.b_toolbar_small')
        self.session.config.subscribe(self._on_cb_show_toolbar_changed,
            'b_show_toolbar')
        self.append_row(self.cb_small_toolbar)

        # Avatar-on-left sensitivity depends on side panel visibility
        self.cb_avatar_left = self.create_check(_('Avatar on conversation left side'), 
            'session.config.b_avatar_on_left')
        self.session.config.subscribe(self._on_cb_side_panel_changed,
            'b_show_info')
        self.append_row(self.cb_avatar_left)
        self.append_check(_('Allow auto scroll in conversation'),
            'session.config.b_allow_auto_scroll')
        self.append_check(_('Enable spell check if available (requires %s)') % 'python-gtkspell',
            'session.config.b_enable_spell_check')
        self.attach(self.lang_menu, 2, 3, 13, 14)
        self.append_check(_('Show avatars in taskbar instead of status icons'), 
            'session.config.b_show_avatar_in_taskbar')

        self.append_range(_('Contact list avatar size'),
            'session.config.i_avatar_size', 18, 64)
        self.append_range(_('Conversation avatar size'),
            'session.config.i_conv_avatar_size', 18, 128)
        
        self.session.config.subscribe(self._on_spell_change,
            'b_enable_spell_check')

        self.session.config.subscribe(self._on_conversation_tabs_change,
            'b_conversation_tabs')

        #update tab_pos combo sensitivity
        self._on_conversation_tabs_change(self.session.config.get_or_set('b_conversation_tabs', True))
        #update spell lang combo sensitivity
        self._on_spell_change(self.session.config.get_or_set('b_enable_spell_check', False))
        #update side-panel dependent options sensitivity
        self._on_cb_side_panel_changed(self.session.config.get_or_set('b_show_info', True))
        #update small-toolbar sensitivity
        self._on_cb_show_toolbar_changed(self.session.config.get_or_set('b_show_toolbar', True))

        self.show_all()

    def _on_cb_show_toolbar_changed(self, value):
        if value:
            self.cb_small_toolbar.set_sensitive(True)
        else:
            self.cb_small_toolbar.set_sensitive(False)

    def _on_cb_side_panel_changed(self, value):
        if value:
            self.cb_avatar_left.set_sensitive(True)
        else:
            self.cb_avatar_left.set_sensitive(False)

    def _on_spell_change(self, value):
        if value:
            self.lang_menu.set_sensitive(True)
        else:
            self.lang_menu.set_sensitive(False)

    def _on_conversation_tabs_change(self, value):
        if value:
            self.tab_pos_cb.set_sensitive(True)
        else:
            self.tab_pos_cb.set_sensitive(False)

    def _on_lang_combo_change(self, combo):
        self.session.config.spell_lang = combo.get_active_text()

    def get_tab_positions(self):
        return [_("Top"),_("Bottom"),_("Left"),_("Right")]

    def remove_subscriptions(self):
        self.session.config.unsubscribe(self._on_cb_show_toolbar_changed,
            'b_show_toolbar')
        self.session.config.unsubscribe(self._on_cb_side_panel_changed,
            'b_show_info')
        self.session.config.unsubscribe(self._on_spell_change,
            'b_enable_spell_check')
        self.session.config.unsubscribe(self._on_conversation_tabs_change,
            'b_conversation_tabs')

class Sound(BaseTable):
    """the panel to display/modify the config related to the sounds
    """

    def __init__(self, session):
        """constructor
        """
        BaseTable.__init__(self, 7, 1)
        self.set_border_width(5)
        self.session = session
        self.array = []
        self.append_markup('<b>'+_('General:')+'</b>')
        self.append_check(_('Mute sounds'),
            'session.config.b_mute_sounds')
        self.append_markup('<b>'+_('Messages events:')+'</b>')
        self.array.append(self.append_check(_('Play sound on sent message'),
            'session.config.b_play_send'))
        self.array.append(self.append_check(_('Play sound on first received message'),
            'session.config.b_play_first_send'))
        self.array.append(self.append_check(_('Play sound on received message'),
            'session.config.b_play_type'))
        self.array.append(self.append_check(_('Play sound on nudge'),
            'session.config.b_play_nudge'))
        self.append_markup('<b>'+_('Users events:')+'</b>')
        self.array.append(self.append_check(_('Play sound on contact online'),
            'session.config.b_play_contact_online'))
        self.array.append(self.append_check(_('Play sound on contact offline'),
            'session.config.b_play_contact_offline'))

        self._on_mute_sounds_changed(self.session.config.b_mute_sounds)

        self.session.config.subscribe(self._on_mute_sounds_changed,
            'b_mute_sounds')

        self.show_all()

    def _on_mute_sounds_changed(self, value):
        for i in self.array:
            if value:
                i.set_sensitive(False)
            else:
                i.set_sensitive(True)

    def remove_subscriptions(self):
        self.session.config.unsubscribe(self._on_mute_sounds_changed,
            'b_mute_sounds')

class Notification(BaseTable):
    """the panel to display/modify the config related to the notifications
    """

    def __init__(self, session):
        """constructor
        """
        BaseTable.__init__(self, 4, 1)
        self.set_border_width(5)
        self.session = session
        self.append_markup('<b>'+_('Users events:')+'</b>')
        self.append_check(_('Notify on contact online'),
            'session.config.b_notify_contact_online')
        self.append_check(_('Notify on contact offline'),
            'session.config.b_notify_contact_offline')
        self.append_markup('<b>'+_('Messages events:')+'</b>')
        self.append_check(_('Notify on received message'),
            'session.config.b_notify_receive_message')
        self.show_all()

class Theme(BaseTable):
    """the panel to display/modify the config related to the theme
    """

    def __init__(self, session):
        """constructor
        """
        BaseTable.__init__(self, 6, 1)
        self.set_border_width(5)
        self.session = session

        ContactList = extension.get_default('contact list')

        self.session.config.get_or_set('adium_theme', 'renkoo')

        cb_override_text_color = self.create_check(_('Override incoming text color'),
            'session.config.b_override_text_color')
        self.session.config.subscribe(self._on_cb_override_text_color_toggled,
            'b_override_text_color')

        def on_color_selected(cb):
            col = cb.get_color()
            col_e3 = e3.base.Color(col.red, col.green, col.blue)
            self.set_attr('session.config.override_text_color', '#'+col_e3.to_hex())

        self.b_text_color = gtk.ColorButton(color=gtk.gdk.color_parse(
                            self.get_attr('session.config.override_text_color')))
        self.b_text_color.set_use_alpha(False)
        self.b_text_color.connect('color-set', on_color_selected)
        h_color_box = gtk.HBox()
        h_color_box.pack_start(cb_override_text_color)
        h_color_box.pack_start(self.b_text_color)

        self.append_row(h_color_box)
        #update ColorButton sensitive
        self._on_cb_override_text_color_toggled(
                self.session.config.get_or_set('b_override_text_color', False))

        self.append_combo(_('Image theme'), gui.theme.get_image_themes,
            'session.config.image_theme')
        self.append_combo(_('Sound theme'), gui.theme.get_sound_themes,
            'session.config.sound_theme')
        self.append_combo(_('Emote theme'), gui.theme.get_emote_themes,
            'session.config.emote_theme')
        self.adium_theme_combo = self.create_combo_with_label(_('Adium theme'),
                gui.theme.get_adium_themes, 'session.config.adium_theme',
                changed_cb = self._on_adium_theme_combo_changed)
        self.append_row(self.adium_theme_combo)
        hbox = gtk.HBox()
        hbox.set_homogeneous(True)
        label = gtk.Label(_('Adium theme variant'))
        label.set_alignment(0.0, 0.5)
        self.adium_variant_combo = self.create_combo(gui.theme.conv_theme.get_theme_variants,
                'session.config.adium_theme_variant')
        hbox.pack_start(label, True, True)
        hbox.pack_start(self.adium_variant_combo, False)
        self.append_row(hbox, None)

        self.append_entry_default(_('Nick format'), 'nick',
                'session.config.nick_template_clist', ContactList.NICK_TPL)
        self.append_entry_default(_('Group format'), 'group',
                'session.config.group_template', ContactList.GROUP_TPL)

        self.add_button(_('Apply'), 0, 8,
                self.on_redraw_main_screen, 0, 0)

    def _on_adium_theme_combo_changed(self, combo, property_name, values=None):
        #update adium variants combo
        self.on_combo_changed(combo, property_name, values)

        image_name = self.session.config.get_or_set('image_theme', 'default')
        emote_name = self.session.config.get_or_set('emote_theme', 'default')
        sound_name = self.session.config.get_or_set('sound_theme', 'default')
        conv_name = self.session.config.get_or_set('adium_theme',
                'renkoo.AdiumMessagesStyle')
        gui.theme.set_theme(image_name, emote_name, sound_name, conv_name)
        #clear combo
        self.adium_variant_combo.get_model().clear()
        self.fill_combo(self.adium_variant_combo,
            gui.theme.conv_theme.get_theme_variants, 'session.config.adium_theme_variant')

    def _on_cb_override_text_color_toggled(self, value):
        if value:
            self.b_text_color.set_sensitive(True)
        else:
            self.b_text_color.set_sensitive(False)

    def remove_subscriptions(self):
        self.session.config.unsubscribe(self._on_cb_override_text_color_toggled,
            'b_override_text_color')

class Extension(BaseTable):
    """the panel to display/modify the config related to the extensions
    """

    def __init__(self, session):
        """constructor
        """
        BaseTable.__init__(self, 8, 2)
        self.set_border_width(5)
        self.session = session

        self.category_info = gtk.Label('')
        self.name_info = gtk.Label('')
        self.description_info = gtk.Label('')
        self.author_info = gtk.Label('')
        self.website_info = gtk.Label('')
        self.extensions = gtk.combo_box_new_text()
        self.categories = gtk.combo_box_new_text()
        self.extension_list = []

        self._add_info_widgets()
        self._add_categories_and_extensions_combos()

    def _add_info_widgets(self):
        """add the widgets that will display the information of the extension
        category and the selected extension
        """
        def on_activate_link(label, uri):
            webbrowser.open_new_tab(uri)
            return True
        
        self.add_text(_('Categories'), 0, 0, True)
        self.add_text(_('Selected'), 0, 1, True)
        self.add_text('', 0, 2, True)
        self.add_text(_('Name'), 0, 3, True)
        self.add_text(_('Description'), 0, 4, True)
        self.add_text(_('Author'), 0, 5, True)
        self.add_text(_('Website'), 0, 6, True)

        self.add_label(self.name_info, 1, 3, True)
        self.description_info.set_width_chars(40)
        self.add_label(self.description_info, 1, 4, True)
        self.add_label(self.author_info, 1, 5, True)
        self.website_info.connect('activate-link', on_activate_link)
        self.add_label(self.website_info, 1, 6, True)

        self.add_text('', 0, 7, True)

        self.add_button(_('Redraw main screen'), 0, 8,
                self.on_redraw_main_screen, 0, 0)

        self.add_button(_('Synch with emesene1'), 1, 8,
                self.on_synch_emesene1, 0, 0)

    def _get_categories(self):
        ''' get available categories'''
        categories = [ctg for ctg in extension.get_categories().keys() if len(extension.get_extensions(ctg)) > 1]
        categories.sort()
        return categories

    def _add_categories_and_extensions_combos(self):
        """add the widgets to display the extensions"""

        categories = self._get_categories()

        for item in categories:
            self.categories.append_text(item)

        self.categories.connect('changed', self._on_category_changed)
        self.ext_id = self.extensions.connect('changed',
                                              self._on_extension_changed)
        self.attach(self.categories, 1, 2, 0, 1, yoptions=0)
        self.attach(self.extensions, 1, 2, 1, 2, yoptions=0)
        self.categories.set_active(0)

    def _on_category_changed(self, combo):
        """callback called when the category on the combo changes"""
        self.extensions.disconnect(self.ext_id)
        self.extensions.get_model().clear()
        self.extension_list = []
        category = combo.get_active_text()
        default = extension.get_default(category)
        extensions = extension.get_extensions(category)

        count = 0
        selected = 0
        for identifier, ext in extensions.iteritems():
            if default is ext:
                selected = count

            self.extensions.append_text(self.get_attr_or_default(ext, 'NAME',
                ext.__name__))
            self.extension_list.append((ext, identifier))
            count += 1

        self.extensions.set_active(selected)
        self.ext_id = self.extensions.connect('changed',
                                              self._on_extension_changed)
        self._on_extension_changed(self.extensions)

    def _on_extension_changed(self, combo):
        """callback called when the extension on the combo changes"""
        category = self.categories.get_active_text()
        extension_index = self.extensions.get_active()

        # when the model is cleared this event is emited
        if extension_index == -1:
            return

        ext, identifier = self.extension_list[extension_index]
        if not extension.set_default_by_id(category, identifier):
            # TODO: revert the selection to the previous selected extension
            log.warning(_('Could not set %1 as default extension for %2') % \
                (extension_index, category))
            return
        else:
            self.session.config.d_extensions[category] = identifier

        ext = extension.get_default(category)
        self._set_extension_info(ext)

    def _set_extension_info(self, ext):
        """fill the information about the ext"""
        name = self.get_attr_or_default(ext, 'NAME', '?')
        description = self.get_attr_or_default(ext, 'DESCRIPTION', '?')
        author = self.get_attr_or_default(ext, 'AUTHOR', '?')
        website = self.get_attr_or_default(ext, 'WEBSITE', '?')

        self.name_info.set_text(name)
        self.description_info.set_text(description)
        self.author_info.set_text(author)
        self.website_info.set_markup(MarkupParser.urlify(website))

    def on_update(self):
        '''called when changed to this page'''
        # empty categories combo
        model = self.categories.get_model()
        self.categories.set_model(None)
        model.clear()
        # fill it again with available categories
        # this is done because a plugin may have changed them
        categories = self._get_categories()

        for item in categories:
            model.append([item])

        self.categories.set_model(model)
        self.categories.set_active(0)

class DesktopTab(BaseTable):
    """ This panel contains some msn-papylib specific settings """

    def __init__(self, session):
        """constructor
        """
        BaseTable.__init__(self, 3, 2)
        self.set_border_width(5)
        self.session = session

        self.append_markup('<b>'+_('Logger')+'</b>')
        self.append_check(_('Enable logger'), 
                          'session.config.b_log_enabled')
        self.append_markup('<b>'+_('File transfers')+'</b>')
        self.append_check(_('Sort received files by sender'), 
                          'session.config.b_download_folder_per_account')
        self.add_text(_('Save files to:'), 0, 4, True)

        def on_path_selected(f_chooser):
            ''' updates the download dir config value '''
            if f_chooser.get_filename() != self.session.config.download_folder:
                self.session.config.download_folder = f_chooser.get_filename()

        path_chooser = gtk.FileChooserDialog(
            title=_('Choose a Directory'),
            action=gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER,
            buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                     gtk.STOCK_OPEN, gtk.RESPONSE_OK))
        fc_button = gtk.FileChooserButton(path_chooser)
        fc_button.set_current_folder(self.session.config.get_or_set("download_folder", \
                e3.common.locations.downloads()))
        fc_button.connect('selection-changed', on_path_selected)
        self.attach(fc_button, 2, 3, 4, 5, gtk.EXPAND|gtk.FILL, 0)

class MSNPapylib(BaseTable):
    """ This panel contains some msn-papylib specific settings """

    def __init__(self, session):
        """constructor
        """
        BaseTable.__init__(self, 1, 1)
        self.set_border_width(5)
        self.session = session

        align_prin = gtk.Alignment(0.5, 0.5, 1, 1)
        vbox = gtk.VBox(False, 5)
        vbox.set_border_width(10)
        align_prin.add(vbox)

        l_text = gtk.Label(_('If you have problems with your nickname/message/picture '
                        'just click on this button, sign in with your account '
                        'and load a picture in your Live Profile. '
                        'Then restart emesene and have fun.'))
        l_text.set_line_wrap(True)

        vbox.pack_start(l_text, False, False)

        hbox = gtk.HBox(False, 0)
        align2 = gtk.Alignment(0.5, 0.5, 1, 1)
        hbox.pack_start(align2, True, False)
        button = gtk.Button(_('Open Live Profile'))
        button.connect('clicked', self._on_live_profile_clicked)
        align2.add(button)

        vbox.pack_start(hbox, False, False)

        self.attach(align_prin, 0, 1, 0, 1)

        self.show_all()

    def _on_live_profile_clicked(self, arg):
        ''' called when live profile button is clicked '''
        webbrowser.open("http://profile.live.com/details/Edit/Pic")

